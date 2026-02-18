import os
import stripe
from app.config import settings

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PLAN_TO_PRICE = {
    "A": settings.stripe_price_a,
    "B": settings.stripe_price_b,
    "C": settings.stripe_price_c,
}

def create_checkout_session(plan: str, customer_email: str | None, business_id: int) -> str:
    plan = (plan or "").upper().strip()
    price_id = PLAN_TO_PRICE.get(plan)
    
    if not stripe.api_key or not price_id:
        return f"/app/billing?plan={plan}&stripe=not_configured"
    
    base = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    success_url = f"{base}/app?checkout=success"
    cancel_url = f"{base}/pricing?checkout=cancel"
    
    s = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=customer_email,
        client_reference_id=str(business_id),
        metadata={"business_id": str(business_id), "plan": plan},
    )
    
    return s.url
