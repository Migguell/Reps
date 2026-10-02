import re
import smtplib
import logging
from typing import Dict, Any
from email.message import EmailMessage

from core.config import get_env

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_placeholder(val: str) -> bool:
    return not val or "your_" in val or "your_email" in val


def is_valid_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def send_lead_email(to_email: str) -> Dict[str, Any]:
    if not is_valid_email(to_email):
        raise ValueError("Endereço de e-mail inválido.")

    smtp_server = get_env("SMTP_SERVER", "smtp.gmail.com")
    smtp_port_raw = get_env("SMTP_PORT", "587")
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_username = get_env("SMTP_USERNAME")
    smtp_password = get_env("SMTP_PASSWORD")
    from_email = get_env("SMTP_FROM_EMAIL", smtp_username)

    if _is_placeholder(smtp_username) or _is_placeholder(smtp_password):
        raise ValueError("Credenciais de SMTP (SMTP_USERNAME ou SMTP_PASSWORD) não configuradas no ambiente.")

    msg = EmailMessage()
    msg["Subject"] = "Hello World"
    msg["From"] = from_email
    msg["To"] = to_email.strip()
    msg.set_content("Hello World")
    msg.add_alternative("<p>Hello World</p>", subtype="html")

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

        return {
            "status": "sent",
            "to": to_email.strip()
        }
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro de autenticação SMTP: {str(e)}")
        raise RuntimeError("Falha de autenticação no servidor de e-mail. Verifique o usuário e a senha de app.")
    except Exception as e:
        logger.error(f"Erro ao disparar e-mail via SMTP: {str(e)}")
        raise RuntimeError(f"Falha no envio do e-mail: {str(e)}")
