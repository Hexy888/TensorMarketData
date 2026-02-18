from fastapi import APIRouter, Depends, Header
from sqlmodel import Session
from app.db import get_session
from app.config import settings
from app.services.digest import send_daily_digest

router = APIRouter(prefix="/api/ops")

def token_ok(x_ops_token: str | None) -> bool:
    if not settings.ops_token:
        return True
    return (x_ops_token or "") == settings.ops_token

@router.post("/digest")
def digest(
    x_ops_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    if not token_ok(x_ops_token):
        return {"ok": False, "error": "unauthorized"}
    
    sent = send_daily_digest(session)
    return {"ok": True, "sent": sent}
