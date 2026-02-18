# Outbound Pipeline - Main Orchestration
# Search → Enrich (bulk) → Draft → Send

import os
from datetime import datetime
from app.integrations.apollo_client import ApolloClient, ApolloPersonShell, TITLE_FILTERS
from app.services.outbound_repo_sql import OutboundRepoSQLModel
from app.services.email_sender import send_email_smtp, EmailSendError
from app.services.outbound_repo import is_valid_business_email, normalize_domain, email_domain

APP_BASE_URL = os.getenv("APP_BASE_URL", "https://tensormarketdata.com")
SEND_CAP_DAILY = int(os.getenv("SEND_CAP_DAILY", "20"))
ENRICH_CAP_DAILY = int(os.getenv("ENRICH_CAP_DAILY", str(SEND_CAP_DAILY * 2)))
PHYSICAL_ADDRESS = os.getenv("PHYSICAL_ADDRESS", "").strip()


EMAIL_TEMPLATES = {
    "A": {
        "subject": "Quick question about reviews at {company}",
        "body": (
            "Hi {first_or_team},\n\n"
            "I run TensorMarketData — we handle reputation operations for HVAC: monitor reviews, draft replies fast, "
            "and route 1–3★ to you for approval before anything posts.\n\n"
            "{personalization}"
            "If you want this handled without extra staff, reply \"YES\" and I'll send a 2-minute onboarding link.\n\n"
            "— Nova\n"
            "TensorMarketData\n\n"
            "Opt out: reply \"opt out\"\n"
            "Address: {address}\n"
        ),
    },
    "B": {
        "subject": "Approval-gated review replies for {company}",
        "body": (
            "Hi {first_or_team},\n\n"
            "Negative replies shouldn't auto-post. We run an approval-gated workflow for HVAC: drafts for everything, "
            "approval queue for 1–3★, audit log, and weekly scorecards.\n\n"
            "{personalization}"
            "Want the onboarding link? Reply \"YES\".\n\n"
            "— Nova\n"
            "TensorMarketData\n\n"
            "Opt out: reply \"opt out\"\n"
            "Address: {address}\n"
        ),
    },
    "C": {
        "subject": "More 5★ reviews (without being pushy)",
        "body": (
            "Hi {first_or_team},\n\n"
            "We operate a clean review system for HVAC: monitoring + drafted replies + (optional) email-based review requests "
            "with one follow-up max.\n\n"
            "{personalization}"
            "If you want the setup link, reply \"YES\".\n\n"
            "— Nova\n"
            "TensorMarketData\n\n"
            "Opt out: reply \"opt out\"\n"
            "Address: {address}\n"
        ),
    },
}


def _pick_variant_round_robin(i: int) -> str:
    """7/7/6 distribution per 20 is handled by caller."""
    return ["A", "B", "C"][i % 3]


def _first_or_team(first: str | None) -> str:
    if first and first.strip():
        return first.strip()
    return "there"


class OutboundPipeline:
    def __init__(self, repo: OutboundRepoSQLModel):
        self.repo = repo
        self.apollo = ApolloClient()

    # --------- Stage 1: Search (no credits) ----------
    def apollo_search_shells(self, *, company_name: str | None = None, domain: str | None = None, limit: int = 25):
        shells = self.apollo.people_search_api(
            q_organization_name=company_name if company_name else None,
            q_organization_domains=[domain] if domain else None,
            person_titles=TITLE_FILTERS,
            per_page=min(limit, 50),
            page=1,
        )
        return shells[:limit]

    # --------- Stage 2: Enrich (credits) - bulk ----------
    def enrich_and_insert_daily(self, shells: list[ApolloPersonShell]) -> dict:
        enriched_today = self.repo.count_events_today(event_type="enrich")
        remaining = max(ENRICH_CAP_DAILY - enriched_today, 0)
        
        if remaining <= 0:
            return {"ok": True, "enriched": 0, "inserted": 0, "reason": "enrich cap reached"}

        to_enrich = shells[:remaining]
        inserted = 0
        enriched = 0

        # Batch size 10 (Apollo bulk_match max)
        for i in range(0, len(to_enrich), 10):
            batch = to_enrich[i:i + 10]
            people_payload = [{"person_id": s.person_id} for s in batch if s.person_id]
            
            if not people_payload:
                continue

            try:
                enriched_contacts = self.apollo.people_bulk_match(people_payload)
            except Exception:
                continue

            enriched += len(people_payload)

            for c in enriched_contacts:
                email = (c.email or "").strip().lower()
                if not is_valid_business_email(email):
                    continue

                dom = normalize_domain(c.organization_domain) or email_domain(email)
                if not dom:
                    continue

                if self.repo.is_opted_out(email=email, domain=dom):
                    continue
                if self.repo.has_target(email=email, domain=dom):
                    continue

                target_id = self.repo.insert_target(
                    company_name=c.organization_name or "Unknown",
                    website_domain=dom,
                    city=c.city,
                    state=c.state,
                    contact_email=email,
                    contact_role="owner",
                    source="apollo",
                    notes=f"Apollo: {c.title}".strip(),
                )

                self.repo.log_event(
                    target_id=target_id,
                    event_type="enrich",
                    meta={"person_id": c.person_id, "title": c.title},
                )
                self.repo.mark_status(target_id=target_id, status="new")
                inserted += 1

        return {"ok": True, "enriched": enriched, "inserted": inserted, "cap": ENRICH_CAP_DAILY}

    # --------- Stage 3: Draft copy ----------
    def draft_copy_for_queued(self, target_rows: list[dict]) -> dict:
        drafted = 0
        for i, t in enumerate(target_rows):
            variant = _pick_variant_round_robin(i)
            tpl = EMAIL_TEMPLATES[variant]
            
            personalization = ""  # Keep blank by default (safe)
            
            body = tpl["body"].format(
                first_or_team=_first_or_team(t.get("first_name")),
                personalization=(personalization + "\n") if personalization else "",
                company=t.get("company_name") or "your company",
                address=PHYSICAL_ADDRESS,
            )
            subject = tpl["subject"].format(company=t.get("company_name") or "your company")

            self.repo.store_email_draft(
                target_id=int(t["id"]),
                variant=variant,
                subject=subject,
                body=body,
                personalization_used=bool(personalization),
            )
            self.repo.log_event(
                target_id=int(t["id"]), 
                event_type="queued", 
                meta={"variant": variant, "subject": subject}
            )
            self.repo.mark_status(target_id=int(t["id"]), status="queued")
            drafted += 1

        return {"ok": True, "drafted": drafted}

    # --------- Stage 4: Send with caps ----------
    def send_daily_cap(self) -> dict:
        sent_today = self.repo.count_events_today(event_type="sent")
        remaining = max(SEND_CAP_DAILY - sent_today, 0)
        
        if remaining <= 0:
            return {"ok": True, "sent": 0, "reason": "send cap reached"}

        batch = self.repo.fetch_queued_drafts(limit=remaining)
        sent = 0
        bounces = 0
        consecutive_errors = 0

        for item in batch:
            target_id = int(item["id"])
            to_email = item["contact_email"]
            subject = item["draft_subject"]
            body = item["draft_body"]

            try:
                # Opt-out final guard
                dom = normalize_domain(item.get("website_domain")) or email_domain(to_email)
                if self.repo.is_opted_out(email=to_email, domain=dom):
                    self.repo.mark_status(target_id=target_id, status="opted_out")
                    self.repo.log_event(target_id=target_id, event_type="optout", meta={"auto": True})
                    continue

                send_email_smtp(to_email=to_email, subject=subject, body_text=body)
                self.repo.log_event(target_id=target_id, event_type="sent", meta={"subject": subject})
                self.repo.mark_status(target_id=target_id, status="sent")
                sent += 1
                consecutive_errors = 0
                
            except Exception as e:
                bounces += 1
                consecutive_errors += 1
                self.repo.log_event(
                    target_id=target_id, 
                    event_type="bounce", 
                    meta={"error": str(e)[:300]}
                )
                self.repo.mark_status(target_id=target_id, status="bounced")
                
                if consecutive_errors >= 3:
                    # Stop for the day (deliverability protection)
                    break

        return {"ok": True, "sent": sent, "bounces": bounces, "cap": SEND_CAP_DAILY}
