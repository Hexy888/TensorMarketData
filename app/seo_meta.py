from dataclasses import dataclass
from urllib.parse import urljoin

@dataclass
class PageSEO:
    title: str
    description: str
    path: str

def canonical(base_url: str, path: str) -> str:
    base = (base_url or "").rstrip("/") + "/"
    p = (path or "").lstrip("/")
    return urljoin(base, p)

BASE_URL = "https://tensormarketdata.com"

DEFAULTS = {
    "home": PageSEO(
        title="Reputation Operations for HVAC — Approval-Gated Review Replies | TensorMarketData",
        description="We monitor reviews, draft replies fast, route negatives for approval, and automate review requests. No calls. Email-only ops. Start in 24 hours after access.",
        path="/",
    ),
    "pricing": PageSEO(
        title="Pricing — Reputation Ops for HVAC | TensorMarketData",
        description="Choose Monitor ($99), Automate ($199), or Multi-Location ($399). Monitoring, drafted replies, approval gates for negatives, and scorecards included.",
        path="/pricing",
    ),
    "how": PageSEO(
        title="How It Works — Approval-Gated Review Automation | TensorMarketData",
        description="Connect Google Business Profile, we monitor reviews, draft replies, route negatives for approval, and report weekly. Clean workflow, audit log included.",
        path="/how-it-works",
    ),
    "faq": PageSEO(
        title="FAQ — Reputation Operations | TensorMarketData",
        description="Answers about platforms, approvals, auto-posting, review requests, and what we do (and don't) do.",
        path="/faq",
    ),
    "blog": PageSEO(
        title="Blog — HVAC Reputation Ops Playbook | TensorMarketData",
        description="Reputation management tactics for HVAC: faster response, approval gates, review requests, and operational best practices.",
        path="/blog",
    ),
    "contact": PageSEO(
        title="Contact — TensorMarketData",
        description="Email-only support and sales. No phone calls. We respond within 1 business day.",
        path="/contact",
    ),
    "privacy": PageSEO(
        title="Privacy Policy — TensorMarketData",
        description="How we collect, use, and protect information for our reputation operations services.",
        path="/privacy",
    ),
    "terms": PageSEO(
        title="Terms of Service — TensorMarketData",
        description="Service terms for review monitoring, response drafting, approval workflows, and reporting.",
        path="/terms",
    ),
}
