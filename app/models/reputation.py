# Reputation Service Models

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, Text


def utcnow() -> datetime:
    return datetime.utcnow()


class Client(SQLModel, table=True):
    __tablename__ = "clients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    plan: str = Field(default="starter", index=True)  # starter|growth|scale
    status: str = Field(default="active", index=True)  # active|paused|canceled
    gbp_refresh_token: str = Field(default="", sa_column=Column(Text))


class ClientLocation(SQLModel, table=True):
    __tablename__ = "client_locations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    client_id: int = Field(index=True, foreign_key="clients.id")
    gbp_account_name: str = Field(default="", index=True)  # e.g. "accounts/123"
    gbp_location_name: str = Field(default="", index=True)  # e.g. "locations/456"
    display_name: str = Field(default="", index=True)
    address: str = Field(default="", sa_column=Column(Text))
    status: str = Field(default="active", index=True)


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
    client_id: int = Field(index=True, foreign_key="clients.id")
    location_id: int = Field(index=True, foreign_key="client_locations.id")
    gbp_review_name: str = Field(index=True, unique=True)  # e.g. "accounts/.../locations/.../reviews/..."
    reviewer_name: str = Field(default="", index=True)
    rating: int = Field(default=0, index=True)  # 1-5
    comment: str = Field(default="", sa_column=Column(Text))
    review_time: Optional[datetime] = Field(default=None, index=True)
    has_reply: bool = Field(default=False, index=True)
    reply_text: str = Field(default="", sa_column=Column(Text))
    status: str = Field(default="new", index=True)  # new|drafted|needs_approval|approved|posted|skipped|error
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class ReplyDraft(SQLModel, table=True):
    __tablename__ = "reply_drafts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
    review_id: int = Field(index=True, foreign_key="reviews.id")
    client_id: int = Field(index=True, foreign_key="clients.id")
    draft_text: str = Field(default="", sa_column=Column(Text))
    status: str = Field(default="drafted", index=True)  # drafted|needs_approval|approved|posted|rejected
    approved_by: str = Field(default="", index=True)  # admin email or "client" or "system"
    approved_at: Optional[datetime] = Field(default=None)
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class WeeklyReport(SQLModel, table=True):
    __tablename__ = "weekly_reports"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    client_id: int = Field(index=True, foreign_key="clients.id")
    week_start: datetime = Field(index=True)
    week_end: datetime = Field(index=True)
    summary_md: str = Field(default="", sa_column=Column(Text))
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
