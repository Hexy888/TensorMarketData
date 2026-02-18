from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()
BASE = "https://tensormarketdata.com"

@router.get("/robots.txt")
def robots():
    txt = f"""User-agent: *
Allow: /
Sitemap: {BASE}/sitemap.xml
"""
    return Response(content=txt, media_type="text/plain")

@router.get("/sitemap.xml")
def sitemap():
    urls = [
        "/",
        "/pricing",
        "/how-it-works",
        "/faq",
        "/blog",
        "/contact",
        "/privacy",
        "/terms"
    ]
    items = "\n".join([f"<url><loc>{BASE}{p}</loc></url>" for p in urls])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>"""
    return Response(content=xml, media_type="application/xml")
