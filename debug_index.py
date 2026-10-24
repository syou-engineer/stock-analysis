# debug_index.py
from backend.services.fetcher import JQuantsFetcher

def run_debug():
    print("=== J-Quants API 指数データ取得テスト ===")
    fetcher = JQuantsFetcher()
    
    # 1. TOPIXのテスト
    print("\n1. TOPIX (0000) の取得テスト...")
    topix_data = fetcher.fetch_index("0000")
    print(f" -> 取得件数: {len(topix_data)} 件")
    if topix_data:
        print(f" -> 最新データサンプル: {topix_data[-1]}")
    else:
        print(" -> [NG] データが空です。エンドポイントまたは権限エラーの可能性があります。")

    # 2. セクター指数（例: 電気機器 004F）のテスト
    print("\n2. 業種別指数 (004F: 電気機器) の取得テスト...")
    sector_data = fetcher.fetch_index("004F")
    print(f" -> 取得件数: {len(sector_data)} 件")
    if sector_data:
        print(f" -> 最新データサンプル: {sector_data[-1]}")
    else:
        print(" -> [NG] データが空です。エンドポイントまたは権限エラーの可能性があります。")

if __name__ == "__main__":
    run_debug()