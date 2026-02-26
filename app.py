import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE URLs ---
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbwnzafkbBVv7duqvjM-Es-a-RraAx3feLcdzC2wmjvA2wZmuQV2IKLDyt89G10BLoqQ/exec"
URL_HOJA_LECTURA = "https://docs.google.com/spreadsheets/d/1P29ZZqlcuYumUQj7uu6keFSdOGHVarVQ1aoS4pT8dhc/edit?usp=sharing"

st.set_page_config(page_title="Sistema CEDH - Captura", layout="wide")

# --- 2. DICCIONARIO DE INDICADORES ---
MENU_INDICADORES = {
    '1VG': {
        "7": "Expedientes de queja iniciados", "7.1": "Iniciados a petición de parte",
        "7.2": "Iniciados de manera oficiosa", "7.4": "Expedientes recibidos inter-turnados",
        "7.5": "Expedientes enviados inter-turnados", "10": "Expedientes de queja concluidos",
        "10.1": "Por haberse solucionado durante el trámite", "10.2": "Por conciliaciones",
        "10.3": "Por recomendaciones", "10.4": "Por otro tipo de conclusión",
        "13": "Medidas cautelares iniciadas", "14": "Medidas cautelares concluidas ", "17":"Recomendaciones emitidas"
    },
    '2VG': {
        "7": "Expedientes de queja iniciados", "7.1": "Iniciados a petición de parte",
        "7.2": "Iniciados de manera oficiosa", "7.4": "Expedientes recibidos inter-turnados",
        "7.5": "Expedientes enviados inter-turnados", "10": "Expedientes de queja concluidos",
        "10.1": "Por haberse solucionado durante el trámite", "10.2": "Por conciliaciones",
        "10.3": "Por recomendaciones", "10.4": "Por otro tipo de conclusión",
        "13": "Medidas cautelares iniciadas", "14": "Medidas cautelares concluidas ", "17":"Recomendaciones emitidas"
    },
    '3VG': {
        "2.6": "Personas atendidas en Centros de Reinserción Social e Internamiento de menores infractores",
        "7": "Expedientes de queja iniciados", "7.1": "Iniciados a petición de parte",
        "7.2": "Iniciados de manera oficiosa", "7.3": "Expedientes de queja iniciados en materia Penitenciaria",
        "7.4": "Expedientes recibidos inter-turnados", "7.5": "Expedientes enviados inter-turnados",
        "8": "Visitas de Supervisión Penitenciaria", "8.1": "Acciones del Mecanismo penitenciario (buzones)",
        "9.2": "Número de visitas a Separos de Seguridad Pública del Estado y Municipios",
        "10": "Expedientes de queja concluidos", "10.1": "Por haberse solucionado durante el trámite",
        "10.2": "Por conciliaciones", "10.3": "Por recomendaciones", "10.4": "Por otro tipo de conclusión",
        "13": "Medidas cautelares iniciadas", "13.1": "Medidas cautelares iniciadas con motivos de asuntos penitenciarios",
        "14": "Medidas cautelares concluidas ", "17":"Recomendaciones emitidas"
    },
    'DORQ': { "2.1": "Atención Oficinas Centrales", "6.1": "Orientaciones", "9": "Prevención Tortura" },
    'CAV': { "15": "Atención Víctimas", "17": "Protocolos Estambul" }
}

# --- 3. FUNCIONES DE BASE DE DATOS ---
def conectar_y_leer():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA_LECTURA)
        return df
    except:
        return pd.DataFrame()

def obtener_valor_previo(df, año, mes, area, id_ind):
    if df is None or df.empty or 'año' not in df.columns: return 0.0
    filtro = df[(df['año'] == año) & (df['mes'] == mes) & 
                (df['area'] == area) & (df['indicador_id'] == str(id_ind))]
    return float(filtro.iloc[-1]['valor']) if not filtro.empty else 0.0

def enviar_datos_a_google(datos_para_enviar):
    try:
        response = requests.post(URL_WEB_APP, data=json.dumps(datos_para_enviar), timeout=10)
        return response.status_code == 200
    except:
        return False

# --- 4. LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acceso Sistema CEDH")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Ingresar"):
            if os.path.exists("usuarios.xlsx"):
                df_u = pd.read_excel("usuarios.xlsx")
                match = df_u[(df_u['usuario'] == u) & (df_u['password'].astype(str) == str(p))]
                if not match.empty:
                    st.session_state['autenticado'] = True
                    st.session_state['user_data'] = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Credenciales incorrectas")
            else: st.error("No se encontró usuarios.xlsx")
    st.stop()
# --- 5. INTERFAZ PRINCIPAL ---

user = st.session_state['user_data']
area_user = user['area']

# Leemos el rol con limpieza de espacios y minúsculas para evitar errores (ej. "Admin " o "ADMIN")
rol_user = str(user.get('rol', 'usuario')).lower().strip() 

df_actual = conectar_y_leer()

# --- BARRA LATERAL (EL VISUALIZADOR IZQUIERDO) ---
with st.sidebar:
    st.title("📌 Panel CEDH")
    st.markdown(f"**Usuario:** {user['nombre']}")
    st.markdown(f"**Área:** {area_user}")
    st.markdown(f"**Perfil:** {rol_user.upper()}") # Para que tú confirmes qué rol detectó
    
    st.divider()
    
    if not df_actual.empty:
        st.subheader("👁️ Últimos Registros")
        resumen = df_actual[df_actual['area'] == area_user].tail(3)
        if not resumen.empty:
            st.dataframe(resumen[['mes', 'valor']], hide_index=True)
        else:
            st.caption("No hay datos previos de tu área.")
    
    if st.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

# --- NAVEGACIÓN PRINCIPAL ---
st.title(f"📊 Sistema de Indicadores")

# Generamos las opciones del menú basadas estrictamente en el ROL
opciones_navegacion = ["📝 Captura de Datos"]
if rol_user == "admin":
    opciones_navegacion.append("👑 Panel Super Administrador")

# Creamos el selector de sección
seccion = st.radio("Ir a:", opciones_navegacion, horizontal=True)

# --- SECCIÓN 1: CAPTURA ---
if seccion == "📝 Captura de Datos":
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    now = datetime.now()
    
    col1, col2 = st.columns(2)
    año_sel = col1.number_input("Año", value=now.year)
    mes_sel = col2.selectbox("Mes", meses, index=now.month - 1)

    indicadores = MENU_INDICADORES.get(area_user, {})
    with st.form(key="mi_formulario_captura"):
        st.info(f"Capturando: {area_user} - {mes_sel}")
        inputs = {}
        cols = st.columns(2)
        for i, (id_ind, nombre) in enumerate(indicadores.items()):
            val_previo = obtener_valor_previo(df_actual, año_sel, mes_sel, area_user, id_ind)
            with cols[i % 2]:
                inputs[id_ind] = st.number_input(f"({id_ind}) {nombre}", min_value=0.0, value=val_previo, step=1.0)
        
        if st.form_submit_button("💾 GUARDAR EN LA NUBE"):
            lista_para_enviar = []
            fecha_reg = datetime.now().strftime("%Y-%m-%d %H:%M")
            for id_ind, valor in inputs.items():
                lista_para_enviar.append({
                    "fecha_registro": fecha_reg, "año": año_sel, "mes": mes_sel,
                    "area": area_user, "indicador_id": str(id_ind),
                    "nombre_indicador": indicadores[id_ind], "valor": valor
                })
            
            if enviar_datos_a_google(lista_para_enviar):
                st.success("¡Datos enviados con éxito!")
                st.balloons()
            else:
                st.error("Error al enviar. Revisa la conexión.")

# --- SECCIÓN 2: SUPER ADMIN ---
elif seccion == "👑 Panel Super Administrador":
    # Doble validación de seguridad
    if rol_user != "admin":
        st.error("⛔ Acceso denegado. No tienes permisos de administrador.")
        st.stop()
    
    st.header("⚡ Tablero de Control Global")
    
    if not df_actual.empty:
        with st.expander("🔍 Filtros de Visualización"):
            col_f1, col_f2 = st.columns(2)
            areas_disponibles = sorted(df_actual['area'].unique())
            meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                           "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            
            filtro_area = col_f1.multiselect("Filtrar por Área", options=areas_disponibles, default=areas_disponibles)
            filtro_mes = col_f2.multiselect("Filtrar por Mes", options=meses_orden, default=df_actual['mes'].unique())

        df_filtrado = df_actual[(df_actual['area'].isin(filtro_area)) & (df_actual['mes'].isin(filtro_mes))]

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Registros", len(df_filtrado))
        m2.metric("Suma Total Valores", f"{df_filtrado['valor'].sum():,.0f}")
        m3.metric("Áreas Activas", len(df_filtrado['area'].unique()))

        st.divider()

        # Gráficas
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📊 Registros por Área")
            conteo_area = df_filtrado.groupby('area').size().reset_index(name='registros')
            st.bar_chart(conteo_area, x="area", y="registros", color="area")

        with col_g2:
            st.subheader("📈 Evolución Mensual")
            df_filtrado['mes_idx'] = df_filtrado['mes'].apply(lambda x: meses_orden.index(x) if x in meses_orden else 0)
            tendencia = df_filtrado.groupby(['mes_idx', 'mes'])['valor'].sum().reset_index().sort_values('mes_idx')
            st.line_chart(tendencia, x="mes", y="valor")

        st.subheader("📋 Detalle de Movimientos")
        st.dataframe(df_filtrado.drop(columns=['mes_idx'], errors='ignore'), use_container_width=True, hide_index=True)
        
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "reporte_cedh.csv", "text/csv")
    else:
        st.warning("⚠️ No hay datos almacenados en la nube.")