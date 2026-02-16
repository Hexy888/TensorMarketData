"""
User Authentication API endpoints.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Cookie
from pydantic import BaseModel, EmailStr

from app.core.auth import auth_service, create_session_token, User
from app.models.schemas import ErrorResponse

router = APIRouter()


# Session storage (in production, use Redis)
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str  # Min 8 chars
    name: str  # Min 2 chars


class LoginResponse(BaseModel):
    """Login response."""
    user_id: str
    email: str
    name: str
    credits: int
    session_token: str


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    name: str
    credits: int
    created_at: str


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    tags=["Auth"],
    summary="Login with email and password",
)
async def login(data: LoginRequest) -> LoginResponse:
    """
    Login with email and password.
    Returns a session token for authenticated requests.
    """
    user, error = await auth_service.login(data.email, data.password)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Login failed",
                detail=error,
                code="AUTH_INVALID",
            ).model_dump(),
        )
    
    # Create session
    session_token = create_session_token()
    sessions[session_token] = {
        "user_id": user.id,
        "expires": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    
    return LoginResponse(
        user_id=user.id,
        email=user.email,
        name=user.name,
        credits=user.credits,
        session_token=session_token,
    )


@router.post(
    "/auth/register",
    response_model=LoginResponse,
    tags=["Auth"],
    summary="Create a new account",
)
async def register(data: RegisterRequest) -> LoginResponse:
    """
    Register a new account.
    """
    # Validate password length
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Invalid password",
                detail="Password must be at least 8 characters",
                code="INVALID_PASSWORD",
            ).model_dump(),
        )
    
    # Validate name length
    if len(data.name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Invalid name",
                detail="Name must be at least 2 characters",
                code="INVALID_NAME",
            ).model_dump(),
        )
    
    user, error = await auth_service.register(data.email, data.password, data.name)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Registration failed",
                detail=error,
                code="AUTH_REGISTER_ERROR",
            ).model_dump(),
        )
    
    # Create session
    session_token = create_session_token()
    sessions[session_token] = {
        "user_id": user.id,
        "expires": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    
    return LoginResponse(
        user_id=user.id,
        email=user.email,
        name=user.name,
        credits=user.credits,
        session_token=session_token,
    )


# API Key generation for agents (no account needed)
class AgentAPIKeyResponse(BaseModel):
    """Response for agent API key generation."""
    api_key: str
    user_id: str
    email: str
    name: str
    credits: int


@router.post(
    "/auth/api-key",
    response_model=AgentAPIKeyResponse,
    tags=["Auth"],
    summary="Generate API key for AI agents (no account needed)",
)
async def generate_agent_api_key():
    """
    Generate a free API key for AI agents.
    No account or email required. Gives 10 free credits to try the API.
    """
    import uuid
    
    # Generate a unique API key
    api_key = f"tmd_agent_{secrets.token_urlsafe(32)}"
    
    # Generate a unique user ID
    user_id = str(uuid.uuid4())
    
    # Return the API key info
    return AgentAPIKeyResponse(
        api_key=api_key,
        user_id=user_id,
        email="agent@tensormarketdata.com",
        name="API Agent",
        credits=10,
    )


@router.post(
    "/auth/logout",
    tags=["Auth"],
    summary="Logout and invalidate session",
)
async def logout(session_token: str = Cookie(None)):
    """Logout and invalidate the session."""
    if session_token and session_token in sessions:
        del sessions[session_token]
    return {"status": "logged_out"}


async def get_current_user(session_token: str = Cookie(None)) -> Optional[User]:
    """Get the current authenticated user."""
    if not session_token or session_token not in sessions:
        return None
    
    session = sessions.get(session_token)
    if not session:
        return None
    
    # Check expiration
    expires = datetime.fromisoformat(session["expires"])
    if expires < datetime.utcnow():
        del sessions[session_token]
        return None
    
    return await auth_service.get_user(session["user_id"])


@router.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["Auth"],
    summary="Get current user profile",
)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get the current authenticated user's profile.
    Requires authentication.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Not authenticated",
                detail="Please login to access this resource",
                code="AUTH_REQUIRED",
            ).model_dump(),
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        credits=user.credits,
        created_at=user.created_at,
    )

__all__ = ['router']
