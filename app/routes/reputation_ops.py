# Reputation Operations Routes

import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.services.reputation_engine import ReputationEngine

OPS_TOKEN = os.getenv("OPS_TOKEN", "")

router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


@router.post("/api/ops/reputation/ingest")
def ops_ingest(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Pull reviews from GBP."""
    return ReputationEngine(session).ingest_reviews()


@router.post("/api/ops/reputation/draft")
def ops_draft(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Draft replies for new reviews."""
    return ReputationEngine(session).draft_new_reviews()


@router.post("/api/ops/reputation/post_autopost")
def ops_post(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Auto-post approved drafts."""
    return ReputationEngine(session).post_autopost()


@router.post("/api/ops/reputation/report_weekly")
def ops_report(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Generate weekly reports."""
    return ReputationEngine(session).weekly_report()


@router.post("/api/ops/reputation/draft/{draft_id}/approve")
def ops_approve(draft_id: int, ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Approve a draft."""
    ReputationEngine(session).approve_draft(draft_id, approved_by="admin")
    return {"ok": True}


@router.post("/api/ops/reputation/draft/{draft_id}/reject")
def ops_reject(draft_id: int, ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Reject a draft."""
    ReputationEngine(session).reject_draft(draft_id, reason="admin_reject")
    return {"ok": True}
