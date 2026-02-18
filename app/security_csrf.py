import secrets
from fastapi import Request
from fastapi.responses import RedirectResponse

CSRF_COOKIE = "tmd_csrf"
CSRF_FIELD = "csrf_token"

def ensure_csrf_cookie(resp):
    if CSRF_COOKIE not in resp.headers.get("set-cookie", ""):
        token = secrets.token_urlsafe(24)
        resp.set_cookie(CSRF_COOKIE, token, httponly=True, samesite="lax")
    return resp

def get_csrf_token(request: Request) -> str:
    return request.cookies.get(CSRF_COOKIE, "")

def verify_csrf(request: Request, form_token: str) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    return bool(cookie_token) and bool(form_token) and (cookie_token == form_token)

def csrf_fail_redirect() -> RedirectResponse:
    return RedirectResponse("/app?csrf=1", status_code=303)
