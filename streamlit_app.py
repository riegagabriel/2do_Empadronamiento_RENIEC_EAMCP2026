# streamlit_app.py (archivo completo)
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
def load_excel(path: str, sheet_name=0):
    """
    Lee un Excel de forma robusta.
    - sheet_name por defecto es 0 (primera hoja).
    - Si ocurre un error devuelve DataFrame vacío.
    """
    try:
        # Forzamos sheet_name por defecto a 0 para evitar que read_excel devuelva dict()
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        st.warning(f"Advertencia al leer {path} (sheet={sheet_name}): {e}")
        return pd.DataFrame()

# ========================
# Cargar DataFrames principales
# ========================
value_box = load_excel("data/value_box.xlsx")
data_graf = load_excel("data/data_graf.xlsx")
tabla_desagregada_mcp_merged = load_excel("data/tabla_desagregada_mcp_merged.xlsx")

# ================================
# CARGA AUTOMÁTICA DE MCPs (busca files que empiecen con data_monitoreo_)
# ================================
@st.cache_data
def load_mcp_details_from_data_folder():
    base_path = "data"
    try:
        files = os.listdir(base_path)
    except Exception as e:
        st.error(f"No se pudo listar la carpeta data/: {e}")
        return {}

    mcp_dict = {}

    for f in files:
        low = f.lower()
        if low.startswith("data_monitoreo_") and (low.endswith(".xlsx") or low.endswith(".xls")):
            path = os.path.join(base_path, f)

            # Intentar leer la primera hoja (como DataFrame). load_excel devuelve DataFrame o DataFrame vacío.
            df = load_excel(path, sheet_name=0)

            # Si por alguna razón load_excel devolviera dict (no debería), intentar coger la primera hoja.
            if isinstance(df, dict):
                # tomar la primera hoja del dict
                try:
                    first_sheet = list(df.keys())[0]
                    df = df[first_sheet]
                except Exception:
                    df = pd.DataFrame()

            # Nombre legible de la MCP: quitar prefijo y extensión, reemplazar guiones/underscores por espacios
            name = f[len("data_monitoreo_"):]
            # remover extensión
            if name.lower().endswith(".xlsx"):
                name = name[:-5]
            elif name.lower().endswith(".xls"):
                name = name[:-4]
            # formatear nombre: cambiar underscores por espacios y mayúsculas
            mcp_name = name.replace("_", " ").strip().upper()

            # Si df no es DataFrame, lo avisamos y añadimos vacío
            if not isinstance(df, pd.DataFrame):
                st.warning(f"El archivo {f} no se pudo leer como tabla. Se añade vacío para {mcp_name}.")
                mcp_dict[mcp_name] = pd.DataFrame(columns=["empadronador", "total_registros"])
                continue

            # Normalizar columnas para reconocimiento (pero no forzamos renombrar en el DF original salvo para uso interno)
            cols_lower = [str(c).lower().strip() for c in df.columns]

            # Caso 1: archivo ya viene agregado: 'empadronador' y 'total_registros'
            if ("empadronador" in cols_lower) and ("total_registros" in cols_lower):
                # Hacemos copia y uniformizamos nombres a minúsculas
                df2 = df.copy()
                df2.columns = [str(c).lower().strip() for c in df2.columns]
                # Asegurar los tipos
                try:
                    df2["total_registros"] = pd.to_numeric(df2["total_registros"], errors="coerce").fillna(0).astype(int)
                except Exception:
                    pass
                mcp_dict[mcp_name] = df2[["empadronador", "total_registros"]]
                continue

            # Caso 2: archivo crudo con registros individuales: buscar columna dni + empadronador para agrupar
            possible_dni_cols = [c for c in df.columns if "dni" in str(c).lower() or "doc" in str(c).lower() or "num_doc" in str(c).lower()]
            possible_emp_cols = [c for c in df.columns if "empadronador" in str(c).lower() or "usuario" in str(c).lower() or "registrador" in str(c).lower() or "nom" in str(c).lower()]

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
                    # Normalizar columnas
                    conteo.columns = [c.lower().strip() for c in conteo.columns]
                    mcp_dict[mcp_name] = conteo[["empadronador", "total_registros"]]
                    continue
                except Exception as e:
                    st.warning(f"No se pudo agregar/contar para {f}: {e}")

            # Si llegamos aquí no pudimos procesar el archivo: lo guardamos pero vacío para avisar luego
            st.warning(f"El archivo {f} no tiene las columnas esperadas (empadronador/total_registros o empadronador + dni).")
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

    # Prevenir error si value_box vacío
    if not value_box.empty and ("Variable" in value_box.columns) and ("Valor" in value_box.columns):
        indicadores = dict(zip(value_box["Variable"], value_box["Valor"]))
    else:
        indicadores = {}

    # Extraer valores con fallback
    dnis_reg = indicadores.get("dnis_registrados", 0)
    deps = indicadores.get("departamentos", 0)
    mcps = indicadores.get("MCPs", 0)
    ccpp = indicadores.get("CCPPs", 0)
    fechas = indicadores.get("fecha_registro", 0)

    # Value Boxes (Métricas)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🆔 DNIs Registrados", f"{int(dnis_reg):,}" if pd.notna(dnis_reg) else "0")
    col2.metric("🗺️ Departamentos", deps)
    col3.metric("🏛️ MCPs", mcps)
    col4.metric("📍 Centros Poblados", ccpp)
    col5.metric("🗓️ Fechas de trabajo", fechas)

    st.markdown("---")

    # GRÁFICO — Avance por fecha y MCP
    if not data_graf.empty:
        try:
            # intentar parseo con formato dado; si falla, dejar tal cual
            data_graf = data_graf.copy()
            if "date" in data_graf.columns:
                try:
                    data_graf['date'] = pd.to_datetime(data_graf['date'], format='%d%b%Y')
                except Exception:
                    data_graf['date'] = pd.to_datetime(data_graf['date'], errors='coerce')

            # Agregado por MCP (necesita columna dni_ciu en raw)
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
                    marker=dict(size=8),
                    hovertemplate='<b>TOTAL GENERAL</b><br>Fecha: %{x}<br>Registros: %{y}<extra></extra>'
                ))

                for mcp in data_agregado['mcp'].unique():
                    df_mcp_line = data_agregado[data_agregado['mcp'] == mcp]
                    fig.add_trace(go.Scatter(
                        x=df_mcp_line['date'],
                        y=df_mcp_line['count'],
                        mode='lines+markers',
                        name=mcp,
                        line=dict(width=1.5),
                        marker=dict(size=5),
                        visible='legendonly',
                        hovertemplate=f'<b>{mcp}</b><br>Fecha: %{{x}}<br>Registros: %{{y}}<extra></extra>'
                    ))

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
                st.info("`data_graf.xlsx` no contiene las columnas necesarias ('date','mcp','dni_ciu') para mostrar el gráfico temporal.")
        except Exception as e:
            st.error(f"Error al procesar data_graf: {e}")
    else:
        st.warning("No se pudo cargar `data_graf.xlsx`. No se muestra el gráfico.")

    st.markdown("---")

    # Tabla de Avance por MCP (si existe)
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

            # ORDENAR DE MAYOR A MENOR POR DNIs REGISTRADOS
            tabla_mostrar = tabla_mostrar.sort_values(
                by="Cantidad de DNIs Registrados",
                ascending=False
            )

            tabla_mostrar = tabla_mostrar.reset_index(drop=True)
            tabla_mostrar.index = tabla_mostrar.index + 1
            tabla_mostrar.index.name = "N°"

            columnas_mostrar = [
                "Departamento",
                "Provincia",
                "Municipalidad de Centro Poblado",
                "Población Electoral Estimada",
                "Cantidad de DNIs Registrados",
                "% Avance",
                "Monitor"
            ]

            st.dataframe(
                tabla_mostrar[columnas_mostrar],
                use_container_width=True,
                height=600
            )

        except Exception as e:
            st.error(f"Error mostrando tabla_desagregada_mcp_merged: {e}")
    else:
        st.warning("No se pudo cargar `tabla_desagregada_mcp_merged.xlsx`. No se muestra la tabla.")


# ===========================================
# 📍 TAB 2: DETALLE POR MCP (Por empadronador)
# ===========================================
with tab2:
    st.subheader("Detalle por MCP")

    if not mcp_details:
        st.warning("No se encontraron archivos de monitoreo (data_monitoreo_*) en la carpeta data/.")
    else:
        # Ordenar lista de MCPs para el selector
        lista_mcps = sorted(list(mcp_details.keys()))
        mcp_seleccionado = st.selectbox("Selecciona un MCP:", options=lista_mcps)

        # Obtener df
        df_mcp = mcp_details.get(mcp_seleccionado, pd.DataFrame())

        if df_mcp.empty:
            st.warning(f"No hay datos procesables para {mcp_seleccionado}.")
        else:
            # Aseguramos nombres en minúsculas (nuestro contrato interno)
            df_mcp = df_mcp.copy()
            df_mcp.columns = [c.lower().strip() for c in df_mcp.columns]

            # Si existe total_registros ya lo usamos; si no, intentar agrupar por empadronador + dni
            if ("empadronador" in df_mcp.columns) and ("total_registros" in df_mcp.columns):
                conteo = df_mcp.sort_values("total_registros", ascending=True)
            else:
                # intentar agrupar por empadronador identificando columna de dni si existe
                possible_dni = [c for c in df_mcp.columns if "dni" in c or "doc" in c or "num_doc" in c]
                possible_emp = [c for c in df_mcp.columns if "empadronador" in c or "usuario" in c or "registrador" in c or "nom" in c]

                if possible_emp and possible_dni:
                    emp_col = possible_emp[0]
                    dni_col = possible_dni[0]
                    conteo = (
                        df_mcp.groupby(emp_col)[dni_col]
                        .count()
                        .reset_index(name="total_registros")
                        .rename(columns={emp_col: "empadronador"})
                        .sort_values("total_registros", ascending=True)
                    )
                else:
                    st.error("El archivo no tiene columnas identificables para empadronador y/o DNI. "
                             "Asegura que la hoja tenga 'empadronador' y 'total_registros' o columnas con 'dni' y 'empadronador'.")
                    conteo = pd.DataFrame(columns=["empadronador", "total_registros"])

            if conteo.empty:
                st.warning("No hay registros para mostrar.")
            else:
                st.markdown(f"### 🧑‍💼 Registros por empadronador — {mcp_seleccionado}")

                # Gráfico horizontal
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
                    template="plotly_white",
                    margin=dict(l=200)  # espacio para nombres largos de empadronadores
                )

                st.plotly_chart(fig, use_container_width=True)

                # Tabla resumen (ordenada desc)
                st.markdown("### 📋 Tabla de conteo general")
                st.dataframe(conteo.sort_values("total_registros", ascending=False), use_container_width=True)


                # ===========================================
                # 🔥 HEATMAP DE AVANCE DIARIO POR EMPADRONADOR
                # ===========================================
                st.markdown("---")
                st.markdown("## 🔥 Avance diario por empadronador")

                # Nombre estandarizado para buscar el archivo
                nombre_archivo = mcp_seleccionado.lower().replace(" ", "_")
                path_excel = f"data/{nombre_archivo}.xlsx"

                if os.path.exists(path_excel):

                    try:
                        # Leer las dos hojas esperadas: 'crosstab' y 'annot'
                        diario_df = load_excel(path_excel, sheet_name="crosstab")
                        annot_df = load_excel(path_excel, sheet_name="annot")

                        # Si load_excel devolviera dict por alguna razón, extraer primera hoja:
                        if isinstance(diario_df, dict):
                            diario_df = diario_df[list(diario_df.keys())[0]]
                        if isinstance(annot_df, dict):
                            annot_df = annot_df[list(annot_df.keys())[0]]

                        if not diario_df.empty and not annot_df.empty:

                            diario_sorted = diario_df.copy()
                            annot_sorted = annot_df.copy()

                            # --- FIX: asegurar índice con nombres ---
                            # Si la primera columna contiene los nombres de empadronadores (cuando excel guardó el índice como columna)
                            first_col = str(diario_sorted.columns[0]).lower() if len(diario_sorted.columns) > 0 else ""
                            if first_col in ["empadronador", "empadronadores", "nombre", "nombres"]:
                                # establecer esa columna como índice
                                diario_sorted = diario_sorted.set_index(diario_sorted.columns[0])
                                annot_sorted = annot_sorted.set_index(annot_sorted.columns[0])

                            # Convertir columnas a fecha y limpiar columnas malas
                            diario_sorted.columns = pd.to_datetime(diario_sorted.columns, errors="coerce")
                            annot_sorted.columns = pd.to_datetime(annot_sorted.columns, errors="coerce")

                            diario_sorted = diario_sorted.dropna(axis=1, how="all")
                            annot_sorted = annot_sorted.dropna(axis=1, how="all")

                            # Ordenar columnas (fechas)
                            diario_sorted = diario_sorted.sort_index(axis=1)
                            annot_sorted = annot_sorted.sort_index(axis=1)

                            # Verificar que tengamos índices con nombres (empadronadores)
                            if diario_sorted.index.is_integer() or diario_sorted.index.name is None and all(isinstance(i, (int, float)) for i in diario_sorted.index):
                                # índice numérico: los nombres no se leyeron correctamente
                                st.warning("Atención: el crosstab no tiene un índice de empadronadores. Verifica que la hoja 'crosstab' tenga los nombres como índice o como primera columna llamada 'empadronador'.")
                            # Formato de fecha bonito para etiquetas x
                            x_labels = diario_sorted.columns.strftime('%d/%m/%Y')

                            # Construir HEATMAP
                            fig_hm = go.Figure(data=go.Heatmap(
                                z=diario_sorted.values,
                                x=x_labels,
                                y=diario_sorted.index.astype(str),
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
                                margin=dict(l=160, r=20)
                            )

                            # Asegurar que Plotly muestre los nombres y margenes
                            fig_hm.update_yaxes(automargin=True)

                            st.plotly_chart(fig_hm, use_container_width=True)

                        else:
                            st.warning("Las hojas 'crosstab' o 'annot' están vacías. No se puede generar el heatmap.")

                    except Exception as e:
                        st.error(f"Error procesando heatmap para {mcp_seleccionado}: {e}")

                else:
                    st.info(f"No se encontró el archivo '{nombre_archivo}.xlsx' en la carpeta data/.")


# ===========================================
# 🗺️ TAB 3: MAPA DE EMPADRONAMIENTO (ZIP)
# ===========================================
with tab3:
    st.subheader("🗺️ Mapa de Empadronamiento")

    st.markdown(
        "📝 **Leyenda:**\n"
        "- 🔴 Rojo: Puntos donde se registraron formularios virtuales\n"
    )

    # Ruta al ZIP
    zip_path = "data/mapa_empadronamiento.zip"

    if os.path.exists(zip_path):

        import zipfile

        try:
            # Abrir ZIP y leer el HTML internamente
            with zipfile.ZipFile(zip_path, "r") as z:
                with z.open("mapa_empadronamiento.html") as f:
                    html_content = f.read().decode("utf-8")

            # Mostrar el mapa en Streamlit
            components.html(html_content, height=800, scrolling=True)

        except Exception as e:
            st.error(f"Error leyendo el archivo ZIP: {e}")

    else:
        st.error(f"No se encontró '{zip_path}'. Súbelo a la carpeta data/.")

