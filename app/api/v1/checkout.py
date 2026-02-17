"""
Checkout API for TensorMarketData - Reputation Operations.
Handles checkout session creation and redirect.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from app.core.stripe import stripe_service, PRICES

router = APIRouter(prefix="/api/checkout", tags=["checkout"])


class CheckoutRequest(BaseModel):
    package: str  # package_a, package_b, package_c
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None


@router.post("/create-session")
async def create_checkout_session(
    request: CheckoutRequest,
):
    """
    Create a Stripe checkout session for the specified package.
    
    Returns the checkout URL to redirect the user to.
    """
    # Validate package
    if request.package not in PRICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid package: {request.package}. Must be one of: {list(PRICES.keys())}"
        )
    
    price_info = PRICES[request.package]
    price_id = price_info["price_id"]
    
    # Get customer if provided
    customer_id = request.customer_id
    
    # If no customer but email provided, check if customer exists
    if not customer_id and request.customer_email:
        existing = await stripe_service.get_customer_by_email(request.customer_email)
        if existing:
            customer_id = existing["id"]
    
    try:
        # Create checkout session
        session = await stripe_service.create_checkout_session(
            price_id=price_id,
            customer_id=customer_id,
            customer_email=request.customer_email,
            success_url=f"https://tensormarketdata.com/thank-you?session_id={{CHECKOUT_SESSION_ID}}&package={request.package}",
            cancel_url="https://tensormarketdata.com/pricing?canceled=1",
        )
        
        return {
            "success": True,
            "checkout_url": session["url"],
            "session_id": session["id"],
            "package": request.package,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/package/{package}")
async def checkout_redirect(
    package: str,
    email: Optional[str] = Query(None),
):
    """
    Simple GET endpoint to start checkout.
    Redirects to Stripe checkout.
    """
    if package not in PRICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid package: {package}"
        )
    
    price_info = PRICES[package]
    price_id = price_info["price_id"]
    
    try:
        # Get or create customer by email
        customer_id = None
        if email:
            existing = await stripe_service.get_customer_by_email(email)
            if existing:
                customer_id = existing["id"]
        
        # Create checkout session
        session = await stripe_service.create_checkout_session(
            price_id=price_id,
            customer_id=customer_id,
            customer_email=email,
            success_url=f"https://tensormarketdata.com/thank-you?session_id={{CHECKOUT_SESSION_ID}}&package={package}",
            cancel_url="https://tensormarketdata.com/pricing?canceled=1",
        )
        
        # Redirect to Stripe
        return RedirectResponse(session["url"])
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )
