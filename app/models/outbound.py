# Outbound Models - SQLModel tables

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text, JSON


def utcnow() -> datetime:
    return datetime.utcnow()


class OutboundTarget(SQLModel, table=True):
    __tablename__ = "outbound_targets"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
    
    # Core identity
    company_name: str = Field(index=True)
    website_domain: Optional[str] = Field(default=None, index=True)
    location_city: Optional[str] = Field(default=None, index=True)
    location_state: Optional[str] = Field(default=None, index=True)
    owner_name: Optional[str] = Field(default=None)
    contact_email: str = Field(index=True)
    contact_role: str = Field(default="unknown", index=True)  # owner/gm/office/admin/unknown
    source: str = Field(default="manual", index=True)  # apollo/maps/directory/vendor/manual
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="new", index=True)  # new/queued/sent/replied/opted_out/bounced/converted
    
    # Email draft storage
    draft_variant: Optional[str] = Field(default=None, index=True)
    draft_subject: Optional[str] = Field(default=None, sa_column=Column(Text))
    draft_body: Optional[str] = Field(default=None, sa_column=Column(Text))
    draft_personalization_used: bool = Field(default=False)
    
    # Optional helper fields
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)


class OutboundEvent(SQLModel, table=True):
    __tablename__ = "outbound_events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    target_id: int = Field(index=True, foreign_key="outbound_targets.id")
    event_type: str = Field(index=True)  # queued/sent/open/click/reply/bounce/optout/convert/enrich
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class OutboundOptout(SQLModel, table=True):
    __tablename__ = "outbound_optouts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    email_or_domain: str = Field(index=True, unique=True)
    reason: str = Field(default="optout", sa_column=Column(Text))


class Experiment(SQLModel, table=True):
    __tablename__ = "experiments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    week_label: str = Field(index=True)  # "2026-W08"
    hypothesis: str = Field(sa_column=Column(Text))
    change: str = Field(sa_column=Column(Text))
    metric_primary: str = Field(default="reply_rate")
    metric_secondary: str = Field(default="bounce_rate")
    result: str = Field(default="", sa_column=Column(Text))
    decision: str = Field(default="iterate")  # keep/kill/iterate


# Alias for case-insensitive import compatibility
OutboundOptOut = OutboundOptout

