from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from app.db import get_session
from app.models import DraftReply, Review
from app.routes.auth_helpers import require_user_or_redirect
from app.services.reputation import set_draft_status
from app.services.stripe import create_checkout_session

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/app")

@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    pending = session.exec(select(DraftReply).where(DraftReply.business_id == biz.id, DraftReply.status == "pending")).all()
    
    # Get weekly stats
    from datetime import timedelta
    from sqlalchemy import func
    since = datetime.utcnow() - timedelta(days=7)
    new_reviews = session.exec(select(func.count(Review.id)).where(Review.business_id == biz.id, Review.created_at >= since)).first() or 0
    replies_posted = session.exec(select(func.count(DraftReply.id)).where(DraftReply.business_id == biz.id, DraftReply.status == "posted", DraftReply.posted_at >= since)).first() or 0
    
    stats = {
        "new_reviews": new_reviews,
        "replies_posted": replies_posted,
        "pending": len(pending),
        "avg_rating": "—"  # Could compute from Review table
    }
    
    # Onboarding steps
    onboarding_steps = True
    
    return templates.TemplateResponse(
        "app/dashboard.html",
        {"request": request, "brand": "TensorMarketData", "user": {"email": user.email}, "business": biz, "pending_count": len(pending), "onboarding_steps": onboarding_steps, "stats": stats}
    )

@router.get("/approvals", response_class=HTMLResponse)
def approvals(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    drafts = session.exec(
        select(DraftReply, Review)
        .join(Review, Review.id == DraftReply.review_id)
        .where(DraftReply.business_id == biz.id)
        .order_by(DraftReply.created_at.desc())
        .limit(50)
    ).all()
    
    rows = []
    for dr, rv in drafts:
        rows.append({
            "draft_id": dr.id,
            "status": dr.status,
            "draft_text": dr.draft_text,
            "rating": rv.rating,
            "reviewer": rv.reviewer_name,
            "review_text": rv.review_text,
            "created_at": dr.created_at,
        })
    
    return templates.TemplateResponse(
        "app/approvals.html",
        {"request": request, "brand": "TensorMarketData", "user": {"email": user.email}, "rows": rows}
    )

@router.post("/approvals/action")
def approvals_action(
    request: Request,
    action: str = Form(...),  # approve | reject
    draft_id: int = Form(...),
    session: Session = Depends(get_session),
):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    if action == "approve":
        set_draft_status(session, biz.id, draft_id, "approved")
    elif action == "reject":
        set_draft_status(session, biz.id, draft_id, "rejected")
    
    return RedirectResponse("/app/approvals", status_code=303)

@router.post("/approvals/post")
def approvals_post(
    request: Request,
    draft_id: int = Form(...),
    session: Session = Depends(get_session),
):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    # Manual post is allowed for ANY star rating, but only if approved
    from app.services.reply_poster import post_draft_reply
    post_draft_reply(session, biz.id, draft_id)
    return RedirectResponse("/app/approvals", status_code=303)

@router.get("/billing", response_class=HTMLResponse)
def billing(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    plan = (request.query_params.get("plan") or "A").upper()
    checkout_url = create_checkout_session(plan, customer_email=user.email, business_id=biz.id)
    
    return templates.TemplateResponse(
        "app/billing.html",
        {"request": request, "brand": "TensorMarketData", "user": {"email": user.email}, "plan": plan, "checkout_url": checkout_url}
    )

@router.get("/settings", response_class=HTMLResponse)
def settings(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    return templates.TemplateResponse(
        "app/settings.html",
        {"request": request, "brand": "TensorMarketData", "user": {"email": user.email}, "business": biz, "login_only": False}
    )
