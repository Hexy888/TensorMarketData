# Onboarding State Model

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


def utcnow() -> datetime:
    return datetime.utcnow()


class OnboardingState(SQLModel, table=True):
    __tablename__ = "onboarding_state"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
    client_id: int = Field(index=True, foreign_key="clients.id", unique=True)
    go_live: bool = Field(default=False, index=True)
    connected_google: bool = Field(default=False, index=True)
    selected_location: bool = Field(default=False, index=True)
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
