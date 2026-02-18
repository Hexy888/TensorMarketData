from fastapi import APIRouter
from app.deps import require_ops
from app.services.email_tx import send_template

router = APIRouter()

@router.post("/api/ops/email_test")
def email_test(ok=require_ops):
    send_template(
        "nova@tensormarketdata.com",
        "TensorMarketData — SMTP test",
        "welcome.html",
        business={"name": "SMTP Test", "plan": "B"},
        login_url="https://tensormarketdata.com",
        support="nova@tensormarketdata.com",
        brand="TensorMarketData"
    )
    return {"ok": True}
