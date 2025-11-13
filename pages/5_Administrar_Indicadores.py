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
    page_title="Gestión de Indicadores",
    page_icon="⚖️",
    layout="wide"
)

st.title("Opción 5: Administrar Indicadores (Hoja 'Valores')")
st.write("Aquí puedes editar, agregar o eliminar los indicadores y sus pesos.")

# --- 2. CARGAR DATOS ---
@st.cache_data(ttl=60) # Cache de 1 minuto
def load_data():
    """Carga los datos de indicadores desde Google Sheets."""
    try:
        df = gc.get_data("rendimiento", "indicadores")
        if df.empty:
            st.warning("No se encontraron datos. La hoja 'Valores' puede estar vacía.")
            return pd.DataFrame()
        
        df.columns = df.columns.str.strip()
        
        # --- Lógica de Porcentaje ---
        # Google Sheets guarda "20%" como 0.2
        # Convertimos 0.2 a 20 para que sea fácil de editar.
        if 'Peso' in df.columns:
            # Creamos una columna 'Peso (en %)' para la edición
            df['Peso (en %)'] = pd.to_numeric(df['Peso'], errors='coerce') * 100
        else:
            st.error("No se encontró la columna 'Peso' en la hoja 'Valores'.")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame()

df_indicadores = load_data()

if df_indicadores.empty:
    st.error("No se pudieron cargar los datos de 'Valores'. Revisa la conexión.")
    st.stop() 

# Guardamos una copia original para comparar
df_original = df_indicadores.copy()

# --- 3. EDITOR INTERACTIVO ---
st.subheader("Editor de Indicadores")
st.info("""
- **Editar:** Haz doble clic en una celda. Para 'Peso (en %)', escribe '20' para 20%.
- **Agregar:** Baja hasta el final y usa la fila vacía.
- **Eliminar:** Haz clic en la casilla de la fila y presiona 'Supr' (Delete).
- **Guardar:** Presiona el botón 'Guardar Cambios' al final.
""")

# Ocultamos la columna original 'Peso' (que tiene 0.2)
# y solo mostramos la columna 'Peso (en %)' (que tiene 20)
edited_df = st.data_editor(
    df_indicadores,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Peso": None, # Ocultamos la columna original
        "Factores de productividad": st.column_config.TextColumn("Factor de Productividad", width="large", required=True),
        "Descripción": st.column_config.TextColumn("Descripción", width="large"),
        "Peso (en %)": st.column_config.NumberColumn("Peso (%)", min_value=0, max_value=100, required=True)
    }
)

st.divider()

# --- 4. LÓGICA DE GUARDADO ---
if st.button("Guardar Cambios en Google Sheets"):
    # Comparamos si el DF original es diferente al editado
    if not df_original.equals(edited_df):
        with st.spinner("Guardando cambios..."):
            try:
                # --- Lógica de Porcentaje (Inversa) ---
                # Tomamos la columna 'Peso (en %)' (ej: 20)
                # La convertimos de nuevo a 0.2
                # y la guardamos en la columna original 'Peso'
                df_to_save = edited_df.copy()
                df_to_save['Peso'] = df_to_save['Peso (en %)'] / 100
                
                # Eliminamos la columna temporal antes de guardar
                df_to_save = df_to_save.drop(columns=['Peso (en %)'])
                
                # Reordenamos las columnas para que coincidan con la hoja original
                columnas_originales = [col for col in df_original.columns if col != 'Peso (en %)']
                df_to_save = df_to_save[columnas_originales]
                
                # Llamamos a nuestra función del conector
                gc.update_dataframe_in_sheet(
                    sheet_key="rendimiento", 
                    data_key="indicadores", 
                    df=df_to_save
                )
                st.success("¡Indicadores guardados con éxito!")
                st.cache_data.clear() # Limpiamos el caché
            
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    else:
        st.info("No se detectaron cambios para guardar.")