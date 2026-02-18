# Public Thank You Page

from __future__ import annotations
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter()

SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "nova@tensormarketdata.com")


@router.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse(
        "public/thank_you.html",
        {"request": request, "support_email": SUPPORT_EMAIL}
    )
