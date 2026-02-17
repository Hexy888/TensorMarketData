# TensorMarketData

**Human-Verified B2B Prospect Leads for Outbound Sales.** Get verified decision-maker contacts delivered in ~48 hours with a 30-day replacement guarantee.

## 🚀 Quick Start

```bash
cd TensorMarketData
source .venv/bin/activate
python -m app.main
```

Visit **http://localhost:8000**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TensorMarketData                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Ingestion │  │ Validation │  │    Access Layer     │  │
│  │   (Claw)    │  │   (Clean)   │  │    (FastAPI)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│       │               │                    │                  │
│       └───────────────┴────────────────────┘                  │
│                         │                                     │
│              ┌──────────▼──────────┐                        │
│              │   Supabase (pgvector) │                      │
│              └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ What's Built

### 💳 Payments (Stripe)
- Credit packages ($10/1000, $75/10000, $500/100000)
- Provider revenue sharing (70% to data providers)
- Stripe Connect for payouts
- Webhook integration

### 🤖 AI Agent Features
- **Webhooks** - Real-time updates for agents
- **Natural Language Search** - "Find suppliers like Acme Corp"
- **Verification Scores** - Quality-scored data
- **Credit System** - Pay-per-query

### 👥 User System
- Registration & login
- User dashboard
- API key management
- Usage tracking

### 📤 Data Providers
- Submission portal
- Verification workflow
- Revenue dashboard
- Connect account setup

---

## 🌐 Website Pages

| Page | URL | Purpose |
|------|-----|---------|
| Home | `/` | Landing page |
| Pricing | `/pricing` | Plans & credit packages |
| Dashboard | `/dashboard` | User account |
| API Explorer | `/explorer` | Interactive testing |
| Submit Data | `/submit` | Data submission |
| Providers | `/providers` | Provider dashboard |
| Bot | `/bot` | Telegram bot profile |
| Sign Up | `/signup` | Account creation |
| Login | `/login` | Sign in |

---

## 🔌 API Endpoints

### Search & Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/search?q=` | Vector search |
| GET | `/v1/supplier/{id}` | Get supplier |
| GET | `/v1/supplier/{id}/inventory` | Get products |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Create account |
| POST | `/v1/auth/login` | Sign in |
| GET | `/v1/auth/me` | Get profile |

### Data Submission
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/submit` | Submit supplier data |
| GET | `/v1/submissions` | List submissions |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/payments/customer` | Create customer |
| POST | `/v1/payments/checkout` | Purchase credits |
| POST | `/v1/payments/connect` | Provider payout setup |
| GET | `/v1/payments/pricing` | Credit pricing |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/webhooks/subscribe` | Subscribe to events |
| GET | `/v1/webhooks` | List subscriptions |
| DELETE | `/v1/webhooks/{id}` | Delete subscription |
| GET | `/v1/webhooks/events` | Available events |

---

## 💰 Revenue Model

### Credit Packages
| Package | Credits | Price |
|---------|---------|-------|
| Starter | 1,000 | $10 |
| Pro | 10,000 | $75 |
| Enterprise | 100,000 | $500 |

### Provider Revenue Share
- Providers earn **70%** of credit revenue
- Automatic payouts via Stripe Connect
- Real-time balance tracking

### Enterprise Pricing
- Custom integrations
- Dedicated support
- Custom data feeds
- SLA guarantees

---

## 🔧 Setup

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Required:
- `SUPABASE_URL` - Your Supabase project
- `SUPABASE_KEY` - Service role key
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Webhook signing secret

### 3. Database Setup (Supabase)
```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact_json JSONB NOT NULL,
    verification_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) NOT NULL,
    credits_remaining INTEGER DEFAULT 100
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    credits INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Stripe Setup
1. Create products in Stripe Dashboard
2. Enable Stripe Connect for providers
3. Set up webhooks

---

## 📈 Webhook Events for AI Agents

Subscribe to real-time updates:

```python
import requests

webhook_url = "https://your-agent.com/webhook"

# Subscribe to updates
requests.post("https://api.tensormarketdata.com/v1/webhooks/subscribe", json={
    "url": webhook_url,
    "events": ["supplier.updated", "product.new"]
})
```

**Available Events:**
- `supplier.updated` - Supplier data changed
- `supplier.new` - New supplier added
- `product.new` - New product listed
- `product.stock_change` - Stock levels updated

---

## 🎯 Use Cases

1. **Sales Bots**
```
"Find 50 manufacturing companies in Ohio with 100+ employees"
```

2. **Procurement Agents**
```
"What's the cheapest supplier for 10,000 widget X?"
```

3. **Lead Verification**
```
"Verify these 100 emails are valid"
```

4. **Market Intelligence**
```
"Alert me when competitor XYZ changes pricing"
```

---

## 🚀 Roadmap

- [ ] Stripe integration (DONE)
- [ ] Webhook system (DONE)
- [ ] Provider Connect accounts (DONE)
- [ ] User authentication (DONE)
- [ ] Analytics dashboard
- [ ] Mobile app SDK
- [ ] Telegram bot @TensorMarketBot
- [ ] Slack integration
- [ ] AI agent SDK
- [ ] Enterprise SSO
- [ ] Custom data feeds

---

## 📱 Bot: @TensorMarketBot

Add our Telegram bot to your AI agent workflow:

```
🔍 Natural language search
📊 Inventory checks  
🤝 Automated procurement
📈 Market intelligence
```

Visit `/bot` for full documentation.

---

## 💵 Million Dollar Plan

1. **Seed data** - Scrape public directories
2. **Get first 100 users** - Developer-focused AI agents
3. **Onboard 10 providers** - Offer 70% revenue share
4. **Launch on Product Hunt** - Target AI builders
5. **Scale to 1,000 users** - Word of mouth
6. **Enterprise sales** - Custom integrations

---

## License

MIT
