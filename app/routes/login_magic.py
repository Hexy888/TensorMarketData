from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.db import get_session
from app.security_magic import verify
from app.security import sign_session
from app.models import User

router = APIRouter(prefix="/login")

@router.get("/magic")
def login_magic(request: Request, token: str, session: Session = Depends(get_session)):
    data = verify(token)
    if not data:
        return RedirectResponse("/login?bad=1", status_code=303)
    
    email = data.get("email", "")
    biz_id = int(data.get("business_id", 0) or 0)
    
    u = session.exec(select(User).where(User.email == email)).first()
    if not u:
        return RedirectResponse("/login?bad=1", status_code=303)
    
    # Set session cookie
    sess = sign_session({"email": email, "business_id": biz_id, "user": True})
    resp = RedirectResponse("/app", status_code=303)
    resp.set_cookie("tmd_session", sess, httponly=True, samesite="lax")
    return resp
