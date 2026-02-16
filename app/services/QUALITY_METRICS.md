# Data Quality Metrics Documentation

## Overview
TensorMarketData uses comprehensive data quality metrics to ensure reliable supplier data for AI agents.

## Quality Dimensions

### 1. Completeness Score
Measures the percentage of important fields that are populated.

**Calculation:**
```
completeness = sum(field_weights where field is populated) / sum(all field_weights)
```

**Field Weights:**
| Field | Weight | Description |
|-------|--------|-------------|
| name | 1.0 | Company name (required) |
| email | 0.8 | Contact email |
| phone | 0.6 | Phone number |
| website | 0.5 | Company website |
| linkedin | 0.4 | LinkedIn profile |
| address | 0.5 | Physical address |
| industry | 0.6 | Industry classification |
| size_estimate | 0.4 | Company size |
| verification_score | 0.7 | Verification level |

### 2. Accuracy Score
Measures the likelihood that data is accurate based on validation.

**Factors:**
- Email format validation (regex + pattern check)
- Phone number format validation
- URL validation
- Name length reasonableness
- Verification score correlation

**Formula:**
```
accuracy = base_score + bonuses - penalties
base_score = 0.5
bonuses:
  - valid email: +0.1
  - valid phone: +0.1
  - valid URL: +0.1
  - valid name: +0.1
  - high verification: +0.1
max_score = 1.0
```

### 3. Consistency Score
Measures internal consistency of data.

**Checks:**
- Industry vs. name keywords
- Company size indicators
- Location consistency
- Contact format consistency

### 4. Timeliness Score
Measures how recently data was collected.

**Freshness Thresholds:**
| Age | Score |
|-----|-------|
| 0-7 days | 1.0 |
| 8-30 days | 0.9 |
| 31-90 days | 0.7 |
| 91-180 days | 0.5 |
| 181-365 days | 0.3 |
| 365+ days | 0.1 |

### 5. Validity Score
Measures format compliance and data integrity.

**Checks:**
- Required field presence
- Field length limits
- Format validation
- Source attribution

### 6. Uniqueness Score
Measures how unique a record is (inverse of duplicate likelihood).

**Calculation:**
```
uniqueness = 1.0 - (matches * 0.15)
matches = count of similar records
```

## Overall Quality Score

**Weighted Formula:**
```
overall = (completeness * 0.25) +
          (accuracy * 0.25) +
          (consistency * 0.15) +
          (timeliness * 0.10) +
          (validity * 0.15) +
          (uniqueness * 0.10)
```

## Quality Tiers

| Tier | Score Range | Color | Description |
|------|-------------|-------|-------------|
| Excellent | 0.80 - 1.00 | 🟢 | Production ready |
| Good | 0.60 - 0.79 | 🟡 | Minor issues |
| Fair | 0.40 - 0.59 | 🟠 | Needs enrichment |
| Poor | 0.00 - 0.39 | 🔴 | Consider removal |

## Dashboard Metrics

### Dataset Overview
- Total records
- Average quality score
- Quality distribution (by tier)
- Dimension averages

### Source Quality
- Quality by data source
- Records per source
- Source reliability scores

### Issues Tracking
- Top issues by frequency
- Common missing fields
- Validation failures

## Usage Examples

```python
from app.services.quality_metrics import DataQualityMetrics

metrics = DataQualityMetrics()

# Calculate score for single record
record = {
    "name": "Acme Corp",
    "email": "contact@acme.com",
    "phone": "+1-555-123-4567",
    "industry": "technology",
    "verification_score": 0.85,
    "scraped_at": "2024-01-15T10:30:00Z"
}

score = metrics.calculate_quality_score(record)
print(f"Overall: {score.overall_score}")
print(f"Completeness: {score.completeness_score}")
print(f"Issues: {score.issues}")
```

## Alert Thresholds

### Warning Alerts
- Average quality < 0.6
- More than 10% poor records
- Any source below 0.4 average

### Critical Alerts
- Average quality < 0.4
- More than 25% poor records
- Data freshness > 90 days old

## Continuous Monitoring

### Metrics to Track Daily
1. Overall dataset quality trend
2. New record quality distribution
3. Source quality comparison
4. Duplicate rate
5. Validation failure rate

### Reports
- Daily quality summary
- Weekly trend analysis
- Monthly compliance report
