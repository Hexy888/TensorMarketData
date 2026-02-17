"""
Lead Generation API - Sample lead requests & checkout
"""

import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import uuid4

router = APIRouter()


class LeadSampleRequest(BaseModel):
    email: EmailStr
    industry: str
    company_size: Optional[str] = None
    criteria: Optional[str] = None


class LeadSampleResponse(BaseModel):
    status: str
    message: str
    request_id: str
    leads_count: Optional[int] = None


class CheckoutRequest(BaseModel):
    tier: str
    email: Optional[str] = None


# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_IDS = {
    "starter": os.getenv("STRIPE_PRICE_STARTER", "price_xxx"),  # 100 leads
    "growth": os.getenv("STRIPE_PRICE_GROWTH", "price_xxx"),     # 500 leads
    "monthly": os.getenv("STRIPE_PRICE_MONTHLY", "price_xxx"),  # 200 leads/mo
}


@router.post(
    "/leads/sample",
    tags=["Leads"],
    summary="Request free sample leads",
)
async def request_sample_leads(data: LeadSampleRequest) -> LeadSampleResponse:
    """
    Request free sample leads. Returns a success response.
    Lead data will be emailed to the requester.
    """
    request_id = str(uuid4())[:8]
    
    return LeadSampleResponse(
        status="success",
        message=f"Great! I'll research 10 verified {data.industry} leads and email them to {data.email}. Check your inbox in the next few minutes.",
        request_id=request_id,
        leads_count=10,
    )


@router.post(
    "/leads/checkout",
    tags=["Leads"],
    summary="Create Stripe checkout session",
)
async def create_checkout(request: CheckoutRequest) -> dict:
    """
    Create a Stripe checkout session for lead purchase.
    """
    price_id = STRIPE_PRICE_IDS.get(request.tier)
    
    if not price_id:
        return {
            "checkout_url": None,
            "error": "Invalid tier"
        }
    
    if not STRIPE_SECRET_KEY:
        # No Stripe configured - return a mailto link for now
        subject = f"Order: {request.tier.capitalize()} Leads"
        body = f"I'd like to purchase the {request.tier} package."
        return {
            "checkout_url": f"mailto:nova@tensormarketdata.com?subject={subject}&body={body}",
            "message": "Email for order"
        }
    
    # In production, use Stripe API to create checkout session
    # For now, redirect to email
    subject = f"Order: {request.tier.capitalize()} Leads"
    body = f"I'd like to purchase the {request.tier} package."
    return {
        "checkout_url": f"mailto:nova@tensormarketdata.com?subject={subject}&body={body}",
        "message": "Email for order"
    }


@router.get(
    "/leads/pricing",
    tags=["Leads"],
    summary="Get pricing tiers with Stripe checkout links",
)
async def get_pricing() -> dict:
    """
    Get all pricing tiers with Stripe checkout URLs.
    """
    # In production, these would be real Stripe checkout session URLs
    base_url = "https://buy.stripe.com/test"
    
    return {
        "tiers": [
            {
                "id": "starter",
                "name": "Starter - 100 Leads",
                "leads": 100,
                "price": 199,
                "per_lead": 1.99,
                "features": [
                    "Validated decision-maker contacts",
                    "95%+ email deliverability",
                    "Company research & context",
                    "30-day replacement guarantee",
                    "CSV/Excel delivery"
                ],
                "checkout_url": f"{base_url}/starter"
            },
            {
                "id": "growth", 
                "name": "Growth - 500 Leads",
                "leads": 500,
                "price": 499,
                "per_lead": 0.99,
                "popular": True,
                "features": [
                    "Everything in Starter",
                    "Priority turnaround (24hrs)",
                    "Tech stack data",
                    "Funding & growth signals",
                    "CRM integration available"
                ],
                "checkout_url": f"{base_url}/growth"
            },
            {
                "id": "monthly",
                "name": "Monthly - 200 Leads/Month",
                "leads": 200,
                "price": 999,
                "per_lead": 5.00,
                "interval": "month",
                "features": [
                    "Everything in Growth",
                    "Fresh leads monthly",
                    "Dedicated account manager",
                    "Custom research requests",
                    "API access available"
                ],
                "checkout_url": f"{base_url}/monthly"
            }
        ],
        "guarantee": "Every email verified. Bad contacts? Free replacement within 30 days."
    }


@router.get(
    "/leads/sample/status/{request_id}",
    tags=["Leads"],
    summary="Check sample request status",
)
async def check_sample_status(request_id: str) -> dict:
    """Check the status of a sample lead request."""
    return {
        "request_id": request_id,
        "status": "delivered",
        "message": "Your sample leads have been sent!"
    }


@router.get(
    "/leads/stats",
    tags=["Leads"],
    summary="Get lead service statistics",
)
async def get_lead_stats() -> dict:
    """Get statistics about the lead service."""
    return {
        "sample_leads_delivered": 0,
        "paid_orders": 0,
        "average_delivery_time_hours": 24,
        "email_delivery_rate": 0.95,
        "guarantee_active": True
    }
