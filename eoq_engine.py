import numpy as np
import pandas as pd

def basic_eoq(D, c, ct, h):
    """
    Modelo EOQ Básico de MIT SC1x:
    D: Demanda anual/periódica (units/time)
    c: Costo unitario ($/unit)
    ct: Costo fijo por orden ($/order)
    h: Tasa anual de mantenimiento de inventario (% o decimal)
    """
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
    """
    EOQ con Lead Time y Pipeline Inventory (MIT SC1x):
    L: Lead time (en la misma unidad de tiempo que D, ej: años o días)
    """
    base = basic_eoq(D, c, ct, h)
    ce = base["ce"]
    API = D * L
    pipeline_holding_cost = ce * API
    
    # El lote óptimo Q* no cambia con L > 0
    trc = base["TRC"]
    tc_with_pipeline = c * D + trc + pipeline_holding_cost
    
    return {
        "model": "EOQ con Lead Time / Pipeline",
        "Q_opt": base["Q_opt"],
        "T_opt": base["T_opt"],
        "N_opt": base["N_opt"],
        "ce": ce,
        "TRC": trc,
        "TC": tc_with_pipeline,
        "Order_Cost": base["Order_Cost"],
        "Holding_Cost": base["Holding_Cost"],
        "Pipeline_Cost": pipeline_holding_cost,
        "IOH_max": base["Q_opt"],
        "IOH_avg": base["Q_opt"] / 2.0,
        "API": API,
        "ROP_IP": D * L,
        "b_opt": 0.0,
        "CR": 1.0
    }

def epq_finite_replenishment(D, c, ct, h, P):
    """
    EPQ (Economic Production Quantity) con tasa finita de producción P (P > D)
    """
    if P <= D:
        raise ValueError("La tasa de producción P debe ser estrictamente mayor a la demanda D (P > D).")
    
    ce = c * h
    factor_epq = np.sqrt(1.0 - (D / P))
    Q_opt = np.sqrt((2 * ct * D) / (ce * (1.0 - (D / P))))
    T_opt = Q_opt / D
    N_opt = 1.0 / T_opt
    
    tp = Q_opt / P       # Tiempo de producción (fase de acumulación)
    td = T_opt - tp      # Tiempo de puro consumo
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
    """
    EOQ con Backorders Planificados (Shortages permitidos):
    cs: Shortage penalty cost ($/unit/time)
    """
    ce = c * h
    CR = cs / (cs + ce)  # Critical Ratio
    Q_opt_pbo = np.sqrt((2 * ct * D) / ce) * np.sqrt((cs + ce) / cs)
    b_opt = Q_opt_pbo * (ce / (cs + ce))
    IOH_max = Q_opt_pbo - b_opt
    
    T_opt = Q_opt_pbo / D
    N_opt = 1.0 / T_opt
    T1 = (Q_opt_pbo - b_opt) / D  # Tiempo con inventario positivo
    T2 = b_opt / D                # Tiempo en backorder
    
    order_cost = ct * (D / Q_opt_pbo)
    holding_cost = ce * ((Q_opt_pbo - b_opt) ** 2) / (2 * Q_opt_pbo)
    shortage_cost = cs * (b_opt ** 2) / (2 * Q_opt_pbo)
    trc = order_cost + holding_cost + shortage_cost
    tc = c * D + trc
    
    return {
        "model": "EOQ con Backorders Planificados",
        "Q_opt": Q_opt_pbo,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": ce,
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

def all_units_discount_eoq(D, c0, c1, Q1, ct, h):
    """
    EOQ con Descuento por Volumen (All-Units):
    c0: Precio unitario base
    c1: Precio con descuento si Q >= Q1
    Q1: Cantidad mínima requerida para el descuento
    """
    ce0 = c0 * h
    ce1 = c1 * h
    Q0_opt = np.sqrt((2 * ct * D) / ce0)
    Q1_opt = np.sqrt((2 * ct * D) / ce1)
    
    TC_Q0 = c0 * D + ct * (D / Q0_opt) + ce0 * (Q0_opt / 2.0)
    
    if Q1_opt >= Q1:
        chosen_Q = Q1_opt
        chosen_c = c1
        chosen_ce = ce1
        decision_note = f"Q*(c1) = {Q1_opt:.2f} >= breakpoint {Q1}. Se toma el descuento al tamaño de lote Q*."
    else:
        TC_breakpoint = c1 * D + ct * (D / Q1) + ce1 * (Q1 / 2.0)
        if TC_breakpoint < TC_Q0:
            chosen_Q = Q1
            chosen_c = c1
            chosen_ce = ce1
            decision_note = f"TC(Q1={Q1}) = ${TC_breakpoint:,.2f} < TC(Q0*) = ${TC_Q0:,.2f}. Conviene ordenar en el breakpoint Q1."
        else:
            chosen_Q = Q0_opt
            chosen_c = c0
            chosen_ce = ce0
            decision_note = f"TC(Q0*) = ${TC_Q0:,.2f} < TC(Q1={Q1}) = ${TC_breakpoint:,.2f}. No conviene el descuento; ordenar Q0*."
            
    T_opt = chosen_Q / D
    N_opt = 1.0 / T_opt
    order_cost = ct * (D / chosen_Q)
    holding_cost = chosen_ce * (chosen_Q / 2.0)
    trc = order_cost + holding_cost
    tc = chosen_c * D + trc
    
    return {
        "model": "EOQ con Descuento por Volumen (All-Units)",
        "Q_opt": chosen_Q,
        "T_opt": T_opt,
        "N_opt": N_opt,
        "ce": chosen_ce,
        "unit_price": chosen_c,
        "TRC": trc,
        "TC": tc,
        "Order_Cost": order_cost,
        "Holding_Cost": holding_cost,
        "IOH_max": chosen_Q,
        "IOH_avg": chosen_Q / 2.0,
        "decision_note": decision_note,
        "Q0_opt": Q0_opt,
        "Q1_opt": Q1_opt,
        "TC_Q0": TC_Q0,
        "b_opt": 0.0,
        "CR": 1.0
    }

def one_time_deal_eoq(D, c, cg, ct, h):
    """
    EOQ Special Order / One Time Good Deal Purchase Price (MIT SC1x)
    """
    Q_base = np.sqrt((2 * ct * D) / (c * h))
    Qg_opt = (Q_base * c * h + D * (c - cg)) / (h * cg)
    return {
        "Qg_opt": Qg_opt,
        "Q_base": Q_base,
        "T_special": Qg_opt / D
    }