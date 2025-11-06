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
import plotly.express as px

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ficha de Empleado",
    page_icon="👤",
    layout="wide"
)

st.title("Opción 6: Ficha de Empleado (Vista 360°)")
st.write("Selecciona un empleado para ver toda su información consolidada.")

# --- 2. CARGAR TODOS LOS DATOS ---
def load_all_data():
    """Carga todas las hojas de datos necesarias."""
    try:
        df_personal = gc.get_data("rendimiento", "personal")
        df_comentarios = gc.get_data("rendimiento", "comentarios")
        df_calculos = gc.get_data("calculo", "calculos")

        # --- Limpieza de datos ---
        if not df_personal.empty:
            df_personal.columns = df_personal.columns.astype(str).str.strip()
            if 'Cédula' in df_personal.columns:
                df_personal['Cédula'] = df_personal['Cédula'].astype(str)
        
        if not df_comentarios.empty:
            df_comentarios.columns = df_comentarios.columns.astype(str).str.strip()
            if 'Cédula' in df_comentarios.columns:
                df_comentarios['Cédula'] = df_comentarios['Cédula'].astype(str)

        if not df_calculos.empty:
            df_calculos.columns = df_calculos.columns.astype(str).str.strip().str.lower()
            if 'porcentaje_rendimiento' in df_calculos.columns:
                df_calculos['porcentaje_num'] = df_calculos['porcentaje_rendimiento'].astype(str).str.replace('%', '', regex=False).astype(float)
            if 'mes' in df_calculos.columns:
                 # Ordenamos los meses para la gráfica
                meses_ordenados = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                df_calculos['mes'] = pd.Categorical(df_calculos['mes'], categories=meses_ordenados, ordered=True)
            
        return df_personal, df_comentarios, df_calculos
    
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_personal, df_comentarios, df_calculos = load_all_data()

if df_personal.empty:
    st.error("No se pudieron cargar los datos de 'Informacion'. La aplicación no puede continuar.")
    st.stop()

# --- 3. SELECCIÓN DE EMPLEADO ---
col_nombre_tecnico = "Nombre del tecnico"
if col_nombre_tecnico not in df_personal.columns:
     col_nombre_tecnico = "Nombre del técnico" 
     if col_nombre_tecnico not in df_personal.columns:
         st.error("No se encuentra 'Nombre del tecnico' o 'Nombre del técnico' en 'Informacion'")
         st.stop()

# Creamos una lista de empleados, con una opción vacía al principio
lista_empleados = [""] + list(df_personal[col_nombre_tecnico].unique())

empleado_sel = st.selectbox(
    "Selecciona un empleado para ver su ficha:",
    options=lista_empleados,
    index=0 # Por defecto no muestra nada
)

st.divider()

# --- 4. MOSTRAR DATOS (si se selecciona un empleado) ---
if empleado_sel:
    
    # --- 4.1. DATOS PERSONALES ---
    st.header(f"Ficha de: {empleado_sel}")
    
    try:
        # Obtenemos la fila (serie) de datos del empleado
        info_empleado = df_personal[df_personal[col_nombre_tecnico] == empleado_sel].iloc[0]
        
        # Mostramos los datos en columnas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cédula", info_empleado.get("Cédula", "N/A"))
        with col2:
            st.metric("Empresa", info_empleado.get("Empresa", "N/A"))
        with col3:
            st.metric("Cargo", info_empleado.get("Cargo", "N/A"))
        
        st.write(f"**Ubicación:** {info_empleado.get('Ubicacion', 'N/A')}")
        st.write(f"**Número de Contacto:** {info_empleado.get('Numero de contacto', 'N/A')}")
        
    except Exception as e:
        st.error(f"No se pudo cargar la información personal de {empleado_sel}.")
        st.error(e)

    # --- 4.2. HISTORIAL DE RENDIMIENTO ---
    st.subheader("Historial de Rendimiento")
    
    if df_calculos.empty:
        st.info("No hay datos de rendimiento registrados.")
    else:
        # Filtramos los cálculos para este empleado
        df_calc_empleado = df_calculos[df_calculos["nombre del técnico"] == empleado_sel]
        
        if df_calc_empleado.empty:
            st.info(f"No se han encontrado evaluaciones de rendimiento para {empleado_sel}.")
        else:
            # Ordenamos por mes para que la gráfica tenga sentido
            df_calc_empleado = df_calc_empleado.sort_values(by='mes')
            
            # Gráfica de evolución
            fig = px.line(
                df_calc_empleado,
                x='mes',
                y='porcentaje_num',
                title=f"Evolución del Rendimiento de {empleado_sel}",
                markers=True,
                text='porcentaje_num'
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(xaxis_title="Mes", yaxis_title="Rendimiento (%)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de historial
            st.dataframe(df_calc_empleado)

    # --- 4.3. COMENTARIOS ---
    st.subheader("Comentarios Registrados")
    
    if df_comentarios.empty:
        st.info("No hay datos de comentarios registrados.")
    else:
        try:
            # Filtramos la fila de comentarios para este empleado
            # Asumimos que la hoja de comentarios usa el mismo nombre
            info_comentarios = df_comentarios[df_comentarios[col_nombre_tecnico] == empleado_sel]
            
            if info_comentarios.empty:
                st.info(f"No se ha encontrado una fila de comentarios para {empleado_sel}.")
            else:
                # Quitamos las columnas de ID para mostrar solo los meses
                columnas_meses = [
                    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
                ]
                
                # Filtramos las columnas que sí existen
                columnas_a_mostrar = [col for col in columnas_meses if col in info_comentarios.columns]
                
                st.dataframe(info_comentarios[columnas_a_mostrar])

        except Exception as e:
            st.error(f"No se pudo cargar la información de comentarios.")
            st.error(e)