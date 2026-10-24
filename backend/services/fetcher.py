# from backend.core.jquants_client import JQuantsClient
# import datetime
    
# class JQuantsFetcher:
#     def __init__(self):
#         self.client = JQuantsClient()

#     def _fetch_all(self, endpoint: str, params: dict, label: str):
#         all_data = []
#         current_params = params.copy()
        
#         while True:
#             try:
#                 res = self.client.get(endpoint, current_params)
#                 if not res: break
                
#                 data = res.get("data", [])
#                 if data: 
#                     all_data.extend(data)

#                 pagination_key = res.get("pagination_key")
#                 if not pagination_key: break
                
#                 current_params["pagination_key"] = pagination_key
#             except Exception as e:
#                 print(f"[ERROR] {label}取得失敗: {e}")
#                 break

#         return {"data": all_data}

#     def fetch_index(self, code: str) -> list:
#         # TOPIXやセクター指数は、取得エラーを防ぐため from を指定せずに全期間を取得する
#         if code == "0000":
#             # TOPIXの場合は専用エンドポイントを優先し、失敗したら汎用エンドポイントにフォールバック
#             res = self._fetch_all("indices/bars/daily/topix", {}, "TOPIX日足")
#             if not res.get("data"):
#                 res = self._fetch_all("indices/bars/daily", {"code": "0000"}, "TOPIX日足(汎用)")
#         else:
#             # セクター指数の場合も全期間取得
#             res = self._fetch_all("indices/bars/daily", {"code": code}, f"指数({code})")
            
#         return res.get("data", [])

#     def fetch_full_profile(self, code: str) -> dict:
#         if len(code) == 4: code += "0"
#         profile = {
#             "code": code, "info": {}, "valuation": {}, "valuation_history": [],
#             "financial_summary": [], "margin_interest": [], "daily_quotes": [],
#             "major_shareholders": [], "large_volume": [], "cross_shareholdings": {},
#             "topix_daily": [], "sector_daily": []
#         }
        
#         try:
#             res_info = self.client.get("equities/master", {"code": code})
#             if res_info and res_info.get("data"): profile["info"] = res_info["data"][-1]
#         except: pass

#         res_val = self._fetch_all("equities/valuation", {"code": code}, "バリュエーション")
#         if res_val.get("data"):
#             profile["valuation_history"] = res_val["data"]
#             profile["valuation"] = res_val["data"][-1]

#         res_fin = self._fetch_all("fins/summary", {"code": code}, "財務サマリー")
#         if res_fin.get("data"): profile["financial_summary"] = res_fin["data"]

#         res_margin = self._fetch_all("markets/margin-interest", {"code": code}, "信用取引残高")
#         if res_margin.get("data"): profile["margin_interest"] = res_margin["data"]

#         ten_years_ago = (datetime.datetime.now() - datetime.timedelta(days=3640)).strftime('%Y%m%d')
        
#         res_prices = self._fetch_all("equities/bars/daily", {"code": code, "from": ten_years_ago}, "株価日足")
        
#         if not res_prices or not res_prices.get("data"):
#             print(f"[{code}] 10年分の取得エラー。デフォルト期間で再取得します。")
#             res_prices = self._fetch_all("equities/bars/daily", {"code": code}, "株価日足")

#         if res_prices and res_prices.get("data"):
#             profile["daily_quotes"] = res_prices["data"]

#         res_maj = self._fetch_all("edinet/major-shareholders", {"code": code}, "大株主")
#         if res_maj.get("data"): profile["major_shareholders"] = res_maj["data"]

#         res_vol = self._fetch_all("edinet/large-volume-shareholders", {"code": code}, "大量保有報告書")
#         if res_vol.get("data"): profile["large_volume"] = res_vol["data"]

#         try:
#             res_cross = self._fetch_all("edinet/cross-shareholdings", {"code": code}, "政策保有株式")
#             if res_cross.get("data"): profile["cross_shareholdings"] = res_cross["data"][-1]
#         except: pass

#         return profile

#     # backend/services/fetcher.py の JQuantsFetcher クラス

#     def fetch_earnings_calendar(self, target_date: str) -> list:
#         """
#         指定した日付の決算発表予定銘柄一覧を取得する
#         J-Quants API: /v2/fins/earnings-date
#         target_date: "YYYY-MM-DD"
#         """
#         # ドキュメントに合わせてハイフンありでも動作しますが、
#         # 念のためハイフンを除去した形式(YYYYMMDD)も安全です(今回はYYYY-MM-DDのまま渡します)
        
#         print(f"[JQuants] 決算カレンダー取得中... (ScheduledDate: {target_date})")
        
#         # ★ 修正: パラメータ名を "date" から "scheduled_date" に変更
#         res = self._fetch_all("fins/earnings-date", {"scheduled_date": target_date}, "決算カレンダー")
#         data = res.get("data", [])
        
#         results = []
#         seen_codes = set()
#         for item in data:
#             code = item.get("Code", "")
#             if not code or code in seen_codes:
#                 continue
                
#             seen_codes.add(code)
#             results.append({
#                 "code": code,
#                 "name": item.get("CoName", ""), 
#                 # APIレスポンスに発表時刻はないため、空文字にしておく
#                 "expected_time": "", 
#                 "period_type": item.get("FQName", ""), 
#             })
        
#         print(f"[JQuants] {target_date} の決算予定銘柄: {len(results)}件取得")
#         return results

# backend/services/fetcher.py

from backend.core.jquants_client import JQuantsClient
import datetime
# 新しく作成した共通関数をインポート
from backend.utils.finance import normalize_code
    
class JQuantsFetcher:
    def __init__(self):
        self.client = JQuantsClient()

    def _fetch_all(self, endpoint: str, params: dict, label: str):
        all_data = []
        current_params = params.copy()
        
        while True:
            try:
                res = self.client.get(endpoint, current_params)
                if not res: break
                
                data = res.get("data", [])
                if data: 
                    all_data.extend(data)

                pagination_key = res.get("pagination_key")
                if not pagination_key: break
                
                current_params["pagination_key"] = pagination_key
            except Exception as e:
                print(f"[ERROR] {label}取得失敗: {e}")
                break

        return {"data": all_data}

    def fetch_index(self, code: str) -> list:
        # TOPIXやセクター指数は、取得エラーを防ぐため from を指定せずに全期間を取得する
        if code == "0000":
            # TOPIXの場合は専用エンドポイントを優先し、失敗したら汎用エンドポイントにフォールバック
            res = self._fetch_all("indices/bars/daily/topix", {}, "TOPIX日足")
            if not res.get("data"):
                res = self._fetch_all("indices/bars/daily", {"code": "0000"}, "TOPIX日足(汎用)")
        else:
            # セクター指数の場合も全期間取得
            res = self._fetch_all("indices/bars/daily", {"code": code}, f"指数({code})")
            
        return res.get("data", [])

    def fetch_full_profile(self, code: str) -> dict:
        # 証券コードを一旦4桁に正規化してから、J-Quantsの仕様に合わせて5桁(末尾0)にする
        code_4digit = normalize_code(code)
        target_code = f"{code_4digit}0" if len(code_4digit) == 4 else code_4digit

        profile = {
            "code": target_code, "info": {}, "valuation": {}, "valuation_history": [],
            "financial_summary": [], "margin_interest": [], "daily_quotes": [],
            "major_shareholders": [], "large_volume": [], "cross_shareholdings": {},
            "topix_daily": [], "sector_daily": []
        }
        
        try:
            res_info = self.client.get("equities/master", {"code": target_code})
            if res_info and res_info.get("data"): profile["info"] = res_info["data"][-1]
        except: pass

        res_val = self._fetch_all("equities/valuation", {"code": target_code}, "バリュエーション")
        if res_val.get("data"):
            profile["valuation_history"] = res_val["data"]
            profile["valuation"] = res_val["data"][-1]

        res_fin = self._fetch_all("fins/summary", {"code": target_code}, "財務サマリー")
        if res_fin.get("data"): profile["financial_summary"] = res_fin["data"]

        res_margin = self._fetch_all("markets/margin-interest", {"code": target_code}, "信用取引残高")
        if res_margin.get("data"): profile["margin_interest"] = res_margin["data"]

        ten_years_ago = (datetime.datetime.now() - datetime.timedelta(days=3640)).strftime('%Y%m%d')
        
        res_prices = self._fetch_all("equities/bars/daily", {"code": target_code, "from": ten_years_ago}, "株価日足")
        
        if not res_prices or not res_prices.get("data"):
            print(f"[{target_code}] 10年分の取得エラー。デフォルト期間で再取得します。")
            res_prices = self._fetch_all("equities/bars/daily", {"code": target_code}, "株価日足")

        if res_prices and res_prices.get("data"):
            profile["daily_quotes"] = res_prices["data"]

        res_maj = self._fetch_all("edinet/major-shareholders", {"code": target_code}, "大株主")
        if res_maj.get("data"): profile["major_shareholders"] = res_maj["data"]

        res_vol = self._fetch_all("edinet/large-volume-shareholders", {"code": target_code}, "大量保有報告書")
        if res_vol.get("data"): profile["large_volume"] = res_vol["data"]

        try:
            res_cross = self._fetch_all("edinet/cross-shareholdings", {"code": target_code}, "政策保有株式")
            if res_cross.get("data"): profile["cross_shareholdings"] = res_cross["data"][-1]
        except: pass

        return profile

    def fetch_earnings_calendar(self, target_date: str) -> list:
        """
        指定した日付の決算発表予定銘柄一覧を取得する
        J-Quants API: /v2/fins/earnings-date
        target_date: "YYYY-MM-DD"
        """
        print(f"[JQuants] 決算カレンダー取得中... (ScheduledDate: {target_date})")
        
        # J-Quants APIの仕様（YYYYMMDD）に合わせてハイフンを除去する
        formatted_date = target_date.replace("-", "")
        res = self._fetch_all("fins/earnings-date", {"scheduled_date": formatted_date}, "決算カレンダー")
        
        # 仕様変更対応（"earnings_dates" か "data" で返る）
        data = res.get("data") or res.get("earnings_dates") or []
        
        results = []
        seen_codes = set()
        for item in data:
            # 取得したコードを4桁に正規化して扱う
            raw_code = item.get("Code", "")
            code_4digit = normalize_code(raw_code)
            
            if not code_4digit or code_4digit in seen_codes:
                continue
                
            seen_codes.add(code_4digit)
            results.append({
                "code": code_4digit, # アプリ全体で4桁に統一
                "name": item.get("CompanyName", item.get("CoName", "")), 
                "expected_time": "", 
                "period_type": item.get("QuarterName", item.get("FQName", "")), 
            })
        
        print(f"[JQuants] {target_date} の決算予定銘柄: {len(results)}件取得")
        return results