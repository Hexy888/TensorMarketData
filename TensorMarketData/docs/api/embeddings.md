# Embeddings API

Generate high-quality vector embeddings using state-of-the-art transformer models. The Embeddings API supports text, image, and multimodal inputs.

## Generate Embeddings

### Endpoint

```
POST /embed
```

### Request Body

```json
{
  "model_id": "text-embedding-3-large",
  "input": [
    "Deep learning transforms AI applications",
    "Neural networks excel at pattern recognition"
  ],
  "encoding_format": "float",
  "dimensions": 1024,
  "normalize": true
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | string | Yes | Embedding model to use |
| `input` | array | Yes | Text strings or image URLs (max 2048 items) |
| `encoding_format` | string | No | float or base64 (default: float) |
| `dimensions` | integer | No | Output dimension (model-dependent) |
| `normalize` | boolean | No | Normalize output vectors (default: true) |
| `truncate` | string | No | Truncate strategy: start, end, none (default: end) |

### Example Request

```bash
curl -X POST "https://api.tensormarketdata.com/v1/embed" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "text-embedding-3-large",
    "input": [
      "Machine learning is transforming healthcare",
      "AI models can predict disease outcomes"
    ]
  }'
```

### Example Response

```json
{
  "model_id": "text-embedding-3-large",
  "usage": {
    "prompt_tokens": 25,
    "total_tokens": 25
  },
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.0123, -0.0456, 0.0789, ...]
    },
    {
      "object": "embedding",
      "index": 1,
      "embedding": [0.0234, -0.0567, 0.0890, ...]
    }
  ]
}
```

---

## Available Models

### Text Embedding Models

| Model ID | Dimension | Max Tokens | Description |
|----------|-----------|------------|-------------|
| `text-embedding-3-small` | 512/1024 | 8192 | Fast, cost-effective |
| `text-embedding-3-large` | 1024/1536/3072 | 8192 | High quality, larger capacity |
| `text-embedding-ada-002` | 1536 | 8191 | General purpose, balanced |
| `e5-small-v2` | 384 | 512 | Lightweight, efficient |
| `e5-large-v2` | 1024 | 512 | High accuracy |

### Image Embedding Models

| Model ID | Dimension | Input Types | Description |
|----------|-----------|-------------|-------------|
| `clip-vit-b-32` | 512 | Images, text | Cross-modal, CLIP-based |
| `clip-vit-l-14` | 768 | Images, text | Higher capacity CLIP |
| `resnet-50` | 2048 | Images only | Classic CNN features |

### Multilingual Models

| Model ID | Languages | Dimension | Description |
|----------|-----------|-----------|-------------|
| `multilingual-e5-large` | 100+ | 1024 | 100+ languages |
| `paraphrase-multilingual` | 50+ | 768 | Paraphrase detection |

---

## Image Embeddings

### Endpoint

```
POST /embed
```

### Example Request

```bash
curl -X POST "https://api.tensormarketdata.com/v1/embed" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "clip-vit-b-32",
    "input": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }'
```

### Image Input Formats

- **Public URLs**: `https://example.com/image.jpg`
- **Base64**: `data:image/jpeg;base64,/9j/4AAQ...`
- **Cloud Storage**: `s3://bucket/path/image.jpg`, `gs://bucket/path/image.jpg`

---

## Batch Embedding

Process up to 2048 items in a single request.

```json
{
  "model_id": "text-embedding-3-small",
  "input": [
    "Document 1 text...",
    "Document 2 text...",
    ...
  ]
}
```

---

## Dimension Reduction

Reduce embedding dimensions to save storage and memory.

```json
{
  "model_id": "text-embedding-3-large",
  "input": ["Your text here"],
  "dimensions": 256
}
```

| Original Dimension | Possible Reductions |
|-------------------|---------------------|
| 3072 | 256, 512, 1024, 1536, 2048 |
| 1536 | 256, 512, 768, 1024 |
| 1024 | 256, 512, 768 |

---

## Python SDK Examples

### Basic Text Embedding

```python
from tensormarketdata import Client

client = Client()

# Generate embeddings
result = client.embed(
    texts=[
        "TensorMarketData provides vector search",
        "High-quality embeddings for AI applications"
    ],
    model="text-embedding-3-large"
)

# Access embeddings
for i, embedding in enumerate(result.embeddings):
    print(f"Text {i}: {len(embedding)} dimensions")
```

### Custom Dimensions

```python
# Generate smaller embeddings for efficiency
result = client.embed(
    texts=["Your text here"],
    model="text-embedding-3-large",
    dimensions=512  # Reduce from 3072
)

print(f"Embedding size: {len(result.embeddings[0])}")
```

### Image Embeddings

```python
# Generate image embeddings
result = client.embed(
    images=[
        "https://example.com/product1.jpg",
        "https://example.com/product2.jpg"
    ],
    model="clip-vit-b-32"
)

# Use for image similarity search
```

### Cross-Modal Search

```python
# Text to image search
text_embedding = client.embed(
    texts=["a red sunset over the ocean"],
    model="clip-vit-b-32"
)

image_embedding = client.embed(
    images=["https://example.com/sunset.jpg"],
    model="clip-vit-b-32"
)

# Compute similarity
import numpy as np
similarity = np.dot(text_embedding[0], image_embedding[0])
```

### Async Batch Processing

```python
import asyncio
from tensormarketdata import AsyncClient

async def embed_large_corpus():
    client = AsyncClient()
    
    texts = [...]  # Your documents
    
    # Process in batches
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = await client.embed(batch, model="text-embedding-3-small")
        all_embeddings.extend(result.embeddings)
    
    return all_embeddings
```

---

## Pricing

Pricing is based on input tokens for text models and per-image for image models.

| Model | Price per 1K tokens | Price per 1K images |
|-------|--------------------|--------------------|
| `text-embedding-3-small` | $0.0001 | - |
| `text-embedding-3-large` | $0.0013 | - |
| `text-embedding-ada-002` | $0.0004 | - |
| `clip-vit-b-32` | - | $0.001 |
| `clip-vit-l-14` | - | $0.005 |

---

## Best Practices

### Input Preparation

```python
# Chunk long documents
def chunk_text(text, chunk_size=1000, overlap=100):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

# Generate embeddings for each chunk
chunks = chunk_text(long_document)
result = client.embed(chunks, model="text-embedding-3-small")
```

### Normalization

```python
# Enable normalization for cosine similarity
result = client.embed(
    texts=["Your text"],
    model="text-embedding-3-large",
    normalize=True  # Already normalized
)

# Cosine similarity = dot product for normalized vectors
```

### Error Handling

```python
from tensormarketdata import TensorMarketDataError

try:
    result = client.embed(texts=very_long_list, model="text-embedding-3-large")
except TensorMarketDataError as e:
    if "too many inputs" in str(e):
        # Split into smaller batches
        result = batch_embed(very_long_list)
```

---

## Troubleshooting

### Empty Results

Ensure input array is not empty and strings are not just whitespace.

### Dimension Mismatch

When searching, ensure your query embedding dimension matches the dataset dimension:

```python
# Check dataset embedding dimension
dataset = client.datasets.get("ds_my_dataset")
print(f"Embedding dimension: {dataset['embedding_dimension']}")

# Generate matching embeddings
query = client.embed(["your query"], model=dataset['embedding_model'])
```

### Rate Limits

Batch multiple texts together to reduce API calls:

```python
# Good: Batch 100 texts
result = client.embed(list_of_100_texts)

# Bad: 100 individual calls
for text in list_of_100_texts:
    result = client.embed([text])
```
