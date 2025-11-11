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
    page_title="Cálculo de Rendimiento",
    page_icon="🧮",
    layout="wide"
)

st.title("Opción 3: Cálculo de Rendimiento")
st.write("Completa el formulario para evaluar el rendimiento de un empleado.")

# --- 2. CARGAR DATOS ---
def load_all_data():
    """Carga todas las hojas de datos necesarias."""
    try:
        df_personal = gc.get_data("rendimiento", "personal")
        df_indicadores = gc.get_data("rendimiento", "indicadores")
        df_calculos = gc.get_data("calculo", "calculos")
        
        if not df_personal.empty:
            df_personal.columns = df_personal.columns.astype(str).str.strip()
            if 'Cédula' in df_personal.columns:
                df_personal['Cédula'] = df_personal['Cédula'].astype(str)
        else:
            st.error("No se pudieron cargar los datos de 'Informacion'.")
            
        if not df_indicadores.empty:
            df_indicadores.columns = df_indicadores.columns.astype(str).str.strip()
            if 'Peso' in df_indicadores.columns:
                df_indicadores['Peso_Float'] = pd.to_numeric(df_indicadores['Peso'], errors='coerce')
                df_indicadores['Peso_Num'] = df_indicadores['Peso_Float'] * 100
            else:
                st.error("No se encontró la columna 'Peso' en la hoja 'Valores'.")
        else:
            st.warning("Advertencia: No se cargaron datos de 'Valores'.")

        if not df_calculos.empty:
            df_calculos.columns = df_calculos.columns.astype(str).str.strip().str.lower()
            if 'dia' in df_calculos.columns:
                df_calculos['dia'] = df_calculos['dia'].astype(str)
            if 'cédula' in df_calculos.columns:
                df_calculos['cédula'] = df_calculos['cédula'].astype(str)
            df_calculos = df_calculos.reset_index(drop=True) 
        
        return df_personal, df_indicadores, df_calculos
    
    except Exception as e:
        st.error(f"Error fatal al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_personal, df_indicadores, df_calculos = load_all_data()

if df_personal.empty or df_indicadores.empty:
    st.error("Faltan datos de 'Informacion' o 'Valores'. Revisa las pestañas en Google Sheets y los errores anteriores.")
    st.stop()

# --- 3. FORMULARIO DE EVALUACIÓN ---
with st.form("evaluacion_form"):
    
    st.subheader("Paso 1: Seleccionar Empleado, Mes y Día")
    col1, col2, col3 = st.columns(3)
    with col1:
        col_nombre_tecnico = "Nombre del tecnico"
        if col_nombre_tecnico not in df_personal.columns:
             col_nombre_tecnico = "Nombre del técnico" 
             if col_nombre_tecnico not in df_personal.columns:
                 st.error("No se encuentra 'Nombre del tecnico' o 'Nombre del técnico' en 'Informacion'")
                 st.stop()
        empleado_sel = st.selectbox("Empleado a evaluar:", options=df_personal[col_nombre_tecnico].unique(), key="empleado_select")
    with col2:
        mes_sel = st.selectbox("Mes de evaluación:", options=["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key="mes_select")
    with col3:
        dia_sel = st.number_input("Día de evaluación:", min_value=1, max_value=31, value=datetime.now().day, key="dia_select")
    
    st.divider()
    st.subheader("Paso 2: Calificar Indicadores (de 1 a 10)")
    calificaciones = {} 
    col_factores = "Factores de productividad"
    st.write("Califica todos los indicadores:")
    for index, row in df_indicadores.iterrows():
        indicador = row[col_factores]
        peso = row["Peso_Num"] 
        calificaciones[indicador] = st.slider(f"**{indicador}** (Peso: {peso}%)", min_value=1, max_value=10, value=5, key=f"slider_{indicador}")
    
    st.divider()
    st.subheader("Paso 3: Comentario (Opcional)")
    comentario_eval = st.text_area("Justificación de la calificación (opcional):")
    
    submitted = st.form_submit_button("Calcular y Guardar Evaluación")

# --- 4. LÓGICA DE CÁLCULO Y GUARDADO (¡¡CORREGIDA!!) ---
if submitted:
    with st.spinner("Calculando y guardando..."):
        rendimiento_final = 0
        for indicador, calificacion in calificaciones.items():
            peso = df_indicadores.loc[df_indicadores[col_factores] == indicador, 'Peso_Num'].values[0]
            score_indicador = (calificacion / 10) * peso
            rendimiento_final += score_indicador
        st.metric(label=f"Rendimiento Final para {empleado_sel} ({mes_sel})", value=f"{rendimiento_final:.2f} %")
        
        try:
            info_empleado = df_personal[df_personal[col_nombre_tecnico] == empleado_sel].iloc[0]
            cedula = info_empleado["Cédula"]
            empresa = info_empleado["Empresa"]
            
            fecha_guardado = datetime.now().strftime("%Y-%m-%d")
            hora_guardado = datetime.now().strftime("%H:%M:%S")

            nueva_fila = [
                fecha_guardado, 
                mes_sel,
                str(dia_sel), 
                empleado_sel,
                str(cedula), 
                empresa,
                f"{rendimiento_final:.2f}%",
                comentario_eval,
                f"{fecha_guardado} {hora_guardado}" 
            ]
            
            # --- ¡¡BLOQUE DE CÓDIGO PROBLEMÁTICO ELIMINADO!! ---
            # Ya no añadimos el encabezado desde aquí.

            # Solo añadimos la fila con los datos
            gc.append_row_to_sheet(sheet_key="calculo", data_key="calculos", data_list=nueva_fila)
            
            st.success("¡Evaluación guardada con éxito en Google Sheets!")
            st.rerun() 
        except Exception as e:
            st.error(f"Error al guardar en Google Sheets: {e}")

# --- 5. SECCIÓN DE HISTORIAL Y GESTIÓN (¡¡CORREGIDA!!) ---
st.divider()
st.title("Historial y Gestión de Evaluaciones")

if df_calculos.empty:
    st.info("Aún no hay datos de rendimiento guardados para mostrar.")
else:
    df_historial = df_calculos.copy()
    
    col_nombre_hist = "nombre del técnico"
    col_cedula_hist = "cédula"
    col_mes_hist = "mes"
    col_dia_hist = "dia"
    col_comentario_hist = "comentario"
    col_creacion_hist = "fecha_creacion"
    
    # --- ¡¡NUEVA LÍNEA DE SEGURIDAD!! ---
    # Convertimos la columna a numérico, y si falla (ej: texto "porcentaje_rendimiento"),
    # lo convierte en 'NaN' (No a Number)
    df_historial['porcentaje_num'] = pd.to_numeric(
        df_historial['porcentaje_rendimiento'].astype(str).str.replace('%', '', regex=False), 
        errors='coerce'
    )
    # Eliminamos las filas donde falló la conversión (ej: la fila de encabezado)
    df_historial = df_historial.dropna(subset=['porcentaje_num'])
    
    st.subheader("Filtros de Historial")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        nombres_sel = st.multiselect("Filtrar por Técnico:", options=df_historial[col_nombre_hist].unique())
    with col2:
        cedulas_sel = st.multiselect("Filtrar por Cédula:", options=df_historial[col_cedula_hist].unique())
    with col3:
        meses_sel = st.multiselect("Filtrar por Mes:", options=df_historial[col_mes_hist].unique())
    with col4:
        dias_sel = st.multiselect("Filtrar por Día:", options=sorted(df_historial[col_dia_hist].unique()))
        
    df_filtrado = df_historial.copy()
    if nombres_sel:
        df_filtrado = df_filtrado[df_filtrado[col_nombre_hist].isin(nombres_sel)]
    if cedulas_sel:
        df_filtrado = df_filtrado[df_filtrado[col_cedula_hist].isin(cedulas_sel)]
    if meses_sel:
        df_filtrado = df_filtrado[df_filtrado[col_mes_hist].isin(meses_sel)]
    if dias_sel:
        df_filtrado = df_filtrado[df_filtrado[col_dia_hist].isin(dias_sel)]

    st.subheader("Resultados Filtrados")
    if df_filtrado.empty:
        st.warning("No se encontraron registros que coincidan con los filtros seleccionados.")
    else:
        columnas_limpias = [
            'fecha', 'mes', 'dia', col_nombre_hist, col_cedula_hist, 
            'empresa', 'porcentaje_rendimiento', 'comentario', col_creacion_hist
        ]
        columnas_a_mostrar = [col for col in columnas_limpias if col in df_filtrado.columns]
        st.dataframe(df_filtrado[columnas_a_mostrar])

        try:
            # La columna 'porcentaje_num' ya existe y está limpia
            df_filtrado_grafica = df_filtrado.copy() 
            fig = px.bar(
                df_filtrado_grafica,
                x="fecha", y="porcentaje_num", color=col_nombre_hist,
                title="Rendimiento por Fecha (Filtrado)", text="porcentaje_num",
                hover_data=[col_nombre_hist, col_mes_hist, col_dia_hist, col_comentario_hist]
            )
            fig.update_layout(xaxis_title="Fecha de Evaluación", yaxis_title="Rendimiento (%)")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar la gráfica: {e}")

    df_calculos_con_id = df_historial.copy() # Usamos el DF ya limpio
    try:
        df_calculos_con_id["id_unico_gestion"] = (
            "Registro #" + (df_calculos_con_id.index + 1).astype(str) + " | " + 
            df_calculos_con_id[col_nombre_hist] + " | " +
            df_calculos_con_id["fecha"].astype(str) + " | " + # Convertimos fecha a str
            df_calculos_con_id["porcentaje_rendimiento"]
        )
    except KeyError:
        st.error("Faltan columnas clave para la gestión de datos. Revisa tu hoja 'Calculo rendimiento'.")
        st.stop()
    
    opciones_gestion = [""] + list(df_calculos_con_id["id_unico_gestion"].unique())
    
    st.divider()
    st.subheader("Modificar un Registro")
    st.info("Selecciona un registro de la lista para editar su mes, día o comentario.")
    id_a_modificar = st.selectbox("Selecciona un registro para modificar:", options=opciones_gestion, key="modify_select")
    
    if id_a_modificar: 
        registro_seleccionado = df_calculos_con_id[df_calculos_con_id["id_unico_gestion"] == id_a_modificar].iloc[0]
        mes_actual = registro_seleccionado[col_mes_hist]
        dia_actual = int(float(registro_seleccionado[col_dia_hist]))
        comentario_actual = registro_seleccionado[col_comentario_hist]
        lista_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        indice_mes = lista_meses.index(mes_actual) if mes_actual in lista_meses else 0
        
        with st.form("modify_form"):
            st.write(f"**Modificando:** {id_a_modificar}")
            col_mod_1, col_mod_2 = st.columns(2)
            with col_mod_1:
                nuevo_mes = st.selectbox("Mes:", options=lista_meses, index=indice_mes)
            with col_mod_2:
                nuevo_dia = st.number_input("Día:", min_value=1, max_value=31, value=dia_actual)
            nuevo_comentario = st.text_area("Comentario:", value=comentario_actual)
            modify_submitted = st.form_submit_button("Guardar Modificación")
            
            if modify_submitted:
                with st.spinner("Guardando modificación..."):
                    try:
                        indice_fila_a_modificar = df_calculos_con_id[df_calculos_con_id["id_unico_gestion"] == id_a_modificar].index[0]
                        df_calculos_con_id.loc[indice_fila_a_modificar, col_mes_hist] = nuevo_mes
                        df_calculos_con_id.loc[indice_fila_a_modificar, col_dia_hist] = str(nuevo_dia)
                        df_calculos_con_id.loc[indice_fila_a_modificar, col_comentario_hist] = nuevo_comentario
                        
                        if col_creacion_hist in df_calculos_con_id.columns:
                            fecha_mod = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            df_calculos_con_id.loc[indice_fila_a_modificar, col_creacion_hist] = f"Modificado: {fecha_mod}"

                        # Preparamos el DF para guardar (quitamos columnas 'num' e 'id')
                        columnas_originales_sheet = [col for col in df_calculos.columns if col != 'porcentaje_num']
                        df_final_para_guardar = df_calculos_con_id[columnas_originales_sheet]
                        
                        gc.update_dataframe_in_sheet(sheet_key="calculo", data_key="calculos", df=df_final_para_guardar)
                        st.success("¡Registro modificado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar la modificación: {e}")

    st.divider()
    st.subheader("Eliminar Registros del Historial")
    st.info("Selecciona uno o más registros de la lista para eliminarlos permanentemente.")
    ids_a_borrar_sel = st.multiselect("Selecciona los registros que deseas eliminar:", options=opciones_gestion[1:], key="delete_select")
    
    if st.button("Confirmar Eliminación", type="primary"):
        if not ids_a_borrar_sel:
            st.error("No has seleccionado ningún registro para eliminar.")
        else:
            with st.spinner("Eliminando registros..."):
                try:
                    df_sin_borrados = df_calculos_con_id[~df_calculos_con_id["id_unico_gestion"].isin(ids_a_borrar_sel)]
                    
                    # Preparamos el DF para guardar (quitamos columnas 'num' e 'id')
                    columnas_originales_sheet = [col for col in df_calculos.columns if col != 'porcentaje_num']
                    df_final_para_guardar = df_sin_borrados[columnas_originales_sheet]

                    gc.update_dataframe_in_sheet(sheet_key="calculo", data_key="calculos", df=df_final_para_guardar)
                    st.success("¡Registros eliminados con éxito!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")

# --- 6. SECCIÓN DE REPORTE MENSUAL (¡¡CORREGIDA!!) ---
st.divider()
st.title("Reporte de Rendimiento Mensual")

if df_calculos.empty:
    st.info("No hay datos de rendimiento para generar un reporte mensual.")
else:
    st.write("Presiona el botón para calcular el promedio mensual de cada técnico y guardarlo en una nueva pestaña de Google Sheets.")
    
    # Usamos el df_historial que ya está limpio de filas de encabezado
    df_reporte = df_historial.copy()
    
    # La columna 'porcentaje_num' ya existe y está limpia
    if 'porcentaje_num' not in df_reporte.columns:
        st.error("Error crítico: La columna 'porcentaje_num' no se pudo calcular.")
        st.stop()
        
    df_summary = df_reporte.groupby([col_nombre_hist, col_mes_hist])['porcentaje_num'].mean().reset_index()
    df_summary = df_summary.rename(columns={'porcentaje_num': 'Rendimiento Promedio (%)'})
    df_summary['Rendimiento Promedio (%)'] = df_summary['Rendimiento Promedio (%)'].round(2)
    
    st.subheader("Previsualización del Reporte Mensual")
    st.dataframe(df_summary)
    
    if st.button("Generar y Guardar Reporte Mensual", type="primary"):
        with st.spinner("Guardando reporte mensual en Google Sheets..."):
            try:
                gc.update_dataframe_in_sheet(sheet_key="calculo", data_key="promedios", df=df_summary)
                st.success("¡Reporte mensual guardado con éxito en la pestaña 'Promedios Mensuales'!")
            except Exception as e:
                st.error(f"Error al guardar el reporte: {e}")