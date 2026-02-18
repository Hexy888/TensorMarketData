from datetime import datetime
from sqlmodel import Session, select
from app.models import Business, Review, DraftReply, AuditLog
from app.services.reputation import ingest_review, generate_draft_reply, NEGATIVE_THRESHOLD, set_draft_status
from app.services.reply_poster import post_draft_reply

def _audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def simulate_pull_reviews(session: Session, business_id: int, n: int = 2) -> int:
    """
    Stub for GBP sync: Generates a couple synthetic reviews only if we don't already have them.
    Replace with real GBP API fetch.
    """
    created = 0
    samples = [
        ("GBP", 5, "Morgan", "Quick repair. Clear pricing. Great service.", "gbp_sim_1"),
        ("GBP", 1, "Riley", "No-show on appointment. Disappointed.", "gbp_sim_2"),
        ("GBP", 4, "Avery", "Professional tech. Fixed it fast.", "gbp_sim_3"),
    ]
    for platform, rating, reviewer, text, ext_id in samples[:max(1, min(n, len(samples)))]:
        before = session.exec(select(Review).where(Review.external_id == ext_id)).first()
        rv = ingest_review(session, business_id, platform, rating, reviewer, text, ext_id)
        if before is None and rv is not None:
            created += 1
    return created

def pull_reviews(session: Session, business_id: int, simulate: bool, simulate_n: int) -> int:
    """
    Route to real or simulated review pull.
    """
    if simulate:
        return simulate_pull_reviews(session, business_id, n=simulate_n)
    
    # Real GBP pull
    from app.services.gbp_sync import gbp_pull_reviews_for_business
    return gbp_pull_reviews_for_business(session, business_id)

def autopost_approved_positives(session: Session, business: Business) -> int:
    """
    If business.autopost_positive is True:
    - Any DraftReply with status=approved AND rating>=4 becomes status=posted
    (This simulates GBP posting; replace with real post call.)
    """
    if not business.autopost_positive:
        return 0
    
    rows = session.exec(
        select(DraftReply, Review)
        .join(Review, Review.id == DraftReply.review_id)
        .where(DraftReply.business_id == business.id, DraftReply.status == "approved")
    ).all()
    
    posted = 0
    for dr, rv in rows:
        if rv.rating >= 4:
            dr.status = "posted"
            session.add(dr)
            posted += 1
    
    if posted:
        session.commit()
        _audit(session, business.id, "autopost_positives", f"posted={posted}")
    
    return posted

def ensure_drafts_for_new_reviews(session: Session, business_id: int) -> int:
    """
    For any Review without a DraftReply, create one.
    """
    reviews = session.exec(select(Review).where(Review.business_id == business_id)).all()
    
    created = 0
    for rv in reviews:
        existing = session.exec(select(DraftReply).where(DraftReply.review_id == rv.id)).first()
        if existing:
            continue
        generate_draft_reply(session, business_id, rv)
        created += 1
    
    if created:
        _audit(session, business_id, "drafts_created_for_reviews", f"created={created}")
    
    return created

def ops_run(session: Session, business_id: int, simulate: bool = True, simulate_n: int = 2) -> dict:
    business = session.get(Business, business_id)
    if not business:
        return {"ok": False, "error": "business_not_found"}
    
    if not business.gbp_connected:
        _audit(session, business_id, "ops_noop", "gbp_not_connected")
        return {"ok": True, "noop": True, "reason": "gbp_not_connected"}
    
    _audit(session, business_id, "ops_start", f"simulate={simulate}")
    
    pulled = pull_reviews(session, business_id, simulate=simulate, simulate_n=simulate_n)
    if simulate:
        _audit(session, business_id, "reviews_pulled_stub", f"pulled={pulled}")
    
    drafts_created = ensure_drafts_for_new_reviews(session, business_id)
    
    # --- AUTOPost block (strict) ---
    # Only autopost 4-5 star reviews, and only if autopost_positive is enabled
    autoposted = 0
    if business and business.autopost_positive:
        pairs = session.exec(
            select(DraftReply, Review)
            .join(Review, Review.id == DraftReply.review_id)
            .where(DraftReply.business_id == business_id, DraftReply.status == "pending")
            .order_by(DraftReply.created_at.desc())
            .limit(50)
        ).all()
        for dr, rv in pairs:
            if rv.rating >= 4:
                # Approve then post
                set_draft_status(session, business_id, dr.id, "approved")
                res = post_draft_reply(session, business_id, dr.id)
                if res.get("ok"):
                    autoposted += 1
    else:
        autoposted = 0
    
    # Policy: negatives require approval; positives can be approved immediately by draft generator
    # Autopost only affects approved positives (>=4)
    posted = autoposted  # Use the new block result
    
    # Count pending negatives
    pending = session.exec(select(DraftReply).where(DraftReply.business_id == business_id, DraftReply.status == "pending")).all()
    
    _audit(session, business_id, "ops_end", f"drafts_created={drafts_created} posted={posted} pending={len(pending)}")
    
    return {
        "ok": True,
        "noop": False,
        "pulled_stub": pulled,
        "drafts_created": drafts_created,
        "autoposted": posted,
        "pending_for_approval": len(pending),
        "negative_threshold": NEGATIVE_THRESHOLD,
    }
