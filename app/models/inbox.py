# Inbox Processing Models

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text


def utcnow() -> datetime:
    return datetime.utcnow()


class InboxProcessed(SQLModel, table=True):
    __tablename__ = "inbox_processed"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    
    # IMAP UID is mailbox-scoped, stable enough for idempotency
    imap_uid: str = Field(index=True, unique=True)
    from_email: str = Field(index=True)
    subject: str = Field(default="", sa_column=Column(Text))
    classification: str = Field(index=True)  # yes|question|later|optout|unknown
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
