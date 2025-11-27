import streamlit as st
import pandas as pd

# ========================
# Cargar DataFrames
# ========================
value_box = pd.read_excel("data/value_box.xlsx")  


# ========================
# CONFIGURACIÓN GENERAL
# ========================
st.set_page_config(
    page_title="Dashboard RENIEC – Empadronamiento",
    layout="wide"
)

st.title("📊 Dashboard RENIEC – Progreso General del Empadronamiento")
st.markdown("Monitoreo de avance de los Municipios de Centros Poblados (MCP)")

# ========================
# Primera pestaña
# ========================
tab1, tab2, tab3 = st.tabs(["📈 Progreso General", "📍 Detalle por MCP", "📋 Otros indicadores"])

with tab1:

    st.subheader("Indicadores Generales")

    # Convertimos el df a un diccionario clave->valor
    indicadores = dict(zip(value_box["Variable"], value_box["Valor"]))

    # Extraemos uno por uno
    dnis_reg = indicadores.get("dnis_registrados", 0)
    deps = indicadores.get("departamentos", 0)
    mcps = indicadores.get("MCPs", 0)
    ccpp = indicadores.get("CCPPs", 0)
    fechas = indicadores.get("fecha_registro", 0)

    # ========================
    # Value Boxes (Métricas)
    # ========================
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="🆔 DNIs Registrados",
            value=f"{dnis_reg:,}"
        )

    with col2:
        st.metric(
            label="🗺️ Departamentos",
            value=deps
        )

    with col3:
        st.metric(
            label="🏛️ Municipios de Centros Poblados (MCP)",
            value=mcps
        )

    with col4:
        st.metric(
            label="📍 Centros Poblados (CCPP)",
            value=ccpp
        )

    with col5:
        st.metric(
            label="🗓️ Fechas con registro",
            value=fechas
        )

    st.markdown("---")
    st.markdown("### Nota")
    st.write("Los indicadores se actualizan automáticamente a partir del dataframe `value_box`.")

