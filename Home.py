import streamlit as st

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestión SICET",
    page_icon="🔐",
    layout="wide"
)

# --- 2. LÓGICA DE AUTENTICACIÓN ---

# Inicializamos el estado de sesión
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Verificamos si el usuario ya está autenticado
if st.session_state['authenticated']:
    # --- PÁGINA DE BIENVENIDA (SI YA ESTÁ LOGUEADO) ---
    
    # Logo y títulos en la barra lateral
    try:
        st.sidebar.image("assets/logo_sicet.png", use_container_width=True)
    except:
        st.sidebar.error("No se encontró el logo.")
    
    st.sidebar.title("SICET INGENIERÍA")
    st.sidebar.subheader("Gestión de Rendimiento")
    st.sidebar.success("Sesión iniciada con éxito.")
    
    # Mensaje de bienvenida
    st.title("Plataforma de Gestión y Análisis de Rendimiento")
    st.write("""
    ¡Bienvenido! Has iniciado sesión correctamente.
    
    **Usa el menú de la izquierda para navegar entre las diferentes opciones.**
    """)
    st.divider()

    # --- ¡¡AQUÍ ESTÁ LA ACTUALIZACIÓN!! ---
    st.subheader("Descripción de Módulos")
    st.markdown("""
    * **Datos Personales:** Permite ver, crear, editar y eliminar la información de los empleados.
    * **Comentarios:** Un espacio para registrar y consultar comentarios de desempeño mensuales por técnico.
    * **Cálculo Rendimiento:** El corazón de la app. Aquí puedes calificar (Normal, Sobre rendimiento, Sin calificación), generar reportes mensuales y gestionar (modificar/borrar) los cálculos.
    * **Visualización General:** Un dashboard profesional con filtros, gráficas (barras, líneas, dispersión, cajas) y rankings de rendimiento.
    * **Administrar Indicadores:** Permite editar los factores de productividad y sus pesos (%) directamente desde la app.
    * **Ficha Empleado:** Una vista 360° que consolida toda la información (datos, comentarios, gráficas) de un solo empleado.
    * **Reporte por Rango:** Genera y guarda un reporte de rendimiento promedio para un rango de fechas personalizado (ej: del 31 de oct al 20 de nov).
    """)
    # --- FIN DE LA ACTUALIZACIÓN ---

    st.divider()
    
    # Botón de Cerrar Sesión
    st.subheader("Cerrar Sesión")
    if st.button("Hacer clic aquí para cerrar sesión", type="primary"):
        st.session_state['authenticated'] = False
        st.rerun() 
    
    st.divider()
    st.success("""
    **Un agradecimiento especial a SICET INGENIERÍA por la oportunidad de desarrollar esta herramienta.**
    
    ¡Esperamos que la disfruten!
    """)
        
else:
    # --- PÁGINA DE LOGIN (SI NO ESTÁ LOGUEADO) ---
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("Autenticación Requerida")
        st.write("Por favor, ingresa la contraseña para acceder a la plataforma.")

        try:
            correct_password = st.secrets["app_password"]["password"]
        except Exception as e:
            st.error("Error: La contraseña no está configurada en '.streamlit/secrets.toml'.")
            st.stop()

        with st.form("login_form"):
            password = st.text_input("Contraseña:", type="password")
            submitted = st.form_submit_button("Ingresar")

            if submitted:
                if password == correct_password:
                    st.session_state['authenticated'] = True
                    st.rerun() 
                else:
                    st.error("Contraseña incorrecta. Por favor, inténtalo de nuevo.")