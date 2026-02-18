# Email Sender - SMTP for TensorMarketData

import os
import smtplib
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", SMTP_USER)
PHYSICAL_ADDRESS = os.getenv("PHYSICAL_ADDRESS", "").strip()


class EmailSendError(RuntimeError):
    pass


def classify_smtp_error(e: Exception) -> Dict[str, Any]:
    """Classify SMTP error as hard bounce, soft bounce, or other."""
    code = getattr(e, "smtp_code", None)
    err = getattr(e, "smtp_error", b"") or b""
    
    if isinstance(err, (bytes, bytearray)):
        msg = err.decode("utf-8", errors="replace")
    else:
        msg = str(err)
    
    # Hard bounces (permanent failures)
    if code in (550, 551, 552, 553, 554):
        return {"bounce": True, "bounce_type": "hard", "code": code, "reason": msg[:300]}
    
    # Soft bounces (temporary failures)
    if code in (421, 450, 451, 452):
        return {"bounce": True, "bounce_type": "soft", "code": code, "reason": msg[:300]}
    
    return {"bounce": False, "code": code, "reason": msg[:300]}


def send_email_smtp(*, to_email: str, subject: str, body_text: str) -> Dict[str, Any]:
    """
    Send email via SMTP.
    Returns: {"ok": True} on success, or {"ok": False, "bounce": True/False, "code": ..., "reason": ...}
    """
    if not (SMTP_USER and SMTP_PASS):
        return {"ok": False, "bounce": False, "code": None, "reason": "SMTP_USER/SMTP_PASS not set"}
    
    if not PHYSICAL_ADDRESS:
        return {"ok": False, "bounce": False, "code": None, "reason": "PHYSICAL_ADDRESS not set"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=25) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        return {"ok": True}
    except smtplib.SMTPResponseException as e:
        info = classify_smtp_error(e)
        return {"ok": False, **info}
    except Exception as e:
        return {"ok": False, "bounce": False, "code": None, "reason": str(e)[:300]}
