# Outbound Email Templates
# Variants A, B, C + Follow-ups + Responses

VARIANT_A_SUBJECT = "Quick question about reviews at {company}"
VARIANT_A_BODY = """Hi {first_or_team},

I run TensorMarketData — we handle reputation operations for HVAC: monitor reviews, draft replies fast, and route 1–3★ to you for approval before anything posts.

{personalization_line}
If you want this handled without extra staff, reply "YES" and I'll send a 2-minute onboarding link.

— Nova
TensorMarketData

Opt out: reply "opt out"
"""

VARIANT_B_SUBJECT = "Approval-gated review replies for {company}"
VARIANT_B_BODY = """Hi {first_or_team},

Negative replies shouldn't auto-post. We run an approval-gated workflow for HVAC: drafts for everything, approval queue for 1–3★, audit log, and weekly scorecards.

{personalization_line}
Want the onboarding link? Reply "YES".

— Nova, TensorMarketData

Opt out: reply "opt out"
"""

VARIANT_C_SUBJECT = "More 5★ reviews (without being pushy)"
VARIANT_C_BODY = """Hi {first_or_team},

We operate a clean review system for HVAC: monitoring + drafted replies + (optional) email-based review requests with one follow-up max.

{personalization_line}
If you want the setup link, reply "YES".

— Nova, TensorMarketData

Opt out: reply "opt out"
"""

FOLLOWUP_2_SUBJECT = "Re: {company}"
FOLLOWUP_2_BODY = """Just checking — should I send the onboarding link? If not relevant, reply "opt out" and I'll close the loop.

— Nova

Opt out: reply "opt out"
"""

FOLLOWUP_3_SUBJECT = "Last note"
FOLLOWUP_3_BODY = """Last note from me — we run email-only reputation ops for HVAC (approval gates for negatives). Reply "YES" for the onboarding link, or "opt out" to stop.

— Nova

Opt out: reply "opt out"
"""

RESPONSE_INTERESTED_SUBJECT = "Onboarding link — TensorMarketData"
RESPONSE_INTERESTED_BODY = """Thanks — here's your onboarding link: https://tensormarketdata.com/get-started

What you'll need:
- Approval email (who approves negatives)
- Google Business Profile access (or invite us)

That's it. No calls required.

— Nova
"""

RESPONSE_QUESTIONS_SUBJECT = "How it works — TensorMarketData"
RESPONSE_QUESTIONS_BODY = """Here's the workflow:

1) Connect Google Business Profile
2) We monitor reviews and draft replies
3) 1–3★ go to approvals (never auto-post)
4) Optional review requests (Package B/C)
5) Weekly scorecard + audit log

Details: https://tensormarketdata.com/how-it-works

— Nova
"""

RESPONSE_OPTOUT_SUBJECT = "Confirmed — removed"
RESPONSE_OPTOUT_BODY = """Confirmed — you're removed and won't be contacted again.

— Nova
"""

# Physical address (placeholder - update with real address)
PHYSICAL_ADDRESS = "TensorMarketData, LLC"
