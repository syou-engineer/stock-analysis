# backend/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone, date
import traceback
from backend.core.jquants_client import JQuantsClient
from backend.db.database import engine, Base, get_db
from backend.db.models import StockCache, StockScreener, EarningsEstimateHistory
from backend.services.fetcher import JQuantsFetcher
from backend.services.analyzer import calculate_analysis

# SQLiteにテーブルを作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Dashboard API")

# フロントエンド(React)からのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fetcher = JQuantsFetcher()
jq_client = JQuantsClient()

SECTOR_INDEX_MAP = {
    "水産・農林業": "0040", "鉱業": "0041", "建設業": "0042", "食料品": "0043",
    "繊維製品": "0044", "パルプ・紙": "0045", "化学": "0046", "医薬品": "0047",
    "石油・石炭製品": "0048", "ゴム製品": "0049", "ガラス・土石製品": "004A",
    "鉄鋼": "004B", "非鉄金属": "004C", "金属製品": "004D", "機械": "004E",
    "電気機器": "004F", "輸送用機器": "0050", "精密機器": "0051", "その他製品": "0052",
    "電気・ガス業": "0053", "陸運業": "0054", "海運業": "0055", "空運業": "0056",
    "倉庫・運輸関連業": "0057", "情報・通信業": "0058", "卸売業": "0059",
    "小売業": "005A", "銀行業": "005B", "証券・商品先物取引業": "005C",
    "保険業": "005D", "その他金融業": "005E", "不動産業": "005F", "サービス業": "0060"
}

# 指数専用の独立キャッシュマネージャー
def get_or_fetch_index(index_code: str, force_refresh: bool, db: Session):
    cache_code = f"IDX_{index_code}"
    cache = db.query(StockCache).filter(StockCache.code == cache_code).first()
    now_utc = datetime.now(timezone.utc)
    
    if cache and not force_refresh:
        updated_at = cache.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        if now_utc - updated_at < timedelta(hours=24):
            print(f"[INDEX:{index_code}] DBキャッシュから指数データを秒速取得しました。")
            return cache.profile_data.get("data", [])
            
    print(f"[INDEX:{index_code}] APIから新たに指数を取得します...")
    try:
        data = fetcher.fetch_index(index_code)
    except Exception as e:
        print(f"[INDEX:{index_code}] 取得エラー: {e}")
        data = []
        
    final_data = {"data": data}
    
    if cache:
        cache.profile_data = final_data
        cache.updated_at = now_utc
    else:
        new_cache = StockCache(code=cache_code, profile_data=final_data, updated_at=now_utc)
        db.add(new_cache)
    db.commit()
    return data

def normalize_period_type(value: str | None) -> str:
    value = str(value or "").strip().upper()
    aliases = {
        "1Q": ("1Q", "第1四半期", "第一四半期"),
        "2Q": ("2Q", "第2四半期", "第二四半期"),
        "3Q": ("3Q", "第3四半期", "第三四半期"),
        "4Q": ("4Q", "第4四半期", "第四四半期"),
        "FY": ("FY", "通期", "本決算"),
    }
    for normalized, candidates in aliases.items():
        if any(candidate in value for candidate in candidates):
            return normalized
    return value


def get_prior_year_revision(code: str, scheduled_date: str, scheduled_period: str, estimates_by_code: dict) -> dict:
    try:
        target_date = date.fromisoformat(scheduled_date)
        prior_year_date = target_date - timedelta(days=365)
    except (TypeError, ValueError):
        return {"status": "判定不可", "metric": None, "previous_value": None, "current_value": None}

    target_period = normalize_period_type(scheduled_period)
    window_start = (prior_year_date - timedelta(days=45)).isoformat()
    window_end = (prior_year_date + timedelta(days=45)).isoformat()

    rows = estimates_by_code.get(str(code).strip(), [])
    candidates = [
        row for row in rows
        if normalize_period_type(row.period_type) == target_period
        and row.disclose_date
        and window_start <= row.disclose_date <= window_end
        and row.fiscal_year_end
    ]
    candidates.sort(key=lambda row: (row.disclose_date or "", row.disclose_time or "", row.disc_no or ""))

    metrics = (
        ("営業利益", "forecast_op_income"),
        ("売上高", "forecast_net_sales"),
        ("純利益", "forecast_net_income"),
    )

    for current in reversed(candidates):
        previous_rows = [
            row for row in rows
            if row.fiscal_year_end == current.fiscal_year_end
            and ((row.disclose_date or "", row.disclose_time or "", row.disc_no or "") < (current.disclose_date or "", current.disclose_time or "", current.disc_no or ""))
        ]
        previous_rows.sort(key=lambda row: (row.disclose_date or "", row.disclose_time or "", row.disc_no or ""), reverse=True)

        for label, field in metrics:
            current_value = getattr(current, field, None)
            if current_value is None: continue
            previous_value = next((getattr(row, field, None) for row in previous_rows if getattr(row, field, None) is not None), None)
            if previous_value is None: continue

            if current_value > previous_value: status = "上方修正"
            elif current_value < previous_value: status = "下方修正"
            else: status = "据え置き"

            return {"status": status, "metric": label, "previous_value": previous_value, "current_value": current_value}

    return {"status": "判定不可", "metric": None, "previous_value": None, "current_value": None}

@app.get("/api/stocks/{code}")
def get_stock_data(code: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    if len(code) == 4:
        code += "0"
        
    cache = db.query(StockCache).filter(StockCache.code == code).first()
    now_utc = datetime.now(timezone.utc)
    
    is_cache_valid = False
    if cache and not force_refresh:
        updated_at = cache.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        if now_utc - updated_at < timedelta(hours=24):
            cached_data = cache.profile_data
            history = cached_data.get("analysis", {}).get("price_margin_history", [])
            if history and history[-1].get("topix") is not None and history[-1].get("sector") is not None:
                is_cache_valid = True
                
    if is_cache_valid:
        print(f"[{code}] DBキャッシュからデータを返却します。")
        return cache.profile_data

    print(f"[{code}] データをAPIから再構築します...")
    try:
        raw_profile = fetcher.fetch_full_profile(code)
        
        topix_data = get_or_fetch_index("0000", force_refresh, db)
        raw_profile["topix_daily"] = topix_data
        
        info = raw_profile.get("info", {})
        sector_name = info.get("Sector33CodeName") or info.get("S33Nm") or info.get("Sector17CodeName") or info.get("S17Nm") or ""
        sector_name = str(sector_name).strip().replace("\u200b", "")
        sector_code = SECTOR_INDEX_MAP.get(sector_name)
        
        if sector_code:
            sector_data = get_or_fetch_index(sector_code, force_refresh, db)
            raw_profile["sector_daily"] = sector_data
        else:
            print(f"[{code}] 業種名 '{sector_name}' に合致する指数コードが見つかりませんでした。")
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")
    
    analysis_data = calculate_analysis(raw_profile)
    
    final_data = {
        "raw": raw_profile,
        "analysis": analysis_data
    }
    
    if cache:
        cache.profile_data = final_data
        cache.updated_at = now_utc
    else:
        new_cache = StockCache(code=code, profile_data=final_data, updated_at=now_utc)
        db.add(new_cache)
    
    db.commit()
    print(f"[{code}] J-Quantsから取得し、DBキャッシュを更新しました。")
    
    return final_data

@app.get("/api/calendar/earnings")
def get_earnings_calendar(date: str, db: Session = Depends(get_db)):
    print(f"検索対象日付: {date}")
    try:
        formatted_date = date.replace("-", "")
        params = {"scheduled_date": formatted_date}
        earnings_list = []

        while True:
            res = jq_client.get("fins/earnings-date", params)
            chunk = res.get("earnings_dates") or res.get("announcement") or res.get("data") or []
            earnings_list.extend(chunk)

            pagination_key = res.get("pagination_key")
            if not pagination_key:
                break
            params["pagination_key"] = pagination_key

    except Exception as e:
        print(f"J-Quants API エラー: {e}")
        raise HTTPException(status_code=502, detail="決算予定日の取得に失敗しました") from e

    if not earnings_list:
        return {"items": []}

    target_codes_4digit = list({str(item["Code"]).strip()[:4] for item in earnings_list if item.get("Code")})

    estimate_records = (
        db.query(EarningsEstimateHistory)
        .filter(EarningsEstimateHistory.code.in_(target_codes_4digit))
        .order_by(EarningsEstimateHistory.code, EarningsEstimateHistory.disclose_date, EarningsEstimateHistory.disclose_time, EarningsEstimateHistory.disc_no)
        .all()
    )

    estimates_by_code = {}
    for estimate in estimate_records:
        code = str(estimate.code).strip()
        estimates_by_code.setdefault(code, []).append(estimate)

    screener_records = db.query(StockScreener).filter(StockScreener.code.in_(target_codes_4digit)).all()
    db_dict = {str(s.code).strip(): s for s in screener_records}

    items = []
    for item in earnings_list:
        original_code = str(item.get("Code", "")).strip()
        if not original_code: continue
        db_code = original_code[:4]
        s = db_dict.get(db_code)

        try:
            revision = get_prior_year_revision(
                code=db_code,
                scheduled_date=date,
                scheduled_period=item.get("QuarterName") or item.get("FQName", ""),
                estimates_by_code=estimates_by_code,
            )
        except NameError:
            revision = {"status": "unchanged", "metric": None, "previous_value": None, "current_value": None}

        items.append({
            "code": original_code, 
            "name": s.company_name if s and s.company_name else item.get("CompanyName", item.get("CoName", "名称取得中...")),
            "period_type": item.get("QuarterName", item.get("FQName", s.period_type if s else "")),
            "market_cap": getattr(s, "market_cap", None),
            "sales_yoy": getattr(s, "sales_yoy", None),
            "op_yoy": getattr(s, "op_yoy", None),
            "sales_yoy_change": getattr(s, "sales_yoy_change", None),
            "op_margin": getattr(s, "op_margin", None),
            "op_margin_change": getattr(s, "op_margin_change", None),
            "progress_rate": getattr(s, "progress_rate", None),
            "avg_progress_rate": getattr(s, "avg_progress_rate", None),
            "progress_diff": getattr(s, "progress_diff", None),
            "flag_growth_accel": getattr(s, "flag_growth_accel", False),
            "flag_margin_imp": getattr(s, "flag_margin_imp", False),
            "flag_turnaround": getattr(s, "flag_turnaround", False),
            "flag_rapid_recover": getattr(s, "flag_rapid_recover", False),
            "industry": getattr(s, "sector", None),
            "prior_year_revision": revision.get("status"),
            "prior_year_revision_metric": revision.get("metric"),
            "prior_year_revision_previous": revision.get("previous_value"),
            "prior_year_revision_current": revision.get("current_value"),
        })

    return {"items": items}