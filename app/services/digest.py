import os
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.tenant_models import Business, DraftReply, AuditLog
from app.services.email_smtp import send_smtp_email

def digest_enabled() -> bool:
    return os.getenv("DIGEST_DAILY", "true").lower() == "true"

def digest_to() -> str:
    return os.getenv("ALERT_TO_EMAIL", "")

def build_digest(session: Session) -> dict:
    since = datetime.utcnow() - timedelta(hours=24)
    
    # Pending approvals
    pending = session.exec(select(DraftReply).where(DraftReply.status == "pending")).all()
    pending_count = len(pending)
    
    # Failures in last 24h
    failed = session.exec(
        select(AuditLog).where(
            AuditLog.created_at >= since,
            (AuditLog.action.contains("failed")) | (AuditLog.action.contains("error"))
        ).order_by(AuditLog.created_at.desc()).limit(100)
    ).all()
    
    # Recent ops summaries
    ops = session.exec(
        select(AuditLog).where(
            AuditLog.created_at >= since,
            (AuditLog.action == "ops_all_summary") | (AuditLog.action == "gbp_reconcile_done")
        ).order_by(AuditLog.created_at.desc()).limit(80)
    ).all()
    
    businesses = session.exec(select(Business).where(Business.gbp_connected == True)).all()
    
    return {
        "pending_count": pending_count,
        "fail_count": len(failed),
        "gbp_connected_count": len(businesses),
        "fail_events": failed,
        "ops_events": ops,
        "time_utc": datetime.utcnow().isoformat() + "Z",
    }

def send_daily_digest(session: Session) -> bool:
    if not digest_enabled():
        return False
    
    to_email = digest_to()
    if not to_email:
        return False
    
    d = build_digest(session)
    
    def row(a):
        detail = (a.detail or "")[:140]
        return f"<tr><td style='padding:6px 8px;border-bottom:1px solid #e5e7eb'>{a.created_at}</td><td style='padding:6px 8px;border-bottom:1px solid #e5e7eb'>{a.action}</td><td style='padding:6px 8px;border-bottom:1px solid #e5e7eb'>{detail}</td></tr>"
    
    fail_rows = "".join([row(x) for x in d["fail_events"][:25]]) or "<tr><td colspan=3 style='padding:8px'>None</td></tr>"
    ops_rows = "".join([row(x) for x in d["ops_events"][:25]]) or "<tr><td colspan=3 style='padding:8px'>None</td></tr>"
    
    html = f"""
    <div style="font-family:system-ui;line-height:1.45">
     <h2 style="margin:0 0 8px">TensorMarketData Daily Digest</h2>
     <div style="color:#475569;margin-bottom:14px">UTC: {d["time_utc"]}</div>
     <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px">
      <div style="border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px"><b>GBP Connected</b><br/>{d["gbp_connected_count"]}</div>
      <div style="border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px"><b>Pending Approvals</b><br/>{d["pending_count"]}</div>
      <div style="border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px"><b>Failures (24h)</b><br/>{d["fail_count"]}</div>
     </div>
     <h3 style="margin:12px 0 8px">Failures (latest)</h3>
     <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
      <tr style="background:#f8fafc"><th style="text-align:left;padding:8px">Time</th><th style="text-align:left;padding:8px">Action</th><th style="text-align:left;padding:8px">Detail</th></tr>
      {fail_rows}
     </table>
     <h3 style="margin:14px 0 8px">Ops + Reconcile (latest)</h3>
     <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
      <tr style="background:#f8fafc"><th style="text-align:left;padding:8px">Time</th><th style="text-align:left;padding:8px">Action</th><th style="text-align:left;padding:8px">Detail</th></tr>
      {ops_rows}
     </table>
     <div style="margin-top:14px">
      <a href="https://tensormarketdata.com/admin" style="display:inline-block;padding:10px 12px;border-radius:12px;background:#2563eb;color:#fff;text-decoration:none">Open Admin</a>
      <a href="https://tensormarketdata.com/app/approvals" style="display:inline-block;padding:10px 12px;border-radius:12px;border:1px solid #e5e7eb;color:#0f172a;text-decoration:none;margin-left:8px">Open Approvals</a>
     </div>
    </div>
    """
    return send_smtp_email(to_email, "TensorMarketData — Daily Digest", html)
