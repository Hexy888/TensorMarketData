# Reply Operations Models

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text


def utcnow() -> datetime:
    return datetime.utcnow()


class ReplyAudit(SQLModel, table=True):
    __tablename__ = "reply_audit"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    target_id: int = Field(index=True, foreign_key="outbound_targets.id")
    to_email: str = Field(index=True)
    template_key: str = Field(index=True)  # onboarding|pricing|question_generic|close_out
    subject: str = Field(default="", sa_column=Column(Text))
    body: str = Field(default="", sa_column=Column(Text))
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
