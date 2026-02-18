# Autopilot Models

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text


def utcnow() -> datetime:
    return datetime.utcnow()


class AutopilotTask(SQLModel, table=True):
    __tablename__ = "autopilot_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
    target_id: int = Field(index=True, foreign_key="outbound_targets.id")
    task_type: str = Field(index=True)  # followup_1|followup_2|followup_3|snooze_followup
    due_at: datetime = Field(index=True)
    status: str = Field(default="pending", index=True)  # pending|done|skipped|canceled
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class AutopilotState(SQLModel, table=True):
    __tablename__ = "autopilot_state"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)  # e.g. "pause_until"
    value: str = Field(default="", sa_column=Column(Text))
    updated_at: datetime = Field(default_factory=utcnow, index=True)
