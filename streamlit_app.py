import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error cargando value_box.xlsx: {e}")
        return pd.DataFrame({"Variable": [], "Valor": []})

@st.cache_data
def load_data_graf():
    try:
        df = pd.read_excel("data/data_graf.xlsx")
        return df
    except Exception as e:
        st.error(f"Error cargando data_graf.xlsx: {e}")
        return pd.DataFrame()

@st.cache_data
def load_tabla_desagregada_mcp_merged():
    try:
        df = pd.read_excel("data/tabla_desagregada_mcp_merged.xlsx")
        return df
    except Exception as e:
        st.error(f"Error cargando tabla_desagregada_mcp_merged.xlsx: {e}")
        return pd.DataFrame()

value_box = load_value_box()
data_graf = load_data_graf()
tabla_desagregada_mcp_merged = load_tabla_desagregada_mcp_merged()

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

    st.subheader("Indicadores")

    # Convertir df a diccionario
    indicadores = dict(zip(value_box["Variable"], value_box["Valor"]))

    # Extraer valores
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

    # ========================
    # 📊 GRÁFICO — Avance por fecha y MCP
    # ========================

    if not data_graf.empty:

        # Convertir fecha
        data_graf['date'] = pd.to_datetime(data_graf['date'], format='%d%b%Y')

        # Agregado por MCP
        data_agregado = (
            data_graf.groupby(['date', 'mcp'])['dni_ciu']
            .count()
            .reset_index()
            .rename(columns={'dni_ciu': 'count'})
        ).sort_values('date')

        # Total general
        data_total = (
            data_agregado.groupby('date')['count']
            .sum()
            .reset_index()
            .rename(columns={'count': 'total_count'})
        )

        # Crear gráfico
        fig = go.Figure()

        # Línea total
        fig.add_trace(go.Scatter(
            x=data_total['date'],
            y=data_total['total_count'],
            mode='lines+markers',
            name='TOTAL GENERAL',
            line=dict(color='red', width=3),
            marker=dict(size=8),
            hovertemplate='<b>TOTAL GENERAL</b><br>Fecha: %{x}<br>Registros: %{y}<extra></extra>'
        ))

        # Líneas por MCP
        for mcp in data_agregado['mcp'].unique():
            df_mcp = data_agregado[data_agregado['mcp'] == mcp]
            fig.add_trace(go.Scatter(
                x=df_mcp['date'],
                y=df_mcp['count'],
                mode='lines+markers',
                name=mcp,
                line=dict(width=1.5),
                marker=dict(size=5),
                visible='legendonly',
                hovertemplate=f'<b>{mcp}</b><br>Fecha: %{{x}}<br>Registros: %{{y}}<extra></extra>'
            ))

        # Layout
        fig.update_layout(
            title='📈 Avance de Registros por MCP y Fecha',
            xaxis_title='Fecha',
            yaxis_title='Cantidad de Registros (DNI)',
            hovermode='x unified',
            legend=dict(
                title='MCPs (clic para mostrar/ocultar)',
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.01
            ),
            height=600,
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No se pudo cargar `data_graf.xlsx`. No se muestra el gráfico.")

        st.markdown("---")
    st.subheader("📋 Avance por Departamento, Provincia y MCP (Tabla Completa)")

    if not tabla_desagregada_mcp_merged.empty:

        # Ordenar tabla
        tabla_ordenada = tabla_desagregada_mcp_merged.sort_values(
            by=["departamento", "PROV", "MCP"]
        )

        # Renombrar columnas para mostrar
        tabla_mostrar = tabla_ordenada.rename(columns={
            "departamento": "Departamento",
            "PROV": "Provincia",
            "MCP": "Municipialidad de Centro Poblado",
            "POBLACION_AJUSTADA_FINAL": "Población Electoral Estimada",
            "dni_ciu": "Cantidad de DNIs Registrados",
            "PORC_AVANCE": "% Avance",
        })

        # Mostrar tabla
        st.dataframe(
            tabla_mostrar[
                [
                    "Departamento",
                    "Provincia",
                    "Municipialidad de Centro Poblado",
                    "Población Electoral Estimada",
                    "Cantidad de DNIs Registrados",
                    "% Avance",
                ]
            ],
            use_container_width=True,
            height=600
        )

    else:
        st.warning("No se pudo cargar `tabla_desagregada_mcp_merged.xlsx`. No se muestra la tabla.")



    st.markdown("### Nota")
    st.write("Los indicadores se actualizan automáticamente desde `data/value_box.xlsx`.")

# ===========================================
# 📋 TAB 3: OTROS INDICADORES (placeholder)
# ===========================================
with tab3:
    st.info("Próximamente: indicadores adicionales.")

