# TensorMarketData "Show HN" Post for Hacker News

---

**Title:** Show HN: TensorMarketData – A data marketplace for AI agents (YC W25)

**Text:**

Hey HN! We're building **TensorMarketData** (https://tensormarketdata.com), a B2B data marketplace where AI agents can discover, evaluate, and purchase data APIs autonomously.

## The Problem

We're building AI agents for a fintech startup, and data was our biggest pain point. Existing data solutions assume human buyers filling out forms, downloading CSVs, and manually processing data. That doesn't work when your product is an autonomous agent.

AI agents need to:
- Discover relevant data sources programmatically
- Evaluate quality, cost, and reliability
- Purchase access without human intervention
- Integrate seamlessly with their codebase

## What We're Building

TensorMarketData is a marketplace for structured data APIs designed specifically for AI agents. Think of it as "Stripe for AI data" — invisible, programmable, and trust-based.

### Key Features

**For Data Buyers:**
- Agent-friendly discovery (search, filter, compare)
- Pay-per-use pricing (no subscriptions required)
- SDKs in Python, REST API for any language
- Budget management for autonomous agents
- Quality ratings, uptime guarantees, reviews

**For Data Sellers:**
- Free listing, 85% revenue share
- Easy API integration (host with us or connect yours)
- Analytics dashboard (earnings, usage, customers)
- Marketing to a developer audience

## Example: An Agent That Trades on Data

```python
from tensormarket import Client

# Agent authenticates with its own API key
client = Client(api_key="agent_tk_...")

# Agent discovers and subscribes to data sources
weather = client.data("weather-api")
stock_data = client.data("realtime-quotes")
news = client.data("financial-news")

# Agent queries as needed
current = weather.current(location="NYC")
prices = stock_data.quote(symbols=["AAPL", "GOOGL"])
headlines = news.headlines(topic="earnings")

# Agent synthesizes and makes decisions
for stock in prices:
    signal = analyze(stock, headlines)
    if signal.strong_buy:
        execute_trade(stock.symbol, signal.size)
```

## What's Available Today

- **50+ data providers** across finance, weather, news, e-commerce, sports, and more
- **Python SDK** (pip install tensormarket)
- **REST API** with comprehensive documentation
- **Pay-per-use pricing** starting at $0.001/call
- **Free tier**: 1,000 API calls/month for development

## Who's It For?

**Data Buyers:**
- AI/ML developers building agentic systems
- Startups integrating AI into products
- Researchers needing diverse data sources
- Enterprises with agent workloads

**Data Sellers:**
- Companies with proprietary data
- Individual developers with unique data sources
- Research institutions sharing data
- Anyone who wants to monetize an API

## Why Now?

The agent economy is exploding. Every major tech company is building AI agents. But these agents need data infrastructure that doesn't exist yet.

We're betting that in 3-5 years, AI agents will be significant economic agents themselves — negotiating contracts, purchasing services, and buying data. We're building that infrastructure now.

## We're YC W25

We're a small team (3 founders) backed by Y Combinator. We're developers ourselves and know the pain firsthand.

## Try It Out

- **Marketplace:** https://tensormarketdata.com
- **Documentation:** https://docs.tensormarketdata.com
- **Python SDK:** `pip install tensormarket`
- **GitHub:** https://github.com/tensormarketdata

**Free tier includes 1,000 API calls/month** — enough to build and test your agent.

## We'd Love Your Feedback

- What data sources would you want available?
- What integrations would be most helpful?
- Any concerns about the model?
- What are we missing?

We're here all day. AMA!

---

## Optional Add-ons for Maximum Visibility

### Technical Deep Dive (comment, not main post):

For those interested in the technical implementation:

**Architecture:**
- Python SDK using httpx for async HTTP
- FastAPI backend with PostgreSQL
- Redis for caching and rate limiting
- Stripe Connect for marketplace payments
- Cloudflare for DDoS protection and CDN

**Agent Authentication:**
- API keys with fine-grained permissions
- Budget limits per agent
- Usage analytics per key
- Key rotation support

**Discovery API:**
- Semantic search over dataset descriptions
- Filter by: category, price, uptime
- Compare mode: side-by-side dataset comparison
- Sample, freshness, rating data preview

**Verification System:**
- Automated uptime monitoring
- Schema validation
- Human spot
- Provider reputation scores

### Demo Links-checks for quality (optional):

- **API Explorer:** https://tensormarketdata.com/explore
- **Pricing Calculator:** https://tensormarketdata.com/pricing
- **Provider Dashboard:** https://tensormarketdata.com/provider/login

### Comment Templates for Team:

**When asked about competitors:**
"Tensormarketdata isn't competing with Kaggle — we're complementary. Kaggle is static datasets for training models. We're live APIs for agents in production. Think of us as the data layer for agentic AI."

**When asked about pricing:**
"Our take rate is 15% — the lowest in the industry. Data providers keep 85% of what they earn. Plus free hosting for simple APIs, no upfront costs."

**When asked about trust:**
"Every provider is vetted. Every dataset is verified. We have uptime SLAs, quality ratings, and a trust system. Bad actors get removed fast."

**When asked about the team:**
"Three technical co-founders who were building AI agents and hit this exact problem. We got frustrated enough to solve it."

---

## Timing Tips for HN

**Best times to post:**
- Tuesday-Thursday, 9-11 AM PST (when HN traffic peaks)
- Avoid Mondays (people catching up) and Fridays (winding down)
- Morning posts get more traction from early reviewers

**Engagement strategy:**
- Reply to every comment in the first 2 hours
- Be authentic, not salesy
- Acknowledge valid criticisms
- Share technical details generously
- Upvote thoughtful questions from others

**Post title options (A/B test mentally):**
1. "Show HN: TensorMarketData – A data marketplace for AI agents (YC W25)"
2. "Show HN: We built a Stripe for AI data agents"
3. "Show HN: My AI agent can now buy its own data"

Option 1 is safest. Option 2 is punchier. Choose based on your confidence in the hook.

---

*Good luck on the launch! 🚀*
