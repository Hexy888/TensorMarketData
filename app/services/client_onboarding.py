# Onboarding Service
# Handles client onboarding workflow: get started → welcome → connect GBP → approval routing → first drafts

from datetime import datetime
from sqlmodel import Session
from app.models import Business, User
from app.services.email_tx import send_template
from app.security_magic import sign

APP_BASE_URL = "https://tensormarketdata.com"

def get_onboarding_context(business: Business) -> dict:
    """Generate onboarding context for a business."""
    return {
        "business_name": business.name,
        "plan": getattr(business, 'plan', 'A'),
        "approval_email": business.approval_email,
        "service_area_city": getattr(business, 'location_city', ''),
        "service_area_state": getattr(business, 'location_state', ''),
        "brand_voice": business.brand_voice if hasattr(business, 'brand_voice') else "Professional Warm",
        "auto_post_4_5_star": business.autopost_positive if hasattr(business, 'autopost_positive') else False,
        "require_approval_1_3_star": True,  # Always true
        "gbp_connected": business.gbp_connected,
    }

def send_welcome_email(session: Session, business: Business, user: User) -> bool:
    """Send welcome email with magic link."""
    # Generate magic link
    token = sign({"email": user.email, "business_id": business.id}, ttl_seconds=60*60*24*7)  # 7 days
    magic_link = f"{APP_BASE_URL}/login/magic?token={token}"
    
    try:
        send_template(
            business.approval_email,
            "Welcome — connect Google Business Profile (2 minutes)",
            "welcome.html",
            business=get_onboarding_context(business),
            magic_link=magic_link,
            support="nova@tensormarketdata.com",
            brand="TensorMarketData"
        )
        return True
    except Exception as e:
        print(f"[WELCOME EMAIL ERROR] {e}")
        return False

def send_gbp_connected_email(business: Business) -> bool:
    """Send confirmation when GBP is connected."""
    try:
        send_template(
            business.approval_email,
            "GBP Connected — next: approvals",
            "gbp_connected.html",
            business=get_onboarding_context(business),
            portal_link=f"{APP_BASE_URL}/app",
            support="nova@tensormarketdata.com",
            brand="TensorMarketData"
        )
        return True
    except Exception as e:
        print(f"[GBP CONNECTED EMAIL ERROR] {e}")
        return False

def send_drafts_ready_email(business: Business, pending_count: int) -> bool:
    """Send notification when drafts are ready."""
    if pending_count == 0:
        return False  # Don't email if nothing to review
    
    try:
        send_template(
            business.approval_email,
            "Replies ready for approval",
            "drafts_ready.html",
            business=get_onboarding_context(business),
            pending_count=pending_count,
            approvals_link=f"{APP_BASE_URL}/app/approvals",
            support="nova@tensormarketdata.com",
            brand="TensorMarketData"
        )
        return True
    except Exception as e:
        print(f"[DRAFTS READY EMAIL ERROR] {e}")
        return False

def send_first_week_day1_email(business: Business) -> bool:
    """Day 1 after GBP connect - what happens next."""
    try:
        send_template(
            business.approval_email,
            "What happens next (no work needed)",
            "first_week_day1.html",
            business=get_onboarding_context(business),
            portal_link=f"{APP_BASE_URL}/app",
            support="nova@tensormarketdata.com",
            brand="TensorMarketData"
        )
        return True
    except Exception as e:
        print(f"[FIRST WEEK DAY1 EMAIL ERROR] {e}")
        return False

def send_weekly_scorecard_email(business: Business, stats: dict) -> bool:
    """Weekly scorecard email."""
    try:
        send_template(
            business.approval_email,
            "Weekly scorecard is ready",
            "weekly_scorecard.html",
            business=get_onboarding_context(business),
            stats=stats,
            portal_link=f"{APP_BASE_URL}/app",
            support="nova@tensormarketdata.com",
            brand="TensorMarketData"
        )
        return True
    except Exception as e:
        print(f"[WEEKLY SCORECARD EMAIL ERROR] {e}")
        return False

def send_onboarding_link_email(contact_email: str, business_name: str) -> bool:
    """Send onboarding link to a lead who said YES."""
    try:
        send_template(
            contact_email,
            "Onboarding link — TensorMarketData",
            "onboarding_link.html",
            business_name=business_name,
            onboarding_link=f"{APP_BASE_URL}/get-started",
            support="nova@tensormarketdata.com",
            brand="TensorMarketData"
        )
        return True
    except Exception as e:
        print(f"[ONBOARDING LINK EMAIL ERROR] {e}")
        return False

# Safety/legal keywords for escalation
SAFETY_KEYWORDS = [
    'threat', 'violence', 'lawsuit', 'attorney', 'police', 
    'fraud', 'scam', 'bbb', 'osha', 'discrimination', 
    'harassment', 'sue', 'legal', 'court', 'lawyer'
]

def contains_safety_legal(content: str) -> bool:
    """Check if content contains safety/legal triggers."""
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in SAFETY_KEYWORDS)

def get_onboarding_checklist(business: Business) -> dict:
    """Get onboarding checklist status for a business."""
    return {
        "gbp_connected": business.gbp_connected,
        "approval_email_confirmed": bool(business.approval_email),
        "posting_settings_configured": hasattr(business, 'autopost_positive'),
        "first_sync_completed": False,  # Would check audit log
    }
