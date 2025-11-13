import streamlit as st # Asegúrate de que esta línea (o similar) ya esté

# --- GUARDIA DE AUTENTICACIÓN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Por favor, inicia sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DE LA GUARDIA ---

import streamlit as st
import google_connector as gc 
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- GUARDIA DE AUTENTICACIÓN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Por favor, inicia sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DE LA GUARDIA ---

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Reporte por Rango",
    page_icon="📅",
    layout="wide"
)

st.title("Opción 7: Reporte de Rendimiento por Rango")
st.write("Selecciona un rango de fechas y otros filtros para calcular y guardar reportes.")

# --- 2. CARGAR DATOS ---
@st.cache_data(ttl=60) 
def load_calculos_data():
    """Carga solo los datos de cálculos y los limpia."""
    try:
        df_calculos = gc.get_data("calculo", "calculos")
        
        if df_calculos.empty:
            return pd.DataFrame()
        
        df_calculos.columns = df_calculos.columns.astype(str).str.strip().str.lower()
        
        df_calculos['fecha_evaluacion'] = pd.to_datetime(df_calculos['fecha'], errors='coerce')
        df_calculos = df_calculos.dropna(subset=['fecha_evaluacion'])
        
        if 'porcentaje_rendimiento' in df_calculos.columns:
            df_calculos['porcentaje_num'] = pd.to_numeric(
                df_calculos['porcentaje_rendimiento'].astype(str).str.replace('%', '', regex=False), 
                errors='coerce'
            )
            df_calculos = df_calculos.dropna(subset=['porcentaje_num'])
        else:
            st.error("No se encontró 'porcentaje_rendimiento' en la hoja de cálculos.")
            return pd.DataFrame()

        if 'nombre del técnico' in df_calculos.columns:
            df_calculos['nombre del técnico'] = df_calculos['nombre del técnico'].astype(str).str.strip()
        
        return df_calculos
    
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame()

df_calculos = load_calculos_data()

if df_calculos.empty:
    st.info("No hay datos de rendimiento numérico para reportar.")
    st.stop()

# --- 3. FILTROS ---
st.subheader("Paso 1: Selecciona los Filtros")

col_nombre_hist = 'nombre del técnico'
col_cedula_hist = 'cédula'

min_date = df_calculos['fecha_evaluacion'].min().date()
max_date = df_calculos['fecha_evaluacion'].max().date()

rango_fechas = st.date_input(
    "Filtrar por Rango de Fechas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="date_range_selector"
)
if len(rango_fechas) != 2:
    st.warning("Por favor, selecciona una fecha de inicio y una de fin.")
    st.stop()
start_date, end_date = rango_fechas

col1, col2 = st.columns(2)
with col1:
    nombres_sel = st.multiselect(
        "Filtrar por Técnico (Opcional):",
        options=df_calculos[col_nombre_hist].unique()
    )
with col2:
    cedulas_sel = st.multiselect(
        "Filtrar por Cédula (Opcional):",
        options=df_calculos[col_cedula_hist].unique()
    )

# --- 4. APLICAR FILTROS ---
df_filtrado = df_calculos[
    (df_calculos['fecha_evaluacion'].dt.date >= start_date) & 
    (df_calculos['fecha_evaluacion'].dt.date <= end_date)
]
if nombres_sel:
    df_filtrado = df_filtrado[df_filtrado[col_nombre_hist].isin(nombres_sel)]
if cedulas_sel:
    df_filtrado = df_filtrado[df_filtrado[col_cedula_hist].isin(cedulas_sel)]

if df_filtrado.empty:
    st.warning(f"No se encontraron registros que coincidan con todos los filtros seleccionados.")
    st.stop()

# --- 5. CALCULAR REPORTE ---
st.divider()
st.subheader(f"Reporte de Rendimiento (Desde {start_date} hasta {end_date})")

df_reporte = df_filtrado.groupby(col_nombre_hist)['porcentaje_num'].mean().reset_index()
df_reporte = df_reporte.rename(columns={'porcentaje_num': 'Rendimiento Promedio (%)'})
df_reporte['Rendimiento Promedio (%)'] = df_reporte['Rendimiento Promedio (%)'].round(2)
df_reporte = df_reporte.sort_values(by='Rendimiento Promedio (%)', ascending=False)

rango_str = f"{start_date} al {end_date}"
df_reporte["Rango de Fechas"] = rango_str
df_reporte = df_reporte[[ "Rango de Fechas", col_nombre_hist, 'Rendimiento Promedio (%)']]

# --- 6. MOSTRAR GRÁFICA Y TABLAS ---
theme_plotly = "plotly_dark"
bg_transparent = {'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)'}
fig = px.bar(
    df_reporte,
    x=col_nombre_hist, y='Rendimiento Promedio (%)',
    title="Rendimiento Promedio por Técnico en el Rango Seleccionado",
    text='Rendimiento Promedio (%)', template=theme_plotly,
    color='Rendimiento Promedio (%)', color_continuous_scale='RdYlGn'
)
fig.update_traces(textposition='outside')
fig.update_layout(xaxis_title="Técnico", yaxis_title="Promedio (%)", **bg_transparent)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Tabla de Promedios (Resultado del Reporte)")
st.dataframe(df_reporte, use_container_width=True)

# --- ¡¡LÓGICA DE GUARDADO CORREGIDA Y SIMPLIFICADA!! ---
if st.button("Guardar este Reporte en Google Sheets", type="primary"):
    with st.spinner("Guardando reporte en 'Reportes Personalizados'..."):
        try:
            # Ahora simplemente sobrescribe la hoja con el nuevo reporte
            gc.update_dataframe_in_sheet(
                sheet_key="calculo",
                data_key="reportes_rango", 
                df=df_reporte
            )
            st.success("¡Reporte guardado con éxito en la pestaña 'Reportes Personalizados'!")
            st.cache_data.clear() # Limpiamos caché por si acaso
        except Exception as e:
            st.error(f"Error al guardar el reporte: {e}")
            st.exception(e)
# --- FIN DE LA CORRECCIÓN ---

# --- 7. REGISTROS DETALLADOS (SIN CAMBIOS) ---
st.divider()
st.subheader("Registros Detallados (Usados para el cálculo)")
columnas_limpias = [
    'fecha', 'mes', 'dia', col_nombre_hist, 'cédula', 
    'empresa', 'porcentaje_rendimiento', 'comentario', 'fecha_creacion'
]
columnas_a_mostrar = [col for col in columnas_limpias if col in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_a_mostrar])

# --- 8. SECCIÓN DE HISTORIAL ELIMINADA ---
# ... (Todo el código del historial, filtros y borrado ha sido eliminado) ...