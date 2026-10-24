# import csv
# import gzip
# import io
# import os
# import sys
# import time
# from datetime import date, datetime, timedelta, timezone

# import requests
# from requests.exceptions import HTTPError, RequestException
# from sqlalchemy.dialects.sqlite import insert
# from sqlalchemy import inspect, and_, or_

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from backend.core.jquants_client import JQuantsClient
# from backend.db.database import SessionLocal, engine, Base
# from backend.db.models import (
#     FinancialHistory,
#     EarningsEstimateHistory,
#     StockScreener,
# )

# def as_float(value):
#     if value is None:
#         return None
#     value = str(value).strip().replace(",", "")
#     if not value:
#         return None
#     try:
#         return float(value)
#     except ValueError:
#         return None


# def as_date(value):
#     value = (value or "").strip()
#     return value or None


# class DWHBuilder:
#     # 決算短信・業績予想修正などの履歴を保持する。
#     # 既存テーブルを削除しない。
#     def __init__(self):
#         self.client = JQuantsClient()
#         self.db = SessionLocal()


#     def load_master_data(self):
#             """銘柄名と業種を取得する。"""
#             rows = self.get_all_pages("equities/master", {})
#             result = {}
    
#             for row in rows:
#                 code = str(row.get("Code") or "").strip()
#                 if not code:
#                     continue
                
#                 result[code] = {
#                     "company_name": row.get("CoName"),
#                     "sector": row.get("S33Nm") or row.get("S17Nm"),
#                 }
    
#             print(f"[Master] 取得件数: {len(result)}")
#             if rows:
#                 print("[Master] API列名:", list(rows[0].keys()))
    
#             return result
    
#     def load_valuation_data(self):
#             """直近の取得可能な日付のバリュエーションを取得する。"""
#             for offset in range(0, 10):
#                 target_date = date.today() - timedelta(days=offset)
    
#                 try:
#                     rows = self.get_all_pages(
#                         "equities/valuation",
#                         {"date": target_date.isoformat()},
#                     )
#                 except RuntimeError as exc:
#                     # APIが利用できない場合は、原因を表示して終了する。
#                     print(f"[Valuation] APIエラー: {exc}")
#                     return {}
    
#                 if not rows:
#                     continue
                
#                 result = {}
#                 for row in rows:
#                     code = str(row.get("Code") or "").strip()
#                     if not code:
#                         continue
                    
#                     # APIの実際の列名は初回取得時に確認する。
#                     result[code] = row
    
#                 print(
#                     f"[Valuation] 日付={target_date.isoformat()}, "
#                     f"取得件数={len(result)}"
#                 )
#                 print("[Valuation] API列名:", list(rows[0].keys()))
#                 return result
    
#             print("[Valuation] 直近10日間に取得できるデータがありません")
#             return {}
    
#     def get_all_pages(self, endpoint, params=None):
#             """pagination_key がなくなるまでAPIの全ページを取得する。"""
#             query = dict(params or {})
#             rows = []
    
#             while True:
#                 result = self.get(endpoint, query)
#                 if not result:
#                     break
                
#                 rows.extend(result.get("data", []))
    
#                 pagination_key = result.get("pagination_key")
#                 if not pagination_key:
#                     break
                
#                 query["pagination_key"] = pagination_key
    
#             return rows


#     def ensure_schema(self):
#         """新規テーブル作成と、既存SQLiteテーブルへのカラム追加。"""
#         Base.metadata.create_all(bind=engine)

#         inspector = inspect(engine)
#         with engine.begin() as conn:
#             for model in (
#                 FinancialHistory,
#                 EarningsEstimateHistory,
#                 StockScreener,
#             ):
#                 table = model.__table__
#                 if not inspector.has_table(table.name):
#                     continue

#                 existing = {
#                     col["name"]
#                     for col in inspect(engine).get_columns(table.name)
#                 }

#                 for column in table.columns:
#                     if column.name in existing:
#                         continue

#                     # SQLiteのALTER TABLEでは複雑な制約変更を避け、
#                     # 追加カラムはNULL許容で追加する。
#                     sql_type = column.type.compile(dialect=engine.dialect)
#                     conn.exec_driver_sql(
#                         f'ALTER TABLE "{table.name}" '
#                         f'ADD COLUMN "{column.name}" {sql_type}'
#                     )
#                     print(f"[Migration] {table.name}.{column.name} を追加")

#         # 新しいモデル定義で不足テーブルを再確認
#         Base.metadata.create_all(bind=engine)

#     def get(self, endpoint, params=None, retries=4):
#         """429や一時的な通信障害に対してバックオフ付きで再試行。"""
#         for attempt in range(retries):
#             try:
#                 return self.client.get(endpoint, params=params or {})
#             except HTTPError as exc:
#                 status = exc.response.status_code if exc.response else None

#                 if status in (403, 404):
#                     raise RuntimeError(
#                         f"J-Quants APIのアクセスに失敗: "
#                         f"{endpoint}, HTTP {status}"
#                     ) from exc

#                 if status != 429 and (status is None or status < 500):
#                     raise

#                 if attempt == retries - 1:
#                     raise

#                 retry_after = (
#                     exc.response.headers.get("Retry-After")
#                     if exc.response
#                     else None
#                 )
#                 try:
#                     wait = float(retry_after) if retry_after else 2 ** (attempt + 1)
#                 except ValueError:
#                     wait = 2 ** (attempt + 1)

#                 time.sleep(min(wait, 60))

#             except RequestException:
#                 if attempt == retries - 1:
#                     raise
#                 time.sleep(min(2 ** (attempt + 1), 30))

#         raise RuntimeError(f"APIリトライ上限: {endpoint}")

#     def download_csv(self, url):
#         """署名付きURLからgzip CSVをダウンロード。APIキーは付けない。"""
#         with requests.get(
#             url,
#             stream=True,
#             timeout=(10, 120),
#         ) as response:
#             response.raise_for_status()
#             with gzip.GzipFile(fileobj=response.raw) as gz:
#                 text = io.TextIOWrapper(
#                     gz,
#                     encoding="utf-8-sig",
#                     newline="",
#                 )
#                 return list(csv.DictReader(text))

#     def list_bulk_files(self, endpoint):
#         """指定期間のBulkファイル一覧を取得。"""
#         today = date.today()
#         years = int(os.getenv("JQUANTS_HISTORY_YEARS", "3"))
#         start = today - timedelta(days=365 * years)

#         params = {
#             "endpoint": endpoint,
#             "from": start.isoformat(),
#             "to": today.isoformat(),
#         }
#         result = self.get("bulk/list", params)
#         files = result.get("data", []) if result else []

#         # LastModifiedが存在する場合は古い順に処理する。
#         files.sort(key=lambda item: item.get("LastModified", ""))

#         # テスト用の制限。未指定または0なら期間内の全ファイル。
#         limit = int(os.getenv("JQUANTS_BULK_FILE_LIMIT", "0"))
#         if limit > 0:
#             files = files[-limit:]

#         return files

#     def download_bulk_file(self, item):
#         result = self.get("bulk/get", {"key": item["Key"]})
#         if not result or not result.get("url"):
#             raise RuntimeError(f"BulkダウンロードURLを取得できません: {item}")
#         return self.download_csv(result["url"])

#     def build_ids(self, row):
#         code = (row.get("Code") or "").strip()
#         disc_date = (row.get("DiscDate") or "").strip()
#         disc_time = (row.get("DiscTime") or "").strip()
#         disc_no = (row.get("DiscNo") or "").strip()
#         doc_type = (row.get("DocType") or "").strip()
#         period_type = (row.get("CurPerType") or "").strip()

#         if not code or not disc_date:
#             return None, None

#         # コードは5桁のまま保持する。先頭4文字には切り詰めない。
#         suffix = f"{disc_date}_{disc_time}_{disc_no}_{doc_type}_{period_type}"
#         history_id = f"{code}_{suffix}"
#         estimate_id = f"{code}_{disc_date}_{disc_time}_{disc_no}_{doc_type}"

#         return history_id, estimate_id

#     def parse_row(self, row):
#         history_id, estimate_id = self.build_ids(row)
#         if not history_id:
#             return None, None

#         code = (row.get("Code") or "").strip()
#         disclose_date = (row.get("DiscDate") or "").strip()
#         disclose_time = (row.get("DiscTime") or "").strip()
#         disc_no = row.get("DiscNo") or None
#         doc_type = (row.get("DocType") or "").strip()
#         period_type = (row.get("CurPerType") or "").strip()

#         now = datetime.now(timezone.utc)

#         # 財務諸表の開示だけを実績履歴に保存する。
#         # 業績予想修正などに含まれる実績欄の値を、
#         # 四半期実績として誤認しないようにする。
#         history = None

#         if "financialstatements" in doc_type.lower():
#             history = {
#                 "id": history_id,
#                 "code": code,
#                 "disclose_date": disclose_date,
#                 "disclose_time": disclose_time or None,
#                 "disc_no": disc_no,
#                 "doc_type": doc_type or None,
#                 "period_type": period_type or None,
#                 "period_start": as_date(row.get("CurPerSt")),
#                 "period_end": as_date(row.get("CurPerEn")),
#                 "fiscal_year_start": as_date(row.get("CurFYSt")),
#                 "fiscal_year_end": as_date(row.get("CurFYEn")),
#                 "net_sales": as_float(row.get("Sales")),
#                 "op_income": as_float(row.get("OP")),
#                 "net_income": as_float(row.get("NP")),
#                 "current_ytd_sales": as_float(row.get("Sales")),
#                 "current_ytd_op_income": as_float(row.get("OP")),
#                 "cfo": as_float(row.get("CFO")),
#                 "cfi": as_float(row.get("CFI")),
#                 "cff": as_float(row.get("CFF")),
#                 "updated_at": now,
#             }

#         # 財務諸表・業績予想修正などのうち、
#         # 通期予想値が含まれている開示を予想履歴に保存する。
#         forecast_sales = as_float(row.get("FSales"))
#         forecast_op = as_float(row.get("FOP"))
#         forecast_np = as_float(row.get("FNP"))

#         estimate = None

#         if any(
#             value is not None
#             for value in (forecast_sales, forecast_op, forecast_np)
#         ):
#             estimate = {
#                 "id": estimate_id,
#                 "code": code,
#                 "disclose_date": disclose_date,
#                 "disclose_time": disclose_time or None,
#                 "disc_no": disc_no,
#                 "doc_type": doc_type or None,
#                 "fiscal_year_start": as_date(row.get("CurFYSt")),
#                 "fiscal_year_end": as_date(row.get("CurFYEn")),
#                 "period_type": period_type or None,
#                 "forecast_net_sales": forecast_sales,
#                 "forecast_op_income": forecast_op,
#                 "forecast_net_income": forecast_np,
#                 "updated_at": now,
#             }

#         return history, estimate

#     def save_history(self, history_records, estimate_records):
#         """履歴を小分けに保存し、SQLiteの変数上限を回避する。"""

#         # 現在のFinancialHistoryは約20カラムなので、
#         # 25件ずつなら旧SQLiteの変数上限999にも収まりやすい。
#         chunk_size = 25

#         def insert_chunks(model, records):
#             inserted = 0

#             for start in range(0, len(records), chunk_size):
#                 chunk = records[start:start + chunk_size]

#                 stmt = insert(model).values(chunk)
#                 stmt = stmt.on_conflict_do_nothing(
#                     index_elements=["id"]
#                 )

#                 self.db.execute(stmt)
#                 inserted += len(chunk)

#             return inserted

#         try:
#             history_count = insert_chunks(
#                 FinancialHistory,
#                 history_records,
#             )
#             estimate_count = insert_chunks(
#                 EarningsEstimateHistory,
#                 estimate_records,
#             )

#             self.db.commit()

#             print(
#                 f"[DB] 保存処理完了: "
#                 f"財務 {history_count}件、予想 {estimate_count}件"
#             )

#         except Exception as exc:
#             self.db.rollback()

#             print("[DB Error] 履歴保存に失敗しました")
#             print(f"[DB Error] 例外型: {type(exc).__name__}")
#             print(f"[DB Error] 詳細: {exc}")

#             # 原因を隠さず、完全なトレースバックを出す
#             import traceback
#             traceback.print_exc()

#             raise

#     def load_earnings_dates(self):
#         """直近の決算発表予定日を銘柄ごとに取得する。"""
#         today = date.today().isoformat()

#         result = self.get(
#             "fins/earnings-date",
#             {"scheduled_date": today},
#         )
#         rows = result.get("data", []) if result else []

#         earnings_dates = {}
#         for row in rows:
#             code = str(row.get("Code") or "").strip()
#             scheduled_date = (
#                 row.get("SchDate") or row.get("ScheduledDate")
#             )

#             if not code or not scheduled_date:
#                 continue

#             old_date = earnings_dates.get(code)
#             if old_date is None or scheduled_date < old_date:
#                 earnings_dates[code] = scheduled_date

#         print(f"[Earnings] 本日発表予定データ: {len(earnings_dates)}件")
#         return earnings_dates


#     def ingest_financial_summaries(self):
#         files = self.list_bulk_files("/fins/summary")
#         print(f"[Bulk] /fins/summary: {len(files)} ファイル")

#         for index, item in enumerate(files, start=1):
#             key = item.get("Key")
#             if not key:
#                 continue

#             rows = self.download_bulk_file(item)
#             history_records = []
#             estimate_records = []

#             for row in rows:
#                 history, estimate = self.parse_row(row)
#                 if history:
#                     history_records.append(history)
#                 if estimate:
#                     estimate_records.append(estimate)

#             self.save_history(history_records, estimate_records)

#             if index == 1 and rows:
#                 print("[Debug] CSV列名:", list(rows[0].keys()))

#             if index % 10 == 0 or index == len(files):
#                 print(
#                     f"[Bulk] {index}/{len(files)} "
#                     f"履歴={self.db.query(FinancialHistory).count()} "
#                     f"予想={self.db.query(EarningsEstimateHistory).count()}"
#                 )

#     @staticmethod
#     def calc_yoy(current, previous):
#         if current is None or previous is None or previous <= 0:
#             return None
#         return (current - previous) / abs(previous) * 100

#     @staticmethod
#     def calc_margin(op, sales):
#         if op is None or sales is None or sales == 0:
#             return None
#         return op / sales * 100

#     @staticmethod
#     def standalone_value(current_cumulative, previous_cumulative):
#         if current_cumulative is None:
#             return None
#         if previous_cumulative is None:
#             return current_cumulative
#         return current_cumulative - previous_cumulative

#     @staticmethod
#     def is_financial_statement(row):
#         doc_type = (row.doc_type or "").lower()
#         return "financialstatements" in doc_type

#     def get_actual_history(self, code):
#         """実績比較用の決算開示を会計年度・期別に整理する。"""
#         rows = (
#             self.db.query(FinancialHistory)
#             .filter(FinancialHistory.code == code)
#             .order_by(
#                 FinancialHistory.disclose_date.asc(),
#                 FinancialHistory.disclose_time.asc(),
#             )
#             .all()
#         )

#         # 同じ年度・同じ期に複数の開示があれば、最後の開示を採用する。
#         by_period = {}
#         for row in rows:
#             if not self.is_financial_statement(row):
#                 continue
#             if not row.fiscal_year_end or not row.period_type:
#                 continue

#             key = (row.fiscal_year_end, row.period_type)
#             old = by_period.get(key)
#             if old is None or (
#                 row.disclose_date, row.disclose_time or ""
#             ) > (
#                 old.disclose_date, old.disclose_time or ""
#             ):
#                 by_period[key] = row

#         return sorted(
#             by_period.values(),
#             key=lambda row: (
#                 row.fiscal_year_end or "",
#                 row.period_end or "",
#                 row.disclose_date or "",
#             ),
#         )

#     def get_quarterly_values(self, rows):
#         """累計実績から単独四半期の値を算出する。"""
#         result = {}
#         order = {"1Q": 1, "2Q": 2, "3Q": 3, "4Q": 4, "FY": 4}
    
#         grouped = {}
#         for row in rows:
#             grouped.setdefault(row.fiscal_year_end, []).append(row)
    
#         for fiscal_end, fiscal_rows in grouped.items():
#             fiscal_rows.sort(
#                 key=lambda row: (
#                     order.get(row.period_type, 99),
#                     row.disclose_date or "",
#                     row.disclose_time or "",
#                 )
#             )
    
#             # 直前までに確認できた累計値
#             previous_sales = None
#             previous_op = None
#             previous_np = None
    
#             for row in fiscal_rows:
#                 period = row.period_type
    
#                 if period not in order:
#                     continue
                
#                 if period == "1Q":
#                     # 1Qは累計値と単独四半期値が一致する
#                     sales_q = row.net_sales
#                     op_q = row.op_income
#                     np_q = row.net_income
    
#                 elif period in ("2Q", "3Q"):
#                     # 前の累計値が欠けている場合、単独値を推定しない
#                     sales_q = (
#                         row.net_sales - previous_sales
#                         if row.net_sales is not None and previous_sales is not None
#                         else None
#                     )
#                     op_q = (
#                         row.op_income - previous_op
#                         if row.op_income is not None and previous_op is not None
#                         else None
#                     )
#                     np_q = (
#                         row.net_income - previous_np
#                         if row.net_income is not None and previous_np is not None
#                         else None
#                     )
    
#                 else:
#                     # 4Q / FYは通期累計から3Q累計を差し引く
#                     sales_q = (
#                         row.net_sales - previous_sales
#                         if row.net_sales is not None and previous_sales is not None
#                         else None
#                     )
#                     op_q = (
#                         row.op_income - previous_op
#                         if row.op_income is not None and previous_op is not None
#                         else None
#                     )
#                     np_q = (
#                         row.net_income - previous_np
#                         if row.net_income is not None and previous_np is not None
#                         else None
#                     )
    
#                 result[(fiscal_end, period)] = {
#                     "row": row,
#                     "sales_q": sales_q,
#                     "op_q": op_q,
#                     "np_q": np_q,
#                 }
    
#                 # 1Q〜3Qの累計値だけを次の期の差分計算に渡す。
#                 # FY / 4Qの後で累計値を更新しない。
#                 if period in ("1Q", "2Q", "3Q"):
#                     if row.net_sales is not None:
#                         previous_sales = row.net_sales
#                     if row.op_income is not None:
#                         previous_op = row.op_income
#                     if row.net_income is not None:
#                         previous_np = row.net_income
    
#         return result

#     def latest_forecast_for(
#         self,
#         code,
#         fiscal_year_end,
#         as_of_date,
#         as_of_time=None,
#     ):
#         """指定日時点で利用可能だった通期予想を取得する。"""

#         filters = [
#             EarningsEstimateHistory.code == code,
#             EarningsEstimateHistory.fiscal_year_end == fiscal_year_end,
#         ]

#         if as_of_time:
#             # 過去の日付の開示、または同日の指定時刻以前の開示
#             filters.append(
#                 or_(
#                     EarningsEstimateHistory.disclose_date < as_of_date,
#                     and_(
#                         EarningsEstimateHistory.disclose_date == as_of_date,
#                         EarningsEstimateHistory.disclose_time <= as_of_time,
#                     ),
#                 )
#             )
#         else:
#             # 開示時刻が不明なら、同日分は除外して未来情報の混入を防ぐ
#             filters.append(
#                 EarningsEstimateHistory.disclose_date < as_of_date
#             )

#         return (
#             self.db.query(EarningsEstimateHistory)
#             .filter(*filters)
#             .order_by(
#                 EarningsEstimateHistory.disclose_date.desc(),
#                 EarningsEstimateHistory.disclose_time.desc(),
#                 EarningsEstimateHistory.disc_no.desc(),
#             )
#             .first()
#         )


#     def build_screener(self):
#         master_data = self.load_master_data()
#         valuation_data = self.load_valuation_data()
#         earnings_dates = self.load_earnings_dates()

#         codes = [
#             row[0]
#             for row in self.db.query(
#                 FinancialHistory.code
#             ).distinct().all()
#         ]
#         print(f"[Metrics] 対象銘柄数: {len(codes)}")

#         results = []
#         for code in codes:
#             rows = self.get_actual_history(code)
#             if not rows:
#                 continue

#             quarterly = self.get_quarterly_values(rows)
#             current = rows[-1]
#             current_key = (current.fiscal_year_end, current.period_type)
#             current_q = quarterly.get(current_key)
#             if not current_q:
#                 continue

#             order = {"1Q": 1, "2Q": 2, "3Q": 3, "4Q": 4, "FY": 4}
#             current_order = order.get(current.period_type)

#             if current_order is None:
#                 continue
            
#             # 前年同期の単独四半期実績
#             prior_candidates = [
#                 value
#                 for (fy_end, period), value in quarterly.items()
#                 if period == current.period_type
#                 and fy_end < current.fiscal_year_end
#             ]
#             prior_q = (
#                 max(
#                     prior_candidates,
#                     key=lambda value: value["row"].fiscal_year_end or "",
#                 )
#                 if prior_candidates
#                 else None
#             )

#             # 直前の四半期を取得
#             if current_order == 1:
#                 # 1Qの前は前年度の4Q / FY
#                 prev_period_candidates = [
#                     value
#                     for (fy_end, period), value in quarterly.items()
#                     if fy_end < current.fiscal_year_end
#                     and period in ("4Q", "FY")
#                 ]
#             else:
#                 # 2Q以降は同一年度の直前の四半期
#                 prev_period_candidates = [
#                     value
#                     for (fy_end, period), value in quarterly.items()
#                     if fy_end == current.fiscal_year_end
#                     and period == f"{current_order - 1}Q"
#                 ]

#             prev_period = (
#                 max(
#                     prev_period_candidates,
#                     key=lambda value: (
#                         value["row"].fiscal_year_end or "",
#                         value["row"].period_end or "",
#                         value["row"].disclose_date or "",
#                         value["row"].disclose_time or "",
#                     ),
#                 )
#                 if prev_period_candidates
#                 else None
#             )

#             sales_yoy = self.calc_yoy(
#                 current_q["sales_q"],
#                 prior_q["sales_q"] if prior_q else None,
#             )
#             op_yoy = self.calc_yoy(
#                 current_q["op_q"],
#                 prior_q["op_q"] if prior_q else None,
#             )

#             prev_sales_yoy = None
#             prev_op_yoy = None

#             if prev_period:
#                 prev_period_type = prev_period["row"].period_type

#                 # 直前の四半期についても、前年の同じ期と比較する
#                 prev_year_candidates = [
#                     value
#                     for (fy_end, period), value in quarterly.items()
#                     if period == prev_period_type
#                     and fy_end < prev_period["row"].fiscal_year_end
#                 ]

#                 prev_year = (
#                     max(
#                         prev_year_candidates,
#                         key=lambda value: value["row"].fiscal_year_end or "",
#                     )
#                     if prev_year_candidates
#                     else None
#                 )

#                 prev_sales_yoy = self.calc_yoy(
#                     prev_period["sales_q"],
#                     prev_year["sales_q"] if prev_year else None,
#                 )
#                 prev_op_yoy = self.calc_yoy(
#                     prev_period["op_q"],
#                     prev_year["op_q"] if prev_year else None,
#                 )

#             sales_yoy_change = (
#                 sales_yoy - prev_sales_yoy
#                 if sales_yoy is not None and prev_sales_yoy is not None
#                 else None
#             )
#             op_yoy_change = (
#                 op_yoy - prev_op_yoy
#                 if op_yoy is not None and prev_op_yoy is not None
#                 else None
#             )

#             current_margin = self.calc_margin(
#                 current_q["op_q"], current_q["sales_q"]
#             )
#             prior_margin = (
#                 self.calc_margin(
#                     prior_q["op_q"], prior_q["sales_q"]
#                 )
#                 if prior_q
#                 else None
#             )
#             margin_change = (
#                 current_margin - prior_margin
#                 if current_margin is not None and prior_margin is not None
#                 else None
#             )

#             # 進捗率は四半期単独値ではなく累計実績 / 通期予想。
#             forecast = self.latest_forecast_for(
#                 code,
#                 current.fiscal_year_end,
#                 current.disclose_date,
#                 current.disclose_time,
#             )
#             progress = None
#             if (
#                 forecast
#                 and forecast.forecast_op_income not in (None, 0)
#                 and current.op_income is not None
#             ):
#                 progress = (
#                     current.op_income / forecast.forecast_op_income * 100
#                 )

#             # 過去の同じ期の進捗率。各年度のその期の開示時点で
#             # 利用可能だった予想を使い、現在の予想を過去に流用しない。
#             historical_progress = []
#             for (fy_end, period), values in quarterly.items():
#                 row = values["row"]
#                 if period != current.period_type or fy_end >= current.fiscal_year_end:
#                     continue

#                 past_forecast = self.latest_forecast_for(
#                     code,
#                     fy_end,
#                     row.disclose_date,
#                     row.disclose_time,
#                 )
#                 if (
#                     past_forecast
#                     and past_forecast.forecast_op_income not in (None, 0)
#                     and row.op_income is not None
#                 ):
#                     historical_progress.append(
#                         row.op_income / past_forecast.forecast_op_income * 100
#                     )

#             avg_progress = (
#                 sum(historical_progress) / len(historical_progress)
#                 if historical_progress
#                 else None
#             )
#             progress_diff = (
#                 progress - avg_progress
#                 if progress is not None and avg_progress is not None
#                 else None
#             )

#             # 赤字→黒字は成長率ではなく独立したフラグで扱う。
#             prior_op = prior_q["op_q"] if prior_q else None
#             current_op = current_q["op_q"]

#             existing = self.db.get(StockScreener, code)

#             master = master_data.get(code, {})
#             valuation = valuation_data.get(code, {})

#             company_name = (
#                 master.get("company_name")
#                 or (existing.company_name if existing else None)
#             )
#             sector = (
#                 master.get("sector")
#                 or (existing.sector if existing else None)
#             )

#             # APIの実際の列名に合わせて取得する
#             raw_market_cap = as_float(valuation.get("MktCap"))
#             raw_per = as_float(valuation.get("PER"))
#             raw_pbr = as_float(valuation.get("PBR"))

#             # API側の値が欠損している場合は既存値を保持する
#             market_cap = (
#                 raw_market_cap
#                 if raw_market_cap is not None
#                 else (existing.market_cap if existing else None)
#             )
#             per = (
#                 raw_per
#                 if raw_per is not None
#                 else (existing.per if existing else None)
#             )
#             pbr = (
#                 raw_pbr
#                 if raw_pbr is not None
#                 else (existing.pbr if existing else None)
#             )

#             next_earnings_date = (
#                 earnings_dates.get(code)
#                 or (
#                     existing.next_earnings_date
#                     if existing
#                     else None
#                 )
#             )

#             results.append({
#                 "code": code,
#                 "company_name": company_name,
#                 "sector": sector,
#                 "next_earnings_date": (
#                     next_earnings_date
#                     or (existing.next_earnings_date if existing else None)
#                 ),
#                 "market_cap": market_cap,
#                 "per": per,
#                 "pbr": pbr,
#                 "sales_yoy": sales_yoy,
#                 "op_yoy": op_yoy,
#                 "prev_sales_yoy": prev_sales_yoy,
#                 "prev_op_yoy": prev_op_yoy,
#                 "sales_yoy_change": sales_yoy_change,
#                 "op_yoy_change": op_yoy_change,
#                 "op_margin": current_margin,
#                 "prev_op_margin": prior_margin,
#                 "op_margin_change": margin_change,
#                 "progress_rate": progress,
#                 "avg_progress_rate": avg_progress,
#                 "progress_diff": progress_diff,
#                 "flag_growth_accel": bool(
#                     sales_yoy_change is not None
#                     and sales_yoy_change >= 5
#                     and sales_yoy is not None
#                     and sales_yoy > 0
#                 ),
#                 "flag_margin_imp": bool(
#                     margin_change is not None and margin_change >= 1
#                 ),
#                 "flag_turnaround": bool(
#                     prior_op is not None
#                     and prior_op < 0
#                     and current_op is not None
#                     and current_op > 0
#                 ),
#                 "flag_rapid_recover": bool(
#                     prev_sales_yoy is not None
#                     and prev_sales_yoy < 0
#                     and sales_yoy is not None
#                     and sales_yoy > 0
#                     and prev_op_yoy is not None
#                     and prev_op_yoy < 0
#                     and op_yoy is not None
#                     and op_yoy > 0
#                 ),
#                 "period_type": current.period_type,
#                 "updated_at": datetime.now(timezone.utc),
#             })

#         if not results:
#             print("[Metrics] 更新対象がありません。")
#             return

#         chunk_size = 500
#         for start in range(0, len(results), chunk_size):
#             chunk = results[start:start + chunk_size]
#             stmt = insert(StockScreener).values(chunk)
#             update_values = {
#                 key: getattr(stmt.excluded, key)
#                 for key in chunk[0]
#                 if key != "code"
#             }
#             stmt = stmt.on_conflict_do_update(
#                 index_elements=["code"],
#                 set_=update_values,
#             )
#             self.db.execute(stmt)

#         self.db.commit()
#         print(f"[Metrics] スクリーナー更新: {len(results)}銘柄")

#     def run(self):
#         try:
#             self.ensure_schema()
#             self.ingest_financial_summaries()
#             self.build_screener()
#             print("=== DWH構築完了 ===")
#         except Exception:
#             self.db.rollback()
#             raise
#         finally:
#             self.db.close()


# if __name__ == "__main__":
#     DWHBuilder().run()


# backend/build_dwh.py

import csv
import gzip
import io
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests
from requests.exceptions import HTTPError, RequestException
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import inspect, and_, or_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.jquants_client import JQuantsClient
from backend.db.database import SessionLocal, engine, Base
from backend.db.models import (
    FinancialHistory,
    EarningsEstimateHistory,
    StockScreener,
)
from backend.utils.finance import to_float, calc_yoy, calc_margin, normalize_code


def as_date(value):
    value = (value or "").strip()
    return value or None


class DWHBuilder:
    # 決算短信・業績予想修正などの履歴を保持する。
    # 既存テーブルを削除しない。
    def __init__(self):
        self.client = JQuantsClient()
        self.db = SessionLocal()


    def load_master_data(self):
            """銘柄名と業種を取得する。"""
            rows = self.get_all_pages("equities/master", {})
            result = {}
    
            for row in rows:
                code = normalize_code(row.get("Code"))
                if not code:
                    continue
                
                result[code] = {
                    "company_name": row.get("CoName"),
                    "sector": row.get("S33Nm") or row.get("S17Nm"),
                }
    
            print(f"[Master] 取得件数: {len(result)}")
            if rows:
                print("[Master] API列名:", list(rows[0].keys()))
    
            return result
    
    def load_valuation_data(self):
            """直近の取得可能な日付のバリュエーションを取得する。"""
            for offset in range(0, 10):
                target_date = date.today() - timedelta(days=offset)
    
                try:
                    rows = self.get_all_pages(
                        "equities/valuation",
                        {"date": target_date.isoformat()},
                    )
                except RuntimeError as exc:
                    print(f"[Valuation] APIエラー: {exc}")
                    return {}
    
                if not rows:
                    continue
                
                result = {}
                for row in rows:
                    code = normalize_code(row.get("Code"))
                    if not code:
                        continue
                    
                    result[code] = row
    
                print(
                    f"[Valuation] 日付={target_date.isoformat()}, "
                    f"取得件数={len(result)}"
                )
                print("[Valuation] API列名:", list(rows[0].keys()))
                return result
    
            print("[Valuation] 直近10日間に取得できるデータがありません")
            return {}
    
    def get_all_pages(self, endpoint, params=None):
            """pagination_key がなくなるまでAPIの全ページを取得する。"""
            query = dict(params or {})
            rows = []
    
            while True:
                result = self.get(endpoint, query)
                if not result:
                    break
                
                rows.extend(result.get("data", []))
    
                pagination_key = result.get("pagination_key")
                if not pagination_key:
                    break
                
                query["pagination_key"] = pagination_key
    
            return rows


    def ensure_schema(self):
        """新規テーブル作成と、既存SQLiteテーブルへのカラム追加。"""
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        with engine.begin() as conn:
            for model in (
                FinancialHistory,
                EarningsEstimateHistory,
                StockScreener,
            ):
                table = model.__table__
                if not inspector.has_table(table.name):
                    continue

                existing = {
                    col["name"]
                    for col in inspect(engine).get_columns(table.name)
                }

                for column in table.columns:
                    if column.name in existing:
                        continue

                    sql_type = column.type.compile(dialect=engine.dialect)
                    conn.exec_driver_sql(
                        f'ALTER TABLE "{table.name}" '
                        f'ADD COLUMN "{column.name}" {sql_type}'
                    )
                    print(f"[Migration] {table.name}.{column.name} を追加")

        Base.metadata.create_all(bind=engine)

    def get(self, endpoint, params=None, retries=4):
        """429や一時的な通信障害に対してバックオフ付きで再試行。"""
        for attempt in range(retries):
            try:
                return self.client.get(endpoint, params=params or {})
            except HTTPError as exc:
                status = exc.response.status_code if exc.response else None

                if status in (403, 404):
                    raise RuntimeError(
                        f"J-Quants APIのアクセスに失敗: "
                        f"{endpoint}, HTTP {status}"
                    ) from exc

                if status != 429 and (status is None or status < 500):
                    raise

                if attempt == retries - 1:
                    raise

                retry_after = (
                    exc.response.headers.get("Retry-After")
                    if exc.response
                    else None
                )
                try:
                    wait = float(retry_after) if retry_after else 2 ** (attempt + 1)
                except ValueError:
                    wait = 2 ** (attempt + 1)

                time.sleep(min(wait, 60))

            except RequestException:
                if attempt == retries - 1:
                    raise
                time.sleep(min(2 ** (attempt + 1), 30))

        raise RuntimeError(f"APIリトライ上限: {endpoint}")

    def download_csv(self, url):
        """署名付きURLからgzip CSVをダウンロード。APIキーは付けない。"""
        with requests.get(
            url,
            stream=True,
            timeout=(10, 120),
        ) as response:
            response.raise_for_status()
            with gzip.GzipFile(fileobj=response.raw) as gz:
                text = io.TextIOWrapper(
                    gz,
                    encoding="utf-8-sig",
                    newline="",
                )
                return list(csv.DictReader(text))

    def list_bulk_files(self, endpoint):
        """指定期間のBulkファイル一覧を取得。"""
        today = date.today()
        years = int(os.getenv("JQUANTS_HISTORY_YEARS", "3"))
        start = today - timedelta(days=365 * years)

        params = {
            "endpoint": endpoint,
            "from": start.isoformat(),
            "to": today.isoformat(),
        }
        result = self.get("bulk/list", params)
        files = result.get("data", []) if result else []

        files.sort(key=lambda item: item.get("LastModified", ""))

        limit = int(os.getenv("JQUANTS_BULK_FILE_LIMIT", "0"))
        if limit > 0:
            files = files[-limit:]

        return files

    def download_bulk_file(self, item):
        result = self.get("bulk/get", {"key": item["Key"]})
        if not result or not result.get("url"):
            raise RuntimeError(f"BulkダウンロードURLを取得できません: {item}")
        return self.download_csv(result["url"])

    def build_ids(self, row):
        code = normalize_code(row.get("Code"))
        disc_date = (row.get("DiscDate") or "").strip()
        disc_time = (row.get("DiscTime") or "").strip()
        disc_no = (row.get("DiscNo") or "").strip()
        doc_type = (row.get("DocType") or "").strip()
        period_type = (row.get("CurPerType") or "").strip()

        if not code or not disc_date:
            return None, None

        suffix = f"{disc_date}_{disc_time}_{disc_no}_{doc_type}_{period_type}"
        history_id = f"{code}_{suffix}"
        estimate_id = f"{code}_{disc_date}_{disc_time}_{disc_no}_{doc_type}"

        return history_id, estimate_id

    def parse_row(self, row):
        history_id, estimate_id = self.build_ids(row)
        if not history_id:
            return None, None

        code = normalize_code(row.get("Code"))
        disclose_date = (row.get("DiscDate") or "").strip()
        disclose_time = (row.get("DiscTime") or "").strip()
        disc_no = row.get("DiscNo") or None
        doc_type = (row.get("DocType") or "").strip()
        period_type = (row.get("CurPerType") or "").strip()

        now = datetime.now(timezone.utc)

        history = None

        if "financialstatements" in doc_type.lower():
            history = {
                "id": history_id,
                "code": code,
                "disclose_date": disclose_date,
                "disclose_time": disclose_time or None,
                "disc_no": disc_no,
                "doc_type": doc_type or None,
                "period_type": period_type or None,
                "period_start": as_date(row.get("CurPerSt")),
                "period_end": as_date(row.get("CurPerEn")),
                "fiscal_year_start": as_date(row.get("CurFYSt")),
                "fiscal_year_end": as_date(row.get("CurFYEn")),
                "net_sales": to_float(row.get("Sales")),
                "op_income": to_float(row.get("OP")),
                "net_income": to_float(row.get("NP")),
                "current_ytd_sales": to_float(row.get("Sales")),
                "current_ytd_op_income": to_float(row.get("OP")),
                "cfo": to_float(row.get("CFO")),
                "cfi": to_float(row.get("CFI")),
                "cff": to_float(row.get("CFF")),
                "updated_at": now,
            }

        forecast_sales = to_float(row.get("FSales"))
        forecast_op = to_float(row.get("FOP"))
        forecast_np = to_float(row.get("FNP"))

        estimate = None

        if any(
            value is not None
            for value in (forecast_sales, forecast_op, forecast_np)
        ):
            estimate = {
                "id": estimate_id,
                "code": code,
                "disclose_date": disclose_date,
                "disclose_time": disclose_time or None,
                "disc_no": disc_no,
                "doc_type": doc_type or None,
                "fiscal_year_start": as_date(row.get("CurFYSt")),
                "fiscal_year_end": as_date(row.get("CurFYEn")),
                "period_type": period_type or None,
                "forecast_net_sales": forecast_sales,
                "forecast_op_income": forecast_op,
                "forecast_net_income": forecast_np,
                "updated_at": now,
            }

        return history, estimate

    def save_history(self, history_records, estimate_records):
        """履歴を小分けに保存し、SQLiteの変数上限を回避する。"""
        chunk_size = 25

        def insert_chunks(model, records):
            inserted = 0

            for start in range(0, len(records), chunk_size):
                chunk = records[start:start + chunk_size]

                stmt = insert(model).values(chunk)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["id"]
                )

                self.db.execute(stmt)
                inserted += len(chunk)

            return inserted

        try:
            history_count = insert_chunks(
                FinancialHistory,
                history_records,
            )
            estimate_count = insert_chunks(
                EarningsEstimateHistory,
                estimate_records,
            )

            self.db.commit()

            print(
                f"[DB] 保存処理完了: "
                f"財務 {history_count}件、予想 {estimate_count}件"
            )

        except Exception as exc:
            self.db.rollback()

            print("[DB Error] 履歴保存に失敗しました")
            print(f"[DB Error] 例外型: {type(exc).__name__}")
            print(f"[DB Error] 詳細: {exc}")

            import traceback
            traceback.print_exc()

            raise

    def load_earnings_dates(self):
        """直近の決算発表予定日を銘柄ごとに取得する。"""
        today = date.today().isoformat()

        result = self.get(
            "fins/earnings-date",
            {"scheduled_date": today.replace("-", "")},
        )
        rows = (result.get("earnings_dates") or result.get("data") or []) if result else []

        earnings_dates = {}
        for row in rows:
            code = normalize_code(row.get("Code"))
            scheduled_date = (
                row.get("SchDate") or row.get("ScheduledDate")
            )

            if not code or not scheduled_date:
                continue

            old_date = earnings_dates.get(code)
            if old_date is None or scheduled_date < old_date:
                earnings_dates[code] = scheduled_date

        print(f"[Earnings] 本日発表予定データ: {len(earnings_dates)}件")
        return earnings_dates


    def ingest_financial_summaries(self):
        files = self.list_bulk_files("/fins/summary")
        print(f"[Bulk] /fins/summary: {len(files)} ファイル")

        for index, item in enumerate(files, start=1):
            key = item.get("Key")
            if not key:
                continue

            rows = self.download_bulk_file(item)
            history_records = []
            estimate_records = []

            for row in rows:
                history, estimate = self.parse_row(row)
                if history:
                    history_records.append(history)
                if estimate:
                    estimate_records.append(estimate)

            self.save_history(history_records, estimate_records)

            if index == 1 and rows:
                print("[Debug] CSV列名:", list(rows[0].keys()))

            if index % 10 == 0 or index == len(files):
                print(
                    f"[Bulk] {index}/{len(files)} "
                    f"履歴={self.db.query(FinancialHistory).count()} "
                    f"予想={self.db.query(EarningsEstimateHistory).count()}"
                )

    @staticmethod
    def standalone_value(current_cumulative, previous_cumulative):
        if current_cumulative is None:
            return None
        if previous_cumulative is None:
            return current_cumulative
        return current_cumulative - previous_cumulative

    @staticmethod
    def is_financial_statement(row):
        doc_type = (row.doc_type or "").lower()
        return "financialstatements" in doc_type

    def get_actual_history(self, code):
        """実績比較用の決算開示を会計年度・期別に整理する。"""
        rows = (
            self.db.query(FinancialHistory)
            .filter(FinancialHistory.code == code)
            .order_by(
                FinancialHistory.disclose_date.asc(),
                FinancialHistory.disclose_time.asc(),
            )
            .all()
        )

        by_period = {}
        for row in rows:
            if not self.is_financial_statement(row):
                continue
            if not row.fiscal_year_end or not row.period_type:
                continue

            key = (row.fiscal_year_end, row.period_type)
            old = by_period.get(key)
            if old is None or (
                row.disclose_date, row.disclose_time or ""
            ) > (
                old.disclose_date, old.disclose_time or ""
            ):
                by_period[key] = row

        return sorted(
            by_period.values(),
            key=lambda row: (
                row.fiscal_year_end or "",
                row.period_end or "",
                row.disclose_date or "",
            ),
        )

    def get_quarterly_values(self, rows):
        """累計実績から単独四半期の値を算出する。"""
        result = {}
        order = {"1Q": 1, "2Q": 2, "3Q": 3, "4Q": 4, "FY": 4}
    
        grouped = {}
        for row in rows:
            grouped.setdefault(row.fiscal_year_end, []).append(row)
    
        for fiscal_end, fiscal_rows in grouped.items():
            fiscal_rows.sort(
                key=lambda row: (
                    order.get(row.period_type, 99),
                    row.disclose_date or "",
                    row.disclose_time or "",
                )
            )
    
            previous_sales = None
            previous_op = None
            previous_np = None
    
            for row in fiscal_rows:
                period = row.period_type
    
                if period not in order:
                    continue
                
                if period == "1Q":
                    sales_q = row.net_sales
                    op_q = row.op_income
                    np_q = row.net_income
    
                elif period in ("2Q", "3Q"):
                    sales_q = (
                        row.net_sales - previous_sales
                        if row.net_sales is not None and previous_sales is not None
                        else None
                    )
                    op_q = (
                        row.op_income - previous_op
                        if row.op_income is not None and previous_op is not None
                        else None
                    )
                    np_q = (
                        row.net_income - previous_np
                        if row.net_income is not None and previous_np is not None
                        else None
                    )
    
                else:
                    sales_q = (
                        row.net_sales - previous_sales
                        if row.net_sales is not None and previous_sales is not None
                        else None
                    )
                    op_q = (
                        row.op_income - previous_op
                        if row.op_income is not None and previous_op is not None
                        else None
                    )
                    np_q = (
                        row.net_income - previous_np
                        if row.net_income is not None and previous_np is not None
                        else None
                    )
    
                result[(fiscal_end, period)] = {
                    "row": row,
                    "sales_q": sales_q,
                    "op_q": op_q,
                    "np_q": np_q,
                }
    
                if period in ("1Q", "2Q", "3Q"):
                    if row.net_sales is not None:
                        previous_sales = row.net_sales
                    if row.op_income is not None:
                        previous_op = row.op_income
                    if row.net_income is not None:
                        previous_np = row.net_income
    
        return result

    def latest_forecast_for(
        self,
        code,
        fiscal_year_end,
        as_of_date,
        as_of_time=None,
    ):
        """指定日時点で利用可能だった通期予想を取得する。"""

        filters = [
            EarningsEstimateHistory.code == code,
            EarningsEstimateHistory.fiscal_year_end == fiscal_year_end,
        ]

        if as_of_time:
            filters.append(
                or_(
                    EarningsEstimateHistory.disclose_date < as_of_date,
                    and_(
                        EarningsEstimateHistory.disclose_date == as_of_date,
                        EarningsEstimateHistory.disclose_time <= as_of_time,
                    ),
                )
            )
        else:
            filters.append(
                EarningsEstimateHistory.disclose_date < as_of_date
            )

        return (
            self.db.query(EarningsEstimateHistory)
            .filter(*filters)
            .order_by(
                EarningsEstimateHistory.disclose_date.desc(),
                EarningsEstimateHistory.disclose_time.desc(),
                EarningsEstimateHistory.disc_no.desc(),
            )
            .first()
        )


    def build_screener(self):
        master_data = self.load_master_data()
        valuation_data = self.load_valuation_data()
        earnings_dates = self.load_earnings_dates()

        codes = [
            row[0]
            for row in self.db.query(
                FinancialHistory.code
            ).distinct().all()
        ]
        print(f"[Metrics] 対象銘柄数: {len(codes)}")

        results = []
        for code in codes:
            rows = self.get_actual_history(code)
            if not rows:
                continue

            quarterly = self.get_quarterly_values(rows)
            current = rows[-1]
            current_key = (current.fiscal_year_end, current.period_type)
            current_q = quarterly.get(current_key)
            if not current_q:
                continue

            order = {"1Q": 1, "2Q": 2, "3Q": 3, "4Q": 4, "FY": 4}
            current_order = order.get(current.period_type)

            if current_order is None:
                continue
            
            prior_candidates = [
                value
                for (fy_end, period), value in quarterly.items()
                if period == current.period_type
                and fy_end < current.fiscal_year_end
            ]
            prior_q = (
                max(
                    prior_candidates,
                    key=lambda value: value["row"].fiscal_year_end or "",
                )
                if prior_candidates
                else None
            )

            if current_order == 1:
                prev_period_candidates = [
                    value
                    for (fy_end, period), value in quarterly.items()
                    if fy_end < current.fiscal_year_end
                    and period in ("4Q", "FY")
                ]
            else:
                prev_period_candidates = [
                    value
                    for (fy_end, period), value in quarterly.items()
                    if fy_end == current.fiscal_year_end
                    and period == f"{current_order - 1}Q"
                ]

            prev_period = (
                max(
                    prev_period_candidates,
                    key=lambda value: (
                        value["row"].fiscal_year_end or "",
                        value["row"].period_end or "",
                        value["row"].disclose_date or "",
                        value["row"].disclose_time or "",
                    ),
                )
                if prev_period_candidates
                else None
            )

            sales_yoy = calc_yoy(
                current_q["sales_q"],
                prior_q["sales_q"] if prior_q else None,
            )
            op_yoy = calc_yoy(
                current_q["op_q"],
                prior_q["op_q"] if prior_q else None,
            )

            prev_sales_yoy = None
            prev_op_yoy = None

            if prev_period:
                prev_period_type = prev_period["row"].period_type

                prev_year_candidates = [
                    value
                    for (fy_end, period), value in quarterly.items()
                    if period == prev_period_type
                    and fy_end < prev_period["row"].fiscal_year_end
                ]

                prev_year = (
                    max(
                        prev_year_candidates,
                        key=lambda value: value["row"].fiscal_year_end or "",
                    )
                    if prev_year_candidates
                    else None
                )

                prev_sales_yoy = calc_yoy(
                    prev_period["sales_q"],
                    prev_year["sales_q"] if prev_year else None,
                )
                prev_op_yoy = calc_yoy(
                    prev_period["op_q"],
                    prev_year["op_q"] if prev_year else None,
                )

            sales_yoy_change = (
                sales_yoy - prev_sales_yoy
                if sales_yoy is not None and prev_sales_yoy is not None
                else None
            )
            op_yoy_change = (
                op_yoy - prev_op_yoy
                if op_yoy is not None and prev_op_yoy is not None
                else None
            )

            current_margin = calc_margin(
                current_q["op_q"], current_q["sales_q"]
            )
            prior_margin = (
                calc_margin(
                    prior_q["op_q"], prior_q["sales_q"]
                )
                if prior_q
                else None
            )
            margin_change = (
                current_margin - prior_margin
                if current_margin is not None and prior_margin is not None
                else None
            )

            forecast = self.latest_forecast_for(
                code,
                current.fiscal_year_end,
                current.disclose_date,
                current.disclose_time,
            )
            progress = None
            if (
                forecast
                and forecast.forecast_op_income not in (None, 0)
                and current.op_income is not None
            ):
                progress = (
                    current.op_income / forecast.forecast_op_income * 100
                )

            historical_progress = []
            for (fy_end, period), values in quarterly.items():
                row = values["row"]
                if period != current.period_type or fy_end >= current.fiscal_year_end:
                    continue

                past_forecast = self.latest_forecast_for(
                    code,
                    fy_end,
                    row.disclose_date,
                    row.disclose_time,
                )
                if (
                    past_forecast
                    and past_forecast.forecast_op_income not in (None, 0)
                    and row.op_income is not None
                ):
                    historical_progress.append(
                        row.op_income / past_forecast.forecast_op_income * 100
                    )

            avg_progress = (
                sum(historical_progress) / len(historical_progress)
                if historical_progress
                else None
            )
            progress_diff = (
                progress - avg_progress
                if progress is not None and avg_progress is not None
                else None
            )

            prior_op = prior_q["op_q"] if prior_q else None
            current_op = current_q["op_q"]

            existing = self.db.get(StockScreener, code)

            master = master_data.get(code, {})
            valuation = valuation_data.get(code, {})

            company_name = (
                master.get("company_name")
                or (existing.company_name if existing else None)
            )
            sector = (
                master.get("sector")
                or (existing.sector if existing else None)
            )

            raw_market_cap = to_float(valuation.get("MktCap"))
            raw_per = to_float(valuation.get("PER"))
            raw_pbr = to_float(valuation.get("PBR"))

            market_cap = (
                raw_market_cap
                if raw_market_cap is not None
                else (existing.market_cap if existing else None)
            )
            per = (
                raw_per
                if raw_per is not None
                else (existing.per if existing else None)
            )
            pbr = (
                raw_pbr
                if raw_pbr is not None
                else (existing.pbr if existing else None)
            )

            next_earnings_date = (
                earnings_dates.get(code)
                or (
                    existing.next_earnings_date
                    if existing
                    else None
                )
            )

            results.append({
                "code": code,
                "company_name": company_name,
                "sector": sector,
                "next_earnings_date": (
                    next_earnings_date
                    or (existing.next_earnings_date if existing else None)
                ),
                "market_cap": market_cap,
                "per": per,
                "pbr": pbr,
                "sales_yoy": sales_yoy,
                "op_yoy": op_yoy,
                "prev_sales_yoy": prev_sales_yoy,
                "prev_op_yoy": prev_op_yoy,
                "sales_yoy_change": sales_yoy_change,
                "op_yoy_change": op_yoy_change,
                "op_margin": current_margin,
                "prev_op_margin": prior_margin,
                "op_margin_change": margin_change,
                "progress_rate": progress,
                "avg_progress_rate": avg_progress,
                "progress_diff": progress_diff,
                "flag_growth_accel": bool(
                    sales_yoy_change is not None
                    and sales_yoy_change >= 5
                    and sales_yoy is not None
                    and sales_yoy > 0
                ),
                "flag_margin_imp": bool(
                    margin_change is not None and margin_change >= 1
                ),
                "flag_turnaround": bool(
                    prior_op is not None
                    and prior_op < 0
                    and current_op is not None
                    and current_op > 0
                ),
                "flag_rapid_recover": bool(
                    prev_sales_yoy is not None
                    and prev_sales_yoy < 0
                    and sales_yoy is not None
                    and sales_yoy > 0
                    and prev_op_yoy is not None
                    and prev_op_yoy < 0
                    and op_yoy is not None
                    and op_yoy > 0
                ),
                "period_type": current.period_type,
                "updated_at": datetime.now(timezone.utc),
            })

        if not results:
            print("[Metrics] 更新対象がありません。")
            return

        chunk_size = 500
        for start in range(0, len(results), chunk_size):
            chunk = results[start:start + chunk_size]
            stmt = insert(StockScreener).values(chunk)
            update_values = {
                key: getattr(stmt.excluded, key)
                for key in chunk[0]
                if key != "code"
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["code"],
                set_=update_values,
            )
            self.db.execute(stmt)

        self.db.commit()
        print(f"[Metrics] スクリーナー更新: {len(results)}銘柄")

    def run(self):
        try:
            self.ensure_schema()
            self.ingest_financial_summaries()
            self.build_screener()
            print("=== DWH構築完了 ===")
        except Exception:
            self.db.rollback()
            raise
        finally:
            self.db.close()


if __name__ == "__main__":
    DWHBuilder().run()