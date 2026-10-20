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
        font-size: 1.7rem !important;
        font-weight: 700;
        color: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 MIT CTL.SC1x: EOQ & Inventory Lot-Sizing Master Suite")
st.caption("Suite completa de modelos de inventario con análisis multi-descuento (All-Units, Incremental 3-Escalones y One-Time Good Deal).")

tab1, tab2 = st.tabs(["🎯 Modelo Individual & Curvas T vs Q", "📊 Comparador Multi-Modelo & Sensibilidad"])

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
        D = st.number_input("Demanda Anual (D) [un/año]", value=2000.0, min_value=1.0, step=100.0)
        ct = st.number_input("Costo Fijo por Orden (ct) [$/orden]", value=500.0, min_value=0.1, step=25.0)
        h = st.number_input("Tasa Anual de Mantenimiento (h) [%]", value=25.0, min_value=0.1, max_value=200.0, step=1.0) / 100.0
        
        # Parámetros dinámicos según el modelo
        c = 50.0
        L = 0.0
        P = 0.0
        cs = 0.0
        
        if selected_model in ["EOQ Básico (Instantaneous)", "EOQ con Lead Time / Pipeline Inventory", "EPQ (Finite Replenishment)", "EOQ con Backorders Planificados"]:
            c = st.number_input("Costo Unitario (c) [$/un]", value=50.0, min_value=0.01, step=1.0)
            
        if selected_model == "EOQ con Lead Time / Pipeline Inventory":
            st.markdown("---")
            L_days = st.number_input("Lead Time (L) [días]", value=30.0, min_value=0.0, step=1.0)
            L = L_days / 365.0

        elif selected_model == "EPQ (Finite Replenishment)":
            st.markdown("---")
            P = st.number_input(f"Tasa de Producción (P) [> {D:.0f}]", value=float(D * 2), min_value=float(D + 1.0), step=100.0)

        elif selected_model == "EOQ con Backorders Planificados":
            st.markdown("---")
            cs = st.number_input("Costo de Faltante / Shortage (cs) [$/un-año]", value=25.0, min_value=0.1, step=5.0)

        elif selected_model in ["1. Descuento All-Units (3 Escalones)", "2. Descuento Incremental / Escalas (3 Escalones)"]:
            st.markdown("---")
            st.markdown("**Estructura de 3 Escalones de Precio:**")
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
            st.markdown("**Parámetros de Oportunidad Única:**")
            c_regular = st.number_input("Precio Regular (c) [$/un]", value=50.0, min_value=0.1, step=1.0)
            cg = st.number_input("Precio de Descuento Especial (cg) [$/un]", value=40.0, min_value=0.01, max_value=float(c_regular), step=1.0)

    # CÁLCULOS
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
        
        # Tarjetas de Indicadores Principales
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Lote Óptimo (Q*)", f"{res['Q_opt']:,.1f} un")
        k2.metric("Ciclo (T*)", f"{res['T_opt']:.3f} años", f"{res['T_opt']*365:,.1f} días")
        k3.metric("Frecuencia (N*)", f"{res['N_opt']:.2f} ped/año")
        k4.metric("TRC*", f"${res['TRC']:,.2f}")
        k5.metric("Costo Total (TC*)", f"${res['TC']:,.2f}")
        
        if "decision_note" in res:
            st.info(f"💡 **Dictamen MIT:** {res['decision_note']}")
            
        if selected_model == "2. Descuento Incremental / Escalas (3 Escalones)":
            with st.expander("📋 Ver Tabla Detallada de Factibilidad y Costos por Escalón (MIT Fi y ci^e)"):
                st.dataframe(res["eval_table"].style.format({
                    "Precio (ci)": "${:.2f}",
                    "Costo Fijo Fi": "${:,.2f}",
                    "Q*_i": "{:,.1f}",
                    "Costo Efectivo ci^e": "${:.3f}",
                    "TC Total ($)": "${:,.2f}"
                }), use_container_width=True)

        if selected_model == "3. Descuento One-Time / Good Deal (Compra Única)":
            c_s1, c_s2 = st.columns(2)
            c_s1.success(f"💰 **Ahorro Total Neto:** ${res['Savings']:,.2f}")
            c_s2.info(f"⚖️ **Lote Regular vs Especial:** Q* base = {res['Q_base']:.1f} un ➔ Qg* = {res['Q_opt']:.1f} un")

        # Gráfico dinámico T vs Q
        cycles = 3
        t_cycle = res["T_opt"]
        Q_val = res["Q_opt"]
        fig = go.Figure()

        if selected_model == "3. Descuento One-Time / Good Deal (Compra Única)":
            # Gráfico comparativo especial MIT: compra gigante + retorno a ciclo normal
            t_special = res["T_opt"]
            t_base = res["T_base"]
            q_base = res["Q_base"]
            
            # Pedido especial
            fig.add_trace(go.Scatter(
                x=[0, 0, t_special],
                y=[0, Q_val, 0],
                mode='lines',
                name=f'Compra Especial Qg* ({Q_val:.0f} un)',
                line=dict(color='#DC2626', width=3, dash='dash')
            ))
            # Ciclos regulares de referencia
            time_reg = []
            ioh_reg = []
            for c_idx in range(int(np.ceil(t_special / t_base))):
                t_st = c_idx * t_base
                t_en = (c_idx + 1) * t_base
                time_reg.extend([t_st, t_st, t_en])
                ioh_reg.extend([0, q_base, 0])
            fig.add_trace(go.Scatter(
                x=time_reg, y=ioh_reg,
                mode='lines', name=f'Ciclo Regular Q* ({q_base:.0f} un)',
                line=dict(color='#0284C7', width=1.5)
            ))
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
            fig.add_trace(go.Scatter(x=time_series, y=ioh_series, mode='lines', name='Inventario Físico EPQ', line=dict(color='#0D9488', width=2.5), fill='tozeroy', fillcolor='rgba(13, 148, 136, 0.15)'))
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
            fig.add_hline(y=-b_val, line_dash="dot", line_color="#DC2626", annotation_text=f"Backorder Máx (b*) = -{b_val:.1f}")
        else:
            time_series, ioh_series = [], []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_end = (cycle + 1) * t_cycle
                time_series.extend([t_start, t_start, t_end])
                ioh_series.extend([0, Q_val, 0])
            fig.add_trace(go.Scatter(x=time_series, y=ioh_series, mode='lines', name='Inventario Físico (IOH)', line=dict(color='#0284C7', width=2.5), fill='tozeroy', fillcolor='rgba(2, 132, 199, 0.1)'))
            fig.add_hline(y=res["IOH_avg"], line_dash="dash", line_color="#059669", annotation_text=f"IOH Promedio = {res['IOH_avg']:.1f}")

        fig.update_layout(
            title=f"Curva de Inventario: Tiempo (T) vs Inventario (Q) — {selected_model}",
            xaxis_title="Tiempo t (años)",
            yaxis_title="Nivel de Inventario (unidades)",
            template="plotly_white",
            height=430,
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PESTAÑA 2: COMPARADOR MULTI-MODELO
# =============================================================================
with tab2:
    st.subheader("📊 Comparación Exhaustiva de Modelos de Inventario")
    
    st.markdown("#### Configuración para Comparativa Simultánea")
    c_cmp1, c_cmp2, c_cmp3, c_cmp4 = st.columns(4)
    with c_cmp1:
        cmp_L_days = st.number_input("Lead Time Pipeline [días]", value=30.0, step=5.0)
        cmp_L = cmp_L_days / 365.0
    with c_cmp2:
        cmp_P = st.number_input("Tasa Producción P (EPQ)", value=float(D * 2), step=100.0)
    with c_cmp3:
        cmp_cs = st.number_input("Costo Shortage cs", value=25.0, step=5.0)
    with c_cmp4:
        cmp_cg = st.number_input("Precio One-Time Deal (cg)", value=40.0, step=1.0)

    # Computación de modelos
    base_price = 50.0
    m_base = eoq.basic_eoq(D, base_price, ct, h)
    m_pipe = eoq.pipeline_eoq(D, base_price, ct, h, cmp_L)
    m_allu = eoq.all_units_discount_3tiers(D, ct, h, base_price, 45.0, 40.0, 500.0, 1000.0)
    m_incr = eoq.incremental_discount_3tiers(D, ct, h, base_price, 45.0, 40.0, 500.0, 1000.0)
    m_otd = eoq.one_time_deal_eoq(D, base_price, cmp_cg, ct, h)
    m_epq = eoq.epq_finite_replenishment(D, base_price, ct, h, cmp_P)
    m_pbo = eoq.planned_backorders_eoq(D, base_price, ct, h, cmp_cs)

    comp_list = [
        {"Modelo": "EOQ Básico", "Q*": m_base["Q_opt"], "T* (días)": m_base["T_opt"]*365, "N*": m_base["N_opt"], "Precio Efectivo": m_base["unit_price"], "TRC ($)": m_base["TRC"], "TC Total ($)": m_base["TC"]},
        {"Modelo": "EOQ con Pipeline", "Q*": m_pipe["Q_opt"], "T* (días)": m_pipe["T_opt"]*365, "N*": m_pipe["N_opt"], "Precio Efectivo": m_pipe["unit_price"], "TRC ($)": m_pipe["TRC"], "TC Total ($)": m_pipe["TC"]},
        {"Modelo": "Descuento All-Units", "Q*": m_allu["Q_opt"], "T* (días)": m_allu["T_opt"]*365, "N*": m_allu["N_opt"], "Precio Efectivo": m_allu["unit_price"], "TRC ($)": m_allu["TRC"], "TC Total ($)": m_allu["TC"]},
        {"Modelo": "Descuento Incremental", "Q*": m_incr["Q_opt"], "T* (días)": m_incr["T_opt"]*365, "N*": m_incr["N_opt"], "Precio Efectivo": m_incr["unit_price"], "TRC ($)": m_incr["TRC"], "TC Total ($)": m_incr["TC"]},
        {"Modelo": "Descuento One-Time", "Q*": m_otd["Q_opt"], "T* (días)": m_otd["T_opt"]*365, "N*": m_otd["N_opt"], "Precio Efectivo": m_otd["unit_price"], "TRC ($)": m_otd["TRC"], "TC Total ($)": m_otd["TC"]},
        {"Modelo": "EPQ (Producción Finita)", "Q*": m_epq["Q_opt"], "T* (días)": m_epq["T_opt"]*365, "N*": m_epq["N_opt"], "Precio Efectivo": m_epq["unit_price"], "TRC ($)": m_epq["TRC"], "TC Total ($)": m_epq["TC"]},
        {"Modelo": "EOQ con Backorders", "Q*": m_pbo["Q_opt"], "T* (días)": m_pbo["T_opt"]*365, "N*": m_pbo["N_opt"], "Precio Efectivo": m_pbo["unit_price"], "TRC ($)": m_pbo["TRC"], "TC Total ($)": m_pbo["TC"]},
    ]

    df_res_comp = pd.DataFrame(comp_list)
    st.dataframe(df_res_comp.style.format({
        "Q*": "{:,.1f}",
        "T* (días)": "{:,.1f}",
        "N*": "{:,.2f}",
        "Precio Efectivo": "${:.2f}",
        "TRC ($)": "${:,.2f}",
        "TC Total ($)": "${:,.2f}"
    }), use_container_width=True)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=df_res_comp["Modelo"], y=df_res_comp["TC Total ($)"], marker_color="#2563EB", name="Costo Total Anualizado"))
    fig_bar.update_layout(title="Comparativa de Costo Total (TC) entre Variantes de Inventario", yaxis_title="Costo ($)", template="plotly_white", height=380)
    st.plotly_chart(fig_bar, use_container_width=True)
