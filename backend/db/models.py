# backend/models.py

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    String,
    JSON,
)
from datetime import datetime, timezone
from backend.db.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class StockCache(Base):
    __tablename__ = "stock_cache"
    
    code = Column(String, primary_key=True, index=True)
    # キャッシュの更新日時
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # J-Quantsの生データと分析結果をまとめたJSON
    profile_data = Column(JSON)


class FinancialHistory(Base):
    __tablename__ = "financial_history"

    # 1開示につき1レコード。過去の開示は上書きしない。
    id = Column(String, primary_key=True)
    code = Column(String, index=True, nullable=False)
    disclose_date = Column(String, index=True, nullable=False)
    disclose_time = Column(String)
    disc_no = Column(String)
    doc_type = Column(String)
    period_type = Column(String)

    period_start = Column(String)
    period_end = Column(String)
    fiscal_year_start = Column(String)
    fiscal_year_end = Column(String)

    # CSVのSales / OP / NP。累計値かどうかは期間とセットで判断する。
    net_sales = Column(Float)
    op_income = Column(Float)
    net_income = Column(Float)

    current_ytd_sales = Column(Float)
    current_ytd_op_income = Column(Float)

    # キャッシュフロー（提供されている場合）
    cfo = Column(Float)
    cfi = Column(Float)
    cff = Column(Float)

    updated_at = Column(DateTime, default=utc_now, nullable=False)


class EarningsEstimateHistory(Base):
    __tablename__ = "earnings_estimate_history"

    # 1開示につき1レコード。予想修正の履歴を保持する。
    id = Column(String, primary_key=True)
    code = Column(String, index=True, nullable=False)
    disclose_date = Column(String, index=True, nullable=False)
    disclose_time = Column(String)
    disc_no = Column(String)
    doc_type = Column(String)

    fiscal_year_start = Column(String)
    fiscal_year_end = Column(String)
    period_type = Column(String)

    forecast_net_sales = Column(Float)
    forecast_op_income = Column(Float)
    forecast_net_income = Column(Float)

    updated_at = Column(DateTime, default=utc_now, nullable=False)


class StockScreener(Base):
    __tablename__ = "stock_screener"

    code = Column(String, primary_key=True)
    company_name = Column(String)
    sector = Column(String)

    market_cap = Column(Float)
    per = Column(Float)
    pbr = Column(Float)

    sales_yoy = Column(Float)
    op_yoy = Column(Float)
    prev_sales_yoy = Column(Float)
    prev_op_yoy = Column(Float)
    sales_yoy_change = Column(Float)
    op_yoy_change = Column(Float)

    op_margin = Column(Float)
    prev_op_margin = Column(Float)
    op_margin_change = Column(Float)

    progress_rate = Column(Float)
    avg_progress_rate = Column(Float)
    progress_diff = Column(Float)

    flag_growth_accel = Column(Boolean, default=False, nullable=False)
    flag_margin_imp = Column(Boolean, default=False, nullable=False)
    flag_turnaround = Column(Boolean, default=False, nullable=False)
    flag_rapid_recover = Column(Boolean, default=False, nullable=False)

    next_earnings_date = Column(String)
    period_type = Column(String)
    updated_at = Column(DateTime, default=utc_now, nullable=False)