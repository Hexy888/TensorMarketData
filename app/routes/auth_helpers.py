from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from app.routes.context import get_current_user_and_business

def require_user_or_redirect(request: Request, session: Session):
    user, biz = get_current_user_and_business(request, session)
    
    if not user:
        return None, None, RedirectResponse("/login", status_code=303)
    
    if not biz:
        # user exists but has no business (should be rare); send to onboarding
        return user, None, RedirectResponse("/get-started", status_code=303)
    
    return user, biz, None
