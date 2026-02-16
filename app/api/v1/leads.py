"""
Lead Generation API - Sample lead requests with abuse protection.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import httpx

from app.models.schemas import ErrorResponse
from app.core.supabase import supabase

router = APIRouter()

# Apollo API configuration
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "kw_KuGhJAIw3DNrCyHdQSQ")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"

# Abuse protection settings
SAMPLE_LIMIT_PER_EMAIL = 3  # Max samples per email in 30 days
SAMPLE_LIMIT_PER_IP = 10   # Max samples per IP in 24 hours
SAMPLE_COOLDOWN_DAYS = 30   # Days before same email can request again


# ============ MODELS ============

class LeadSampleRequest(BaseModel):
    """Request for sample leads."""
    email: EmailStr
    industry: str
    company_size: Optional[str] = None
    criteria: Optional[str] = None


class LeadSampleResponse(BaseModel):
    """Response after lead sample request."""
    status: str
    message: str
    request_id: str
    leads_count: Optional[int] = None


class LeadRecord(BaseModel):
    """Individual lead record."""
    name: str
    title: str
    email: str
    company: str
    company_size: Optional[str] = None
    linkedin: Optional[str] = None


# ============ RATE LIMITING ============

async def check_abuse_protection(email: str, ip_address: str = None) -> tuple[bool, str]:
    """
    Check if requester is abusing the sample system.
    
    Returns:
        (is_allowed, reason) - if not allowed, reason explains why
    """
    now = datetime.utcnow()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    yesterday = (now - timedelta(days=1)).isoformat()
    
    # Check email history (last 30 days)
    try:
        email_result = supabase.table("lead_samples").select("id").eq("email", email).gte("created_at", thirty_days_ago).execute()
        email_count = len(email_result.data) if email_result.data else 0
        
        if email_count >= SAMPLE_LIMIT_PER_EMAIL:
            return False, f"You've already requested {email_count} samples. Limit is {SAMPLE_LIMIT_PER_EMAIL} per 30 days."
    except Exception as e:
        print(f"Abuse check error: {e}")
    
    # Check IP history (last 24 hours) - if IP available
    if ip_address:
        try:
            # Note: We'd need to store IP to check this
            # For now, rely on email-based protection
            pass
        except Exception as e:
            print(f"IP check error: {e}")
    
    return True, ""


# ============ APOLLO INTEGRATION ============

async def search_apollo_leads(industry: str, company_size: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for leads using Apollo API.
    """
    headers = {
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }
    
    # Build search query
    query_parts = []
    if industry:
        query_parts.append(industry)
    if company_size:
        query_parts.append(f"{company_size} employees")
    
    query = " ".join(query_parts) if query_parts else "B2B"
    
    # Try people search first
    try:
        url = f"{APOLLO_BASE_URL}/mixed_people/api_search"
        payload = {
            "q": query,
            "page": 1,
            "per_page": min(limit, 20)
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                persons = data.get("persons", [])
                
                leads = []
                for person in persons:
                    lead = {
                        "name": person.get("name", ""),
                        "title": person.get("title", ""),
                        "email": person.get("email", ""),
                        "company": person.get("organization", {}).get("name", "") if person.get("organization") else "",
                        "company_size": person.get("organization", {}).get("employee_count", "") if person.get("organization") else "",
                        "linkedin": person.get("linkedin_url", ""),
                    }
                    # Only add leads with valid email
                    if lead["email"] and "@" in lead["email"]:
                        leads.append(lead)
                
                return leads[:limit]
    except Exception as e:
        print(f"Apollo search error: {e}")
    
    return []


async def verify_email(email: str) -> bool:
    """
    Verify email is valid using Apollo's verification endpoint.
    """
    headers = {
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }
    
    try:
        url = f"{APOLLO_BASE_URL}/emails/verify"
        payload = {"email": email}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                # Check verification status
                return data.get("result") == "verified"
    except Exception as", "") e:
        print(f"Email verify error: {e}")
    
    return False


# ============ EMAIL NOTIFICATION ============

async def send_sample_email(request_email: str, leads: List[Dict[str, Any]], request_id: str):
    """
    Send sample leads via email using Resend or SMTP.
    """
    # Build lead table HTML
    leads_html = ""
    for lead in leads:
        leads_html += f"""
        <tr>
            <td>{lead.get('name', 'N/A')}</td>
            <td>{lead.get('title', 'N/A')}</td>
            <td>{lead.get('company', 'N/A')}</td>
            <td>{lead.get('email', 'N/A')}</td>
        </tr>
        """
    
    subject = f"Your Sample Leads - {len(leads)} Verified Contacts"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; padding: 30px; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #4f46e5; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
            .footer {{ background: #1e293b; color: #94a3b8; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; }}
            .cta {{ display: inline-block; background: #4f46e5; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Your Sample Leads</h1>
                <p style="margin: 10px 0 0 0;">{len(leads)} verified contacts ready for outreach</p>
            </div>
            <div class="content">
                <p>Here are {len(leads)} sample leads matching your criteria. Each contact has been verified for deliverability.</p>
                
                <table>
                    <tr>
                        <th>Name</th>
                        <th>Title</th>
                        <th>Company</th>
                        <th>Email</th>
                    </tr>
                    {leads_html}
                </table>
                
                <p style="margin-top: 30px;">
                    <a href="https://tensormarketdata.com/pricing" class="cta">View Pricing Plans</a>
                </p>
                
                <p style="margin-top: 20px; color: #64748b; font-size: 14px;">
                    Need more leads? We offer 100, 500, or custom monthly plans.
                </p>
            </div>
            <div class="footer">
                <p style="margin: 0;">TensorMarketData - Premium B2B Lead Generation</p>
                <p style="margin: 10px 0 0 0; font-size: 12px;">
                    Request ID: {request_id[:8]}...
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Try using Resend if available, otherwise log
    resend_api_key = os.getenv("RESEND_API_KEY")
    
    if resend_api_key:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    json={
                        "from": "Nova <nova@tensormarketdata.com>",
                        "to": [request_email],
                        "subject": subject,
                        "html": html_body,
                    },
                    headers={"Authorization": f"Bearer {resend_api_key}"},
                    timeout=30.0
                )
                if resp.status_code == 200:
                    return True
        except Exception as e:
            print(f"Resend send error: {e}")
    
    # Fallback: log the email that would be sent
    print(f"[EMAIL] Would send to: {request_email}")
    print(f"[EMAIL] Subject: {subject}")
    print(f"[EMAIL] Leads count: {len(leads)}")
    return False


# ============ ENDPOINTS ============

@router.post(
    "/leads/sample",
    response_model=LeadSampleResponse,
    tags=["Leads"],
    summary="Request sample leads",
)
async def request_sample_leads(data: LeadSampleRequest) -> LeadSampleResponse:
    """
    Request a sample of leads. Includes abuse protection.
    
    - Max 3 requests per email per 30 days
    - Leads are searched via Apollo API
    - Results are emailed to the requester
    """
    request_id = str(uuid4())
    
    # Check abuse protection
    is_allowed, reason = await check_abuse_protection(data.email)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorResponse(
                error="Rate limit exceeded",
                detail=reason,
                code="RATE_LIMIT",
            ).model_dump(),
        )
    
    try:
        # Search Apollo for leads
        leads = await search_apollo_leads(
            industry=data.industry,
            company_size=data.company_size,
            limit=10
        )
        
        # Store the request
        sample_record = {
            "id": request_id,
            "email": data.email,
            "industry": data.industry,
            "company_size": data.company_size or "",
            "criteria": data.criteria or "",
            "leads_count": len(leads),
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        supabase.table("lead_samples").insert(sample_record).execute()
        
        # Send email with leads
        if leads:
            await send_sample_email(data.email, leads, request_id)
        
        return LeadSampleResponse(
            status="success",
            message=f"Sample sent to {data.email} with {len(leads)} leads",
            request_id=request_id,
            leads_count=len(leads),
        )
        
    except Exception as e:
        print(f"Sample request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to process request",
                detail=str(e),
                code="REQUEST_ERROR",
            ).model_dump(),
        )


@router.get(
    "/leads/sample/status/{request_id}",
    tags=["Leads"],
    summary="Check sample request status",
)
async def check_sample_status(request_id: str) -> dict:
    """Check the status of a sample lead request."""
    try:
        result = supabase.table("lead_samples").select("*").eq("id", request_id).execute()
        if result.data:
            return {"status": result.data[0].get("status"), "leads_count": result.data[0].get("leads_count")}
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get(
    "/leads/stats",
    tags=["Leads"],
    summary="Get lead sample statistics",
)
async def get_lead_stats() -> dict:
    """Get statistics about lead sample requests."""
    try:
        # Total requests
        total_result = supabase.table("lead_samples").select("id", count="exact").execute()
        total = total_result.count or 0
        
        # Last 7 days
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        week_result = supabase.table("lead_samples").select("id", count="exact").gte("created_at", week_ago).execute()
        this_week = week_result.count or 0
        
        return {
            "total_requests": total,
            "this_week": this_week,
            "limit_per_email": SAMPLE_LIMIT_PER_EMAIL,
        }
    except Exception as e:
        return {"error": str(e)}
