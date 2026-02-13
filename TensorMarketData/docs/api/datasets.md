# Datasets API

The Datasets API enables you to browse, search, purchase, and download datasets from the TensorMarketData marketplace.

## Dataset Schema

```json
{
  "id": "ds_wikipedia_2023",
  "name": "Wikipedia 2023 Full Text",
  "description": "Complete Wikipedia articles from 2023, preprocessed and chunked for embedding generation.",
  "category": "text",
  "subcategory": "encyclopedic",
  "size_gb": 45.2,
  "vector_count": 12500000,
  "embedding_model": "text-embedding-3-large",
  "embedding_dimension": 3072,
  "license": "cc-by-sa-4.0",
  "price": {
    "amount": 299.00,
    "currency": "USD"
  },
  "publisher": {
    "id": "pub_wikimedia",
    "name": "Wikimedia Foundation"
  },
  "tags": ["encyclopedia", "reference", "general-knowledge"],
  "quality_score": 4.8,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-02-01T14:20:00Z"
}
```

## List All Datasets

### Endpoint

```
GET /datasets
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category (text, image, audio, video, multimodal) |
| `subcategory` | string | No | Filter by subcategory |
| `min_size_gb` | number | No | Minimum dataset size in GB |
| `max_size_gb` | number | No | Maximum dataset size in GB |
| `min_quality` | number | No | Minimum quality score (0-5) |
| `license` | string | No | Filter by license type |
| `search` | string | No | Full-text search in name and description |
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Results per page (default: 20, max: 100) |
| `sort_by` | string | No | Sort field (relevance, size, price, quality, created_at) |
| `sort_order` | string | No | asc or desc |

### Example Request

```bash
curl "https://api.tensormarketdata.com/v1/datasets?category=text&min_quality=4.5&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Example Response

```json
{
  "data": [
    {
      "id": "ds_wikipedia_2023",
      "name": "Wikipedia 2023 Full Text",
      "category": "text",
      "size_gb": 45.2,
      "quality_score": 4.8,
      "price": {
        "amount": 299.00,
        "currency": "USD"
      }
    },
    {
      "id": "ds_pubmed_abstracts",
      "name": "PubMed Research Abstracts",
      "category": "text",
      "subcategory": "scientific",
      "size_gb": 12.8,
      "quality_score": 4.9,
      "price": {
        "amount": 149.00,
        "currency": "USD"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 2847,
    "has_more": true
  }
}
```

### Python SDK

```python
from tensormarketdata import Client

client = Client()

# List datasets with filters
datasets = client.datasets.list(
    category="text",
    min_quality=4.5,
    limit=10,
    sort_by="quality",
    sort_order="desc"
)

for ds in datasets:
    print(f"{ds.name} - ${ds.price['amount']}")
```

---

## Get Dataset Details

### Endpoint

```
GET /datasets/{dataset_id}
```

### Example Request

```bash
curl "https://api.tensormarketdata.com/v1/datasets/ds_wikipedia_2023" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Example Response

```json
{
  "id": "ds_wikipedia_2023",
  "name": "Wikipedia 2023 Full Text",
  "description": "Complete Wikipedia articles from 2023, preprocessed and chunked for embedding generation.",
  "category": "text",
  "subcategory": "encyclopedic",
  "size_gb": 45.2,
  "vector_count": 12500000,
  "record_count": 3200000,
  "embedding_model": "text-embedding-3-large",
  "embedding_dimension": 3072,
  "license": {
    "type": "cc-by-sa-4.0",
    "attribution_required": true,
    "commercial_use": true,
    "modifications_allowed": true
  },
  "price": {
    "amount": 299.00,
    "currency": "USD"
  },
  "publisher": {
    "id": "pub_wikimedia",
    "name": "Wikimedia Foundation",
    "verified": true
  },
  "tags": ["encyclopedia", "reference", "general-knowledge", "text"],
  "quality_score": 4.8,
  "metadata_schema": {
    "fields": ["title", "url", "last_updated", "language", "word_count"]
  },
  "sample_records": [
    {
      "id": "rec_001",
      "title": "Artificial Intelligence",
      "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
      "word_count": 15420
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-02-01T14:20:00Z"
}
```

---

## Purchase Dataset

### Endpoint

```
POST /datasets/{dataset_id}/purchase
```

### Example Request

```bash
curl -X POST "https://api.tensormarketdata.com/v1/datasets/ds_wikipedia_2023/purchase" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "credit_card",
    "invoice_id": "INV-2024-001"
  }'
```

### Example Response

```json
{
  "purchase_id": "pur_abc123xyz",
  "dataset_id": "ds_wikipedia_2023",
  "amount": 299.00,
  "currency": "USD",
  "status": "completed",
  "purchased_at": "2024-02-12T15:30:00Z",
  "license": "cc-by-sa-4.0",
  "download_urls": {
    "vectors": "https://cdn.tensormarketdata.com/downloads/ds_wikipedia_2023/vectors.tar.gz",
    "metadata": "https://cdn.tensormarketdata.com/downloads/ds_wikipedia_2023/metadata.jsonl.gz",
    "manifest": "https://cdn.tensormarketdata.com/downloads/ds_wikipedia_2023/manifest.json"
  },
  "expires_at": "2025-02-12T15:30:00Z"
}
```

### Python SDK

```python
from tensormarketdata import Client

client = Client()

# Check ownership first
if client.datasets.is_purchased("ds_wikipedia_2023"):
    print("Already owned!")
else:
    # Purchase dataset
    purchase = client.datasets.purchase(
        dataset_id="ds_wikipedia_2023",
        payment_method="credit_card"
    )
    print(f"Purchased: {purchase['dataset_id']}")
```

---

## Download Dataset

### Endpoint

```
GET /datasets/{dataset_id}/download
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | Download format (default: tar.gz) |
| `include` | string | No | What to include: vectors, metadata, both (default: both) |

### Example Request

```bash
# Get download URL (redirects to CDN)
curl -L "https://api.tensormarketdata.com/v1/datasets/ds_wikipedia_2023/download" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o wikipedia_vectors.tar.gz
```

### Python SDK

```python
from tensormarketdata import Client
import os

client = Client()

# Download with progress
def progress_callback(bytes_downloaded, total_bytes):
    percent = (bytes_downloaded / total_bytes) * 100
    print(f"Downloaded: {percent:.1f}%")

# Download to local path
client.datasets.download(
    dataset_id="ds_wikipedia_2023",
    path="./data/wikipedia_2023",
    progress_callback=progress_callback
)

# List downloaded files
for f in os.listdir("./data/wikipedia_2023"):
    size = os.path.getsize(f"./data/wikipedia_2023/{f}")
    print(f"{f}: {size / (1024**3):.2f} GB")
```

### Download Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `tar.gz` | Compressed tar archive | Bulk downloads |
| `zip` | ZIP archive (Windows compatible) | Windows environments |
| `streaming` | Streaming download (chunked) | Large datasets, limited memory |

---

## Stream Dataset Records

### Endpoint

```
GET /datasets/{dataset_id}/stream
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_size` | integer | No | Records per batch (default: 1000) |
| `filter` | string | No | JSON filter expression |
| `shuffle` | boolean | No | Shuffle records (default: false) |
| `seed` | integer | No | Random seed for shuffling |

### Example Request

```python
# Python streaming example
import tensormarketdata as tmd

client = tmd.Client()

# Stream records in batches
for batch in client.datasets.stream(
    dataset_id="ds_wikipedia_2023",
    batch_size=5000,
    filter='{"language": "en"}'
):
    # Process each record
    for record in batch:
        process_record(record)
```

---

## Check Dataset Ownership

### Endpoint

```
GET /datasets/{dataset_id}/ownership
```

### Example Request

```bash
curl "https://api.tensormarketdata.com/v1/datasets/ds_wikipedia_2023/ownership" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Example Response

```json
{
  "owned": true,
  "purchase_id": "pur_abc123xyz",
  "purchased_at": "2024-02-01T10:30:00Z",
  "license": "cc-by-sa-4.0",
  "downloads_remaining": null,
  "expires_at": null
}
```

---

## Dataset Categories

| Category | Subcategories | Example Use Cases |
|----------|---------------|-------------------|
| `text` | news, scientific, legal, social, encyclopedic | RAG, semantic search, classification |
| `image` | product, medical, satellite, artistic, document | Visual similarity, object detection |
| `audio` | speech, music, environmental, medical | Voice search, audio classification |
| `video` | surveillance, autonomous driving, sports | Action recognition, video search |
| `multimodal` | image-text, video-text, audio-text | Cross-modal retrieval, CLIP models |

---

## Dataset Quality Score

The quality score (0-5 stars) is calculated based on:

- **Completeness**: No missing or corrupted records
- **Consistency**: Uniform formatting and schema adherence
- **Freshness**: Last update recency
- **Metadata Quality**: Rich, accurate metadata
- **Community Rating**: User reviews and ratings

---

## License Types

| License | Attribution Required | Commercial Use | Modifications |
|---------|---------------------|----------------|---------------|
| `cc-by-4.0` | Yes | Yes | Yes |
| `cc-by-sa-4.0` | Yes | Yes | Yes (share-alike) |
| `cc0` | No | Yes | Yes |
| `proprietary` | Varies | Varies | Varies |
| `custom` | See dataset | See dataset | See dataset |

---

## Error Responses

### 403 - Dataset Not Purchased

```json
{
  "error": {
    "code": "DATASET_NOT_PURCHASED",
    "message": "You must purchase this dataset before downloading.",
    "status": 403,
    "details": {
      "dataset_id": "ds_wikipedia_2023",
      "price": {
        "amount": 299.00,
        "currency": "USD"
      }
    }
  }
}
```

### 404 - Dataset Not Found

```json
{
  "error": {
    "code": "DATASET_NOT_FOUND",
    "message": "Dataset 'ds_nonexistent' does not exist.",
    "status": 404
  }
}
```
