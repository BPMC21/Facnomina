# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA (Título amigable) ---
st.set_page_config(page_title="crmnominafactura - Tu Compañero Financiero", layout="wide", page_icon="🌿")

# --- CONTROL DE SESIÓN Y TEMAS (Nombres más cercanos) ---
if "tema_amigable" not in st.session_state:
    st.session_state["tema_amigable"] = "Fica Lúa (Noche Cálida) 🌕"

TEMAS = {
    "Fica Lúa (Noche Cálida) 🌕": {
        "bg": "#111418", "text": "#e0e6ed", "accent": "#f1c40f", 
        "sidebar": "#1a1f26", "card": "#1c2129", "input_bg": "#111418"
    },
    "Terra (Día Orgánico) 🌱": {
        "bg": "#fdfdfb", "text": "#34495e", "accent": "#27ae60", 
        "sidebar": "#f4f7f6", "card": "#ffffff", "input_bg": "#f4f7f6"
    },
    "Serea (Verano Suave) 🏖️": {
        "bg": "#fefaf3", "text": "#5d4037", "accent": "#e67e22", 
        "sidebar": "#fff3e0", "card": "#fffdfa", "input_bg": "#fff3e0"
    }
}

t = TEMAS[st.session_state["tema_amigable"]]

# --- INYECCIÓN DE ESTILOS CSS (Soft-UI, Adaptable y Amigable) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Quicksand', sans-serif;
        background-color: {t['bg']};
        color: {t['text']};
    }}

    .stApp {{ background-color: {t['bg']}; }}
    
    /* Barra lateral con bordes suaves */
    div[data-testid="stSidebar"] {{ 
        background-color: {t['sidebar']} !important; 
        border-right: 1px solid rgba(255,255,255,0.05);
    }}
    
    /* Tarjetas KPIs con sombra suave y bordes redondeados */
    .kpi-card {{
        background-color: {t['card']};
        padding: 25px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.03);
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }}
    .kpi-card:hover {{ transform: translateY(-5px); }}
    .kpi-card h3 {{ color: {t['text']} !important; opacity: 0.8; font-size: 16px; margin-bottom: 5px; }}
    .kpi-card h2 {{ color: {t['accent']} !important; font-size: 36px; font-weight: 700; margin: 0; }}

    /* Títulos amigables */
    h1, h2, h3 {{ 
        color: {t['text']} !important; 
        font-weight: 700 !important; 
        letter-spacing: -0.5px;
    }}
    h1 {{ border-bottom: 2px solid {t['accent']}; padding-bottom: 10px; }}

    /* Botones suaves y modernos */
    .stButton>button {{
        background-color: {t['accent']} !important;
        color: #111418 !important;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{ 
        background-color: {t['accent']}e6 !important; 
        transform: translateY(-2px); 
        box-shadow: 0 6px 15px rgba(0,0,0,0.2);
    }}

    /* Estilo de inputs */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="date-picker"] {{
        background-color: {t['input_bg']} !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
    }}
    
    /* Contenedor de info amigable */
    .stAlert {{
        background-color: {t['card']} !important;
        border-radius: 15px !important;
        border: 1px solid {t['accent']}33 !important;
        color: {t['text']} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE CÁLCULO DE RETENCIONES (IRPF Progresivo 2024/25) ---
def calcular_irpf_estimado(bruto_anual):
    """Calcula el porcentaje de retención recomendado según tramos españoles"""
    if bruto_anual <= 12450: return 19.0
    elif bruto_anual <= 20200: return 24.0
    elif bruto_anual <= 35200: return 30.0
    elif bruto_anual <= 60000: return 37.0
    elif bruto_anual <= 300000: return 45.0
    else: return 47.0

# --- BASE DE DATOS NOMBRADA COMO crmnominafactura ---
DB_NAME = "crmnominafactura_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        tipo TEXT,
        concepto TEXT,
        bruto REAL,
        base_cotizacion REAL,
        seguridad_social REAL,
        irpf_porcentaje REAL,
        neto REAL,
        periodo TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# --- BARRA LATERAL (Más ordenada y limpia) ---
st.sidebar.markdown(f"<h1 style='text-align:center; color:{t['accent']} !important; font-size:28px; border:none;'>🌿 crmnominafactura</h1>", unsafe_allow_html=True)
st.sidebar.write("---")

st.sidebar.subheader("🎨 Tu Entorno Visual")
tema_anterior = st.session_state["tema_amigable"]
st.session_state["tema_amigable"] = st.sidebar.selectbox("Elige cómo te sientes hoy", list(TEMAS.keys()), index=list(TEMAS.keys()).index(tema_anterior))
if st.session_state["tema_amigable"] != tema_anterior:
    st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("⚙️ Ajustes Automáticos")
st.sidebar.caption("Configura los valores por defecto para tus cálculos.")
porc_ss = st.sidebar.slider("Cotización SS (%)", 6.35, 6.55, 6.45, help="El valor estándar para el trabajador suele estar aquí.")

st.sidebar.write("---")
st.sidebar.caption("Desarrollado con ❤️ para tu tranquilidad financiera.")

# --- INTERFAZ PRINCIPAL ---
st.title("🤝 Tu Gestor Financiero Personal")
st.markdown("Bienvenido. Vamos a poner orden en tus números de la forma más sencilla posible.")

tab1, tab2, tab3 = st.tabs(["📝 Introducir Datos", "📊 Ver Mi Progreso", "📂 Historial y Cargas"])

with tab1:
    st.markdown("### ¿Qué documento vamos a registrar hoy?")
    st.write("Rellena los datos a continuación. Calcularemos todo automáticamente para ti.")
    
    with st.form("form_entrada", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo = st.selectbox("Tipo de Documento", ["Nómina Recibida", "Factura Emitida (Autónomo)", "Pago Varios"])
            concepto = st.text_input("Concepto o Pagador", placeholder="Ej: Nómina Junio / Cliente ABC")
            fecha = st.date_input("Fecha", value=datetime.now())
            periodo = st.text_input("Mes / Año", value=datetime.now().strftime("%m/%Y"), help="Ej: 06/2024")

        with col2:
            bruto = st.number_input("Importe Bruto (€)", min_value=0.0, step=10.0, help="El total antes de impuestos.")
            base_cot = st.number_input("Base de Cotización (€)", min_value=0.0, value=bruto, help="Suele coincidir con el bruto en nóminas sencillas.")
            
            # Cálculo Sugerido e Inteligente
            ss_deduccion = (base_cot * porc_ss) / 100
            irpf_recomendado = calcular_irpf_estimado(bruto * 12) # Proyección básica anual
            irpf_manual = st.number_input("IRPF Aplicado (%)", value=irpf_recomendado, help=f"Sugerimos un {irpf_recomendado}% basado en tu bruto proyectado.")
            
            irpf_deduccion = (bruto * irpf_manual) / 100
            neto = bruto - ss_deduccion - irpf_deduccion

        st.markdown("---")
        st.info(f"✨ **Resumen del cálculo suguerido:** De un bruto de {bruto:.2f}€, estimamos una deducción de SS de **{ss_deduccion:.2f}€** y un IRPF de **{irpf_deduccion:.2f}€** ({irpf_manual}%). Tu Neto sería de **{neto:.2f}€**. *¡Revisa los datos antes de guardar!*")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
        with col_btn2:
            submit_btn = st.form_submit_button("💾 Guardar Registro en Mi Historial")

    if submit_btn:
        if concepto and bruto > 0:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO registros (fecha, tipo, concepto, bruto, base_cotizacion, seguridad_social, irpf_porcentaje, neto, periodo) VALUES (?,?,?,?,?,?,?,?,?)",
                      (fecha.strftime("%Y-%m-%d"), tipo, concepto, bruto, base_cot, ss_deduccion, irpf_manual, neto, periodo))
            conn.commit()
            conn.close()
            st.balloons()
            st.success(f"✅ ¡Genial! He guardado '{concepto}' en tu historial.")
        else:
            st.error("⚠️ Ocurrió un error. Asegúrate de poner un concepto y un importe bruto mayor que cero.")

with tab2:
    st.markdown("### ¿Cómo van mis números?")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.sort_values(by='fecha')

        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.markdown(f"<div class='kpi-card'><h3>💰 Total Ingresado (Bruto)</h3><h2>{df['bruto'].sum():,.2f}€</h2></div>", unsafe_allow_html=True)
        with col_kpi2:
            total_impuestos = df['seguridad_social'].sum() + (df['bruto'] * df['irpf_porcentaje']/100).sum()
            st.markdown(f"<div class='kpi-card'><h3>💸 Total Impuestos Pagados</h3><h2>{total_impuestos:,.2f}€</h2></div>", unsafe_allow_html=True)
        with col_kpi3:
            st.markdown(f"<div class='kpi-card'><h3>🏦 Total Neto (En Cuenta)</h3><h2>{df['neto'].sum():,.2f}€</h2></div>", unsafe_allow_html=True)

        st.write("---")
        
        # Gráfico amigable y claro
        st.markdown("#### Evolución de mis Ingresos Brutos vs Netos")
        df_melt = df.melt(id_vars=['periodo', 'fecha'], value_vars=['bruto', 'neto'], var_name='Tipo', value_name='Importe')
        fig = px.line(df_melt, x="fecha", y="Importe", color="Tipo", markers=True,
                     color_discrete_sequence=[t['accent'], "#94a3b8"])
        
        # Personalización del gráfico para que sea más "real" y menos "corporativo"
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color=t['text'], title_font_size=20,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Importe (€)")
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("👋 ¡Aún no hay registros! Ve a la pestaña 'Introducir Datos' para empezar a ver gráficos aquí.")

with tab3:
    st.markdown("### Gestión de Datos Masivos y Borrado")
    
    col_upload, col_empty = st.columns([2,1])
    with col_upload:
        st.markdown("#### 📥 Importar desde Excel o CSV")
        st.write("Sube un archivo con tus datos antiguos para integrarlos rápidamente.")
        archivo = st.file_uploader("Arrastra tu archivo aquí", type=["xlsx", "csv"])
        
        if archivo:
            st.info("Función de importación masiva detectada. Vista previa disponible pronto.")
            # Lógica simplificada de importación
            if st.button("Confirmar Importación Masiva"):
                st.success("Esta función se activará en la próxima actualización.")

    st.write("---")
    st.markdown("#### 📂 Mi Histórico Completo")
    if not df.empty:
        # Dataframe con estilo suave
        st.dataframe(df, use_container_width=True)
        
        col_actions1, col_actions2, col_actions3 = st.columns([1,1,1])
        
        with col_actions1:
            # Exportar a Excel nombrado como crmnominafactura
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Historial Pagos', index=False)
            st.download_button("📥 Descargar Mi Historial (Excel)", data=output.getvalue(), file_name="crmnominafactura.xlsx")
            
        with col_actions3:
            # Opción de Borrar con confirmación suave
            if st.button("🗑️ Vaciar Todo Mi Historial"):
                if st.checkbox("Estoy seguro de que quiero borrar TODO", value=False):
                    conn = sqlite3.connect(DB_NAME)
                    conn.cursor().execute("DELETE FROM registros")
                    conn.commit()
                    conn.close()
                    st.success("Historial vaciado. Empezamos de cero.")
                    st.rerun()
                else:
                    st.warning("⚠️ Por seguridad, marca la casilla de confirmación para borrar.")
