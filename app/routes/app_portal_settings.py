from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from datetime import datetime
from app.db import get_session
from app.tenant_models import AuditLog
from app.routes.auth_helpers import require_user_or_redirect

router = APIRouter(prefix="/app")

@router.post("/settings/save")
def settings_save(
    request: Request,
    brand_voice: str = Form(""),
    autopost_positive: str = Form("off"),
    session: Session = Depends(get_session),
):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    biz.brand_voice = (brand_voice or "").strip()[:1000]
    biz.autopost_positive = (autopost_positive == "on")
    
    session.add(biz)
    session.add(AuditLog(business_id=biz.id, action="settings_saved", detail="brand_voice/autopost updated", created_at=datetime.utcnow()))
    session.commit()
    
    return RedirectResponse("/app/settings", status_code=303)

@router.post("/settings/gbp/toggle")
def gbp_toggle(
    request: Request,
    connected: str = Form("off"),
    session: Session = Depends(get_session),
):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    biz.gbp_connected = (connected == "on")
    
    session.add(biz)
    session.add(AuditLog(business_id=biz.id, action="gbp_toggle_stub", detail=f"gbp_connected={biz.gbp_connected}", created_at=datetime.utcnow()))
    session.commit()
    
    return RedirectResponse("/app/settings", status_code=303)
