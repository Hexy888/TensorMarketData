from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db import get_session
from app.services.ops import ops_run

router = APIRouter(prefix="/api/ops")

@router.post("/run")
def run_ops(
    business_id: int = 1,
    simulate: bool = True,
    simulate_n: int = 2,
    session: Session = Depends(get_session),
):
    return ops_run(session, business_id=business_id, simulate=simulate, simulate_n=simulate_n)
