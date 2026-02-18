# Checkout API Routes

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.stripe_checkout import create_checkout_session

router = APIRouter()


class CheckoutIn(BaseModel):
    plan: str
    email: str | None = None


@router.post("/api/checkout")
def api_checkout(payload: CheckoutIn):
    """Create Stripe checkout session."""
    try:
        out = create_checkout_session(payload.plan, payload.email)
        return JSONResponse(out)
    except Exception as e:
        raise HTTPException(400, str(e))
