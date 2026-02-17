"""
Lead Generation API - Simple endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/leads/sample")
async def test_leads():
    """Test endpoint."""
    return {"status": "ok", "message": "Leads API working"}


@router.post("/leads/sample")
async def request_sample():
    """Request sample leads."""
    return {
        "status": "success", 
        "message": "Sample request received! We'll email you shortly.",
        "leads_count": 10
    }


@router.get("/leads/stats")
async def get_stats():
    """Get lead stats."""
    return {
        "sample_requests": 0,
        "paid_orders": 0
    }
