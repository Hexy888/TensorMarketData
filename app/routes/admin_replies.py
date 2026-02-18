# Admin Replies Routes - Needs Answer Queue

from __future__ import annotations
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, Depends, Header, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models.outbound import OutboundTarget, OutboundEvent
from app.models.inbox import InboxProcessed
from app.models.reply_ops import ReplyAudit
from app.services.email_sender import send_email_smtp

OPS_TOKEN = os.getenv("OPS_TOKEN", "")
ONBOARDING_URL = os.getenv("ONBOARDING_URL", "https://tensormarketdata.com/get-started")

templates = Jinja2Templates(directory="templates")
router = APIRouter()


def require_admin(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "unauthorized")
    return True


def _latest_reply_snippet(session: Session, email_addr: str) -> str:
    """Fetch most recent InboxProcessed for this sender."""
    if not email_addr:
        return ""
    
    row = session.exec(
        select(InboxProcessed)
        .where(InboxProcessed.from_email.contains(email_addr))
        .order_by(InboxProcessed.created_at.desc())
        .limit(1)
    ).first()
    
    if not row:
        return ""
    
    meta = row.meta or {}
    return (meta.get("body_head") or "")[:180]


def canned_templates(company: str) -> Dict[str, Dict[str, str]]:
    """Short, safe canned responses."""
    return {
        "onboarding": {
            "subject": f"Setup link — {company}",
            "body": (
                f"Got it.\n\n"
                f"Here's the setup link to get started: {ONBOARDING_URL}\n"
                f"If you'd like, reply with your Google Business Profile link and I'll confirm it's connected.\n\n"
                f"If you prefer no more emails, reply opt out.\n"
            ),
        },
        "pricing": {
            "subject": f"Pricing + what's included — {company}",
            "body": (
                f"Here are the plans and what they cover:\n"
                f"• $99/mo: monitoring + drafted replies (approval for 1–3★)\n"
                f"• $199/mo: higher volume + weekly report\n"
                f"• $399/mo: multi-location or higher volume + priority handling\n\n"
                f"Setup link: {ONBOARDING_URL}\n\n"
                f"Reply opt out anytime.\n"
            ),
        },
        "question_generic": {
            "subject": f"Quick answer — {company}",
            "body": (
                f"Yes — we handle monitoring + drafted review replies.\n"
                f"Nothing sensitive posts without approval (1–3★ approval-gated).\n\n"
                f"If you want to proceed, use this setup link: {ONBOARDING_URL}\n"
                f"Or reply with your GBP link and I'll confirm next steps.\n\n"
                f"Reply opt out anytime.\n"
            ),
        },
        "close_out": {
            "subject": f"Closing the loop — {company}",
            "body": (
                f"All good — I'll close this out.\n"
                f"If you want to revisit later, the setup link is here: {ONBOARDING_URL}\n\n"
                f"Reply opt out anytime.\n"
            ),
        },
    }


@router.get("/admin/replies", response_class=HTMLResponse)
def replies_queue(request: Request, ok=Depends(require_admin), session: Session = Depends(get_session)):
    """Show needs_answer queue."""
    rows = session.exec(
        select(OutboundTarget)
        .where(OutboundTarget.status == "needs_answer")
        .order_by(OutboundTarget.updated_at.asc())
        .limit(200)
    ).all()
    
    view = []
    for t in rows:
        view.append({
            "id": t.id,
            "company_name": t.company_name,
            "contact_email": t.contact_email,
            "title": t.notes or "",
            "updated_at": t.updated_at.isoformat() if t.updated_at else "",
            "snippet": _latest_reply_snippet(session, t.contact_email),
        })
    
    return templates.TemplateResponse(
        "admin/replies.html",
        {"request": request, "rows": view}
    )


@router.get("/admin/replies/{target_id}", response_class=HTMLResponse)
def reply_detail(request: Request, target_id: int, ok=Depends(require_admin), session: Session = Depends(get_session)):
    """Detail view for a reply."""
    t = session.get(OutboundTarget, target_id)
    if not t:
        raise HTTPException(404, "not found")
    
    templates_map = canned_templates(t.company_name or "your team")
    snippet = _latest_reply_snippet(session, t.contact_email)
    
    return templates.TemplateResponse(
        "admin/reply_detail.html",
        {"request": request, "t": t, "snippet": snippet, "templates": templates_map}
    )


@router.post("/admin/replies/{target_id}/send")
def send_reply(
    request: Request,
    target_id: int,
    template_key: str = Form(default="question_generic"),
    subject: str = Form(default=""),
    body: str = Form(default=""),
    ok=Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Send a reply and update status."""
    t = session.get(OutboundTarget, target_id)
    if not t:
        raise HTTPException(404, "not found")
    
    # Get canned template if needed
    templates_map = canned_templates(t.company_name or "your team")
    if not subject.strip() or not body.strip():
        chosen = templates_map.get(template_key) or templates_map["question_generic"]
        subject = subject.strip() or chosen["subject"]
        body = body.strip() or chosen["body"]
    
    to_email = (t.contact_email or "").strip().lower()
    if not to_email:
        raise HTTPException(400, "missing contact email")
    
    # Send
    send_email_smtp(to_email=to_email, subject=subject, body_text=body)
    
    # Audit
    session.add(ReplyAudit(
        target_id=t.id,
        to_email=to_email,
        template_key=template_key,
        subject=subject,
        body=body,
        meta={},
    ))
    
    # Event log
    session.add(OutboundEvent(
        target_id=t.id,
        event_type="reply_sent",
        meta={"template_key": template_key},
    ))
    
    # Move status
    t.status = "sent"
    session.add(t)
    session.commit()
    
    return RedirectResponse(url="/admin/replies", status_code=303)
