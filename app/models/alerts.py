# Alerts Model

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text


def utcnow() -> datetime:
    return datetime.utcnow()


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
    severity: str = Field(default="warn", index=True)  # info|warn|error|critical
    kind: str = Field(index=True)  # gbp_auth|gbp_quota|gbp_verification|openai|pipeline
    client_id: Optional[int] = Field(default=None, index=True, foreign_key="clients.id")
    location_id: Optional[int] = Field(default=None, index=True, foreign_key="client_locations.id")
    message: str = Field(default="", sa_column=Column(Text))
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="open", index=True)  # open|acked|resolved
