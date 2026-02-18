import os
import stripe
from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from datetime import datetime
from app.db import get_session
from app.models import Subscription, AuditLog, Business

router = APIRouter(prefix="/webhooks")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

def audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def resolve_business_id_from_event(session: Session, event: dict) -> int | None:
    obj = event["data"]["object"]
    
    # Preferred: checkout.session.completed carries metadata + client_reference_id
    meta = obj.get("metadata") or {}
    if "business_id" in meta:
        try:
            return int(meta["business_id"])
        except:
            pass
    
    ref = obj.get("client_reference_id")
    if ref:
        try:
            return int(ref)
        except:
            pass
    
    # Fallback: map by stripe customer id if stored on Business
    cus_id = obj.get("customer")
    if cus_id:
        biz = session.exec(select(Business).where(Business.stripe_customer_id == cus_id)).first()
        if biz:
            return biz.id
    
    return None

@router.post("/stripe")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    sig_header = request.headers.get("stripe-signature", "")
    payload_bytes = await request.body()
    payload = payload_bytes.decode("utf-8")
    
    if not endpoint_secret:
        return {"ok": False, "error": "missing_STRIPE_WEBHOOK_SECRET"}
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return {"ok": False, "error": "signature_verification_failed", "detail": str(e)}
    
    etype = event["type"]
    obj = event["data"]["object"]
    
    business_id = resolve_business_id_from_event(session, event)
    if not business_id:
        return {"ok": False, "error": "cannot_resolve_business_id", "type": etype}
    
    if etype == "checkout.session.completed":
        sub_id = obj.get("subscription")
        cus_id = obj.get("customer")
        
        # store stripe_customer_id on business for future mapping
        biz = session.get(Business, business_id)
        if biz and cus_id and not biz.stripe_customer_id:
            biz.stripe_customer_id = cus_id
            session.add(biz)
            session.commit()
        
        if sub_id:
            sub = session.exec(select(Subscription).where(Subscription.business_id == business_id)).first()
            if not sub:
                sub = Subscription(business_id=business_id, plan=(obj.get("metadata") or {}).get("plan", "A"), status="active")
            sub.status = "active"
            sub.stripe_subscription_id = sub_id
            session.add(sub)
            session.commit()
            audit(session, business_id, "stripe_checkout_completed", f"cus={cus_id} sub={sub_id}")
    
    elif etype == "customer.subscription.updated":
        sub_id = obj.get("id")
        status = obj.get("status", "active")
        
        sub = session.exec(select(Subscription).where(Subscription.business_id == business_id)).first()
        if not sub:
            sub = Subscription(business_id=business_id, plan="A", status=status)
        sub.status = status
        sub.stripe_subscription_id = sub_id
        session.add(sub)
        session.commit()
        audit(session, business_id, "stripe_sub_updated", f"status={status} sub={sub_id}")
    
    elif etype == "customer.subscription.deleted":
        sub_id = obj.get("id")
        sub = session.exec(select(Subscription).where(Subscription.business_id == business_id)).first()
        if sub:
            sub.status = "canceled"
            session.add(sub)
            session.commit()
            audit(session, business_id, "stripe_sub_deleted", f"sub={sub_id}")
    
    elif etype == "invoice.payment_failed":
        sub = session.exec(select(Subscription).where(Subscription.business_id == business_id)).first()
        if sub:
            sub.status = "past_due"
            session.add(sub)
            session.commit()
            audit(session, business_id, "stripe_payment_failed", "invoice.payment_failed")
    
    return {"ok": True, "type": etype, "business_id": business_id}
