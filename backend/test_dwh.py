
# backend/test_dwh.py
"""DWHのデータ取得・保存状況を確認するスモークテスト。

実行:
    python -m backend.test_dwh
"""

from collections import Counter

from sqlalchemy import func, inspect, text

from backend.db.database import SessionLocal, engine
from backend.db.models import (
    FinancialHistory,
    EarningsEstimateHistory,
    StockScreener,
)


def print_result(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")


def check_table_exists(db, model) -> bool:
    table_name = model.__tablename__
    exists = inspect(engine).has_table(table_name)
    print_result(
        f"テーブル存在: {table_name}",
        exists,
    )
    return exists


def check_count(db, model) -> int:
    count = db.query(func.count()).select_from(model).scalar() or 0
    print_result(
        f"データ件数: {model.__tablename__}",
        count > 0,
        f"{count:,}件",
    )
    return count


def check_financial_history(db, count: int) -> None:
    if count == 0:
        print_result("財務データの内容", False, "データがありません")
        return

    latest_date = (
        db.query(func.max(FinancialHistory.disclose_date)).scalar()
    )
    code_count = (
        db.query(func.count(func.distinct(FinancialHistory.code))).scalar()
    )

    print_result(
        "財務データの開示日",
        latest_date is not None,
        str(latest_date),
    )
    print_result(
        "財務データの銘柄数",
        code_count > 0,
        f"{code_count:,}銘柄",
    )

    # 主要な財務数値が入っているレコードを確認
    actual_count = (
        db.query(func.count())
        .select_from(FinancialHistory)
        .filter(
            (FinancialHistory.net_sales.isnot(None))
            | (FinancialHistory.op_income.isnot(None))
            | (FinancialHistory.net_income.isnot(None))
        )
        .scalar()
        or 0
    )

    print_result(
        "財務数値が存在するレコード",
        actual_count > 0,
        f"{actual_count:,}件",
    )

    # 直近のデータを表示
    samples = (
        db.query(FinancialHistory)
        .order_by(
            FinancialHistory.disclose_date.desc(),
            FinancialHistory.code,
        )
        .limit(5)
        .all()
    )

    print("\n--- 財務データのサンプル（最大5件） ---")
    for row in samples:
        print(
            f"code={row.code}, "
            f"date={row.disclose_date}, "
            f"period={row.period_type}, "
            f"sales={row.net_sales}, "
            f"op={row.op_income}, "
            f"net_income={row.net_income}"
        )


def check_estimates(db, count: int) -> None:
    if count == 0:
        print_result("業績予想データ", False, "データがありません")
        return

    latest_date = (
        db.query(func.max(EarningsEstimateHistory.disclose_date)).scalar()
    )
    forecast_count = (
        db.query(func.count())
        .select_from(EarningsEstimateHistory)
        .filter(
            (EarningsEstimateHistory.forecast_net_sales.isnot(None))
            | (EarningsEstimateHistory.forecast_op_income.isnot(None))
            | (EarningsEstimateHistory.forecast_net_income.isnot(None))
        )
        .scalar()
        or 0
    )

    print_result(
        "業績予想の開示日",
        latest_date is not None,
        str(latest_date),
    )
    print_result(
        "業績予想の数値",
        forecast_count > 0,
        f"{forecast_count:,}件",
    )

    samples = (
        db.query(EarningsEstimateHistory)
        .order_by(
            EarningsEstimateHistory.disclose_date.desc(),
            EarningsEstimateHistory.code,
        )
        .limit(5)
        .all()
    )

    print("\n--- 業績予想のサンプル（最大5件） ---")
    for row in samples:
        print(
            f"code={row.code}, "
            f"date={row.disclose_date}, "
            f"sales={row.forecast_net_sales}, "
            f"op={row.forecast_op_income}, "
            f"net_income={row.forecast_net_income}"
        )


def check_screener(db, count: int) -> None:
    if count == 0:
        print_result("スクリーナーデータ", False, "データがありません")
        return

    samples = (
        db.query(StockScreener)
        .order_by(StockScreener.code)
        .limit(5)
        .all()
    )

    # 全件数と、主要指標が設定されている件数を確認
    metric_count = (
        db.query(func.count())
        .select_from(StockScreener)
        .filter(
            StockScreener.sales_yoy.isnot(None)
            | StockScreener.op_yoy.isnot(None)
            | StockScreener.market_cap.isnot(None)
        )
        .scalar()
        or 0
    )

    print_result(
        "スクリーナーの主要指標",
        metric_count > 0,
        f"{metric_count:,}/{count:,}件",
    )

    print("\n--- スクリーナーのサンプル（最大5件） ---")
    for row in samples:
        print(
            f"code={row.code}, "
            f"name={row.company_name}, "
            f"market_cap={row.market_cap}, "
            f"sales_yoy={row.sales_yoy}, "
            f"op_yoy={row.op_yoy}, "
            f"next_earnings_date={row.next_earnings_date}"
        )


def check_missing_screener_data(db):
    total = db.query(func.count()).select_from(StockScreener).scalar() or 0

    fields = {
        "会社名": StockScreener.company_name,
        "時価総額": StockScreener.market_cap,
        "PER": StockScreener.per,
        "PBR": StockScreener.pbr,
        "売上成長率": StockScreener.sales_yoy,
        "営業利益成長率": StockScreener.op_yoy,
        "次回決算日": StockScreener.next_earnings_date,
    }

    print("\n--- スクリーナー NULL率 ---")
    for label, column in fields.items():
        missing = (
            db.query(func.count())
            .select_from(StockScreener)
            .filter(column.is_(None))
            .scalar()
            or 0
        )
        rate = missing / total * 100 if total else 0
        print(f"{label}: {missing:,}/{total:,}件 ({rate:.1f}%)")

    print("\n--- 会社名・時価総額がNULLの銘柄例 ---")
    rows = (
        db.query(StockScreener)
        .filter(
            StockScreener.company_name.is_(None)
            | StockScreener.market_cap.is_(None)
        )
        .limit(10)
        .all()
    )

    for row in rows:
        print(
            f"code={row.code}, "
            f"name={row.company_name}, "
            f"market_cap={row.market_cap}"
        )


def main() -> int:
    print("========================================")
    print(" DWH データ取得・保存チェック")
    print("========================================")

    failed = False

    # DBへの接続を確認
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print_result("DB接続", True)
    except Exception as exc:
        print_result("DB接続", False, str(exc))
        return 1

    db = SessionLocal()

    try:
        models = [
            FinancialHistory,
            EarningsEstimateHistory,
            StockScreener,
        ]

        # テーブルの存在確認
        table_results = {
            model.__tablename__: check_table_exists(db, model)
            for model in models
        }

        if not all(table_results.values()):
            print("\nテーブルが不足しています。先にDWHの初期化処理を確認してください。")
            return 1

        # レコード件数
        counts = {
            model.__tablename__: check_count(db, model)
            for model in models
        }

        check_financial_history(
            db, counts[FinancialHistory.__tablename__]
        )
        check_estimates(
            db, counts[EarningsEstimateHistory.__tablename__]
        )
        check_screener(
            db, counts[StockScreener.__tablename__]
        )

        # 財務データと予想データが同じ銘柄コード形式か確認
        actual_codes = {
            code
            for (code,) in db.query(FinancialHistory.code).distinct().all()
        }
        estimate_codes = {
            code
            for (code,) in db.query(
                EarningsEstimateHistory.code
            ).distinct().all()
        }

        common_codes = actual_codes & estimate_codes
        print_result(
            "財務データと予想データの銘柄コード一致",
            bool(common_codes),
            f"共通 {len(common_codes):,}銘柄",
        )

        # 期間区分の偏りを確認
        period_counts = Counter(
            period or "(NULL)"
            for (period,) in db.query(
                FinancialHistory.period_type
            ).all()
        )
        print("\n--- 期間区分の内訳 ---")
        for period, count in sorted(period_counts.items()):
            print(f"{period}: {count:,}件")

        # 全テーブルで最低限データがあるか確認
        failed = any(count == 0 for count in counts.values())

    except Exception as exc:
        print_result("テスト実行", False, f"{type(exc).__name__}: {exc}")
        raise
    finally:
        db.close()

    print("\n--- 実績数値がすべてNULLのレコード ---")
    
    rows = (
        db.query(FinancialHistory)
        .filter(
            FinancialHistory.net_sales.is_(None),
            FinancialHistory.op_income.is_(None),
            FinancialHistory.net_income.is_(None),
        )
        .order_by(FinancialHistory.disclose_date.desc())
        .limit(10)
        .all()
    )
    
    for row in rows:
        print(
            f"code={row.code}, "
            f"date={row.disclose_date}, "
            f"period={row.period_type}, "
            f"doc_type={getattr(row, 'doc_type', None)}"
        )

    print("\n========================================")
    if failed:
        print("結果: FAIL（データが入っていないテーブルがあります）")
        return 1

    print("結果: PASS（最低限のデータ保存を確認しました）")
    print("※ 数値の正確性や成長率の計算までは保証しません。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
