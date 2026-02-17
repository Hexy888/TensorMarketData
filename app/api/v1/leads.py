"""
Leads API
"""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/hello")
async def hello():
    """Test endpoint - hello."""
    return {"message": "hello from leads"}


@router.get("/sample-leads")
async def get_sample(
    email: str = Query(default="demo@example.com"),
    industry: str = Query(default="SaaS")
):
    """Get free sample leads."""
    return {
        "status": "success",
        "message": f"I'll send 10 {industry} leads to {email}",
        "leads_count": 10,
        "email": email,
        "industry": industry
    }


@router.get("/stats")
async def get_stats():
    """Get lead stats."""
    return {"samples": 0, "orders": 0}
