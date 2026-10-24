# import math
# from statistics import median

# def to_float(value, default=None):
#     if value is None or value == "":
#         return default
#     try:
#         if isinstance(value, str):
#             value = value.replace(",", "").strip()
#         return float(value)
#     except (TypeError, ValueError):
#         return default

# def format_jpy(value):
#     val = to_float(value)
#     if val is None: return "-"
#     oku = val / 100_000_000
#     if abs(oku) >= 10_000: return f"{oku / 10_000:,.1f}兆円"
#     return f"{oku:,.0f}億円"

# def calc_yoy(current, previous):
#     curr = to_float(current)
#     prev = to_float(previous)
#     if curr is None or prev is None or prev == 0: return None
#     return (curr - prev) / abs(prev) * 100

# def calc_cagr(latest, past, years):
#     l = to_float(latest)
#     p = to_float(past)
#     y = to_float(years)
#     if l is None or p is None or y is None or l <= 0 or p <= 0 or y <= 0: return None
#     return (math.pow(l / p, 1 / y) - 1) * 100

# def get_field(obj, *keys):
#     """オブジェクトからキーを順番に探し、空文字列でない最初の値を返す"""
#     if not isinstance(obj, dict): return None
#     for k in keys:
#         val = obj.get(k)
#         if val is not None and val != "":
#             return val
#     return None

# def get_valuation_statistics(valuation_history):
#     if not valuation_history or not isinstance(valuation_history, list):
#         return {"per_avg": None, "per_median": None, "pbr_avg": None, "pbr_median": None}
    
#     hist_1yr = valuation_history[-250:]
#     per_list = [to_float(get_field(v, "FwdPER", "PER")) for v in hist_1yr if to_float(get_field(v, "FwdPER", "PER")) is not None]
#     pbr_list = [to_float(get_field(v, "PBR")) for v in hist_1yr if to_float(get_field(v, "PBR")) is not None]
    
#     return {
#         "per_avg": sum(per_list)/len(per_list) if per_list else None,
#         "per_median": median(per_list) if per_list else None,
#         "pbr_avg": sum(pbr_list)/len(pbr_list) if pbr_list else None,
#         "pbr_median": median(pbr_list) if pbr_list else None,
#     }

# def build_cumulative_adjustment_map(daily_quotes):
#     if not daily_quotes or not isinstance(daily_quotes, list): return {}
#     quotes_desc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""), reverse=True)
    
#     adjustment_map = {}
#     cum = 1.0
#     cum_list = []
    
#     for q in quotes_desc:
#         f_raw = get_field(q, "AdjFactor", "AdjustmentFactor", "adj_factor")
#         f = to_float(f_raw, 1.0)
#         if f <= 0: f = 1.0
#         cum *= f
#         cum_list.append(cum)
        
#     for i in range(len(quotes_desc)):
#         date = quotes_desc[i].get("Date")
#         if i == 0:
#             val = 1.0
#         else:
#             val = cum_list[i - 1]
#         adjustment_map[date] = val
        
#     return adjustment_map

# def get_adjustment_factor_for_date(target_date, adjustment_map):
#     if not target_date or not adjustment_map: return 1.0
#     if target_date in adjustment_map: return adjustment_map[target_date]
#     dates_desc = sorted(adjustment_map.keys(), reverse=True)
#     for d in dates_desc:
#         if d <= target_date:
#             return adjustment_map[d]
#     return 1.0

# def adjust_per_share_value(raw_value, adjustment_factor):
#     v = to_float(raw_value)
#     f = to_float(adjustment_factor, 1.0)
#     if v is None: return None
#     return v * f

# def calculate_analysis(profile):
#     if not isinstance(profile, dict): profile = {}
#     info = profile.get("info", {})
#     if not isinstance(info, dict): info = {}
#     valuation = profile.get("valuation", {})
#     if not isinstance(valuation, dict): valuation = {}
#     fins = profile.get("financial_summary", [])
#     if not isinstance(fins, list): fins = []
#     daily_quotes = profile.get("daily_quotes", [])
#     if not isinstance(daily_quotes, list): daily_quotes = []
    
#     adj_map = build_cumulative_adjustment_map(daily_quotes)
#     daily_quotes_asc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""))
#     fins_sorted = sorted([f for f in fins if isinstance(f, dict) and f.get("DiscDate")], key=lambda x: x.get("DiscDate", ""))

#     # ==========================================
#     # 1. 予実管理 (売上高と営業利益の10年トラッキング)
#     # ==========================================
#     fy_tracking = {}
#     revisions = []

#     for f in fins_sorted:
#         fy_en = f.get("CurFYEn", "")
#         if not fy_en or not isinstance(fy_en, str) or len(fy_en) < 10: continue
#         fy_en_date = fy_en[:10]
#         fy_label = f"{fy_en[:4]}年{int(fy_en[5:7])}月期"
        
#         if fy_en_date not in fy_tracking:
#             fy_tracking[fy_en_date] = {
#                 "fy": fy_label, 
#                 "initial_sales": None, "final_sales": None, "latest_fsales": None,
#                 "initial_op": None, "final_op": None, "latest_fop": None,
#                 "up_revisions": [], "down_revisions": []
#             }
        
#         current_fsales = to_float(get_field(f, "ForecastNetSales", "FSales"))
#         current_fop = to_float(get_field(f, "ForecastOperatingProfit", "FOP"))
#         disc_date = f.get("DiscDate", "")[:10]
#         cur_per_type = f.get("CurPerType", "")

#         if current_fsales is not None:
#             if fy_tracking[fy_en_date]["initial_sales"] is None:
#                 fy_tracking[fy_en_date]["initial_sales"] = current_fsales
#             fy_tracking[fy_en_date]["latest_fsales"] = current_fsales

#         if current_fop is not None:
#             if fy_tracking[fy_en_date]["initial_op"] is None:
#                 fy_tracking[fy_en_date]["initial_op"] = current_fop
            
#             prev_fop = fy_tracking[fy_en_date]["latest_fop"]
#             if prev_fop is not None and current_fop != prev_fop:
#                 diff = current_fop - prev_fop
#                 diff_pct = (diff / abs(prev_fop) * 100) if prev_fop != 0 else 0
#                 is_up = diff > 0
#                 timing = cur_per_type if cur_per_type else "不明"
#                 if timing == "FY": timing = "4Q"
                
#                 if is_up: fy_tracking[fy_en_date]["up_revisions"].append(timing)
#                 else: fy_tracking[fy_en_date]["down_revisions"].append(timing)
                
#                 revisions.append({
#                     "date": disc_date, "fy": fy_label, "prev_fop": prev_fop,
#                     "new_fop": current_fop, "diff_pct": diff_pct, "is_up": is_up, "timing": timing
#                 })
#             fy_tracking[fy_en_date]["latest_fop"] = current_fop
        
#         if cur_per_type == "FY":
#             fy_tracking[fy_en_date]["final_op"] = to_float(get_field(f, "OperatingProfit", "OP"))
#             fy_tracking[fy_en_date]["final_sales"] = to_float(get_field(f, "NetSales", "Sales"))

#     guidance_history = []
#     for fy_en in sorted(fy_tracking.keys())[-10:]:
#         track = fy_tracking[fy_en]
#         achieve = None
#         if track["final_op"] is not None and track["initial_op"] and track["initial_op"] > 0:
#             achieve = (track["final_op"] / track["initial_op"]) * 100
            
#         guidance_history.append({
#             "fy": track["fy"], 
#             "initial_sales": track["initial_sales"], "final_sales": track["final_sales"],
#             "initial_op": track["initial_op"], "final_op": track["final_op"],
#             "achievement_rate": achieve, "up_revisions": track["up_revisions"], "down_revisions": track["down_revisions"]
#         })

#     # ==========================================
#     # 2. 財務指標計算
#     # ==========================================
#     fy_dict = {}
#     for f in fins_sorted:
#         if f.get("CurPerType") == "FY":
#             year = f.get("CurFYEn", "")[:4]
#             if year: fy_dict[year] = f
    
#     fy_fins = [fy_dict[y] for y in sorted(fy_dict.keys())]
#     fy_latest = fy_fins[-1] if fy_fins else {}
#     fy_3yr_ago = fy_fins[-4] if len(fy_fins) >= 4 else {}

#     latest_fin = fins_sorted[-1] if fins_sorted else {}
#     cur_type = latest_fin.get("CurPerType", "")
    
#     prev_fin = {}
#     for f in reversed(fins_sorted[:-1]):
#         if f.get("CurPerType") == cur_type:
#             prev_fin = f
#             break

#     sales = to_float(get_field(latest_fin, "NetSales", "Sales"))
#     op = to_float(get_field(latest_fin, "OperatingProfit", "OP"))
#     np = to_float(get_field(latest_fin, "ProfitAttributableToOwnersOfParent", "NP", "NetIncome"))
    
#     latest_target_date = latest_fin.get("CurFYEn", "")[:10] if latest_fin.get("CurFYEn") else ""
#     adj_factor = get_adjustment_factor_for_date(latest_target_date, adj_map)

#     eps_raw = to_float(get_field(latest_fin, "EarningsPerShare", "EPS"))
#     eps_adj = adjust_per_share_value(eps_raw, adj_factor)
    
#     bps_raw = to_float(get_field(latest_fin, "BookValuePerShare", "BPS", "bps"))
#     bps_adj = adjust_per_share_value(bps_raw, adj_factor)
    
#     dps_raw = to_float(get_field(latest_fin, "ResultDividendPerShareAnnual", "ResultDPS", "DividendPerShare", "dps"))
#     dps_adj = adjust_per_share_value(dps_raw, adj_factor)
    
#     ta = to_float(get_field(latest_fin, "TotalAssets", "TA", "total_assets"))
#     equity = to_float(get_field(latest_fin, "Equity", "NetAssets", "equity"))
    
#     equity_ratio = to_float(get_field(latest_fin, "EquityToAssetRatio", "EqAR"))
#     if equity_ratio is not None:
#         equity_ratio = equity_ratio * 100 if equity_ratio <= 1.0 else equity_ratio
#     elif equity and ta:
#         equity_ratio = (equity / ta) * 100

#     cfo = to_float(get_field(latest_fin, "NetCashProvidedByUsedInOperatingActivities", "CFO")) or 0
#     cfi = to_float(get_field(latest_fin, "NetCashProvidedByUsedInInvestmentActivities", "CFI")) or 0
#     fcf = (cfo + cfi) if cfo != 0 or cfi != 0 else None
    
#     prev_op = to_float(get_field(prev_fin, "OperatingProfit", "OP"))
#     prev_sales = to_float(get_field(prev_fin, "NetSales", "Sales"))
    
#     prev_eps_raw = to_float(get_field(prev_fin, "EarningsPerShare", "EPS"))
#     prev_target_date = prev_fin.get("CurFYEn", "")[:10] if prev_fin.get("CurFYEn") else ""
#     prev_eps_adj = adjust_per_share_value(prev_eps_raw, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
#     op_margin = (op / sales * 100) if op and sales else None
#     prev_op_margin = (prev_op / prev_sales * 100) if prev_op and prev_sales else None
#     op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

#     f_sales = to_float(get_field(latest_fin, "ForecastNetSales", "FSales"))
#     f_op = to_float(get_field(latest_fin, "ForecastOperatingProfit", "FOP"))
#     f_np = to_float(get_field(latest_fin, "ForecastProfitAttributableToOwnersOfParent", "FNP"))
    
#     f_eps_raw = to_float(get_field(latest_fin, "ForecastEarningsPerShare", "FEPS"))
#     f_eps_adj = adjust_per_share_value(f_eps_raw, adj_factor)

#     payout_ratio = None
#     if dps_raw and f_eps_raw and f_eps_raw > 0:
#         payout_ratio = (dps_raw / f_eps_raw) * 100
#     elif dps_raw and fy_latest:
#         fy_eps = to_float(get_field(fy_latest, "EarningsPerShare", "EPS"))
#         if fy_eps and fy_eps > 0:
#             payout_ratio = (dps_raw / fy_eps) * 100

#     # ==========================================
#     # ★修正: ROEは自前計算を一切やめ、API提供のバリュエーションROEをそのまま利用
#     # （TTM純利益ベースで正確に計算されているため）
#     # ==========================================
#     per = to_float(get_field(valuation, "FwdPER", "PER", "per"))
#     pbr = to_float(get_field(valuation, "PBR", "pbr"))
#     mktcap = to_float(get_field(valuation, "MktCap", "market_cap"))
    
#     # 取得した ROE（少数なので x100 する）
#     api_roe = to_float(get_field(valuation, "ROE", "roe"))
#     roe = api_roe * 100 if api_roe is not None else None
    
#     eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
#     peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

#     # Annual Data
#     history = []
#     hist_fys = fy_fins[-10:] if len(fy_fins) >= 10 else fy_fins
#     for i, fy in enumerate(hist_fys):
#         y_str = fy.get("CurFYEn", "")[:4]
#         s = to_float(get_field(fy, "NetSales", "Sales"))
#         o = to_float(get_field(fy, "OperatingProfit", "OP"))
        
#         cfo_fy = to_float(get_field(fy, "NetCashProvidedByUsedInOperatingActivities", "CFO")) or 0
#         cfi_fy = to_float(get_field(fy, "NetCashProvidedByUsedInInvestmentActivities", "CFI")) or 0
#         fc = (cfo_fy + cfi_fy) if cfo_fy != 0 or cfi_fy != 0 else None
        
#         target_date = fy.get("CurFYEn", "")[:10]
#         e_raw = to_float(get_field(fy, "EarningsPerShare", "EPS"))
#         e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
#         prev_s = to_float(get_field(hist_fys[i-1], "NetSales", "Sales")) if i > 0 else None
#         prev_o = to_float(get_field(hist_fys[i-1], "OperatingProfit", "OP")) if i > 0 else None
        
#         prev_e_raw = to_float(get_field(hist_fys[i-1], "EarningsPerShare", "EPS")) if i > 0 else None
#         p_target = hist_fys[i-1].get("CurFYEn", "")[:10] if i > 0 else ""
#         prev_e_adj = adjust_per_share_value(prev_e_raw, get_adjustment_factor_for_date(p_target, adj_map)) if i > 0 else None
        
#         history.append({
#             "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
#             "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
#             "op_margin": (o / s * 100) if o and s else None,
#             "eps_raw": e_raw, "eps_adjusted": e_adj,
#             "fcf_raw": fc, "fcf_margin": (fc / s * 100) if fc is not None and s else None
#         })

#     if f_sales or f_op or f_eps_raw:
#         next_year = str(int(history[-1]["year"]) + 1) if history else "予"
#         history.append({
#             "year": f"{next_year}(予)", "sales_str": format_jpy(f_sales), "sales_raw": f_sales, "sales_yoy": None,
#             "op_str": format_jpy(f_op), "op_raw": f_op, "op_yoy": None,
#             "op_margin": (f_op / f_sales * 100) if f_op and f_sales else None,
#             "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "eps_yoy": None,
#             "fcf_raw": None, "fcf_margin": None
#         })

#     # Quarterly Data
#     q_dict = {}
#     actual_fins = [f for f in fins_sorted if isinstance(f, dict) and f.get("CurPerType") in ["1Q", "2Q", "3Q", "FY"]]
#     fy_tree = {}
#     for f in actual_fins:
#         year = f.get("CurFYEn", "")[:4]
#         q_type = f.get("CurPerType", "")
#         if year and q_type:
#             q_dict[f"{year}-{q_type}"] = f
#             if year not in fy_tree: fy_tree[year] = {}
#             fy_tree[year][q_type] = f

#     sorted_q_keys = sorted(q_dict.keys())
#     recent_quarters = [q_dict[k] for k in sorted_q_keys[-20:]]
#     quarterly_history = []
    
#     for i, q in enumerate(recent_quarters):
#         q_year = q.get("CurFYEn", "")[:4]
#         q_type = q.get("CurPerType", "")
#         c_sales = to_float(get_field(q, "NetSales", "Sales"))
#         c_op = to_float(get_field(q, "OperatingProfit", "OP"))
#         single_sales = c_sales
#         single_op = c_op
#         prev_q_type_in_fy = None
#         if q_type == "2Q": prev_q_type_in_fy = "1Q"
#         elif q_type == "3Q": prev_q_type_in_fy = "2Q"
#         elif q_type == "FY": prev_q_type_in_fy = "3Q"
#         if prev_q_type_in_fy and q_year in fy_tree and prev_q_type_in_fy in fy_tree[q_year]:
#             prev_q_data = fy_tree[q_year][prev_q_type_in_fy]
#             p_c_sales = to_float(get_field(prev_q_data, "NetSales", "Sales"))
#             if c_sales is not None and p_c_sales is not None: single_sales = c_sales - p_c_sales
#             p_c_op = to_float(get_field(prev_q_data, "OperatingProfit", "OP"))
#             if c_op is not None and p_c_op is not None: single_op = c_op - p_c_op

#         target_date = q.get("CurFYEn", "")[:10]
#         e_raw = to_float(get_field(q, "EarningsPerShare", "EPS"))
#         e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
#         label = f"{q_year[-2:]}年 {q_type.replace('FY', '4Q')}" 
        
#         quarterly_history.append({
#             "year": label, "sales_str": format_jpy(single_sales), "sales_raw": single_sales, "sales_yoy": None,
#             "op_str": format_jpy(single_op), "op_raw": single_op, "op_yoy": None,
#             "op_margin": (single_op / single_sales * 100) if single_op and single_sales else None,
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "eps_yoy": None,
#             "fcf_raw": None, "fcf_margin": None
#         })

#     # ==========================================
#     # 株価・バリュエーション履歴 (全期間)
#     # ==========================================
#     margin_interest = profile.get("margin_interest", [])
#     if not isinstance(margin_interest, list): margin_interest = []
#     margin_dict = {m.get("Date"): m for m in margin_interest if isinstance(m, dict) and "Date" in m}
    
#     val_history = profile.get("valuation_history", [])
#     if not isinstance(val_history, list): val_history = []
#     val_dict = {v.get("Date"): v for v in val_history if isinstance(v, dict) and "Date" in v}

#     price_margin_history = []
    
#     for q in daily_quotes_asc:
#         date_str = q.get("Date")
#         if not date_str: continue

#         adj_c = to_float(get_field(q, "AdjC", "AdjClose", "adj_c", "adj_close"))
#         if adj_c is None:
#             continue
            
#         m = margin_dict.get(date_str, {})
#         v = val_dict.get(date_str, {}) 
        
#         adj_o = to_float(get_field(q, "AdjO", "AdjOpen", "adj_o", "adj_open"))
#         adj_h = to_float(get_field(q, "AdjH", "AdjHigh", "adj_h", "adj_high"))
#         adj_l = to_float(get_field(q, "AdjL", "AdjLow", "adj_l", "adj_low"))
#         adj_vo = to_float(get_field(q, "AdjVo", "AdjVolume", "adj_vo", "adj_volume"))
        
#         price_margin_history.append({
#             "date": date_str,
#             "open": adj_o if adj_o is not None else adj_c,
#             "high": adj_h if adj_h is not None else adj_c,
#             "low": adj_l if adj_l is not None else adj_c,
#             "close": adj_c,
#             "volume": adj_vo,
#             "margin_buy": to_float(get_field(m, "LongVol", "margin_buy")),
#             "margin_sell": to_float(get_field(m, "ShrtVol", "margin_sell")),
#             "per": to_float(get_field(v, "FwdPER", "PER", "per")),
#             "pbr": to_float(get_field(v, "PBR", "pbr")),
#             "market_cap": to_float(get_field(v, "MktCap", "market_cap"))
#         })

#     stock_perf_1y = None
#     if len(price_margin_history) > 250:
#         current_close = price_margin_history[-1].get("close")
#         close_1y_ago = price_margin_history[-250].get("close")
#         if current_close and close_1y_ago:
#             stock_perf_1y = (current_close - close_1y_ago) / close_1y_ago * 100

#     return {
#         "basic": { 
#             "code": profile.get("code", "")[:4], 
#             "company_name": info.get("CompanyName", info.get("CoName", "-")), 
#             "industry": info.get("Sector33CodeName", info.get("S17Nm", "-")), 
#             "market": info.get("MarketCodeName", info.get("MktNm", "-")) 
#         },
#         "period": { "current_type": cur_type, "disclosure_date": latest_fin.get("DiscDate", "") },
#         "actual": { 
#             "sales": sales, "op": op, "net_income": np, "eps_raw": eps_raw, "eps_adjusted": eps_adj, "fcf": fcf,
#             "bps": bps_adj, "dps": dps_adj
#         },
#         "forecast": { "sales": f_sales, "op": f_op, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
#         "growth": { 
#             "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
#             "eps_yoy": eps_yoy_adjusted, "sales_cagr_3y": calc_cagr(fy_latest.get("Sales"), fy_3yr_ago.get("Sales"), 3) 
#         },
#         "profitability": { 
#             "op_margin": op_margin, "op_margin_change": op_margin_change, 
#             "roe": roe, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
#             "equity_ratio": equity_ratio, "payout_ratio": payout_ratio
#         },
#         "valuation": { 
#             "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
#             **get_valuation_statistics(profile.get("valuation_history", [])) 
#         },
#         "market_perf": { "stock_1y": stock_perf_1y },
#         "history": history,
#         "quarterly_history": quarterly_history,
#         "price_margin_history": price_margin_history,
#         "major_shareholders": profile.get("major_shareholders", {}),
#         "large_volume": profile.get("large_volume", []),
#         "cross_shareholdings": profile.get("cross_shareholdings", {}),
#         "events": { "revisions": revisions },
#         "guidance_history": guidance_history
#     }



import math
from statistics import median

def to_float(value, default=None):
    if value is None or value == "": return default
    try:
        if isinstance(value, str): value = value.replace(",", "").strip()
        return float(value)
    except (TypeError, ValueError): return default

def format_jpy(value):
    val = to_float(value)
    if val is None: return "-"
    oku = val / 100_000_000
    if abs(oku) >= 10_000: return f"{oku / 10_000:,.1f}兆円"
    return f"{oku:,.0f}億円"

def calc_yoy(current, previous):
    curr = to_float(current)
    prev = to_float(previous)
    if curr is None or prev is None or prev == 0: return None
    return (curr - prev) / abs(prev) * 100

def calc_cagr(latest, past, years):
    l = to_float(latest)
    p = to_float(past)
    y = to_float(years)
    if l is None or p is None or y is None or l <= 0 or p <= 0 or y <= 0: return None
    return (math.pow(l / p, 1 / y) - 1) * 100

def get_field(obj, *keys):
    if not isinstance(obj, dict): return None
    for k in keys:
        val = obj.get(k)
        if val is not None and val != "": return val
    return None

def get_valuation_statistics(valuation_history):
    if not valuation_history or not isinstance(valuation_history, list):
        return {"per_avg": None, "per_median": None, "pbr_avg": None, "pbr_median": None}
    hist_1yr = valuation_history[-250:]
    per_list = [to_float(get_field(v, "FwdPER", "PER")) for v in hist_1yr if to_float(get_field(v, "FwdPER", "PER")) is not None]
    pbr_list = [to_float(get_field(v, "PBR")) for v in hist_1yr if to_float(get_field(v, "PBR")) is not None]
    return {
        "per_avg": sum(per_list)/len(per_list) if per_list else None,
        "per_median": median(per_list) if per_list else None,
        "pbr_avg": sum(pbr_list)/len(pbr_list) if pbr_list else None,
        "pbr_median": median(pbr_list) if pbr_list else None,
    }

def build_cumulative_adjustment_map(daily_quotes):
    if not daily_quotes or not isinstance(daily_quotes, list): return {}
    quotes_asc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""))
    if not quotes_asc: return {}
    
    factors_by_date = {}
    for q in quotes_asc:
        f_raw = get_field(q, "AdjFactor", "AdjustmentFactor", "adj_factor")
        f = to_float(f_raw, 1.0)
        if f > 0 and f != 1.0:
            factors_by_date[q.get("Date")] = f
            
    adjustment_map = {}
    for q in quotes_asc:
        date = q.get("Date")
        cum_factor = 1.0
        for factor_date, f in factors_by_date.items():
            if factor_date > date:
                cum_factor *= f
        adjustment_map[date] = cum_factor
        
    return adjustment_map

def get_adjustment_factor_for_date(target_date, adjustment_map):
    if not target_date or not adjustment_map: return 1.0
    if target_date in adjustment_map: return adjustment_map[target_date]
    dates_asc = sorted(adjustment_map.keys())
    for d in dates_asc:
        if d >= target_date: 
            return adjustment_map[d]
    return 1.0

def adjust_per_share_value(raw_value, adjustment_factor):
    v = to_float(raw_value)
    f = to_float(adjustment_factor, 1.0)
    if v is None: return None
    return v * f

def calculate_analysis(profile):
    if not isinstance(profile, dict): profile = {}
    info = profile.get("info", {})
    if not isinstance(info, dict): info = {}
    valuation = profile.get("valuation", {})
    if not isinstance(valuation, dict): valuation = {}
    fins = profile.get("financial_summary", [])
    if not isinstance(fins, list): fins = []
    daily_quotes = profile.get("daily_quotes", [])
    if not isinstance(daily_quotes, list): daily_quotes = []
    
    adj_map = build_cumulative_adjustment_map(daily_quotes)
    daily_quotes_asc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""))
    fins_sorted = sorted([f for f in fins if isinstance(f, dict) and f.get("DiscDate")], key=lambda x: x.get("DiscDate", ""))

    fy_tracking = {}
    revisions = []
    other_events = [] 

    for f in fins_sorted:
        fy_en = f.get("CurFYEn", "")
        if not fy_en or len(fy_en) < 10: continue
        fy_en_date = fy_en[:10]
        fy_label = f"{fy_en[:4]}年{int(fy_en[5:7])}月期"
        disc_date = f.get("DiscDate", "")[:10]
        cur_per_type = f.get("CurPerType", "")
        
        flags = {
            "MatChgSub": "子会社異動", "SigChgInC": "連結範囲変更",
            "ChgByASRev": "会計基準変更", "ChgNoASRev": "会計方針変更",
            "ChgAcEst": "会計見積り変更", "RetroRst": "修正再表示"
        }
        for k, v in flags.items():
            if str(f.get(k, "")).lower() in ["true", "1"]:
                other_events.append({
                    "date": disc_date, "type": "ACCOUNTING", "title": v,
                    "desc": f"{cur_per_type}決算にて{v}の開示あり"
                })

        if fy_en_date not in fy_tracking:
            fy_tracking[fy_en_date] = {
                "fy": fy_label, "initial_sales": None, "final_sales": None, "latest_fsales": None,
                "initial_op": None, "final_op": None, "latest_fop": None,
                "up_revisions": [], "down_revisions": []
            }
        
        current_fsales = to_float(get_field(f, "FSales", "ForecastNetSales"))
        current_fop = to_float(get_field(f, "FOP", "ForecastOperatingProfit"))

        if current_fsales is not None:
            if fy_tracking[fy_en_date]["initial_sales"] is None:
                fy_tracking[fy_en_date]["initial_sales"] = current_fsales
            fy_tracking[fy_en_date]["latest_fsales"] = current_fsales

        if current_fop is not None:
            if fy_tracking[fy_en_date]["initial_op"] is None:
                fy_tracking[fy_en_date]["initial_op"] = current_fop
            
            prev_fop = fy_tracking[fy_en_date]["latest_fop"]
            if prev_fop is not None and current_fop != prev_fop:
                diff = current_fop - prev_fop
                diff_pct = (diff / abs(prev_fop) * 100) if prev_fop != 0 else 0
                is_up = diff > 0
                timing = cur_per_type if cur_per_type else "不明"
                if timing == "FY": timing = "4Q"
                
                if is_up: fy_tracking[fy_en_date]["up_revisions"].append(timing)
                else: fy_tracking[fy_en_date]["down_revisions"].append(timing)
                
                revisions.append({
                    "date": disc_date, "fy": fy_label, "prev_fop": prev_fop,
                    "new_fop": current_fop, "diff_pct": diff_pct, "is_up": is_up, "timing": timing
                })
            fy_tracking[fy_en_date]["latest_fop"] = current_fop
        
        if cur_per_type == "FY":
            fy_tracking[fy_en_date]["final_op"] = to_float(get_field(f, "OP", "OperatingProfit"))
            fy_tracking[fy_en_date]["final_sales"] = to_float(get_field(f, "Sales", "NetSales"))

    guidance_history = []
    for fy_en in sorted(fy_tracking.keys())[-10:]:
        track = fy_tracking[fy_en]
        achieve = None
        if track["final_op"] is not None and track["initial_op"] and track["initial_op"] > 0:
            achieve = (track["final_op"] / track["initial_op"]) * 100
        guidance_history.append({
            "fy": track["fy"], "initial_sales": track["initial_sales"], "final_sales": track["final_sales"],
            "initial_op": track["initial_op"], "final_op": track["final_op"],
            "achievement_rate": achieve, "up_revisions": track["up_revisions"], "down_revisions": track["down_revisions"]
        })

    fy_dict = {}
    for f in fins_sorted:
        if f.get("CurPerType") == "FY":
            year = f.get("CurFYEn", "")[:4]
            if year: fy_dict[year] = f
    
    fy_fins = [fy_dict[y] for y in sorted(fy_dict.keys())]
    fy_latest = fy_fins[-1] if fy_fins else {}
    fy_3yr_ago = fy_fins[-4] if len(fy_fins) >= 4 else {}

    latest_fin = fins_sorted[-1] if fins_sorted else {}
    cur_type = latest_fin.get("CurPerType", "")
    prev_fin = next((f for f in reversed(fins_sorted[:-1]) if f.get("CurPerType") == cur_type), {})

    sales = to_float(get_field(latest_fin, "Sales", "NetSales"))
    op = to_float(get_field(latest_fin, "OP", "OperatingProfit"))
    np_latest = to_float(get_field(latest_fin, "NP", "ProfitAttributableToOwnersOfParent", "NetIncome"))
    
    f_op = to_float(get_field(latest_fin, "FOP", "ForecastOperatingProfit"))
    progress_op = None
    if cur_type in ["1Q", "2Q", "3Q"] and op is not None and f_op and f_op > 0:
        progress_op = (op / f_op) * 100

    latest_target_date = latest_fin.get("CurPerEn", latest_fin.get("CurFYEn", ""))[:10]
    adj_factor = get_adjustment_factor_for_date(latest_target_date, adj_map)

    eps_raw = to_float(get_field(latest_fin, "EPS", "EarningsPerShare"))
    eps_adj = adjust_per_share_value(eps_raw, adj_factor)
    
    bps_raw = to_float(get_field(latest_fin, "BPS", "BookValuePerShare"))
    bps_adj = adjust_per_share_value(bps_raw, adj_factor)
    
    dps_raw = to_float(get_field(latest_fin, "DivAnn", "ResultDividendPerShareAnnual", "ResultDPS"))
    dps_adj = adjust_per_share_value(dps_raw, adj_factor)
    
    ta = to_float(get_field(latest_fin, "TA", "TotalAssets"))
    equity = to_float(get_field(latest_fin, "Eq", "ShEq", "Equity", "NetAssets"))
    
    equity_ratio = to_float(get_field(latest_fin, "EqAR", "EquityToAssetRatio"))
    if equity_ratio is not None:
        equity_ratio = equity_ratio * 100 if equity_ratio <= 1.0 else equity_ratio
    elif equity and ta:
        equity_ratio = (equity / ta) * 100

    tr_sh = to_float(get_field(latest_fin, "TrShFY", "TreasuryStock"))
    out_sh = to_float(get_field(latest_fin, "ShOutFY", "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
    treasury_ratio = (tr_sh / out_sh * 100) if tr_sh is not None and out_sh and out_sh > 0 else None

    cfo = to_float(get_field(latest_fin, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
    cfi = to_float(get_field(latest_fin, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
    cff = to_float(get_field(latest_fin, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
    cash_eq = to_float(get_field(latest_fin, "CashEq", "CashAndCashEquivalents"))
    prev_cash_eq = to_float(get_field(prev_fin, "CashEq", "CashAndCashEquivalents"))
    cash_change = (cash_eq - prev_cash_eq) if cash_eq is not None and prev_cash_eq is not None else None
    fcf = (cfo + cfi) if cfo is not None and cfi is not None else None

    def calc_dupont(fin_data):
        if not fin_data: return None
        d_s = to_float(get_field(fin_data, "Sales", "NetSales"))
        d_np = to_float(get_field(fin_data, "NP", "ProfitAttributableToOwnersOfParent"))
        d_ta = to_float(get_field(fin_data, "TA", "TotalAssets"))
        d_eq = to_float(get_field(fin_data, "Eq", "ShEq", "Equity", "NetAssets"))
        if d_s and d_np and d_ta and d_eq and d_eq > 0 and d_ta > 0:
            return {
                "npm": (d_np / d_s) * 100,      
                "at": d_s / d_ta,               
                "fl": d_ta / d_eq,              
                "roe": (d_np / d_eq) * 100      
            }
        return None

    dupont_current = calc_dupont(fy_latest)
    fy_prev = fy_fins[-2] if len(fy_fins) >= 2 else {}
    dupont_prev = calc_dupont(fy_prev)
    
    prev_op = to_float(get_field(prev_fin, "OP", "OperatingProfit"))
    prev_sales = to_float(get_field(prev_fin, "Sales", "NetSales"))
    prev_eps_raw = to_float(get_field(prev_fin, "EPS", "EarningsPerShare"))
    prev_target_date = prev_fin.get("CurPerEn", prev_fin.get("CurFYEn", ""))[:10]
    prev_eps_adj = adjust_per_share_value(prev_eps_raw, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
    op_margin = (op / sales * 100) if op and sales else None
    prev_op_margin = (prev_op / prev_sales * 100) if prev_op and prev_sales else None
    op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

    f_sales = to_float(get_field(latest_fin, "FSales", "ForecastNetSales"))
    f_np = to_float(get_field(latest_fin, "FNP", "ForecastProfitAttributableToOwnersOfParent"))
    f_eps_raw = to_float(get_field(latest_fin, "FEPS", "ForecastEarningsPerShare"))
    f_eps_adj = adjust_per_share_value(f_eps_raw, adj_factor)

    payout_ratio = to_float(get_field(latest_fin, "PayoutRatioAnn"))
    if payout_ratio is None:
        if dps_raw and f_eps_raw and f_eps_raw > 0:
            payout_ratio = (dps_raw / f_eps_raw) * 100
        elif dps_raw and fy_latest:
            fy_eps = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
            if fy_eps and fy_eps > 0:
                payout_ratio = (dps_raw / fy_eps) * 100

    per = to_float(get_field(valuation, "FwdPER", "PER"))
    pbr = to_float(get_field(valuation, "PBR"))
    mktcap = to_float(get_field(valuation, "MktCap"))
    
    fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
    fy_cfo = to_float(get_field(fy_latest, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
    
    cfo_to_np = None
    if fy_cfo is not None and fy_np and fy_np > 0:
        cfo_to_np = (fy_cfo / fy_np) * 100

    roe = None
    if f_np and equity and equity > 0:
        roe = (f_np / equity) * 100
    elif fy_np and equity and equity > 0:
        roe = (fy_np / equity) * 100
    else:
        api_roe = to_float(get_field(valuation, "ROE"))
        if api_roe is not None: roe = api_roe * 100

    eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
    peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

    # Annual Data
    history = []
    hist_fys = fy_fins[-10:] if len(fy_fins) >= 10 else fy_fins
    for i, fy in enumerate(hist_fys):
        y_str = fy.get("CurFYEn", "")[:4]
        s = to_float(get_field(fy, "Sales", "NetSales"))
        o = to_float(get_field(fy, "OP", "OperatingProfit"))
        eq = to_float(get_field(fy, "Eq", "Equity", "NetAssets"))
        pr = to_float(get_field(fy, "NP", "ProfitAttributableToOwnersOfParent"))
        r = (pr / eq) if pr and eq else to_float(get_field(fy, "ROE"))
        
        cfo_fy = to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities")) or 0
        cfi_fy = to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities")) or 0
        fc = (cfo_fy + cfi_fy) if cfo_fy != 0 or cfi_fy != 0 else None
        
        target_date = fy.get("CurFYEn", "")[:10]
        e_raw = to_float(get_field(fy, "EPS", "EarningsPerShare"))
        e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
        prev_s = to_float(get_field(hist_fys[i-1], "Sales", "NetSales")) if i > 0 else None
        prev_o = to_float(get_field(hist_fys[i-1], "OP", "OperatingProfit")) if i > 0 else None
        
        history.append({
            "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
            "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
            "op_margin": (o / s * 100) if o and s else None,
            "eps_raw": e_raw, "eps_adjusted": e_adj, "roe_raw": r * 100 if r and r < 1.0 else r,
            "fcf_raw": fc, "fcf_margin": (fc / s * 100) if fc is not None and s else None
        })

    if f_sales or f_op or f_eps_raw:
        next_year = str(int(history[-1]["year"]) + 1) if history else "予"
        history.append({
            "year": f"{next_year}(予)", "sales_str": format_jpy(f_sales), "sales_raw": f_sales, "sales_yoy": None,
            "op_str": format_jpy(f_op), "op_raw": f_op, "op_yoy": None,
            "op_margin": (f_op / f_sales * 100) if f_op and f_sales else None,
            "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "eps_yoy": None,
            "roe_raw": None, "fcf_raw": None, "fcf_margin": None
        })

    # Quarterly Data
    actual_fins = [f for f in fins_sorted if isinstance(f, dict) and f.get("CurPerType") in ["1Q", "2Q", "3Q", "FY"]]
    fy_tree = {}
    for f in actual_fins:
        year = f.get("CurFYEn", "")[:4]
        q_type = f.get("CurPerType", "")
        if year and q_type:
            if year not in fy_tree: fy_tree[year] = {}
            fy_tree[year][q_type] = f

    single_q_data = {}
    for year in sorted(fy_tree.keys()):
        for qt in ["1Q", "2Q", "3Q", "FY"]:
            if qt not in fy_tree[year]: continue
            q_data = fy_tree[year][qt]
            
            c_sales = to_float(get_field(q_data, "Sales", "NetSales"))
            c_op = to_float(get_field(q_data, "OP", "OperatingProfit"))
            s_sales, s_op = c_sales, c_op
            
            prev_qt = {"2Q":"1Q", "3Q":"2Q", "FY":"3Q"}.get(qt)
            if prev_qt and prev_qt in fy_tree[year]:
                p_data = fy_tree[year][prev_qt]
                p_c_sales = to_float(get_field(p_data, "Sales", "NetSales"))
                p_c_op = to_float(get_field(p_data, "OP", "OperatingProfit"))
                if c_sales is not None and p_c_sales is not None: s_sales = c_sales - p_c_sales
                if c_op is not None and p_c_op is not None: s_op = c_op - p_c_op
                
            single_q_data[f"{year}-{qt}"] = {
                "sales": s_sales, "op": s_op, "raw": q_data
            }

    sorted_q_keys = sorted(single_q_data.keys())
    quarterly_history = []
    
    for k in sorted_q_keys[-40:]:
        year_str, q_type = k.split("-")
        curr = single_q_data[k]
        q_raw = curr["raw"]
        
        prev_year_str = str(int(year_str) - 1)
        prev_k = f"{prev_year_str}-{q_type}"
        prev_q = single_q_data.get(prev_k, {})
        
        s_yoy = calc_yoy(curr["sales"], prev_q.get("sales"))
        o_yoy = calc_yoy(curr["op"], prev_q.get("op"))
        
        target_date = q_raw.get("CurPerEn", q_raw.get("CurFYEn", ""))[:10]
        e_raw = to_float(get_field(q_raw, "EPS", "EarningsPerShare"))
        e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
        label = f"{year_str[-2:]}年 {q_type.replace('FY', '4Q')}" 
        
        quarterly_history.append({
            "year": label, "sales_str": format_jpy(curr["sales"]), "sales_raw": curr["sales"], "sales_yoy": s_yoy,
            "op_str": format_jpy(curr["op"]), "op_raw": curr["op"], "op_yoy": o_yoy,
            "op_margin": (curr["op"] / curr["sales"] * 100) if curr["op"] and curr["sales"] else None,
            "eps_raw": e_raw, "eps_adjusted": e_adj, "eps_yoy": None,
            "fcf_raw": None, "fcf_margin": None
        })

    margin_interest = profile.get("margin_interest", [])
    if not isinstance(margin_interest, list): margin_interest = []
    margin_dict = {m.get("Date"): m for m in margin_interest if isinstance(m, dict) and "Date" in m}
    val_history = profile.get("valuation_history", [])
    if not isinstance(val_history, list): val_history = []
    val_dict = {v.get("Date"): v for v in val_history if isinstance(v, dict) and "Date" in v}
    price_margin_history = []
    last_topix = None
    last_sector = None
    
    # 信用残高の Forward Fill 用変数
    last_margin_buy = None
    last_margin_sell = None

    for q in daily_quotes_asc:
        date_str = q.get("Date", "")[:10]
        if not date_str: continue

        adj_c = to_float(get_field(q, "AdjC", "AdjClose", "adj_c", "adj_close"))
        if adj_c is None:
            raw_c = to_float(get_field(q, "Close", "C"))
            if raw_c is None: continue
            adj_f = get_adjustment_factor_for_date(date_str, adj_map)
            adj_c = raw_c / adj_f if adj_f > 0 else raw_c

        adj_o = to_float(get_field(q, "AdjO", "AdjOpen"))
        adj_h = to_float(get_field(q, "AdjH", "AdjHigh"))
        adj_l = to_float(get_field(q, "AdjL", "AdjLow"))
        adj_vo = to_float(get_field(q, "AdjVo", "AdjVolume"))

        if adj_o is None: adj_o = adj_c
        if adj_h is None: adj_h = adj_c
        if adj_l is None: adj_l = adj_c
        
        v = val_dict.get(date_str, {}) 
        curr_topix = topix_dict.get(date_str)
        if curr_topix is not None: last_topix = curr_topix
            
        curr_sector = sector_dict.get(date_str)
        if curr_sector is not None: last_sector = curr_sector

        # ★ 信用残高の処理（更新日のみ増減を計算）
        m = margin_dict.get(date_str)
        mb_chg = None
        ms_chg = None
        std_avg_price = None

        if m: # この日に信用残高のデータ更新がある場合
            curr_mb = to_float(get_field(m, "LongVol", "margin_buy"))
            curr_ms = to_float(get_field(m, "ShrtVol", "margin_sell"))
            
            if last_margin_buy is not None and curr_mb is not None:
                mb_chg = curr_mb - last_margin_buy
            if last_margin_sell is not None and curr_ms is not None:
                ms_chg = curr_ms - last_margin_sell
                
            last_margin_buy = curr_mb
            last_margin_sell = curr_ms

            # ★ 新仕様(2026/9/25~)のみ: 制度信用の平均取得価格（推定建値）を計算
            std_vol = to_float(get_field(m, "LongStdVol"))
            std_val = to_float(get_field(m, "LongStdVal"))
            if std_vol and std_val and std_vol > 0:
                std_avg_price = std_val / std_vol

        price_margin_history.append({
            "date": date_str, "open": adj_o, "high": adj_h, "low": adj_l, "close": adj_c, "volume": adj_vo,
            "margin_buy": last_margin_buy,       # 値は常に引き継ぐ(チャート描画用)
            "margin_sell": last_margin_sell,
            "margin_buy_chg": mb_chg,            # 増減はデータ更新日のみ値が入る
            "margin_sell_chg": ms_chg,
            "std_avg_price": std_avg_price,      # 2026/9/25以降のみ値が入る
            "per": to_float(get_field(v, "FwdPER", "PER")),
            "pbr": to_float(get_field(v, "PBR")),
            "market_cap": to_float(get_field(v, "MktCap")),
            "topix": last_topix,
            "sector": last_sector
        })

    stock_perf_1y = None
    if len(price_margin_history) > 250:
        current_close = price_margin_history[-1].get("close")
        close_1y_ago = price_margin_history[-250].get("close")
        if current_close and close_1y_ago:
            stock_perf_1y = (current_close - close_1y_ago) / close_1y_ago * 100

    return {
        "basic": { 
            "code": profile.get("code", "")[:4], 
            "company_name": info.get("CompanyName", info.get("CoName", "-")), 
            "industry": info.get("Sector33CodeName", info.get("S17Nm", "-")), 
            "market": info.get("MarketCodeName", info.get("MktNm", "-")) 
        },
        "period": { "current_type": cur_type, "disclosure_date": latest_fin.get("DiscDate", "") },
        "actual": { 
            "sales": sales, "op": op, "net_income": np_latest, "eps_raw": eps_raw, "eps_adjusted": eps_adj, "fcf": fcf,
            "bps": bps_adj, "dps": dps_adj,
            "cfo": cfo, "cfi": cfi, "cff": cff, "cash_eq": cash_eq, "cash_change": cash_change
        },
        "forecast": { "sales": f_sales, "op": f_op, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
        "growth": { 
            "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
            "eps_yoy": eps_yoy_adjusted, "sales_cagr_3y": calc_cagr(fy_latest.get("Sales"), fy_3yr_ago.get("Sales"), 3),
            "progress_op": progress_op
        },
        "profitability": { 
            "op_margin": op_margin, "op_margin_change": op_margin_change, 
            "roe": roe, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
            "equity_ratio": equity_ratio, "payout_ratio": payout_ratio,
            "cfo_to_np": cfo_to_np, "treasury_ratio": treasury_ratio,
            "dupont": {"current": dupont_current, "prev": dupont_prev}
        },
        "valuation": { 
            "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
            **get_valuation_statistics(profile.get("valuation_history", [])) 
        },
        "market_perf": { "stock_1y": stock_perf_1y },
        "history": history,
        "quarterly_history": quarterly_history,
        "price_margin_history": price_margin_history,
        "major_shareholders": profile.get("major_shareholders", {}),
        "large_volume": profile.get("large_volume", []),
        "cross_shareholdings": profile.get("cross_shareholdings", {}),
        "events": { "revisions": revisions, "other": other_events },
        "guidance_history": guidance_history
    }