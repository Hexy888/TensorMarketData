from fastapi import Request
from sqlmodel import Session, select
from app.security import unsign_session
from app.tenant_models import User, Business

def get_session_claims(request: Request) -> dict | None:
    token = request.cookies.get("tmd_session", "")
    return unsign_session(token) if token else None

def get_current_user_and_business(request: Request, session: Session):
    """
    Returns (user, business) or (None, None)
    Priority:
    1) claims.business_id
    2) user.default_business_id
    3) first business owned by user
    """
    claims = get_session_claims(request)
    if not claims:
        return None, None
    
    user_id = claims.get("user_id")
    if not user_id:
        return None, None
    
    user = session.get(User, int(user_id))
    if not user:
        return None, None
    
    biz = None
    
    # 1) claims business_id (preferred)
    claim_bid = claims.get("business_id")
    if claim_bid:
        biz = session.get(Business, int(claim_bid))
        if biz and biz.owner_user_id != user.id:
            biz = None  # safety: ignore business not owned by user
    
    # 2) user default
    if not biz and user.default_business_id:
        biz = session.get(Business, int(user.default_business_id))
        if biz and biz.owner_user_id != user.id:
            biz = None
    
    # 3) fallback
    if not biz:
        biz = session.exec(
            select(Business)
            .where(Business.owner_user_id == user.id)
            .order_by(Business.created_at.asc())
        ).first()
    
    if biz and not user.default_business_id:
        user.default_business_id = biz.id
        session.add(user)
        session.commit()
    
    return user, biz

def list_user_businesses(session: Session, user_id: int):
    return session.exec(
        select(Business)
        .where(Business.owner_user_id == user_id)
        .order_by(Business.created_at.asc())
    ).all()
