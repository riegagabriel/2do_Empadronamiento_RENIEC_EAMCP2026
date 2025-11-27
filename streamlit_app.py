import streamlit as st
import pandas as pd

# ========================
# CONFIGURACIÓN GENERAL
# ========================
st.set_page_config(
    page_title="Dashboard RENIEC – Empadronamiento",
    layout="wide"
)

st.title("📊 2do Empadronamiento")
st.markdown("Monitoreo de avance de los Municipios de Centros Poblados (MCP)")

# ========================
# Cargar DataFrames
# ========================
@st.cache_data
def load_value_box():
    try:
        df = pd.read_excel("data/value_box.xlsx")
        df.columns = df.columns.str.strip()  # Limpia espacios accidentales
        return df
    except Exception as e:
        st.error(f"Error cargando value_box.xlsx: {e}")
        return pd.DataFrame({"Variable": [], "Valor": []})

value_box = load_value_box()

# ========================
# PESTAÑAS
# ========================
tab1, tab2, tab3 = st.tabs([
    "📈 Progreso General",
    "📍 Detalle por MCP",
    "📋 Otros indicadores"
])

# ===========================================
# 📈 TAB 1: PROGRESO GENERAL
# ===========================================
with tab1:

    st.subheader("Indicadores Generales")

    # Convertir df a diccionario
    indicadores = dict(zip(value_box["Variable"], value_box["Valor"]))

    # Extraer valores seguros
    dnis_reg = indicadores.get("dnis_registrados", 0)
    deps = indicadores.get("departamentos", 0)
    mcps = indicadores.get("MCPs", 0)
    ccpp = indicadores.get("CCPPs", 0)
    fechas = indicadores.get("fecha_registro", 0)

    # ========================
    # Value Boxes (Métricas)
    # ========================
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("🆔 DNIs Registrados", f"{dnis_reg:,}")
    col2.metric("🗺️ Departamentos", deps)
    col3.metric("🏛️ MCPs", mcps)
    col4.metric("📍 Centros Poblados", ccpp)
    col5.metric("🗓️ Fechas de trabajo", fechas)

    st.markdown("---")
    st.markdown("### Nota")
    st.write("Los indicadores se actualizan automáticamente desde `data/value_box.xlsx`.")

# ===========================================
# 📍 TAB 2: DETALLE MCP (placeholder)
# ===========================================
with tab2:
    st.info("Próximamente: detalle por Municipio de Centro Poblado.")

# ===========================================
# 📋 TAB 3: OTROS INDICADORES (placeholder)
# ===========================================
with tab3:
    st.info("Próximamente: indicadores adicionales.")
