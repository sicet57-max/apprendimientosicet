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

# --- 2. CARGAR DATOS ---
def load_data():
    """Carga los datos de comentarios Y de personal."""
    try:
        df_personal = gc.get_data("rendimiento", "personal")
        df_comentarios = gc.get_data("rendimiento", "comentarios")
        
        if df_personal.empty:
            st.error("No se pudieron cargar los datos de 'Informacion'.")
            return pd.DataFrame(), pd.DataFrame()
        
        if df_comentarios.empty:
            st.warning("No se encontraron datos en la hoja 'Comentarios'. Se creará si es necesario.")
            df_comentarios = pd.DataFrame() 

        df_personal.columns = df_personal.columns.str.strip()
        df_comentarios.columns = df_comentarios.columns.str.strip()

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

col_nombre_tecnico_personal = "Nombre del tecnico"
if col_nombre_tecnico_personal not in df_personal.columns:
     col_nombre_tecnico_personal = "Nombre del técnico" 
     if col_nombre_tecnico_personal not in df_personal.columns:
         st.error("No se encuentra 'Nombre del tecnico' o 'Nombre del técnico' en 'Informacion'")
         st.stop()

empleado_seleccionado = st.selectbox(
    "Selecciona un Empleado:",
    options=df_personal[col_nombre_tecnico_personal].unique()
)

meses_columnas = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]
df_comentarios_lower_cols = df_comentarios.copy()
df_comentarios_lower_cols.columns = df_comentarios_lower_cols.columns.str.lower()
meses_disponibles = [mes for mes in meses_columnas if mes in df_comentarios_lower_cols.columns]

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
    
    cedula_empleado = df_personal[df_personal[col_nombre_tecnico_personal] == empleado_seleccionado]['Cédula'].values[0]
    
    fila_comentario = pd.DataFrame()
    if 'cédula' in df_comentarios_lower_cols.columns:
        fila_comentario = df_comentarios_lower_cols[df_comentarios_lower_cols['cédula'] == cedula_empleado]
    
    comentario_actual = ""
    if not fila_comentario.empty:
        try:
            comentario_actual = fila_comentario[mes_seleccionado].values[0]
            if pd.isna(comentario_actual):
                comentario_actual = ""
        except KeyError:
             comentario_actual = ""
            
    st.subheader(f"Editando comentario para {empleado_seleccionado} - Mes: {mes_seleccionado.capitalize()}")

    comentario_nuevo = st.text_area(
        "Comentario:",
        value=comentario_actual,
        height=200,
        key=f"{empleado_seleccionado}_{mes_seleccionado}"
    )

    # --- 5. LÓGICA DE GUARDADO (¡¡CORREGIDA!!) ---
    if st.button("Guardar Comentario"):
        
        if comentario_nuevo != comentario_actual:
            with st.spinner("Guardando comentario..."):
                try:
                    df_para_guardar = gc.get_data("rendimiento", "comentarios")
                    df_para_guardar.columns = df_para_guardar.columns.str.strip()

                    # Buscamos la fila por CÉDULA
                    if 'Cédula' in df_para_guardar.columns:
                        indice_fila = df_para_guardar[df_para_guardar['Cédula'] == cedula_empleado].index
                    else:
                        indice_fila = pd.Index([]) # Creamos un índice vacío si la columna no existe

                    # Buscamos el nombre de columna original (con mayúsculas/minúsculas)
                    columna_mes_original = [
                        col for col in df_para_guardar.columns 
                        if col.lower() == mes_seleccionado
                    ][0]
                    
                    if not indice_fila.empty:
                        # --- LÓGICA DE ACTUALIZACIÓN (SI YA EXISTE) ---
                        st.write("Actualizando fila existente...")
                        df_para_guardar.loc[indice_fila, columna_mes_original] = comentario_nuevo
                        
                    else:
                        # --- ¡¡NUEVA LÓGICA DE ADICIÓN (SI NO EXISTE)!! ---
                        st.write("Creando nueva fila para el empleado...")
                        
                        # Buscamos el nombre de la columna Cédula y Nombre
                        col_cedula_original = [col for col in df_para_guardar.columns if col.lower() == 'cédula'][0]
                        col_nombre_original = [col for col in df_para_guardar.columns if col.lower() == col_nombre_tecnico_personal.lower()][0]
                        
                        # Creamos la nueva fila como un diccionario
                        nueva_fila = {
                            col_cedula_original: cedula_empleado,
                            col_nombre_original: empleado_seleccionado,
                            columna_mes_original: comentario_nuevo
                        }
                        
                        # Convertimos el dict a un DataFrame y lo añadimos al final
                        df_nueva_fila = pd.DataFrame([nueva_fila])
                        df_para_guardar = pd.concat([df_para_guardar, df_nueva_fila], ignore_index=True)

                    # Subimos el DataFrame COMPLETO (actualizado o con la nueva fila)
                    gc.update_dataframe_in_sheet(
                        sheet_key="rendimiento",
                        data_key="comentarios",
                        df=df_para_guardar
                    )
                    
                    st.success("¡Comentario guardado con éxito!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Error al guardar el comentario: {e}")
                    st.exception(e) # Muestra el error detallado
        else:
            st.info("No se detectaron cambios en el comentario.")