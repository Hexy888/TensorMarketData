# Gmail State Model

from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


def utcnow() -> datetime:
    return datetime.utcnow()


class GmailState(SQLModel, table=True):
    __tablename__ = "gmail_state"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email_address: str = Field(index=True, unique=True)
    last_history_id: str = Field(default="", index=True)
    watch_expiration_ms: Optional[int] = Field(default=None)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
