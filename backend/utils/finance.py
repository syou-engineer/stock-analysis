
import math

def normalize_code(code: str) -> str:
    """証券コードをプロジェクト標準の4桁文字列に統一する"""
    if not code:
        return ""
    code_str = str(code).strip()
    # 5桁以上のコード（J-Quantsの末尾0など）は最初の4桁を取り出す
    if len(code_str) >= 4:
        return code_str[:4]
    return code_str

def to_float(value, default=None):
    """文字列カンマ付き数値などを安全にfloatに変換する"""
    if value is None or value == "": 
        return default
    try:
        if isinstance(value, str): 
            value = value.replace(",", "").strip()
        return float(value)
    except (TypeError, ValueError): 
        return default

def calc_yoy(current, previous):
    """前年同期比（YoY）のパーセンテージを計算する"""
    curr = to_float(current)
    prev = to_float(previous)
    if curr is None or prev is None or prev == 0: 
        return None
    # 赤字から黒字への転換は便宜上 999.9 とする（あるいはNoneにするかは要件次第）
    if prev < 0 and curr > 0: 
        return 999.9 
    # 赤字拡大/縮小は単純なパーセント計算が直感に反するためNone
    if prev < 0 and curr < 0: 
        return None
    return ((curr - prev) / abs(prev)) * 100

def calc_margin(profit, sales):
    """売上高に対する利益率（％）を計算する"""
    p = to_float(profit)
    s = to_float(sales)
    if p is None or s is None or s == 0: 
        return None
    return (p / s) * 100

def calc_cagr(latest, past, years):
    """年平均成長率（CAGR）のパーセンテージを計算する"""
    l = to_float(latest)
    p = to_float(past)
    y = to_float(years)
    if l is None or p is None or y is None or l <= 0 or p <= 0 or y <= 0: 
        return None
    return (math.pow(l / p, 1 / y) - 1) * 100

def format_jpy(value):
    """数値を日本円（億円・兆円）の読みやすい文字列にフォーマットする"""
    val = to_float(value)
    if val is None: 
        return "-"
    oku = val / 100_000_000
    if abs(oku) >= 10_000: 
        return f"{oku / 10_000:,.1f}兆円"
    return f"{oku:,.0f}億円"

def get_field(obj, *keys):
    """辞書から複数のキー候補を順に探し、最初に見つかった有効な値を返す"""
    if not isinstance(obj, dict): 
        return None
    for k in keys:
        val = obj.get(k)
        if val is not None and val != "": 
            return val
    return None