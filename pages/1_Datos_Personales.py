import streamlit as st # Asegúrate de que esta línea (o similar) ya esté

# --- GUARDIA DE AUTENTICACIÓN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Por favor, inicia sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DE LA GUARDIA ---

# ... (El resto del código de tu página va aquí abajo) ...

import streamlit as st
import google_connector as gc # Importamos nuestro conector
import pandas as pd

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestión de Personal",
    page_icon="👤",
    layout="wide"
)

# Título de la página
st.title("Opción 1: Gestión de Datos Personales")
st.write("Aquí puedes ver, editar, agregar y eliminar empleados. Los cambios se guardan en Google Sheets.")

# --- 2. CARGAR DATOS ---
# Usamos un caché para no recargar de Google en cada click
@st.cache_data(ttl=60) # Cache de 1 minuto
def load_data():
    """Carga los datos del personal desde Google Sheets."""
    try:
        df = gc.get_data("rendimiento", "personal")
        if df.empty:
            st.warning("No se encontraron datos. La hoja 'Informacion' puede estar vacía.")
        
        # Asegurarnos que Cédula sea string para evitar problemas de formato
        if 'Cédula' in df.columns:
            df['Cédula'] = df['Cédula'].astype(str)
            
        return df
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame()

df_personal = load_data()

if df_personal.empty:
    st.error("No se pudieron cargar los datos. Revisa la conexión o la hoja de cálculo.")
    st.stop() # Detiene la ejecución si no hay datos

# --- 3. EDITOR INTERACTIVO ---
st.subheader("Editor de Empleados")
st.info("""
- **Editar:** Haz doble clic en una celda para editarla.
- **Agregar:** Baja hasta el final de la tabla y usa la fila vacía.
- **Eliminar:** Haz clic en la casilla a la izquierda de la fila y presiona la tecla 'Supr' (Delete).
- **Buscar/Filtrar:** Haz clic en el ícono de 🔍 (lupa) en la esquina superior derecha de la tabla.
""")

# st.data_editor es la herramienta clave aquí.
# Le pasamos el DataFrame y nos devuelve una versión editada.
edited_df = st.data_editor(
    df_personal,
    num_rows="dynamic", # Permite agregar y eliminar filas
    use_container_width=True,
    # Configuración de columnas para un mejor UI
    column_config={
        "Cédula": st.column_config.TextColumn("Cédula (ID Único)", width="medium", required=True),
        "Nombre del tecnico": st.column_config.TextColumn("Nombre del Técnico", width="large"),
        "Numero de contacto": st.column_config.TextColumn("Número de Contacto", width="medium"),
        "Empresa": st.column_config.TextColumn("Empresa", width="medium"),
        "Cargo": st.column_config.TextColumn("Cargo", width="medium"),
        "Ubicacion": st.column_config.TextColumn("Ubicación", width="medium"),
    }
)

st.divider()

# --- 4. LÓGICA DE GUARDADO ---
if st.button("Guardar Cambios en Google Sheets"):
    # Comparamos el DF original (del caché) con el DF editado
    if not df_personal.equals(edited_df):
        with st.spinner("Guardando cambios..."):
            try:
                # Llamamos a nuestra función del conector para ACTUALIZAR la hoja
                gc.update_dataframe_in_sheet("rendimiento", "personal", edited_df)
                st.success("¡Cambios guardados con éxito en Google Sheets!")
                
                # Limpiamos los cachés para forzar la re-lectura
                st.cache_data.clear()
            
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    else:
        st.info("No se detectaron cambios para guardar.")