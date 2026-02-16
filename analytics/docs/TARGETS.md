# TensorMarketData KPI Targets & OKRs

## FY 2026 Targets

### Q1 2026 (Jan-Mar)
| KPI | Baseline | Target | Stretch |
|-----|----------|--------|---------|
| MAU | 1,000 | 2,500 | 4,000 |
| MRR | $10,000 | $35,000 | $50,000 |
| New Signups | 150/mo | 500/mo | 800/mo |
| Paid Conversion | 3% | 5% | 7% |
| CAC | $300 | $200 | $150 |
| Monthly Churn | 8% | 5% | 3% |
| NRR | 95% | 110% | 125% |

### Q2 2026 (Apr-Jun)
| KPI | Target | Stretch |
|-----|--------|---------|
| MAU | 5,000 | 7,500 |
| MRR | $75,000 | $120,000 |
| New Signups | 750/mo | 1,200/mo |
| Paid Conversion | 6% | 8% |
| CAC | $180 | $140 |
| Monthly Churn | 4% | 3% |
| NRR | 115% | 130% |

### Q3 2026 (Jul-Sep)
| KPI | Target | Stretch |
|-----|--------|---------|
| MAU | 10,000 | 15,000 |
| MRR | $150,000 | $250,000 |
| New Signups | 1,200/mo | 1,800/mo |
| Paid Conversion | 7% | 9% |
| CAC | $160 | $130 |
| Monthly Churn | 4% | 3% |
| NRR | 120% | 135% |

### Q4 2026 (Oct-Dec)
| KPI | Target | Stretch |
|-----|--------|---------|
| MAU | 20,000 | 30,000 |
| MRR | $300,000 | $500,000 |
| New Signups | 1,800/mo | 2,500/mo |
| Paid Conversion | 8% | 10% |
| CAC | $150 | $125 |
| Monthly Churn | 3% | 2% |
| NRR | 125% | 140% |

---

## KPI Traffic Light System

```yaml
status_thresholds:
  excellent:
    color: green
    criteria: "> 90% of target"
  
  on_track:
    color: yellow
    criteria: "70% - 90% of target"
  
  at_risk:
    color: orange
    criteria: "50% - 70% of target"
  
  critical:
    color: red
    criteria: "< 50% of target"
```

### Weekly KPI Status Report

| KPI | Current | Target | Status | Trend |
|-----|---------|--------|--------|-------|
| MAU | 2,100 | 2,500 | 🟡 On Track | ↑ |
| MRR | $28,000 | $35,000 | 🟡 On Track | ↑ |
| Signups | 480 | 500 | 🟢 Excellent | → |
| CAC | $210 | $200 | 🟡 On Track | ↓ |
| Churn | 4.5% | 5.0% | 🟢 Excellent | ↓ |
| NRR | 105% | 110% | 🟡 On Track | ↑ |

---

## North Star Alignment

### How Activities Impact North Star (Revenue Queries)

| Activity | Impact | Measure |
|----------|--------|---------|
| Developer documentation improvements | High | Time to first query |
| API client library releases | High | Query volume per user |
| Dataset additions | Medium | Dataset views → queries |
| Pricing page optimization | Medium | Paid conversion rate |
| Email campaigns | Medium | Reactivation rate |
| Content marketing | Low | Signup → query conversion |
| Paid ads | Low | CAC efficiency |

---

## Unit Economics Targets

| Metric | Seed | Series A | Series B |
|--------|------|----------|----------|
| CAC | <$300 | <$200 | <$150 |
| LTV | >$600 | >$1,000 | >$2,000 |
| LTV:CAC | >2:1 | >5:1 | >8:1 |
| Payback | <12 mo | <8 mo | <6 mo |
| Gross Margin | >70% | >75% | >80% |

---

## Alert Triggers

```yaml
alerts:
  kpi_degradation:
    - metric: "DAU"
      condition: "drop > 20% vs 7-day average"
      severity: warning
    
    - metric: "MRR"
      condition: "negative growth 2 consecutive weeks"
      severity: critical
    
    - metric: "Churn"
      condition: "> 7% monthly"
      severity: critical
    
    - metric: "CAC"
      condition: "> 50% above target"
      severity: warning
    
    - metric: "Error Rate"
      condition: "> 5%"
      severity: critical
```
