# TensorMarketData Services

## Directory Structure

```
app/services/
├── __init__.py           # Package initialization
├── collection/           # Data collection scrapers
│   ├── __init__.py
│   ├── scraper.py        # Original scrapers (base)
│   └── enhanced_scraper.py # Improved scrapers
├── validation/           # Data validation pipeline
│   ├── __init__.py
│   ├── cleaner.py        # Original cleaner
│   └── enhanced_cleaner.py # Enhanced validation
├── enrichment.py         # Data enrichment services
├── quality_metrics.py    # Data quality scoring
├── compliance.py         # GDPR/compliance management
├── DATA_SOURCES.md       # Data source documentation
├── QUALITY_METRICS.md    # Quality metrics documentation
└── GDPR_COMPLIANCE.md    # GDPR guidelines
```

## Quick Start

### Collecting Data

```python
from app.services.collection.enhanced_scraper import create_default_collector

# Create collector with default scrapers
collector = create_default_collector(api_keys={
    "crunchbase": "your-key",
    "linkedin": "your-token"
})

# Collect from all sources
data = await collector.collect_all()

print(f"Collected {len(data)} records")
print(collector.get_collection_stats())
```

### Validating Data

```python
from app.services.validation.enhanced_cleaner import EnhancedValidationPipeline

pipeline = EnhancedValidationPipeline()
result = await pipeline.process_batch(raw_records)

print(f"Valid: {len(result['valid_records'])}")
print(f"Invalid: {len(result['invalid_records'])}")
print(f"Duplicates removed: {result['deduplication_info']['duplicates_removed']}")
```

### Enriching Data

```python
from app.services.enrichment import enrich_company_data

enriched = await enrich_company_data({
    "name": "Example Corp",
    "email": "contact@example.com"
})

print(f"Social handles: {enriched.get('social_handles')}")
print(f"Web presence: {enriched.get('web_presence')}")
```

### Quality Scoring

```python
from app.services.quality_metrics import DataQualityMetrics

metrics = DataQualityMetrics()
score = metrics.calculate_quality_score(record)

print(f"Overall: {score.overall_score}")
print(f"Completeness: {score.completeness_score}")
print(f"Issues: {score.issues}")
```

### Compliance Checking

```python
from app.services.compliance import GDPRComplianceManager

manager = GDPRComplianceManager()
request = DataSubjectRightsRequest(
    request_id="req_123",
    request_type="access",
    data_subject_id="user_456",
    submitted_at=datetime.utcnow(),
    status="pending",
    notes=""
)

result = manager.handle_rights_request(request)
```

## Data Quality Tiers

| Tier | Score | Usage |
|------|-------|-------|
| Excellent | 0.80-1.00 | Production use |
| Good | 0.60-0.79 | Minor enrichment |
| Fair | 0.40-0.59 | Needs review |
| Poor | 0.00-0.39 | Consider removal |

## Supported Sources

| Source | Type | Quality |
|--------|------|---------|
| SEC EDGAR | Government | High |
| FDA | Government | High |
| SAM.gov | Government | High |
| Crunchbase | API | High |
| LinkedIn | API | High |
| BBB | Directory | Medium-High |
| Yellow Pages | Directory | Medium |
| Manta | Directory | Medium |

## Compliance Notes

- Personal data requires consent
- GDPR Article 15-22 rights apply
- CCPA opt-out for California residents
- 2-year default retention for personal data
- 7-year retention for regulated data

## API Reference

### EnhancedBaseScraper
```python
class EnhancedBaseScraper:
    async def scrape() -> List[Dict]
    def validate_supplier(data: Dict) -> Optional[Dict]
```

### DataCollector
```python
class DataCollector:
    def add_scraper(scraper: EnhancedBaseScraper)
    async def collect_all() -> List[Dict]
    def get_collection_stats() -> Dict
```

### EnhancedValidationPipeline
```python
class EnhancedValidationPipeline:
    def validate_record(record: Dict) -> Tuple[bool, Dict, List[str]]
    async def process_batch(records: List[Dict]) -> Dict
```

### DataQualityMetrics
```python
class DataQualityMetrics:
    def calculate_quality_score(record: Dict) -> QualityScore
    def calculate_dataset_quality(records: List[Dict]) -> Dict
```
