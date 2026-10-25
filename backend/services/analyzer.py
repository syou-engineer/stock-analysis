
# from backend.utils.finance import (
#     to_float, format_jpy, calc_yoy, calc_cagr, calc_margin, get_field, normalize_code
# )
# from statistics import median
# import math

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
#     quotes_asc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""))
#     if not quotes_asc: return {}
    
#     factors_by_date = {}
#     for q in quotes_asc:
#         f = to_float(get_field(q, "AdjustmentFactor", "AdjFactor", "adj_factor"), 1.0)
#         if f > 0 and f != 1.0: 
#             factors_by_date[q.get("Date")[:10]] = f
            
#     adjustment_map = {}
#     for q in quotes_asc:
#         date = q.get("Date", "")[:10]
#         cum_factor = 1.0
#         for factor_date, f in factors_by_date.items():
#             if factor_date > date: 
#                 cum_factor *= f
#         adjustment_map[date] = cum_factor
        
#     return adjustment_map

# def get_adjustment_factor_for_date(target_date, adjustment_map):
#     if not target_date or not adjustment_map: return 1.0
#     target_date = target_date[:10]
#     if target_date in adjustment_map: return adjustment_map[target_date]
    
#     dates_asc = sorted(adjustment_map.keys())
#     for d in dates_asc:
#         if d >= target_date: return adjustment_map[d]
#     return 1.0

# def adjust_per_share_value(raw_value, adjustment_factor):
#     v = to_float(raw_value)
#     f = to_float(adjustment_factor, 1.0)
#     if v is None: return None
#     return v * f if f > 0 else v

# def adjust_share_count(raw_shares, adjustment_factor):
#     v = to_float(raw_shares)
#     f = to_float(adjustment_factor, 1.0)
#     if v is None: return None
#     return v / f if f > 0 else v

# def get_closest_past_price(target_date, daily_quotes_asc, adj_map):
#     """
#     指定された日付(開示日など)から、最も近い過去の株価(分割調整後)を取得する
#     """
#     if not target_date or not daily_quotes_asc:
#         return None
#     # daily_quotes_asc は既に日付昇順にソートされている前提
#     closest_price = None
#     for q in daily_quotes_asc:
#         q_date = q.get("Date", "")[:10]
#         if q_date > target_date:
#             break
#         c = to_float(get_field(q, "Close", "C"))
#         if c is not None:
#             # その時点の株価を現在の分割基準に合わせる
#             adj_f = get_adjustment_factor_for_date(q_date, adj_map)
#             closest_price = adjust_per_share_value(c, adj_f)
#     return closest_price


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

#     fy_tracking = {}
#     revisions = []
#     other_events = [] 

#     for f in fins_sorted:
#         fy_en = f.get("CurFYEn", "")
#         if not fy_en or len(fy_en) < 10: continue
#         fy_en_date = fy_en[:10]
#         fy_label = f"{fy_en[:4]}年{int(fy_en[5:7])}月期"
#         disc_date = f.get("DiscDate", "")[:10]
#         cur_per_type = f.get("CurPerType", "")
        
#         flags = {
#             "MatChgSub": "子会社異動", "SigChgInC": "連結範囲変更",
#             "ChgByASRev": "会計基準変更", "ChgNoASRev": "会計方針変更",
#             "ChgAcEst": "会計見積り変更", "RetroRst": "修正再表示"
#         }
#         for k, v in flags.items():
#             if str(f.get(k, "")).lower() in ["true", "1"]:
#                 other_events.append({"date": disc_date, "type": "ACCOUNTING", "title": v, "desc": f"{cur_per_type}決算にて{v}の開示あり"})

#         if fy_en_date not in fy_tracking:
#             fy_tracking[fy_en_date] = {
#                 "fy": fy_label, "initial_sales": None, "final_sales": None, "latest_fsales": None,
#                 "initial_op": None, "final_op": None, "latest_fop": None, "sales_up": [], "sales_down": [], "op_up": [], "op_down": []
#             }
        
#         current_fsales = to_float(get_field(f, "FSales", "ForecastNetSales"))
#         current_fop = to_float(get_field(f, "FOP", "ForecastOperatingProfit"))
#         timing = cur_per_type if cur_per_type else "不明"
#         if timing == "FY": timing = "4Q"

#         if current_fsales is not None:
#             if fy_tracking[fy_en_date]["initial_sales"] is None: fy_tracking[fy_en_date]["initial_sales"] = current_fsales
#             prev_fsales = fy_tracking[fy_en_date]["latest_fsales"]
#             if prev_fsales is not None and current_fsales != prev_fsales:
#                 if current_fsales > prev_fsales: fy_tracking[fy_en_date]["sales_up"].append(timing)
#                 else: fy_tracking[fy_en_date]["sales_down"].append(timing)
#             fy_tracking[fy_en_date]["latest_fsales"] = current_fsales

#         if current_fop is not None:
#             if fy_tracking[fy_en_date]["initial_op"] is None: fy_tracking[fy_en_date]["initial_op"] = current_fop
#             prev_fop = fy_tracking[fy_en_date]["latest_fop"]
#             if prev_fop is not None and current_fop != prev_fop:
#                 diff = current_fop - prev_fop
#                 diff_pct = (diff / abs(prev_fop) * 100) if prev_fop != 0 else 0
#                 is_up = diff > 0
#                 if is_up: fy_tracking[fy_en_date]["op_up"].append(timing)
#                 else: fy_tracking[fy_en_date]["op_down"].append(timing)
#                 revisions.append({"date": disc_date, "fy": fy_label, "prev_fop": prev_fop, "new_fop": current_fop, "diff_pct": diff_pct, "is_up": is_up, "timing": timing})
#             fy_tracking[fy_en_date]["latest_fop"] = current_fop
        
#         if cur_per_type == "FY":
#             fy_tracking[fy_en_date]["final_op"] = to_float(get_field(f, "OP", "OperatingProfit"))
#             fy_tracking[fy_en_date]["final_sales"] = to_float(get_field(f, "Sales", "NetSales"))

#     guidance_history = []
#     for fy_en in sorted(fy_tracking.keys()):
#         track = fy_tracking[fy_en]
#         guidance_history.append({
#             "fy": track["fy"], "initial_sales": track["initial_sales"], "final_sales": track["final_sales"],
#             "initial_op": track["initial_op"], "final_op": track["final_op"],
#             "sales_achieve": (track["final_sales"] / track["initial_sales"] * 100) if track["final_sales"] and track["initial_sales"] else None,
#             "op_achieve": (track["final_op"] / track["initial_op"] * 100) if track["final_op"] and track["initial_op"] else None,
#             "sales_up": track["sales_up"], "sales_down": track["sales_down"], "op_up": track["op_up"], "op_down": track["op_down"]
#         })

#     fy_dict = {}
#     for f in fins_sorted:
#         if f.get("CurPerType") == "FY":
#             year = f.get("CurFYEn", "")[:4]
#             if year: fy_dict[year] = f
#     fy_fins = [fy_dict[y] for y in sorted(fy_dict.keys())]
#     fy_latest = fy_fins[-1] if fy_fins else {}

#     latest_fin = fins_sorted[-1] if fins_sorted else {}
#     cur_type = latest_fin.get("CurPerType", "")
#     prev_fin = next((f for f in reversed(fins_sorted[:-1]) if f.get("CurPerType") == cur_type), {})

#     sales = to_float(get_field(latest_fin, "Sales", "NetSales"))
#     op = to_float(get_field(latest_fin, "OP", "OperatingProfit"))
#     odp = to_float(get_field(latest_fin, "OdP", "OrdinaryProfit"))
#     np_latest = to_float(get_field(latest_fin, "NP", "ProfitAttributableToOwnersOfParent", "NetIncome"))
#     f_op = to_float(get_field(latest_fin, "FOP", "ForecastOperatingProfit"))
#     progress_op = None
#     if cur_type in ["1Q", "2Q", "3Q"] and op is not None and f_op and f_op > 0:
#         progress_op = (op / f_op) * 100

#     latest_target_date = latest_fin.get("CurPerEn", latest_fin.get("CurFYEn", ""))[:10]
#     adj_factor = get_adjustment_factor_for_date(latest_target_date, adj_map)

#     eps_raw = to_float(get_field(latest_fin, "EPS", "EarningsPerShare"))
#     eps_adj = adjust_per_share_value(eps_raw, adj_factor)
    
#     ta = to_float(get_field(latest_fin, "TA", "TotalAssets"))
#     equity = to_float(get_field(latest_fin, "Eq", "ShEq", "Equity", "NetAssets"))
#     out_sh_raw = to_float(get_field(latest_fin, "ShOutFY", "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
    
#     bps_raw = to_float(get_field(latest_fin, "BPS", "BookValuePerShare"))
#     if bps_raw is None and equity is not None and out_sh_raw is not None and out_sh_raw > 0:
#         bps_raw = equity / out_sh_raw
#     bps_adj = adjust_per_share_value(bps_raw, adj_factor)

#     dps_raw = to_float(get_field(latest_fin, "DivAnn", "ResultDividendPerShareAnnual", "ResultDPS"))
#     dps_adj = adjust_per_share_value(dps_raw, adj_factor)
    
#     equity_ratio = to_float(get_field(latest_fin, "EqAR", "EquityToAssetRatio"))
#     if equity_ratio is not None:
#         equity_ratio = equity_ratio * 100 if equity_ratio <= 1.0 else equity_ratio
#     elif equity and ta:
#         equity_ratio = (equity / ta) * 100

#     tr_sh_raw = to_float(get_field(latest_fin, "TrShFY", "TreasStock", "TreasuryStock"))
#     tr_sh = adjust_share_count(tr_sh_raw, adj_factor)
#     out_sh = adjust_share_count(out_sh_raw, adj_factor)
#     treasury_ratio = (tr_sh / out_sh * 100) if tr_sh is not None and out_sh and out_sh > 0 else None
    
#     avg_sh_raw = to_float(get_field(latest_fin, "AvgSh", "AverageNumberOfShares"))
#     avg_sh = adjust_share_count(avg_sh_raw, adj_factor)

#     deps_raw = to_float(get_field(latest_fin, "DEPS", "DilutedEarningsPerShare"))
#     dilution_rate = None
#     if deps_raw is not None and eps_raw is not None and eps_raw > 0:
#         dilution_rate = (1 - (deps_raw / eps_raw)) * 100

#     cfo = to_float(get_field(latest_fin, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#     cfi = to_float(get_field(latest_fin, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
#     cff = to_float(get_field(latest_fin, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
#     cash_eq = to_float(get_field(latest_fin, "CashEq", "CashAndCashEquivalents"))
#     prev_cash_eq = to_float(get_field(prev_fin, "CashEq", "CashAndCashEquivalents"))
#     cash_change = (cash_eq - prev_cash_eq) if cash_eq is not None and prev_cash_eq is not None else None
    
#     fcf = None
#     if cfo is not None or cfi is not None:
#         fcf = (cfo or 0) + (cfi or 0)

#     fy_prev = fy_fins[-2] if len(fy_fins) >= 2 else {}
#     np_prev = to_float(get_field(fy_prev, "NP", "ProfitAttributableToOwnersOfParent"))
#     eps_prev_raw = to_float(get_field(fy_prev, "EPS", "EarningsPerShare"))
#     avg_sh_prev_raw = to_float(get_field(fy_prev, "AvgSh", "AverageNumberOfShares"))
    
#     fy_latest_sales = to_float(get_field(fy_latest, "Sales", "NetSales"))
#     fy_latest_op = to_float(get_field(fy_latest, "OP", "OperatingProfit"))
#     fy_latest_odp = to_float(get_field(fy_latest, "OdP", "OrdinaryProfit"))
#     fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
#     fy_eps_raw = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
#     fy_avg_sh_raw = to_float(get_field(fy_latest, "AvgSh", "AverageNumberOfShares"))
    
#     fy_prev_cfo = to_float(get_field(fy_prev, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#     fy_cfo = to_float(get_field(fy_latest, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#     cfo_yoy = calc_yoy(fy_cfo, fy_prev_cfo)

#     eps_growth_factors = None
#     if fy_np and np_prev and np_prev > 0 and fy_avg_sh_raw and avg_sh_prev_raw and avg_sh_prev_raw > 0 and fy_eps_raw and eps_prev_raw and eps_prev_raw > 0:
#         eps_yoy_val = ((fy_eps_raw / eps_prev_raw) - 1) * 100
#         np_yoy_val = ((fy_np / np_prev) - 1) * 100
#         share_yoy_val = ((fy_avg_sh_raw / avg_sh_prev_raw) - 1) * 100
#         share_reduction_contribution = eps_yoy_val - np_yoy_val
#         eps_growth_factors = {"eps_yoy": eps_yoy_val, "np_yoy": np_yoy_val, "share_yoy": share_yoy_val, "share_effect": share_reduction_contribution}

#     def calc_dupont(fin_data):
#         if not fin_data: return None
#         d_s = to_float(get_field(fin_data, "Sales", "NetSales"))
#         d_np = to_float(get_field(fin_data, "NP", "ProfitAttributableToOwnersOfParent"))
#         d_ta = to_float(get_field(fin_data, "TA", "TotalAssets"))
#         d_eq = to_float(get_field(fin_data, "Eq", "ShEq", "Equity", "NetAssets"))
#         if d_s and d_np and d_ta and d_eq and d_eq > 0 and d_ta > 0:
#             return {"npm": (d_np / d_s) * 100, "at": d_s / d_ta, "fl": d_ta / d_eq, "roe": (d_np / d_eq) * 100}
#         return None

#     dupont_current = calc_dupont(fy_latest)
#     dupont_prev = calc_dupont(fy_prev)
    
#     prev_op = to_float(get_field(prev_fin, "OP", "OperatingProfit"))
#     prev_sales = to_float(get_field(prev_fin, "Sales", "NetSales"))
    
#     prev_eps_raw_for_yoy = to_float(get_field(prev_fin, "EPS", "EarningsPerShare"))
#     prev_target_date = prev_fin.get("DiscDate", prev_fin.get("CurPerEn", ""))[:10]
#     prev_eps_adj = adjust_per_share_value(prev_eps_raw_for_yoy, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
#     op_margin = calc_margin(op, sales)
#     prev_op_margin = calc_margin(prev_op, prev_sales)
#     op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

#     f_sales = to_float(get_field(latest_fin, "FSales", "ForecastNetSales"))
#     f_np = to_float(get_field(latest_fin, "FNP", "ForecastProfitAttributableToOwnersOfParent"))
#     f_odp = to_float(get_field(latest_fin, "FOdP", "ForecastOrdinaryProfit"))
#     f_eps_raw = to_float(get_field(latest_fin, "FEPS", "ForecastEarningsPerShare"))
#     f_eps_adj = adjust_per_share_value(f_eps_raw, adj_factor)

#     payout_ratio = to_float(get_field(latest_fin, "PayoutRatioAnn"))
#     if payout_ratio is None:
#         if dps_raw and f_eps_raw and f_eps_raw > 0: payout_ratio = (dps_raw / f_eps_raw) * 100
#         elif dps_raw and fy_latest:
#             fy_eps = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
#             if fy_eps and fy_eps > 0: payout_ratio = (dps_raw / fy_eps) * 100

#     per = to_float(get_field(valuation, "FwdPER", "PER"))
#     pbr = to_float(get_field(valuation, "PBR"))
#     mktcap = to_float(get_field(valuation, "MktCap"))

#     quotes_desc = sorted([q for q in daily_quotes_asc if to_float(get_field(q, "Close", "C")) is not None], key=lambda x: x.get("Date", ""), reverse=True)
#     latest_c = None
#     if len(quotes_desc) > 0:
#         ldate = quotes_desc[0].get("Date", "")[:10]
#         ladj = get_adjustment_factor_for_date(ldate, adj_map)
#         lraw = to_float(get_field(quotes_desc[0], "Close", "C"))
#         if lraw: latest_c = adjust_per_share_value(lraw, ladj)

#     div_yield = to_float(get_field(valuation, "DividendYield"))
#     if div_yield is not None and div_yield < 1.0: 
#         div_yield *= 100
#     if div_yield is None and dps_adj is not None and latest_c is not None and latest_c > 0:
#         div_yield = (dps_adj / latest_c) * 100
    
#     cfo_to_np = None
#     if fy_cfo is not None and fy_np and fy_np > 0: cfo_to_np = (fy_cfo / fy_np) * 100

#     roe = None
#     if f_np and equity and equity > 0: roe = (f_np / equity) * 100
#     elif fy_np and equity and equity > 0: roe = (fy_np / equity) * 100
#     else:
#         api_roe = to_float(get_field(valuation, "ROE"))
#         if api_roe is not None: roe = api_roe * 100

#     op_to_equity = None
#     if f_op and equity and equity > 0:
#         op_to_equity = (f_op / equity) * 100
#     elif fy_latest_op and equity and equity > 0:
#         op_to_equity = (fy_latest_op / equity) * 100

#     eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
#     peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

#     momentum = {
#         "ret_25d": None, "ret_75d": None, "ret_200d": None,
#         "ma25_diff": None, "ma75_diff": None,
#         "avg_val_25d": None, "vol_spike": None,
#         "dist_high": None, "dist_low": None,
#         "short_interest_change": None
#     }
#     if latest_c:
#         def get_past_price(days_ago):
#             if len(quotes_desc) > days_ago:
#                 q = quotes_desc[days_ago]
#                 d = q.get("Date", "")[:10]
#                 rc = to_float(get_field(q, "Close", "C"))
#                 if rc: return adjust_per_share_value(rc, get_adjustment_factor_for_date(d, adj_map))
#             return None

#         p25 = get_past_price(25)
#         p75 = get_past_price(75)
#         p200 = get_past_price(200)
        
#         momentum["ret_25d"] = calc_yoy(latest_c, p25)
#         momentum["ret_75d"] = calc_yoy(latest_c, p75)
#         momentum["ret_200d"] = calc_yoy(latest_c, p200)
        
#         if len(quotes_desc) >= 25:
#             recent_25 = quotes_desc[:25]
#             prices_25 = [adjust_per_share_value(to_float(get_field(q, "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_25]
#             volumes_25 = [adjust_share_count(to_float(get_field(q, "Volume", "V")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_25]
            
#             prices_25 = [p for p in prices_25 if p is not None]
#             volumes_25 = [v for v in volumes_25 if v is not None]
            
#             if len(prices_25) > 0:
#                 ma25 = sum(prices_25) / len(prices_25)
#                 momentum["ma25_diff"] = ((latest_c / ma25) - 1) * 100
            
#             if len(prices_25) > 0 and len(volumes_25) > 0:
#                 vals_25 = [p * v for p, v in zip(prices_25, volumes_25)]
#                 momentum["avg_val_25d"] = sum(vals_25) / len(vals_25)
                
#                 latest_vo = adjust_share_count(to_float(get_field(quotes_desc[0], "Volume", "V")), latest_adj_f)
#                 avg_vo_25 = sum(volumes_25) / len(volumes_25)
#                 if latest_vo and avg_vo_25 > 0:
#                     momentum["vol_spike"] = latest_vo / avg_vo_25

#         if len(quotes_desc) >= 75:
#             recent_75 = quotes_desc[:75]
#             prices_75 = [adjust_per_share_value(to_float(get_field(q, "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_75]
#             prices_75 = [p for p in prices_75 if p is not None]
#             if len(prices_75) > 0:
#                 ma75 = sum(prices_75) / len(prices_75)
#                 momentum["ma75_diff"] = ((latest_c / ma75) - 1) * 100

#         if len(quotes_desc) > 0:
#             recent_250 = quotes_desc[:250]
#             highs = [adjust_per_share_value(to_float(get_field(q, "High", "H", "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_250]
#             lows = [adjust_per_share_value(to_float(get_field(q, "Low", "L", "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_250]
#             highs = [h for h in highs if h is not None]
#             lows = [l for l in lows if l is not None]
            
#             if highs:
#                 highest = max(highs)
#                 if highest > 0: momentum["dist_high"] = ((latest_c / highest) - 1) * 100
#             if lows:
#                 lowest = min(lows)
#                 if lowest > 0: momentum["dist_low"] = ((latest_c / lowest) - 1) * 100

#     margin_interest = profile.get("margin_interest", [])
#     if not isinstance(margin_interest, list): margin_interest = []
#     margin_history = sorted([m for m in margin_interest if isinstance(m, dict) and m.get("Date")], key=lambda x: x.get("Date", ""))
#     margin_buy_latest = None
#     margin_ratio = None
#     if len(margin_history) > 0:
#         latest_m = margin_history[-1]
#         mb = to_float(get_field(latest_m, "LongVol", "margin_buy"))
#         ms = to_float(get_field(latest_m, "ShrtVol", "margin_sell"))
#         margin_buy_latest = mb
#         if mb is not None and ms and ms > 0: margin_ratio = mb / ms
        
#         if len(margin_history) > 1:
#             prev_m = margin_history[-2]
#             p_ms = to_float(get_field(prev_m, "ShrtVol", "margin_sell"))
#             if ms is not None and p_ms is not None:
#                 momentum["short_interest_change"] = ms - p_ms 

#     # ====== 年次（通期）ヒストリーの生成 ======
#     history = []
#     for i, fy in enumerate(fy_fins):
#         y_str = fy.get("CurFYEn", "")[:4]
#         s = to_float(get_field(fy, "Sales", "NetSales"))
#         o = to_float(get_field(fy, "OP", "OperatingProfit"))
#         odp = to_float(get_field(fy, "OdP", "OrdinaryProfit"))
#         eq = to_float(get_field(fy, "Eq", "Equity", "NetAssets"))
#         pr = to_float(get_field(fy, "NP", "ProfitAttributableToOwnersOfParent"))
#         r = (pr / eq) if pr and eq else to_float(get_field(fy, "ROE"))
        
#         cfo_fy = to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#         cfi_fy = to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
#         cff_fy = to_float(get_field(fy, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
        
#         fc = None
#         if cfo_fy is not None or cfi_fy is not None:
#             fc = (cfo_fy or 0) + (cfi_fy or 0)
        
#         target_date = fy.get("DiscDate", fy.get("CurFYEn", ""))[:10]
#         fy_adj_f = get_adjustment_factor_for_date(target_date, adj_map)
        
#         e_raw = to_float(get_field(fy, "EPS", "EarningsPerShare"))
#         e_adj = adjust_per_share_value(e_raw, fy_adj_f)
#         de_raw = to_float(get_field(fy, "DEPS", "DilutedEarningsPerShare"))
#         de_adj = adjust_per_share_value(de_raw, fy_adj_f)
        
#         out_s_raw = to_float(get_field(fy, "ShOutFY"))
#         tr_s_raw = to_float(get_field(fy, "TrShFY", "TreasStock"))
#         out_s_adj = adjust_share_count(out_s_raw, fy_adj_f)
#         tr_s_adj = adjust_share_count(tr_s_raw, fy_adj_f)
        
#         tr_ratio = (tr_s_adj / out_s_adj * 100) if tr_s_adj is not None and out_s_adj and out_s_adj > 0 else None
        
#         ta_fy = to_float(get_field(fy, "TA", "TotalAssets"))
#         eq_ratio_fy = to_float(get_field(fy, "EqAR", "EquityToAssetRatio"))
#         if eq_ratio_fy is not None:
#             eq_ratio_fy = eq_ratio_fy * 100 if eq_ratio_fy <= 1.0 else eq_ratio_fy
#         elif eq and ta_fy:
#             eq_ratio_fy = (eq / ta_fy) * 100
        
#         roa_fy = None
#         if pr and ta_fy and ta_fy > 0:
#             roa_fy = (pr / ta_fy) * 100

#         prev_s = to_float(get_field(fy_fins[i-1], "Sales", "NetSales")) if i > 0 else None
#         prev_o = to_float(get_field(fy_fins[i-1], "OP", "OperatingProfit")) if i > 0 else None
#         prev_odp = to_float(get_field(fy_fins[i-1], "OdP", "OrdinaryProfit")) if i > 0 else None
#         prev_pr = to_float(get_field(fy_fins[i-1], "NP", "ProfitAttributableToOwnersOfParent")) if i > 0 else None
        
#         prev_e_raw = to_float(get_field(fy_fins[i-1], "EPS", "EarningsPerShare")) if i > 0 else None
#         prev_date = fy_fins[i-1].get("DiscDate", "")[:10] if i > 0 else ""
#         prev_e_adj = adjust_per_share_value(prev_e_raw, get_adjustment_factor_for_date(prev_date, adj_map)) if i > 0 else None

#         prev_out_s_raw = to_float(get_field(fy_fins[i-1], "ShOutFY")) if i > 0 else None
#         prev_tr_s_raw = to_float(get_field(fy_fins[i-1], "TrShFY", "TreasStock")) if i > 0 else None
#         prev_fy_adj_f = get_adjustment_factor_for_date(prev_date, adj_map) if prev_date else 1.0
        
#         prev_out_s_adj = adjust_share_count(prev_out_s_raw, prev_fy_adj_f)
#         prev_tr_s_adj = adjust_share_count(prev_tr_s_raw, prev_fy_adj_f)
        
#         # ★ PER/PBRの計算 ★
#         closest_p = get_closest_past_price(target_date, daily_quotes_asc, adj_map)
#         calc_per = None
#         calc_pbr = None
#         if closest_p is not None:
#             if e_adj and e_adj > 0:
#                 calc_per = closest_p / e_adj
            
#             bps_raw_hist = to_float(get_field(fy, "BPS", "BookValuePerShare"))
#             if bps_raw_hist is None and eq is not None and out_s_raw is not None and out_s_raw > 0:
#                 bps_raw_hist = eq / out_s_raw
            
#             if bps_raw_hist is not None:
#                 bps_adj_hist = adjust_per_share_value(bps_raw_hist, fy_adj_f)
#                 if bps_adj_hist and bps_adj_hist > 0:
#                     calc_pbr = closest_p / bps_adj_hist
        
#         history.append({
#             "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
#             "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
#             "odp_str": format_jpy(odp), "odp_raw": odp, "odp_yoy": calc_yoy(odp, prev_odp),
#             "np_str": format_jpy(pr), "np_raw": pr, "np_yoy": calc_yoy(pr, prev_pr),
#             "op_margin": calc_margin(o, s),
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj, "eps_yoy": calc_yoy(e_adj, prev_e_adj),
#             "roe_raw": r * 100 if r and r < 1.0 else r,
#             "roa_estimate": roa_fy,
#             "equity_ratio": eq_ratio_fy,
#             "cfo": cfo_fy, "cfi": cfi_fy, "cff": cff_fy,
#             "fcf_raw": fc, "fcf_margin": calc_margin(fc, s),
#             "out_shares": out_s_adj, "tr_shares": tr_s_adj, "tr_ratio": tr_ratio,
#             "out_shares_yoy": calc_yoy(out_s_adj, prev_out_s_adj), "tr_shares_yoy": calc_yoy(tr_s_adj, prev_tr_s_adj),
#             "calc_per": calc_per,
#             "calc_pbr": calc_pbr
#         })

#     sales_cagr_3y = None
#     op_cagr_3y = None
#     eps_cagr_3y = None
#     if len(history) >= 4:
#         latest_hist = history[-1]
#         past_hist = history[-4]
#         sales_cagr_3y = calc_cagr(latest_hist["sales_raw"], past_hist["sales_raw"], 3)
#         op_cagr_3y = calc_cagr(latest_hist["op_raw"], past_hist["op_raw"], 3)
#         eps_cagr_3y = calc_cagr(latest_hist["eps_adjusted"], past_hist["eps_adjusted"], 3)

#     if f_sales or f_op or f_eps_raw:
#         next_year = str(int(history[-1]["year"]) + 1) if history else "予"
#         history.append({
#             "year": f"{next_year}(予)", 
#             "sales_str": format_jpy(f_sales), "sales_raw": f_sales, 
#             "sales_yoy": calc_yoy(f_sales, fy_latest_sales),
#             "op_str": format_jpy(f_op), "op_raw": f_op, 
#             "op_yoy": calc_yoy(f_op, fy_latest_op),
#             "odp_str": format_jpy(f_odp), "odp_raw": f_odp, 
#             "odp_yoy": calc_yoy(f_odp, fy_latest_odp),
#             "np_str": format_jpy(f_np), "np_raw": f_np, 
#             "np_yoy": calc_yoy(f_np, fy_np),
#             "op_margin": calc_margin(f_op, f_sales),
#             "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "deps_adjusted": None, 
#             "eps_yoy": calc_yoy(f_eps_adj, history[-1]["eps_adjusted"] if history else None),
#             "roe_raw": None, "roa_estimate": None, "equity_ratio": None,
#             "cfo": None, "cfi": None, "cff": None, "fcf_raw": None, "fcf_margin": None,
#             "out_shares": None, "tr_shares": None, "tr_ratio": None,
#             "out_shares_yoy": None, "tr_shares_yoy": None,
#             "calc_per": per, "calc_pbr": pbr
#         })

#     # ====== 四半期（Quarterly）ヒストリーの生成 ======
#     actual_fins = [f for f in fins_sorted if isinstance(f, dict) and f.get("CurPerType") in ["1Q", "2Q", "3Q", "FY"]]
    
#     fy_tree = {}
#     for f in actual_fins:
#         year = f.get("CurFYEn", "")[:4]
#         q_type = f.get("CurPerType", "")
#         if year and q_type:
#             if year not in fy_tree: fy_tree[year] = {}
#             fy_tree[year][q_type] = f

#     single_q_data = {}
#     for year in sorted(fy_tree.keys()):
#         for qt in ["1Q", "2Q", "3Q", "FY"]:
#             if qt not in fy_tree[year]: continue
#             q_data = fy_tree[year][qt]
            
#             c_sales = to_float(get_field(q_data, "Sales", "NetSales"))
#             c_op = to_float(get_field(q_data, "OP", "OperatingProfit"))
#             c_odp = to_float(get_field(q_data, "OdP", "OrdinaryProfit"))
#             c_np = to_float(get_field(q_data, "NP", "ProfitAttributableToOwnersOfParent"))
            
#             s_sales, s_op, s_odp, s_np = c_sales, c_op, c_odp, c_np
            
#             prev_qt = {"2Q":"1Q", "3Q":"2Q", "FY":"3Q"}.get(qt)
#             if prev_qt and prev_qt in fy_tree[year]:
#                 p_data = fy_tree[year][prev_qt]
#                 p_c_sales = to_float(get_field(p_data, "Sales", "NetSales"))
#                 p_c_op = to_float(get_field(p_data, "OP", "OperatingProfit"))
#                 p_c_odp = to_float(get_field(p_data, "OdP", "OrdinaryProfit"))
#                 p_c_np = to_float(get_field(p_data, "NP", "ProfitAttributableToOwnersOfParent"))
#                 if c_sales is not None and p_c_sales is not None: s_sales = c_sales - p_c_sales
#                 if c_op is not None and p_c_op is not None: s_op = c_op - p_c_op
#                 if c_odp is not None and p_c_odp is not None: s_odp = c_odp - p_c_odp
#                 if c_np is not None and p_c_np is not None: s_np = c_np - p_c_np
                
#             single_q_data[f"{year}-{qt}"] = {"sales": s_sales, "op": s_op, "odp": s_odp, "np": s_np, "raw": q_data}

#     sorted_keys_full = sorted(single_q_data.keys())
#     quarterly_history = []
#     earnings_events = [] 
    
#     for idx, k in enumerate(sorted_keys_full):
#         year_str, q_type = k.split("-")
#         curr = single_q_data[k]
#         q_raw = curr["raw"]
        
#         prev_year_str = str(int(year_str) - 1)
#         prev_k = f"{prev_year_str}-{q_type}"
#         prev_q = single_q_data.get(prev_k, {})
        
#         s_yoy = calc_yoy(curr["sales"], prev_q.get("sales"))
#         o_yoy = calc_yoy(curr["op"], prev_q.get("op"))
#         odp_yoy = calc_yoy(curr["odp"], prev_q.get("odp"))
#         np_yoy = calc_yoy(curr["np"], prev_q.get("np"))
        
#         prev_q_raw_qoq = single_q_data[sorted_keys_full[idx - 1]]["raw"] if idx > 0 else {}
        
#         target_date = q_raw.get("DiscDate", q_raw.get("CurPerEn", ""))[:10]
#         q_adj_f = get_adjustment_factor_for_date(target_date, adj_map)
        
#         e_raw = to_float(get_field(q_raw, "EPS", "EarningsPerShare"))
#         de_raw = to_float(get_field(q_raw, "DEPS", "DilutedEarningsPerShare"))
#         e_adj = adjust_per_share_value(e_raw, q_adj_f)
#         de_adj = adjust_per_share_value(de_raw, q_adj_f)
        
#         out_s_raw = to_float(get_field(q_raw, "ShOutFY"))
#         tr_s_raw = to_float(get_field(q_raw, "TrShFY", "TreasStock"))
#         out_s_adj = adjust_share_count(out_s_raw, q_adj_f)
#         tr_s_adj = adjust_share_count(tr_s_raw, q_adj_f)
        
#         prev_target_date = prev_q_raw_qoq.get("DiscDate", "")[:10] if prev_q_raw_qoq else ""
#         prev_q_adj_f = get_adjustment_factor_for_date(prev_target_date, adj_map) if prev_target_date else 1.0
        
#         prev_e_raw = to_float(get_field(prev_q_raw_qoq, "EPS", "EarningsPerShare"))
#         prev_e_adj = adjust_per_share_value(prev_e_raw, prev_q_adj_f)

#         prev_out_s_raw = to_float(get_field(prev_q_raw_qoq, "ShOutFY"))
#         prev_tr_s_raw = to_float(get_field(prev_q_raw_qoq, "TrShFY", "TreasStock"))
#         prev_out_s_adj = adjust_share_count(prev_out_s_raw, prev_q_adj_f)
#         prev_tr_s_adj = adjust_share_count(prev_tr_s_raw, prev_q_adj_f)

#         tr_ratio = (tr_s_adj / out_s_adj * 100) if tr_s_adj is not None and out_s_adj and out_s_adj > 0 else None
#         label = f"{year_str[-2:]}年 {q_type.replace('FY', '4Q')}" 
        
#         disc_date = q_raw.get("DiscDate", "")[:10]
#         if disc_date:
#             earnings_events.append({
#                 "date": disc_date, "title": label, "sales_str": format_jpy(curr["sales"]), "sales_yoy": s_yoy,
#                 "op_str": format_jpy(curr["op"]), "op_yoy": o_yoy
#             })
            
#         cfo_q = to_float(get_field(q_raw, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#         cfi_q = to_float(get_field(q_raw, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
#         cff_q = to_float(get_field(q_raw, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
        
#         fcf_q = (cfo_q or 0) + (cfi_q or 0) if (cfo_q is not None or cfi_q is not None) else None
        
#         eq_q = to_float(get_field(q_raw, "Eq", "Equity", "NetAssets"))
#         ta_q = to_float(get_field(q_raw, "TA", "TotalAssets"))
#         eq_ratio_q = to_float(get_field(q_raw, "EqAR", "EquityToAssetRatio"))
#         if eq_ratio_q is not None:
#             eq_ratio_q = eq_ratio_q * 100 if eq_ratio_q <= 1.0 else eq_ratio_q
#         elif eq_q and ta_q:
#             eq_ratio_q = (eq_q / ta_q) * 100
        
#         annualization_factor = 1.0
#         if q_type == "1Q": annualization_factor = 4.0
#         elif q_type == "2Q": annualization_factor = 2.0
#         elif q_type == "3Q": annualization_factor = 4.0 / 3.0

#         roa_q = None
#         if curr["np"] and ta_q and ta_q > 0:
#             roa_q = ((curr["np"] * annualization_factor) / ta_q) * 100
            
#         roe_q = None
#         if curr["np"] and eq_q and eq_q > 0:
#             roe_q = ((curr["np"] * annualization_factor) / eq_q) * 100
            
#         # ★ 四半期の PER/PBRの計算 ★
#         closest_p = get_closest_past_price(target_date, daily_quotes_asc, adj_map)
#         calc_per = None
#         calc_pbr = None
#         if closest_p is not None:
#             # EPSは年率換算されたものを期待値としてPERを出す
#             if e_adj and e_adj > 0:
#                 calc_per = closest_p / (e_adj * annualization_factor)
            
#             bps_raw_q = to_float(get_field(q_raw, "BPS", "BookValuePerShare"))
#             if bps_raw_q is None and eq_q is not None and out_s_raw is not None and out_s_raw > 0:
#                 bps_raw_q = eq_q / out_s_raw
            
#             if bps_raw_q is not None:
#                 bps_adj_q = adjust_per_share_value(bps_raw_q, q_adj_f)
#                 if bps_adj_q and bps_adj_q > 0:
#                     calc_pbr = closest_p / bps_adj_q
        
#         quarterly_history.append({
#             "year": label, "sales_str": format_jpy(curr["sales"]), "sales_raw": curr["sales"], "sales_yoy": s_yoy,
#             "op_str": format_jpy(curr["op"]), "op_raw": curr["op"], "op_yoy": o_yoy,
#             "odp_str": format_jpy(curr["odp"]), "odp_raw": curr["odp"], "odp_yoy": odp_yoy,
#             "np_str": format_jpy(curr["np"]), "np_raw": curr["np"], "np_yoy": np_yoy,
#             "op_margin": calc_margin(curr["op"], curr["sales"]),
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj, "eps_yoy": calc_yoy(e_adj, prev_e_adj),
#             "out_shares": out_s_adj, "tr_shares": tr_s_adj, "tr_ratio": tr_ratio,
#             "out_shares_yoy": calc_yoy(out_s_adj, prev_out_s_adj), "tr_shares_yoy": calc_yoy(tr_s_adj, prev_tr_s_adj),
#             "roe_raw": roe_q,
#             "roa_estimate": roa_q,
#             "equity_ratio": eq_ratio_q,
#             "cfo": cfo_q, "cfi": cfi_q, "cff": cff_q,
#             "fcf_raw": fcf_q, "fcf_margin": calc_margin(fcf_q, curr["sales"]),
#             "calc_per": calc_per,
#             "calc_pbr": calc_pbr
#         })

#     op_margins_3y = []
#     for fy in fy_fins[-4:-1]:
#         s = to_float(get_field(fy, "Sales", "NetSales"))
#         o = to_float(get_field(fy, "OP", "OperatingProfit"))
#         if s and o and s > 0: op_margins_3y.append((o / s) * 100)
#     avg_op_margin_3y = sum(op_margins_3y) / len(op_margins_3y) if op_margins_3y else None

#     eps_yoy_3y = []
#     for i in range(len(fy_fins)-4, len(fy_fins)-1):
#         if i < 1: continue
#         c_eps = to_float(get_field(fy_fins[i], "EPS", "EarningsPerShare"))
#         p_eps = to_float(get_field(fy_fins[i-1], "EPS", "EarningsPerShare"))
#         if c_eps is not None and p_eps is not None and p_eps != 0:
#             eps_yoy_3y.append(((c_eps - p_eps) / abs(p_eps)) * 100)
#     avg_eps_yoy_3y = sum(eps_yoy_3y) / len(eps_yoy_3y) if eps_yoy_3y else None

#     major_history = profile.get("major_shareholders", [])
#     if not isinstance(major_history, list): major_history = [major_history] if major_history else []
#     def extract_shareholders(data_dict):
#         if not isinstance(data_dict, dict): return []
#         return data_dict.get("Hldrs") or data_dict.get("MajorShareholders") or data_dict.get("Shareholders") or []
#     curr_majors = extract_shareholders(major_history[-1]) if len(major_history) > 0 else []
#     prev_majors = extract_shareholders(major_history[-2]) if len(major_history) > 1 else []
    
#     prev_map = {}
#     for s in prev_majors:
#         name = s.get("HldrName") or s.get("Name")
#         ratio = to_float(s.get("ShsRatio") or s.get("HoldingRatio"))
#         if name and ratio is not None: prev_map[name] = ratio

#     processed_majors = []
#     for idx, s in enumerate(curr_majors):
#         name = s.get("HldrName") or s.get("Name") or "不明"
#         ratio = to_float(s.get("ShsRatio") or s.get("HoldingRatio"))
#         diff = None
#         if ratio is not None:
#             if ratio <= 1.0: ratio *= 100
#             if name in prev_map:
#                 p_ratio = prev_map[name]
#                 if p_ratio <= 1.0: p_ratio *= 100
#                 diff = ratio - p_ratio
#         processed_majors.append({"rank": s.get("Rank") or (idx + 1), "name": name, "ratio": ratio, "diff": diff})

#     val_dict = {v.get("Date"): v for v in valuation.get("valuation_history", []) if isinstance(v, dict) and "Date" in v}
#     topix_dict = {t.get("Date", "")[:10]: to_float(t.get("C", t.get("Close"))) for t in profile.get("topix_daily", []) if isinstance(t, dict) and "Date" in t}
#     sector_dict = {s.get("Date", "")[:10]: to_float(s.get("C", s.get("Close"))) for s in profile.get("sector_daily", []) if isinstance(s, dict) and "Date" in s}

#     price_margin_history = []
#     last_topix = None
#     last_sector = None

#     for q in daily_quotes_asc:
#         date_str = q.get("Date", "")[:10]
#         if not date_str: continue
        
#         adj_f = get_adjustment_factor_for_date(date_str, adj_map)

#         adj_c = to_float(get_field(q, "AdjC", "AdjClose", "adj_c", "adj_close"))
#         if adj_c is None:
#             raw_c = to_float(get_field(q, "Close", "C"))
#             if raw_c is None: continue
#             adj_c = adjust_per_share_value(raw_c, adj_f)

#         adj_o = to_float(get_field(q, "AdjO", "AdjOpen"))
#         if adj_o is None:
#             raw_o = to_float(get_field(q, "Open", "O"))
#             adj_o = adjust_per_share_value(raw_o, adj_f) if raw_o is not None else adj_c
            
#         adj_h = to_float(get_field(q, "AdjH", "AdjHigh"))
#         if adj_h is None:
#             raw_h = to_float(get_field(q, "High", "H"))
#             adj_h = adjust_per_share_value(raw_h, adj_f) if raw_h is not None else adj_c
            
#         adj_l = to_float(get_field(q, "AdjL", "AdjLow"))
#         if adj_l is None:
#             raw_l = to_float(get_field(q, "Low", "L"))
#             adj_l = adjust_per_share_value(raw_l, adj_f) if raw_l is not None else adj_c
            
#         adj_vo = to_float(get_field(q, "AdjVo", "AdjVolume"))
#         if adj_vo is None:
#             raw_vo = to_float(get_field(q, "Volume", "V"))
#             adj_vo = adjust_share_count(raw_vo, adj_f) if raw_vo is not None else None
        
#         v = val_dict.get(date_str, {}) 
#         curr_topix = topix_dict.get(date_str)
#         if curr_topix is not None: last_topix = curr_topix
            
#         curr_sector = sector_dict.get(date_str)
#         if curr_sector is not None: last_sector = curr_sector

#         price_margin_history.append({
#             "date": date_str, "open": adj_o, "high": adj_h, "low": adj_l, "close": adj_c, "volume": adj_vo,
#             "per": to_float(get_field(v, "FwdPER", "PER")),
#             "pbr": to_float(get_field(v, "PBR")),
#             "market_cap": to_float(get_field(v, "MktCap")),
#             "topix": last_topix,
#             "sector": last_sector
#         })

#     stock_perf_1y = None
#     topix_perf_1y = None
#     sector_perf_1y = None
#     if len(price_margin_history) > 250:
#         current_close = price_margin_history[-1].get("close")
#         close_1y_ago = price_margin_history[-250].get("close")
#         if current_close and close_1y_ago:
#             stock_perf_1y = (current_close - close_1y_ago) / close_1y_ago * 100
            
#         current_topix = price_margin_history[-1].get("topix")
#         topix_1y_ago = price_margin_history[-250].get("topix")
#         if current_topix and topix_1y_ago:
#             topix_perf_1y = (current_topix - topix_1y_ago) / topix_1y_ago * 100

#         current_sector = price_margin_history[-1].get("sector")
#         sector_1y_ago = price_margin_history[-250].get("sector")
#         if current_sector and sector_1y_ago:
#             sector_perf_1y = (current_sector - sector_1y_ago) / sector_1y_ago * 100

#     return {
#         "basic": { 
#             "code": normalize_code(profile.get("code")), 
#             "company_name": info.get("CompanyName", info.get("CoName", "-")), 
#             "industry": info.get("Sector33CodeName") or info.get("S33Nm") or info.get("Sector17CodeName") or info.get("S17Nm") or "-",
#             "market": info.get("MarketCodeName", info.get("MktNm", "-")) 
#         },
#         "period": { "current_type": cur_type, "disclosure_date": latest_fin.get("DiscDate", "") },
#         "actual": { 
#             "sales": sales, "op": op, "odp": odp, "net_income": np_latest, "eps_raw": eps_raw, "eps_adjusted": eps_adj, 
#             "bps": bps_adj, "dps": dps_adj,
#             "cfo": cfo, "cfi": cfi, "cff": cff, "fcf": fcf, "fcf_margin": calc_margin(fcf, sales),
#             "cash_eq": cash_eq, "cash_change": cash_change,
#             "out_sh": out_sh, "tr_sh": tr_sh, "avg_sh": avg_sh, "deps_raw": deps_raw 
#         },
#         "forecast": { "sales": f_sales, "op": f_op, "odp": f_odp, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
#         "growth": { 
#             "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
#             "eps_yoy": eps_yoy_adjusted, "sales_cagr_3y": sales_cagr_3y, "op_cagr_3y": op_cagr_3y, "eps_cagr_3y": eps_cagr_3y,
#             "progress_op": progress_op, "avg_eps_yoy_3y": avg_eps_yoy_3y,
#             "np_yoy": eps_growth_factors.get("np_yoy") if eps_growth_factors else None
#         },
#         "profitability": { 
#             "op_margin": op_margin, "op_margin_change": op_margin_change, "avg_op_margin_3y": avg_op_margin_3y,
#             "roe": roe, "op_to_equity": op_to_equity, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
#             "equity_ratio": equity_ratio, "payout_ratio": payout_ratio,
#             "cfo_to_np": cfo_to_np, "treasury_ratio": treasury_ratio,
#             "dilution_rate": dilution_rate, "eps_growth_factors": eps_growth_factors, 
#             "dupont": {"current": dupont_current, "prev": dupont_prev}
#         },
#         "quality": {
#             "cfo_yoy": cfo_yoy,
#             "working_capital_change": None,
#             "capex": None,
#             "depreciation": None
#         },
#         "momentum": momentum,
#         "health": {
#             "roic": None,
#             "net_cash": None,
#             "debt_ebitda": None,
#             "icr": None
#         },
#         "valuation": { 
#             "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
#             "dividend_yield": div_yield,
#             **get_valuation_statistics(profile.get("valuation_history", [])) 
#         },
#         "market_perf": { 
#             "stock_1y": stock_perf_1y, "topix_1y": topix_perf_1y, "sector_1y": sector_perf_1y,
#             "margin_buy": margin_buy_latest, "margin_ratio": margin_ratio
#         },
#         "history": history,
#         "quarterly_history": quarterly_history,
#         "price_margin_history": price_margin_history,
#         "major_shareholders": processed_majors,
#         "large_volume": profile.get("large_volume", []),
#         "cross_shareholdings": profile.get("cross_shareholdings", {}),
#         "events": { "revisions": revisions, "other": other_events, "earnings": earnings_events },
#         "guidance_history": guidance_history
#     }


# backend/analyzer.py

from backend.utils.finance import (
    to_float, format_jpy, calc_yoy, calc_cagr, calc_margin, get_field, normalize_code
)
from statistics import median
import math

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
        f = to_float(get_field(q, "AdjustmentFactor", "AdjFactor", "adj_factor"), 1.0)
        if f > 0 and f != 1.0: 
            factors_by_date[q.get("Date")[:10]] = f
            
    adjustment_map = {}
    for q in quotes_asc:
        date = q.get("Date", "")[:10]
        cum_factor = 1.0
        for factor_date, f in factors_by_date.items():
            if factor_date > date: 
                cum_factor *= f
        adjustment_map[date] = cum_factor
        
    return adjustment_map

def get_adjustment_factor_for_date(target_date, adjustment_map):
    if not target_date or not adjustment_map: return 1.0
    target_date = target_date[:10]
    if target_date in adjustment_map: return adjustment_map[target_date]
    
    dates_asc = sorted(adjustment_map.keys())
    for d in dates_asc:
        if d >= target_date: return adjustment_map[d]
    return 1.0

def adjust_per_share_value(raw_value, adjustment_factor):
    v = to_float(raw_value)
    f = to_float(adjustment_factor, 1.0)
    if v is None: return None
    return v * f if f > 0 else v

def adjust_share_count(raw_shares, adjustment_factor):
    v = to_float(raw_shares)
    f = to_float(adjustment_factor, 1.0)
    if v is None: return None
    return v / f if f > 0 else v

def get_closest_past_price(target_date, daily_quotes_asc, adj_map):
    if not target_date or not daily_quotes_asc:
        return None
    closest_price = None
    for q in daily_quotes_asc:
        q_date = q.get("Date", "")[:10]
        if q_date > target_date:
            break
        c = to_float(get_field(q, "Close", "C"))
        if c is not None:
            adj_f = get_adjustment_factor_for_date(q_date, adj_map)
            closest_price = adjust_per_share_value(c, adj_f)
    return closest_price

def get_q_order(q_type):
    mapping = {"1Q": 1, "2Q": 2, "3Q": 3, "4Q": 4, "5Q": 5, "FY": 9}
    return mapping.get(q_type, 99)

def get_latest_forecast_val(fins_list, field_names):
    for f in reversed(fins_list):
        v = to_float(get_field(f, *field_names))
        if v is not None:
            return v
    return None

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
    
    # 全ての開示（予想修正も含む）
    fins_sorted = sorted([f for f in fins if isinstance(f, dict) and f.get("DiscDate")], key=lambda x: x.get("DiscDate", ""))
    
    # ★追加: 「決算短信（実績データ）」のみに絞り込んだリスト
    # DocTypeに "FinancialStatements" が含まれるものだけを抽出する
    actual_fins_sorted = [f for f in fins_sorted if "FinancialStatements" in f.get("DocType", "")]

    fy_tracking = {}
    revisions = []
    other_events = [] 

    # ガイダンス（予実トラッキング）やイベント取得用には全ての開示(fins_sorted)を使う
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
                other_events.append({"date": disc_date, "type": "ACCOUNTING", "title": v, "desc": f"{cur_per_type}決算にて{v}の開示あり"})

        if fy_en_date not in fy_tracking:
            fy_tracking[fy_en_date] = {
                "fy": fy_label, "initial_sales": None, "final_sales": None, "latest_fsales": None,
                "initial_op": None, "final_op": None, "latest_fop": None, "sales_up": [], "sales_down": [], "op_up": [], "op_down": []
            }
        
        current_fsales = to_float(get_field(f, "FSales", "ForecastNetSales"))
        current_fop = to_float(get_field(f, "FOP", "ForecastOperatingProfit"))
        timing = cur_per_type if cur_per_type else "不明"
        if timing == "FY": timing = "4Q"

        if current_fsales is not None:
            if fy_tracking[fy_en_date]["initial_sales"] is None: fy_tracking[fy_en_date]["initial_sales"] = current_fsales
            prev_fsales = fy_tracking[fy_en_date]["latest_fsales"]
            if prev_fsales is not None and current_fsales != prev_fsales:
                if current_fsales > prev_fsales: fy_tracking[fy_en_date]["sales_up"].append(timing)
                else: fy_tracking[fy_en_date]["sales_down"].append(timing)
            fy_tracking[fy_en_date]["latest_fsales"] = current_fsales

        if current_fop is not None:
            if fy_tracking[fy_en_date]["initial_op"] is None: fy_tracking[fy_en_date]["initial_op"] = current_fop
            prev_fop = fy_tracking[fy_en_date]["latest_fop"]
            if prev_fop is not None and current_fop != prev_fop:
                diff = current_fop - prev_fop
                diff_pct = (diff / abs(prev_fop) * 100) if prev_fop != 0 else 0
                is_up = diff > 0
                if is_up: fy_tracking[fy_en_date]["op_up"].append(timing)
                else: fy_tracking[fy_en_date]["op_down"].append(timing)
                revisions.append({"date": disc_date, "fy": fy_label, "prev_fop": prev_fop, "new_fop": current_fop, "diff_pct": diff_pct, "is_up": is_up, "timing": timing})
            fy_tracking[fy_en_date]["latest_fop"] = current_fop
        
        # 最終実績は、実績開示のみから取るよう修正
        if cur_per_type == "FY" and "FinancialStatements" in f.get("DocType", ""):
            fy_tracking[fy_en_date]["final_op"] = to_float(get_field(f, "OP", "OperatingProfit"))
            fy_tracking[fy_en_date]["final_sales"] = to_float(get_field(f, "Sales", "NetSales"))

    guidance_history = []
    for fy_en in sorted(fy_tracking.keys()):
        track = fy_tracking[fy_en]
        guidance_history.append({
            "fy": track["fy"], "initial_sales": track["initial_sales"], "final_sales": track["final_sales"],
            "initial_op": track["initial_op"], "final_op": track["final_op"],
            "sales_achieve": (track["final_sales"] / track["initial_sales"] * 100) if track["final_sales"] and track["initial_sales"] else None,
            "op_achieve": (track["final_op"] / track["initial_op"] * 100) if track["final_op"] and track["initial_op"] else None,
            "sales_up": track["sales_up"], "sales_down": track["sales_down"], "op_up": track["op_up"], "op_down": track["op_down"]
        })

    # 通期のデータ抽出（実績のみ）
    fy_dict = {}
    for f in actual_fins_sorted:
        if f.get("CurPerType") == "FY":
            year = f.get("CurFYEn", "")[:4]
            if year: fy_dict[year] = f
    fy_fins = [fy_dict[y] for y in sorted(fy_dict.keys())]
    fy_latest = fy_fins[-1] if fy_fins else {}

    # 最新実績
    latest_fin = actual_fins_sorted[-1] if actual_fins_sorted else {}
    cur_type = latest_fin.get("CurPerType", "")
    prev_fin = next((f for f in reversed(actual_fins_sorted[:-1]) if f.get("CurPerType") == cur_type), {})

    sales = to_float(get_field(latest_fin, "Sales", "NetSales"))
    op = to_float(get_field(latest_fin, "OP", "OperatingProfit"))
    odp = to_float(get_field(latest_fin, "OdP", "OrdinaryProfit"))
    np_latest = to_float(get_field(latest_fin, "NP", "ProfitAttributableToOwnersOfParent", "NetIncome"))
    
    # 予想データは、全開示(fins_sorted)から最新のものを引っ張ってくる
    is_latest_fy = (cur_type == "FY")
    if is_latest_fy:
        f_sales = get_latest_forecast_val(fins_sorted, ["NxFSales", "ForecastNetSales"])
        f_np = get_latest_forecast_val(fins_sorted, ["NxFNp", "ForecastProfitAttributableToOwnersOfParent"])
        f_odp = get_latest_forecast_val(fins_sorted, ["NxFOdP", "ForecastOrdinaryProfit"])
        f_op = get_latest_forecast_val(fins_sorted, ["NxFOP", "ForecastOperatingProfit"])
        f_eps_raw = get_latest_forecast_val(fins_sorted, ["NxFEPS", "ForecastEarningsPerShare"])
        f_div_raw = get_latest_forecast_val(fins_sorted, ["NxFDivAnn", "NxFDivFY"])
    else:
        f_sales = get_latest_forecast_val(fins_sorted, ["FSales", "ForecastNetSales"])
        f_np = get_latest_forecast_val(fins_sorted, ["FNP", "ForecastProfitAttributableToOwnersOfParent"])
        f_odp = get_latest_forecast_val(fins_sorted, ["FOdP", "ForecastOrdinaryProfit"])
        f_op = get_latest_forecast_val(fins_sorted, ["FOP", "ForecastOperatingProfit"])
        f_eps_raw = get_latest_forecast_val(fins_sorted, ["FEPS", "ForecastEarningsPerShare"])
        f_div_raw = get_latest_forecast_val(fins_sorted, ["FDivAnn", "FDivFY"])
    
    progress_op = None
    if cur_type in ["1Q", "2Q", "3Q", "4Q", "5Q"] and op is not None and f_op and f_op > 0:
        progress_op = (op / f_op) * 100

    latest_target_date = latest_fin.get("CurPerEn", latest_fin.get("CurFYEn", ""))[:10]
    adj_factor = get_adjustment_factor_for_date(latest_target_date, adj_map)

    eps_raw = to_float(get_field(latest_fin, "EPS", "EarningsPerShare"))
    eps_adj = adjust_per_share_value(eps_raw, adj_factor)
    
    ta = to_float(get_field(latest_fin, "TA", "TotalAssets"))
    equity = to_float(get_field(latest_fin, "Eq", "ShEq", "Equity", "NetAssets"))
    out_sh_raw = to_float(get_field(latest_fin, "ShOutFY", "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
    
    bps_raw = to_float(get_field(latest_fin, "BPS", "BookValuePerShare"))
    if bps_raw is None and equity is not None and out_sh_raw is not None and out_sh_raw > 0:
        bps_raw = equity / out_sh_raw
    bps_adj = adjust_per_share_value(bps_raw, adj_factor)

    dps_raw = to_float(get_field(latest_fin, "DivAnn", "ResultDividendPerShareAnnual", "ResultDPS"))
    dps_adj = adjust_per_share_value(dps_raw, adj_factor)
    
    equity_ratio = to_float(get_field(latest_fin, "EqAR", "EquityToAssetRatio"))
    if equity_ratio is not None:
        equity_ratio = equity_ratio * 100 if equity_ratio <= 1.0 else equity_ratio
    elif equity and ta:
        equity_ratio = (equity / ta) * 100

    tr_sh_raw = to_float(get_field(latest_fin, "TrShFY", "TreasStock", "TreasuryStock"))
    tr_sh = adjust_share_count(tr_sh_raw, adj_factor)
    out_sh = adjust_share_count(out_sh_raw, adj_factor)
    treasury_ratio = (tr_sh / out_sh * 100) if tr_sh is not None and out_sh and out_sh > 0 else None
    
    avg_sh_raw = to_float(get_field(latest_fin, "AvgSh", "AverageNumberOfShares"))
    avg_sh = adjust_share_count(avg_sh_raw, adj_factor)

    deps_raw = to_float(get_field(latest_fin, "DEPS", "DilutedEarningsPerShare"))
    dilution_rate = None
    if deps_raw is not None and eps_raw is not None and eps_raw > 0:
        dilution_rate = (1 - (deps_raw / eps_raw)) * 100

    cfo = to_float(get_field(latest_fin, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
    cfi = to_float(get_field(latest_fin, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
    cff = to_float(get_field(latest_fin, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
    cash_eq = to_float(get_field(latest_fin, "CashEq", "CashAndCashEquivalents"))
    prev_cash_eq = to_float(get_field(prev_fin, "CashEq", "CashAndCashEquivalents"))
    cash_change = (cash_eq - prev_cash_eq) if cash_eq is not None and prev_cash_eq is not None else None
    
    fcf = None
    if cfo is not None or cfi is not None:
        fcf = (cfo or 0) + (cfi or 0)

    fy_prev = fy_fins[-2] if len(fy_fins) >= 2 else {}
    np_prev = to_float(get_field(fy_prev, "NP", "ProfitAttributableToOwnersOfParent"))
    eps_prev_raw = to_float(get_field(fy_prev, "EPS", "EarningsPerShare"))
    avg_sh_prev_raw = to_float(get_field(fy_prev, "AvgSh", "AverageNumberOfShares"))
    
    fy_latest_sales = to_float(get_field(fy_latest, "Sales", "NetSales"))
    fy_latest_op = to_float(get_field(fy_latest, "OP", "OperatingProfit"))
    fy_latest_odp = to_float(get_field(fy_latest, "OdP", "OrdinaryProfit"))
    fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
    fy_eps_raw = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
    fy_avg_sh_raw = to_float(get_field(fy_latest, "AvgSh", "AverageNumberOfShares"))
    
    fy_prev_cfo = to_float(get_field(fy_prev, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
    fy_cfo = to_float(get_field(fy_latest, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
    cfo_yoy = calc_yoy(fy_cfo, fy_prev_cfo)

    eps_growth_factors = None
    if fy_np and np_prev and np_prev > 0 and fy_avg_sh_raw and avg_sh_prev_raw and avg_sh_prev_raw > 0 and fy_eps_raw and eps_prev_raw and eps_prev_raw > 0:
        eps_yoy_val = ((fy_eps_raw / eps_prev_raw) - 1) * 100
        np_yoy_val = ((fy_np / np_prev) - 1) * 100
        share_yoy_val = ((fy_avg_sh_raw / avg_sh_prev_raw) - 1) * 100
        share_reduction_contribution = eps_yoy_val - np_yoy_val
        eps_growth_factors = {"eps_yoy": eps_yoy_val, "np_yoy": np_yoy_val, "share_yoy": share_yoy_val, "share_effect": share_reduction_contribution}

    def calc_dupont(fin_data):
        if not fin_data: return None
        d_s = to_float(get_field(fin_data, "Sales", "NetSales"))
        d_np = to_float(get_field(fin_data, "NP", "ProfitAttributableToOwnersOfParent"))
        d_ta = to_float(get_field(fin_data, "TA", "TotalAssets"))
        d_eq = to_float(get_field(fin_data, "Eq", "ShEq", "Equity", "NetAssets"))
        if d_s and d_np and d_ta and d_eq and d_eq > 0 and d_ta > 0:
            return {"npm": (d_np / d_s) * 100, "at": d_s / d_ta, "fl": d_ta / d_eq, "roe": (d_np / d_eq) * 100}
        return None

    dupont_current = calc_dupont(fy_latest)
    dupont_prev = calc_dupont(fy_prev)
    
    prev_op = to_float(get_field(prev_fin, "OP", "OperatingProfit"))
    prev_sales = to_float(get_field(prev_fin, "Sales", "NetSales"))
    
    prev_eps_raw_for_yoy = to_float(get_field(prev_fin, "EPS", "EarningsPerShare"))
    prev_target_date = prev_fin.get("DiscDate", prev_fin.get("CurPerEn", ""))[:10]
    prev_eps_adj = adjust_per_share_value(prev_eps_raw_for_yoy, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
    op_margin = calc_margin(op, sales)
    prev_op_margin = calc_margin(prev_op, prev_sales)
    op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

    f_eps_adj = adjust_per_share_value(f_eps_raw, adj_factor)

    payout_ratio = to_float(get_field(latest_fin, "PayoutRatioAnn"))
    if payout_ratio is None:
        if dps_raw and f_eps_raw and f_eps_raw > 0: payout_ratio = (dps_raw / f_eps_raw) * 100
        elif dps_raw and fy_latest:
            fy_eps = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
            if fy_eps and fy_eps > 0: payout_ratio = (dps_raw / fy_eps) * 100

    per = to_float(get_field(valuation, "FwdPER", "PER"))
    pbr = to_float(get_field(valuation, "PBR"))
    mktcap = to_float(get_field(valuation, "MktCap"))

    quotes_desc = sorted([q for q in daily_quotes_asc if to_float(get_field(q, "Close", "C")) is not None], key=lambda x: x.get("Date", ""), reverse=True)
    latest_c = None
    if len(quotes_desc) > 0:
        ldate = quotes_desc[0].get("Date", "")[:10]
        ladj = get_adjustment_factor_for_date(ldate, adj_map)
        lraw = to_float(get_field(quotes_desc[0], "Close", "C"))
        if lraw: latest_c = adjust_per_share_value(lraw, ladj)

    div_yield = to_float(get_field(valuation, "DividendYield"))
    if div_yield is not None and div_yield < 1.0: 
        div_yield *= 100
    if div_yield is None and latest_c is not None and latest_c > 0:
        expected_div = adjust_per_share_value(f_div_raw, adj_factor) if f_div_raw is not None else dps_adj
        if expected_div:
            div_yield = (expected_div / latest_c) * 100
    
    cfo_to_np = None
    if fy_cfo is not None and fy_np and fy_np > 0: cfo_to_np = (fy_cfo / fy_np) * 100

    roe = None
    if f_np and equity and equity > 0: roe = (f_np / equity) * 100
    elif fy_np and equity and equity > 0: roe = (fy_np / equity) * 100
    else:
        api_roe = to_float(get_field(valuation, "ROE"))
        if api_roe is not None: roe = api_roe * 100

    op_to_equity = None
    if f_op and equity and equity > 0:
        op_to_equity = (f_op / equity) * 100
    elif fy_latest_op and equity and equity > 0:
        op_to_equity = (fy_latest_op / equity) * 100

    eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
    peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

    momentum = {
        "ret_25d": None, "ret_75d": None, "ret_200d": None,
        "ma25_diff": None, "ma75_diff": None,
        "avg_val_25d": None, "vol_spike": None,
        "dist_high": None, "dist_low": None,
        "short_interest_change": None
    }
    if latest_c:
        def get_past_price(days_ago):
            if len(quotes_desc) > days_ago:
                q = quotes_desc[days_ago]
                d = q.get("Date", "")[:10]
                rc = to_float(get_field(q, "Close", "C"))
                if rc: return adjust_per_share_value(rc, get_adjustment_factor_for_date(d, adj_map))
            return None

        p25 = get_past_price(25)
        p75 = get_past_price(75)
        p200 = get_past_price(200)
        
        momentum["ret_25d"] = calc_yoy(latest_c, p25)
        momentum["ret_75d"] = calc_yoy(latest_c, p75)
        momentum["ret_200d"] = calc_yoy(latest_c, p200)
        
        if len(quotes_desc) >= 25:
            recent_25 = quotes_desc[:25]
            prices_25 = [adjust_per_share_value(to_float(get_field(q, "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_25]
            volumes_25 = [adjust_share_count(to_float(get_field(q, "Volume", "V")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_25]
            
            prices_25 = [p for p in prices_25 if p is not None]
            volumes_25 = [v for v in volumes_25 if v is not None]
            
            if len(prices_25) > 0:
                ma25 = sum(prices_25) / len(prices_25)
                momentum["ma25_diff"] = ((latest_c / ma25) - 1) * 100
            
            if len(prices_25) > 0 and len(volumes_25) > 0:
                vals_25 = [p * v for p, v in zip(prices_25, volumes_25)]
                momentum["avg_val_25d"] = sum(vals_25) / len(vals_25)
                
                latest_vo = adjust_share_count(to_float(get_field(quotes_desc[0], "Volume", "V")), get_adjustment_factor_for_date(quotes_desc[0].get("Date", "")[:10], adj_map))
                avg_vo_25 = sum(volumes_25) / len(volumes_25)
                if latest_vo and avg_vo_25 > 0:
                    momentum["vol_spike"] = latest_vo / avg_vo_25

        if len(quotes_desc) >= 75:
            recent_75 = quotes_desc[:75]
            prices_75 = [adjust_per_share_value(to_float(get_field(q, "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_75]
            prices_75 = [p for p in prices_75 if p is not None]
            if len(prices_75) > 0:
                ma75 = sum(prices_75) / len(prices_75)
                momentum["ma75_diff"] = ((latest_c / ma75) - 1) * 100

        if len(quotes_desc) > 0:
            recent_250 = quotes_desc[:250]
            highs = [adjust_per_share_value(to_float(get_field(q, "High", "H", "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_250]
            lows = [adjust_per_share_value(to_float(get_field(q, "Low", "L", "Close", "C")), get_adjustment_factor_for_date(q.get("Date", "")[:10], adj_map)) for q in recent_250]
            highs = [h for h in highs if h is not None]
            lows = [l for l in lows if l is not None]
            
            if highs:
                highest = max(highs)
                if highest > 0: momentum["dist_high"] = ((latest_c / highest) - 1) * 100
            if lows:
                lowest = min(lows)
                if lowest > 0: momentum["dist_low"] = ((latest_c / lowest) - 1) * 100

    margin_interest = profile.get("margin_interest", [])
    if not isinstance(margin_interest, list): margin_interest = []
    margin_history = sorted([m for m in margin_interest if isinstance(m, dict) and m.get("Date")], key=lambda x: x.get("Date", ""))
    margin_buy_latest = None
    margin_ratio = None
    if len(margin_history) > 0:
        latest_m = margin_history[-1]
        mb = to_float(get_field(latest_m, "LongVol", "margin_buy"))
        ms = to_float(get_field(latest_m, "ShrtVol", "margin_sell"))
        margin_buy_latest = mb
        if mb is not None and ms and ms > 0: margin_ratio = mb / ms
        
        if len(margin_history) > 1:
            prev_m = margin_history[-2]
            p_ms = to_float(get_field(prev_m, "ShrtVol", "margin_sell"))
            if ms is not None and p_ms is not None:
                momentum["short_interest_change"] = ms - p_ms 

    # ====== 年次（通期）ヒストリーの生成 ======
    history = []
    for i, fy in enumerate(fy_fins):
        y_str = fy.get("CurFYEn", "")[:4]
        s = to_float(get_field(fy, "Sales", "NetSales"))
        o = to_float(get_field(fy, "OP", "OperatingProfit"))
        odp = to_float(get_field(fy, "OdP", "OrdinaryProfit"))
        eq = to_float(get_field(fy, "Eq", "Equity", "NetAssets"))
        pr = to_float(get_field(fy, "NP", "ProfitAttributableToOwnersOfParent"))
        r = (pr / eq) if pr and eq else to_float(get_field(fy, "ROE"))
        
        cfo_fy = to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
        cfi_fy = to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
        cff_fy = to_float(get_field(fy, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
        
        fc = None
        if cfo_fy is not None or cfi_fy is not None:
            fc = (cfo_fy or 0) + (cfi_fy or 0)
        
        target_date = fy.get("DiscDate", fy.get("CurFYEn", ""))[:10]
        fy_adj_f = get_adjustment_factor_for_date(target_date, adj_map)
        
        e_raw = to_float(get_field(fy, "EPS", "EarningsPerShare"))
        e_adj = adjust_per_share_value(e_raw, fy_adj_f)
        de_raw = to_float(get_field(fy, "DEPS", "DilutedEarningsPerShare"))
        de_adj = adjust_per_share_value(de_raw, fy_adj_f)
        
        out_s_raw = to_float(get_field(fy, "ShOutFY"))
        tr_s_raw = to_float(get_field(fy, "TrShFY", "TreasStock"))
        out_s_adj = adjust_share_count(out_s_raw, fy_adj_f)
        tr_s_adj = adjust_share_count(tr_s_raw, fy_adj_f)
        
        tr_ratio = (tr_s_adj / out_s_adj * 100) if tr_s_adj is not None and out_s_adj and out_s_adj > 0 else None
        
        ta_fy = to_float(get_field(fy, "TA", "TotalAssets"))
        eq_ratio_fy = to_float(get_field(fy, "EqAR", "EquityToAssetRatio"))
        if eq_ratio_fy is not None:
            eq_ratio_fy = eq_ratio_fy * 100 if eq_ratio_fy <= 1.0 else eq_ratio_fy
        elif eq and ta_fy:
            eq_ratio_fy = (eq / ta_fy) * 100
        
        roa_fy = None
        if pr and ta_fy and ta_fy > 0:
            roa_fy = (pr / ta_fy) * 100

        prev_s = to_float(get_field(fy_fins[i-1], "Sales", "NetSales")) if i > 0 else None
        prev_o = to_float(get_field(fy_fins[i-1], "OP", "OperatingProfit")) if i > 0 else None
        prev_odp = to_float(get_field(fy_fins[i-1], "OdP", "OrdinaryProfit")) if i > 0 else None
        prev_pr = to_float(get_field(fy_fins[i-1], "NP", "ProfitAttributableToOwnersOfParent")) if i > 0 else None
        
        prev_e_raw = to_float(get_field(fy_fins[i-1], "EPS", "EarningsPerShare")) if i > 0 else None
        prev_date = fy_fins[i-1].get("DiscDate", "")[:10] if i > 0 else ""
        prev_e_adj = adjust_per_share_value(prev_e_raw, get_adjustment_factor_for_date(prev_date, adj_map)) if i > 0 else None

        prev_out_s_raw = to_float(get_field(fy_fins[i-1], "ShOutFY")) if i > 0 else None
        prev_tr_s_raw = to_float(get_field(fy_fins[i-1], "TrShFY", "TreasStock")) if i > 0 else None
        prev_fy_adj_f = get_adjustment_factor_for_date(prev_date, adj_map) if prev_date else 1.0
        
        prev_out_s_adj = adjust_share_count(prev_out_s_raw, prev_fy_adj_f)
        prev_tr_s_adj = adjust_share_count(prev_tr_s_raw, prev_fy_adj_f)
        
        closest_p = get_closest_past_price(target_date, daily_quotes_asc, adj_map)
        calc_per = None
        calc_pbr = None
        if closest_p is not None:
            if e_adj and e_adj > 0:
                calc_per = closest_p / e_adj
            bps_raw_hist = to_float(get_field(fy, "BPS", "BookValuePerShare"))
            if bps_raw_hist is None and eq is not None and out_s_raw is not None and out_s_raw > 0:
                bps_raw_hist = eq / out_s_raw
            if bps_raw_hist is not None:
                bps_adj_hist = adjust_per_share_value(bps_raw_hist, fy_adj_f)
                if bps_adj_hist and bps_adj_hist > 0:
                    calc_pbr = closest_p / bps_adj_hist
        
        history.append({
            "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
            "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
            "odp_str": format_jpy(odp), "odp_raw": odp, "odp_yoy": calc_yoy(odp, prev_odp),
            "np_str": format_jpy(pr), "np_raw": pr, "np_yoy": calc_yoy(pr, prev_pr),
            "op_margin": calc_margin(o, s),
            "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj, "eps_yoy": calc_yoy(e_adj, prev_e_adj),
            "roe_raw": r * 100 if r and r < 1.0 else r,
            "roa_estimate": roa_fy,
            "equity_ratio": eq_ratio_fy,
            "cfo": cfo_fy, "cfi": cfi_fy, "cff": cff_fy,
            "fcf_raw": fc, "fcf_margin": calc_margin(fc, s),
            "out_shares": out_s_adj, "tr_shares": tr_s_adj, "tr_ratio": tr_ratio,
            "out_shares_yoy": calc_yoy(out_s_adj, prev_out_s_adj), "tr_shares_yoy": calc_yoy(tr_s_adj, prev_tr_s_adj),
            "calc_per": calc_per,
            "calc_pbr": calc_pbr
        })

    sales_cagr_3y = None
    op_cagr_3y = None
    eps_cagr_3y = None
    if len(history) >= 4:
        latest_hist = history[-1]
        past_hist = history[-4]
        sales_cagr_3y = calc_cagr(latest_hist["sales_raw"], past_hist["sales_raw"], 3)
        op_cagr_3y = calc_cagr(latest_hist["op_raw"], past_hist["op_raw"], 3)
        eps_cagr_3y = calc_cagr(latest_hist["eps_adjusted"], past_hist["eps_adjusted"], 3)

    if history and latest_fin:
        latest_actual_year_str = history[-1]["year"]
        
        if is_latest_fy:
            target_forecast_year_str = latest_fin.get("NxtFYEn", "")[:4]
        else:
            target_forecast_year_str = latest_fin.get("CurFYEn", "")[:4]
        
        if target_forecast_year_str:
            if target_forecast_year_str > latest_actual_year_str or (target_forecast_year_str == latest_actual_year_str and not is_latest_fy):
                history.append({
                    "year": f"{target_forecast_year_str}(予)", 
                    "sales_str": format_jpy(f_sales) if f_sales is not None else "-", "sales_raw": f_sales, 
                    "sales_yoy": calc_yoy(f_sales, fy_latest_sales) if is_latest_fy else calc_yoy(f_sales, history[-1]["sales_raw"]),
                    "op_str": format_jpy(f_op) if f_op is not None else "-", "op_raw": f_op, 
                    "op_yoy": calc_yoy(f_op, fy_latest_op) if is_latest_fy else calc_yoy(f_op, history[-1]["op_raw"]),
                    "odp_str": format_jpy(f_odp) if f_odp is not None else "-", "odp_raw": f_odp, 
                    "odp_yoy": calc_yoy(f_odp, fy_latest_odp) if is_latest_fy else calc_yoy(f_odp, history[-1]["odp_raw"]),
                    "np_str": format_jpy(f_np) if f_np is not None else "-", "np_raw": f_np, 
                    "np_yoy": calc_yoy(f_np, fy_np) if is_latest_fy else calc_yoy(f_np, history[-1]["np_raw"]),
                    "op_margin": calc_margin(f_op, f_sales),
                    "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "deps_adjusted": None, 
                    "eps_yoy": calc_yoy(f_eps_adj, history[-1]["eps_adjusted"] if history else None),
                    "roe_raw": None, "roa_estimate": None, "equity_ratio": None,
                    "cfo": None, "cfi": None, "cff": None, "fcf_raw": None, "fcf_margin": None,
                    "out_shares": None, "tr_shares": None, "tr_ratio": None,
                    "out_shares_yoy": None, "tr_shares_yoy": None,
                    "calc_per": per, "calc_pbr": pbr
                })

    # ====== 四半期（Quarterly）ヒストリーの生成 ======
    
    # 予想修正などの実績値がないデータを除外した actual_fins_sorted を元に処理する
    q_fins = [f for f in actual_fins_sorted if isinstance(f, dict) and f.get("CurPerType") in ["1Q", "2Q", "3Q", "4Q", "5Q", "FY"]]
    
    fy_tree = {}
    for f in q_fins:
        year = f.get("CurFYEn", "")[:4]
        q_type = f.get("CurPerType", "")
        if year and q_type:
            if year not in fy_tree: fy_tree[year] = {}
            fy_tree[year][q_type] = f

    single_q_data = {}
    q_types_ordered = ["1Q", "2Q", "3Q", "4Q", "5Q", "FY"]
    
    for year in sorted(fy_tree.keys()):
        available_qs = [qt for qt in q_types_ordered if qt in fy_tree[year]]
        
        for idx, qt in enumerate(available_qs):
            q_data = fy_tree[year][qt]
            
            c_sales = to_float(get_field(q_data, "Sales", "NetSales"))
            c_op = to_float(get_field(q_data, "OP", "OperatingProfit"))
            c_odp = to_float(get_field(q_data, "OdP", "OrdinaryProfit"))
            c_np = to_float(get_field(q_data, "NP", "ProfitAttributableToOwnersOfParent"))
            
            s_sales, s_op, s_odp, s_np = c_sales, c_op, c_odp, c_np
            
            if idx > 0:
                prev_qt = available_qs[idx - 1]
                p_data = fy_tree[year][prev_qt]
                
                p_c_sales = to_float(get_field(p_data, "Sales", "NetSales"))
                p_c_op = to_float(get_field(p_data, "OP", "OperatingProfit"))
                p_c_odp = to_float(get_field(p_data, "OdP", "OrdinaryProfit"))
                p_c_np = to_float(get_field(p_data, "NP", "ProfitAttributableToOwnersOfParent"))
                
                if c_sales is not None and p_c_sales is not None: s_sales = c_sales - p_c_sales
                if c_op is not None and p_c_op is not None: s_op = c_op - p_c_op
                if c_odp is not None and p_c_odp is not None: s_odp = c_odp - p_c_odp
                if c_np is not None and p_c_np is not None: s_np = c_np - p_c_np
                
            order_num = get_q_order(qt)
            sort_key = f"{year}-{order_num}"
            
            single_q_data[sort_key] = {
                "year_str": year, 
                "q_type": qt,
                "sales": s_sales, "op": s_op, "odp": s_odp, "np": s_np, 
                "raw": q_data
            }

    sorted_keys_full = sorted(single_q_data.keys())
    quarterly_history = []
    earnings_events = [] 
    
    for idx, k in enumerate(sorted_keys_full):
        curr = single_q_data[k]
        year_str = curr["year_str"]
        q_type = curr["q_type"]
        q_raw = curr["raw"]
        
        prev_year_str = str(int(year_str) - 1)
        prev_k = f"{prev_year_str}-{get_q_order(q_type)}"
        prev_q = single_q_data.get(prev_k, {})
        
        s_yoy = calc_yoy(curr["sales"], prev_q.get("sales"))
        o_yoy = calc_yoy(curr["op"], prev_q.get("op"))
        odp_yoy = calc_yoy(curr["odp"], prev_q.get("odp"))
        np_yoy = calc_yoy(curr["np"], prev_q.get("np"))
        
        prev_q_raw_qoq = single_q_data[sorted_keys_full[idx - 1]]["raw"] if idx > 0 else {}
        
        target_date = q_raw.get("DiscDate", q_raw.get("CurPerEn", ""))[:10]
        q_adj_f = get_adjustment_factor_for_date(target_date, adj_map)
        
        e_raw = to_float(get_field(q_raw, "EPS", "EarningsPerShare"))
        de_raw = to_float(get_field(q_raw, "DEPS", "DilutedEarningsPerShare"))
        e_adj = adjust_per_share_value(e_raw, q_adj_f)
        de_adj = adjust_per_share_value(de_raw, q_adj_f)
        
        out_s_raw = to_float(get_field(q_raw, "ShOutFY"))
        tr_s_raw = to_float(get_field(q_raw, "TrShFY", "TreasStock"))
        out_s_adj = adjust_share_count(out_s_raw, q_adj_f)
        tr_s_adj = adjust_share_count(tr_s_raw, q_adj_f)
        
        prev_target_date = prev_q_raw_qoq.get("DiscDate", "")[:10] if prev_q_raw_qoq else ""
        prev_q_adj_f = get_adjustment_factor_for_date(prev_target_date, adj_map) if prev_target_date else 1.0
        
        prev_e_raw = to_float(get_field(prev_q_raw_qoq, "EPS", "EarningsPerShare"))
        prev_e_adj = adjust_per_share_value(prev_e_raw, prev_q_adj_f)

        prev_out_s_raw = to_float(get_field(prev_q_raw_qoq, "ShOutFY"))
        prev_tr_s_raw = to_float(get_field(prev_q_raw_qoq, "TrShFY", "TreasStock"))
        prev_out_s_adj = adjust_share_count(prev_out_s_raw, prev_q_adj_f)
        prev_tr_s_adj = adjust_share_count(prev_tr_s_raw, prev_q_adj_f)

        tr_ratio = (tr_s_adj / out_s_adj * 100) if tr_s_adj is not None and out_s_adj and out_s_adj > 0 else None
        
        display_q = "通期" if q_type == "FY" else q_type
        label = f"{year_str[-2:]}年 {display_q}" 
        
        disc_date = q_raw.get("DiscDate", "")[:10]
        if disc_date:
            earnings_events.append({
                "date": disc_date, "title": label, "sales_str": format_jpy(curr["sales"]), "sales_yoy": s_yoy,
                "op_str": format_jpy(curr["op"]), "op_yoy": o_yoy
            })
            
        cfo_q = to_float(get_field(q_raw, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
        cfi_q = to_float(get_field(q_raw, "CFI", "NetCashProvidedByUsedInInvestmentActivities"))
        cff_q = to_float(get_field(q_raw, "CFF", "NetCashProvidedByUsedInFinancingActivities"))
        
        fcf_q = (cfo_q or 0) + (cfi_q or 0) if (cfo_q is not None or cfi_q is not None) else None
        
        eq_q = to_float(get_field(q_raw, "Eq", "Equity", "NetAssets"))
        ta_q = to_float(get_field(q_raw, "TA", "TotalAssets"))
        eq_ratio_q = to_float(get_field(q_raw, "EqAR", "EquityToAssetRatio"))
        if eq_ratio_q is not None:
            eq_ratio_q = eq_ratio_q * 100 if eq_ratio_q <= 1.0 else eq_ratio_q
        elif eq_q and ta_q:
            eq_ratio_q = (eq_q / ta_q) * 100
        
        annualization_factor = 4.0
        if q_type == "1Q": annualization_factor = 4.0
        elif q_type == "2Q": annualization_factor = 2.0
        elif q_type == "3Q": annualization_factor = 4.0 / 3.0
        
        roa_q = None
        if curr["np"] and ta_q and ta_q > 0:
            roa_q = ((curr["np"] * annualization_factor) / ta_q) * 100
            
        roe_q = None
        if curr["np"] and eq_q and eq_q > 0:
            roe_q = ((curr["np"] * annualization_factor) / eq_q) * 100
            
        closest_p = get_closest_past_price(target_date, daily_quotes_asc, adj_map)
        calc_per = None
        calc_pbr = None
        if closest_p is not None:
            if e_adj and e_adj > 0:
                calc_per = closest_p / (e_adj * annualization_factor)
            
            bps_raw_q = to_float(get_field(q_raw, "BPS", "BookValuePerShare"))
            if bps_raw_q is None and eq_q is not None and out_s_raw is not None and out_s_raw > 0:
                bps_raw_q = eq_q / out_s_raw
            
            if bps_raw_q is not None:
                bps_adj_q = adjust_per_share_value(bps_raw_q, q_adj_f)
                if bps_adj_q and bps_adj_q > 0:
                    calc_pbr = closest_p / bps_adj_q
        
        quarterly_history.append({
            "year": label, "sales_str": format_jpy(curr["sales"]) if curr["sales"] is not None else "-", "sales_raw": curr["sales"], "sales_yoy": s_yoy,
            "op_str": format_jpy(curr["op"]) if curr["op"] is not None else "-", "op_raw": curr["op"], "op_yoy": o_yoy,
            "odp_str": format_jpy(curr["odp"]) if curr["odp"] is not None else "-", "odp_raw": curr["odp"], "odp_yoy": odp_yoy,
            "np_str": format_jpy(curr["np"]) if curr["np"] is not None else "-", "np_raw": curr["np"], "np_yoy": np_yoy,
            "op_margin": calc_margin(curr["op"], curr["sales"]),
            "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj, "eps_yoy": calc_yoy(e_adj, prev_e_adj),
            "out_shares": out_s_adj, "tr_shares": tr_s_adj, "tr_ratio": tr_ratio,
            "out_shares_yoy": calc_yoy(out_s_adj, prev_out_s_adj), "tr_shares_yoy": calc_yoy(tr_s_adj, prev_tr_s_adj),
            "roe_raw": roe_q,
            "roa_estimate": roa_q,
            "equity_ratio": eq_ratio_q,
            "cfo": cfo_q, "cfi": cfi_q, "cff": cff_q,
            "fcf_raw": fcf_q, "fcf_margin": calc_margin(fcf_q, curr["sales"]),
            "calc_per": calc_per,
            "calc_pbr": calc_pbr
        })

    op_margins_3y = []
    for fy in fy_fins[-4:-1]:
        s = to_float(get_field(fy, "Sales", "NetSales"))
        o = to_float(get_field(fy, "OP", "OperatingProfit"))
        if s and o and s > 0: op_margins_3y.append((o / s) * 100)
    avg_op_margin_3y = sum(op_margins_3y) / len(op_margins_3y) if op_margins_3y else None

    eps_yoy_3y = []
    for i in range(len(fy_fins)-4, len(fy_fins)-1):
        if i < 1: continue
        c_eps = to_float(get_field(fy_fins[i], "EPS", "EarningsPerShare"))
        p_eps = to_float(get_field(fy_fins[i-1], "EPS", "EarningsPerShare"))
        if c_eps is not None and p_eps is not None and p_eps != 0:
            eps_yoy_3y.append(((c_eps - p_eps) / abs(p_eps)) * 100)
    avg_eps_yoy_3y = sum(eps_yoy_3y) / len(eps_yoy_3y) if eps_yoy_3y else None

    major_history = profile.get("major_shareholders", [])
    if not isinstance(major_history, list): major_history = [major_history] if major_history else []
    def extract_shareholders(data_dict):
        if not isinstance(data_dict, dict): return []
        return data_dict.get("Hldrs") or data_dict.get("MajorShareholders") or data_dict.get("Shareholders") or []
    curr_majors = extract_shareholders(major_history[-1]) if len(major_history) > 0 else []
    prev_majors = extract_shareholders(major_history[-2]) if len(major_history) > 1 else []
    
    prev_map = {}
    for s in prev_majors:
        name = s.get("HldrName") or s.get("Name")
        ratio = to_float(s.get("ShsRatio") or s.get("HoldingRatio"))
        if name and ratio is not None: prev_map[name] = ratio

    processed_majors = []
    for idx, s in enumerate(curr_majors):
        name = s.get("HldrName") or s.get("Name") or "不明"
        ratio = to_float(s.get("ShsRatio") or s.get("HoldingRatio"))
        diff = None
        if ratio is not None:
            if ratio <= 1.0: ratio *= 100
            if name in prev_map:
                p_ratio = prev_map[name]
                if p_ratio <= 1.0: p_ratio *= 100
                diff = ratio - p_ratio
        processed_majors.append({"rank": s.get("Rank") or (idx + 1), "name": name, "ratio": ratio, "diff": diff})

    val_dict = {v.get("Date"): v for v in valuation.get("valuation_history", []) if isinstance(v, dict) and "Date" in v}
    topix_dict = {t.get("Date", "")[:10]: to_float(t.get("C", t.get("Close"))) for t in profile.get("topix_daily", []) if isinstance(t, dict) and "Date" in t}
    sector_dict = {s.get("Date", "")[:10]: to_float(s.get("C", s.get("Close"))) for s in profile.get("sector_daily", []) if isinstance(s, dict) and "Date" in s}

    price_margin_history = []
    last_topix = None
    last_sector = None

    for q in daily_quotes_asc:
        date_str = q.get("Date", "")[:10]
        if not date_str: continue
        
        adj_f = get_adjustment_factor_for_date(date_str, adj_map)

        adj_c = to_float(get_field(q, "AdjC", "AdjClose", "adj_c", "adj_close"))
        if adj_c is None:
            raw_c = to_float(get_field(q, "Close", "C"))
            if raw_c is None: continue
            adj_c = adjust_per_share_value(raw_c, adj_f)

        adj_o = to_float(get_field(q, "AdjO", "AdjOpen"))
        if adj_o is None:
            raw_o = to_float(get_field(q, "Open", "O"))
            adj_o = adjust_per_share_value(raw_o, adj_f) if raw_o is not None else adj_c
            
        adj_h = to_float(get_field(q, "AdjH", "AdjHigh"))
        if adj_h is None:
            raw_h = to_float(get_field(q, "High", "H"))
            adj_h = adjust_per_share_value(raw_h, adj_f) if raw_h is not None else adj_c
            
        adj_l = to_float(get_field(q, "AdjL", "AdjLow"))
        if adj_l is None:
            raw_l = to_float(get_field(q, "Low", "L"))
            adj_l = adjust_per_share_value(raw_l, adj_f) if raw_l is not None else adj_c
            
        adj_vo = to_float(get_field(q, "AdjVo", "AdjVolume"))
        if adj_vo is None:
            raw_vo = to_float(get_field(q, "Volume", "V"))
            adj_vo = adjust_share_count(raw_vo, adj_f) if raw_vo is not None else None
        
        v = val_dict.get(date_str, {}) 
        curr_topix = topix_dict.get(date_str)
        if curr_topix is not None: last_topix = curr_topix
            
        curr_sector = sector_dict.get(date_str)
        if curr_sector is not None: last_sector = curr_sector

        price_margin_history.append({
            "date": date_str, "open": adj_o, "high": adj_h, "low": adj_l, "close": adj_c, "volume": adj_vo,
            "per": to_float(get_field(v, "FwdPER", "PER")),
            "pbr": to_float(get_field(v, "PBR")),
            "market_cap": to_float(get_field(v, "MktCap")),
            "topix": last_topix,
            "sector": last_sector
        })

    stock_perf_1y = None
    topix_perf_1y = None
    sector_perf_1y = None
    if len(price_margin_history) > 250:
        current_close = price_margin_history[-1].get("close")
        close_1y_ago = price_margin_history[-250].get("close")
        if current_close and close_1y_ago:
            stock_perf_1y = (current_close - close_1y_ago) / close_1y_ago * 100
            
        current_topix = price_margin_history[-1].get("topix")
        topix_1y_ago = price_margin_history[-250].get("topix")
        if current_topix and topix_1y_ago:
            topix_perf_1y = (current_topix - topix_1y_ago) / topix_1y_ago * 100

        current_sector = price_margin_history[-1].get("sector")
        sector_1y_ago = price_margin_history[-250].get("sector")
        if current_sector and sector_1y_ago:
            sector_perf_1y = (current_sector - sector_1y_ago) / sector_1y_ago * 100

    return {
        "basic": { 
            "code": normalize_code(profile.get("code")), 
            "company_name": info.get("CompanyName", info.get("CoName", "-")), 
            "industry": info.get("Sector33CodeName") or info.get("S33Nm") or info.get("Sector17CodeName") or info.get("S17Nm") or "-",
            "market": info.get("MarketCodeName", info.get("MktNm", "-")) 
        },
        "period": { "current_type": cur_type, "disclosure_date": latest_fin.get("DiscDate", "") },
        "actual": { 
            "sales": sales, "op": op, "odp": odp, "net_income": np_latest, "eps_raw": eps_raw, "eps_adjusted": eps_adj, 
            "bps": bps_adj, "dps": dps_adj,
            "cfo": cfo, "cfi": cfi, "cff": cff, "fcf": fcf, "fcf_margin": calc_margin(fcf, sales),
            "cash_eq": cash_eq, "cash_change": cash_change,
            "out_sh": out_sh, "tr_sh": tr_sh, "avg_sh": avg_sh, "deps_raw": deps_raw 
        },
        "forecast": { "sales": f_sales, "op": f_op, "odp": f_odp, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
        "growth": { 
            "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
            "eps_yoy": eps_yoy_adjusted, "sales_cagr_3y": sales_cagr_3y, "op_cagr_3y": op_cagr_3y, "eps_cagr_3y": eps_cagr_3y,
            "progress_op": progress_op, "avg_eps_yoy_3y": avg_eps_yoy_3y,
            "np_yoy": eps_growth_factors.get("np_yoy") if eps_growth_factors else None
        },
        "profitability": { 
            "op_margin": op_margin, "op_margin_change": op_margin_change, "avg_op_margin_3y": avg_op_margin_3y,
            "roe": roe, "op_to_equity": op_to_equity, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
            "equity_ratio": equity_ratio, "payout_ratio": payout_ratio,
            "cfo_to_np": cfo_to_np, "treasury_ratio": treasury_ratio,
            "dilution_rate": dilution_rate, "eps_growth_factors": eps_growth_factors, 
            "dupont": {"current": dupont_current, "prev": dupont_prev}
        },
        "quality": {
            "cfo_yoy": cfo_yoy,
            "working_capital_change": None,
            "capex": None,
            "depreciation": None
        },
        "momentum": momentum,
        "health": {
            "roic": None,
            "net_cash": None,
            "debt_ebitda": None,
            "icr": None
        },
        "valuation": { 
            "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
            "dividend_yield": div_yield,
            **get_valuation_statistics(profile.get("valuation_history", [])) 
        },
        "market_perf": { 
            "stock_1y": stock_perf_1y, "topix_1y": topix_perf_1y, "sector_1y": sector_perf_1y,
            "margin_buy": margin_buy_latest, "margin_ratio": margin_ratio
        },
        "history": history,
        "quarterly_history": quarterly_history,
        "price_margin_history": price_margin_history,
        "major_shareholders": processed_majors,
        "large_volume": profile.get("large_volume", []),
        "cross_shareholdings": profile.get("cross_shareholdings", {}),
        "events": { "revisions": revisions, "other": other_events, "earnings": earnings_events },
        "guidance_history": guidance_history
    }