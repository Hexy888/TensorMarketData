from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    default_business_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_user_id: int = Field(index=True)  # User.id
    name: str
    industry: str = "HVAC"
    approval_email: str
    autopost_positive: bool = False
    gbp_connected: bool = False
    gbp_account_name: Optional[str] = Field(default=None, index=True)
    gbp_location_name: Optional[str] = Field(default=None, index=True)
    gbp_location_title: Optional[str] = Field(default=None)
    brand_voice: str = "Professional, calm, helpful. No arguments. Offer resolution."
    stripe_customer_id: Optional[str] = Field(default=None, index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True)
    plan: str  # A, B, C
    status: str = "active"  # active, past_due, canceled
    stripe_subscription_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True)
    platform: str = "GBP"
    rating: int
    reviewer_name: str = ""
    review_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    external_id: str = Field(index=True, default="")

class DraftReply(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: int = Field(index=True)
    business_id: int = Field(index=True)
    draft_text: str
    status: str = "pending"  # pending, approved, rejected, posted, post_failed
    gbp_review_name: str = Field(default="", index=True)
    posted_at: Optional[datetime] = None
    posted_error: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True)
    action: str
    detail: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Onboarding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: Optional[int] = Field(default=None, index=True)
    business_name: str
    approval_email: str
    plan: str  # A/B/C
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GBPCredential(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True, unique=True)
    access_token: str = ""
    refresh_token_enc: str = ""
    token_expiry_utc: Optional[datetime] = None
    scopes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Outbound growth models
class OutboundTarget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    company_name: str
    website_url: Optional[str] = Field(default=None)
    location_city: str
    location_state: str
    gbp_url: Optional[str] = Field(default=None)
    contact_email: str
    contact_role: str = "unknown"  # owner/gm/office/admin/unknown
    owner_name: Optional[str] = Field(default=None)
    source: str = "manual"  # maps/directory/vendor/manual
    notes: Optional[str] = Field(default=None)
    status: str = "new"  # new/queued/sent/replied/opted_out/bounced/converted

class OutboundEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    target_id: int = Field(index=True)
    event_type: str  # queued/sent/open/click/reply/bounce/optout/convert
    meta: str = ""  # JSON text

class OutboundOptout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email_or_domain: str = Field(index=True, unique=True)
    reason: Optional[str] = Field(default=None)

class Experiment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    week_label: str  # e.g. "2026-W08"
    hypothesis: str
    change: str
    metric_primary: str  # reply_rate/signup_rate/booked_async_rate
    metric_secondary: str  # bounce/optout/CTR
    result: Optional[str] = Field(default=None)
    decision: str = "pending"  # keep/kill/iterate/pending

# Apollo-sourced HVAC accounts (raw, before enrichment)
class HVACAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    company_name: str
    website_url: Optional[str] = Field(default=None)
    domain: Optional[str] = Field(default=None)
    city: str
    state: str
    # Apollo-sourced person (if available)
    apollo_person_id: Optional[str] = Field(default=None)
    person_name: Optional[str] = Field(default=None)
    person_title: Optional[str] = Field(default=None)
    person_email: Optional[str] = Field(default=None)
    person_linkedin: Optional[str] = Field(default=None)
    # Status
    status: str = "raw"  # raw/enriched/queued/sent/replied/opted_out
    source: str = "apollo"
