import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Integral CEDH", layout="wide")

# Diccionario Maestro de Indicadores
MENU_INDICADORES = {
    '2VG': {
        "7": "Expedientes de queja iniciados",
        "7.1": "Iniciados a petición de parte",
        "7.2": "Iniciados de manera oficiosa",
        "7.4": "Expedientes recibidos inter-turnados",
        "7.5": "Expedientes enviados inter-turnados",
        "10": "Expedientes de queja concluidos",
        "10.1": "Por haberse solucionado durante el trámite",
        "10.2": "Por conciliaciones",
        "10.3": "Por recomendaciones",
        "10.4": "Por otro tipo de conclusión",
        "13": "Medidas cautelares iniciadas",
        "14": "Medidas cautelares concluidas ",
        "17":"Recomendaciones emitidas"
    },
    'DORQ': {
        "2.1": "Atención Oficinas Centrales",
        "6.1": "Orientaciones",
        "9": "Prevención Tortura"
    },
    'CAV': {
        "15": "Atención Víctimas",
        "17": "Protocolos Estambul"
    }
}

# --- FUNCIONES DB ---
def init_db():
    conn = sqlite3.connect('indicadores_master.db')
    c = conn.cursor()
    # Añadimos ID único para poder borrar fácilmente
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_registro TEXT, 
                  año INTEGER, mes TEXT, area TEXT, 
                  indicador_id TEXT, nombre_indicador TEXT, valor REAL)''')
    conn.commit()
    conn.close()

def guardar_datos(año, mes, area, datos_dict):
    conn = sqlite3.connect('indicadores_master.db')
    c = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for id_ind, valor in datos_dict.items():
        nombre_ind = MENU_INDICADORES[area][id_ind]
        # Borramos el registro previo del mismo mes/año/indicador para no duplicar
        c.execute("DELETE FROM registros WHERE año=? AND mes=? AND area=? AND indicador_id=?", 
                  (año, mes, area, id_ind))
        # Insertamos el nuevo valor
        c.execute("INSERT INTO registros (fecha_registro, año, mes, area, indicador_id, nombre_indicador, valor) VALUES (?,?,?,?,?,?,?)", 
                  (fecha_hoy, año, mes, area, id_ind, nombre_ind, valor))
    conn.commit()
    conn.close()

def obtener_valor_previo(año, mes, area, indicador_id):
    conn = sqlite3.connect('indicadores_master.db')
    df = pd.read_sql_query("SELECT valor FROM registros WHERE año=? AND mes=? AND area=? AND indicador_id=?", 
                           conn, params=(año, mes, area, indicador_id))
    conn.close()
    return float(df.iloc[0]['valor']) if not df.empty else 0.0

# --- AUTENTICACIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Control de Acceso")
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
                else: st.error("Usuario/Contraseña incorrectos")
            else: st.error("Falta archivo usuarios.xlsx")
    st.stop()

# --- PROGRAMA PRINCIPAL ---
init_db()
user = st.session_state['user_data']
area_user = user['area']

with st.sidebar:
    st.success(f"Usuario: {user['nombre']}")
    st.info(f"Área: {area_user}")
    if st.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

# --- LÓGICA DE ADMINISTRADOR ---
if area_user == "ADMIN":
    st.title("👨‍✈️ Panel de Administración Global")
    
    tab_admin1, tab_admin2 = st.tabs(["📊 Visualización Global", "🗑️ Gestionar Registros"])
    
    with tab_admin1:
        conn = sqlite3.connect('indicadores_master.db')
        df_global = pd.read_sql_query("SELECT * FROM registros", conn)
        conn.close()

        if not df_global.empty:
            fig_admin = px.bar(df_global, x="mes", y="valor", color="area", barmode="group", title="Actividad por Área")
            st.plotly_chart(fig_admin, use_container_width=True)
            st.dataframe(df_global, use_container_width=True)
        else:
            st.info("Sin datos registrados.")

    with tab_admin2:
        st.subheader("Eliminar registros incorrectos")
        conn = sqlite3.connect('indicadores_master.db')
        df_edit = pd.read_sql_query("SELECT id, fecha_registro, area, mes, nombre_indicador, valor FROM registros", conn)
        conn.close()

        if not df_edit.empty:
            registro_a_borrar = st.selectbox("Seleccione el registro a eliminar (ID - Área - Mes - Indicador)", 
                                             options=df_edit.apply(lambda x: f"{x['id']} | {x['area']} | {x['mes']} | {x['nombre_indicador']}", axis=1))
            
            id_borrar = int(registro_a_borrar.split(" | ")[0])
            
            if st.button("Confirmar Eliminación Permanente", type="primary"):
                conn = sqlite3.connect('indicadores_master.db')
                c = conn.cursor()
                c.execute("DELETE FROM registros WHERE id=?", (id_borrar,))
                conn.commit()
                conn.close()
                st.warning(f"Registro {id_borrar} eliminado.")
                st.rerun()
        else:
            st.write("No hay registros para eliminar.")

# --- LÓGICA DE USUARIO DE ÁREA ---
else:
    st.title(f"📈 Gestión de Indicadores - {area_user}")
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    now = datetime.now()
    
    col1, col2 = st.columns(2)
    año_sel = col1.number_input("Año", value=now.year)
    mes_sel = col2.selectbox("Mes", meses, index=now.month - 1)

    tab1, tab2 = st.tabs(["📝 Captura y Edición", "📊 Mi Progreso"])
    
    with tab1:
        es_pasado = (meses.index(mes_sel) + 1) < now.month
        
        if es_pasado:
            st.error(f"🚫 El periodo {mes_sel} está cerrado. Solo lectura.")
        else:
            indicadores = MENU_INDICADORES.get(area_user, {})
            with st.form("captura_form"):
                st.write(f"### Datos registrados para {mes_sel}")
                inputs = {}
                cols = st.columns(2)
                
                for i, (id_ind, nombre) in enumerate(indicadores.items()):
                    # AQUÍ ESTÁ LA MAGIA: Busca el valor actual en la DB
                    valor_actual = obtener_valor_previo(año_sel, mes_sel, area_user, id_ind)
                    
                    with cols[i % 2]:
                        inputs[id_ind] = st.number_input(f"{id_ind}: {nombre}", 
                                                         min_value=0.0, 
                                                         value=valor_actual, # Carga el número registrado
                                                         step=1.0)
                
                if st.form_submit_button("Actualizar / Guardar Datos"):
                    guardar_datos(año_sel, mes_sel, area_user, inputs)
                    st.success("Datos actualizados correctamente.")
                    st.rerun()

    with tab2:
        conn = sqlite3.connect('indicadores_master.db')
        df_area = pd.read_sql_query(f"SELECT * FROM registros WHERE area='{area_user}'", conn)
        conn.close()
        if not df_area.empty:
            fig_area = px.line(df_area, x="mes", y="valor", color="nombre_indicador", markers=True)
            st.plotly_chart(fig_area, use_container_width=True)