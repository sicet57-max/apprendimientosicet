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

# --- GUARDIA DE AUTENTICACIÓN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Por favor, inicia sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DE LA GUARDIA ---

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestión de Comentarios",
    page_icon="💬",
    layout="wide"
)

st.title("Opción 2: Comentarios por Empleado")
st.write("Selecciona un empleado y un mes para ver, agregar o modificar un comentario.")

# --- 2. CARGAR DATOS (¡¡LÓGICA MEJORADA!!) ---
# ¡¡Eliminamos el caché!!
def load_data():
    """Carga los datos de comentarios Y de personal."""
    try:
        # Cargamos la lista de empleados (la fuente de verdad)
        df_personal = gc.get_data("rendimiento", "personal")
        
        # Cargamos la hoja de comentarios
        df_comentarios = gc.get_data("rendimiento", "comentarios")
        
        if df_personal.empty:
            st.error("No se pudieron cargar los datos de 'Informacion'.")
            return pd.DataFrame(), pd.DataFrame()
        
        if df_comentarios.empty:
            st.warning("No se encontraron datos en la hoja 'Comentarios'.")
            # Creamos un DF vacío si no existe
            df_comentarios = pd.DataFrame() 

        # Limpiamos los nombres de las columnas
        df_personal.columns = df_personal.columns.str.strip()
        df_comentarios.columns = df_comentarios.columns.str.strip()

        # Asegurarnos que Cédula sea string
        if 'Cédula' in df_personal.columns:
            df_personal['Cédula'] = df_personal['Cédula'].astype(str)
        if 'Cédula' in df_comentarios.columns:
            df_comentarios['Cédula'] = df_comentarios['Cédula'].astype(str)
            
        return df_personal, df_comentarios
    
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_personal, df_comentarios = load_data()

if df_personal.empty:
    st.error("No se pudieron cargar los datos de personal. Revisa la conexión.")
    st.stop()

# --- 3. FILTROS DE SELECCIÓN ---
st.subheader("Seleccionar Empleado y Mes")

# Columna de nombre de técnico (con y sin acento)
col_nombre_tecnico = "Nombre del tecnico"
if col_nombre_tecnico not in df_personal.columns:
     col_nombre_tecnico = "Nombre del técnico" 
     if col_nombre_tecnico not in df_personal.columns:
         st.error("No se encuentra 'Nombre del tecnico' o 'Nombre del técnico' en 'Informacion'")
         st.stop()

# ¡¡CAMBIO!! Usamos la lista de df_personal para el selector
empleado_seleccionado = st.selectbox(
    "Selecciona un Empleado:",
    options=df_personal[col_nombre_tecnico].unique()
)

# Lista de meses
meses_columnas = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]
# Convertimos las columnas del DF de comentarios a minúsculas para comparar
df_comentarios.columns = df_comentarios.columns.str.lower()
meses_disponibles = [mes for mes in meses_columnas if mes in df_comentarios.columns]

if not meses_disponibles:
    st.error("No se encontraron columnas de meses (ej: 'enero', 'febrero') en tu hoja 'Comentarios'.")
    st.stop()

mes_seleccionado = st.selectbox(
    "Selecciona un Mes:",
    options=meses_disponibles,
    format_func=lambda x: x.capitalize()
)

st.divider()

# --- 4. LÓGICA DE EDICIÓN DE COMENTARIO ---

if empleado_seleccionado and mes_seleccionado:
    
    # Obtenemos la cédula del empleado
    cedula_empleado = df_personal[df_personal[col_nombre_tecnico] == empleado_seleccionado]['Cédula'].values[0]

    # Buscamos la fila en df_comentarios
    fila_comentario = df_comentarios[df_comentarios['cédula'] == cedula_empleado]
    
    comentario_actual = ""
    if not fila_comentario.empty:
        try:
            comentario_actual = fila_comentario[mes_seleccionado].values[0]
            if pd.isna(comentario_actual):
                comentario_actual = ""
        except KeyError:
             st.warning(f"La columna '{mes_seleccionado}' parece no existir en minúsculas.")
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
                    # Cargamos los datos originales OTRA VEZ para evitar conflictos
                    df_para_guardar = gc.get_data("rendimiento", "comentarios")
                    df_para_guardar.columns = df_para_guardar.columns.str.strip()

                    # Buscamos la fila por CÉDULA (más seguro que por nombre)
                    indice_fila = df_para_guardar[df_para_guardar['Cédula'] == cedula_empleado].index
                    
                    if not indice_fila.empty:
                        # Buscamos el nombre de columna original (con mayúsculas/minúsculas)
                        columna_mes_original = [
                            col for col in df_para_guardar.columns 
                            if col.lower() == mes_seleccionado
                        ][0]
                        
                        df_para_guardar.loc[indice_fila, columna_mes_original] = comentario_nuevo
                        
                        # Subimos el DataFrame COMPLETO de vuelta a Google Sheets
                        gc.update_dataframe_in_sheet(
                            sheet_key="rendimiento",
                            data_key="comentarios",
                            df=df_para_guardar
                        )
                        st.success("¡Comentario guardado con éxito!")
                        st.rerun() # Recargamos para ver el cambio
                    else:
                        st.error("No se pudo encontrar la fila del empleado para guardar. ¿Está el empleado en la hoja 'Comentarios'?")
                
                except Exception as e:
                    st.error(f"Error al guardar el comentario: {e}")
        else:
            st.info("No se detectaron cambios en el comentario.")