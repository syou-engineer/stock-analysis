
import argparse
import time
from pathlib import Path

import pandas as pd
from backend.services.fetcher import JQuantsFetcher


MARGIN_ENDPOINT = "markets/margin-interest"
PRICE_ENDPOINT = "equities/bars/daily"


def normalize_code(value):
    """証券コードを文字列に統一する。"""
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value


def find_column(df, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    return None


def fetch_margin(client, start_date, end_date):
    """
    まず期間指定で取得する。
    APIが期間指定を受け付けない場合は日付指定で試す。
    """
    try:
        rows = client.get_all_pages(
            MARGIN_ENDPOINT,
            {
                "from": start_date,
                "to": end_date,
            },
        )
        if rows:
            return pd.DataFrame(rows)
    except Exception as exc:
        print(f"期間指定での取得に失敗: {exc}")

    print("日付単位で取得します。")
    records = []

    for date in pd.date_range(start_date, end_date):
        date_str = date.strftime("%Y-%m-%d")

        try:
            rows = client.get_all_pages(
                MARGIN_ENDPOINT,
                {"date": date_str},
            )
            records.extend(rows)

            if rows:
                print(f"{date_str}: {len(rows)}件")

        except Exception as exc:
            print(f"{date_str}: 取得できませんでした ({exc})")

        time.sleep(0.1)

    if not records:
        raise RuntimeError(
            "信用残データを取得できませんでした。"
            "APIのパラメータと利用プランを確認してください。"
        )

    return pd.DataFrame(records)


def fetch_prices(client, codes, start_date, end_date):
    """銘柄ごとに日足株価を取得する。"""
    records = []

    for index, code in enumerate(codes, start=1):
        try:
            rows = client.get_all_pages(
                PRICE_ENDPOINT,
                {
                    "code": code,
                    "from": start_date,
                    "to": end_date,
                },
            )
            records.extend(rows)

        except Exception as exc:
            print(f"株価取得失敗 {code}: {exc}")

        if index % 10 == 0 or index == len(codes):
            print(f"株価取得: {index}/{len(codes)}銘柄")

        time.sleep(0.1)

    return pd.DataFrame(records)


def prepare_margin(df):
    df = df.copy()

    date_col = find_column(df, ["Date", "date"])
    code_col = find_column(df, ["Code", "code"])

    if not date_col or not code_col:
        raise ValueError(
            f"信用残のDate/Code列が見つかりません: "
            f"{df.columns.tolist()}"
        )

    df["Date"] = pd.to_datetime(
        df[date_col], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["Code"] = df[code_col].map(normalize_code)

    numeric_columns = [
        "LongVol", "ShrtVol",
        "LongNegVol", "ShrtNegVol",
        "LongStdVol", "ShrtStdVol",
        "LongVal", "ShrtVal",
        "LongNegVal", "ShrtNegVal",
        "LongStdVal", "ShrtStdVal",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

    # IssTypeが存在する場合は残す。
    keys = ["Date", "Code"]
    if "IssType" in df.columns:
        keys.append("IssType")

    return df.drop_duplicates(subset=keys)


def prepare_prices(df):
    if df.empty:
        raise ValueError(
            "株価データがありません。APIのエンドポイントを確認してください。"
        )

    date_col = find_column(df, ["Date", "date"])
    code_col = find_column(df, ["Code", "code"])
    close_col = find_column(
        df, ["C", "Close", "close"]
    )

    if not date_col or not code_col or not close_col:
        raise ValueError(
            f"株価の日付・コード・終値列が見つかりません: "
            f"{df.columns.tolist()}"
        )

    result = pd.DataFrame({
        "Date": pd.to_datetime(
            df[date_col], errors="coerce"
        ).dt.strftime("%Y-%m-%d"),
        "Code": df[code_col].map(normalize_code),
        "Close": pd.to_numeric(
            df[close_col], errors="coerce"
        ),
    })

    volume_col = find_column(df, ["Vo", "Volume", "volume"])
    value_col = find_column(df, ["Va", "TurnoverValue"])

    if volume_col:
        result["PriceVolume"] = pd.to_numeric(
            df[volume_col], errors="coerce"
        )

    if value_col:
        result["TurnoverValue"] = pd.to_numeric(
            df[value_col], errors="coerce"
        )

    return result.drop_duplicates(
        subset=["Date", "Code"]
    )


def calculate_metrics(df):
    df = df.copy()

    # 金額 / 株数
    ratio_specs = [
        ("LongVal", "LongVol", "LongAmountPerShare"),
        ("ShrtVal", "ShrtVol", "ShortAmountPerShare"),
        (
            "LongNegVal",
            "LongNegVol",
            "LongGeneralAmountPerShare",
        ),
        (
            "ShrtNegVal",
            "ShrtNegVol",
            "ShortGeneralAmountPerShare",
        ),
        (
            "LongStdVal",
            "LongStdVol",
            "LongSystemAmountPerShare",
        ),
        (
            "ShrtStdVal",
            "ShrtStdVol",
            "ShortSystemAmountPerShare",
        ),
    ]

    for amount_col, volume_col, output_col in ratio_specs:
        if amount_col not in df.columns:
            continue
        if volume_col not in df.columns:
            continue

        volume = df[volume_col].where(df[volume_col] > 0)
        df[output_col] = df[amount_col] / volume

        # 終値との乖離率。取得単価と断定しない。
        if "Close" in df.columns:
            df[output_col + "VsClosePct"] = (
                df[output_col] / df["Close"] - 1
            ) * 100

    # 時系列変化
    df = df.sort_values(["Code", "Date"])

    change_columns = [
        "Close",
        "LongVol", "ShrtVol",
        "LongVal", "ShrtVal",
        "LongAmountPerShare",
        "ShortAmountPerShare",
    ]

    for col in change_columns:
        if col not in df.columns:
            continue

        grouped = df.groupby("Code")[col]

        df[f"{col}Change"] = grouped.diff()
        df[f"{col}ChangePct"] = grouped.pct_change() * 100

    return df


def create_summary(df):
    rows = []

    for code, group in df.groupby("Code"):
        row = {
            "Code": code,
            "Rows": len(group),
        }

        if "LongAmountPerShare" in group.columns:
            valid = group[
                group["LongAmountPerShare"].notna()
                & group["Close"].notna()
                & (group["Close"] > 0)
            ]

            if not valid.empty:
                deviation = (
                    valid["LongAmountPerShare"]
                    / valid["Close"] - 1
                ) * 100

                row["LongRatioMedianVsClosePct"] = (
                    deviation.median()
                )
                row["LongRatioMedianAbsDeviationPct"] = (
                    deviation.abs().median()
                )

                if len(valid) >= 3:
                    row["LongRatioCloseCorrelation"] = (
                        valid["LongAmountPerShare"]
                        .corr(valid["Close"])
                    )

        rows.append(row)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--from-date",
        default="2026-09-25",
    )
    parser.add_argument(
        "--to-date",
        default="2026-10-10",
    )
    parser.add_argument(
        "--codes",
        default="",
        help="例: 72030,83060,68570",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="コード指定なしの場合に株価取得する銘柄数",
    )
    parser.add_argument(
        "--out-dir",
        default="margin_validation",
    )

    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = JQuantsClient()

    print("信用残データを取得します...")
    margin_raw = fetch_margin(
        client,
        args.from_date,
        args.to_date,
    )
    margin_raw.to_csv(
        out_dir / "margin_raw.csv",
        index=False,
        encoding="utf-8-sig",
    )

    margin = prepare_margin(margin_raw)

    if args.codes.strip():
        codes = [
            normalize_code(x)
            for x in args.codes.split(",")
            if x.strip()
        ]
    else:
        # 最新日付の信用買い残金額が大きい銘柄を選ぶ。
        latest_date = margin["Date"].max()
        latest = margin[margin["Date"] == latest_date].copy()

        if "LongVal" in latest.columns:
            latest = latest.sort_values(
                "LongVal", ascending=False
            )

        codes = (
            latest["Code"]
            .drop_duplicates()
            .head(args.top_n)
            .tolist()
        )

    margin = margin[margin["Code"].isin(codes)].copy()

    if margin.empty:
        raise RuntimeError("対象銘柄の信用残がありません。")

    print(f"対象銘柄数: {len(codes)}")

    print("日足株価を取得します...")
    prices_raw = fetch_prices(
        client,
        codes,
        args.from_date,
        args.to_date,
    )
    prices_raw.to_csv(
        out_dir / "prices_raw.csv",
        index=False,
        encoding="utf-8-sig",
    )

    prices = prepare_prices(prices_raw)

    # Date + Codeで突合
    joined = margin.merge(
        prices,
        on=["Date", "Code"],
        how="left",
        suffixes=("", "_price"),
    )

    joined = calculate_metrics(joined)

    joined.to_csv(
        out_dir / "joined_validation.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = create_summary(joined)
    summary.to_csv(
        out_dir / "summary_by_code.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n検証完了")
    print(f"出力先: {out_dir.resolve()}")
    print("  margin_raw.csv")
    print("  prices_raw.csv")
    print("  joined_validation.csv")
    print("  summary_by_code.csv")
    print(
        "\n注意: 金額/株数を平均取得単価と断定しないでください。"
        "まず正式なフィールド定義を確認してください。"
    )


if __name__ == "__main__":
    main()
