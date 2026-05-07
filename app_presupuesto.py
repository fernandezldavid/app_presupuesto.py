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
st.set_page_config(page_title="Presupuesto Masaveu", page_icon="💶")

if os.path.exists("logo.png"):
    st.image("logo.png", width=200)

st.title("💶 Gestión de Presupuesto y Albaranes")
st.write("Registra gastos y envía evidencias fotográficas a jefatura de obra.")

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
        st.success("✅ Registro guardado temporalmente.")

# 5. Visualización y Envío
if st.session_state.datos_gasto:
    df = pd.DataFrame(st.session_state.datos_gasto)
    st.dataframe(df)
    
    # Generar Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    
    st.download_button("📥 Descargar Excel", buf, "presupuesto_obra.xlsx")

    if st.button("📨 Enviar Reporte a Ana y Jefatura"):
        try:
            # DATOS DESDE SECRETS
            emisor = st.secrets["correo_alumno"]
            password = st.secrets["contrasena_aplicacion"]
            profe_1 = st.secrets["correo_profesora"] # fmo@fundacionmasaveu.com
            
            # LISTA DE DESTINATARIOS
            # Aquí añadimos directamente a Ana
            destinatarios = [profe_1, "ana@fundacionmasaveu.com", emisor]
            
            msg = MIMEMultipart()
            msg['Subject'] = f"Nuevo Albarán Obra: {n_albaran} - {trabajador}"
            msg['From'] = emisor
            msg['To'] = ", ".join(destinatarios)
            
            cuerpo = f"Se ha registrado un nuevo gasto de obra.\n\n" \
                     f"Trabajador: {trabajador}\n" \
                     f"Importe: {gasto}€\n" \
                     f"Partida: {partida}\n" \
                     f"Comentarios: {comentarios}"
            msg.attach(MIMEText(cuerpo, 'plain'))
            
            # Adjuntar Excel
            adjunto_excel = MIMEBase('application', 'octet-stream')
            adjunto_excel.set_payload(buf.getvalue())
            encoders.encode_base64(adjunto_excel)
            adjunto_excel.add_header('Content-Disposition', 'attachment; filename="presupuesto.xlsx"')
            msg.attach(adjunto_excel)
            
            # Adjuntar Foto si existe
            if foto is not None:
                adjunto_foto = MIMEBase('image', 'jpeg')
                adjunto_foto.set_payload(foto.getvalue())
                encoders.encode_base64(adjunto_foto)
                adjunto_foto.add_header('Content-Disposition', f'attachment; filename="albaran_{n_albaran}.jpg"')
                msg.attach(adjunto_foto)
            
            # Conexión Servidor
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(emisor, password)
            server.sendmail(emisor, destinatarios, msg.as_string())
            server.quit()
            
            st.success(f"🚀 ¡Enviado con éxito a {len(destinatarios)-1} profesoras y copia para ti!")
        except Exception as e:
            st.error(f"❌ Error crítico: {e}")

