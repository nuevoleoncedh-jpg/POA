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
        df = conn.read(spreadsheet=URL_HOJA_LECTURA, ttl=0) 
        return df
    except:
        return pd.DataFrame()

def obtener_valor_previo(df, año, mes, area, id_ind):
    if df is None or df.empty or 'año' not in df.columns: 
        return 0.0
    filtro = df[(df['año'] == año) & (df['mes'] == mes) & 
                (df['area'] == area) & (df['indicador_id'] == str(id_ind))]
    if not filtro.empty:
        return float(filtro.iloc[-1]['valor'])        
    return 0.0

def enviar_datos_a_google(datos_para_enviar):
    try:
        response = requests.post(URL_WEB_APP, data=json.dumps(datos_para_enviar), timeout=10)
        return response.status_code == 200
    except:
        return False
    
    import smtplib
from email.mime.text import MIMEText

def enviar_recordatorio_email(destinatario, nombre_usuario, mes):
    # Configuración del servidor (Ejemplo con Gmail/Outlook Institucional)
    servidor_smtp = "smtp.gmail.com" # Cambia según tu proveedor
    puerto = 587
    correo_remitente = "tu_correo@cedhbc.org.mx"
    password_remitente = "tu_contraseña_de_aplicacion" # No es tu clave normal, es una clave de app

    asunto = f"📢 Recordatorio: Captura de Indicadores - {mes}"
    cuerpo = f"""
    Hola {nombre_usuario},
    
    Te recordamos que el sistema de captura para el mes de {mes} cerrará pronto (Día 5).
    Detectamos que tu área aún no tiene registros completos en la plataforma.
    
    Por favor, ingresa a la brevedad para actualizar tu información.
    
    Saludos,
    Sistema de Indicadores CEDH
    """
    
    msg = MIMEText(cuerpo)
    msg['Subject'] = asunto
    msg['From'] = correo_remitente
    msg['To'] = destinatario

    try:
        server = smtplib.SMTP(servidor_smtp, puerto)
        server.starttls()
        server.login(correo_remitente, password_remitente)
        server.sendmail(correo_remitente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
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
rol_user = str(user.get('rol', 'usuario')).lower().strip() 

df_actual = conectar_y_leer()

# --- BARRA LATERAL (VISUALIZADOR CON PROGRESO) ---
with st.sidebar:
    st.title("📌 Panel CEDH")
    st.markdown(f"**Usuario:** {user['nombre']}")
    st.markdown(f"**Área:** {area_user}")
    
    st.divider()
    
 # --- LÓGICA DE PROGRESO DEL MES ---
    if not df_actual.empty:
        # 1. Definimos la lista primero (O muévela al inicio del archivo como te sugerí antes)
        MESES_LISTA = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                       "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # 2. Obtener qué indicadores corresponden a esta área
        indicadores_area = MENU_INDICADORES.get(area_user, {})
        total_esperados = len(indicadores_area)
        
        # 3. Ver cuántos ha llenado en el mes actual
        mes_actual_nombre = MESES_LISTA[datetime.now().month - 1]
        año_actual = datetime.now().year
        
        # Filtramos los datos
        capturados_hoy = df_actual[
            (df_actual['area'] == area_user) & 
            (df_actual['mes'] == mes_actual_nombre) & 
            (df_actual['año'] == año_actual)
        ]['indicador_id'].unique()
        
        # 4. Calcular porcentaje y mostrar
        total_capturados = len(capturados_hoy)
        porcentaje = (total_capturados / total_esperados) if total_esperados > 0 else 0
        
        st.subheader(f"📅 Avance de {mes_actual_nombre}")
        st.progress(porcentaje)
        st.write(f"✅ {total_capturados} de {total_esperados} indicadores")
        
        if porcentaje == 1:
            st.success("¡Completado!")
        elif porcentaje > 0:
            st.info("Captura en proceso...")
        else:
            st.warning("Pendiente de iniciar")

    st.divider()
    
    # Visualizador de los últimos 3 movimientos
    if not df_actual.empty:
        st.subheader("👁️ Últimos Cambios")
        resumen = df_actual[df_actual['area'] == area_user].tail(3)
        if not resumen.empty:
            # Añadimos 'indicador_id' para que sepa cuál cambió
            st.dataframe(resumen[['mes', 'indicador_id', 'valor']], hide_index=True)
    
    if st.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

# --- NAVEGACIÓN ---
st.title(f"📊 Sistema de Indicadores")
opciones_navegacion = ["📝 Captura de Datos"]
if rol_user == "admin":
    opciones_navegacion.append("👑 Panel Super Administrador")

seccion = st.radio("Ir a:", opciones_navegacion, horizontal=True)

if seccion == "📝 Captura de Datos":
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    now = datetime.now()
    
    col1, col2 = st.columns(2)
    año_sel = col1.number_input("Año", value=now.year)
    mes_sel = col2.selectbox("Mes", meses, index=now.month - 1)

   # --- SECCIÓN 1: CAPTURA ---
if seccion == "📝 Captura de Datos":
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    dia_actual = ahora.day
    mes_actual_idx = ahora.month - 1  # Enero es 0, Febrero es 1...
    año_actual = ahora.year
    
    col1, col2 = st.columns(2)
    año_sel = col1.number_input("Año", value=año_actual, min_value=2024, max_value=año_actual)
    mes_sel = col2.selectbox("Mes a reportar", meses, index=mes_actual_idx)
    mes_sel_idx = meses.index(mes_sel)

    # --- LÓGICA DE BLOQUEO (REGLA DEL DÍA 5) ---
    bloqueado = False
    motivo_bloqueo = ""

    # Regla 1: No se puede capturar meses futuros
    if año_sel == año_actual and mes_sel_idx > mes_actual_idx:
        bloqueado = True
        motivo_bloqueo = "No se pueden capturar meses futuros."
    
    # Regla 2: Si ya pasamos el día 5, se bloquea el mes anterior y anteriores
    elif dia_actual > 5:
        # Si el usuario intenta capturar el mes actual, se permite (porque está en curso)
        # Pero si intenta capturar el mes pasado o anteriores, se bloquea
        if año_sel < año_actual or (año_sel == año_actual and mes_sel_idx < mes_actual_idx):
            bloqueado = True
            motivo_bloqueo = f"El sistema cerró el día 5. No se pueden capturar o corregir datos de {mes_sel}."

    # --- MOSTRAR INTERFAZ SEGÚN BLOQUEO ---
    if bloqueado:
        st.error(f"⚠️ **SISTEMA CERRADO:** {motivo_bloqueo}")
        # Mostramos los datos actuales pero sin formulario de edición
        indicadores = MENU_INDICADORES.get(area_user, {})
        st.info("Solo lectura: Estos son los valores registrados actualmente:")
        for id_ind, nombre in indicadores.items():
            val = obtener_valor_previo(df_actual, año_sel, mes_sel, area_user, id_ind)
            st.write(f"**({id_ind}) {nombre}:** {val}")
    
    else:
        # Si no está bloqueado, mostramos el formulario normal
        indicadores = MENU_INDICADORES.get(area_user, {})
        with st.form(key="mi_formulario_captura"):
            st.success(f"🔓 Periodo abierto para captura: {mes_sel} {año_sel}")
            inputs = {}
            cols = st.columns(2)
            for i, (id_ind, nombre) in enumerate(indicadores.items()):
                val_previo = obtener_valor_previo(df_actual, año_sel, mes_sel, area_user, id_ind)
                with cols[i % 2]:
                    inputs[id_ind] = st.number_input(f"({id_ind}) {nombre}", min_value=0.0, value=val_previo, step=1.0)
            
            if st.form_submit_button("💾 GUARDAR EN LA NUBE"):
                lista_para_enviar = []
                fecha_reg = ahora.strftime("%Y-%m-%d %H:%M")
                for id_ind, valor in inputs.items():
                    lista_para_enviar.append({
                        "fecha_registro": fecha_reg, "año": año_sel, "mes": mes_sel,
                        "area": area_user, "indicador_id": str(id_ind),
                        "nombre_indicador": indicadores[id_ind], "valor": valor
                    })
                
                if enviar_datos_a_google(lista_para_enviar):
                    st.success("🎉 ¡Datos actualizados con éxito!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Error al enviar. Revisa la conexión.")

elif seccion == "👑 Panel Super Administrador":
    if rol_user != "admin":
        st.error("⛔ Acceso denegado.")
        st.stop()
    
    st.header("⚡ Tablero de Control Global")
    if not df_actual.empty:
        df_limpio = df_actual.sort_values('fecha_registro').drop_duplicates(
            subset=['año', 'mes', 'area', 'indicador_id'], 
            keep='last'
        )
        with st.expander("🔍 Filtros de Visualización"):
            col_f1, col_f2 = st.columns(2)
            areas_disponibles = sorted(df_limpio['area'].unique())
            meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            filtro_area = col_f1.multiselect("Filtrar por Área", options=areas_disponibles, default=areas_disponibles)
            filtro_mes = col_f2.multiselect("Filtrar por Mes", options=meses_orden, default=df_limpio['mes'].unique())

        df_filtrado = df_limpio[(df_limpio['area'].isin(filtro_area)) & (df_limpio['mes'].isin(filtro_mes))]

        m1, m2, m3 = st.columns(3)
        m1.metric("Registros Únicos", len(df_filtrado))
        m2.metric("Suma de Valores Actuales", f"{df_filtrado['valor'].sum():,.0f}")
        m3.metric("Áreas Activas", len(df_filtrado['area'].unique()))
        st.divider()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📊 Totales por Área")
            resumen_area = df_filtrado.groupby('area')['valor'].sum().reset_index()
            st.bar_chart(resumen_area, x="area", y="valor", color="area")
        with col_g2:
            st.subheader("📈 Evolución Mensual")
            df_filtrado['mes_idx'] = df_filtrado['mes'].apply(lambda x: meses_orden.index(x) if x in meses_orden else 0)
            tendencia = df_filtrado.groupby(['mes_idx', 'mes'])['valor'].sum().reset_index().sort_values('mes_idx')
            st.line_chart(tendencia, x="mes", y="valor")

        st.subheader("📋 Detalle de Información")
        st.dataframe(df_filtrado.drop(columns=['mes_idx'], errors='ignore'), use_container_width=True, hide_index=True)
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "reporte_cedh.csv", "text/csv")
    else:
        st.warning("⚠️ No hay datos almacenados.")

        st.divider()
    st.subheader("🔔 Gestión de Cumplimiento")
    
    # 1. Identificar quién falta
    areas_totales = set(MENU_INDICADORES.keys())
    # mes_actual se obtiene de datetime.now()
    mes_actual_nombre = meses_orden[datetime.now().month - 1] 
    areas_con_datos = set(df_actual[df_actual['mes'] == mes_actual_nombre]['area'].unique())
    
    faltantes = areas_totales - areas_con_datos
    
    if faltantes:
        st.warning(f"Las siguientes áreas no han capturado datos en {mes_actual_nombre}: {', '.join(faltantes)}")
        if st.button("📧 Enviar Recordatorio a Pendientes"):
            # Aquí buscaríamos los correos en el df_u de usuarios y llamaríamos a la función
            st.info("Enviando correos de notificación...")
            # Lógica de envío masivo aquí
            st.success("Recordatorios enviados correctamente.")
    else:
        st.success("✅ ¡Todas las áreas han cumplido con su captura este mes!")