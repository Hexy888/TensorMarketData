"""
Leads API - Simple endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SampleRequest(BaseModel):
    email: str = "demo@example.com"
    industry: str = "SaaS"


@router.post("/leads/sample")
async def request_sample(request: SampleRequest = SampleRequest()):
    """Request free sample leads."""
    return {
        "status": "success",
        "message": f"Great! I'll send 10 {request.industry} leads to {request.email}",
        "leads_count": 10
    }


@router.get("/leads/stats")
async def get_stats():
    """Get lead stats."""
    return {"samples": 0, "orders": 0}
