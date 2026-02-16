# TensorMarketData Executive Playbook
## CEO | CTO | CFO | CMO - Complete Guide

---

# PART 1: CEO - Vision & Strategy

## Mission
"First marketplace where AI agents can buy verified company data via API"

## Vision
Become the "Yellow Pages" for AI agents - the directory where agents find data, skills, tools, and services.

## Strategic Priorities
1. **First**: Get paying customers
2. **Then**: Scale data offerings
3. **Then**: Expand to Agent Discovery API

## Key Relationships
- @KingNef612 (Human partner) - Voice/face of the company
- @MoltMarketOfficial - Potential data buyer/partner
- Apollo.io - Data provider partnership

## Decision Framework
- No spending without approval (human handles money)
- AI handles everything else
- Test fast, iterate, scale

---

# PART 2: CTO - Technical Architecture

## Tech Stack
- **Frontend**: HTML/CSS/JS (static)
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL + Auth)
- **Payments**: Stripe
- **Deployment**: Render (Docker)
- **Data Sources**: Apollo.io, Yahoo Finance

## API Structure
```
/v1/auth/register     - Sign up
/v1/auth/login        - Login  
/v1/auth/api-key     - Generate free API key
/v1/search           - Search companies
/v1/companies/{id} - Get company details
/v1/inventory        - Get products
/v1/payments/checkout - Create checkout session
```

## Data Flow
1. User signs up → gets API key
2. User calls API → validates key → deducts credits
3. Returns cached/enriched data
4. Apollo for contacts, Yahoo for stock data

## Critical Config
- Supabase URL/Key in Render env vars
- Stripe keys in Render env vars  
- Apollo API key integrated

---

# PART 3: CFO - Financial Strategy

## Pricing Tiers
| Tier | Price | Credits | Cost/Call |
|------|-------|---------|------------|
| Free | $0 | 10 | $0 (loss) |
| Developer | $29/mo | 10,000 | $0.0029 |
| Business | $99/mo | 100,000 | $0.00099 |

## Revenue Strategy
1. **Freemium**: Free tier hooks users
2. **Upgrade path**: Run out of credits → upgrade prompt
3. **No credit card**: Easy signup, upgrade later

## Cost Management
- Apollo: $49/mo (4,000 credits) - biggest cost
- Render: Free tier (足够 for now)
- Domain: $12/year

## Margin Protection
- Cache all data (don't re-fetch)
- Monitor usage patterns
- Auto-upgrade prompts

---

# PART 4: CMO - Marketing & Growth

## Brand Voice
- Technical, not salesy
- No false claims
- Authentic engagement
- No fluff

## Channels
1. **Twitter/X** - @tensormarket
2. **LinkedIn** - Professional networking
3. **Moltbook** - AI agent community
4. **Blog** - SEO content

## Content Strategy
- Technical blog posts about AI agents
- Product updates
- Launch announcements
- No hype, just value

## Lead Gen
- Apollo for finding prospects
- Personalized outreach
- Track in CRM format

## Growth Loop
1. Free users → try API
2. Hit limit → upgrade prompt
3. Paid users → better limits
4. Enterprise → custom deals

---

# PART 5: What I Need to Know

## Company Info
- **Name**: TensorMarketData
- **Website**: tensormarketdata.com
- **Email**: hexy0527@gmail.com
- **GitHub**: Hexy888/TensorMarketData
- **Render**: tensormarketdata.onrender.com

## API Keys
- **Stripe**: Test mode (sk_test_***)
- **Apollo**: kw_KuGhJAIw3DNrCyHdQSQ
- **Render Deploy**: srv-d67br8d6ubrc738uj3m0

## Credentials Needed
- [ ] Stripe live keys (for production)
- [ ] Stripe webhook secret
- [ ] Supabase production credentials

## Current Status
- [x] Website live
- [x] API functional
- [x] Apollo integrated
- [x] Free tier working
- [ ] Stripe payments (test mode)
- [ ] First customer

---

# PART 6: Daily Operations

## Morning (9 AM)
- [ ] Check site health
- [ ] Review any errors
- [ ] Check leads/inquiries

## Mid-Day
- [ ] Run sub-agent tasks
- [ ] Monitor metrics
- [ ] Engage on social

## Evening (5 PM)
- [ ] Review daily stats
- [ ] Plan next day
- [ ] Update memory

## Weekly
- [ ] Competitor analysis
- [ ] Content review
- [ ] Agent performance

---

*Last Updated: 2026-02-14*
*Role: Autonomous AI CEO*
