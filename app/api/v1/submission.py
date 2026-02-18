"""
Data Submission API endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.supabase import supabase
from app.models.schemas import ErrorResponse

router = APIRouter()


class SubmissionCreate(BaseModel):
    """Schema for data submission."""
    company_name: str
    website: Optional[str] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    products: Optional[str] = None
    categories: Optional[list[str]] = None
    source_type: str
    source_date: datetime


class SubmissionResponse(BaseModel):
    """Response after successful submission."""
    submission_id: str
    status: str
    message: str


@router.post(
    "/submit",
    response_model=SubmissionResponse,
    tags=["Data"],
    summary="Submit supplier data",
)
async def submit_data(data: SubmissionCreate) -> SubmissionResponse:
    """
    Submit supplier data for review.
    Data is verified before being added to the marketplace.
    """
    try:
        # Create submission record
        submission = {
            "id": str(uuid4()),
            "company_name": data.company_name,
            "website": data.website,
            "description": data.description,
            "email": data.email,
            "phone": data.phone,
            "linkedin": data.linkedin,
            "products": data.products,
            "categories": data.categories,
            "source_type": data.source_type,
            "source_date": data.source_date.isoformat(),
            "status": "pending",
            "submitted_at": datetime.utcnow().isoformat(),
        }

        # Store in submissions table
        await supabase.query(
            "submissions",
            method="POST",
            data=submission,
        )

        return SubmissionResponse(
            submission_id=submission["id"],
            status="pending",
            message="Submission received. Verification typically takes 24-48 hours.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Submission failed",
                detail=str(e),
                code="SUBMISSION_ERROR",
            ).model_dump(),
        )


@router.get(
    "/submissions",
    tags=["Data"],
    summary="List your submissions",
)
async def list_submissions(api_key_id: str):
    """
    List all submissions for an API key.
    """
    try:
        # Get submissions for this provider
        result = await supabase.query(
            "submissions",
            params={"select": "*", "limit": 50},
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to fetch submissions",
                detail=str(e),
                code="FETCH_ERROR",
            ).model_dump(),
        )


@router.post(
    "/submissions/{submission_id}/verify",
    tags=["Data"],
    summary="Verify and approve a submission",
)
async def verify_submission(submission_id: str):
    """
    Move a submission to the suppliers table.
    Admin only in production.
    """
    try:
        # Get submission
        result = await supabase.query(
            "submissions",
            params={"id": f"eq.{submission_id}", "select": "*"},
        )
        submission = result[0] if result else None

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Submission not found",
                    detail=f"No submission with ID {submission_id}",
                    code="NOT_FOUND",
                ).model_dump(),
            )

        if submission.get("status") != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="Submission already processed",
                    detail=f"Status is {submission.get('status')}",
                    code="ALREADY_PROCESSED",
                ).model_dump(),
            )

        # Create supplier from submission
        supplier = {
            "id": str(uuid4()),
            "name": submission["company_name"],
            "contact_json": {
                "email": submission.get("email"),
                "phone": submission.get("phone"),
                "linkedin": submission.get("linkedin"),
            },
            "verification_score": 0.7,  # Verified by admin
            "source": f"submission:{submission_id}",
        }

        await supabase.query(
            "suppliers",
            method="POST",
            data=supplier,
        )

        # Update submission status
        await supabase.query(
            "submissions",
            method="PATCH",
            params={"id": f"eq.{submission_id}"},
            data={"status": "approved", "processed_at": datetime.utcnow().isoformat()},
        )

        return {"status": "approved", "supplier_id": supplier["id"]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Verification failed",
                detail=str(e),
                code="VERIFY_ERROR",
            ).model_dump(),
        )
