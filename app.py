import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import eoq_engine as eoq

st.set_page_config(
    page_title="MIT SC1x EOQ & Lot-Sizing Suite",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
<style>
    div[data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
        font-weight: 700;
        color: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 MIT CTL.SC1x: EOQ & Inventory Lot-Sizing Master Suite")
st.caption("Suite completa para Supply Chain: Modelado dinámico, comparación de variantes y calculadora de preguntas de examen.")

tab1, tab2, tab3 = st.tabs([
    "🎯 Modelo Individual & Curvas T vs Q",
    "📊 Comparador Multi-Modelo & Sensibilidad",
    "🧮 Calculadora Manual (Exámenes MIT)"
])

# =============================================================================
# PESTAÑA 1: MODELO INDIVIDUAL
# =============================================================================
with tab1:
    col_input, col_view = st.columns([1, 2], gap="large")
    
    with col_input:
        st.subheader("⚙️ Selección del Modelo")
        selected_model = st.selectbox(
            "Selecciona la variante de EOQ:",
            [
                "EOQ Básico (Instantaneous)",
                "EOQ con Lead Time / Pipeline Inventory",
                "1. Descuento All-Units (3 Escalones)",
                "2. Descuento Incremental / Escalas (3 Escalones)",
                "3. Descuento One-Time / Good Deal (Compra Única)",
                "EPQ (Finite Replenishment)",
                "EOQ con Backorders Planificados"
            ]
        )
        st.markdown("---")
        st.markdown("**Variables Base:**")
        D = st.number_input("Demanda Anual (D) [un/año]", value=2000.0, min_value=1.0, step=100.0, key="t1_D")
        ct = st.number_input("Costo Fijo por Orden (ct) [$/orden]", value=500.0, min_value=0.1, step=25.0, key="t1_ct")
        h = st.number_input("Tasa Anual de Mantenimiento (h) [%]", value=25.0, min_value=0.1, max_value=200.0, step=1.0, key="t1_h") / 100.0
        
        c = 50.0
        L = 0.0
        P = 0.0
        cs = 0.0
        
        if selected_model in ["EOQ Básico (Instantaneous)", "EOQ con Lead Time / Pipeline Inventory", "EPQ (Finite Replenishment)", "EOQ con Backorders Planificados"]:
            c = st.number_input("Costo Unitario (c) [$/un]", value=50.0, min_value=0.01, step=1.0, key="t1_c")
            
        if selected_model == "EOQ con Lead Time / Pipeline Inventory":
            st.markdown("---")
            L_days = st.number_input("Lead Time (L) [días]", value=30.0, min_value=0.0, step=1.0, key="t1_L")
            L = L_days / 365.0

        elif selected_model == "EPQ (Finite Replenishment)":
            st.markdown("---")
            P = st.number_input(f"Tasa de Producción (P) [> {D:.0f}]", value=float(D * 2), min_value=float(D + 1.0), step=100.0, key="t1_P")

        elif selected_model == "EOQ con Backorders Planificados":
            st.markdown("---")
            cs = st.number_input("Costo de Faltante (cs) [$/un-año]", value=25.0, min_value=0.1, step=5.0, key="t1_cs")

        elif selected_model in ["1. Descuento All-Units (3 Escalones)", "2. Descuento Incremental / Escalas (3 Escalones)"]:
            st.markdown("---")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                c0 = st.number_input("Precio Base c0 [0 a Q1)", value=50.0, min_value=0.1, step=1.0)
                c1 = st.number_input("Precio c1 [Q1 a Q2)", value=45.0, min_value=0.1, step=1.0)
                c2 = st.number_input("Precio c2 [>= Q2]", value=40.0, min_value=0.1, step=1.0)
            with col_t2:
                Q1 = st.number_input("Breakpoint 1 (Q1) [un]", value=500.0, min_value=1.0, step=50.0)
                Q2 = st.number_input("Breakpoint 2 (Q2) [un]", value=1000.0, min_value=float(Q1 + 1), step=50.0)

        elif selected_model == "3. Descuento One-Time / Good Deal (Compra Única)":
            st.markdown("---")
            c_regular = st.number_input("Precio Regular (c) [$/un]", value=50.0, min_value=0.1, step=1.0)
            cg = st.number_input("Precio Oferta (cg) [$/un]", value=40.0, min_value=0.01, max_value=float(c_regular), step=1.0)

    # Computación
    if selected_model == "EOQ Básico (Instantaneous)":
        res = eoq.basic_eoq(D, c, ct, h)
    elif selected_model == "EOQ con Lead Time / Pipeline Inventory":
        res = eoq.pipeline_eoq(D, c, ct, h, L)
    elif selected_model == "1. Descuento All-Units (3 Escalones)":
        res = eoq.all_units_discount_3tiers(D, ct, h, c0, c1, c2, Q1, Q2)
    elif selected_model == "2. Descuento Incremental / Escalas (3 Escalones)":
        res = eoq.incremental_discount_3tiers(D, ct, h, c0, c1, c2, Q1, Q2)
    elif selected_model == "3. Descuento One-Time / Good Deal (Compra Única)":
        res = eoq.one_time_deal_eoq(D, c_regular, cg, ct, h)
    elif selected_model == "EPQ (Finite Replenishment)":
        res = eoq.epq_finite_replenishment(D, c, ct, h, P)
    elif selected_model == "EOQ con Backorders Planificados":
        res = eoq.planned_backorders_eoq(D, c, ct, h, cs)

    with col_view:
        st.subheader("📈 Resultados & Gráfico del Ciclo (T vs Q)")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Lote Óptimo (Q*)", f"{res['Q_opt']:,.1f} un")
        k2.metric("Ciclo (T*)", f"{res['T_opt']:.3f} años", f"{res['T_opt']*365:,.1f} días")
        k3.metric("Frecuencia (N*)", f"{res['N_opt']:.2f} ped/año")
        k4.metric("TRC*", f"${res['TRC']:,.2f}")
        k5.metric("Costo Total (TC*)", f"${res['TC']:,.2f}")
        
        if "decision_note" in res:
            st.info(f"💡 **Dictamen MIT:** {res['decision_note']}")
            
        cycles = 3
        t_cycle = res["T_opt"]
        Q_val = res["Q_opt"]
        fig = go.Figure()

        if selected_model == "3. Descuento One-Time / Good Deal (Compra Única)":
            t_special = res["T_opt"]
            t_base = res["T_base"]
            q_base = res["Q_base"]
            fig.add_trace(go.Scatter(x=[0, 0, t_special], y=[0, Q_val, 0], mode='lines', name=f'Compra Especial Qg* ({Q_val:.0f} un)', line=dict(color='#DC2626', width=3, dash='dash')))
            time_reg, ioh_reg = [], []
            for c_idx in range(int(np.ceil(t_special / t_base))):
                t_st = c_idx * t_base
                t_en = (c_idx + 1) * t_base
                time_reg.extend([t_st, t_st, t_en])
                ioh_reg.extend([0, q_base, 0])
            fig.add_trace(go.Scatter(x=time_reg, y=ioh_reg, mode='lines', name=f'Ciclo Regular Q* ({q_base:.0f} un)', line=dict(color='#0284C7', width=1.5)))
        elif selected_model == "EPQ (Finite Replenishment)":
            tp = res["tp"]
            ioh_max = res["IOH_max"]
            time_series, ioh_series = [], []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_peak = t_start + tp
                t_end = (cycle + 1) * t_cycle
                time_series.extend([t_start, t_peak, t_end])
                ioh_series.extend([0, ioh_max, 0])
            fig.add_trace(go.Scatter(x=time_series, y=ioh_series, mode='lines', name='Inventario EPQ', line=dict(color='#0D9488', width=2.5), fill='tozeroy'))
            fig.add_hline(y=res["IOH_avg"], line_dash="dash", line_color="#D97706", annotation_text=f"IOH Promedio = {res['IOH_avg']:.1f}")
        elif selected_model == "EOQ con Backorders Planificados":
            b_val = res["b_opt"]
            ioh_max = res["IOH_max"]
            t1 = res["T1"]
            time_series, ioh_series = [], []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_cross = t_start + t1
                t_end = (cycle + 1) * t_cycle
                time_series.extend([t_start, t_cross, t_end, t_end])
                ioh_series.extend([ioh_max, 0, -b_val, ioh_max])
            fig.add_trace(go.Scatter(x=time_series, y=ioh_series, mode='lines', name='Inventario Neto', line=dict(color='#E11D48', width=2.5)))
            fig.add_hline(y=0, line_color="#1F2937")
        else:
            time_series, ioh_series = [], []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_end = (cycle + 1) * t_cycle
                time_series.extend([t_start, t_start, t_end])
                ioh_series.extend([0, Q_val, 0])
            fig.add_trace(go.Scatter(x=time_series, y=ioh_series, mode='lines', name='Inventario Físico (IOH)', line=dict(color='#0284C7', width=2.5), fill='tozeroy'))
            fig.add_hline(y=res["IOH_avg"], line_dash="dash", line_color="#059669", annotation_text=f"IOH Promedio = {res['IOH_avg']:.1f}")

        fig.update_layout(title="Curva T vs Q de Inventario", xaxis_title="Tiempo t (años)", yaxis_title="Unidades", template="plotly_white", height=430)
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PESTAÑA 2: COMPARADOR MULTI-MODELO
# =============================================================================
with tab2:
    st.subheader("📊 Comparación Exhaustiva de Modelos de Inventario")
    c_cmp1, c_cmp2, c_cmp3, c_cmp4 = st.columns(4)
    with c_cmp1:
        cmp_L_days = st.number_input("Lead Time Pipeline [días]", value=30.0, step=5.0, key="c_L")
        cmp_L = cmp_L_days / 365.0
    with c_cmp2:
        cmp_P = st.number_input("Tasa Producción P (EPQ)", value=float(D * 2), step=100.0, key="c_P")
    with c_cmp3:
        cmp_cs = st.number_input("Costo Shortage cs", value=25.0, step=5.0, key="c_cs")
    with c_cmp4:
        cmp_cg = st.number_input("Precio One-Time Deal (cg)", value=40.0, step=1.0, key="c_cg")

    base_price = 50.0
    m_base = eoq.basic_eoq(D, base_price, ct, h)
    m_pipe = eoq.pipeline_eoq(D, base_price, ct, h, cmp_L)
    m_allu = eoq.all_units_discount_3tiers(D, ct, h, base_price, 45.0, 40.0, 500.0, 1000.0)
    m_incr = eoq.incremental_discount_3tiers(D, ct, h, base_price, 45.0, 40.0, 500.0, 1000.0)
    m_otd = eoq.one_time_deal_eoq(D, base_price, cmp_cg, ct, h)
    m_epq = eoq.epq_finite_replenishment(D, base_price, ct, h, cmp_P)
    m_pbo = eoq.planned_backorders_eoq(D, base_price, ct, h, cmp_cs)

    comp_list = [
        {"Modelo": "EOQ Básico", "Q*": m_base["Q_opt"], "T* (días)": m_base["T_opt"]*365, "N*": m_base["N_opt"], "Precio": m_base["unit_price"], "TRC ($)": m_base["TRC"], "TC Total ($)": m_base["TC"]},
        {"Modelo": "EOQ con Pipeline", "Q*": m_pipe["Q_opt"], "T* (días)": m_pipe["T_opt"]*365, "N*": m_pipe["N_opt"], "Precio": m_pipe["unit_price"], "TRC ($)": m_pipe["TRC"], "TC Total ($)": m_pipe["TC"]},
        {"Modelo": "Descuento All-Units", "Q*": m_allu["Q_opt"], "T* (días)": m_allu["T_opt"]*365, "N*": m_allu["N_opt"], "Precio": m_allu["unit_price"], "TRC ($)": m_allu["TRC"], "TC Total ($)": m_allu["TC"]},
        {"Modelo": "Descuento Incremental", "Q*": m_incr["Q_opt"], "T* (días)": m_incr["T_opt"]*365, "N*": m_incr["N_opt"], "Precio": m_incr["unit_price"], "TRC ($)": m_incr["TRC"], "TC Total ($)": m_incr["TC"]},
        {"Modelo": "Descuento One-Time", "Q*": m_otd["Q_opt"], "T* (días)": m_otd["T_opt"]*365, "N*": m_otd["N_opt"], "Precio": m_otd["unit_price"], "TRC ($)": m_otd["TRC"], "TC Total ($)": m_otd["TC"]},
        {"Modelo": "EPQ (Producción Finita)", "Q*": m_epq["Q_opt"], "T* (días)": m_epq["T_opt"]*365, "N*": m_epq["N_opt"], "Precio": m_epq["unit_price"], "TRC ($)": m_epq["TRC"], "TC Total ($)": m_epq["TC"]},
        {"Modelo": "EOQ con Backorders", "Q*": m_pbo["Q_opt"], "T* (días)": m_pbo["T_opt"]*365, "N*": m_pbo["N_opt"], "Precio": m_pbo["unit_price"], "TRC ($)": m_pbo["TRC"], "TC Total ($)": m_pbo["TC"]},
    ]
    df_res_comp = pd.DataFrame(comp_list)
    st.dataframe(df_res_comp.style.format({
        "Q*": "{:,.1f}", "T* (días)": "{:,.1f}", "N*": "{:,.2f}", "Precio": "${:.2f}", "TRC ($)": "${:,.2f}", "TC Total ($)": "${:,.2f}"
    }), use_container_width=True)

# =============================================================================
# PESTAÑA 3: CALCULADORA MANUAL (PREGUNTAS DE EXAMEN MIT)
# =============================================================================
with tab3:
    st.subheader("🧮 Solucionador de Preguntas Típicas del MIT (Exámenes & Tareas)")
    st.markdown("Herramientas analíticas instantáneas diseñadas para responder exactamente a los formatos numéricos evaluados en MIT CTL.SC1x.")

    sub_tool = st.radio(
        "Seleccione el tipo de cálculo manual que solicita el problema:",
        [
            "1. Lote Restringido / Empaque de Proveedor (Vendor batch size: 50, 100, etc.)",
            "2. Regla de Potencias de Dos (Power of Two Policy en Semanas)",
            "3. Sensibilidad a Errores de Pronóstico de Demanda (DA vs DF)",
            "4. Calculadora Flash de Métricas MIT (Q*, T*, API, b*, Qg*, tp)"
        ],
        horizontal=False
    )
    st.markdown("---")

    # -------------------------------------------------------------
    # PROBLEMA TIPO 1: VENDOR BATCH SIZES (IMAGEN 5)
    # -------------------------------------------------------------
    if sub_tool == "1. Lote Restringido / Empaque de Proveedor (Vendor batch size: 50, 100, etc.)":
        st.markdown("#### 📦 Resolución: Restricción de Tamaño de Lote / Empaque")
        st.caption("Resuelve: *'The vendor only sells in quantities of X units. What order quantity do you recommend?'*")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            q_mode = st.radio("Método de entrada:", ["Tengo D, ct, c, h", "Ya calculé Q* directamente"])
            if q_mode == "Tengo D, ct, c, h":
                m_D = st.number_input("Demanda D [un/año]", value=2000.0, step=100.0, key="m_b_D")
                m_ct = st.number_input("Costo Fijo ct [$/orden]", value=500.0, step=25.0, key="m_b_ct")
                m_c = st.number_input("Costo unitario c [$/un]", value=50.0, step=1.0, key="m_b_c")
                m_h = st.number_input("Tasa h [%]", value=25.0, step=1.0, key="m_b_h") / 100.0
                m_ce = m_c * m_h
            else:
                m_Q_dir = st.number_input("Q* calculado [unidades]", value=400.0, step=10.0, key="m_b_Qdir")
                m_D = st.number_input("Demanda D [un/año]", value=2000.0, step=100.0, key="m_b_D2")
                m_ct = st.number_input("Costo Fijo ct [$/orden]", value=500.0, step=25.0, key="m_b_ct2")
                m_ce = (2 * m_ct * m_D) / (m_Q_dir ** 2)

        with c_p2:
            batch_val = st.number_input("Restricción del Proveedor: Empaques de (ej: 50 unidades)", value=50, min_value=1, step=5, key="m_batch")
            solve_batch = eoq.batch_size_rounding(m_D, m_ct, m_ce, batch_val)
            
            st.markdown("**Evaluación de Candidatos (MIT Method):**")
            st.write(f"- $Q^*$ Óptimo sin restricción: **{solve_batch['Q_opt']:.2f} un**")
            st.write(f"- Opción Redondeo Abajo: **{solve_batch['q_low']} un** ➔ TRC = **${solve_batch['trc_low']:,.2f}**")
            st.write(f"- Opción Redondeo Arriba: **{solve_batch['q_high']} un** ➔ TRC = **${solve_batch['trc_high']:,.2f}**")

        with c_p3:
            st.success("### ✅ Respuesta para el Casillero MIT:")
            st.metric("Order Quantity Recomendado", f"{solve_batch['recommended_Q']} unidades")
            st.caption(f"Penalidad en TRC frente al óptimo teórico: **+{solve_batch['pct_penalty']:.3f}%**")
            st.info(f"**Justificación:** Al ordenar {solve_batch['recommended_Q']} unidades, el TRC es ${solve_batch['recommended_trc']:,.2f}, que es estrictamente menor al de la opción alternativa.")

    # -------------------------------------------------------------
    # PROBLEMA TIPO 2: POWER OF TWO RULE (IMAGEN 6)
    # -------------------------------------------------------------
    elif sub_tool == "2. Regla de Potencias de Dos (Power of Two Policy en Semanas)":
        st.markdown("#### ⏱️ Resolución: Power of Two Policy (Calendario en Semanas)")
        st.caption("Resuelve: *'Keep the ordering pattern following the Power of Two rule (weekly, every 2, 4, 8... weeks). Assume 52 weeks/year.'*")
        
        c_w1, c_w2, c_w3 = st.columns(3)
        with c_w1:
            pw_mode = st.radio("Método de entrada:", ["Ingresar parámetros D, ct, c, h", "Ya tengo T* (en semanas o años)"], key="pw_in_mode")
            weeks_in_year = st.number_input("Semanas por año", value=52, min_value=1, step=1, key="pw_weeks")
            
            if pw_mode == "Ingresar parámetros D, ct, c, h":
                pw_D = st.number_input("Demanda D [un/año]", value=25000.0, step=1000.0, key="pw_D")
                pw_ct = st.number_input("Costo Fijo ct [$/orden]", value=750.0, step=25.0, key="pw_ct")
                pw_c = st.number_input("Costo c [$/un]", value=25.50, step=0.5, key="pw_c")
                pw_h = st.number_input("Tasa h [%]", value=15.0, step=1.0, key="pw_h") / 100.0
                pw_ce = pw_c * pw_h
                pw_res = eoq.power_of_two_calculator(pw_D, pw_ct, pw_ce, weeks_in_year)
            else:
                pw_unit_t = st.selectbox("Unidad de T* que posees:", ["Semanas", "Años directos"])
                pw_t_in = st.number_input("Valor de T*", value=6.50, step=0.5)
                pw_D = st.number_input("Demanda D [un/año]", value=25000.0, step=1000.0, key="pw_D_only")
                if pw_unit_t == "Semanas":
                    t_weeks = pw_t_in
                    t_years = pw_t_in / weeks_in_year
                else:
                    t_years = pw_t_in
                    t_weeks = pw_t_in * weeks_in_year
                
                k_val = int(np.ceil(np.log(t_weeks / np.sqrt(2)) / np.log(2)))
                t_prac = 2 ** k_val
                q_prac = pw_D * (t_prac / weeks_in_year)
                r_t = t_prac / t_weeks
                pct_err = (0.5 * (r_t + (1.0 / r_t)) - 1.0) * 100.0
                
                pw_res = {
                    "T_opt_weeks": t_weeks,
                    "T_opt_years": t_years,
                    "Q_opt": pw_D * t_years,
                    "k_power": k_val,
                    "T_practical_weeks": t_prac,
                    "Q_practical": q_prac,
                    "pct_penalty": pct_err
                }

        with c_w2:
            st.markdown("**Desglose del Procedimiento MIT:**")
            st.write(f"- $T^*$ Óptimo exacto: **{pw_res['T_opt_weeks']:.3f} semanas** ({pw_res['T_opt_years']:.4f} años)")
            st.write(f"- Fórmula MIT: $2^{{\\lceil \\ln(T^* / \\sqrt{{2}}) / \\ln(2) \\rceil}}$")
            st.write(f"- Exponente calculado: $k = {pw_res['k_power']}$ ($2^{pw_res['k_power']} = {pw_res['T_practical_weeks']}$)")
            st.write(f"- Tamaño de lote ajustado ($Q_{{practical}}$): **{pw_res['Q_practical']:,.1f} unidades**")

        with c_w3:
            st.success("### ✅ Respuesta para el Casillero MIT:")
            st.metric("Frecuencia de Reorden Recomendada", f"{pw_res['T_practical_weeks']} semanas")
            st.metric("Cantidad de Pedido (Q)", f"{pw_res['Q_practical']:,.0f} un")
            st.caption(f"Error sobre TRC*: **+{pw_res['pct_penalty']:.2f}%** (garantizado $\le 6\%$ por el Teorema MIT)")

    # -------------------------------------------------------------
    # PROBLEMA TIPO 3: SENSIBILIDAD DE PRONÓSTICO (DA vs DF)
    # -------------------------------------------------------------
    elif sub_tool == "3. Sensibilidad a Errores de Pronóstico de Demanda (DA vs DF)":
        st.markdown("#### 🎯 Análisis de Error de Pronóstico: Demanda Real ($D_A$) vs Pronosticada ($D_F$)")
        st.caption(r"Fórmula oficial MIT: $\frac{TRC(Q_F^*)}{TRC(Q_A^*)} = \frac{1}{2}\left(\sqrt{\frac{D_A}{D_F}} + \sqrt{\frac{D_F}{D_A}}\right)$")
        
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            df_val = st.number_input("Demanda Pronosticada / Usada para ordenar (DF)", value=2000.0, step=100.0)
            da_val = st.number_input("Demanda Real que ocurrió (DA)", value=3000.0, step=100.0)
            
            res_sens = eoq.demand_sensitivity_calculator(da_val, df_val)

        with c_s2:
            st.success("### Resultado de Sensibilidad MIT:")
            st.metric("Ratio de Sobrecosto: TRC(QF*) / TRC(QA*)", f"{res_sens['ratio']:.4f}x")
            st.metric("Penalidad Porcentual en Costos Relevantes", f"+{res_sens['pct_penalty']:.2f}%")
            st.info(f"A pesar de un error en demanda del {abs((da_val-df_val)/df_val)*100:.1f}%, el costo solo aumenta un **{res_sens['pct_penalty']:.2f}%**, demostrando la robustez del modelo.")

    # -------------------------------------------------------------
    # PROBLEMA TIPO 4: FLASH CALCULATOR POR MODELO
    # -------------------------------------------------------------
    elif sub_tool == "4. Calculadora Flash de Métricas MIT (Q*, T*, API, b*, Qg*, tp)":
        st.markdown("#### ⚡ Calculadora Rápida de Métricas Específicas")
        flash_model = st.selectbox(
            "Seleccione el modelo para extraer sus variables directas:",
            ["EOQ con Backorders (b*, CR, T1, T2)", "EPQ (tp, td, IOH max)", "Lead Time / Pipeline (API, ROP)", "One-Time Good Deal (Qg*, Ahorro)"]
        )
        
        if flash_model == "EOQ con Backorders (b*, CR, T1, T2)":
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                f_D = st.number_input("D", value=2000.0, step=100.0, key="fb_D")
                f_ct = st.number_input("ct", value=500.0, step=25.0, key="fb_ct")
                f_ce = st.number_input("ce (c * h)", value=12.5, step=1.0, key="fb_ce")
                f_cs = st.number_input("cs (costo unitario faltante)", value=25.0, step=2.5, key="fb_cs")
                f_res = eoq.planned_backorders_eoq(f_D, f_ce/0.25, f_ct, 0.25, f_cs)
            with col_b2:
                st.write(f"- **Critical Ratio (CR):** `{f_res['CR']:.4f}`")
                st.write(f"- **Lote Óptimo Q* (PBO):** `{f_res['Q_opt']:.2f}` unidades")
                st.write(f"- **Faltante Máximo b*:** `{f_res['b_opt']:.2f}` unidades")
                st.write(f"- **Inventario Físico Máximo (Q* - b*):** `{f_res['IOH_max']:.2f}` unidades")
                st.write(f"- **Tiempo con inventario T1:** `{f_res['T1']*365:.1f}` días")
                st.write(f"- **Tiempo en agotado T2:** `{f_res['T2']*365:.1f}` días")

        elif flash_model == "EPQ (tp, td, IOH max)":
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                fe_D = st.number_input("Demanda D", value=2000.0, key="fe_D")
                fe_P = st.number_input("Tasa de Producción P (> D)", value=4000.0, key="fe_P")
                fe_ct = st.number_input("Costo de Setup ct", value=500.0, key="fe_ct")
                fe_ce = st.number_input("ce (c * h)", value=12.5, key="fe_ce")
                fe_res = eoq.epq_finite_replenishment(fe_D, fe_ce/0.25, fe_ct, 0.25, fe_P)
            with col_e2:
                st.write(f"- **Lote Óptimo EPQ (Q*):** `{fe_res['Q_opt']:.2f}` unidades")
                st.write(f"- **Inventario Máximo (IOH max):** `{fe_res['IOH_max']:.2f}` unidades")
                st.write(f"- **Tiempo de Producción tp:** `{fe_res['tp']*365:.1f}` días ({fe_res['tp']:.3f} años)")
                st.write(f"- **Tiempo de Consumo td:** `{fe_res['td']*365:.1f}` días ({fe_res['td']:.3f} años)")

        elif flash_model == "Lead Time / Pipeline (API, ROP)":
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                fl_D = st.number_input("Demanda Anual D", value=2000.0, key="fl_D")
                fl_L = st.number_input("Lead Time L (en días)", value=30.0, key="fl_L") / 365.0
            with col_l2:
                st.write(f"- **Average Pipeline Inventory (API = D * L):** `{fl_D * fl_L:.2f}` unidades")
                st.write(f"- **Punto de Reorden en Posición de Inventario (ROP IP = D * L):** `{fl_D * fl_L:.2f}` unidades")

        elif flash_model == "One-Time Good Deal (Qg*, Ahorro)":
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fg_D = st.number_input("Demanda D", value=2000.0, key="fg_D")
                fg_c = st.number_input("Precio regular c", value=50.0, key="fg_c")
                fg_cg = st.number_input("Precio oferta cg", value=40.0, key="fg_cg")
                fg_ct = st.number_input("Costo orden ct", value=500.0, key="fg_ct")
                fg_h = st.number_input("Tasa h [%]", value=25.0, key="fg_h") / 100.0
                fg_res = eoq.one_time_deal_eoq(fg_D, fg_c, fg_cg, fg_ct, fg_h)
            with col_g2:
                st.write(f"- **Cantidad Óptima a Comprar (Qg*):** `{fg_res['Q_opt']:,.1f}` unidades")
                st.write(f"- **Tiempo cubierto por el pedido:** `{fg_res['T_opt']*365:.1f}` días ({fg_res['T_opt']:.2f} años)")
                st.write(f"- **Ahorro Neto Total:** `${fg_res['Savings']:,.2f}`")
