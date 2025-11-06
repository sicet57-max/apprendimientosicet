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
import google_connector as gc 
import pandas as pd

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestión de Comentarios",
    page_icon="💬",
    layout="wide"
)

st.title("Opción 2: Comentarios por Empleado")
st.write("Selecciona un empleado y un mes para ver, agregar o modificar un comentario.")

# --- 2. CARGAR DATOS (CON CORRECCIÓN DE STRIP) ---
@st.cache_data(ttl=60) 
def load_data():
    """Carga los datos de comentarios desde Google Sheets."""
    try:
        df = gc.get_data("rendimiento", "comentarios")
        if df.empty:
            st.warning("No se encontraron datos en la hoja 'Comentarios'.")
            return pd.DataFrame() 

        # Limpiamos los espacios en blanco de todos los nombres de columnas
        df.columns = df.columns.str.strip()

        if 'Cédula' in df.columns:
            df['Cédula'] = df['Cédula'].astype(str)
            
        return df
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame()

df_comentarios = load_data()

if df_comentarios.empty:
    st.error("No se pudieron cargar los datos de comentarios. Revisa la conexión o la hoja.")
    st.stop() 

# --- 3. FILTROS DE SELECCIÓN ---
st.subheader("Seleccionar Empleado y Mes")

# --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
# Cambiamos "Nombre del Ventano" por el nombre correcto de tu hoja
COLUMNA_NOMBRE = "Nombre del técnico"
# --- FIN DE LA CORRECCIÓN ---

COLUMNAS_MESES_BUSCAR = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]

# Verificamos que la columna de nombre exista
if COLUMNA_NOMBRE not in df_comentarios.columns:
    st.error(f"Error fatal: No se encontró la columna '{COLUMNA_NOMBRE}' en la hoja 'Comentarios'.")
    st.error("Revisa que el nombre en tu Google Sheet sea EXACTAMENTE ese (mayúsculas y acentos importan).")
    st.write("Columnas encontradas:", df_comentarios.columns.to_list()) # Imprime las columnas que SÍ encontró
    st.stop()

# Guardamos los nombres de columna tal cual están en el DF
meses_en_df = [
    col for col in df_comentarios.columns 
    if col.lower() in COLUMNAS_MESES_BUSCAR
]

if not meses_en_df:
    st.error("No se encontraron columnas de meses (ej: 'enero', 'febrero') en tu hoja 'Comentarios'.")
    st.write("Columnas encontradas:", df_comentarios.columns.to_list())
    st.stop()

# Selectbox para Empleados
empleado_seleccionado = st.selectbox(
    "Selecciona un Empleado:",
    options=df_comentarios[COLUMNA_NOMBRE].unique()
)

# Selectbox para el Mes
mes_seleccionado = st.selectbox(
    "Selecciona un Mes:",
    options=meses_en_df, # Usamos los nombres de columna reales
    format_func=lambda x: x.capitalize() # Muestra el mes con mayúscula
)

st.divider()

# --- 4. LÓGICA DE EDICIÓN DE COMENTARIO ---

if empleado_seleccionado and mes_seleccionado:
    
    try:
        # Extraemos el valor de la celda específica
        comentario_actual = df_comentarios.loc[
            df_comentarios[COLUMNA_NOMBRE] == empleado_seleccionado,
            mes_seleccionado 
        ].values[0]
        
        if pd.isna(comentario_actual):
            comentario_actual = ""
            
    except Exception as e:
        st.error(f"Error al leer el comentario: {e}")
        comentario_actual = ""

    st.subheader(f"Editando comentario para {empleado_seleccionado} - Mes: {mes_seleccionado.capitalize()}")

    comentario_nuevo = st.text_area(
        "Comentario:",
        value=comentario_actual,
        height=200,
        key=f"{empleado_seleccionado}_{mes_seleccionado}"
    )

    # --- 5. LÓGICA DE GUARDADO ---
    if st.button("Guardar Comentario"):
        
        if comentario_nuevo != comentario_actual:
            with st.spinner("Guardando comentario..."):
                try:
                    df_para_guardar = gc.get_data("rendimiento", "comentarios")
                    df_para_guardar.columns = df_para_guardar.columns.str.strip() 

                    indice_fila = df_para_guardar[
                        df_para_guardar[COLUMNA_NOMBRE] == empleado_seleccionado
                    ].index
                    
                    if not indice_fila.empty:
                        df_para_guardar.loc[indice_fila, mes_seleccionado] = comentario_nuevo
                        
                        gc.update_dataframe_in_sheet(
                            sheet_key="rendimiento",
                            data_key="comentarios",
                            df=df_para_guardar
                        )
                        
                        st.success("¡Comentario guardado con éxito!")
                        st.cache_data.clear()
                    else:
                        st.error("No se pudo encontrar la fila del empleado para guardar.")
                
                except Exception as e:
                    st.error(f"Error al guardar el comentario: {e}")
        else:
            st.info("No se detectaron cambios en el comentario.")