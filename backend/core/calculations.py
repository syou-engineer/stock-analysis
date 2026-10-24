def calculate_growth(current: float, previous: float) -> float:
    """
    前年同期比(YoY)や成長率を安全に計算してパーセントで返す関数。
    - previous が 0 や None の場合は None を返す。
    - 負の数からの成長（赤字縮小など）は単純な割り算では計算できないため、絶対値などで調整するかNoneにする。
      （ここでは一般的な簡易計算とし、previousが負の場合はNoneとする）
    """
    if current is None or previous is None or previous <= 0:
        return None
    
    try:
        return ((current / previous) - 1) * 100
    except ZeroDivisionError:
        return None

def calculate_roe(net_income: float, equity: float) -> float:
    """
    自己資本利益率(ROE)を計算してパーセントで返す関数。
    """
    if net_income is None or equity is None or equity <= 0:
        return None
    
    try:
        return (net_income / equity) * 100
    except ZeroDivisionError:
        return None

def calculate_margin(profit: float, revenue: float) -> float:
    """
    利益率を計算してパーセントで返す関数。
    """
    if profit is None or revenue is None or revenue <= 0:
        return None
    
    try:
        return (profit / revenue) * 100
    except ZeroDivisionError:
        return None