from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from app.config import settings
from app.db import get_session
from app.tenant_models import Onboarding, Business, Subscription, User
from app.security import hash_password, make_magic_token
from app.services.email import send_email

templates = Jinja2Templates(directory="templates")
router = APIRouter()

def base_ctx(request: Request):
    return {"request": request, "brand": "TensorMarketData", "support_email": settings.support_email}

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("public/home.html", base_ctx(request))

@router.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request):
    return templates.TemplateResponse("public/pricing.html", base_ctx(request))

@router.get("/how-it-works", response_class=HTMLResponse)
def how(request: Request):
    return templates.TemplateResponse("public/how.html", base_ctx(request))

@router.get("/faq", response_class=HTMLResponse)
def faq(request: Request):
    return templates.TemplateResponse("public/faq.html", base_ctx(request))

@router.get("/get-started", response_class=HTMLResponse)
def get_started(request: Request):
    return templates.TemplateResponse("public/get_started.html", base_ctx(request))

@router.post("/get-started")
def get_started_submit(
    request: Request,
    plan: str = Form(...),  # A/B/C
    business_name: str = Form(...),
    approval_email: str = Form(...),
    autopost_positive: str = Form("off"),
    session: Session = Depends(get_session),
):
    plan = plan.strip().upper()
    business_name = business_name.strip()
    approval_email = approval_email.strip()
    auto = (autopost_positive == "on")
    
    # Create or fetch user for approval_email
    user = session.exec(select(User).where(User.email == approval_email)).first()
    if not user:
        user = User(email=approval_email, password_hash=hash_password("TEMP_PASSWORD_DO_NOT_USE"), created_at=datetime.utcnow())
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # Create a NEW business owned by this user
    biz = Business(
        owner_user_id=user.id,
        name=business_name,
        approval_email=approval_email,
        autopost_positive=auto,
        created_at=datetime.utcnow(),
    )
    session.add(biz)
    session.commit()
    session.refresh(biz)
    
    # Set user's default business
    user.default_business_id = biz.id
    session.add(user)
    session.commit()
    
    # Create subscription row (status becomes active once Stripe webhook confirms)
    sub = Subscription(business_id=biz.id, plan=plan, status="active", created_at=datetime.utcnow())
    session.add(sub)
    
    # Record onboarding
    ob = Onboarding(business_id=biz.id, business_name=business_name, approval_email=approval_email, plan=plan, created_at=datetime.utcnow())
    session.add(ob)
    session.commit()
    
    # Send magic link
    token = make_magic_token(approval_email)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    scheme = request.headers.get("x-forwarded-proto") or "http"
    link = f"{scheme}://{host}/magic-login?token={token}"
    
    send_email(
        to_email=approval_email,
        subject="Finish setup: sign in to TensorMarketData",
        html=f"<p>Your setup is ready for <b>{business_name}</b>.</p><p>Sign in (expires in 30 min):</p><p><a href='{link}'>{link}</a></p>",
    )
    
    return RedirectResponse("/login?sent=1", status_code=303)

@router.get("/blog", response_class=HTMLResponse)
def blog_index(request: Request):
    return templates.TemplateResponse("public/blog_index.html", base_ctx(request))

@router.get("/blog/response-time-matters", response_class=HTMLResponse)
def blog_post(request: Request):
    return templates.TemplateResponse("public/blog_post.html", base_ctx(request))

@router.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("public/contact.html", base_ctx(request))

@router.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("public/privacy.html", base_ctx(request))

@router.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("public/terms.html", base_ctx(request))

@router.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("public/thank_you.html", {"request": request, "title": "Thanks — TensorMarketData"})
