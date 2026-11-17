import poplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
import time
import re

# ================= CONFIGURACIÓN =================
# Cuenta de correo (para recibir y enviar)
EMAIL_USER = "tu_correo@ejemplo.com"
EMAIL_PASS = "tu_contraseña_o_autorizacion"
POP3_SERVER = "pop.ejemplo.com"  # Servidor de entrada
SMTP_SERVER = "smtp.ejemplo.com" # Servidor de salida
SMTP_PORT = 587                  # 587 para TLS, 465 para SSL

# Reglas de respuesta: Palabra clave -> Plantilla de respuesta
# El script buscará estas palabras en el cuerpo o asunto del correo.
REGLAS = {
    "precio": "Gracias por tu interés. Nuestros precios están en la web oficial.",
    "soporte": "Hemos recibido tu solicitud de soporte. Un agente te contactará pronto.",
    "informacion": "Para más información, visita nuestra página de preguntas frecuentes."
}

# =================================================

def conectar_pop3():
    """Conecta al servidor POP3 de forma segura."""
    try:
        # Usamos POP3_SSL para el puerto 995 (estándar seguro)
        mail = poplib.POP3_SSL(POP3_SERVER)
        mail.user(EMAIL_USER)
        mail.pass_(EMAIL_PASS)
        return mail
    except Exception as e:
        print(f"Error conectando a POP3: {e}")
        return None

def enviar_respuesta(destinatario, asunto_original, cuerpo_respuesta):
    """Envía un correo de respuesta usando SMTP."""
    try:
        msg = MIMEText(cuerpo_respuesta, 'plain', 'utf-8')
        msg['Subject'] = f"Re: {asunto_original}"
        msg['From'] = EMAIL_USER
        msg['To'] = destinatario

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Iniciar cifrado
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"Respuesta enviada a: {destinatario}")
    except Exception as e:
        print(f"Error enviando correo a {destinatario}: {e}")

def procesar_correos():
    """Revisa el buzón, busca palabras clave y responde."""
    mail = conectar_pop3()
    if not mail:
        return

    try:
        # Obtener cantidad de mensajes
        num_mensajes = len(mail.list()[1])
        print(f"Mensajes en el buzón: {num_mensajes}")

        for i in range(1, num_mensajes + 1):
            # Descargar el mensaje completo
            respuesta, lineas, octetos = mail.retr(i)
            mensaje_crudo = b"\r\n".join(lineas)
            msg = email.message_from_bytes(mensaje_crudo)

            # Obtener asunto y remitente
            asunto, codificacion = decode_header(msg["Subject"])[0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(codificacion or "utf-8")
            
            remitente = msg.get("From")
            # Extraer solo el correo del remitente (ej. "Nombre <correo@dominio.com>")
            match = re.search(r'<(.+?)>', remitente)
            email_remitente = match.group(1) if match else remitente

            print(f"Revisando mensaje {i}: {asunto} de {email_remitente}")

            # Obtener el cuerpo del mensaje
            cuerpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        cuerpo = part.get_payload(decode=True).decode()
                        break
            else:
                cuerpo = msg.get_payload(decode=True).decode()

            # Buscar palabras clave en el asunto o cuerpo
            texto_completo = (asunto + " " + cuerpo).lower()
            
            for palabra, plantilla in REGLAS.items():
                if palabra in texto_completo:
                    print(f"Palabra clave '{palabra}' encontrada. Respondiendo...")
                    enviar_respuesta(email_remitente, asunto, plantilla)
                    # Nota: Podrías marcar el correo para borrar (mail.dele(i)) si quieres
                    break # Solo una respuesta por correo

    except Exception as e:
        print(f"Error procesando correos: {e}")
    finally:
        # Cerrar conexión (guarda los cambios si marcaste borrados)
        mail.quit()

if __name__ == "__main__":
    print("Iniciando monitor de correo...")
    # Bucle infinito para que se ejecute en el servidor
    while True:
        procesar_correos()
        print("Esperando 60 segundos para la siguiente revisión...")
        time.sleep(60) # Revisa cada minuto
