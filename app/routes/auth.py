from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.db import get_session
from app.models import User, Business
from app.security import verify_password, sign_session, make_magic_token, verify_magic_token
from app.services.email import send_email

templates = Jinja2Templates(directory="templates")
router = APIRouter()

def resolve_default_business_id(session: Session, user: User) -> int | None:
    if user.default_business_id:
        return user.default_business_id
    biz = session.exec(select(Business).where(Business.owner_user_id == user.id).order_by(Business.created_at.asc())).first()
    if biz:
        user.default_business_id = biz.id
        session.add(user)
        session.commit()
        return biz.id
    return None

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "app/settings.html",
        {"request": request, "brand": "TensorMarketData", "login_only": True, "error": request.query_params.get("error"), "sent": request.query_params.get("sent")}
    )

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url="/login?error=1", status_code=303)
    
    business_id = resolve_default_business_id(session, user)
    token = sign_session({"user_id": user.id, "email": user.email, "business_id": business_id})
    
    resp = RedirectResponse(url="/app", status_code=303)
    resp.set_cookie("tmd_session", token, httponly=True, samesite="lax")
    return resp

@router.post("/login/link")
def login_link(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return RedirectResponse(url="/login?sent=1", status_code=303)
    
    token = make_magic_token(email)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    scheme = request.headers.get("x-forwarded-proto") or "http"
    link = f"{scheme}://{host}/magic-login?token={token}"
    
    send_email(
        to_email=email,
        subject="Your sign-in link",
        html=f"<p>Click to sign in:</p><p><a href='{link}'>{link}</a></p><p>This link expires in 30 minutes.</p>",
    )
    return RedirectResponse(url="/login?sent=1", status_code=303)

@router.get("/magic-login")
def magic_login(token: str, session: Session = Depends(get_session)):
    data = verify_magic_token(token, max_age_seconds=1800)
    if not data or "email" not in data:
        return RedirectResponse(url="/login?error=1", status_code=303)
    
    email = data["email"]
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return RedirectResponse(url="/login?error=1", status_code=303)
    
    business_id = resolve_default_business_id(session, user)
    cookie = sign_session({"user_id": user.id, "email": user.email, "business_id": business_id})
    
    resp = RedirectResponse(url="/app", status_code=303)
    resp.set_cookie("tmd_session", cookie, httponly=True, samesite="lax")
    return resp

@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=303)
    resp.delete_cookie("tmd_session")
    return resp
