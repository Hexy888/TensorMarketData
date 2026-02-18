from fastapi import APIRouter, Depends, Header
from sqlmodel import Session, select
from app.db import get_session
from app.config import settings
from app.tenant_models import Business
from app.services.ops import ops_run
from app.services.alerts import send_alert

router = APIRouter(prefix="/api/ops")

def token_ok(x_ops_token: str | None) -> bool:
    # If no token configured, allow (dev). If configured, require match.
    if not settings.ops_token:
        return True
    return (x_ops_token or "") == settings.ops_token

@router.post("/run_all")
def run_all_ops(
    simulate: bool = False,
    simulate_n: int = 0,
    x_ops_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    if not token_ok(x_ops_token):
        return {"ok": False, "error": "unauthorized"}
    
    # Get all businesses
    businesses = session.exec(select(Business)).all()
    
    results = []
    ran_fail = 0
    for biz in businesses:
        result = ops_run(session, business_id=biz.id, simulate=simulate, simulate_n=simulate_n)
        results.append({
            "business_id": biz.id,
            "business_name": biz.name,
            "result": result
        })
        if not result.get("ok", True):
            ran_fail += 1
    
    # Alert if failures detected
    if ran_fail > 0:
        send_alert(
            "TensorMarketData — Ops failures detected",
            f"<p><b>{ran_fail}</b> business runs failed.</p><pre style='white-space:pre-wrap'>{results}</pre>",
        )
    
    return {
        "ok": True,
        "businesses_processed": len(results),
        "ran_fail": ran_fail,
        "results": results
    }
