"""
Leads API - Simple endpoints
"""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/leads/sample")
async def get_sample(
    email: str = Query(default="demo@example.com"),
    industry: str = Query(default="SaaS")
):
    """Get free sample leads."""
    return {
        "status": "success",
        "message": f"Great! I'll send 10 {industry} leads to {email}",
        "leads_count": 10,
        "email": email,
        "industry": industry
    }


@router.get("/leads/stats")
async def get_stats():
    """Get lead stats."""
    return {"samples": 0, "orders": 0}
