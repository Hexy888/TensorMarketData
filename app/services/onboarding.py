from datetime import datetime
from sqlmodel import Session, select
from app.models import Business, User, AuditLog
from app.security_magic import sign
from app.services.email_tx import send_template, support_email

def audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def create_workspace(session: Session, plan: str, business_name: str, approval_email: str, autopost_positive: bool) -> dict:
    # Create Business
    biz = Business(
        name=business_name,
        industry="HVAC",
        approval_email=approval_email,
        autopost_positive=bool(autopost_positive),
        gbp_connected=False,
    )
    session.add(biz)
    session.commit()
    session.refresh(biz)
    
    # Create or fetch User
    u = session.exec(select(User).where(User.email == approval_email)).first()
    if not u:
        u = User(email=approval_email, created_at=datetime.utcnow())
        session.add(u)
        session.commit()
        session.refresh(u)
    
    # Set default business
    u.default_business_id = biz.id
    session.add(u)
    session.commit()
    
    audit(session, biz.id, "onboarding_workspace_created", f"plan={plan} email={approval_email}")
    
    # Send welcome + magic link
    token = sign({"email": approval_email, "business_id": biz.id}, ttl_seconds=60*60)
    login_url = f"https://tensormarketdata.com/login/magic?token={token}"
    
    send_template(
        approval_email,
        "Welcome to TensorMarketData — connect Google Business Profile",
        "welcome.html",
        business=biz,
        login_url=login_url,
        support=support_email(),
    )
    
    return {"ok": True, "business_id": biz.id, "email": approval_email}
