"""
Email subscription API endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.email import email_service
from app.models.schemas import ErrorResponse

router = APIRouter()


# ============ MODELS ============

class SubscribeRequest(BaseModel):
    """Email subscription request."""
    email: EmailStr
    source: str = "website"


class SubscribeResponse(BaseModel):
    """Subscription response."""
    status: str
    email: str


class UnsubscribeRequest(BaseModel):
    """Unsubscribe request."""
    email: EmailStr


class CountResponse(BaseModel):
    """Subscriber count response."""
    count: int


# ============ ENDPOINTS ============

@router.post(
    "/email/subscribe",
    response_model=SubscribeResponse,
    tags=["Email"],
    summary="Subscribe to email updates",
)
async def subscribe(data: SubscribeRequest) -> SubscribeResponse:
    """
    Subscribe an email to marketing updates.
    """
    try:
        result = await email_service.subscribe(data.email)
        return SubscribeResponse(
            status=result["status"],
            email=data.email,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to subscribe",
                detail=str(e),
                code="SUBSCRIBE_ERROR",
            ).model_dump(),
        )


@router.post(
    "/email/unsubscribe",
    tags=["Email"],
    summary="Unsubscribe from emails",
)
async def unsubscribe(data: UnsubscribeRequest) -> dict:
    """
    Unsubscribe an email from marketing updates.
    """
    try:
        result = await email_service.unsubscribe(data.email)
        return {"status": result["status"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to unsubscribe",
                detail=str(e),
                code="UNSUBSCRIBE_ERROR",
            ).model_dump(),
        )


@router.get(
    "/email/count",
    response_model=CountResponse,
    tags=["Email"],
    summary="Get subscriber count",
)
async def get_count() -> CountResponse:
    """
    Get the number of active subscribers.
    """
    count = await email_service.get_count()
    return CountResponse(count=count)


@router.get(
    "/email/subscribers",
    tags=["Email"],
    summary="List subscribers (admin)",
)
async def get_subscribers() -> dict:
    """
    Get list of active subscribers.
    In production, would require admin auth.
    """
    subscribers = await email_service.get_subscribers()
    return {
        "subscribers": [
            {"email": s["email"], "subscribed_at": s["subscribed_at"]}
            for s in subscribers
        ],
        "total": len(subscribers),
    }
