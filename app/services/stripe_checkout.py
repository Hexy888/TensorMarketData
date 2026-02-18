# Stripe Checkout Service

from __future__ import annotations
import os
from typing import Dict, Any
import stripe

BASE_URL = os.getenv("BASE_URL", "https://tensormarketdata.com").rstrip("/")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "")
PRICE_GROWTH = os.getenv("STRIPE_PRICE_GROWTH", "")
PRICE_SCALE = os.getenv("STRIPE_PRICE_SCALE", "")

stripe.api_key = STRIPE_SECRET_KEY


def price_for_plan(plan: str) -> str:
    plan = (plan or "").strip().lower()
    if plan == "starter":
        return PRICE_STARTER
    if plan == "growth":
        return PRICE_GROWTH
    if plan == "scale":
        return PRICE_SCALE
    raise ValueError("unknown plan")


def create_checkout_session(plan: str, customer_email: str | None = None) -> Dict[str, Any]:
    price_id = price_for_plan(plan)
    if not price_id:
        raise RuntimeError("missing STRIPE_PRICE_* env var")
    
    sess = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        allow_promotion_codes=True,
        success_url=f"{BASE_URL}/thank-you?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/pricing",
        customer_email=customer_email,
        metadata={"plan": plan, "price_id": price_id},
    )
    
    return {
        "id": sess.id,
        "url": sess.url,
        "plan": plan,
        "price_id": price_id
    }
