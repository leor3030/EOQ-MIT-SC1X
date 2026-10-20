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

# Estilo personalizado para KPIs
st.markdown("""
<style>
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
        color: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 MIT CTL.SC1x: Economic Order Quantity (EOQ) Master Suite")
st.caption("Calculadora analítica, curvas dinámicas de inventario T vs Q y comparador multi-modelo de gestión de inventarios.")

tab1, tab2 = st.tabs(["🎯 Modelo Individual & Curvas T vs Q", "📊 Comparador Multi-Modelo & Sensibilidad"])

# =============================================================================
# PESTAÑA 1: MODELO INDIVIDUAL CON INPUTS DINÁMICOS Y GRÁFICO T VS Q
# =============================================================================
with tab1:
    col_input, col_view = st.columns([1, 2], gap="large")
    
    with col_input:
        st.subheader("⚙️ Configuración del Modelo")
        selected_model = st.selectbox(
            "Seleccione el Modelo de EOQ a Calcular",
            [
                "EOQ Básico (Instantaneous)",
                "EOQ con Lead Time / Pipeline Inventory",
                "EOQ con Descuento por Volumen (All-Units)",
                "EPQ (Economic Production Quantity)",
                "EOQ con Backorders Planificados (Shortages)"
            ]
        )
        st.markdown("---")
        st.markdown("**Variables Base:**")
        
        # Inputs Base comunes
        D = st.number_input("Demanda Periódica / Anual (D) [unidades/año]", value=2000.0, min_value=1.0, step=100.0)
        c = st.number_input("Costo Unitario Base (c) [$/unidad]", value=50.0, min_value=0.01, step=1.0)
        ct = st.number_input("Costo Fijo por Orden (ct) [$/orden]", value=500.0, min_value=0.1, step=25.0)
        h = st.number_input("Tasa Anual de Mantenimiento (h) [%]", value=25.0, min_value=0.1, max_value=200.0, step=1.0) / 100.0
        
        # Inputs Dinámicos según modelo
        L = 0.0
        P = 0.0
        cs = 0.0
        c1 = c
        Q1 = 0.0
        
        if selected_model == "EOQ con Lead Time / Pipeline Inventory":
            st.markdown("---")
            st.markdown("**Parámetros de Tiempo de Entrega:**")
            unit_time = st.radio("Unidad del Lead Time:", ["Días (asumiendo 365 días/año)", "Años directos"], horizontal=True)
            if "Días" in unit_time:
                L_days = st.number_input("Lead Time (L) [días]", value=30.0, min_value=0.0, step=1.0)
                L = L_days / 365.0
            else:
                L = st.number_input("Lead Time (L) [en fracción de año]", value=0.1, min_value=0.0, step=0.01)

        elif selected_model == "EOQ con Descuento por Volumen (All-Units)":
            st.markdown("---")
            st.markdown("**Parámetros del Descuento por Volumen:**")
            c1 = st.number_input("Precio con Descuento (c1) [$/unidad]", value=42.5, min_value=0.01, max_value=float(c), step=0.5)
            Q1 = st.number_input("Breakpoint de Cantidad (Q1) [unidades]", value=800.0, min_value=1.0, step=50.0)

        elif selected_model == "EPQ (Economic Production Quantity)":
            st.markdown("---")
            st.markdown("**Parámetros de Producción Finita:**")
            P = st.number_input(f"Tasa de Producción (P) [debe ser > D ({D:.0f})]", value=float(D * 2), min_value=float(D + 1.0), step=100.0)

        elif selected_model == "EOQ con Backorders Planificados (Shortages)":
            st.markdown("---")
            st.markdown("**Parámetros de Faltantes:**")
            cs = st.number_input("Costo de Faltante / Penalidad (cs) [$/unidad-año]", value=25.0, min_value=0.1, step=5.0)

    # CÁLCULO DEL MODELO
    if selected_model == "EOQ Básico (Instantaneous)":
        res = eoq.basic_eoq(D, c, ct, h)
    elif selected_model == "EOQ con Lead Time / Pipeline Inventory":
        res = eoq.pipeline_eoq(D, c, ct, h, L)
    elif selected_model == "EOQ con Descuento por Volumen (All-Units)":
        res = eoq.all_units_discount_eoq(D, c, c1, Q1, ct, h)
    elif selected_model == "EPQ (Economic Production Quantity)":
        res = eoq.epq_finite_replenishment(D, c, ct, h, P)
    elif selected_model == "EOQ con Backorders Planificados (Shortages)":
        res = eoq.planned_backorders_eoq(D, c, ct, h, cs)

    with col_view:
        st.subheader("📈 Resultados & Gráfico del Ciclo (T vs Q)")
        
        # Tarjetas de Indicadores Principales (MIT KPIs)
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Lote Óptimo (Q*)", f"{res['Q_opt']:.1f} un")
        kpi2.metric("Ciclo (T*)", f"{res['T_opt']:.3f} años", f"{res['T_opt']*365:.1f} días")
        kpi3.metric("Frecuencia (N*)", f"{res['N_opt']:.2f} ped/año")
        kpi4.metric("TRC*", f"${res['TRC']:,.2f}")
        kpi5.metric("Costo Total (TC*)", f"${res['TC']:,.2f}")

        # Indicadores Secundarios específicos
        if selected_model == "EOQ con Lead Time / Pipeline Inventory":
            m1, m2 = st.columns(2)
            m1.info(f"📦 **Inventario en Tránsito (API):** {res['API']:.1f} unidades")
            m2.info(f"🎯 **Punto de Reorden en Posición de Inventario (IP):** {res['ROP_IP']:.1f} unidades")
        elif selected_model == "EPQ (Economic Production Quantity)":
            m1, m2 = st.columns(2)
            m1.info(f"⚙️ **Tiempo de Producción (tp):** {res['tp']:.3f} años ({res['tp']*365:.1f} días) | Tasa: P-D = {P-D:.1f} un/año")
            m2.info(f"📦 **Inventario Máximo en Mano (IOH max):** {res['IOH_max']:.1f} unidades")
        elif selected_model == "EOQ con Backorders Planificados (Shortages)":
            m1, m2, m3 = st.columns(3)
            m1.info(f"⚖️ **Critical Ratio (CR):** {res['CR']:.4f}")
            m2.info(f"⏳ **Backorder Óptimo (b*):** {res['b_opt']:.1f} unidades")
            m3.info(f"📦 **Inventario Físico Máx (Q* - b*):** {res['IOH_max']:.1f} unidades")
        elif selected_model == "EOQ con Descuento por Volumen (All-Units)":
            st.success(f"💡 **Decisión MIT:** {res['decision_note']}")

        # GENERACIÓN DEL GRÁFICO DINÁMICO T vs Q (Inventario en Mano a lo largo del tiempo)
        cycles = 3  # Mostrar 3 ciclos completos
        t_cycle = res["T_opt"]
        Q_val = res["Q_opt"]
        
        fig = go.Figure()

        if selected_model in ["EOQ Básico (Instantaneous)", "EOQ con Lead Time / Pipeline Inventory", "EOQ con Descuento por Volumen (All-Units)"]:
            time_series = []
            ioh_series = []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_end = (cycle + 1) * t_cycle
                # Vértices del diente de sierra clásico
                time_series.extend([t_start, t_start, t_end])
                ioh_series.extend([0 if cycle > 0 else 0, Q_val, 0])
                
            fig.add_trace(go.Scatter(
                x=time_series, y=ioh_series,
                mode='lines', name='Inventario Físico (IOH)',
                line=dict(color='#0284C7', width=2.5),
                fill='tozeroy', fillcolor='rgba(2, 132, 199, 0.1)'
            ))
            
            # Línea promedio
            fig.add_hline(y=res["IOH_avg"], line_dash="dash", line_color="#059669",
                          annotation_text=f"IOH Promedio = {res['IOH_avg']:.1f} un", annotation_position="top right")

        elif selected_model == "EPQ (Economic Production Quantity)":
            tp = res["tp"]
            ioh_max = res["IOH_max"]
            time_series = []
            ioh_series = []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_peak = t_start + tp
                t_end = (cycle + 1) * t_cycle
                time_series.extend([t_start, t_peak, t_end])
                ioh_series.extend([0, ioh_max, 0])
                
            fig.add_trace(go.Scatter(
                x=time_series, y=ioh_series,
                mode='lines', name='Inventario Físico EPQ',
                line=dict(color='#0D9488', width=2.5),
                fill='tozeroy', fillcolor='rgba(13, 148, 136, 0.15)'
            ))
            fig.add_hline(y=res["IOH_avg"], line_dash="dash", line_color="#D97706",
                          annotation_text=f"IOH Promedio = {res['IOH_avg']:.1f} un", annotation_position="top right")
            fig.add_hline(y=ioh_max, line_dash="dot", line_color="#6B7280",
                          annotation_text=f"IOH Máx = {ioh_max:.1f} un", annotation_position="bottom right")

        elif selected_model == "EOQ con Backorders Planificados (Shortages)":
            b_val = res["b_opt"]
            ioh_max = res["IOH_max"]
            t1 = res["T1"]
            time_series = []
            ioh_series = []
            for cycle in range(cycles):
                t_start = cycle * t_cycle
                t_cross = t_start + t1
                t_end = (cycle + 1) * t_cycle
                time_series.extend([t_start, t_cross, t_end, t_end])
                ioh_series.extend([ioh_max, 0, -b_val, ioh_max])
                
            fig.add_trace(go.Scatter(
                x=time_series, y=ioh_series,
                mode='lines', name='Nivel Neto de Inventario (IOH & Backorder)',
                line=dict(color='#E11D48', width=2.5)
            ))
            fig.add_hline(y=0, line_color="#1F2937", line_width=1.5)
            fig.add_hline(y=-b_val, line_dash="dot", line_color="#DC2626",
                          annotation_text=f"Backorder Máx (b*) = -{b_val:.1f} un", annotation_position="bottom left")
            fig.add_hline(y=ioh_max, line_dash="dot", line_color="#2563EB",
                          annotation_text=f"IOH Máx = {ioh_max:.1f} un", annotation_position="top left")

        fig.update_layout(
            title=f"Curva de Ciclo de Inventario: Tiempo (T) vs Inventario (Q) — {selected_model}",
            xaxis_title="Tiempo t (años)",
            yaxis_title="Unidades de Inventario (Q / IOH)",
            template="plotly_white",
            hovermode="x unified",
            height=430,
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gráfico adicional: Curvas de Costos TRC(Q) vs Q
        with st.expander("🔎 Ver Curvas de Costos Relevantes: TRC(Q) vs Tamaño de Lote (Q)"):
            q_range = np.linspace(max(10, res["Q_opt"] * 0.2), res["Q_opt"] * 2.2, 200)
            ce_val = res["ce"]
            
            fig_cost = go.Figure()
            if selected_model == "EPQ (Economic Production Quantity)":
                trc_curve = ct * (D / q_range) + ce_val * (q_range / 2.0) * (1.0 - (D / P))
                holding_curve = ce_val * (q_range / 2.0) * (1.0 - (D / P))
            elif selected_model == "EOQ con Backorders Planificados (Shortages)":
                trc_curve = np.sqrt(2 * ct * ce_val * D * (cs / (cs + ce_val))) * (0.5 * (q_range/res["Q_opt"] + res["Q_opt"]/q_range))
                holding_curve = ce_val * ((q_range - res["b_opt"])**2) / (2 * q_range)
            else:
                trc_curve = ct * (D / q_range) + ce_val * (q_range / 2.0)
                holding_curve = ce_val * (q_range / 2.0)
                
            order_curve = ct * (D / q_range)

            fig_cost.add_trace(go.Scatter(x=q_range, y=order_curve, mode='lines', name='Costo de Ordenar (ct*D/Q)', line=dict(color='#DC2626', dash='dash')))
            fig_cost.add_trace(go.Scatter(x=q_range, y=holding_curve, mode='lines', name='Costo de Mantenimiento', line=dict(color='#16A34A', dash='dash')))
            fig_cost.add_trace(go.Scatter(x=q_range, y=trc_curve, mode='lines', name='TRC Total Relevante', line=dict(color='#1E40AF', width=3)))
            fig_cost.add_vline(x=res["Q_opt"], line_color="#D97706", line_dash="dot", annotation_text=f"Q* = {res['Q_opt']:.1f}")

            fig_cost.update_layout(
                title="Trade-off Económico: Costo de Ordenar vs Costo de Mantener",
                xaxis_title="Cantidad de Pedido (Q)",
                yaxis_title="Costo ($/año)",
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_cost, use_container_width=True)

# =============================================================================
# PESTAÑA 2: COMPARADOR MULTI-MODELO & ANÁLISIS DE SENSIBILIDAD MIT
# =============================================================================
with tab2:
    st.subheader("📊 Comparación Exhaustiva de Modelos de Inventario")
    st.markdown("Compara el modelo base frente a variaciones (Pipeline, EPQ, Descuentos y Backorders) bajo un mismo escenario de demanda.")

    st.markdown("#### 1. Parámetros Específicos para la Comparación")
    c_cmp1, c_cmp2, c_cmp3, c_cmp4 = st.columns(4)
    with c_cmp1:
        cmp_L_days = st.number_input("Lead Time para Pipeline [días]", value=30.0, min_value=0.0, step=5.0)
        cmp_L = cmp_L_days / 365.0
    with c_cmp2:
        cmp_P = st.number_input(f"Tasa de Producción P para EPQ [> {D:.0f}]", value=float(D * 2), min_value=float(D + 1), step=100.0)
    with c_cmp3:
        cmp_cs = st.number_input("Costo de Faltante cs [$/un-año]", value=25.0, min_value=0.1, step=5.0)
    with c_cmp4:
        cmp_c1 = st.number_input("Precio con Descuento c1 [$/un]", value=float(c * 0.85), min_value=0.1, step=0.5)
        cmp_Q1 = st.number_input("Breakpoint Descuento Q1 [un]", value=800.0, min_value=1.0, step=50.0)

    # Computar los 5 modelos
    m_basic = eoq.basic_eoq(D, c, ct, h)
    m_pipe = eoq.pipeline_eoq(D, c, ct, h, cmp_L)
    m_epq = eoq.epq_finite_replenishment(D, c, ct, h, cmp_P)
    m_pbo = eoq.planned_backorders_eoq(D, c, ct, h, cmp_cs)
    m_disc = eoq.all_units_discount_eoq(D, c, cmp_c1, cmp_Q1, ct, h)

    models_data = [
        {
            "Modelo": "1. EOQ Básico",
            "Lote Óptimo (Q*)": m_basic["Q_opt"],
            "Ciclo T* (días)": m_basic["T_opt"] * 365.0,
            "Pedidos/Año (N*)": m_basic["N_opt"],
            "IOH Máx": m_basic["IOH_max"],
            "IOH Prom": m_basic["IOH_avg"],
            "API (En Tránsito)": 0.0,
            "Backorder (b*)": 0.0,
            "TRC ($)": m_basic["TRC"],
            "TC Total ($)": m_basic["TC"],
            "Diferencia TC vs Base ($)": 0.0
        },
        {
            "Modelo": "2. EOQ con Pipeline",
            "Lote Óptimo (Q*)": m_pipe["Q_opt"],
            "Ciclo T* (días)": m_pipe["T_opt"] * 365.0,
            "Pedidos/Año (N*)": m_pipe["N_opt"],
            "IOH Máx": m_pipe["IOH_max"],
            "IOH Prom": m_pipe["IOH_avg"],
            "API (En Tránsito)": m_pipe["API"],
            "Backorder (b*)": 0.0,
            "TRC ($)": m_pipe["TRC"],
            "TC Total ($)": m_pipe["TC"],
            "Diferencia TC vs Base ($)": m_pipe["TC"] - m_basic["TC"]
        },
        {
            "Modelo": "3. EPQ (Producción Finita)",
            "Lote Óptimo (Q*)": m_epq["Q_opt"],
            "Ciclo T* (días)": m_epq["T_opt"] * 365.0,
            "Pedidos/Año (N*)": m_epq["N_opt"],
            "IOH Máx": m_epq["IOH_max"],
            "IOH Prom": m_epq["IOH_avg"],
            "API (En Tránsito)": 0.0,
            "Backorder (b*)": 0.0,
            "TRC ($)": m_epq["TRC"],
            "TC Total ($)": m_epq["TC"],
            "Diferencia TC vs Base ($)": m_epq["TC"] - m_basic["TC"]
        },
        {
            "Modelo": "4. EOQ con Backorders",
            "Lote Óptimo (Q*)": m_pbo["Q_opt"],
            "Ciclo T* (días)": m_pbo["T_opt"] * 365.0,
            "Pedidos/Año (N*)": m_pbo["N_opt"],
            "IOH Máx": m_pbo["IOH_max"],
            "IOH Prom": m_pbo["IOH_avg"],
            "API (En Tránsito)": 0.0,
            "Backorder (b*)": m_pbo["b_opt"],
            "TRC ($)": m_pbo["TRC"],
            "TC Total ($)": m_pbo["TC"],
            "Diferencia TC vs Base ($)": m_pbo["TC"] - m_basic["TC"]
        },
        {
            "Modelo": "5. EOQ con Descuento",
            "Lote Óptimo (Q*)": m_disc["Q_opt"],
            "Ciclo T* (días)": m_disc["T_opt"] * 365.0,
            "Pedidos/Año (N*)": m_disc["N_opt"],
            "IOH Máx": m_disc["IOH_max"],
            "IOH Prom": m_disc["IOH_avg"],
            "API (En Tránsito)": 0.0,
            "Backorder (b*)": 0.0,
            "TRC ($)": m_disc["TRC"],
            "TC Total ($)": m_disc["TC"],
            "Diferencia TC vs Base ($)": m_disc["TC"] - m_basic["TC"]
        }
    ]

    df_compare = pd.DataFrame(models_data)
    
    st.markdown("#### 2. Matriz Comparativa de Desempeño Operacional y Costos")
    st.dataframe(
        df_compare.style.format({
            "Lote Óptimo (Q*)": "{:,.1f}",
            "Ciclo T* (días)": "{:,.1f}",
            "Pedidos/Año (N*)": "{:,.2f}",
            "IOH Máx": "{:,.1f}",
            "IOH Prom": "{:,.1f}",
            "API (En Tránsito)": "{:,.1f}",
            "Backorder (b*)": "{:,.1f}",
            "TRC ($)": "${:,.2f}",
            "TC Total ($)": "${:,.2f}",
            "Diferencia TC vs Base ($)": "${:,.2f}"
        }),
        use_container_width=True
    )

    # Gráfico de barras comparativo de costos
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df_compare["Modelo"],
        y=df_compare["TRC ($)"],
        name="Total Relevant Costs (TRC)",
        marker_color="#3B82F6"
    ))
    fig_bar.update_layout(
        title="Comparación de Costos Relevantes (TRC) entre Modelos",
        yaxis_title="Costo ($/año)",
        template="plotly_white",
        height=380
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------------------------------------
    # ANÁLISIS DE SENSIBILIDAD EOQ (MIT SC1X FORMULA)
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 3. Análisis de Robustez y Sensibilidad del EOQ (Fórmula MIT)")
    st.markdown(r"En MIT CTL.SC1x se demuestra que el EOQ es sumamente robusto frente a desviaciones del lote: $\frac{TRC(Q)}{TRC(Q^*)} = \frac{1}{2}\left(\frac{Q}{Q^*} + \frac{Q^*}{Q}\right)$")
    
    col_sens1, col_sens2 = st.columns([1, 2])
    with col_sens1:
        ratio_q = st.slider("Desviación del lote ordenado (Q / Q*)", min_value=0.2, max_value=2.5, value=1.5, step=0.05)
        trc_ratio = 0.5 * (ratio_q + (1.0 / ratio_q))
        pct_penalty = (trc_ratio - 1.0) * 100.0
        
        st.metric("Penalidad en Costos Relevantes (TRC / TRC*)", f"{trc_ratio:.3f}x", f"+{pct_penalty:.2f}%")
        st.caption(f"Si ordenas un **{ratio_q*100:.0f}%** del lote óptimo (Q = {ratio_q*m_basic['Q_opt']:.0f} un), tus costos relevantes solo se incrementan en **{pct_penalty:.2f}%**.")

    with col_sens2:
        r_vals = np.linspace(0.2, 2.5, 100)
        trc_ratios = 0.5 * (r_vals + (1.0 / r_vals))
        
        fig_sens = go.Figure()
        fig_sens.add_trace(go.Scatter(x=r_vals * 100, y=trc_ratios * 100, mode='lines', name='Curva de Sensibilidad MIT', line=dict(color='#8B5CF6', width=2.5)))
        fig_sens.add_trace(go.Scatter(x=[ratio_q * 100], y=[trc_ratio * 100], mode='markers', marker=dict(size=10, color='#EF4444'), name='Punto Seleccionado'))
        fig_sens.update_layout(
            title="Sensibilidad del TRC vs Desviación del Tamaño de Lote (Q / Q*)",
            xaxis_title="Porcentaje del Lote Óptimo (Q / Q* %)",
            yaxis_title="Porcentaje del TRC Óptimo (TRC / TRC* %)",
            template="plotly_white",
            height=320,
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig_sens, use_container_width=True)