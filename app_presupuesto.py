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

# 1. Configuración visual
st.set_page_config(page_title="Control de Gastos - Masaveu", page_icon="💶")

if os.path.exists("logo.png"):
    st.image("logo.png", width=200)

st.title("💶 Seguimiento de Presupuesto")
st.info("Introduce los datos del albarán y adjunta una foto para el archivo digital.")

# 2. Base de datos temporal (mientras la web esté abierta)
if "datos_gasto" not in st.session_state:
    st.session_state.datos_gasto = []

# 3. Formulario de entrada
with st.form("form_presupuesto", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        n_albaran = st.text_input("Número de Albarán:")
        fecha = st.date_input("Fecha", value=datetime.today())
        trabajador = st.text_input("Nombre del Trabajador:")
    
    with col2:
        partida = st.selectbox("Partida del Presupuesto:", [
            "Mecanismos", "Cableado", "Cuadros Eléctricos", 
            "Iluminación", "Canalización", "Domótica", "Varios"
        ])
        gasto = st.number_input("Importe (€):", min_value=0.0, step=0.01)
    
    comentarios = st.text_area("Comentarios:")
    
    # Campo para la foto (Nota Extra)
    foto = st.file_uploader("📸 Foto del Albarán", type=["jpg", "png", "jpeg"])
    
    btn_guardar = st.form_submit_button("Registrar Gasto")

# 4. Lógica de guardado
if btn_guardar:
    if not n_albaran or not trabajador:
        st.error("Faltan campos obligatorios.")
    else:
        registro = {
            "Albarán": n_albaran,
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Trabajador": trabajador,
            "Partida": partida,
            "Euros": gasto,
            "Comentarios": comentarios
        }
        st.session_state.datos_gasto.append(registro)
        st.success("✅ Gasto registrado en la tabla inferior.")

# 5. Mostrar tabla y Botones de envío
if st.session_state.datos_gasto:
    df = pd.DataFrame(st.session_state.datos_gasto)
    st.dataframe(df)
    
    # Crear Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    
    st.download_button("📥 Descargar Excel", buf, "presupuesto.xlsx")

    if st.button("📨 Enviar por Correo a Profesoras"):
        try:
            # Sacamos los datos de los "Secrets" de Streamlit
            emisor = st.secrets["correo_alumno"]
            password = st.secrets["contrasena_aplicacion"]
            destinatarios = [st.secrets["correo_profesora"], "ana@fundacionmasaveu.com", emisor]
            
            msg = MIMEMultipart()
            msg['Subject'] = f"Nuevo Albarán Registrado: {n_albaran}"
            msg['From'] = emisor
            msg['To'] = ", ".join(destinatarios)
            
            cuerpo = f"Registro de gasto realizado por {trabajador}.\nPartida: {partida}\nImporte: {gasto}€"
            msg.attach(MIMEText(cuerpo, 'plain'))
            
            # Adjuntar Excel
            adjunto_excel = MIMEBase('application', 'octet-stream')
            adjunto_excel.set_payload(buf.getvalue())
            encoders.encode_base64(adjunto_excel)
            adjunto_excel.add_header('Content-Disposition', 'attachment; filename="presupuesto.xlsx"')
            msg.attach(adjunto_excel)
            
            # Adjuntar Foto si el usuario subió una
            if foto is not None:
                adjunto_foto = MIMEBase('image', 'jpeg')
                adjunto_foto.set_payload(foto.getvalue())
                encoders.encode_base64(adjunto_foto)
                adjunto_foto.add_header('Content-Disposition', f'attachment; filename="albaran_{n_albaran}.jpg"')
                msg.attach(adjunto_foto)
            
            # Enviar
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(emisor, password)
            server.sendmail(emisor, destinatarios, msg.as_string())
            server.quit()
            st.success("📧 Correo enviado con éxito.")
        except Exception as e:
            st.error(f"Error: {e}. ¿Has configurado los Secrets?")
