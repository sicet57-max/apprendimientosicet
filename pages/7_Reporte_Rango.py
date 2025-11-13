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
import plotly.express as px # <-- ¡¡AQUÍ ESTÁ LA LÍNEA QUE FALTABA!!

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
st.write("Selecciona un rango de fechas para calcular el rendimiento promedio de los técnicos.")

# --- 2. CARGAR DATOS ---
@st.cache_data(ttl=60) 
def load_calculos_data():
    """Carga solo los datos de cálculos y los limpia."""
    try:
        df_calculos = gc.get_data("calculo", "calculos")
        
        if df_calculos.empty:
            return pd.DataFrame()
        
        df_calculos.columns = df_calculos.columns.astype(str).str.strip().str.lower()
        
        df_calculos['fecha'] = pd.to_datetime(df_calculos['fecha'], errors='coerce')
        df_calculos = df_calculos.dropna(subset=['fecha'])
        
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

# --- 3. FILTRO DE RANGO DE FECHAS ---
st.subheader("Paso 1: Selecciona el rango de fechas")

min_date = df_calculos['fecha'].min().date()
max_date = df_calculos['fecha'].max().date()

rango_fechas = st.date_input(
    "Selecciona el rango (Desde - Hasta):",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="date_range_selector"
)

if len(rango_fechas) != 2:
    st.warning("Por favor, selecciona una fecha de inicio y una de fin.")
    st.stop()

start_date, end_date = rango_fechas

# --- 4. APLICAR FILTRO ---
df_filtrado = df_calculos[
    (df_calculos['fecha'].dt.date >= start_date) & 
    (df_calculos['fecha'].dt.date <= end_date)
]

if df_filtrado.empty:
    st.warning(f"No se encontraron registros de rendimiento entre {start_date} y {end_date}.")
    st.stop()

# --- 5. CALCULAR REPORTE (Rendimiento Promedio) ---
st.divider()
st.subheader(f"Rendimiento Promedio (Desde {start_date} hasta {end_date})")

col_nombre_hist = 'nombre del técnico'

df_reporte = df_filtrado.groupby(col_nombre_hist)['porcentaje_num'].mean().reset_index()
df_reporte = df_reporte.rename(columns={'porcentaje_num': 'Rendimiento Promedio (%)'})
df_reporte['Rendimiento Promedio (%)'] = df_reporte['Rendimiento Promedio (%)'].round(2)
df_reporte = df_reporte.sort_values(by='Rendimiento Promedio (%)', ascending=False)

# --- 6. MOSTRAR GRÁFICA Y TABLAS ---

# Gráfica de Barras
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

# Tabla Resumen (El promedio)
st.subheader("Tabla de Promedios")
st.dataframe(df_reporte, use_container_width=True)

if st.button("Guardar este Reporte en Google Sheets", type="primary"):
    with st.spinner("Guardando reporte en 'Reportes Personalizados'..."):
        try:
            df_to_save = df_reporte.copy()
            
            gc.update_dataframe_in_sheet(
                sheet_key="calculo",
                data_key="reportes_rango", 
                df=df_to_save
            )
            st.success("¡Reporte guardado con éxito en la pestaña 'Reportes Personalizados'!")
        except Exception as e:
            st.error(f"Error al guardar el reporte: {e}")

# Tabla Detallada (Los datos usados para el cálculo)
st.divider()
st.subheader("Registros Detallados (Usados para el cálculo)")
columnas_limpias = [
    'fecha', 'mes', 'dia', col_nombre_hist, 'cédula', 
    'empresa', 'porcentaje_rendimiento', 'comentario', 'fecha_creacion'
]
columnas_a_mostrar = [col for col in columnas_limpias if col in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_a_mostrar])