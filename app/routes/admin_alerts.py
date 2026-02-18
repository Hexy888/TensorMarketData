# Admin Alerts Routes

from __future__ import annotations
import os
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models.alerts import Alert

OPS_TOKEN = os.getenv("OPS_TOKEN", "")

templates = Jinja2Templates(directory="templates")
router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


@router.get("/admin/alerts", response_class=HTMLResponse)
def alerts_page(request: Request, ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Show open alerts."""
    rows = session.exec(
        select(Alert)
        .where(Alert.status == "open")
        .order_by(Alert.severity.desc(), Alert.updated_at.desc())
        .limit(200)
    ).all()
    
    return templates.TemplateResponse("admin/alerts.html", {"request": request, "rows": rows})


@router.post("/admin/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Acknowledge an alert."""
    alert = session.get(Alert, alert_id)
    if alert:
        alert.status = "acked"
        session.add(alert)
        session.commit()
    return {"ok": True}


@router.post("/admin/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Resolve an alert."""
    alert = session.get(Alert, alert_id)
    if alert:
        alert.status = "resolved"
        session.add(alert)
        session.commit()
    return {"ok": True}
