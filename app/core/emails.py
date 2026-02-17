"""
Email Templates for Order Flow
Based on copy pack specifications.
"""
from typing import Optional, Dict, Any
import os

# Email configuration
EMAIL_FROM = os.environ.get("EMAIL_FROM", "TensorMarketData <nova@tensormarketdata.com>")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://tensormarketdata.com")

# TODO: Implement actual email sending (Resend/Postmark/gog)
async def send_email(to: str, subject: str, body: str) -> bool:
    """Send email. Implement with actual provider."""
    print(f"📧 EMAIL to {to}: {subject}")
    print(f"   {body[:200]}...")
    return True

# ============ ORDER RECEIVED (PAID) ============
def order_received_email(order: Dict[str, Any], requirements: Dict[str, Any]) -> tuple:
    """Order Received - sent when paid order is created."""
    subject = "We received your order — ICP confirmation within 24 hours"
    
    body = f"""Hi {requirements.get('buyer_titles', {}).get('titles', ['Team'])[0].split(',')[0] or 'Team'},

We received your order request.

Summary:
- Package: {order['package'].upper()}
- Quantity: {order['quantity']} leads
- Industry: {requirements.get('target_industry')}
- Geography: {requirements.get('geography', {}).get('country', 'N/A')}
- Titles/personas: {', '.join(requirements.get('buyer_titles', {}).get('titles', []))}
- Company size: {requirements.get('company_size_range')}
- Outreach channel: {requirements.get('outreach_channel')}

Next steps:
- We'll confirm scope + delivery timeline within 24 hours.
- If you have a suppression list, reply to this email and attach it.

Reminder:
- 30-day 1:1 replacement for invalid emails (hard bounce / failed verification evidence).
- Replacement covers emails only; it does not guarantee replies, meetings, or revenue.

Thanks,
TensorMarketData
"""
    return subject, body

# ============ SAMPLE RECEIVED (FREE) ============
def sample_received_email(requirements: Dict[str, Any]) -> tuple:
    """Sample Received - sent when free sample is requested."""
    subject = "Sample request received — delivery within 24 hours"
    
    body = f"""Hi {requirements.get('buyer_titles', {}).get('titles', ['Team'])[0].split(',')[0] or 'Team'},

We received your free sample request (10 leads).

We'll email your sample within 24 hours.

Reminder: A "lead" is 1 verified decision-maker contact record (not an inbound conversion).

Thanks,
TensorMarketData
"""
    return subject, body

# ============ CLARIFICATION NEEDED ============
def clarification_needed_email(order: Dict[str, Any], question: str) -> tuple:
    """Clarification Needed - sent when admin needs more info."""
    subject = "Quick question to finalize your lead list"
    
    body = f"""Hi,

We're ready to start, but we need 1 clarification:

{question}

Once we have this, we'll confirm your delivery timeline.

Thanks,
TensorMarketData
"""
    return subject, body

# ============ ORDER ACCEPTED + ETA ============
def order_accepted_email(order: Dict[str, Any], eta: str) -> tuple:
    """Order Accepted + ETA - sent when order is accepted."""
    subject = f"Order confirmed — expected delivery {eta}"
    
    body = f"""Hi,

Your order is confirmed.

Expected delivery: {eta}

We'll deliver a CSV/Excel export with the package fields listed on the Pricing page.

Reminder:
- 30-day 1:1 replacement for invalid emails (hard bounce / failed verification evidence).

Thanks,
TensorMarketData
"""
    return subject, body

# ============ DELIVERY EMAIL ============
def delivery_email(order: Dict[str, Any], download_url: str) -> tuple:
    """Delivery Email - sent when order is delivered with signed link."""
    subject = "Your leads are ready — download inside"
    
    body = f"""Hi,

Your lead list is ready.

Download: {download_url}

Order summary:
- Package: {order['package'].upper()}
- Quantity: {order['quantity']} leads

Replacement guarantee:
- 30-day 1:1 replacement for invalid emails (hard bounce / failed verification evidence).

Thanks,
TensorMarketData
"""
    return subject, body

# ============ REPLACEMENT REQUEST RECEIVED ============
def replacement_received_email(order: Dict[str, Any]) -> tuple:
    """Replacement Request Received - sent when customer requests replacement."""
    subject = "Replacement request received"
    
    body = """Hi,

We received your replacement request.

Please reply with:
- Bounce evidence (hard bounce logs) OR verification output
- The affected email(s) / rows

Once received, we'll process replacements and send an updated file.

Thanks,
TensorMarketData
"""
    return subject, body

# ============ REPLACEMENT DELIVERED ============
def replacement_delivered_email(order: Dict[str, Any], download_url: str) -> tuple:
    """Replacement Delivered - sent when replacement is sent."""
    subject = "Replacement delivered — updated file"
    
    body = f"""Hi,

Your replacement is complete.

Updated download: {download_url}

Thanks,
TensorMarketData
"""
    return subject, body

# ============ SAMPLE UPSELL (FOLLOW-UP) ============
def sample_upsell_email(requirements: Dict[str, Any]) -> tuple:
    """Sample Upsell - sent 24h after sample delivery."""
    subject = "Want 200+ leads delivered in 48 hours?"
    
    body = f"""Hi,

Want 200+ leads like your sample?

Pro plan: $4.50/lead, 200 minimum
- Verified work email
- LinkedIn URL
- Company details + HQ location
- 30-day replacement guarantee
- Delivery in ~48 hours

Get started: {APP_BASE_URL}/get-started?package=pro

Thanks,
TensorMarketData
"""
    return subject, body


# ============ EMAIL DISPATCHER ============
async def dispatch_email(order_type: str, event: str, order: Optional[Dict] = None, 
                         requirements: Optional[Dict] = None, **kwargs) -> bool:
    """Route email sending based on event type."""
    
    if not order or not requirements:
        return False
    
    to = requirements.get("work_email")
    if not to:
        return False
    
    email_map = {
        ("order", "created"): order_received_email,
        ("sample", "created"): sample_received_email,
        ("order", "clarification_needed"): lambda o, r, **k: clarification_needed_email(o, k.get("question", "")),
        ("order", "accepted"): lambda o, r, **k: order_accepted_email(o, k.get("eta", "TBD")),
        ("order", "delivered"): lambda o, r, **k: delivery_email(o, k.get("download_url", "#")),
        ("order", "replacement_requested"): lambda o, r, **k: replacement_received_email(o),
        ("order", "replacement_delivered"): lambda o, r, **k: replacement_delivered_email(o, k.get("download_url", "#")),
    }
    
    key = (order_type, event)
    if key in email_map:
        subject, body = email_map[key](order, requirements, **kwargs)
        return await send_email(to, subject, body)
    
    return False
