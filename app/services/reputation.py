from datetime import datetime
from sqlmodel import Session, select
from app.models import Review, DraftReply, AuditLog

NEGATIVE_THRESHOLD = 3  # 1–3 stars = approval required

def ingest_review(session: Session, business_id: int, platform: str, rating: int, reviewer_name: str, review_text: str, external_id: str) -> Review:
    existing = session.exec(select(Review).where(Review.external_id == external_id)).first()
    if existing:
        return existing
    
    r = Review(
        business_id=business_id,
        platform=platform,
        rating=rating,
        reviewer_name=reviewer_name or "",
        review_text=review_text or "",
        external_id=external_id,
        created_at=datetime.utcnow(),
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    
    session.add(AuditLog(business_id=business_id, action="review_ingested", detail=f"{platform}:{external_id} rating={rating}"))
    session.commit()
    return r

def generate_draft_reply(session: Session, business_id: int, review: Review) -> DraftReply:
    # Stub mechanism: simple templated response. Replace with LLM later.
    if review.rating <= NEGATIVE_THRESHOLD:
        draft = (
            "Thanks for the feedback — we take this seriously. "
            "We'd like to make this right. Please reply with the best contact number or email so a manager can follow up."
        )
        status = "pending"  # requires approval
    else:
        draft = (
            "Thanks for the kind words — we appreciate your business. "
            "If you ever need anything HVAC-related, we're here to help."
        )
        status = "approved"  # can be autoposted if enabled (handled by ops policy)
    
    dr = DraftReply(
        review_id=review.id,
        business_id=business_id,
        draft_text=draft,
        status=status,
        created_at=datetime.utcnow(),
    )
    session.add(dr)
    session.add(AuditLog(business_id=business_id, action="draft_created", detail=f"review_id={review.id} status={status}"))
    session.commit()
    session.refresh(dr)
    return dr

def set_draft_status(session: Session, business_id: int, draft_id: int, new_status: str) -> DraftReply | None:
    dr = session.get(DraftReply, draft_id)
    if not dr or dr.business_id != business_id:
        return None
    
    dr.status = new_status
    session.add(dr)
    session.add(AuditLog(business_id=business_id, action="draft_status_changed", detail=f"draft_id={draft_id} -> {new_status}"))
    session.commit()
    session.refresh(dr)
    return dr
