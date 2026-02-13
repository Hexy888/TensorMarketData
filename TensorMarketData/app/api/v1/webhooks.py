"""
Webhook API endpoints for AI agent real-time updates.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, HttpUrl

from app.services.webhook import (
    webhook_service,
    WebhookEvent,
    EventBuilder,
)
from app.core.auth import auth_service, create_session_token, User
from app.api.v1.auth_routes import get_current_user
from app.models.schemas import ErrorResponse

router = APIRouter()


# ============ MODELS ============

class CreateSubscriptionRequest(BaseModel):
    """Create webhook subscription."""
    url: HttpUrl
    events: List[str]
    description: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Webhook subscription response."""
    id: str
    url: str
    events: List[str]
    secret: str
    active: bool
    created_at: str


class SubscriptionListResponse(BaseModel):
    """List subscriptions response."""
    subscriptions: List[SubscriptionResponse]


class EventPayload(BaseModel):
    """Test webhook event payload."""
    event_type: str
    data: dict


# ============ ENDPOINTS ============

@router.post(
    "/webhooks/subscribe",
    response_model=SubscriptionResponse,
    tags=["Webhooks"],
    summary="Subscribe to webhook events",
)
async def create_subscription(
    data: CreateSubscriptionRequest,
    user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """
    Create a webhook subscription for real-time updates.
    
    AI agents can subscribe to events like:
    - supplier.updated
    - supplier.new
    - product.new
    - product.stock_change
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    # Validate events
    valid_events = WebhookEvent.all()
    for event in data.events:
        if event not in valid_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="Invalid event type",
                    detail=f"Event must be one of: {valid_events}",
                    code="INVALID_EVENT",
                ).model_dump(),
            )
    
    try:
        subscription = await webhook_service.create_subscription(
            url=str(data.url),
            events=data.events,
        )
        
        return SubscriptionResponse(
            id=subscription.id,
            url=subscription.url,
            events=subscription.events,
            secret=subscription.secret,
            active=subscription.active,
            created_at=subscription.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to create subscription",
                detail=str(e),
                code="WEBHOOK_ERROR",
            ).model_dump(),
        )


@router.get(
    "/webhooks",
    response_model=SubscriptionListResponse,
    tags=["Webhooks"],
    summary="List webhook subscriptions",
)
async def list_subscriptions(
    event_type: Optional[str] = None,
    user: User = Depends(get_current_user),
) -> SubscriptionListResponse:
    """List all webhook subscriptions."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    subscriptions = await webhook_service.list_subscriptions(event_type)
    
    return SubscriptionListResponse(
        subscriptions=[
            SubscriptionResponse(
                id=s.id,
                url=s.url,
                events=s.events,
                secret="[hidden]",  # Don't show secret in list
                active=s.active,
                created_at=s.created_at,
            )
            for s in subscriptions
        ]
    )


@router.delete(
    "/webhooks/{subscription_id}",
    tags=["Webhooks"],
    summary="Delete a webhook subscription",
)
async def delete_subscription(
    subscription_id: str,
    user: User = Depends(get_current_user),
) -> dict:
    """Delete a webhook subscription."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    success = await webhook_service.delete_subscription(subscription_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error="Subscription not found",
                code="NOT_FOUND",
            ).model_dump(),
        )
    
    return {"status": "deleted"}


@router.post(
    "/webhooks/test",
    tags=["Webhooks"],
    summary="Send a test webhook event",
)
async def test_webhook(
    payload: EventPayload,
    user: User = Depends(get_current_user),
) -> dict:
    """Send a test webhook event to verify your endpoint."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    # Build event
    event_data = getattr(EventBuilder, payload.event_type.replace(".", "_"))(
        **payload.data
    )
    
    # Emit event
    results = await webhook_service.emit_event(
        event_type=payload.event_type,
        payload=event_data,
    )
    
    return {"delivered": len(results)}


@router.get(
    "/webhooks/events",
    tags=["Webhooks"],
    summary="Get available webhook events",
)
async def get_available_events() -> dict:
    """Get list of available webhook event types."""
    return {
        "events": WebhookEvent.all(),
        "descriptions": {
            "supplier.updated": "Fired when a supplier's data changes",
            "supplier.new": "Fired when a new supplier is added",
            "product.new": "Fired when a new product is listed",
            "product.stock_change": "Fired when product stock levels change",
        },
    }


@router.get(
    "/webhooks/history/{subscription_id}",
    tags=["Webhooks"],
    summary="Get webhook delivery history",
)
async def get_delivery_history(
    subscription_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
) -> dict:
    """Get delivery history for a subscription."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    history = await webhook_service.get_history(subscription_id, limit)
    
    return {
        "subscription_id": subscription_id,
        "deliveries": history,
    }
