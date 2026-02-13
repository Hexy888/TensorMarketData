# TensorMarketData Metrics Glossary

## User Metrics

| Metric | Definition | Formula | Source |
|--------|------------|---------|--------|
| **DAU** | Daily Active Users | Unique users with ≥1 session/day | Mixpanel |
| **MAU** | Monthly Active Users | Unique users with ≥1 session/month | Mixpanel |
| **WAU** | Weekly Active Users | Unique users with ≥1 session/week | Mixpanel |
| **Stickiness** | DAU/MAU ratio | DAU ÷ MAU × 100 | Calculated |
| **New Users** | First-time signups | Users with signup_date = today | Auth |
| **Registered Users** | All signups ever | COUNT(user_id) WHERE status=active | Auth |

## API Usage Metrics

| Metric | Definition | Formula | Source |
|--------|------------|---------|--------|
| **API Calls** | Total API requests | SUM(requests) | API Gateway |
| **Successful Queries** | 2xx responses | COUNT WHERE status ∈ (200,201) | API Gateway |
| **Failed Queries** | 4xx/5xx responses | COUNT WHERE status ∈ (400-599) | API Gateway |
| **Query Latency (p95)** | 95th percentile latency | PERCENTILE(95, latency_ms) | API Gateway |
| **Queries per User** | Avg queries per active user | API Calls ÷ MAU | Calculated |

## Conversion Metrics

| Metric | Definition | Formula | Source |
|--------|------------|---------|--------|
| **Signup Rate** | Visitors who sign up | Signups ÷ Visitors × 100 | Plausible |
| **API Key Conversion** | Signups with API key | Users_with_key ÷ Total_users × 100 | Auth |
| **First Query Rate** | API keys with ≥1 query | Users_queried ÷ Users_with_key × 100 | Mixpanel |
| **Paid Conversion** | Free users upgrading | Paid_users ÷ Free_users × 100 | Stripe |
| **Trial Conversion** | Trials that convert | Paid_trial ÷ Total_trials × 100 | Stripe |

## Revenue Metrics

| Metric | Definition | Formula | Source |
|--------|------------|---------|--------|
| **MRR** | Monthly Recurring Revenue | SUM(monthly_billing) | Stripe |
| **ARR** | Annual Recurring Revenue | MRR × 12 | Calculated |
| **ARPU** | Avg Revenue Per User | MRR ÷ Paid_users | Calculated |
| **Revenue per Query** | Avg revenue per API call | MRR ÷ Total_queries | Calculated |
| **Expansion Revenue** | Upsells to existing accounts | New_mrr - New_business_mrr | Stripe |

## Efficiency Metrics

| Metric | Definition | Formula | Source |
|--------|------------|---------|--------|
| **CAC** | Customer Acquisition Cost | Sales_marketing ÷ New_customers | Finance |
| **Blended CAC** | Including organic | Total_spend ÷ New_customers | Finance |
| **LTV** | Lifetime Value | ARPU ÷ Monthly_churn | Calculated |
| **LTV:CAC** | Unit economics ratio | LTV ÷ CAC | Calculated |
| **Payback Period** | Months to recover CAC | CAC ÷ (ARPU × Gross_margin) | Finance |
| **Quick Ratio** | Growth efficiency | (New + Expansion) ÷ (Churn + Contraction) | Calculated |

## Retention Metrics

| Metric | Definition | Formula | Source |
|--------|------------|---------|--------|
| **Monthly Churn** | % users lost this month | Lost_users ÷ Start_users × 100 | Mixpanel |
| **Gross Retention** | Revenue retained | Starting_mrr - Lost_mrr | Stripe |
| **Net Retention** | Revenue including expansion | (Ending_mrr ÷ Starting_mrr) × 100 | Stripe |
| **NPS** | Net Promoter Score | %Promoters - %Detractors | UserVoice |

## Error & Performance Metrics

| Metric | Definition | Target | Alert Threshold |
|--------|------------|--------|-----------------|
| **API Error Rate** | % failed requests | <1% | >5% |
| **Latency (p95)** | 95th percentile response | <500ms | >1000ms |
| **Uptime** | Service availability | 99.9% | <99.5% |
| **Support Ticket Volume** | Tickets per user | <0.1/ticket | >2x baseline |
