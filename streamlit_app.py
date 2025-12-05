import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import streamlit.components.v1 as components

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
# Helper: cargar excel con manejo de errores
# ========================
@st.cache_data
def load_excel(path: str, sheet_name=None):
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        st.warning(f"Advertencia al leer {path}: {e}")
        return pd.DataFrame()

# ========================
# Cargar DataFrames principales
# ========================
value_box = load_excel("data/value_box.xlsx")
data_graf = load_excel("data/data_graf.xlsx")
tabla_desagregada_mcp_merged = load_excel("data/tabla_desagregada_mcp_merged.xlsx")

# ================================
# CARGA AUTOMÁTICA DE MCPs (data_monitoreo_*)
# ================================
@st.cache_data
def load_mcp_details_from_data_folder():
    base_path = "data"
    files = os.listdir(base_path)
    mcp_dict = {}

    for f in files:
        low = f.lower()
        if low.startswith("data_monitoreo_") and (low.endswith(".xlsx") or low.endswith(".xls")):
            path = os.path.join(base_path, f)
            df = load_excel(path)

            name = f[len("data_monitoreo_"):]
            if name.lower().endswith(".xlsx"):
                name = name[:-5]
            elif name.lower().endswith(".xls"):
                name = name[:-4]

            mcp_name = name.replace("_", " ").strip().upper()

            cols_lower = [c.lower().strip() for c in df.columns]

            # Caso 1: archivo agregado
            if ("empadronador" in cols_lower) and ("total_registros" in cols_lower):
                df2 = df.copy()
                df2.columns = [c.lower().strip() for c in df2.columns]
                try:
                    df2["total_registros"] = pd.to_numeric(df2["total_registros"], errors="coerce").fillna(0).astype(int)
                except:
                    pass

                mcp_dict[mcp_name] = df2[["empadronador", "total_registros"]]
                continue

            # Caso 2: crudo (agrupar)
            possible_dni_cols = [c for c in df.columns if "dni" in c.lower() or "doc" in c.lower()]
            possible_emp_cols = [c for c in df.columns if "empadronador" in c.lower() or "usuario" in c.lower()]

            if possible_dni_cols and possible_emp_cols:
                dni_col = possible_dni_cols[0]
                emp_col = possible_emp_cols[0]

                try:
                    conteo = (
                        df.groupby(emp_col)[dni_col]
                        .count()
                        .reset_index(name="total_registros")
                        .rename(columns={emp_col: "empadronador"})
                        .sort_values("total_registros", ascending=False)
                    )

                    conteo.columns = [c.lower().strip() for c in conteo.columns]

                    mcp_dict[mcp_name] = conteo[["empadronador", "total_registros"]]
                    continue
                except Exception as e:
                    st.warning(f"No se pudo agregar/contar para {f}: {e}")

            st.warning(f"El archivo {f} no tiene columnas esperadas.")
            mcp_dict[mcp_name] = pd.DataFrame(columns=["empadronador", "total_registros"])

    return mcp_dict

mcp_details = load_mcp_details_from_data_folder()

# ========================
# PESTAÑAS
# ========================
tab1, tab2, tab3 = st.tabs([
    "📈 Progreso General",
    "📍 Monitoreo por MCP",
    "🗺️ Mapa de Empadronamiento"
])

# ===========================================
# 📈 TAB 1: PROGRESO GENERAL
# ===========================================
with tab1:
    st.subheader("Indicadores")

    if not value_box.empty and ("Variable" in value_box.columns) and ("Valor" in value_box.columns):
        indicadores = dict(zip(value_box["Variable"], value_box["Valor"]))
    else:
        indicadores = {}

    dnis_reg = indicadores.get("dnis_registrados", 0)
    deps = indicadores.get("departamentos", 0)
    mcps = indicadores.get("MCPs", 0)
    ccpp = indicadores.get("CCPPs", 0)
    fechas = indicadores.get("fecha_registro", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🆔 DNIs Registrados", f"{int(dnis_reg):,}" if pd.notna(dnis_reg) else "0")
    col2.metric("🗺️ Departamentos", deps)
    col3.metric("🏛️ MCPs", mcps)
    col4.metric("📍 Centros Poblados", ccpp)
    col5.metric("🗓️ Fechas de trabajo", fechas)

    st.markdown("---")

    # Gráfico temporal
    if not data_graf.empty:
        try:
            data_graf = data_graf.copy()
            if "date" in data_graf.columns:
                try:
                    data_graf['date'] = pd.to_datetime(data_graf['date'], format='%d%b%Y')
                except:
                    data_graf['date'] = pd.to_datetime(data_graf['date'], errors='coerce')

            if ("mcp" in data_graf.columns) and ("dni_ciu" in data_graf.columns):
                data_agregado = (
                    data_graf.groupby(['date', 'mcp'])['dni_ciu']
                    .count()
                    .reset_index()
                    .rename(columns={'dni_ciu': 'count'})
                ).sort_values('date')

                data_total = (
                    data_agregado.groupby('date')['count']
                    .sum()
                    .reset_index()
                    .rename(columns={'count': 'total_count'})
                )

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=data_total['date'],
                    y=data_total['total_count'],
                    mode='lines+markers',
                    name='TOTAL GENERAL',
                    line=dict(color='red', width=3),
                    marker=dict(size=8)
                ))

                for mcp in data_agregado['mcp'].unique():
                    df_mcp_line = data_agregado[data_agregado['mcp'] == mcp]
                    fig.add_trace(go.Scatter(
                        x=df_mcp_line['date'],
                        y=df_mcp_line['count'],
                        mode='lines+markers',
                        name=mcp,
                        visible='legendonly'
                    ))

                fig.update_layout(
                    title='📈 Avance de Registros por MCP y Fecha',
                    xaxis_title='Fecha',
                    yaxis_title='Cantidad de Registros (DNI)',
                    height=600,
                    template='plotly_white'
                )

                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error al procesar data_graf: {e}")

    st.markdown("---")

    # Tabla MCP
    st.subheader("📋 Tabla de Avance por MCP")

    if not tabla_desagregada_mcp_merged.empty:
        try:
            tabla_ordenada = tabla_desagregada_mcp_merged.sort_values(
                by=["departamento", "PROV", "MCP"]
            )

            tabla_mostrar = tabla_ordenada.rename(columns={
                "departamento": "Departamento",
                "PROV": "Provincia",
                "MCP": "Municipalidad de Centro Poblado",
                "Monitor": "Monitor",
                "POBLACION_AJUSTADA_FINAL": "Población Electoral Estimada",
                "dni_ciu": "Cantidad de DNIs Registrados",
                "PORC_AVANCE": "% Avance",
            })

            tabla_mostrar = tabla_mostrar.sort_values(
                by="Cantidad de DNIs Registrados",
                ascending=False
            )

            tabla_mostrar = tabla_mostrar.reset_index(drop=True)
            tabla_mostrar.index = tabla_mostrar.index + 1
            tabla_mostrar.index.name = "N°"

            st.dataframe(
                tabla_mostrar[
                    [
                        "Departamento",
                        "Provincia",
                        "Municipalidad de Centro Poblado",
                        "Población Electoral Estimada",
                        "Cantidad de DNIs Registrados",
                        "% Avance",
                        "Monitor"
                    ]
                ],
                use_container_width=True,
                height=600
            )
        except Exception as e:
            st.error(f"Error mostrando tabla MCP: {e}")

# ===========================================
# 📍 TAB 2: DETALLE POR MCP (Registros + HEATMAP)
# ===========================================
with tab2:

    st.subheader("Detalle por MCP")

    if not mcp_details:
        st.warning("No se encontraron archivos de monitoreo (data_monitoreo_*) en la carpeta data/.")
    else:
        lista_mcps = sorted(list(mcp_details.keys()))
        mcp_seleccionado = st.selectbox("Selecciona un MCP:", options=lista_mcps)

        # DF por empadronador
        df_mcp = mcp_details.get(mcp_seleccionado, pd.DataFrame())

        if df_mcp.empty:
            st.warning(f"No hay datos procesables para {mcp_seleccionado}.")
        else:
            df_mcp = df_mcp.copy()
            df_mcp.columns = [c.lower().strip() for c in df_mcp.columns]

            if ("empadronador" in df_mcp.columns) and ("total_registros" in df_mcp.columns):
                conteo = df_mcp.sort_values("total_registros", ascending=True)
            else:
                possible_dni = [c for c in df_mcp.columns if "dni" in c]
                possible_emp = [c for c in df_mcp.columns if "empadronador" in c]
                if possible_emp and possible_dni:
                    emp_col = possible_emp[0]
                    dni_col = possible_dni[0]
                    conteo = (
                        df_mcp.groupby(emp_col)[dni_col]
                        .count()
                        .reset_index(name="total_registros")
                        .rename(columns={emp_col: "empadronador"})
                    )
                else:
                    conteo = pd.DataFrame()

            # ------------------------------
            # GRÁFICO DE BARRAS
            # ------------------------------
            if not conteo.empty:
                st.markdown(f"### 🧑‍💼 Registros por empadronador — {mcp_seleccionado}")

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=conteo["total_registros"],
                    y=conteo["empadronador"],
                    orientation="h",
                    marker=dict(color="#4A90E2"),
                ))

                fig.update_layout(
                    title=f"Total de registros por empadronador — {mcp_seleccionado}",
                    xaxis_title="Total de registros (DNIs)",
                    yaxis_title="Empadronador",
                    height=500,
                    margin=dict(l=200)
                )

                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### 📋 Tabla de conteo general")
                st.dataframe(
                    conteo.sort_values("total_registros", ascending=False),
                    use_container_width=True
                )

        # ----------------------------------------------------
        # 🔥 HEATMAP DIARIO — Integrado aquí (NUEVA SECCIÓN)
        # ----------------------------------------------------
        st.markdown("---")
        st.markdown("## 🔥 Avance diario por empadronador")

        nombre_archivo = mcp_seleccionado.lower().replace(" ", "_")
        path_excel = f"data/{nombre_archivo}.xlsx"

        if os.path.exists(path_excel):

            try:
                diario_df = load_excel(path_excel, sheet_name="crosstab")
                annot_df = load_excel(path_excel, sheet_name="annot")

                if not diario_df.empty and not annot_df.empty:

                    diario_sorted = diario_df.copy()
                    annot_sorted = annot_df.copy()

                    diario_sorted.columns = pd.to_datetime(diario_sorted.columns, errors="coerce")
                    annot_sorted.columns = pd.to_datetime(annot_sorted.columns, errors="coerce")

                    diario_sorted = diario_sorted.sort_index(axis=1)
                    annot_sorted = annot_sorted.sort_index(axis=1)

                    x_labels = diario_sorted.columns.strftime('%d/%m/%Y')

                    fig_hm = go.Figure(data=go.Heatmap(
                        z=diario_sorted.values,
                        x=x_labels,
                        y=diario_sorted.index,
                        text=annot_sorted.values,
                        texttemplate="%{text}",
                        colorscale="YlGnBu",
                        zmin=0,
                        zmax=30,
                        colorbar=dict(title="Avances diarios"),
                        hovertemplate=(
                            'Empadronador: %{y}<br>'
                            'Fecha: %{x}<br>'
                            'Avances: %{z}<extra></extra>'
                        )
                    ))

                    fig_hm.update_layout(
                        title=f"📅 Heatmap de avances diarios — {mcp_seleccionado}",
                        xaxis_title="Fecha",
                        yaxis_title="Empadronadores",
                        width=1000,
                        height=600,
                        margin=dict(l=120, r=20)
                    )

                    st.plotly_chart(fig_hm, use_container_width=True)

                else:
                    st.warning("Las hojas 'crosstab' o 'annot' están vacías.")

            except Exception as e:
                st.error(f"Error procesando heatmap para {mcp_seleccionado}: {e}")

        else:
            st.info(f"No se encontró el archivo '{nombre_archivo}.xlsx' en la carpeta data/.")

# ===========================================
# 🗺️ TAB 3: MAPA
# ===========================================
with tab3:
    st.subheader("🗺️ Mapa de Empadronamiento")

    st.markdown(
        "📝 **Leyenda:**\n"
        "- 🔴 Rojo: Puntos donde se registraron formularios virtuales\n"
    )

    mapa_path = "data/mapa_empadronamiento.html"

    if os.path.exists(mapa_path):
        with open(mapa_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        components.html(html_content, height=800, scrolling=True)

    else:
        st.error(f"No se encontró el archivo '{mapa_path}'.")
        st.info("Guárdalo como 'mapa_empadronamiento.html' en la carpeta data/")
