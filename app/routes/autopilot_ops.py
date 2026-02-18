# Autopilot Operations Routes

import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.services.autopilot_engine import AutopilotEngine

OPS_TOKEN = os.getenv("OPS_TOKEN", "")

router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


@router.post("/api/ops/outbound/autopilot/run")
def autopilot_run(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """
    Run due autopilot tasks (follow-ups).
    """
    engine = AutopilotEngine(session)
    return engine.run_due_tasks()
