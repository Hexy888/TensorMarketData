# Stripe Webhook Handler

from __future__ import annotations
import os
import secrets
import stripe
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.models.reputation import Client
from app.models.onboarding import OnboardingState
from app.services.email_sender import send_email_smtp

BASE_URL = os.getenv("BASE_URL", "https://tensormarketdata.com").rstrip("/")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "")
PRICE_GROWTH = os.getenv("STRIPE_PRICE_GROWTH", "")
PRICE_SCALE = os.getenv("STRIPE_PRICE_SCALE", "")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


def plan_from_price(price_id: str) -> str:
    if price_id == PRICE_STARTER:
        return "starter"
    if price_id == PRICE_GROWTH:
        return "growth"
    if price_id == PRICE_SCALE:
        return "scale"
    return "starter"


def upsert_client(session: Session, email: str, plan: str) -> Client:
    email = (email or "").strip().lower()
    c = session.exec(select(Client).where(Client.email == email)).first()
    if not c:
        c = Client(name=email.split("@")[0].title(), email=email, plan=plan, status="active")
    else:
        c.plan = plan
        if c.status != "canceled":
            c.status = "active"
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def ensure_onboarding_state(session: Session, client_id: int) -> OnboardingState:
    ob = session.exec(
        select(OnboardingState).where(OnboardingState.client_id == client_id)
    ).first()
    if not ob:
        ob = OnboardingState(client_id=client_id)
        session.add(ob)
        session.commit()
        session.refresh(ob)
    return ob


def send_magic_link(session: Session, client: Client):
    """Send login magic link after checkout."""
    ob = ensure_onboarding_state(session, client.id)
    
    token = secrets.token_urlsafe(32)
    exp = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    
    m = ob.meta or {}
    m["login_token"] = token
    m["login_token_exp"] = exp
    ob.meta = m
    ob.updated_at = datetime.utcnow()
    session.add(ob)
    session.commit()
    
    link = f"{BASE_URL}/app/login/callback?t={token}&e={client.email}"
    
    body = f"""Login link (valid 30 minutes): {link}

Next steps:
1. Connect Google Business Profile
2. Select your location
3. Turn on "Go Live"

Questions? Reply to this email.
"""
    
    try:
        send_email_smtp(
            to_email=client.email,
            subject="Your TensorMarketData login link",
            body_text=body
        )
    except Exception:
        pass  # Don't fail checkout on email error


def handle_checkout_completed(event_obj: dict, session_db: Session):
    """Handle Stripe checkout.session.completed event."""
    email = (event_obj.get("customer_details") or {}).get("email") or event_obj.get("customer_email") or ""
    meta = event_obj.get("metadata") or {}
    plan = (meta.get("plan") or "").strip().lower()
    price_id = meta.get("price_id") or ""
    
    if not plan and price_id:
        plan = plan_from_price(price_id)
    if not plan:
        plan = "starter"
    
    client = upsert_client(session_db, email=email, plan=plan)
    ensure_onboarding_state(session_db, client.id)
    
    # Auto-send magic link
    if email:
        send_magic_link(session_db, client)
    
    return client
