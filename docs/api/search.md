# Search API

The Search API enables semantic similarity search across vector datasets, powering use cases like recommendation systems, document retrieval, and question answering.

## Search Endpoints

### Basic Search

```
POST /search
```

Perform a similarity search using a text query.

#### Request Body

```json
{
  "query": "machine learning algorithms",
  "dataset_id": "ds_pubmed_abstracts",
  "top_k": 10,
  "filters": {
    "year": { "$gte": 2020 },
    "journal": "Nature"
  },
  "include_metadata": true,
  "include_vectors": false,
  "score_threshold": 0.7
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Text query for semantic search |
| `dataset_id` | string | Yes | ID of the dataset to search |
| `top_k` | integer | No | Number of results (default: 10, max: 100) |
| `filters` | object | No | Metadata filters |
| `include_metadata` | boolean | No | Include metadata in results (default: true) |
| `include_vectors` | boolean | No | Include vectors in results (default: false) |
| `score_threshold` | number | No | Minimum similarity score (0-1) |
| `model_id` | string | No | Override embedding model |
| `search_type` | string | No | search_type: hybrid, semantic, keyword |

#### Example Request

```bash
curl -X POST "https://tensormarketdata.com/v1/search" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformer models for natural language processing",
    "dataset_id": "ds_wikipedia_2023",
    "top_k": 5,
    "filters": {
      "language": "en"
    }
  }'
```

#### Example Response

```json
{
  "results": [
    {
      "id": "rec_abc123",
      "score": 0.8923,
      "metadata": {
        "title": "Attention Is All You Need",
        "url": "https://en.wikipedia.org/wiki/Attention_Is_All_You_Need",
        "word_count": 5420,
        "last_updated": "2024-01-15"
      }
    },
    {
      "id": "rec_def456",
      "score": 0.8751,
      "metadata": {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "url": "https://en.wikipedia.org/wiki/BERT_(language_model)",
        "word_count": 3200,
        "last_updated": "2024-02-01"
      }
    }
  ],
  "query_metadata": {
    "model_id": "text-embedding-3-large",
    "query_embedding_dim": 3072,
    "search_time_ms": 45
  }
}
```

---

### Vector Search

```
POST /search/vectors
```

Perform search using pre-computed vectors.

#### Request Body

```json
{
  "vector": [0.123, 0.456, 0.789, ...],
  "dataset_id": "ds_wikipedia_2023",
  "top_k": 10,
  "filters": {
    "category": "technology"
  }
}
```

#### Example Request

```bash
curl -X POST "https://tensormarketdata.com/v1/search/vectors" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, 0.3, ...],
    "dataset_id": "ds_wikipedia_2023",
    "top_k": 10
  }'
```

---

### Batch Search

```
POST /search/batch
```

Search multiple queries in a single request.

#### Request Body

```json
{
  "queries": [
    "machine learning",
    "deep learning",
    "neural networks"
  ],
  "dataset_id": "ds_pubmed_abstracts",
  "top_k": 5
}
```

#### Example Response

```json
{
  "results": [
    {
      "query": "machine learning",
      "results": [
        {"id": "rec_001", "score": 0.912},
        {"id": "rec_002", "score": 0.887}
      ]
    },
    {
      "query": "deep learning",
      "results": [
        {"id": "rec_003", "score": 0.923},
        {"id": "rec_004", "score": 0.901}
      ]
    }
  ]
}
```

---

### Hybrid Search

Combine semantic and keyword search for better results.

```
POST /search/hybrid
```

#### Request Body

```json
{
  "query": "transformer attention mechanism",
  "dataset_id": "ds_wikipedia_2023",
  "top_k": 10,
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  },
  "keyword_fields": ["title", "text"]
}
```

---

## Filter Operators

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equals | `{"year": {"$eq": 2023}}` |
| `$ne` | Not equals | `{"status": {"$ne": "archived"}}` |
| `$gt` | Greater than | `{"score": {"$gt": 0.8}}` |
| `$gte` | Greater than or equal | `{"year": {"$gte": 2020}}` |
| `$lt` | Less than | `{"price": {"$lt": 100}}` |
| `$lte` | Less than or equal | `{"rating": {"$lte": 3.5}}` |

### Array Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$in` | Value in array | `{"category": {"$in": ["tech", "science"]}}` |
| `$nin` | Value not in array | `{"status": {"$nin": ["deleted", "banned"]}}` |
| `$contains` | Array contains value | `{"tags": {"$contains": "featured"}}` |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$and` | AND conditions | `{"$and": [{"year": 2023}, {"status": "published"}]}` |
| `$or` | OR conditions | `{"$or": [{"category": "A"}, {"category": "B"}]}` |
| `$not` | NOT condition | `{"$not": {"status": "deleted"}}` |

### Complex Filter Example

```json
{
  "filters": {
    "$and": [
      {"year": {"$gte": 2020}},
      {"$or": [
        {"category": "machine-learning"},
        {"category": "deep-learning"}
      ]},
      {"citations": {"$gte": 100}}
    ]
  }
}
```

---

## Python SDK Examples

### Basic Search

```python
from tensormarketdata import Client

client = Client()

# Text search
results = client.search(
    query="reinforcement learning applications",
    dataset_id="ds_pubmed_abstracts",
    top_k=10
)

for result in results:
    print(f"ID: {result.id}, Score: {result.score:.4f}")
    print(f"Title: {result.metadata['title']}")
```

### Search with Filters

```python
results = client.search(
    query="climate change impacts",
    dataset_id="ds_wikipedia_2023",
    top_k=20,
    filters={
        "year": {"$gte": 2020},
        "category": "science"
    },
    score_threshold=0.7
)
```

### Vector Search

```python
import numpy as np

# Generate query vector
query_vector = client.embed("autonomous vehicle technology").vector

# Search with vector
results = client.search_vectors(
    vector=query_vector,
    dataset_id="ds_wikipedia_2023",
    top_k=10
)
```

### Batch Search

```python
queries = [
    "neural network architectures",
    "computer vision models",
    "natural language processing"
]

all_results = client.search_batch(
    queries=queries,
    dataset_id="ds_wikipedia_2023",
    top_k=5
)

for query, results in zip(queries, all_results):
    print(f"\nQuery: {query}")
    for r in results:
        print(f"  - {r.id}: {r.score:.4f}")
```

### Async Search

```python
import asyncio
from tensormarketdata import AsyncClient

async def search_multiple():
    client = AsyncClient()
    
    # Run searches concurrently
    results = await asyncio.gather(
        client.search("query 1", dataset_id="ds_1"),
        client.search("query 2", dataset_id="ds_2"),
        client.search("query 3", dataset_id="ds_3")
    )
    
    return results
```

---

## Search Types

### Semantic Search

Uses transformer-based embeddings to find semantically similar content.

```json
{
  "search_type": "semantic",
  "query": "how to cook pasta",
  "dataset_id": "ds_recipes"
}
```

**Best for**: Concept matching, natural language queries, intent understanding

### Keyword Search

Traditional BM25-based keyword matching.

```json
{
  "search_type": "keyword",
  "query": "pasta carbonara recipe",
  "dataset_id": "ds_recipes"
}
```

**Best for**: Exact phrase matching, entity lookup, known-item search

### Hybrid Search

Combines semantic and keyword with configurable weights.

```json
{
  "search_type": "hybrid",
  "query": "quick pasta dinner ideas",
  "dataset_id": "ds_recipes",
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  }
}
```

**Best for**: Production systems requiring robust recall, mixed query types

---

## Scoring and Ranking

### Similarity Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `cosine` | Cosine similarity | Standard for embeddings |
| `dot` | Dot product | When vectors are normalized |
| `euclidean` | L2 distance | Geometric similarity |
| `manhattan` | L1 distance | Sparse vectors |

### Score Normalization

Scores are normalized to [0, 1] range:

```
normalized_score = (raw_score - min_possible) / (max_possible - min_possible)
```

### Reranking

Post-search reranking using cross-encoder models:

```python
results = client.search(
    query="transformer attention mechanism",
    dataset_id="ds_papers",
    top_k=100,  # Get more initial results
    search_type="semantic"
)

# Rerank top results
reranked = client.rerank(
    query="transformer attention mechanism",
    candidates=results[:20],
    model="cross-encoder/ms-marco-MiniLM"
)
```

---

## Performance Optimization

### Caching

```python
# Enable query result caching
client = Client(
    cache_enabled=True,
    cache_ttl_seconds=3600
)

# Cache hit
results = client.search("common query", dataset_id="ds_1")  # First call
results = client.search("common query", dataset_id="ds_1")  # Cached
```

### Request Batching

```python
# Instead of many individual calls
for query in queries:
    client.search(query, dataset_id="ds_1")

# Use batch endpoint
client.search_batch(queries, dataset_id="ds_1")
```

### Async for High Throughput

```python
import asyncio

async def search_all(queries):
    client = AsyncClient()
    tasks = [
        client.search(q, dataset_id="ds_1")
        for q in queries
    ]
    return await asyncio.gather(*tasks)
```

---

## Error Responses

### 400 - Invalid Vector Dimension

```json
{
  "error": {
    "code": "INVALID_VECTOR_DIMENSION",
    "message": "Query vector dimension (768) doesn't match dataset (3072)",
    "status": 400,
    "details": {
      "query_dimension": 768,
      "expected_dimension": 3072
    }
  }
}
```

### 429 - Rate Limited

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Retry after 30 seconds.",
    "status": 429,
    "details": {
      "retry_after_seconds": 30,
      "current_usage": 150,
      "limit": 100
    }
  }
}
```

---

## Best Practices

1. **Set appropriate `top_k`**: Higher values increase latency
2. **Use filters early**: Reduce search space before semantic matching
3. **Cache frequently searched queries**
4. **Use async for batch operations**
5. **Consider hybrid search for better recall**
6. **Implement proper error handling and retries**
