import os
from app.config import settings

def send_email(to_email: str, subject: str, html: str) -> None:
    api_key = os.getenv("SENDGRID_API_KEY", "")
    from_email = os.getenv("SEND_FROM_EMAIL", settings.send_from_email)
    
    if not api_key:
        # safe fallback for dev
        print("--------------------------------------------------")
        print(f"[EMAIL FALLBACK] FROM: {from_email}")
        print(f"[EMAIL FALLBACK] TO: {to_email}")
        print(f"[EMAIL FALLBACK] SUBJ: {subject}")
        print("[EMAIL FALLBACK] BODY:")
        print(html)
        print("--------------------------------------------------")
        return
    
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html,
    )
    SendGridAPIClient(api_key).send(message)
