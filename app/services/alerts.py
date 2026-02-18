import os
from datetime import datetime
from app.services.email_smtp import send_smtp_email

def should_alert() -> bool:
    return os.getenv("ALERT_ON_FAIL", "true").lower() == "true"

def alert_to() -> str:
    return os.getenv("ALERT_TO_EMAIL", "")

def send_alert(subject: str, body_html: str) -> bool:
    if not should_alert():
        return False
    
    to_email = alert_to()
    if not to_email:
        return False
    
    full = f"""
    <div style="font-family:system-ui;line-height:1.5">
     <h2 style="margin:0 0 8px">TensorMarketData Alert</h2>
     <div style="color:#475569;margin-bottom:14px">UTC: {datetime.utcnow().isoformat()}Z</div>
     {body_html}
    </div>
    """
    return send_smtp_email(to_email, subject, full)
