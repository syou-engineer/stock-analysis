# import math
# from statistics import median

# def to_float(value, default=None):
#     if value is None or value == "": return default
#     try:
#         if isinstance(value, str): value = value.replace(",", "").strip()
#         return float(value)
#     except (TypeError, ValueError): return default

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
#     if not isinstance(obj, dict): return None
#     for k in keys:
#         val = obj.get(k)
#         if val is not None and val != "": return val
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
#     quotes_asc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""))
#     if not quotes_asc: return {}
#     factors_by_date = {}
#     for q in quotes_asc:
#         f = to_float(get_field(q, "AdjFactor", "AdjustmentFactor", "adj_factor"), 1.0)
#         if f > 0 and f != 1.0: factors_by_date[q.get("Date")] = f
#     adjustment_map = {}
#     for q in quotes_asc:
#         date = q.get("Date")
#         cum_factor = 1.0
#         for factor_date, f in factors_by_date.items():
#             if factor_date > date: cum_factor *= f
#         adjustment_map[date] = cum_factor
#     return adjustment_map

# def get_adjustment_factor_for_date(target_date, adjustment_map):
#     if not target_date or not adjustment_map: return 1.0
#     if target_date in adjustment_map: return adjustment_map[target_date]
#     dates_asc = sorted(adjustment_map.keys())
#     for d in dates_asc:
#         if d >= target_date: return adjustment_map[d]
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
#                 "initial_op": None, "final_op": None, "latest_fop": None, 
#                 "sales_up": [], "sales_down": [], "op_up": [], "op_down": []
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
#     for fy_en in sorted(fy_tracking.keys())[-10:]:
#         track = fy_tracking[fy_en]
#         s_achieve = (track["final_sales"] / track["initial_sales"] * 100) if track["final_sales"] and track["initial_sales"] else None
#         o_achieve = (track["final_op"] / track["initial_op"] * 100) if track["final_op"] and track["initial_op"] else None
#         guidance_history.append({
#             "fy": track["fy"], "initial_sales": track["initial_sales"], "final_sales": track["final_sales"],
#             "initial_op": track["initial_op"], "final_op": track["final_op"],
#             "sales_achieve": s_achieve, "op_achieve": o_achieve, 
#             "sales_up": track["sales_up"], "sales_down": track["sales_down"], 
#             "op_up": track["op_up"], "op_down": track["op_down"]
#         })

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
#     prev_fin = next((f for f in reversed(fins_sorted[:-1]) if f.get("CurPerType") == cur_type), {})

#     sales = to_float(get_field(latest_fin, "Sales", "NetSales"))
#     op = to_float(get_field(latest_fin, "OP", "OperatingProfit"))
#     np_latest = to_float(get_field(latest_fin, "NP", "ProfitAttributableToOwnersOfParent", "NetIncome"))
    
#     f_op = to_float(get_field(latest_fin, "FOP", "ForecastOperatingProfit"))
#     progress_op = None
#     if cur_type in ["1Q", "2Q", "3Q"] and op is not None and f_op and f_op > 0:
#         progress_op = (op / f_op) * 100

#     latest_target_date = latest_fin.get("CurPerEn", latest_fin.get("CurFYEn", ""))[:10]
#     adj_factor = get_adjustment_factor_for_date(latest_target_date, adj_map)

#     eps_raw = to_float(get_field(latest_fin, "EPS", "EarningsPerShare"))
#     eps_adj = adjust_per_share_value(eps_raw, adj_factor)
#     bps_raw = to_float(get_field(latest_fin, "BPS", "BookValuePerShare"))
#     bps_adj = adjust_per_share_value(bps_raw, adj_factor)
#     dps_raw = to_float(get_field(latest_fin, "DivAnn", "ResultDividendPerShareAnnual", "ResultDPS"))
#     dps_adj = adjust_per_share_value(dps_raw, adj_factor)
    
#     ta = to_float(get_field(latest_fin, "TA", "TotalAssets"))
#     equity = to_float(get_field(latest_fin, "Eq", "ShEq", "Equity", "NetAssets"))
    
#     equity_ratio = to_float(get_field(latest_fin, "EqAR", "EquityToAssetRatio"))
#     if equity_ratio is not None:
#         equity_ratio = equity_ratio * 100 if equity_ratio <= 1.0 else equity_ratio
#     elif equity and ta:
#         equity_ratio = (equity / ta) * 100

#     tr_sh = to_float(get_field(latest_fin, "TrShFY", "TreasuryStock"))
#     out_sh = to_float(get_field(latest_fin, "ShOutFY", "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
#     treasury_ratio = (tr_sh / out_sh * 100) if tr_sh is not None and out_sh and out_sh > 0 else None
#     avg_sh = to_float(get_field(latest_fin, "AvgSh", "AverageNumberOfShares"))

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
#     fcf = (cfo + cfi) if cfo is not None and cfi is not None else None

#     fy_prev = fy_fins[-2] if len(fy_fins) >= 2 else {}
#     np_prev = to_float(get_field(fy_prev, "NP", "ProfitAttributableToOwnersOfParent"))
#     eps_prev_raw = to_float(get_field(fy_prev, "EPS", "EarningsPerShare"))
#     avg_sh_prev = to_float(get_field(fy_prev, "AvgSh", "AverageNumberOfShares"))
    
#     eps_growth_factors = None
#     fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
#     fy_eps_raw = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
#     fy_avg_sh = to_float(get_field(fy_latest, "AvgSh", "AverageNumberOfShares"))

#     if fy_np and np_prev and np_prev > 0 and fy_avg_sh and avg_sh_prev and avg_sh_prev > 0 and fy_eps_raw and eps_prev_raw and eps_prev_raw > 0:
#         eps_yoy = ((fy_eps_raw / eps_prev_raw) - 1) * 100
#         np_yoy = ((fy_np / np_prev) - 1) * 100
#         share_yoy = ((fy_avg_sh / avg_sh_prev) - 1) * 100
#         share_reduction_contribution = eps_yoy - np_yoy
#         eps_growth_factors = {"eps_yoy": eps_yoy, "np_yoy": np_yoy, "share_yoy": share_yoy, "share_effect": share_reduction_contribution}

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
#     prev_target_date = prev_fin.get("CurPerEn", prev_fin.get("CurFYEn", ""))[:10]
#     prev_eps_adj = adjust_per_share_value(prev_eps_raw_for_yoy, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
#     op_margin = (op / sales * 100) if op and sales else None
#     prev_op_margin = (prev_op / prev_sales * 100) if prev_op and prev_sales else None
#     op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

#     f_sales = to_float(get_field(latest_fin, "FSales", "ForecastNetSales"))
#     f_np = to_float(get_field(latest_fin, "FNP", "ForecastProfitAttributableToOwnersOfParent"))
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
    
#     fy_cfo = to_float(get_field(fy_latest, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#     cfo_to_np = None
#     if fy_cfo is not None and fy_np and fy_np > 0: cfo_to_np = (fy_cfo / fy_np) * 100

#     roe = None
#     if f_np and equity and equity > 0: roe = (f_np / equity) * 100
#     elif fy_np and equity and equity > 0: roe = (fy_np / equity) * 100
#     else:
#         api_roe = to_float(get_field(valuation, "ROE"))
#         if api_roe is not None: roe = api_roe * 100

#     eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
#     peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

#     # Annual Data
#     history = []
#     hist_fys = fy_fins[-10:] if len(fy_fins) >= 10 else fy_fins
#     for i, fy in enumerate(hist_fys):
#         y_str = fy.get("CurFYEn", "")[:4]
#         s = to_float(get_field(fy, "Sales", "NetSales"))
#         o = to_float(get_field(fy, "OP", "OperatingProfit"))
#         odp = to_float(get_field(fy, "OdP", "OrdinaryProfit"))
#         eq = to_float(get_field(fy, "Eq", "Equity", "NetAssets"))
#         pr = to_float(get_field(fy, "NP", "ProfitAttributableToOwnersOfParent"))
#         r = (pr / eq) if pr and eq else to_float(get_field(fy, "ROE"))
        
#         cfo_fy = to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities")) or 0
#         cfi_fy = to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities")) or 0
#         fc = (cfo_fy + cfi_fy) if cfo_fy != 0 or cfi_fy != 0 else None
        
#         target_date = fy.get("CurFYEn", "")[:10]
#         e_raw = to_float(get_field(fy, "EPS", "EarningsPerShare"))
#         e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
#         de_raw = to_float(get_field(fy, "DEPS", "DilutedEarningsPerShare"))
#         de_adj = adjust_per_share_value(de_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
#         out_s = to_float(get_field(fy, "ShOutFY"))
#         tr_s = to_float(get_field(fy, "TrShFY"))
#         tr_ratio = (tr_s / out_s * 100) if tr_s is not None and out_s and out_s > 0 else None
        
#         prev_s = to_float(get_field(hist_fys[i-1], "Sales", "NetSales")) if i > 0 else None
#         prev_o = to_float(get_field(hist_fys[i-1], "OP", "OperatingProfit")) if i > 0 else None
#         prev_odp = to_float(get_field(hist_fys[i-1], "OdP", "OrdinaryProfit")) if i > 0 else None
#         prev_pr = to_float(get_field(hist_fys[i-1], "NP", "ProfitAttributableToOwnersOfParent")) if i > 0 else None
        
#         prev_out_s = to_float(get_field(hist_fys[i-1], "ShOutFY")) if i > 0 else None
#         prev_tr_s = to_float(get_field(hist_fys[i-1], "TrShFY")) if i > 0 else None
        
#         history.append({
#             "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
#             "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
#             "odp_str": format_jpy(odp), "odp_raw": odp, "odp_yoy": calc_yoy(odp, prev_odp),
#             "np_str": format_jpy(pr), "np_raw": pr, "np_yoy": calc_yoy(pr, prev_pr),
#             "op_margin": (o / s * 100) if o and s else None,
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj,
#             "roe_raw": r * 100 if r and r < 1.0 else r,
#             "fcf_raw": fc, "fcf_margin": (fc / s * 100) if fc is not None and s else None,
#             "out_shares": out_s, "tr_shares": tr_s, "tr_ratio": tr_ratio,
#             "out_shares_yoy": calc_yoy(out_s, prev_out_s), "tr_shares_yoy": calc_yoy(tr_s, prev_tr_s)
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
#             "year": f"{next_year}(予)", "sales_str": format_jpy(f_sales), "sales_raw": f_sales, "sales_yoy": None,
#             "op_str": format_jpy(f_op), "op_raw": f_op, "op_yoy": None,
#             "odp_str": format_jpy(to_float(get_field(latest_fin, "FOdP", "ForecastOrdinaryProfit"))), "odp_raw": to_float(get_field(latest_fin, "FOdP", "ForecastOrdinaryProfit")), "odp_yoy": None,
#             "np_str": format_jpy(f_np), "np_raw": f_np, "np_yoy": None,
#             "op_margin": (f_op / f_sales * 100) if f_op and f_sales else None,
#             "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "deps_adjusted": None, "eps_yoy": None,
#             "roe_raw": None, "fcf_raw": None, "fcf_margin": None,
#             "out_shares": None, "tr_shares": None, "tr_ratio": None,
#             "out_shares_yoy": None, "tr_shares_yoy": None
#         })

#     # Quarterly Data
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
#     earnings_events = [] # ★新規: 決算イベントリスト
    
#     for k in sorted_keys_full[-40:]:
#         idx = sorted_keys_full.index(k)
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
#         target_date = q_raw.get("CurPerEn", q_raw.get("CurFYEn", ""))[:10]
        
#         e_raw = to_float(get_field(q_raw, "EPS", "EarningsPerShare"))
#         de_raw = to_float(get_field(q_raw, "DEPS", "DilutedEarningsPerShare"))
#         e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
#         de_adj = adjust_per_share_value(de_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
#         out_s = to_float(get_field(q_raw, "ShOutFY"))
#         tr_s = to_float(get_field(q_raw, "TrShFY"))
#         prev_out_s = to_float(get_field(prev_q_raw_qoq, "ShOutFY"))
#         prev_tr_s = to_float(get_field(prev_q_raw_qoq, "TrShFY"))

#         tr_ratio = (tr_s / out_s * 100) if tr_s is not None and out_s and out_s > 0 else None
#         label = f"{year_str[-2:]}年 {q_type.replace('FY', '4Q')}" 
        
#         # ★ 新規: 決算発表イベントの登録
#         disc_date = q_raw.get("DiscDate", "")[:10]
#         if disc_date:
#             earnings_events.append({
#                 "date": disc_date,
#                 "title": label,
#                 "sales_str": format_jpy(curr["sales"]),
#                 "sales_yoy": s_yoy,
#                 "op_str": format_jpy(curr["op"]),
#                 "op_yoy": o_yoy
#             })
        
#         quarterly_history.append({
#             "year": label, "sales_str": format_jpy(curr["sales"]), "sales_raw": curr["sales"], "sales_yoy": s_yoy,
#             "op_str": format_jpy(curr["op"]), "op_raw": curr["op"], "op_yoy": o_yoy,
#             "odp_str": format_jpy(curr["odp"]), "odp_raw": curr["odp"], "odp_yoy": odp_yoy,
#             "np_str": format_jpy(curr["np"]), "np_raw": curr["np"], "np_yoy": np_yoy,
#             "op_margin": (curr["op"] / curr["sales"] * 100) if curr["op"] and curr["sales"] else None,
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj,
#             "out_shares": out_s, "tr_shares": tr_s, "tr_ratio": tr_ratio,
#             "out_shares_yoy": calc_yoy(out_s, prev_out_s), "tr_shares_yoy": calc_yoy(tr_s, prev_tr_s),
#             "roe_raw": to_float(get_field(q_raw, "ROE"))
#         })

#     # === 大株主の増減比較 ===
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

#     margin_interest = profile.get("margin_interest", [])
#     if not isinstance(margin_interest, list): margin_interest = []
#     margin_dict = {m.get("Date"): m for m in margin_interest if isinstance(m, dict) and "Date" in m}
#     val_history = profile.get("valuation_history", [])
#     if not isinstance(val_history, list): val_history = []
#     val_dict = {v.get("Date"): v for v in val_history if isinstance(v, dict) and "Date" in v}

#     topix_daily = profile.get("topix_daily", [])
#     if not isinstance(topix_daily, list): topix_daily = []
#     topix_dict = {t.get("Date"): to_float(t.get("C")) for t in topix_daily if isinstance(t, dict) and "Date" in t}

#     price_margin_history = []

#     for q in daily_quotes_asc:
#         date_str = q.get("Date")
#         if not date_str: continue

#         adj_c = to_float(get_field(q, "AdjC", "AdjClose", "adj_c", "adj_close"))
#         if adj_c is None: continue
            
#         m = margin_dict.get(date_str, {})
#         v = val_dict.get(date_str, {}) 
        
#         adj_o = to_float(get_field(q, "AdjO", "AdjOpen"))
#         adj_h = to_float(get_field(q, "AdjH", "AdjHigh"))
#         adj_l = to_float(get_field(q, "AdjL", "AdjLow"))
#         adj_vo = to_float(get_field(q, "AdjVo", "AdjVolume"))
        
#         price_margin_history.append({
#             "date": date_str, "open": adj_o if adj_o is not None else adj_c,
#             "high": adj_h if adj_h is not None else adj_c, "low": adj_l if adj_l is not None else adj_c,
#             "close": adj_c, "volume": adj_vo,
#             "margin_buy": to_float(get_field(m, "LongVol", "margin_buy")),
#             "margin_sell": to_float(get_field(m, "ShrtVol", "margin_sell")),
#             "per": to_float(get_field(v, "FwdPER", "PER")),
#             "pbr": to_float(get_field(v, "PBR")),
#             "market_cap": to_float(get_field(v, "MktCap"))
#         })

#     stock_perf_1y = None
#     topix_perf_1y = None
#     if len(price_margin_history) > 250:
#         current_close = price_margin_history[-1].get("close")
#         close_1y_ago = price_margin_history[-250].get("close")
#         if current_close and close_1y_ago:
#             stock_perf_1y = (current_close - close_1y_ago) / close_1y_ago * 100

#         current_topix = price_margin_history[-1].get("topix")
#         topix_1y_ago = price_margin_history[-250].get("topix")
#         if current_topix and topix_1y_ago:
#             topix_perf_1y = (current_topix - topix_1y_ago) / topix_1y_ago * 100

#     # 過去3年間の平均営業利益率の計算
#     op_margins_3y = []
#     for fy in hist_fys[-4:-1]: # 直近(-1)を除いた過去3年
#         s = to_float(get_field(fy, "Sales", "NetSales"))
#         o = to_float(get_field(fy, "OP", "OperatingProfit"))
#         if s and o and s > 0:
#             op_margins_3y.append((o / s) * 100)
#     avg_op_margin_3y = sum(op_margins_3y) / len(op_margins_3y) if op_margins_3y else None

#     # 過去3年間の平均EPS成長率の計算
#     eps_yoy_3y = []
#     for i in range(len(hist_fys)-4, len(hist_fys)-1):
#         if i < 1: continue
#         curr_fy = hist_fys[i]
#         prev_fy = hist_fys[i-1]
        
#         c_eps = to_float(get_field(curr_fy, "EPS", "EarningsPerShare"))
#         p_eps = to_float(get_field(prev_fy, "EPS", "EarningsPerShare"))
#         if c_eps is not None and p_eps is not None and p_eps != 0:
#             eps_yoy_3y.append(((c_eps - p_eps) / abs(p_eps)) * 100)
#     avg_eps_yoy_3y = sum(eps_yoy_3y) / len(eps_yoy_3y) if eps_yoy_3y else None

#     # === [return ブロックを以下に置き換え] ===
#     return {
#         "basic": { 
#             "code": profile.get("code", "")[:4], 
#             "company_name": info.get("CompanyName", info.get("CoName", "-")), 
#             "industry": info.get("Sector33CodeName", info.get("S17Nm", "-")), 
#             "market": info.get("MarketCodeName", info.get("MktNm", "-")) 
#         },
#         "period": { "current_type": cur_type, "disclosure_date": latest_fin.get("DiscDate", "") },
#         "actual": { 
#             "sales": sales, "op": op, "net_income": np_latest, "eps_raw": eps_raw, "eps_adjusted": eps_adj, 
#             "bps": bps_adj, "dps": dps_adj,
#             "cfo": cfo, "cfi": cfi, "cff": cff, "cash_eq": cash_eq, "cash_change": cash_change,
#             "out_sh": out_sh, "tr_sh": tr_sh, "avg_sh": avg_sh, "deps_raw": deps_raw 
#         },
#         "forecast": { "sales": f_sales, "op": f_op, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
#         "growth": { 
#             "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
#             "eps_yoy": eps_yoy_adjusted, 
#             "sales_cagr_3y": sales_cagr_3y, "op_cagr_3y": op_cagr_3y, "eps_cagr_3y": eps_cagr_3y, # ★営利とEPSのCAGRを追加
#             "progress_op": progress_op,
#             "avg_eps_yoy_3y": avg_eps_yoy_3y
#         },
#         "profitability": { 
#             "op_margin": op_margin, "op_margin_change": op_margin_change, 
#             "avg_op_margin_3y": avg_op_margin_3y, # ★新規追加
#             "roe": roe, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
#             "equity_ratio": equity_ratio, "payout_ratio": payout_ratio,
#             "cfo_to_np": cfo_to_np, "treasury_ratio": treasury_ratio,
#             "dilution_rate": dilution_rate, "eps_growth_factors": eps_growth_factors, 
#             "dupont": {"current": dupont_current, "prev": dupont_prev}
#         },
#         "valuation": { 
#             "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
#             **get_valuation_statistics(profile.get("valuation_history", [])) 
#         },
#         "market_perf": { "stock_1y": stock_perf_1y, "topix_1y": topix_perf_1y },
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

# import math
# from statistics import median

# def to_float(value, default=None):
#     if value is None or value == "": return default
#     try:
#         if isinstance(value, str): value = value.replace(",", "").strip()
#         return float(value)
#     except (TypeError, ValueError): return default

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
#     if not isinstance(obj, dict): return None
#     for k in keys:
#         val = obj.get(k)
#         if val is not None and val != "": return val
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
#     quotes_asc = sorted([q for q in daily_quotes if isinstance(q, dict) and q.get("Date")], key=lambda x: x.get("Date", ""))
#     if not quotes_asc: return {}
    
#     # 株式分割・併合の係数を収集
#     factors_by_date = {}
#     for q in quotes_asc:
#         f = to_float(get_field(q, "AdjustmentFactor", "AdjFactor", "adj_factor"), 1.0)
#         if f > 0 and f != 1.0: 
#             factors_by_date[q.get("Date")[:10]] = f
            
#     adjustment_map = {}
#     # 全日付に対して、その日以降に発生した分割・併合係数の累積を計算
#     # 過去のEPSにこの係数を掛けることで、現在の株式数ベースのEPSに変換される
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
    
#     # 厳密な日付が一致しない場合、最も近い過去の日付の係数を探す
#     dates_desc = sorted(adjustment_map.keys(), reverse=True)
#     for d in dates_desc:
#         if d <= target_date: 
#             return adjustment_map[d]
#     return 1.0

# def adjust_per_share_value(raw_value, adjustment_factor):
#     v = to_float(raw_value)
#     f = to_float(adjustment_factor, 1.0)
#     if v is None: return None
#     # 過去のEPS（1株当たり利益）に対して、その後に発生した分割係数(例: 2分割なら0.5)を掛けることで
#     # 現在の株数ベースのEPSに調整される。
#     return v * f if f > 0 else v

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
#     for fy_en in sorted(fy_tracking.keys())[-10:]:
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
#     fy_3yr_ago = fy_fins[-4] if len(fy_fins) >= 4 else {}

#     latest_fin = fins_sorted[-1] if fins_sorted else {}
#     cur_type = latest_fin.get("CurPerType", "")
#     prev_fin = next((f for f in reversed(fins_sorted[:-1]) if f.get("CurPerType") == cur_type), {})

#     sales = to_float(get_field(latest_fin, "Sales", "NetSales"))
#     op = to_float(get_field(latest_fin, "OP", "OperatingProfit"))
#     np_latest = to_float(get_field(latest_fin, "NP", "ProfitAttributableToOwnersOfParent", "NetIncome"))
    
#     f_op = to_float(get_field(latest_fin, "FOP", "ForecastOperatingProfit"))
#     progress_op = None
#     if cur_type in ["1Q", "2Q", "3Q"] and op is not None and f_op and f_op > 0:
#         progress_op = (op / f_op) * 100

#     latest_target_date = latest_fin.get("CurPerEn", latest_fin.get("CurFYEn", ""))[:10]
#     adj_factor = get_adjustment_factor_for_date(latest_target_date, adj_map)

#     eps_raw = to_float(get_field(latest_fin, "EPS", "EarningsPerShare"))
#     eps_adj = adjust_per_share_value(eps_raw, adj_factor)
#     bps_raw = to_float(get_field(latest_fin, "BPS", "BookValuePerShare"))
#     bps_adj = adjust_per_share_value(bps_raw, adj_factor)
#     dps_raw = to_float(get_field(latest_fin, "DivAnn", "ResultDividendPerShareAnnual", "ResultDPS"))
#     dps_adj = adjust_per_share_value(dps_raw, adj_factor)
    
#     ta = to_float(get_field(latest_fin, "TA", "TotalAssets"))
#     equity = to_float(get_field(latest_fin, "Eq", "ShEq", "Equity", "NetAssets"))
    
#     equity_ratio = to_float(get_field(latest_fin, "EqAR", "EquityToAssetRatio"))
#     if equity_ratio is not None:
#         equity_ratio = equity_ratio * 100 if equity_ratio <= 1.0 else equity_ratio
#     elif equity and ta:
#         equity_ratio = (equity / ta) * 100

#     tr_sh = to_float(get_field(latest_fin, "TrShFY", "TreasuryStock"))
#     out_sh = to_float(get_field(latest_fin, "ShOutFY", "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
#     treasury_ratio = (tr_sh / out_sh * 100) if tr_sh is not None and out_sh and out_sh > 0 else None
#     avg_sh = to_float(get_field(latest_fin, "AvgSh", "AverageNumberOfShares"))

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
#     fcf = (cfo + cfi) if cfo is not None and cfi is not None else None

#     fy_prev = fy_fins[-2] if len(fy_fins) >= 2 else {}
#     np_prev = to_float(get_field(fy_prev, "NP", "ProfitAttributableToOwnersOfParent"))
#     eps_prev_raw = to_float(get_field(fy_prev, "EPS", "EarningsPerShare"))
#     avg_sh_prev = to_float(get_field(fy_prev, "AvgSh", "AverageNumberOfShares"))
    
#     eps_growth_factors = None
#     fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
#     fy_eps_raw = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
#     fy_avg_sh = to_float(get_field(fy_latest, "AvgSh", "AverageNumberOfShares"))

#     if fy_np and np_prev and np_prev > 0 and fy_avg_sh and avg_sh_prev and avg_sh_prev > 0 and fy_eps_raw and eps_prev_raw and eps_prev_raw > 0:
#         eps_yoy = ((fy_eps_raw / eps_prev_raw) - 1) * 100
#         np_yoy = ((fy_np / np_prev) - 1) * 100
#         share_yoy = ((fy_avg_sh / avg_sh_prev) - 1) * 100
#         share_reduction_contribution = eps_yoy - np_yoy
#         eps_growth_factors = {"eps_yoy": eps_yoy, "np_yoy": np_yoy, "share_yoy": share_yoy, "share_effect": share_reduction_contribution}

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
#     prev_target_date = prev_fin.get("CurPerEn", prev_fin.get("CurFYEn", ""))[:10]
#     prev_eps_adj = adjust_per_share_value(prev_eps_raw_for_yoy, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
#     op_margin = (op / sales * 100) if op and sales else None
#     prev_op_margin = (prev_op / prev_sales * 100) if prev_op and prev_sales else None
#     op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

#     f_sales = to_float(get_field(latest_fin, "FSales", "ForecastNetSales"))
#     f_np = to_float(get_field(latest_fin, "FNP", "ForecastProfitAttributableToOwnersOfParent"))
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
    
#     fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
#     fy_cfo = to_float(get_field(fy_latest, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
#     cfo_to_np = None
#     if fy_cfo is not None and fy_np and fy_np > 0: cfo_to_np = (fy_cfo / fy_np) * 100

#     roe = None
#     if f_np and equity and equity > 0: roe = (f_np / equity) * 100
#     elif fy_np and equity and equity > 0: roe = (fy_np / equity) * 100
#     else:
#         api_roe = to_float(get_field(valuation, "ROE"))
#         if api_roe is not None: roe = api_roe * 100

#     eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
#     peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

#     history = []
#     hist_fys = fy_fins[-10:] if len(fy_fins) >= 10 else fy_fins
#     for i, fy in enumerate(hist_fys):
#         y_str = fy.get("CurFYEn", "")[:4]
#         s = to_float(get_field(fy, "Sales", "NetSales"))
#         o = to_float(get_field(fy, "OP", "OperatingProfit"))
#         odp = to_float(get_field(fy, "OdP", "OrdinaryProfit"))
#         eq = to_float(get_field(fy, "Eq", "Equity", "NetAssets"))
#         pr = to_float(get_field(fy, "NP", "ProfitAttributableToOwnersOfParent"))
#         r = (pr / eq) if pr and eq else to_float(get_field(fy, "ROE"))
        
#         cfo_fy = to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities")) or 0
#         cfi_fy = to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities")) or 0
#         fc = (cfo_fy + cfi_fy) if cfo_fy != 0 or cfi_fy != 0 else None
        
#         target_date = fy.get("CurFYEn", "")[:10]
#         e_raw = to_float(get_field(fy, "EPS", "EarningsPerShare"))
#         e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
#         de_raw = to_float(get_field(fy, "DEPS", "DilutedEarningsPerShare"))
#         de_adj = adjust_per_share_value(de_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
#         out_s = to_float(get_field(fy, "ShOutFY"))
#         tr_s = to_float(get_field(fy, "TrShFY"))
#         tr_ratio = (tr_s / out_s * 100) if tr_s is not None and out_s and out_s > 0 else None
        
#         prev_s = to_float(get_field(hist_fys[i-1], "Sales", "NetSales")) if i > 0 else None
#         prev_o = to_float(get_field(hist_fys[i-1], "OP", "OperatingProfit")) if i > 0 else None
#         prev_odp = to_float(get_field(hist_fys[i-1], "OdP", "OrdinaryProfit")) if i > 0 else None
#         prev_pr = to_float(get_field(hist_fys[i-1], "NP", "ProfitAttributableToOwnersOfParent")) if i > 0 else None
        
#         prev_out_s = to_float(get_field(hist_fys[i-1], "ShOutFY")) if i > 0 else None
#         prev_tr_s = to_float(get_field(hist_fys[i-1], "TrShFY")) if i > 0 else None
        
#         history.append({
#             "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
#             "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
#             "odp_str": format_jpy(odp), "odp_raw": odp, "odp_yoy": calc_yoy(odp, prev_odp),
#             "np_str": format_jpy(pr), "np_raw": pr, "np_yoy": calc_yoy(pr, prev_pr),
#             "op_margin": (o / s * 100) if o and s else None,
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj,
#             "roe_raw": r * 100 if r and r < 1.0 else r,
#             "fcf_raw": fc, "fcf_margin": (fc / s * 100) if fc is not None and s else None,
#             "out_shares": out_s, "tr_shares": tr_s, "tr_ratio": tr_ratio,
#             "out_shares_yoy": calc_yoy(out_s, prev_out_s), "tr_shares_yoy": calc_yoy(tr_s, prev_tr_s)
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
#             "year": f"{next_year}(予)", "sales_str": format_jpy(f_sales), "sales_raw": f_sales, "sales_yoy": None,
#             "op_str": format_jpy(f_op), "op_raw": f_op, "op_yoy": None,
#             "odp_str": format_jpy(to_float(get_field(latest_fin, "FOdP", "ForecastOrdinaryProfit"))), "odp_raw": to_float(get_field(latest_fin, "FOdP", "ForecastOrdinaryProfit")), "odp_yoy": None,
#             "np_str": format_jpy(f_np), "np_raw": f_np, "np_yoy": None,
#             "op_margin": (f_op / f_sales * 100) if f_op and f_sales else None,
#             "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "deps_adjusted": None, "eps_yoy": None,
#             "roe_raw": None, "fcf_raw": None, "fcf_margin": None,
#             "out_shares": None, "tr_shares": None, "tr_ratio": None,
#             "out_shares_yoy": None, "tr_shares_yoy": None
#         })

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
    
#     for k in sorted_keys_full[-40:]:
#         idx = sorted_keys_full.index(k)
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
#         target_date = q_raw.get("CurPerEn", q_raw.get("CurFYEn", ""))[:10]
        
#         e_raw = to_float(get_field(q_raw, "EPS", "EarningsPerShare"))
#         de_raw = to_float(get_field(q_raw, "DEPS", "DilutedEarningsPerShare"))
#         e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
#         de_adj = adjust_per_share_value(de_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
#         out_s = to_float(get_field(q_raw, "ShOutFY"))
#         tr_s = to_float(get_field(q_raw, "TrShFY"))
#         prev_out_s = to_float(get_field(prev_q_raw_qoq, "ShOutFY"))
#         prev_tr_s = to_float(get_field(prev_q_raw_qoq, "TrShFY"))

#         tr_ratio = (tr_s / out_s * 100) if tr_s is not None and out_s and out_s > 0 else None
#         label = f"{year_str[-2:]}年 {q_type.replace('FY', '4Q')}" 
        
#         disc_date = q_raw.get("DiscDate", "")[:10]
#         if disc_date:
#             earnings_events.append({
#                 "date": disc_date, "title": label, "sales_str": format_jpy(curr["sales"]), "sales_yoy": s_yoy,
#                 "op_str": format_jpy(curr["op"]), "op_yoy": o_yoy
#             })
        
#         quarterly_history.append({
#             "year": label, "sales_str": format_jpy(curr["sales"]), "sales_raw": curr["sales"], "sales_yoy": s_yoy,
#             "op_str": format_jpy(curr["op"]), "op_raw": curr["op"], "op_yoy": o_yoy,
#             "odp_str": format_jpy(curr["odp"]), "odp_raw": curr["odp"], "odp_yoy": odp_yoy,
#             "np_str": format_jpy(curr["np"]), "np_raw": curr["np"], "np_yoy": np_yoy,
#             "op_margin": (curr["op"] / curr["sales"] * 100) if curr["op"] and curr["sales"] else None,
#             "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj,
#             "out_shares": out_s, "tr_shares": tr_s, "tr_ratio": tr_ratio,
#             "out_shares_yoy": calc_yoy(out_s, prev_out_s), "tr_shares_yoy": calc_yoy(tr_s, prev_tr_s),
#             "roe_raw": to_float(get_field(q_raw, "ROE"))
#         })

#     op_margins_3y = []
#     for fy in hist_fys[-4:-1]:
#         s = to_float(get_field(fy, "Sales", "NetSales"))
#         o = to_float(get_field(fy, "OP", "OperatingProfit"))
#         if s and o and s > 0: op_margins_3y.append((o / s) * 100)
#     avg_op_margin_3y = sum(op_margins_3y) / len(op_margins_3y) if op_margins_3y else None

#     eps_yoy_3y = []
#     for i in range(len(hist_fys)-4, len(hist_fys)-1):
#         if i < 1: continue
#         c_eps = to_float(get_field(hist_fys[i], "EPS", "EarningsPerShare"))
#         p_eps = to_float(get_field(hist_fys[i-1], "EPS", "EarningsPerShare"))
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

#     margin_interest = profile.get("margin_interest", [])
#     if not isinstance(margin_interest, list): margin_interest = []
#     margin_dict = {m.get("Date"): m for m in margin_interest if isinstance(m, dict) and "Date" in m}
#     val_history = profile.get("valuation_history", [])
#     if not isinstance(val_history, list): val_history = []
#     val_dict = {v.get("Date"): v for v in val_history if isinstance(v, dict) and "Date" in v}
    
#     topix_daily = profile.get("topix_daily", [])
#     if not isinstance(topix_daily, list): topix_daily = []
#     topix_dict = {t.get("Date", "")[:10]: to_float(t.get("C", t.get("Close"))) for t in topix_daily if isinstance(t, dict) and "Date" in t}

#     sector_daily = profile.get("sector_daily", [])
#     if not isinstance(sector_daily, list): sector_daily = []
#     sector_dict = {s.get("Date", "")[:10]: to_float(s.get("C", s.get("Close"))) for s in sector_daily if isinstance(s, dict) and "Date" in s}

#     price_margin_history = []
#     last_topix = None
#     last_sector = None
    
#     last_margin_buy = None
#     last_margin_sell = None

#     for q in daily_quotes_asc:
#         date_str = q.get("Date", "")[:10]
#         if not date_str: continue

#         adj_c = to_float(get_field(q, "AdjC", "AdjClose", "adj_c", "adj_close"))
#         if adj_c is None:
#             raw_c = to_float(get_field(q, "Close", "C"))
#             if raw_c is None: continue
#             adj_f = get_adjustment_factor_for_date(date_str, adj_map)
#             adj_c = raw_c * adj_f if adj_f > 0 else raw_c

#         adj_o = to_float(get_field(q, "AdjO", "AdjOpen"))
#         adj_h = to_float(get_field(q, "AdjH", "AdjHigh"))
#         adj_l = to_float(get_field(q, "AdjL", "AdjLow"))
#         adj_vo = to_float(get_field(q, "AdjVo", "AdjVolume"))

#         if adj_o is None: adj_o = adj_c
#         if adj_h is None: adj_h = adj_c
#         if adj_l is None: adj_l = adj_c
        
#         v = val_dict.get(date_str, {}) 
#         curr_topix = topix_dict.get(date_str)
#         if curr_topix is not None: last_topix = curr_topix
            
#         curr_sector = sector_dict.get(date_str)
#         if curr_sector is not None: last_sector = curr_sector

#         m = margin_dict.get(date_str)
#         mb_chg = None
#         ms_chg = None
#         std_buy_avg_price = None  
#         std_sell_avg_price = None 

#         if m: 
#             curr_mb = to_float(get_field(m, "LongVol", "margin_buy"))
#             curr_ms = to_float(get_field(m, "ShrtVol", "margin_sell"))
            
#             if last_margin_buy is not None and curr_mb is not None:
#                 mb_chg = curr_mb - last_margin_buy
#             if last_margin_sell is not None and curr_ms is not None:
#                 ms_chg = curr_ms - last_margin_sell
                
#             last_margin_buy = curr_mb
#             last_margin_sell = curr_ms

#             buy_vol = to_float(get_field(m, "LongStdVol"))
#             buy_val = to_float(get_field(m, "LongStdVal"))
#             if buy_vol and buy_val and buy_vol > 0:
#                 std_buy_avg_price = buy_val / buy_vol

#             sell_vol = to_float(get_field(m, "ShrtStdVol"))
#             sell_val = to_float(get_field(m, "ShrtStdVal"))
#             if sell_vol and sell_val and sell_vol > 0:
#                 std_sell_avg_price = sell_val / sell_vol

#         price_margin_history.append({
#             "date": date_str, "open": adj_o, "high": adj_h, "low": adj_l, "close": adj_c, "volume": adj_vo,
#             "margin_buy": last_margin_buy,       
#             "margin_sell": last_margin_sell,
#             "margin_buy_chg": mb_chg,            
#             "margin_sell_chg": ms_chg,
#             "std_avg_price": std_buy_avg_price,        
#             "std_buy_avg_price": std_buy_avg_price,    
#             "std_sell_avg_price": std_sell_avg_price,  
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
#             "code": profile.get("code", "")[:4], 
#             "company_name": info.get("CompanyName", info.get("CoName", "-")), 
#             "industry": info.get("Sector33CodeName") or info.get("S33Nm") or info.get("Sector17CodeName") or info.get("S17Nm") or "-",
#             "market": info.get("MarketCodeName", info.get("MktNm", "-")) 
#         },
#         "period": { "current_type": cur_type, "disclosure_date": latest_fin.get("DiscDate", "") },
#         "actual": { 
#             "sales": sales, "op": op, "net_income": np_latest, "eps_raw": eps_raw, "eps_adjusted": eps_adj, 
#             "bps": bps_adj, "dps": dps_adj,
#             "cfo": cfo, "cfi": cfi, "cff": cff, "cash_eq": cash_eq, "cash_change": cash_change,
#             "out_sh": out_sh, "tr_sh": tr_sh, "avg_sh": avg_sh, "deps_raw": deps_raw 
#         },
#         "forecast": { "sales": f_sales, "op": f_op, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
#         "growth": { 
#             "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
#             "eps_yoy": eps_yoy_adjusted, "sales_cagr_3y": sales_cagr_3y, "op_cagr_3y": op_cagr_3y, "eps_cagr_3y": eps_cagr_3y,
#             "progress_op": progress_op, "avg_eps_yoy_3y": avg_eps_yoy_3y
#         },
#         "profitability": { 
#             "op_margin": op_margin, "op_margin_change": op_margin_change, "avg_op_margin_3y": avg_op_margin_3y,
#             "roe": roe, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
#             "equity_ratio": equity_ratio, "payout_ratio": payout_ratio,
#             "cfo_to_np": cfo_to_np, "treasury_ratio": treasury_ratio,
#             "dilution_rate": dilution_rate, "eps_growth_factors": eps_growth_factors, 
#             "dupont": {"current": dupont_current, "prev": dupont_prev}
#         },
#         "valuation": { 
#             "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
#             **get_valuation_statistics(profile.get("valuation_history", [])) 
#         },
#         "market_perf": { "stock_1y": stock_perf_1y, "topix_1y": topix_perf_1y, "sector_1y": sector_perf_1y },
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
    """
    元の正しいロジック。
    対象日付と完全に一致しなくても、それより未来（>=）の最初の係数を返す。
    """
    if not target_date or not adjustment_map: return 1.0
    target_date = target_date[:10]
    if target_date in adjustment_map: return adjustment_map[target_date]
    
    dates_asc = sorted(adjustment_map.keys())
    for d in dates_asc:
        if d >= target_date: return adjustment_map[d]
    return 1.0

def adjust_per_share_value(raw_value, adjustment_factor):
    """
    元の正しいロジック。
    過去のEPS等に対して、その後に発生した分割係数を掛けることで現在の株数ベースに調整する。
    """
    v = to_float(raw_value)
    f = to_float(adjustment_factor, 1.0)
    if v is None: return None
    return v * f if f > 0 else v

def adjust_share_count(raw_shares, adjustment_factor):
    """
    株数の調整。過去の株数は現在ベースに直す場合は分割係数で割る必要がある。
    """
    v = to_float(raw_shares)
    f = to_float(adjustment_factor, 1.0)
    if v is None: return None
    return v / f if f > 0 else v


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
        
        if cur_per_type == "FY":
            fy_tracking[fy_en_date]["final_op"] = to_float(get_field(f, "OP", "OperatingProfit"))
            fy_tracking[fy_en_date]["final_sales"] = to_float(get_field(f, "Sales", "NetSales"))

    guidance_history = []
    for fy_en in sorted(fy_tracking.keys())[-10:]:
        track = fy_tracking[fy_en]
        guidance_history.append({
            "fy": track["fy"], "initial_sales": track["initial_sales"], "final_sales": track["final_sales"],
            "initial_op": track["initial_op"], "final_op": track["final_op"],
            "sales_achieve": (track["final_sales"] / track["initial_sales"] * 100) if track["final_sales"] and track["initial_sales"] else None,
            "op_achieve": (track["final_op"] / track["initial_op"] * 100) if track["final_op"] and track["initial_op"] else None,
            "sales_up": track["sales_up"], "sales_down": track["sales_down"], "op_up": track["op_up"], "op_down": track["op_down"]
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
    odp = to_float(get_field(latest_fin, "OdP", "OrdinaryProfit"))
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

    tr_sh_raw = to_float(get_field(latest_fin, "TrShFY", "TreasuryStock"))
    out_sh_raw = to_float(get_field(latest_fin, "ShOutFY", "NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock"))
    avg_sh_raw = to_float(get_field(latest_fin, "AvgSh", "AverageNumberOfShares"))
    
    tr_sh = adjust_share_count(tr_sh_raw, adj_factor)
    out_sh = adjust_share_count(out_sh_raw, adj_factor)
    avg_sh = adjust_share_count(avg_sh_raw, adj_factor)

    treasury_ratio = (tr_sh / out_sh * 100) if tr_sh is not None and out_sh and out_sh > 0 else None

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
    
    fy_np = to_float(get_field(fy_latest, "NP", "ProfitAttributableToOwnersOfParent"))
    fy_eps_raw = to_float(get_field(fy_latest, "EPS", "EarningsPerShare"))
    fy_avg_sh_raw = to_float(get_field(fy_latest, "AvgSh", "AverageNumberOfShares"))

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
    prev_target_date = prev_fin.get("CurPerEn", prev_fin.get("CurFYEn", ""))[:10]
    prev_eps_adj = adjust_per_share_value(prev_eps_raw_for_yoy, get_adjustment_factor_for_date(prev_target_date, adj_map))
    
    op_margin = calc_margin(op, sales)
    prev_op_margin = calc_margin(prev_op, prev_sales)
    op_margin_change = op_margin - prev_op_margin if op_margin is not None and prev_op_margin is not None else None

    f_sales = to_float(get_field(latest_fin, "FSales", "ForecastNetSales"))
    f_np = to_float(get_field(latest_fin, "FNP", "ForecastProfitAttributableToOwnersOfParent"))
    f_odp = to_float(get_field(latest_fin, "FOdP", "ForecastOrdinaryProfit"))
    f_eps_raw = to_float(get_field(latest_fin, "FEPS", "ForecastEarningsPerShare"))
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
    
    fy_cfo = to_float(get_field(fy_latest, "CFO", "NetCashProvidedByUsedInOperatingActivities"))
    cfo_to_np = None
    if fy_cfo is not None and fy_np and fy_np > 0: cfo_to_np = (fy_cfo / fy_np) * 100

    roe = None
    if f_np and equity and equity > 0: roe = (f_np / equity) * 100
    elif fy_np and equity and equity > 0: roe = (fy_np / equity) * 100
    else:
        api_roe = to_float(get_field(valuation, "ROE"))
        if api_roe is not None: roe = api_roe * 100

    eps_yoy_adjusted = calc_yoy(eps_adj, prev_eps_adj)
    peg = per / eps_yoy_adjusted if per and eps_yoy_adjusted and eps_yoy_adjusted > 0 else None

    history = []
    hist_fys = fy_fins[-10:] if len(fy_fins) >= 10 else fy_fins
    for i, fy in enumerate(hist_fys):
        y_str = fy.get("CurFYEn", "")[:4]
        s = to_float(get_field(fy, "Sales", "NetSales"))
        o = to_float(get_field(fy, "OP", "OperatingProfit"))
        odp = to_float(get_field(fy, "OdP", "OrdinaryProfit"))
        eq = to_float(get_field(fy, "Eq", "Equity", "NetAssets"))
        pr = to_float(get_field(fy, "NP", "ProfitAttributableToOwnersOfParent"))
        r = (pr / eq) if pr and eq else to_float(get_field(fy, "ROE"))
        
        cfo_fy = to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities")) or 0
        cfi_fy = to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities")) or 0
        
        fc = None
        if to_float(get_field(fy, "CFO", "NetCashProvidedByUsedInOperatingActivities")) is not None or \
           to_float(get_field(fy, "CFI", "NetCashProvidedByUsedInInvestmentActivities")) is not None:
            fc = cfo_fy + cfi_fy
        
        target_date = fy.get("CurFYEn", "")[:10]
        e_raw = to_float(get_field(fy, "EPS", "EarningsPerShare"))
        e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
        de_raw = to_float(get_field(fy, "DEPS", "DilutedEarningsPerShare"))
        de_adj = adjust_per_share_value(de_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
        out_s_raw = to_float(get_field(fy, "ShOutFY"))
        tr_s_raw = to_float(get_field(fy, "TrShFY"))
        out_s = adjust_share_count(out_s_raw, get_adjustment_factor_for_date(target_date, adj_map))
        tr_s = adjust_share_count(tr_s_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
        tr_ratio = (tr_s / out_s * 100) if tr_s is not None and out_s and out_s > 0 else None
        
        prev_s = to_float(get_field(hist_fys[i-1], "Sales", "NetSales")) if i > 0 else None
        prev_o = to_float(get_field(hist_fys[i-1], "OP", "OperatingProfit")) if i > 0 else None
        prev_odp = to_float(get_field(hist_fys[i-1], "OdP", "OrdinaryProfit")) if i > 0 else None
        prev_pr = to_float(get_field(hist_fys[i-1], "NP", "ProfitAttributableToOwnersOfParent")) if i > 0 else None
        
        prev_out_s_raw = to_float(get_field(hist_fys[i-1], "ShOutFY")) if i > 0 else None
        prev_tr_s_raw = to_float(get_field(hist_fys[i-1], "TrShFY")) if i > 0 else None
        prev_target_date = hist_fys[i-1].get("CurFYEn", "")[:10] if i > 0 else ""
        prev_out_s = adjust_share_count(prev_out_s_raw, get_adjustment_factor_for_date(prev_target_date, adj_map))
        prev_tr_s = adjust_share_count(prev_tr_s_raw, get_adjustment_factor_for_date(prev_target_date, adj_map))
        
        history.append({
            "year": y_str, "sales_str": format_jpy(s), "sales_raw": s, "sales_yoy": calc_yoy(s, prev_s),
            "op_str": format_jpy(o), "op_raw": o, "op_yoy": calc_yoy(o, prev_o),
            "odp_str": format_jpy(odp), "odp_raw": odp, "odp_yoy": calc_yoy(odp, prev_odp),
            "np_str": format_jpy(pr), "np_raw": pr, "np_yoy": calc_yoy(pr, prev_pr),
            "op_margin": calc_margin(o, s),
            "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj,
            "roe_raw": r * 100 if r and r < 1.0 else r,
            "fcf_raw": fc, "fcf_margin": calc_margin(fc, s),
            "out_shares": out_s, "tr_shares": tr_s, "tr_ratio": tr_ratio,
            "out_shares_yoy": calc_yoy(out_s, prev_out_s), "tr_shares_yoy": calc_yoy(tr_s, prev_tr_s)
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

    fy_latest_sales = to_float(get_field(fy_latest, "Sales", "NetSales"))
    fy_latest_op = to_float(get_field(fy_latest, "OP", "OperatingProfit"))
    fy_latest_odp = to_float(get_field(fy_latest, "OdP", "OrdinaryProfit"))

    if f_sales or f_op or f_eps_raw:
        next_year = str(int(history[-1]["year"]) + 1) if history else "予"
        history.append({
            "year": f"{next_year}(予)", 
            "sales_str": format_jpy(f_sales), "sales_raw": f_sales, 
            "sales_yoy": calc_yoy(f_sales, fy_latest_sales),
            "op_str": format_jpy(f_op), "op_raw": f_op, 
            "op_yoy": calc_yoy(f_op, fy_latest_op),
            "odp_str": format_jpy(f_odp), "odp_raw": f_odp, 
            "odp_yoy": calc_yoy(f_odp, fy_latest_odp),
            "np_str": format_jpy(f_np), "np_raw": f_np, 
            "np_yoy": calc_yoy(f_np, fy_np),
            "op_margin": calc_margin(f_op, f_sales),
            "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj, "deps_adjusted": None, 
            "eps_yoy": calc_yoy(f_eps_adj, history[-1]["eps_adjusted"] if history else None),
            "roe_raw": None, "fcf_raw": None, "fcf_margin": None,
            "out_shares": None, "tr_shares": None, "tr_ratio": None,
            "out_shares_yoy": None, "tr_shares_yoy": None
        })

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
            c_odp = to_float(get_field(q_data, "OdP", "OrdinaryProfit"))
            c_np = to_float(get_field(q_data, "NP", "ProfitAttributableToOwnersOfParent"))
            
            s_sales, s_op, s_odp, s_np = c_sales, c_op, c_odp, c_np
            
            prev_qt = {"2Q":"1Q", "3Q":"2Q", "FY":"3Q"}.get(qt)
            if prev_qt and prev_qt in fy_tree[year]:
                p_data = fy_tree[year][prev_qt]
                p_c_sales = to_float(get_field(p_data, "Sales", "NetSales"))
                p_c_op = to_float(get_field(p_data, "OP", "OperatingProfit"))
                p_c_odp = to_float(get_field(p_data, "OdP", "OrdinaryProfit"))
                p_c_np = to_float(get_field(p_data, "NP", "ProfitAttributableToOwnersOfParent"))
                if c_sales is not None and p_c_sales is not None: s_sales = c_sales - p_c_sales
                if c_op is not None and p_c_op is not None: s_op = c_op - p_c_op
                if c_odp is not None and p_c_odp is not None: s_odp = c_odp - p_c_odp
                if c_np is not None and p_c_np is not None: s_np = c_np - p_c_np
                
            single_q_data[f"{year}-{qt}"] = {"sales": s_sales, "op": s_op, "odp": s_odp, "np": s_np, "raw": q_data}

    sorted_keys_full = sorted(single_q_data.keys())
    quarterly_history = []
    earnings_events = [] 
    
    for k in sorted_keys_full[-40:]:
        idx = sorted_keys_full.index(k)
        year_str, q_type = k.split("-")
        curr = single_q_data[k]
        q_raw = curr["raw"]
        
        prev_year_str = str(int(year_str) - 1)
        prev_k = f"{prev_year_str}-{q_type}"
        prev_q = single_q_data.get(prev_k, {})
        
        s_yoy = calc_yoy(curr["sales"], prev_q.get("sales"))
        o_yoy = calc_yoy(curr["op"], prev_q.get("op"))
        odp_yoy = calc_yoy(curr["odp"], prev_q.get("odp"))
        np_yoy = calc_yoy(curr["np"], prev_q.get("np"))
        
        prev_q_raw_qoq = single_q_data[sorted_keys_full[idx - 1]]["raw"] if idx > 0 else {}
        target_date = q_raw.get("CurPerEn", q_raw.get("CurFYEn", ""))[:10]
        
        e_raw = to_float(get_field(q_raw, "EPS", "EarningsPerShare"))
        de_raw = to_float(get_field(q_raw, "DEPS", "DilutedEarningsPerShare"))
        e_adj = adjust_per_share_value(e_raw, get_adjustment_factor_for_date(target_date, adj_map))
        de_adj = adjust_per_share_value(de_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
        out_s_raw = to_float(get_field(q_raw, "ShOutFY"))
        tr_s_raw = to_float(get_field(q_raw, "TrShFY"))
        out_s = adjust_share_count(out_s_raw, get_adjustment_factor_for_date(target_date, adj_map))
        tr_s = adjust_share_count(tr_s_raw, get_adjustment_factor_for_date(target_date, adj_map))
        
        prev_out_s_raw = to_float(get_field(prev_q_raw_qoq, "ShOutFY"))
        prev_tr_s_raw = to_float(get_field(prev_q_raw_qoq, "TrShFY"))
        prev_target_date = prev_q_raw_qoq.get("CurPerEn", prev_q_raw_qoq.get("CurFYEn", ""))[:10] if prev_q_raw_qoq else ""
        prev_out_s = adjust_share_count(prev_out_s_raw, get_adjustment_factor_for_date(prev_target_date, adj_map))
        prev_tr_s = adjust_share_count(prev_tr_s_raw, get_adjustment_factor_for_date(prev_target_date, adj_map))

        tr_ratio = (tr_s / out_s * 100) if tr_s is not None and out_s and out_s > 0 else None
        label = f"{year_str[-2:]}年 {q_type.replace('FY', '4Q')}" 
        
        disc_date = q_raw.get("DiscDate", "")[:10]
        if disc_date:
            earnings_events.append({
                "date": disc_date, "title": label, "sales_str": format_jpy(curr["sales"]), "sales_yoy": s_yoy,
                "op_str": format_jpy(curr["op"]), "op_yoy": o_yoy
            })
        
        quarterly_history.append({
            "year": label, "sales_str": format_jpy(curr["sales"]), "sales_raw": curr["sales"], "sales_yoy": s_yoy,
            "op_str": format_jpy(curr["op"]), "op_raw": curr["op"], "op_yoy": o_yoy,
            "odp_str": format_jpy(curr["odp"]), "odp_raw": curr["odp"], "odp_yoy": odp_yoy,
            "np_str": format_jpy(curr["np"]), "np_raw": curr["np"], "np_yoy": np_yoy,
            "op_margin": calc_margin(curr["op"], curr["sales"]),
            "eps_raw": e_raw, "eps_adjusted": e_adj, "deps_adjusted": de_adj,
            "out_shares": out_s, "tr_shares": tr_s, "tr_ratio": tr_ratio,
            "out_shares_yoy": calc_yoy(out_s, prev_out_s), "tr_shares_yoy": calc_yoy(tr_s, prev_tr_s),
            "roe_raw": to_float(get_field(q_raw, "ROE"))
        })

    op_margins_3y = []
    for fy in hist_fys[-4:-1]:
        s = to_float(get_field(fy, "Sales", "NetSales"))
        o = to_float(get_field(fy, "OP", "OperatingProfit"))
        if s and o and s > 0: op_margins_3y.append((o / s) * 100)
    avg_op_margin_3y = sum(op_margins_3y) / len(op_margins_3y) if op_margins_3y else None

    eps_yoy_3y = []
    for i in range(len(hist_fys)-4, len(hist_fys)-1):
        if i < 1: continue
        c_eps = to_float(get_field(hist_fys[i], "EPS", "EarningsPerShare"))
        p_eps = to_float(get_field(hist_fys[i-1], "EPS", "EarningsPerShare"))
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

    margin_interest = profile.get("margin_interest", [])
    if not isinstance(margin_interest, list): margin_interest = []
    margin_dict = {m.get("Date"): m for m in margin_interest if isinstance(m, dict) and "Date" in m}
    val_history = profile.get("valuation_history", [])
    if not isinstance(val_history, list): val_history = []
    val_dict = {v.get("Date"): v for v in val_history if isinstance(v, dict) and "Date" in v}
    
    topix_daily = profile.get("topix_daily", [])
    if not isinstance(topix_daily, list): topix_daily = []
    topix_dict = {t.get("Date", "")[:10]: to_float(t.get("C", t.get("Close"))) for t in topix_daily if isinstance(t, dict) and "Date" in t}

    sector_daily = profile.get("sector_daily", [])
    if not isinstance(sector_daily, list): sector_daily = []
    sector_dict = {s.get("Date", "")[:10]: to_float(s.get("C", s.get("Close"))) for s in sector_daily if isinstance(s, dict) and "Date" in s}

    price_margin_history = []
    last_topix = None
    last_sector = None
    
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
            adj_c = raw_c * adj_f if adj_f > 0 else raw_c

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

        m = margin_dict.get(date_str)
        mb_chg = None
        ms_chg = None
        std_buy_avg_price = None  
        std_sell_avg_price = None 

        if m: 
            curr_mb = to_float(get_field(m, "LongVol", "margin_buy"))
            curr_ms = to_float(get_field(m, "ShrtVol", "margin_sell"))
            
            if last_margin_buy is not None and curr_mb is not None:
                mb_chg = curr_mb - last_margin_buy
            if last_margin_sell is not None and curr_ms is not None:
                ms_chg = curr_ms - last_margin_sell
                
            last_margin_buy = curr_mb
            last_margin_sell = curr_ms

            buy_vol = to_float(get_field(m, "LongStdVol"))
            buy_val = to_float(get_field(m, "LongStdVal"))
            if buy_vol and buy_val and buy_vol > 0:
                std_buy_avg_price = buy_val / buy_vol

            sell_vol = to_float(get_field(m, "ShrtStdVol"))
            sell_val = to_float(get_field(m, "ShrtStdVal"))
            if sell_vol and sell_val and sell_vol > 0:
                std_sell_avg_price = sell_val / sell_vol

        price_margin_history.append({
            "date": date_str, "open": adj_o, "high": adj_h, "low": adj_l, "close": adj_c, "volume": adj_vo,
            "margin_buy": last_margin_buy,       
            "margin_sell": last_margin_sell,
            "margin_buy_chg": mb_chg,            
            "margin_sell_chg": ms_chg,
            "std_avg_price": std_buy_avg_price,        
            "std_buy_avg_price": std_buy_avg_price,    
            "std_sell_avg_price": std_sell_avg_price,  
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
            "cfo": cfo, "cfi": cfi, "cff": cff, "cash_eq": cash_eq, "cash_change": cash_change,
            "out_sh": out_sh, "tr_sh": tr_sh, "avg_sh": avg_sh, "deps_raw": deps_raw 
        },
        "forecast": { "sales": f_sales, "op": f_op, "odp": f_odp, "net_income": f_np, "eps_raw": f_eps_raw, "eps_adjusted": f_eps_adj },
        "growth": { 
            "sales_yoy": calc_yoy(sales, prev_sales), "op_yoy": calc_yoy(op, prev_op), 
            "eps_yoy": eps_yoy_adjusted, "sales_cagr_3y": sales_cagr_3y, "op_cagr_3y": op_cagr_3y, "eps_cagr_3y": eps_cagr_3y,
            "progress_op": progress_op, "avg_eps_yoy_3y": avg_eps_yoy_3y
        },
        "profitability": { 
            "op_margin": op_margin, "op_margin_change": op_margin_change, "avg_op_margin_3y": avg_op_margin_3y,
            "roe": roe, "roa_estimate": (f_np / ta * 100) if f_np and ta else None,
            "equity_ratio": equity_ratio, "payout_ratio": payout_ratio,
            "cfo_to_np": cfo_to_np, "treasury_ratio": treasury_ratio,
            "dilution_rate": dilution_rate, "eps_growth_factors": eps_growth_factors, 
            "dupont": {"current": dupont_current, "prev": dupont_prev}
        },
        "valuation": { 
            "market_cap": mktcap, "forward_per": per, "pbr": pbr, "peg": peg, 
            **get_valuation_statistics(profile.get("valuation_history", [])) 
        },
        "market_perf": { "stock_1y": stock_perf_1y, "topix_1y": topix_perf_1y, "sector_1y": sector_perf_1y },
        "history": history,
        "quarterly_history": quarterly_history,
        "price_margin_history": price_margin_history,
        "major_shareholders": processed_majors,
        "large_volume": profile.get("large_volume", []),
        "cross_shareholdings": profile.get("cross_shareholdings", {}),
        "events": { "revisions": revisions, "other": other_events, "earnings": earnings_events },
        "guidance_history": guidance_history
    }