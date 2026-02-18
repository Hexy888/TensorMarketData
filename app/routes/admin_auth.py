from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.db import get_session
from app.models_admin import AdminUser
from app.security import verify_password, hash_password, sign_session, unsign_session

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/admin")

ADMIN_COOKIE = "tmd_admin"

def admin_claims(request: Request) -> dict | None:
    token = request.cookies.get(ADMIN_COOKIE, "")
    return unsign_session(token) if token else None

def require_admin_or_redirect(request: Request):
    c = admin_claims(request)
    if not c or not c.get("admin") or not c.get("admin_email"):
        return None, RedirectResponse("/admin/login", status_code=303)
    return c, None

@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request, "brand": "TensorMarketData"})

@router.post("/login")
def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    a = session.exec(select(AdminUser).where(AdminUser.email == email)).first()
    if not a or not verify_password(password, a.password_hash):
        return RedirectResponse("/admin/login?error=1", status_code=303)
    
    token = sign_session({"admin": True, "admin_email": email})
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie(ADMIN_COOKIE, token, httponly=True, samesite="lax")
    return resp

@router.post("/logout")
def admin_logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie(ADMIN_COOKIE)
    return resp
