import numpy as np
import pandas as pd

# =============================================================================
# 1. MODELOS CLÁSICOS DE INVENTARIOS (MIT CTL.SC1x)
# =============================================================================

def basic_eoq(D, c, ct, h):
    ce = c * h
    Q_opt = np.sqrt((2 * ct * D) / ce)
    T_opt = Q_opt / D
    N_opt = 1.0 / T_opt
    order_cost = ct * (D / Q_opt)
    holding_cost = ce * (Q_opt / 2.0)
    trc = order_cost + holding_cost
    tc = c * D + trc
    return {
        "model": "EOQ Básico",
        "Q_opt": Q_opt,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": ce,
        "unit_price": c,
        "TRC": trc,
        "TC": tc,
        "Order_Cost": order_cost,
        "Holding_Cost": holding_cost,
        "IOH_max": Q_opt,
        "IOH_avg": Q_opt / 2.0,
        "API": 0.0,
        "b_opt": 0.0,
        "CR": 1.0
    }

def pipeline_eoq(D, c, ct, h, L):
    base = basic_eoq(D, c, ct, h)
    ce = base["ce"]
    API = D * L
    pipeline_cost = ce * API
    tc_total = base["TC"] + pipeline_cost
    return {
        "model": "EOQ con Lead Time / Pipeline",
        "Q_opt": base["Q_opt"],
        "T_opt": base["T_opt"],
        "N_opt": base["N_opt"],
        "ce": ce,
        "unit_price": c,
        "TRC": base["TRC"],
        "TC": tc_total,
        "Order_Cost": base["Order_Cost"],
        "Holding_Cost": base["Holding_Cost"],
        "Pipeline_Cost": pipeline_cost,
        "IOH_max": base["Q_opt"],
        "IOH_avg": base["Q_opt"] / 2.0,
        "API": API,
        "ROP_IP": D * L,
        "b_opt": 0.0,
        "CR": 1.0
    }

def epq_finite_replenishment(D, c, ct, h, P):
    if P <= D:
        raise ValueError("P debe ser estrictamente mayor a D.")
    ce = c * h
    Q_opt = np.sqrt((2 * ct * D) / (ce * (1.0 - (D / P))))
    T_opt = Q_opt / D
    N_opt = 1.0 / T_opt
    tp = Q_opt / P
    td = T_opt - tp
    IOH_max = Q_opt * (1.0 - (D / P))
    IOH_avg = IOH_max / 2.0
    order_cost = ct * (D / Q_opt)
    holding_cost = ce * IOH_avg
    trc = order_cost + holding_cost
    tc = c * D + trc
    return {
        "model": "EPQ (Finite Replenishment)",
        "Q_opt": Q_opt,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": ce,
        "unit_price": c,
        "TRC": trc,
        "TC": tc,
        "Order_Cost": order_cost,
        "Holding_Cost": holding_cost,
        "IOH_max": IOH_max,
        "IOH_avg": IOH_avg,
        "tp": tp,
        "td": td,
        "P": P,
        "b_opt": 0.0,
        "CR": 1.0
    }

def planned_backorders_eoq(D, c, ct, h, cs):
    ce = c * h
    CR = cs / (cs + ce)
    Q_opt_pbo = np.sqrt((2 * ct * D) / ce) * np.sqrt((cs + ce) / cs)
    b_opt = Q_opt_pbo * (ce / (cs + ce))
    IOH_max = Q_opt_pbo - b_opt
    T_opt = Q_opt_pbo / D
    N_opt = 1.0 / T_opt
    T1 = IOH_max / D
    T2 = b_opt / D
    order_cost = ct * (D / Q_opt_pbo)
    holding_cost = ce * (IOH_max ** 2) / (2 * Q_opt_pbo)
    shortage_cost = cs * (b_opt ** 2) / (2 * Q_opt_pbo)
    trc = order_cost + holding_cost + shortage_cost
    tc = c * D + trc
    return {
        "model": "EOQ con Backorders",
        "Q_opt": Q_opt_pbo,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": ce,
        "unit_price": c,
        "TRC": trc,
        "TC": tc,
        "Order_Cost": order_cost,
        "Holding_Cost": holding_cost,
        "Shortage_Cost": shortage_cost,
        "IOH_max": IOH_max,
        "IOH_avg": (IOH_max ** 2) / (2 * Q_opt_pbo),
        "b_opt": b_opt,
        "CR": CR,
        "T1": T1,
        "T2": T2
    }

# =============================================================================
# 2. MODELOS DE DESCUENTO (MIT CTL.SC1x)
# =============================================================================

def all_units_discount_3tiers(D, ct, h, c0, c1, c2, Q1, Q2):
    tiers = [
        {"tier": 0, "c": c0, "min_q": 0.0, "max_q": Q1},
        {"tier": 1, "c": c1, "min_q": Q1, "max_q": Q2},
        {"tier": 2, "c": c2, "min_q": Q2, "max_q": np.inf}
    ]
    candidates = []
    for t in tiers:
        ci = t["c"]
        Q_unc = np.sqrt((2 * ct * D) / (ci * h))
        if t["min_q"] <= Q_unc < t["max_q"]:
            tc_val = ci * D + ct * (D / Q_unc) + (ci * h) * (Q_unc / 2.0)
            candidates.append({"Q": Q_unc, "c": ci, "TC": tc_val, "type": f"Q* factible en Tier {t['tier']}"})
    for bp, ci in [(Q1, c1), (Q2, c2)]:
        tc_bp = ci * D + ct * (D / bp) + (ci * h) * (bp / 2.0)
        candidates.append({"Q": bp, "c": ci, "TC": tc_bp, "type": f"Breakpoint Q={bp}"})
        
    df_cand = pd.DataFrame(candidates).drop_duplicates(subset=["Q"]).sort_values("TC")
    best = df_cand.iloc[0]
    chosen_Q = best["Q"]
    chosen_c = best["c"]
    ce = chosen_c * h
    order_cost = ct * (D / chosen_Q)
    holding_cost = ce * (chosen_Q / 2.0)
    trc = order_cost + holding_cost
    tc = chosen_c * D + trc
    T_opt = chosen_Q / D
    N_opt = 1.0 / T_opt
    
    return {
        "model": "Descuento All-Units (3 Escalones)",
        "Q_opt": chosen_Q,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": ce,
        "unit_price": chosen_c,
        "TRC": trc,
        "TC": tc,
        "Order_Cost": order_cost,
        "Holding_Cost": holding_cost,
        "IOH_max": chosen_Q,
        "IOH_avg": chosen_Q / 2.0,
        "decision_note": f"Óptimo en {best['type']} con Q* = {chosen_Q:,.1f} y TC = ${tc:,.2f}",
        "candidates": df_cand,
        "b_opt": 0.0,
        "CR": 1.0
    }

def incremental_discount_3tiers(D, ct, h, c0, c1, c2, Q1, Q2):
    F0 = 0.0
    F1 = F0 + (c0 - c1) * Q1
    F2 = F1 + (c1 - c2) * Q2
    tiers_info = [
        {"i": 0, "c": c0, "F": F0, "min_q": 0.0, "max_q": Q1},
        {"i": 1, "c": c1, "F": F1, "min_q": Q1, "max_q": Q2},
        {"i": 2, "c": c2, "F": F2, "min_q": Q2, "max_q": np.inf}
    ]
    valid_results = []
    for t in tiers_info:
        ci = t["c"]
        Fi = t["F"]
        Qi_opt = np.sqrt((2 * D * (ct + Fi)) / (h * ci))
        is_feasible = (t["min_q"] <= Qi_opt < t["max_q"])
        cei_eff = ci + (Fi / Qi_opt)
        order_cost = ct * (D / Qi_opt)
        holding_cost = (ci * h) * (Qi_opt / 2.0)
        purch_cost = D * cei_eff
        tc_total = purch_cost + order_cost + holding_cost
        valid_results.append({
            "Tier": t["i"],
            "Rango": f"[{t['min_q']:.0f} - {t['max_q'] if t['max_q'] != np.inf else 'inf'})",
            "Precio (ci)": ci,
            "Costo Fijo Fi": Fi,
            "Q*_i": Qi_opt,
            "Factible?": is_feasible,
            "Costo Efectivo ci^e": cei_eff,
            "TC Total ($)": tc_total
        })
    df_eval = pd.DataFrame(valid_results)
    feasible_df = df_eval[df_eval["Factible?"] == True].sort_values("TC Total ($)")
    best = feasible_df.iloc[0] if not feasible_df.empty else df_eval.sort_values("TC Total ($)").iloc[0]
    
    chosen_Q = best["Q*_i"]
    chosen_c = best["Costo Efectivo ci^e"]
    marginal_c = best["Precio (ci)"]
    ce = marginal_c * h
    order_cost = ct * (D / chosen_Q)
    holding_cost = ce * (chosen_Q / 2.0)
    tc = best["TC Total ($)"]
    trc = order_cost + holding_cost
    T_opt = chosen_Q / D
    N_opt = 1.0 / T_opt
    
    return {
        "model": "Descuento Incremental (3 Escalones)",
        "Q_opt": chosen_Q,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": ce,
        "unit_price": chosen_c,
        "marginal_c": marginal_c,
        "TRC": trc,
        "TC": tc,
        "Order_Cost": order_cost,
        "Holding_Cost": holding_cost,
        "IOH_max": chosen_Q,
        "IOH_avg": chosen_Q / 2.0,
        "eval_table": df_eval,
        "decision_note": f"Tier {best['Tier']} óptimo con Q* = {chosen_Q:,.1f} un, ci^e = ${chosen_c:.3f}/un y TC = ${tc:,.2f}",
        "b_opt": 0.0,
        "CR": 1.0
    }

def one_time_deal_eoq(D, c, cg, ct, h):
    ce_base = c * h
    Q_base = np.sqrt((2 * ct * D) / ce_base)
    Qg_opt = (Q_base * c * h + D * (c - cg)) / (h * cg)
    T_normal = Q_base / D
    T_special = Qg_opt / D
    tc_base_anual = c * D + ct * (D / Q_base) + ce_base * (Q_base / 2.0)
    tc_normal_covered = (Qg_opt / D) * tc_base_anual
    tc_special = cg * Qg_opt + (h * cg) * (Qg_opt / 2.0) * (Qg_opt / D) + ct
    savings = tc_normal_covered - tc_special
    return {
        "model": "Descuento One-Time (Good Deal)",
        "Q_opt": Qg_opt,
        "Q_base": Q_base,
        "T_opt": T_special,
        "T_base": T_normal,
        "N_opt": 1.0 / T_special,
        "ce": cg * h,
        "unit_price": cg,
        "base_price": c,
        "TRC": ct + (h * cg) * (Qg_opt / 2.0) * (Qg_opt / D),
        "TC": tc_special,
        "TC_normal_period": tc_normal_covered,
        "Savings": savings,
        "IOH_max": Qg_opt,
        "IOH_avg": Qg_opt / 2.0,
        "decision_note": f"Comprar Qg* = {Qg_opt:,.1f} unidades (cubre {T_special*365:,.1f} días). Ahorro neto: ${savings:,.2f}",
        "b_opt": 0.0,
        "CR": 1.0
    }

# =============================================================================
# 3. CALCULADORA MANUAL (EXÁMENES MIT CTL.SC1x)
# =============================================================================

def batch_size_rounding(D, ct, ce, batch_size):
    Q_opt = np.sqrt((2 * ct * D) / ce)
    q_low = int(np.floor(Q_opt / batch_size)) * batch_size
    if q_low == 0:
        q_low = batch_size
    q_high = int(np.ceil(Q_opt / batch_size)) * batch_size
    
    trc_opt = np.sqrt(2 * ct * ce * D)
    trc_low = ct * (D / q_low) + ce * (q_low / 2.0)
    trc_high = ct * (D / q_high) + ce * (q_high / 2.0)
    
    if trc_low < trc_high:
        recommended_Q = q_low
        recommended_trc = trc_low
    else:
        recommended_Q = q_high
        recommended_trc = trc_high
        
    pct_penalty = ((recommended_trc / trc_opt) - 1.0) * 100.0
    return {
        "Q_opt": Q_opt,
        "batch_size": batch_size,
        "q_low": q_low,
        "trc_low": trc_low,
        "q_high": q_high,
        "trc_high": trc_high,
        "recommended_Q": recommended_Q,
        "recommended_trc": recommended_trc,
        "trc_opt": trc_opt,
        "pct_penalty": pct_penalty
    }

def power_of_two_calculator(D, ct, ce, weeks_per_year=52):
    T_opt_years = np.sqrt((2 * ct) / (D * ce))
    T_opt_weeks = T_opt_years * weeks_per_year
    Q_opt = T_opt_years * D
    k = int(np.ceil(np.log(T_opt_weeks / np.sqrt(2)) / np.log(2)))
    T_practical_weeks = 2 ** k
    T_practical_years = T_practical_weeks / weeks_per_year
    Q_practical = D * T_practical_years
    
    ratio_t = T_practical_weeks / T_opt_weeks
    trc_ratio = 0.5 * (ratio_t + (1.0 / ratio_t))
    pct_penalty = (trc_ratio - 1.0) * 100.0
    trc_opt = np.sqrt(2 * ct * ce * D)
    trc_practical = ct * (D / Q_practical) + ce * (Q_practical / 2.0)
    return {
        "T_opt_weeks": T_opt_weeks,
        "T_opt_years": T_opt_years,
        "Q_opt": Q_opt,
        "k_power": k,
        "T_practical_weeks": T_practical_weeks,
        "Q_practical": Q_practical,
        "trc_opt": trc_opt,
        "trc_practical": trc_practical,
        "pct_penalty": pct_penalty
    }

def demand_sensitivity_calculator(DA, DF):
    ratio = 0.5 * (np.sqrt(DA / DF) + np.sqrt(DF / DA))
    pct_penalty = (ratio - 1.0) * 100.0
    return {
        "ratio": ratio,
        "pct_penalty": pct_penalty
    }
