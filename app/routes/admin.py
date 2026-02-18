from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.db import get_session
from app.tenant_models import DraftReply, Review, AuditLog
from app.routes.admin_auth import require_admin_or_redirect
from datetime import datetime

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/admin")

@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, session: Session = Depends(get_session)):
    claims, redirect = require_admin_or_redirect(request)
    if redirect:
        return redirect
    
    drafts = session.exec(
        select(DraftReply, Review)
        .join(Review, Review.id == DraftReply.review_id)
        .where(DraftReply.business_id == 1)
        .order_by(DraftReply.created_at.desc())
        .limit(100)
    ).all()
    
    columns = {"pending": [], "approved": [], "rejected": [], "posted": []}
    for dr, rv in drafts:
        columns.setdefault(dr.status, []).append({
            "draft_id": dr.id,
            "rating": rv.rating,
            "review_text": rv.review_text,
            "draft_text": dr.draft_text,
            "created_at": dr.created_at,
        })
    
    logs = session.exec(select(AuditLog).where(AuditLog.business_id == 1).order_by(AuditLog.created_at.desc()).limit(25)).all()
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "brand":"TensorMarketData", "columns": columns, "logs": logs, "admin_key": ADMIN_KEY}
    )

@router.post("/move")
def move_card(
    request: Request,
    draft_id: int = Form(...),
    status: str = Form(...),  # pending|approved|rejected|posted
    session: Session = Depends(get_session),
):
    if not is_admin(request):
        return RedirectResponse("/", status_code=303)
    
    dr = session.get(DraftReply, draft_id)
    if dr and dr.business_id == 1:
        dr.status = status
        session.add(dr)
        session.add(AuditLog(business_id=1, action="admin_move", detail=f"draft_id={draft_id} -> {status}", created_at=datetime.utcnow()))
        session.commit()
    
    return RedirectResponse(f"/admin?key={ADMIN_KEY}", status_code=303)
