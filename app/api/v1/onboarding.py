"""
Onboarding API for TensorMarketData - Reputation Operations.
Handles onboarding form submission and client status.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class OnboardingRequest(BaseModel):
    business_name: str
    website_url: Optional[str] = None
    contact_email: str
    escalation_email: str
    business_type: str
    platforms: List[str]
    tone: str = "professional"
    signoff: str = "Ops Team"
    autopost: bool = False
    request_source: Optional[str] = None
    channels: List[str] = ["email"]
    package: str = "package_a"


class ClientStatusResponse(BaseModel):
    client_id: str
    status: str
    onboarding_complete: bool
    access_granted: bool
    access_verified: bool


@router.post("")
async def submit_onboarding(
    request: OnboardingRequest,
):
    """
    Submit onboarding form.
    
    In production, this would:
    1. Create client record in database
    2. Create client settings
    3. Create onboarding status record
    4. Send transactional emails
    5. Schedule first sync job
    """
    # Validate required fields
    if not request.business_name:
        raise HTTPException(status_code=400, detail="Business name is required")
    
    if not request.contact_email:
        raise HTTPException(status_code=400, detail="Contact email is required")
    
    if not request.escalation_email:
        raise HTTPException(status_code=400, detail="Escalation email is required")
    
    if not request.platforms:
        raise HTTPException(status_code=400, detail="At least one platform is required")
    
    # Validate package
    valid_packages = ["package_a", "package_b", "package_c"]
    if request.package not in valid_packages:
        request.package = "package_a"
    
    # In production: Save to database
    # For now, return success with mock client_id
    client_id = f"client_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "success": True,
        "client_id": client_id,
        "message": "Onboarding submitted successfully",
        "next_step": "/access",
        "status": "onboarding_complete",
        "access_status": "pending",
    }


@router.get("/status/{client_id}")
async def get_client_status(client_id: str):
    """
    Get client onboarding and access status.
    """
    # In production: Query database
    # For now, return mock status
    return {
        "client_id": client_id,
        "status": "pending_access",
        "onboarding_complete": True,
        "access_granted": False,
        "access_verified": False,
        "platforms": {
            "google": "pending",
            "yelp": "not_requested",
        },
    }


@router.post("/access/verify")
async def verify_access(client_id: str):
    """
    Request verification of platform access.
    """
    # In production: Trigger verification job
    return {
        "success": True,
        "message": "Verification requested",
        "client_id": client_id,
        "estimated_time": "24 hours",
    }
