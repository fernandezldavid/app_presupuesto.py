import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# 1. Configuración visual y Logo
st.set_page_config(page_title="Presupuesto - Solo Ana", page_icon="💶")

if os.path.exists("logo.png"):
    st.image("logo.png", width=200)

st.title("💶 Gestión de Presupuesto y Albaranes")
st.write("Registro de gastos para envío directo a la profesora Ana.")

# 2. Base de datos temporal
if "datos_gasto" not in st.session_state:
    st.session_state.datos_gasto = []

# 3. Formulario de entrada
with st.form("form_presupuesto", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        n_albaran = st.text_input("Número de Albarán:")
        fecha = st.date_input("Fecha", value=datetime.today())
        trabajador = st.text_input("Trabajador:")
    with col2:
        partida = st.selectbox("Partida:", ["Mecanismos", "Cableado", "Cuadros", "Iluminación", "Domótica", "Varios"])
        gasto = st.number_input("Importe (€):", min_value=0.0, step=0.01)
    
    comentarios = st.text_area("Comentarios:")
    foto = st.file_uploader("📸 Foto del Albarán", type=["jpg", "png", "jpeg"])
    
    btn_guardar = st.form_submit_button("Registrar Gasto")

# 4. Guardar datos en la tabla
if btn_guardar:
    if not n_albaran or not trabajador:
        st.error("❌ Por favor, rellena el Número de Albarán y el Nombre.")
    else:
        registro = {
            "Albarán": n_albaran,
            "Fecha": fecha.strftime("%d/%m/%Y"),
            "Trabajador": trabajador,
            "Partida": partida,
            "Euros": gasto,
            "Comentarios": comentarios
        }
        st.session_state.datos_gasto.append(registro)
        st.success("✅ Registro guardado en la tabla.")

# 5. Visualización y Envío
if st.session_state.datos_gasto:
    df = pd.DataFrame(st.session_state.datos_gasto)
    st.dataframe(df)
    
    # Generar Excel en memoria
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    
    st.download_button("📥 Descargar Excel", buf, "presupuesto_obra.xlsx")

    # BOTÓN DE ENVÍO SOLO A ANA
    if st.button("📨 Enviar Reporte a Ana"):
