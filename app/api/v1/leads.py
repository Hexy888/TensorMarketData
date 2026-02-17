"""
Leads API - Simple endpoints
"""
from fastapi import APIRouter, Query

router = APIRouter()


@router.post("/leads/sample")
async def request_sample(
    email: str = Query(...),
    industry: str = Query(...)
):
    """Request free sample leads."""
    return {
        "status": "success",
        "message": f"Great! I'll send 10 {industry} leads to {email}",
        "leads_count": 10
    }


@router.get("/leads/stats")
async def get_stats():
    """Get lead stats."""
    return {"samples": 0, "orders": 0}
