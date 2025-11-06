import streamlit as st
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from tenacity import retry, stop_after_attempt, wait_fixed

# --- 0. MAPEADO DE NOMBRES DE PESTAÑAS ---
WORKSHEET_NAMES = {
    "rendimiento": {
        "personal": "Informacion",
        "comentarios": "Comentarios",
        "indicadores": "Valores"
    },
    "calculo": {
        "calculos": "Hoja 1",
        "promedios": "Promedios Mensuales" # <-- ¡¡AQUÍ ESTÁ EL CAMBIO!!
    }
}

# --- 1. CONEXIÓN (SOLO SE EJECUTA UNA VEZ) ---
@st.cache_resource
def connect_to_sheets():
    """Establece conexión con Google Sheets usando las credenciales."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh_rendimiento = gc.open_by_key(st.secrets["google_sheets"]["rendimiento_pro_key"])
        sh_calculo = gc.open_by_key(st.secrets["google_sheets"]["calculo_rendimiento_key"])
        return sh_rendimiento, sh_calculo
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        st.error("Verifica las 'keys' en secrets.toml y los permisos de 'Editor'.")
        return None, None

# --- FUNCIÓN DE BÚSQUEDA INTELIGENTE ---
def find_worksheet_by_name(spreadsheet, clean_name):
    """Busca una pestaña (worksheet) ignorando espacios en blanco."""
    all_worksheets = spreadsheet.worksheets()
    for ws in all_worksheets:
        if ws.title.strip() == clean_name:
            return ws
    raise gspread.exceptions.WorksheetNotFound(
        f"No se encontró la pestaña llamada '{clean_name}'. "
        f"Revisa el nombre en Google Sheet y en WORKSHEET_NAMES."
    )

# --- 2. LECTURA DE DATOS (ACTUALIZADO) ---
@st.cache_data(ttl=300) 
def get_data(sheet_key, data_key):
    """Obtiene datos de una hoja específica (usando la búsqueda inteligente)."""
    worksheet_name_clean = "desconocida" 
    try:
        sh_rendimiento, sh_calculo = connect_to_sheets()
        worksheet_name_clean = WORKSHEET_NAMES[sheet_key][data_key]
        
        if sheet_key == "rendimiento":
            worksheet = find_worksheet_by_name(sh_rendimiento, worksheet_name_clean)
        elif sheet_key == "calculo":
            worksheet = find_worksheet_by_name(sh_calculo, worksheet_name_clean)
        else:
            raise ValueError("Clave de hoja no válida.")

        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        df = df.dropna(how='all')
        return df
    
    except gspread.exceptions.WorksheetNotFound as e:
        st.error(str(e)) 
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al leer la hoja '{worksheet_name_clean}': {e}")
        return pd.DataFrame()

# --- 3. ESCRITURA DE DATOS (ACTUALIZADO) ---
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def update_dataframe_in_sheet(sheet_key, data_key, df):
    """Actualiza una hoja completa con un DataFrame de Pandas."""
    worksheet_name_clean = "desconocida"
    try:
        sh_rendimiento, sh_calculo = connect_to_sheets()
        worksheet_name_clean = WORKSHEET_NAMES[sheet_key][data_key]
        
        if sheet_key == "rendimiento":
            worksheet = find_worksheet_by_name(sh_rendimiento, worksheet_name_clean)
        elif sheet_key == "calculo":
            worksheet = find_worksheet_by_name(sh_calculo, worksheet_name_clean)
        else:
            raise ValueError("Clave de hoja no válida.")

        worksheet.clear() 
        set_with_dataframe(worksheet, df, include_index=False, resize=True)
        st.cache_data.clear() 
        return True
    
    except Exception as e:
        st.error(f"Error al actualizar la hoja '{worksheet_name_clean}' (reintentando...): {e}")
        raise e

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def append_row_to_sheet(sheet_key, data_key, data_list):
    """Agrega una NUEVA fila de datos."""
    worksheet_name_clean = "desconocida"
    try:
        sh_rendimiento, sh_calculo = connect_to_sheets()
        worksheet_name_clean = WORKSHEET_NAMES[sheet_key][data_key]
        
        if sheet_key == "rendimiento":
            worksheet = find_worksheet_by_name(sh_rendimiento, worksheet_name_clean)
        elif sheet_key == "calculo":
            worksheet = find_worksheet_by_name(sh_calculo, worksheet_name_clean)
        else:
            raise ValueError("Clave de hoja no válida.")
            
        worksheet.append_row(data_list)
        st.cache_data.clear() 
        return True
    
    except Exception as e:
        st.error(f"Error al agregar fila en '{worksheet_name_clean}' (reintentando...): {e}")
        raise e