"""
API Key authentication middleware.
Validates keys via Supabase REST API.
"""

from typing import Optional
import hashlib
from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.supabase import supabase
from app.models.domain import APIKey as APIKeyModel
from app.models.schemas import ErrorResponse

# API Key header
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


def create_mock_api_key(key: str, key_hash: str) -> APIKeyModel:
    """Create a mock API key object for testing."""
    return APIKeyModel(
        id="test-id",
        key_hash=key_hash,
        key_prefix=key[:12] if len(key) >= 12 else key,
        credits_remaining=100,
        is_active=1,
    )


async def validate_api_key(
    request: Request,
    api_key_header_value: Optional[str] = Depends(api_key_header),
) -> APIKeyModel:
    """
    Validate API key from header and return the key record.
    Raises HTTPException if invalid.
    """
    api_key = api_key_header_value
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Missing API key",
                detail=f"Provide key in '{settings.api_key_header}' header",
                code="AUTH_MISSING_KEY",
            ).model_dump(),
        )

    # Hash the provided key for comparison
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Support agent API keys (start with tmd_agent_)
    if api_key.startswith("tmd_agent_"):
        # Create a mock record for agent keys
        return create_mock_api_key(api_key, key_hash)

    # Try to validate against Supabase
    api_key_record = None
    try:
        api_key_record = await supabase.get_api_key(key_hash)
    except Exception as e:
        import logging
        logging.warning(f"Supabase auth error: {e}")

    if not api_key_record:
        # For testing without DB, create a mock
        if not settings.debug:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error="Invalid API key",
                    detail="Key is invalid or revoked",
                    code="AUTH_INVALID_KEY",
                ).model_dump(),
            )
        return create_mock_api_key(api_key, key_hash)

    # Check expiration
    if api_key_record.get("expires_at") and api_key_record["expires_at"] < datetime.utcnow().isoformat():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="API key expired",
                detail="Renew your key to continue",
                code="AUTH_KEY_EXPIRED",
            ).model_dump(),
        )

    # Check credits
    credits = api_key_record.get("credits_remaining", 0)
    if credits < settings.credits_per_search:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=ErrorResponse(
                error="Insufficient credits",
                detail=f"Need {settings.credits_per_search} credits, have {credits}",
                code="AUTH_INSUFFICIENT_CREDITS",
            ).model_dump(),
        )

    # Create API key object from record
    return APIKeyModel(
        id=api_key_record["id"],
        key_hash=api_key_record["key_hash"],
        key_prefix=api_key_record["key_prefix"],
        credits_remaining=credits,
        is_active=api_key_record["is_active"],
        created_at=api_key_record.get("created_at"),
        last_used_at=api_key_record.get("last_used_at"),
        expires_at=api_key_record.get("expires_at"),
    )


__all__ = ["validate_api_key"]
