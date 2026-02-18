from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api")

class TrackEvent(BaseModel):
    event: str
    props: dict = {}
    ts: int | None = None

@router.post("/track")
async def track(evt: TrackEvent, request: Request):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent","")[:160]
    print(f"[TRACK] {datetime.utcnow().isoformat()}Z ip={ip} ua={ua} event={evt.event} props={evt.props}")
    return {"ok": True}
