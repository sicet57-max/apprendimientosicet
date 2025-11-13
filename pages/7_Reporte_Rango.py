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

# --- NUEVA FUNCIÓN PARA CARGAR EL HISTORIAL DE REPORTES ---
@st.cache_data(ttl=60)
def load_history_data():
    """Carga los reportes ya guardados."""
    try:
        df_history = gc.get_data("calculo", "reportes_rango")
        if not df_history.empty:
            df_history.columns = df_history.columns.astype(str).str.strip().str.lower()
            df_history = df_history.reset_index(drop=True) 
        return df_history
    except Exception as e:
        st.error(f"Error al cargar el historial de reportes: {e}")
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

if st.button("Guardar este Reporte en Google Sheets", type="primary"):
    with st.spinner("Añadiendo reporte al historial en 'Reportes Personalizados'..."):
        try:
            # 1. Obtenemos el historial existente (columnas en minúsculas)
            df_historial_existente = load_history_data()
            
            # 2. Preparamos el nuevo reporte
            df_reporte_limpio = df_reporte.copy()
            # --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
            # Convertimos las columnas a minúsculas para que coincidan
            df_reporte_limpio.columns = df_reporte_limpio.columns.astype(str).str.strip().str.lower()
            
            # 3. Combinamos (ahora las columnas coinciden)
            df_para_guardar = pd.concat([df_historial_existente, df_reporte_limpio], ignore_index=True)
            
            gc.update_dataframe_in_sheet(
                sheet_key="calculo",
                data_key="reportes_rango", 
                df=df_para_guardar
            )
            st.success("¡Reporte guardado con éxito en la pestaña 'Reportes Personalizados'!")
            st.cache_data.clear() 
            st.rerun() 
        except Exception as e:
            st.error(f"Error al guardar el reporte: {e}")
            st.exception(e) # Muestra el error detallado

# --- 7. REGISTROS DETALLADOS (SIN CAMBIOS) ---
st.divider()
st.subheader("Registros Detallados (Usados para el cálculo)")
columnas_limpias = [
    'fecha', 'mes', 'dia', col_nombre_hist, 'cédula', 
    'empresa', 'porcentaje_rendimiento', 'comentario', 'fecha_creacion'
]
columnas_a_mostrar = [col for col in columnas_limpias if col in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_a_mostrar])

# --- 8. HISTORIAL DE REPORTES GUARDADOS ---
st.divider()
st.title("Historial de Reportes Guardados")
st.write("Aquí puedes ver todos los reportes que has guardado en la hoja 'Reportes Personalizados'.")

df_historial = load_history_data()

if df_historial.empty:
    st.info("Aún no se ha guardado ningún reporte personalizado.")
else:
    col_rango = 'rango de fechas'
    col_nombre_reporte = 'nombre del técnico'
    col_promedio = 'rendimiento promedio (%)'
    
    st.subheader("Filtros del Historial de Reportes")
    col1_hist, col2_hist = st.columns(2)
    with col1_hist:
        rangos_sel = st.multiselect(
            "Filtrar por Rango:",
            options=df_historial[col_rango].unique()
        )
    with col2_hist:
        nombres_hist_sel = st.multiselect(
            "Filtrar por Técnico:",
            options=df_historial[col_nombre_reporte].unique()
        )
        
    df_historial_filtrado = df_historial.copy()
    if rangos_sel:
        df_historial_filtrado = df_historial_filtrado[df_historial_filtrado[col_rango].isin(rangos_sel)]
    if nombres_hist_sel:
        df_historial_filtrado = df_historial_filtrado[df_historial_filtrado[col_nombre_reporte].isin(nombres_hist_sel)]

    st.dataframe(df_historial_filtrado)
    
    st.subheader("Eliminar Registros del Historial")
    st.warning("Advertencia: Esta acción es permanente.")
    
    df_historial["id_unico_borrado"] = (
        "Reporte #" + (df_historial.index + 1).astype(str) + " | " +
        df_historial[col_rango] + " | " +
        df_historial[col_nombre_reporte] + " | " +
        df_historial[col_promedio].astype(str) + "%"
    )
    
    opciones_borrado = [""] + list(df_historial["id_unico_borrado"].unique())
    
    ids_a_borrar_sel = st.multiselect(
        "Selecciona los registros de reporte que deseas eliminar:",
        options=opciones_borrado[1:]
    )
    
    if st.button("Confirmar Eliminación", type="primary"):
        if not ids_a_borrar_sel:
            st.error("No has seleccionado ningún registro para eliminar.")
        else:
            with st.spinner("Eliminando reportes..."):
                try:
                    df_sin_borrados = df_historial[
                        ~df_historial["id_unico_borrado"].isin(ids_a_borrar_sel)
                    ]
                    
                    df_final_para_guardar = df_sin_borrados.drop(columns=["id_unico_borrado"])
                    
                    gc.update_dataframe_in_sheet(
                        sheet_key="calculo",
                        data_key="reportes_rango",
                        df=df_final_para_guardar
                    )
                    
                    st.success("¡Reportes eliminados con éxito!")
                    st.cache_data.clear()
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")