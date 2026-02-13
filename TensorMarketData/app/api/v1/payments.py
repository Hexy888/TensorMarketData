"""
Payment API endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.stripe import stripe_service, CREDIT_PACKAGES, PROVIDER_REVENUE_SHARE
from app.core.auth import auth_service, create_session_token, User
from app.api.v1.auth_routes import get_current_user
from app.models.schemas import ErrorResponse

router = APIRouter()


# ============ MODELS ============

class CreateCustomerRequest(BaseModel):
    """Create Stripe customer."""
    email: EmailStr
    name: Optional[str] = None


class CheckoutSessionRequest(BaseModel):
    """Create checkout session."""
    package: str  # starter, pro, enterprise
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Checkout session response."""
    session_id: str
    url: str


class ConnectAccountRequest(BaseModel):
    """Create Connect account for providers."""
    email: EmailStr
    return_url: str


class ConnectAccountResponse(BaseModel):
    """Connect account response."""
    account_id: str
    onboarding_url: str


class TransferRequest(BaseModel):
    """Transfer funds to provider."""
    amount_cents: int
    description: Optional[str] = None


class TransferResponse(BaseModel):
    """Transfer response."""
    transfer_id: str
    amount: int


# ============ ENDPOINTS ============

@router.post(
    "/payments/customer",
    tags=["Payments"],
    summary="Create a Stripe customer",
)
async def create_customer(
    data: CreateCustomerRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """
    Create a Stripe customer for the current user.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    try:
        customer = await stripe_service.create_customer(
            email=data.email or user.email,
            name=data.name or user.name,
        )
        return {"customer_id": customer["id"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to create customer",
                detail=str(e),
                code="STRIPE_ERROR",
            ).model_dump(),
        )


@router.post(
    "/payments/checkout",
    response_model=CheckoutSessionResponse,
    tags=["Payments"],
    summary="Create a credit purchase session",
)
async def create_checkout_session(
    data: CheckoutSessionRequest,
    user: User = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout session to purchase credits.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    if data.package not in CREDIT_PACKAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Invalid package",
                detail=f"Package must be one of: {list(CREDIT_PACKAGES.keys())}",
                code="INVALID_PACKAGE",
            ).model_dump(),
        )
    
    try:
        session = await stripe_service.create_credit_package_session(
            customer_id=user.id,  # In production, would be Stripe customer ID
            package_id=data.package,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
        )
        return CheckoutSessionResponse(
            session_id=session["id"],
            url=session["url"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to create checkout",
                detail=str(e),
                code="STRIPE_ERROR",
            ).model_dump(),
        )


@router.post(
    "/payments/connect",
    response_model=ConnectAccountResponse,
    tags=["Payments"],
    summary="Create a provider Connect account",
)
async def create_connect_account(
    data: ConnectAccountRequest,
    user: User = Depends(get_current_user),
) -> ConnectAccountResponse:
    """
    Create a Stripe Connect account for a data provider.
    This allows providers to receive payouts.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    try:
        account = await stripe_service.create_connect_account(
            provider_email=data.email,
        )
        
        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account["id"],
            refresh_url=data.return_url,
            return_url=data.return_url,
            type="account_onboarding",
        )
        
        return ConnectAccountResponse(
            account_id=account["id"],
            onboarding_url=account_link["url"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to create Connect account",
                detail=str(e),
                code="STRIPE_ERROR",
            ).model_dump(),
        )


@router.get(
    "/payments/connect/balance",
    tags=["Payments"],
    summary="Get provider account balance",
)
async def get_provider_balance(
    account_id: str,
    user: User = Depends(get_current_user),
) -> dict:
    """
    Get the balance of a provider's Connect account.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    try:
        balance_cents = await stripe_service.get_account_balance(account_id)
        return {
            "balance_cents": balance_cents,
            "balance_dollars": balance_cents / 100,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to get balance",
                detail=str(e),
                code="STRIPE_ERROR",
            ).model_dump(),
        )


@router.post(
    "/payments/transfer",
    response_model=TransferResponse,
    tags=["Payments"],
    summary="Transfer funds to provider",
)
async def transfer_to_provider(
    data: TransferRequest,
    user: User = Depends(get_current_user),
) -> TransferResponse:
    """
    Transfer funds to a data provider (admin only in production).
    """
    # In production, would verify admin permissions
    
    try:
        transfer = await stripe_service.create_transfer(
            amount=data.amount_cents,
            destination_account="acct_example",  # Would come from database
            description=data.description,
        )
        return TransferResponse(
            transfer_id=transfer["id"],
            amount=transfer["amount"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to create transfer",
                detail=str(e),
                code="STRIPE_ERROR",
            ).model_dump(),
        )


@router.post(
    "/payments/webhook",
    tags=["Payments"],
    summary="Stripe webhook endpoint",
)
async def stripe_webhook(
    payload: bytes,
    signature: str,
) -> dict:
    """
    Handle Stripe webhooks.
    """
    try:
        event = stripe_service.construct_webhook_event(payload, signature)
        result = await stripe_service.handle_webhook(event)
        return {"status": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Webhook failed",
                detail=str(e),
                code="WEBHOOK_ERROR",
            ).model_dump(),
        )


# ============ PRICING INFO ============

@router.get(
    "/payments/pricing",
    tags=["Payments"],
    summary="Get credit package pricing",
)
async def get_pricing() -> dict:
    """Get available credit packages and pricing."""
    return {
        "packages": CREDIT_PACKAGES,
        "revenue_share_percent": PROVIDER_REVENUE_SHARE * 100,
    }
