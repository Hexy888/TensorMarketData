from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db import get_session
from app.services.gbp import sync_reviews_for_business
from app.services.reputation import ingest_review, generate_draft_reply

router = APIRouter(prefix="/api")

@router.post("/reviews/sync")
def reviews_sync(business_id: int, session: Session = Depends(get_session)):
    # Stub: GBP sync returns count
    count = sync_reviews_for_business(business_id)
    return {"ok": True, "synced": count}

@router.post("/reviews/ingest")
def reviews_ingest(
    business_id: int,
    platform: str,
    rating: int,
    reviewer_name: str = "",
    review_text: str = "",
    external_id: str = "",
    session: Session = Depends(get_session),
):
    # Real DB ingest + draft generation
    rv = ingest_review(session, business_id, platform, rating, reviewer_name, review_text, external_id or f"{platform}:{rating}:{hash(review_text)}")
    dr = generate_draft_reply(session, business_id, rv)
    return {"ok": True, "review_id": rv.id, "draft_id": dr.id, "draft_status": dr.status}

@router.post("/drafts/approve")
def drafts_approve(business_id: int, draft_id: int, session: Session = Depends(get_session)):
    from app.services.reputation import set_draft_status
    dr = set_draft_status(session, business_id, draft_id, "approved")
    return {"ok": bool(dr), "draft_id": draft_id, "status": dr.status if dr else None}

@router.post("/drafts/reject")
def drafts_reject(business_id: int, draft_id: int, session: Session = Depends(get_session)):
    from app.services.reputation import set_draft_status
    dr = set_draft_status(session, business_id, draft_id, "rejected")
    return {"ok": bool(dr), "draft_id": draft_id, "status": dr.status if dr else None}
