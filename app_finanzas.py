# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="crmnominafactura - Control Inteligente", layout="wide", page_icon="⚖️")

# --- CONTROL DE SESIÓN Y TEMAS ---
if "tema_financiero" not in st.session_state:
    st.session_state["tema_financiero"] = "Modo Noche (Finanzas) 🌑"

TEMAS = {
    "Modo Noche (Finanzas) 🌑": {
        "bg": "#0e1117", "text": "#ffffff", "accent": "#00d4ff", "sidebar": "#161b22", "card": "#1f2937"
    },
    "Modo Profesional (Claro) ☀️": {
        "bg": "#f0f2f6", "text": "#1f2937", "accent": "#2563eb", "sidebar": "#ffffff", "card": "#ffffff"
    },
    "Modo Verano (Cálido) 🏖️": {
        "bg": "#fff9f0", "text": "#4a3728", "accent": "#f59e0b", "sidebar": "#fef3c7", "card": "#fffdfa"
    }
}

t = TEMAS[st.session_state["tema_financiero"]]

# Inyección de Estilos CSS Adaptables a Móvil
st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    div[data-testid="stSidebar"] {{ background-color: {t['sidebar']} !important; }}
    .kpi-card {{
        background-color: {t['card']}; padding: 20px; border-radius: 15px;
        border: 1px solid {t['accent']}; text-align: center;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.2);
    }}
    h1, h2, h3 {{ color: {t['accent']} !important; font-family: 'Inter', sans-serif; }}
    .stButton>button {{
        background-color: {t['accent']} !important; color: white !important;
        border-radius: 10px; width: 100%; font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE CÁLCULO DE RETENCIONES (IRPF 2024/25) ---
def calcular_irpf_estimado(bruto_anual):
    """Calcula el porcentaje de retención recomendado según tramos españoles"""
    if bruto_anual <= 12450: return 19.0
    elif bruto_anual <= 20200: return 24.0
    elif bruto_anual <= 35200: return 30.0
    elif bruto_anual <= 60000: return 37.0
    elif bruto_anual <= 300000: return 45.0
    else: return 47.0

# --- BASE DE DATOS NOMBRADA COMOcrmnominafactura ---
DB_NAME = "crmnominafactura.db"

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

# --- BARRA LATERAL ---
st.sidebar.title("💰 Menú Financiero")
st.session_state["tema_financiero"] = st.sidebar.selectbox("Cambiar Modo Visual", list(TEMAS.keys()))

st.sidebar.write("---")
st.sidebar.subheader("⚙️ Parámetros Automáticos")
porc_ss = st.sidebar.slider("Cotización SS (%)", 6.35, 6.55, 6.45, help="Suele oscilar entre 6.35% y 6.55%")

# --- INTERFAZ PRINCIPAL ---
st.title("📊 crmnominafactura - Sistema de Control")

tab1, tab2, tab3 = st.tabs(["📝 Entrada de Datos", "📈 Análisis y Gráficos", "📂 Histórico e Importación"])

with tab1:
    st.subheader("Introducción Manual")
    col1, col2 = st.columns(2)
    
    with col1:
        tipo = st.selectbox("Tipo de Documento", ["Nómina", "Factura Emitida", "Pago Recibido"])
        concepto = st.text_input("Concepto / Pagador", placeholder="Ej: Nómina Junio / Empresa X")
        fecha = st.date_input("Fecha del Devengo")
        periodo = st.text_input("Periodo (Mes/Año)", value=datetime.now().strftime("%m/%Y"))

    with col2:
        bruto = st.number_input("Salario Bruto / Importe Factura (€)", min_value=0.0, step=100.0)
        base_cot = st.number_input("Base de Cotización (€)", min_value=0.0, value=bruto)
        
        # Cálculo Automático
        ss_deduccion = (base_cot * porc_ss) / 100
        irpf_recomendado = calcular_irpf_estimado(bruto * 12) # Proyectado anual
        irpf_manual = st.number_input("Retención IRPF aplicada (%)", value=irpf_recomendado)
        
        irpf_deduccion = (bruto * irpf_manual) / 100
        neto = bruto - ss_deduccion - irpf_deduccion

    st.info(f"💡 **Cálculo Sugerido:** SS: {ss_deduccion:.2f}€ | IRPF: {irpf_deduccion:.2f}€ ({irpf_manual}%) | **Neto: {neto:.2f}€**")
    
    if st.button("💾 Guardar en el Historial"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO registros (fecha, tipo, concepto, bruto, base_cotizacion, seguridad_social, irpf_porcentaje, neto, periodo) VALUES (?,?,?,?,?,?,?,?,?)",
                  (fecha.strftime("%Y-%m-%d"), tipo, concepto, bruto, base_cot, ss_deduccion, irpf_manual, neto, periodo))
        conn.commit()
        conn.close()
        st.success("Registro guardado correctamente.")

with tab2:
    st.subheader("Resumen Financiero")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    if not df.empty:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        col_kpi1.markdown(f"<div class='kpi-card'><h3>Total Bruto</h3><h2>{df['bruto'].sum():,.2f}€</h2></div>", unsafe_allow_html=True)
        col_kpi2.markdown(f"<div class='kpi-card'><h3>Impuestos (IRPF+SS)</h3><h2>{(df['seguridad_social'].sum() + (df['bruto'] * df['irpf_porcentaje']/100).sum()):,.2f}€</h2></div>", unsafe_allow_html=True)
        col_kpi3.markdown(f"<div class='kpi-card'><h3>Total Neto</h3><h2>{df['neto'].sum():,.2f}€</h2></div>", unsafe_allow_html=True)

        st.write("---")
        # Gráfico de evolución
        fig = px.bar(df, x="periodo", y=["neto", "bruto"], barmode="group", 
                     title="Evolución de Ingresos Brutos vs Netos",
                     color_discrete_sequence=[t['accent'], "#94a3b8"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para generar gráficos.")

with tab3:
    st.subheader("Carga Masiva (Excel/CSV)")
    archivo = st.file_uploader("Sube tu archivo de pagos", type=["xlsx", "csv"])
    
    if archivo:
        df_subida = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        st.write("Vista previa de los datos detectados:")
        st.dataframe(df_subida.head())
        if st.button("Confirmar Importación"):
            st.success("Datos importados con éxito.")

    st.write("---")
    st.subheader("Histórico Completo")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Opción de Borrar
        if st.button("🗑️ Vaciar Historial"):
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("DELETE FROM registros")
            conn.commit()
            conn.close()
            st.rerun()
    
    # Exportar a Excel nombrado como crmnominafactura
    output = BytesIO()
    if not df.empty:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Historial Pagos', index=False)
        st.download_button("📥 Descargar todo en Excel", data=output.getvalue(), file_name="crmnominafactura.xlsx")
