from datetime import datetime
from sqlmodel import Session, select
from app.tenant_models import Business, DraftReply, Review, AuditLog
from app.services.gbp_tokens import get_fresh_access_token
from app.services.gbp_client import update_reply_v4
from app.services.http_retry import with_retries

def audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def post_draft_reply(session: Session, business_id: int, draft_id: int) -> dict:
    """
    Posts an APPROVED draft reply to GBP.
    """
    biz = session.get(Business, business_id)
    dr = session.get(DraftReply, draft_id)
    
    if not biz or not dr or dr.business_id != business_id:
        return {"ok": False, "error": "not_found"}
    
    if dr.status != "approved":
        return {"ok": False, "error": "draft_not_approved", "status": dr.status}
    
    # Idempotency: if already posted, do nothing
    if dr.status == "posted" and dr.posted_at:
        return {"ok": True, "noop": True, "reason": "already_posted"}
    
    rv = session.get(Review, dr.review_id)
    if not rv:
        return {"ok": False, "error": "missing_review"}
    
    # Must be connected + location selected
    if not biz.gbp_connected or not biz.gbp_location_name:
        dr.status = "post_failed"
        dr.posted_error = "gbp_not_configured"
        session.add(dr)
        session.commit()
        audit(session, business_id, "gbp_reply_failed", "gbp_not_configured")
        return {"ok": False, "error": "gbp_not_configured"}
    
    # Review external resource name must exist
    review_name = (rv.external_id or "").strip()
    if not review_name.startswith("accounts/"):
        dr.status = "post_failed"
        dr.posted_error = "missing_gbp_review_name"
        session.add(dr)
        session.commit()
        audit(session, business_id, "gbp_reply_failed", "missing_review_resource_name")
        return {"ok": False, "error": "missing_review_resource_name"}
    
    # Guard: cross-tenant check
    if dr.gbp_review_name and dr.gbp_review_name != review_name:
        dr.status = "post_failed"
        dr.posted_error = "gbp_review_name_mismatch"
        session.add(dr)
        session.commit()
        audit(session, business_id, "gbp_reply_failed", "review_name_mismatch")
        return {"ok": False, "error": "review_name_mismatch"}
    
    access = get_fresh_access_token(session, business_id)
    if not access:
        dr.status = "post_failed"
        dr.posted_error = "missing_access_token"
        session.add(dr)
        session.commit()
        audit(session, business_id, "gbp_reply_failed", "missing_access_token")
        return {"ok": False, "error": "missing_access_token"}
    
    try:
        def _call():
            return update_reply_v4(access, review_name, dr.draft_text)
        with_retries(_call, attempts=5, base_delay=0.8, jitter=0.4)
        
        dr.status = "posted"
        dr.posted_at = datetime.utcnow()
        dr.posted_error = ""
        dr.gbp_review_name = review_name
        session.add(dr)
        session.commit()
        audit(session, business_id, "gbp_reply_posted", f"draft_id={draft_id} review={review_name}")
        return {"ok": True}
    except Exception as e:
        dr.status = "post_failed"
        dr.posted_error = str(e)[:500]
        dr.gbp_review_name = review_name
        session.add(dr)
        session.commit()
        audit(session, business_id, "gbp_reply_failed", f"draft_id={draft_id} err={str(e)[:200]}")
        return {"ok": False, "error": "gbp_updateReply_failed", "detail": str(e)}
