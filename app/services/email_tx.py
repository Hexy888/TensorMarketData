import os
from app.services.email_smtp import send_smtp_email
from app.services.email_templates import render_email

def send_template(to_email: str, subject: str, template: str, **ctx) -> bool:
    brand = ctx.get("brand", "TensorMarketData")
    ctx["brand"] = brand
    html = render_email(template, **ctx)
    return send_smtp_email(to_email, subject, html)

def support_email() -> str:
    return os.getenv("ALERT_FROM_EMAIL", "support@tensormarketdata.com")
