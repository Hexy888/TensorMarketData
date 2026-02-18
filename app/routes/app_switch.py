from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.db import get_session
from app.routes.auth_helpers import require_user_or_redirect
from app.routes.context import list_user_businesses
from app.security import sign_session

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/app")

@router.get("/switch-business", response_class=HTMLResponse)
def switch_page(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    businesses = list_user_businesses(session, user.id)
    
    return templates.TemplateResponse(
        "app/switch_business.html",
        {"request": request, "brand": "TensorMarketData", "user": {"email": user.email}, "business": biz, "businesses": businesses}
    )

@router.post("/switch-business")
def switch_post(
    request: Request,
    business_id: int = Form(...),
    session: Session = Depends(get_session),
):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    businesses = list_user_businesses(session, user.id)
    allowed_ids = {b.id for b in businesses}
    
    if business_id not in allowed_ids:
        return RedirectResponse("/app/switch-business", status_code=303)
    
    # Keep same user/email, swap business_id claim
    token = sign_session({"user_id": user.id, "email": user.email, "business_id": business_id})
    resp = RedirectResponse("/app", status_code=303)
    resp.set_cookie("tmd_session", token, httponly=True, samesite="lax")
    return resp
