# =============================================================================
# HERRAMIENTAS DE CÁLCULO MANUAL (PREGUNTAS TÍPICAS EXÁMENES MIT SC1X)
# =============================================================================

def batch_size_rounding(D, ct, ce, batch_size):
    """
    Resuelve preguntas como Part 2 (Vendor sells in quantities of X units):
    Evalúa TRC(Q_abajo) vs TRC(Q_arriba) y elige el mínimo costo relevante.
    """
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
    """
    Resuelve preguntas como Part 3 (Power of Two Rule en semanas):
    Fórmula oficial MIT: Tpractical = 2 ^ ceil( ln(T_weeks / sqrt(2)) / ln(2) )
    """
    T_opt_years = np.sqrt((2 * ct) / (D * ce))
    T_opt_weeks = T_opt_years * weeks_per_year
    Q_opt = T_opt_years * D
    
    # Fórmula MIT exacta con base logarítmica
    k = int(np.ceil(np.log(T_opt_weeks / np.sqrt(2)) / np.log(2)))
    T_practical_weeks = 2 ** k
    
    # Cantidad correspondiente y TRC
    T_practical_years = T_practical_weeks / weeks_per_year
    Q_practical = D * T_practical_years
    
    # Ratio TRC según fórmula MIT: 0.5 * (T/T* + T*/T)
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
    """
    Sensibilidad por pronóstico erróneo de demanda:
    TRC(Q_F*) / TRC(Q_A*) = 0.5 * ( sqrt(DA/DF) + sqrt(DF/DA) )
    """
    ratio = 0.5 * (np.sqrt(DA / DF) + np.sqrt(DF / DA))
    pct_penalty = (ratio - 1.0) * 100.0
    return {
        "ratio": ratio,
        "pct_penalty": pct_penalty
    }
