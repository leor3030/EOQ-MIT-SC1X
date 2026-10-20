# 📦 MIT CTL.SC1x: Economic Order Quantity (EOQ) Master Suite

[![Streamlit App](https://static.streamlit.io/badge/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Aplicación interactiva de analítica y optimización de inventarios basada en las metodologías cuantitativas del curso **MIT CTL.SC1x (Supply Chain Fundamentals)** de MIT Center for Transportation & Logistics.

## 🚀 Modelos Implementados
- **EOQ Básico (Instantaneous Replenishment)**: Compensación exacta entre costos fijos de orden y mantenimiento.
- **EOQ con Lead Time / Pipeline Inventory**: Cálculo de inventario en tránsito ($API = D \cdot L$) y punto de reorden en posición de inventario ($IP$).
- **EOQ con Descuento por Volumen (All-Units & Good Deal)**: Análisis de viabilidad y trade-off de breakpoints de compra.
- **EPQ (Economic Production Quantity)**: Tasa de producción finita $P > D$, tiempos de acumulación ($t_p$) y consumo ($t_d$).
- **EOQ con Backorders Planificados**: Optimización de faltantes con Critical Ratio ($CR$), cálculo de faltante óptimo ($b^*$) e inventario neto.

## 📊 Características
- Entradas dinámicas adaptadas según el modelo seleccionado.
- Gráficos interactivos de ciclo diente de sierra ($T$ vs $Q$) y trade-off de costos en Plotly.
- Matriz comparativa multi-modelo con indicadores clave ($Q^*, T^*, N^*, TRC^*, TC^*$).
- Analizador de sensibilidad y robustez del lote óptimo según la formulación del MIT.

## 🛠️ Instalación Local
```bash
git clone [https://github.com/leor3030/EOQ-MIT-SC1X.git](https://github.com/leor3030/EOQ-MIT-SC1X.git)
cd EOQ-MIT-SC1X
pip install -r requirements.txt
streamlit run app.py