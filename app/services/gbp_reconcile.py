from datetime import datetime
from sqlmodel import Session, select
from app.models import Business, DraftReply, Review, AuditLog
from app.services.gbp_tokens import get_fresh_access_token
from app.services.gbp_client import list_reviews_v4_all

def audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def reconcile_business(session: Session, business_id: int, max_items: int = 50) -> dict:
    biz = session.get(Business, business_id)
    if not biz or not biz.gbp_connected or not biz.gbp_location_name:
        return {"ok": True, "noop": True, "reason": "gbp_not_configured"}
    
    access = get_fresh_access_token(session, business_id)
    if not access:
        audit(session, business_id, "gbp_reconcile_failed", "missing_access_token")
        return {"ok": False, "error": "missing_access_token"}
    
    try:
        reviews = list_reviews_v4_all(access, biz.gbp_location_name, page_size=50, max_pages=4)
    except Exception as e:
        audit(session, business_id, "gbp_reconcile_failed", str(e)[:200])
        return {"ok": False, "error": str(e)}
    
    # Build map review_name -> reply present
    reply_present = {}
    for r in reviews:
        name = r.get("name", "")
        reply = r.get("reviewReply") or r.get("reply") or {}
        comment = reply.get("comment") if isinstance(reply, dict) else None
        reply_present[name] = bool(comment)
    
    # Find recent posted drafts
    rows = session.exec(
        select(DraftReply, Review)
        .join(Review, Review.id == DraftReply.review_id)
        .where(DraftReply.business_id == business_id, DraftReply.status == "posted")
        .order_by(DraftReply.posted_at.desc())
        .limit(max_items)
    ).all()
    
    mismatches = 0
    for dr, rv in rows:
        review_name = (rv.external_id or "").strip()
        if review_name and review_name.startswith("accounts/"):
            if not reply_present.get(review_name, False):
                mismatches += 1
    
    audit(session, business_id, "gbp_reconcile_done", f"checked={len(rows)} mismatches={mismatches}")
    return {"ok": True, "checked": len(rows), "mismatches": mismatches}
