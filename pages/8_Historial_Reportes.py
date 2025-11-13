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

# --- GUARDIA DE AUTENTICACIÓN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Por favor, inicia sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DE LA GUARDIA ---

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Historial de Reportes",
    page_icon="📚",
    layout="wide"
)

st.title("Opción 8: Historial de Reportes Guardados")
st.write("Aquí puedes ver y eliminar todos los reportes por rango que has guardado.")

# --- 2. CARGAR DATOS DEL HISTORIAL ---
@st.cache_data(ttl=60)
def load_history_data():
    """Carga los reportes ya guardados."""
    try:
        # Usamos 'reportes_rango' que es el data_key para "Reportes Personalizados"
        df_history = gc.get_data("calculo", "reportes_rango")
        if not df_history.empty:
            df_history.columns = df_history.columns.astype(str).str.strip().str.lower()
            df_history = df_history.reset_index(drop=True) 
        return df_history
    except Exception as e:
        st.error(f"Error al cargar el historial de reportes: {e}")
        return pd.DataFrame()

df_historial = load_history_data()

# --- 3. MOSTRAR HISTORIAL Y FILTROS (¡¡CORREGIDO!!) ---
# --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
# Revisamos si el historial está vacío. Si lo está, mostramos un mensaje.
# Si NO lo está, mostramos toda la lógica de filtros y borrado.
if df_historial.empty:
    st.info("Aún no se ha guardado ningún reporte personalizado.")
else:
    # Definimos los nombres de columna (en minúsculas, como se cargan)
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

    st.dataframe(df_historial_filtrado, use_container_width=True)
    
    # --- Lógica de Eliminación ---
    st.divider()
    st.subheader("Eliminar Registros del Historial")
    st.warning("Advertencia: Esta acción es permanente.")
    
    # Creamos un ID único usando el índice
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