# ===========================================
# 🔥 HEATMAP DE AVANCE DIARIO POR EMPADRONADOR
# ===========================================

st.markdown("---")
st.markdown("## 🔥 Avance diario por empadronador")

# Nombre estandarizado para buscar el archivo
nombre_archivo = mcp_seleccionado.lower().replace(" ", "_")

# (Ya no usamos diario_ ni annot_)
path_excel = f"data/{nombre_archivo}.xlsx"

if os.path.exists(path_excel):

    try:
        diario_df = load_excel(path_excel, sheet_name="crosstab")
        annot_df = load_excel(path_excel, sheet_name="annot")

        if not diario_df.empty and not annot_df.empty:

            diario_sorted = diario_df.copy()
            annot_sorted = annot_df.copy()

            # Convertir columnas a fecha
            diario_sorted.columns = pd.to_datetime(diario_sorted.columns, errors="coerce")
            annot_sorted.columns = pd.to_datetime(annot_sorted.columns, errors="coerce")

            # Ordenar columnas (fechas)
            diario_sorted = diario_sorted.sort_index(axis=1)
            annot_sorted = annot_sorted.sort_index(axis=1)

            # Etiquetas bonitas
            x_labels = diario_sorted.columns.strftime('%d/%m/%Y')

            # HEATMAP
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
