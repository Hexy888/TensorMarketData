from datetime import datetime
from sqlmodel import Session, select
from app.models import Business, AuditLog
from app.services.ops import ops_run

def audit(session: Session, business_id: int, action: str, detail: str):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def run_ops_for_all(session: Session, simulate: bool = False, simulate_n: int = 0) -> dict:
    """
    Iterates all businesses with gbp_connected=true and runs ops per business.
    Returns summary counts + per-business result.
    """
    businesses = session.exec(select(Business).where(Business.gbp_connected == True)).all()
    
    results = []
    ok_count = 0
    fail_count = 0
    
    for biz in businesses:
        try:
            r = ops_run(session, business_id=biz.id, simulate=simulate, simulate_n=simulate_n)
            results.append({"business_id": biz.id, "business_name": biz.name, "result": r})
            ok_count += 1 if r.get("ok") else 0
            fail_count += 0 if r.get("ok") else 1
            
            # Write a compact summary audit entry
            if r.get("noop"):
                audit(session, biz.id, "ops_all_noop", r.get("reason", "noop"))
            else:
                audit(
                    session, biz.id, "ops_all_summary",
                    f"pulled={r.get('pulled_stub')} drafts_created={r.get('drafts_created')} autoposted={r.get('autoposted')} pending={r.get('pending_for_approval')}",
                )
        except Exception as e:
            fail_count += 1
            results.append({"business_id": biz.id, "business_name": biz.name, "error": str(e)})
            audit(session, biz.id, "ops_all_error", str(e))
    
    return {
        "ok": True,
        "time_utc": datetime.utcnow().isoformat() + "Z",
        "businesses_total_connected": len(businesses),
        "ran_ok": ok_count,
        "ran_fail": fail_count,
        "results": results[:50],
    }
