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
    page_title="Dashboard General",
    page_icon="📈",
    layout="wide"
)

# --- GUARDIA DE AUTENTICACIÓN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Por favor, inicia sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DE LA GUARDIA ---

st.title("Opción 4: Visualización y Dashboard General")

# --- 2. CARGAR DATOS ---
def load_dashboard_data():
    """Carga los datos de promedios, cálculos detallados y personal."""
    try:
        df_promedios = gc.get_data("calculo", "promedios")
        df_calculos = gc.get_data("calculo", "calculos")
        df_personal = gc.get_data("rendimiento", "personal")

        # --- Limpieza de datos ---
        if not df_promedios.empty:
            df_promedios.columns = df_promedios.columns.astype(str).str.strip().str.lower()

        if not df_calculos.empty:
            df_calculos.columns = df_calculos.columns.astype(str).str.strip().str.lower()
            if 'fecha' in df_calculos.columns:
                df_calculos['fecha'] = pd.to_datetime(df_calculos['fecha'], errors='coerce').dt.date
            if 'porcentaje_rendimiento' in df_calculos.columns:
                df_calculos['porcentaje_num'] = df_calculos['porcentaje_rendimiento'].astype(str).str.replace('%', '', regex=False).astype(float)
            if 'dia' in df_calculos.columns:
                df_calculos['dia'] = df_calculos['dia'].astype(str)
            if 'cédula' in df_calculos.columns:
                df_calculos['cédula'] = df_calculos['cédula'].astype(str)
            if 'fecha_creacion' in df_calculos.columns:
                df_calculos['fecha_creacion'] = pd.to_datetime(df_calculos['fecha_creacion'], errors='coerce')
        
        if not df_personal.empty:
            df_personal.columns = df_personal.columns.astype(str).str.strip()
            if 'Cédula' in df_personal.columns:
                df_personal['Cédula'] = df_personal['Cédula'].astype(str)
            
        return df_promedios, df_calculos, df_personal
    
    except Exception as e:
        st.error(f"Error fatal al cargar datos del dashboard: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_promedios, df_calculos, df_personal = load_dashboard_data()

# --- 3. MOSTRAR TABLA DE PROMEDIOS MENSUALES ---
st.subheader("📈 Reporte de Promedios Mensuales")
st.write("Esta es la tabla resumen generada desde la 'Opción 3'.")

if df_promedios.empty:
    st.info("Aún no se ha generado ningún reporte de promedios mensuales. Ve a la 'Opción 3' para generarlo.")
else:
    st.dataframe(df_promedios, use_container_width=True)

st.divider()

# --- 4. DASHBOARD DE ANÁLISIS DETALLADO ---
st.title("📊 Análisis Detallado de Rendimiento")

if df_calculos.empty:
    st.info("No hay datos de cálculos detallados para analizar.")
    st.stop()

# --- 4.1. Unir datos ---
col_nombre_tecnico_calc = "nombre del técnico"
col_cedula_calc = "cédula"
col_cedula_pers = "Cédula"
col_creacion_hist = "fecha_creacion" 

if (col_cedula_pers in df_personal.columns) and (col_cedula_calc in df_calculos.columns):
    df_personal_simple = df_personal[[col_cedula_pers, "Empresa", "Cargo"]].rename(columns={"Empresa": "Empresa_Info", "Cargo": "Cargo_Info"})
    df_consolidado = pd.merge(
        df_calculos,
        df_personal_simple,
        left_on=col_cedula_calc,
        right_on=col_cedula_pers,
        how="left"
    )
else:
    st.warning("No se pudo cruzar la información con 'Informacion' (no se encontró 'Cédula' en ambas hojas).")
    df_consolidado = df_calculos.copy()
    df_consolidado['Empresa_Info'] = "N/A"
    df_consolidado['Cargo_Info'] = "N/A" # Añadimos columna dummy para la tabla final

# --- 4.2. Filtros del Dashboard ---
st.subheader("Filtros del Dashboard")
col_mes_hist = "mes"
col_dia_hist = "dia"

col1, col2, col3, col4 = st.columns(4)
with col1:
    nombres_sel = st.multiselect("Filtrar por Técnico:", options=df_consolidado[col_nombre_tecnico_calc].unique())
with col2:
    cedulas_sel = st.multiselect("Filtrar por Cédula:", options=df_consolidado[col_cedula_calc].unique())
with col3:
    meses_sel = st.multiselect("Filtrar por Mes:", options=df_consolidado[col_mes_hist].unique())
with col4:
    dias_sel = st.multiselect("Filtrar por Día:", options=sorted(df_consolidado[col_dia_hist].unique()))

if col_creacion_hist in df_consolidado.columns and not df_consolidado[col_creacion_hist].isnull().all():
    min_fecha_creacion = df_consolidado[col_creacion_hist].min().date()
    max_fecha_creacion = df_consolidado[col_creacion_hist].max().date()
    
    if min_fecha_creacion != max_fecha_creacion:
        rango_fechas_creacion = st.slider(
            "Filtrar por Fecha de Creación (Auditoría):",
            min_value=min_fecha_creacion,
            max_value=max_fecha_creacion,
            value=(min_fecha_creacion, max_fecha_creacion),
            format="YYYY-MM-DD"
        )
    else:
        rango_fechas_creacion = (min_fecha_creacion, max_fecha_creacion)
else:
    rango_fechas_creacion = None

# --- 4.3. Aplicar Filtros ---
df_filtrado_dash = df_consolidado.copy()
if nombres_sel:
    df_filtrado_dash = df_filtrado_dash[df_filtrado_dash[col_nombre_tecnico_calc].isin(nombres_sel)]
if cedulas_sel:
    df_filtrado_dash = df_filtrado_dash[df_filtrado_dash[col_cedula_calc].isin(cedulas_sel)]
if meses_sel:
    df_filtrado_dash = df_filtrado_dash[df_filtrado_dash[col_mes_hist].isin(meses_sel)]
if dias_sel:
    df_filtrado_dash = df_filtrado_dash[df_filtrado_dash[col_dia_hist].isin(dias_sel)]

if rango_fechas_creacion and col_creacion_hist in df_filtrado_dash.columns:
    df_filtrado_dash = df_filtrado_dash[
        (df_filtrado_dash[col_creacion_hist].dt.date >= rango_fechas_creacion[0]) &
        (df_filtrado_dash[col_creacion_hist].dt.date <= rango_fechas_creacion[1])
    ]

# --- 4.4. SECCIÓN "MEJORES RENDIMIENTOS" ---
st.subheader("🏆 Mejores Rendimientos (Promedio)")
tab_top1, tab_top2 = st.tabs(["Según Filtros Aplicados", "General (Todos los Tiempos)"])
# (Esta sección no cambia)
with tab_top1:
    if df_filtrado_dash.empty:
        st.info("No hay datos para los filtros seleccionados.")
    else:
        df_top_filtrado = df_filtrado_dash.groupby(col_nombre_tecnico_calc)['porcentaje_num'].mean().reset_index()
        df_top_filtrado = df_top_filtrado.rename(columns={'porcentaje_num': 'Rendimiento Promedio'})
        df_top_filtrado = df_top_filtrado.sort_values(by='Rendimiento Promedio', ascending=False)
        df_top_filtrado['Rendimiento Promedio'] = df_top_filtrado['Rendimiento Promedio'].round(2)
        if not df_top_filtrado.empty:
            st.metric(label=f"Mejor Técnico (#1): {df_top_filtrado.iloc[0][col_nombre_tecnico_calc]}", value=f"{df_top_filtrado.iloc[0]['Rendimiento Promedio']:.2f} %")
            st.dataframe(df_top_filtrado, use_container_width=True)
        else:
            st.info("No hay datos para mostrar.")
with tab_top2:
    df_top_general = df_consolidado.groupby(col_nombre_tecnico_calc)['porcentaje_num'].mean().reset_index()
    df_top_general = df_top_general.rename(columns={'porcentaje_num': 'Rendimiento Promedio'})
    df_top_general = df_top_general.sort_values(by='Rendimiento Promedio', ascending=False)
    df_top_general['Rendimiento Promedio'] = df_top_general['Rendimiento Promedio'].round(2)
    if not df_top_general.empty:
        st.metric(label=f"Mejor Técnico (#1): {df_top_general.iloc[0][col_nombre_tecnico_calc]}", value=f"{df_top_general.iloc[0]['Rendimiento Promedio']:.2f} %")
        st.dataframe(df_top_general, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")

# --- 4.5. Gráficas de Rendimiento (Filtradas) ---
st.divider()
st.subheader("Visualización Profesional (Filtrada)")

theme_plotly = "plotly_dark"
bg_transparent = {'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)'}

if df_filtrado_dash.empty:
    st.warning("No se encontraron registros que coincidan con los filtros.")
else:
    st.info("Selecciona una pestaña para cambiar el tipo de gráfica. Todas reaccionan a los filtros.")
    
    # --- Lógica de Eje X Inteligente (para gráficas de tiempo) ---
    df_graficos = df_filtrado_dash.copy()
    meses_ordenados = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    if not dias_sel and not meses_sel: 
        x_axis_label_tiempo = col_mes_hist
        xaxis_title_tiempo = "Mes"
        if col_mes_hist in df_graficos.columns:
            df_graficos[col_mes_hist] = pd.Categorical(df_graficos[col_mes_hist], categories=meses_ordenados, ordered=True)
            df_graficos = df_graficos.sort_values(by=col_mes_hist)
    else:
        x_axis_label_tiempo = 'fecha'
        xaxis_title_tiempo = "Fecha de Evaluación"
    
    tab_g1, tab_g2, tab_g3, tab_g4 = st.tabs([
        "📊 Promedio por Técnico (Barras)", 
        "📈 Evolución (Líneas)", 
        "📍 Dispersión (Puntos)", 
        "📦 Distribución (Cajas)"
    ])
    
    with tab_g1:
        # Gráfica 1: (Barras)
        df_graf_tecnico = df_graficos.groupby(col_nombre_tecnico_calc)['porcentaje_num'].mean().reset_index()
        df_graf_tecnico = df_graf_tecnico.rename(columns={'porcentaje_num': 'Rendimiento Promedio'})
        df_graf_tecnico['Rendimiento Promedio'] = df_graf_tecnico['Rendimiento Promedio'].round(2)
        fig_tecnico = px.bar(
            df_graf_tecnico, x=col_nombre_tecnico_calc, y='Rendimiento Promedio',
            title="Rendimiento Promedio por Técnico",
            text='Rendimiento Promedio', template=theme_plotly,
            color='Rendimiento Promedio', color_continuous_scale='RdYlGn'
        )
        fig_tecnico.update_traces(textposition='outside')
        fig_tecnico.update_layout(xaxis_title="Técnico", yaxis_title="Rendimiento Promedio (%)", **bg_transparent)
        st.plotly_chart(fig_tecnico, use_container_width=True)

    with tab_g2:
        # Gráfica 2: (Líneas) - ¡¡CORREGIDA!!
        if x_axis_label_tiempo in df_graficos.columns and col_nombre_tecnico_calc in df_graficos.columns:
            df_graf_tiempo = df_graficos.groupby([x_axis_label_tiempo, col_nombre_tecnico_calc])['porcentaje_num'].mean().reset_index()
            df_graf_tiempo = df_graf_tiempo.rename(columns={'porcentaje_num': 'Rendimiento'})
            df_graf_tiempo['Rendimiento'] = df_graf_tiempo['Rendimiento'].round(2)

            # --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
            # Ordenamos los datos por el eje X ANTES de graficar
            if x_axis_label_tiempo == col_mes_hist:
                 df_graf_tiempo[col_mes_hist] = pd.Categorical(df_graf_tiempo[col_mes_hist], categories=meses_ordenados, ordered=True)
                 df_graf_tiempo = df_graf_tiempo.sort_values(by=col_mes_hist)
            else:
                 df_graf_tiempo = df_graf_tiempo.sort_values(by='fecha')
            # --- FIN DE LA CORRECCIÓN ---

            fig_tiempo = px.line(
                df_graf_tiempo, x=x_axis_label_tiempo, y='Rendimiento',
                color=col_nombre_tecnico_calc,
                title="Evolución del Rendimiento (Promedio)",
                markers=True, line_shape='linear', template=theme_plotly
            )
            fig_tiempo.update_layout(xaxis_title=xaxis_title_tiempo, yaxis_title="Rendimiento (%)", **bg_transparent)
            st.plotly_chart(fig_tiempo, use_container_width=True)
        else:
            st.info("No hay suficientes datos o columnas para mostrar la gráfica de Evolución.")

    with tab_g3:
        # Gráfica 3: (Dispersión)
        hover_data_list = ['comentario', 'mes', 'dia', 'porcentaje_rendimiento']
        if col_creacion_hist in df_graficos.columns:
            hover_data_list.append(col_creacion_hist)
        hover_data_list = [col for col in hover_data_list if col in df_graficos.columns]
        if x_axis_label_tiempo in df_graficos.columns and 'porcentaje_num' in df_graficos.columns and col_nombre_tecnico_calc in df_graficos.columns:
            fig_dispersion = px.scatter(
                df_graficos, x=x_axis_label_tiempo, y='porcentaje_num',
                color=col_nombre_tecnico_calc,
                title="Dispersión de Evaluaciones Individuales",
                hover_data=hover_data_list, template=theme_plotly
            )
            fig_dispersion.update_layout(xaxis_title=xaxis_title_tiempo, yaxis_title="Rendimiento (%)", **bg_transparent)
            st.plotly_chart(fig_dispersion, use_container_width=True)
        else:
            st.info("No hay suficientes datos o columnas para mostrar la gráfica de Dispersión.")

    with tab_g4:
        # Gráfica 4: (Cajas)
        if col_nombre_tecnico_calc in df_graficos.columns and 'porcentaje_num' in df_graficos.columns:
            fig_box = px.box(
                df_graficos, x=col_nombre_tecnico_calc, y='porcentaje_num',
                color=col_nombre_tecnico_calc,
                title="Distribución de Calificaciones por Técnico",
                template=theme_plotly
            )
            fig_box.update_layout(xaxis_title="Técnico", yaxis_title="Rendimiento (%)", **bg_transparent)
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No hay suficientes datos o columnas para mostrar la gráfica de Distribución.")
    
    # --- 4.6. TABLA DE AUDITORÍA (¡¡CORREGIDA!!) ---
    st.divider()
    st.subheader("Trazabilidad de Registros (Auditoría)")
    
    # Definimos la lista de columnas limpias que queremos mostrar
    columnas_finales_tabla = [
        'fecha', 
        'mes', 
        'dia', 
        col_nombre_tecnico_calc, 
        col_cedula_calc, 
        'Empresa_Info', # Usamos la columna limpia de la hoja 'Informacion'
        'Cargo_Info',   # Usamos la columna limpia de la hoja 'Informacion'
        'porcentaje_rendimiento', 
        'comentario',
        col_creacion_hist
    ]
    
    # Filtramos la lista para quedarnos solo con las que existen en el dataframe
    columnas_a_mostrar = [col for col in columnas_finales_tabla if col in df_filtrado_dash.columns]
    
    if col_creacion_hist not in df_filtrado_dash.columns:
        st.info("No se encontró la columna 'fecha_creacion'. Los registros guardados a partir de ahora incluirán esta marca de tiempo.")
    else:
        st.info("Esta tabla muestra cuándo se creó o modificó cada registro (reacciona a los filtros).")
    
    # Mostramos el dataframe filtrado SOLAMENTE con las columnas limpias
    st.dataframe(df_filtrado_dash[columnas_a_mostrar])