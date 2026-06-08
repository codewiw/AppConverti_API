import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email_otp(email_destino: str, codigo_otp: str, nome_utilizador: str):
    sender_email = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = "O seu código de verificação Converti"
    message["From"] = sender_email
    message["To"] = email_destino

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2>Olá, {nome_utilizador}! Bem-vindo à Converti.</h2>
        <p>Para ativar a sua conta, utilize o código de segurança abaixo:</p>
        <h1 style="color: #fb6107; font-size: 36px; letter-spacing: 5px;">{codigo_otp}</h1>
        <p>Este código expira em 10 minutos.</p>
      </body>
    </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls() # Inicia a ligação segura
            server.login(sender_email, password)
            server.sendmail(sender_email, email_destino, message.as_string())
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def enviar_email_recuperacao(email_destino: str, codigo_otp: str, nome_usuario: str):
    sender_email = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Recuperação de Senha - Converti"
    message["From"] = sender_email
    message["To"] = email_destino

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2>Olá, {nome_usuario}.</h2>
        <p>Recebemos um pedido para redefinir a senha da sua conta Converti.</p>
        <p>Utilize o código de segurança abaixo para criar uma nova senha:</p>
        <h1 style="color: #fb6107; font-size: 36px; letter-spacing: 5px;">{codigo_otp}</h1>
        <p>Este código expira em 10 minutos.</p>
        <p style="font-size: 12px; color: #999;">Se não solicitou esta alteração, por favor ignore este e-mail.</p>
      </body>
    </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, email_destino, message.as_string())
    except Exception as e:
        print(f"Erro ao enviar email de recuperação: {e}")