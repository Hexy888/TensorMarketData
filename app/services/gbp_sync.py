from datetime import datetime
from sqlmodel import Session, select
from app.models import Business, GBPCredential, AuditLog
from app.services.gbp_client import decrypt_refresh_token, refresh_access_token, list_reviews_v4_all
from app.services.reputation import ingest_review

def audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def gbp_pull_reviews_for_business(session: Session, business_id: int) -> int:
    """
    Placeholder that is 90% real:
    - refresh access token
    - list reviews for selected location (v4 endpoint)
    - ingest into our Review table (idempotent via external_id)
    """
    biz = session.get(Business, business_id)
    if not biz or not biz.gbp_connected or not biz.gbp_location_name:
        audit(session, business_id, "gbp_pull_noop", "gbp_not_configured")
        return 0
    
    cred = session.exec(select(GBPCredential).where(GBPCredential.business_id == business_id)).first()
    if not cred:
        audit(session, business_id, "gbp_pull_noop", "missing_credential")
        return 0
    
    refresh_tok = decrypt_refresh_token(cred.refresh_token_enc)
    if not refresh_tok:
        audit(session, business_id, "gbp_pull_noop", "missing_refresh_token")
        return 0
    
    tok = refresh_access_token(refresh_tok)
    access = tok.get("access_token", "")
    if not access:
        audit(session, business_id, "gbp_pull_failed", "no_access_token")
        return 0
    
    # Pull reviews
    try:
        reviews = list_reviews_v4_all(access, biz.gbp_location_name, page_size=50, max_pages=6)
    except Exception as e:
        audit(session, business_id, "gbp_pull_failed", str(e))
        return 0
    
    created = 0
    for r in reviews:
        ext_id = r.get("name", "")
        
        # Star rating mapping - v4 sometimes returns enums
        raw_star = r.get("starRating", 0)
        if isinstance(raw_star, str):
            mapping = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
            star = mapping.get(raw_star.upper(), 0)
        else:
            star = int(raw_star or 0)
        
        reviewer = ""
        if isinstance(r.get("reviewer"), dict):
            reviewer = r.get("reviewer", {}).get("displayName", "")
        text = r.get("comment", "") or ""
        
        if not ext_id:
            continue
        
        rv = ingest_review(session, business_id, "GBP", star, reviewer, text, ext_id)
        if rv is not None:
            created += 1
    
    audit(session, business_id, "gbp_pull_done", f"created={created} total_seen={len(reviews)}")
    return created
