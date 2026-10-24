# backend/init_db.py

import os
import sys
import gzip
import csv
from io import BytesIO
import datetime
from sqlalchemy.dialects.sqlite import insert

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.jquants_client import JQuantsClient
from backend.db.database import SessionLocal, engine, Base
from backend.db.models import StockScreener
from backend.core.calculations import calculate_growth, calculate_roe, calculate_margin

class DatabaseInitializer:
    def __init__(self):
        self.client = JQuantsClient()
        self.db = SessionLocal()
        Base.metadata.create_all(bind=engine)

    def _convert_float(self, val_str: str):
        if not val_str or val_str.strip() == "":
            return None
        try:
            return float(val_str)
        except ValueError:
            return None

    def fetch_csv_from_url(self, download_url: str):
        import requests
        resp = requests.get(download_url)
        if resp.status_code != 200:
            return []
        try:
            with gzip.GzipFile(fileobj=BytesIO(resp.content)) as gz:
                content = gz.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines())
                return list(reader)
        except Exception:
            return []

    def run(self):
        print("=== データベースの初期化（全銘柄の過去データ収集）を開始します ===")
        
        # 1. マスター、バリュエーション、カレンダーは「最新の1日分」だけで全件取れる
        print("\n--- 最新の基本データを取得 ---")
        
        def get_latest_data(endpoint):
            res = self.client.get("bulk/list", {"endpoint": endpoint})
            if not res or not res.get("data"): return []
            url_res = self.client.get("bulk/get", {"key": res["data"][-1]["Key"]})
            if not url_res: return []
            return self.fetch_csv_from_url(url_res["url"])

        master_data = get_latest_data("/equities/master")
        valuation_data = get_latest_data("/equities/valuation")
        earnings_data = get_latest_data("/fins/earnings-date")

        # 2. 財務サマリーは「直近約3ヶ月半（100日分）」のZIPを全部取得してマージする
        # （全企業が四半期に1回は決算を出すため、100日分遡れば全社の最新データが埋まる）
        print("\n--- 過去約100日分の財務データを取得（これには少し時間がかかります） ---")
        summary_res = self.client.get("bulk/list", {"endpoint": "/fins/summary"})
        summary_list = summary_res.get("data", [])
        
        # 後ろから100件（約100営業日分）を取得
        target_summaries = summary_list[-100:]
        print(f"対象となる財務ZIPファイル数: {len(target_summaries)}件")
        
        sum_dict = {} # Codeをキーにした財務データの辞書
        
        import requests
        for i, item in enumerate(target_summaries):
            file_key = item["Key"]
            url_res = self.client.get("bulk/get", {"key": file_key})
            if not url_res: continue
                
            csv_data = self.fetch_csv_from_url(url_res["url"])
            
            # 各CSVのデータを辞書に追加（古い日付から順に処理されるため、新しいデータで上書きされていく）
            for row in csv_data:
                code = row.get("LocalCode", "")[:4]
                if code:
                    sum_dict[code] = row
                    
            if (i+1) % 10 == 0:
                print(f"  ... {i+1}/{len(target_summaries)} 件のZIPを処理完了")

        print(f"過去の財務データから {len(sum_dict)} 社分の最新データを復元しました。")

        # 3. 辞書化と結合
        val_dict = {row["Code"][:4]: row for row in valuation_data if "Code" in row}
        earn_dict = {row["Code"][:4]: row for row in earnings_data if "Code" in row}
        
        upsert_data_list = []
        for master in master_data:
            code = master.get("Code", "")[:4]
            if not code: continue
                
            val_row = val_dict.get(code, {})
            sum_row = sum_dict.get(code, {})
            earn_row = earn_dict.get(code, {})
            
            market_cap = self._convert_float(val_row.get("MarketCapitalization"))
            per = self._convert_float(val_row.get("PER"))
            pbr = self._convert_float(val_row.get("PBR"))
            
            net_sales = self._convert_float(sum_row.get("NetSales"))
            prev_net_sales = self._convert_float(sum_row.get("PrevNetSales"))
            op_income = self._convert_float(sum_row.get("OperatingProfit"))
            prev_op_income = self._convert_float(sum_row.get("PrevOperatingProfit"))
            
            eps = self._convert_float(sum_row.get("EarningsPerShare"))
            bps = self._convert_float(sum_row.get("BookValuePerShare"))
            roe = calculate_roe(eps, bps) if eps and bps else None
            
            sales_yoy = calculate_growth(net_sales, prev_net_sales)
            op_yoy = calculate_growth(op_income, prev_op_income)
            op_margin = calculate_margin(op_income, net_sales)
            
            upsert_data_list.append({
                "code": code,
                "company_name": master.get("CompanyName", ""),
                "sector": master.get("Sector33CodeName", ""),
                "market_cap": market_cap,
                "per": per,
                "pbr": pbr,
                "roe": roe,
                "sales_yoy": sales_yoy,
                "op_yoy": op_yoy,
                "op_margin": op_margin,
                "next_earnings_date": earn_row.get("SchDate", ""),
                "period_type": earn_row.get("FQName", ""),
                "updated_at": datetime.datetime.utcnow()
            })
            
        # 4. DB書き込み
        print(f"\n--- DBへ {len(upsert_data_list)} 件のデータを保存中 ---")
        try:
            chunk_size = 1000
            for i in range(0, len(upsert_data_list), chunk_size):
                chunk = upsert_data_list[i:i + chunk_size]
                stmt = insert(StockScreener).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['code'],
                    set_={
                        "company_name": stmt.excluded.company_name,
                        "market_cap": stmt.excluded.market_cap,
                        "per": stmt.excluded.per,
                        "roe": stmt.excluded.roe,
                        "sales_yoy": stmt.excluded.sales_yoy,
                        "op_yoy": stmt.excluded.op_yoy,
                        "next_earnings_date": stmt.excluded.next_earnings_date,
                        "period_type": stmt.excluded.period_type,
                        "updated_at": stmt.excluded.updated_at
                    }
                )
                self.db.execute(stmt)
            self.db.commit()
            print("=== データベースの初期化が完了しました！ ===")
        except Exception as e:
            self.db.rollback()
            print(f"DB書き込みエラー: {e}")
        finally:
            self.db.close()

if __name__ == "__main__":
    updater = DatabaseInitializer()
    updater.run()