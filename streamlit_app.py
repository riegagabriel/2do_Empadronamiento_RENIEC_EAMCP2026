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

@st.cache_data
def load_mcp_details():
    data = {}

    try:
        data["19 DE AGOSTO"] = pd.read_excel("data/data_monitoreo_19_de_agosto.xlsx")
        data["CIUDAD DE DIOS"] = pd.read_excel("data/data_monitoreo_ciudad_de_dios.xlsx")
        data["CRUZ PAMPA YAPATERA"] = pd.read_excel("data/data_monitoreo_cruz_pampa_yapatera.xlsx")
        data["CURVA DE SUN"] = pd.read_excel("data/data_monitoreo_curva_de_sun.xlsx")
        data["HUAMBOCANCHA ALTA"] = pd.read_excel("data/data_monitoreo_huambocancha_alta.xlsx")
        data["HUANCHAQUITO"] = pd.read_excel("data/data_monitoreo_huanchaquito.xlsx")
        data["LA COLORADA"] = pd.read_excel("data/data_monitoreo_la_colorada.xlsx")
        data["LA PEÑITA"] = pd.read_excel("data/data_monitoreo_la_peñita.xlsx")
        data["LA VILLA LETIRA - BECARA"] = pd.read_excel("data/data_monitoreo_la_villa_letira_becara.xlsx")
        data["MALINGAS"] = pd.read_excel("data/data_monitoreo_malingas.xlsx")
        data["OTUZCO"] = pd.read_excel("data/data_monitoreo_otuzco.xlsx")
        data["SAN ANTONIO BAJO"] = pd.read_excel("data/data_monitoreo_san_antonio_bajo.xlsx")
        data["VIVIATE"] = pd.read_excel("data/data_monitoreo_viviate.xlsx")

    except Exception as e:
        st.error(f"Error cargando datos detallados por MCP: {e}")

    return data

value_box = load_value_box()
data_graf = load_data_graf()
tabla_desagregada_mcp_merged = load_tabla_desagregada_mcp_merged()
mcp_details = load_mcp_details()

# ========================
# PESTAÑAS
# ========================
tab1, tab2 = st.tabs([
    "📈 Progreso General",
    "📍 Monitoreo por MCP",
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
st.subheader("📋 Tabla de Avance por MCP")

if not tabla_desagregada_mcp_merged.empty:

    # Ordenar tabla
    tabla_ordenada = tabla_desagregada_mcp_merged.sort_values(
        by=["departamento", "PROV", "MCP"]
    )

    # Renombrar columnas para mostrar
    tabla_mostrar = tabla_ordenada.rename(columns={
        "departamento": "Departamento",
        "PROV": "Provincia",
        "MCP": "Municipalidad de Centro Poblado",
        "POBLACION_AJUSTADA_FINAL": "Población Electoral Estimada",
        "dni_ciu": "Cantidad de DNIs Registrados",
        "PORC_AVANCE": "% Avance",
    })

    # Crear índice desde 1
    tabla_mostrar = tabla_mostrar.reset_index(drop=True)
    tabla_mostrar.index = tabla_mostrar.index + 1
    tabla_mostrar.index.name = "N°"

    # Columnas a mostrar (seguras)
    columnas_mostrar = [
        "Departamento",
        "Provincia",
        "Municipalidad de Centro Poblado",
        "Población Electoral Estimada",
        "Cantidad de DNIs Registrados",
        "% Avance",
    ]

    # Mostrar tabla final
    st.dataframe(
        tabla_mostrar[columnas_mostrar],
        use_container_width=True,
        height=600
    )

else:
    st.warning("No se pudo cargar `tabla_desagregada_mcp_merged.xlsx`. No se muestra la tabla.")
    
# ===========================================
# 📍 TAB 2: DETALLE POR MCP (Por empadronador)
# ===========================================
with tab2:

    st.subheader("Detalle por MCP")

    # Selector de MCP
    mcp_seleccionado = st.selectbox(
        "Selecciona un MCP:",
        options=list(mcp_details.keys())
    )

    df_mcp = mcp_details[mcp_seleccionado]

    if df_mcp.empty:
        st.warning("No hay datos para este MCP.")
    else:
        # =======================================
        # Agrupar: registros por empadronador
        # =======================================
        conteo = (
            df_mcp.groupby("empadronador")["dni_ciu"]
            .count()
            .reset_index(name="total_registros")
            .sort_values("total_registros", ascending=True)
        )

        st.markdown(f"### 🧑‍💼 Registros por empadronador — {mcp_seleccionado}")

        # ============================
        # Grafico de barras horizontal
        # ============================
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=conteo["total_registros"],
            y=conteo["empadronador"],
            orientation="h",
            marker=dict(color="#4A90E2"),
            hovertemplate="<b>%{y}</b><br>Registros: %{x}<extra></extra>"
        ))

        fig.update_layout(
            title=f"Total de registros por empadronador — {mcp_seleccionado}",
            xaxis_title="Total de registros (DNIs)",
            yaxis_title="Empadronador",
            height=600,
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

        # ============================
        # Mostrar tabla ordenada
        # ============================
        st.markdown("### 📋 Tabla resumida")
        st.dataframe(conteo.sort_values("total_registros", ascending=False),
                     use_container_width=True)

