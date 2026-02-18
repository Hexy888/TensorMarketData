from fastapi import APIRouter, Depends, Header
from sqlmodel import Session, select
from app.db import get_session
from app.config import settings
from app.tenant_models import Business
from app.services.gbp_reconcile import reconcile_business
from app.services.alerts import send_alert

router = APIRouter(prefix="/api/ops")

def token_ok(x_ops_token: str | None) -> bool:
    if not settings.ops_token:
        return True
    return (x_ops_token or "") == settings.ops_token

@router.post("/reconcile_all")
def reconcile_all(
    x_ops_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    if not token_ok(x_ops_token):
        return {"ok": False, "error": "unauthorized"}
    
    businesses = session.exec(select(Business).where(Business.gbp_connected == True)).all()
    
    results = []
    any_err = False
    mism = 0
    for b in businesses:
        r = reconcile_business(session, b.id)
        results.append({"business_id": b.id, "name": b.name, "result": r})
        if not r.get("ok", True):
            any_err = True
        mism += int(r.get("mismatches", 0) or 0)
    
    # Alert if issues found
    if any_err or mism > 0:
        send_alert(
            "TensorMarketData — Reconcile issues",
            f"<p>Errors: <b>{any_err}</b> · Mismatches: <b>{mism}</b></p>",
        )
    
    return {"ok": True, "count": len(results), "results": results}
