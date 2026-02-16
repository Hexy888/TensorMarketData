# Building RAG Applications with TensorMarketData

This tutorial guides you through building a production-ready Retrieval-Augmented Generation (RAG) system using TensorMarketData's vector search and datasets.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌────────┐  │
│  │ User    │───▶│ Embed    │───▶│ Vector  │───▶│ LLM    │  │
│  │ Query   │    │ Query    │    │ Search  │    │ Output │  │
│  └─────────┘    └──────────┘    └─────────┘    └────────┘  │
│       │                              │                       │
│       │              ┌───────────────┘                       │
│       │              ▼                                       │
│       │        ┌─────────────┐                               │
│       └───────▶│ Retrieved   │◀─────── Document Store       │
│               │ Context     │                               │
│               └─────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

```bash
pip install tensormarketdata openai tqdm
```

---

## Part 1: Document Ingestion Pipeline

Build a pipeline to ingest documents into TensorMarketData:

```python
from tensormarketdata import Client
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

class DocumentIngestor:
    def __init__(self, api_key: str):
        self.client = Client(api_key=api_key)
        self.batch_size = 100
    
    def load_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """Load documents from various formats."""
        path = Path(file_path)
        
        if path.suffix == '.jsonl':
            return self._load_jsonl(path)
        elif path.suffix == '.json':
            return self._load_json(path)
        elif path.suffix == '.txt':
            return self._load_txt(path)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")
    
    def _load_jsonl(self, path: Path) -> List[Dict]:
        documents = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    documents.append(json.loads(line))
        return documents
    
    def _load_json(self, path: Path) -> List[Dict]:
        with open(path, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    
    def _load_txt(self, path: Path) -> List[Dict]:
        with open(path, 'r') as f:
            content = f.read()
        # Split by double newlines (paragraphs)
        paragraphs = content.split('\n\n')
        return [
            {'id': hashlib.md5(p.encode()).hexdigest()[:8], 'text': p}
            for p in paragraphs if p.strip()
        ]
    
    def chunk_document(self, text: str, chunk_size: int = 1000, 
                       overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks."""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            result = self.client.embed(
                texts=batch,
                model="text-embedding-3-small",
                dimensions=1024,
                normalize=True
            )
            all_embeddings.extend(result.embeddings)
        
        return all_embeddings
    
    def ingest(self, file_path: str, dataset_name: str, 
               chunk_size: int = 1000) -> Dict[str, Any]:
        """Main ingestion pipeline."""
        print("Loading documents...")
        documents = self.load_documents(file_path)
        
        print(f"Loaded {len(documents)} documents")
        
        # Extract text and chunk
        print("Chunking documents...")
        all_chunks = []
        chunk_metadata = []
        
        for doc in documents:
            text = doc.get('text', doc.get('content', doc.get('body', str(doc))))
            chunks = self.chunk_document(text, chunk_size)
            
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    'document_id': doc.get('id', hashlib.md5(text.encode()).hexdigest()[:8]),
                    'chunk_index': idx,
                    'text_preview': chunk[:100],
                    **doc  # Include original metadata
                })
        
        print(f"Created {len(all_chunks)} chunks")
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.generate_embeddings(all_chunks)
        
        # Prepare for upload
        print("Preparing upload...")
        records = [
            {
                'id': f"{meta['document_id']}_{meta['chunk_index']}",
                'vector': emb,
                'metadata': meta
            }
            for emb, meta in zip(embeddings, chunk_metadata)
        ]
        
        return {
            'dataset_name': dataset_name,
            'total_records': len(records),
            'records': records
        }

# Usage
ingestor = DocumentIngestor(api_key="YOUR_API_KEY")

result = ingestor.ingest(
    file_path="data/documents.jsonl",
    dataset_name="my-knowledge-base",
    chunk_size=1500
)

print(f"Ingested {result['total_records']} chunks")
```

---

## Part 2: Retrieval System

Build a robust retrieval system with reranking:

```python
from tensormarketdata import Client
import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class SearchType(Enum):
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"

@dataclass
class RetrievedDocument:
    id: str
    score: float
    text: str
    metadata: dict
    rank: int

class RAGRetriever:
    def __init__(self, api_key: str, default_dataset: str):
        self.client = Client(api_key=api_key)
        self.default_dataset = default_dataset
    
    def retrieve(self, query: str, dataset_id: Optional[str] = None,
                 top_k: int = 10, search_type: SearchType = SearchType.HYBRID,
                 filters: Optional[dict] = None) -> List[RetrievedDocument]:
        """Retrieve relevant documents for a query."""
        dataset_id = dataset_id or self.default_dataset
        
        # Step 1: Initial retrieval (broader set)
        if search_type == SearchType.SEMANTIC:
            results = self.client.search(
                query=query,
                dataset_id=dataset_id,
                top_k=top_k * 3,  # Get more for reranking
                filters=filters
            )
        elif search_type == SearchType.HYBRID:
            results = self.client.search(
                query=query,
                dataset_id=dataset_id,
                top_k=top_k * 3,
                search_type="hybrid",
                filters=filters
            )
        else:
            results = self.client.search(
                query=query,
                dataset_id=dataset_id,
                top_k=top_k * 3,
                search_type="keyword",
                filters=filters
            )
        
        # Step 2: Extract text from metadata
        documents = []
        for rank, r in enumerate(results, 1):
            text = r.metadata.get('text', r.metadata.get('content', 
                         r.metadata.get('title', '')))
            documents.append(RetrievedDocument(
                id=r.id,
                score=r.score,
                text=text,
                metadata=r.metadata,
                rank=rank
            ))
        
        # Step 3: Optional cross-encoder reranking
        if len(documents) > top_k:
            documents = self._rerank(query, documents[:top_k * 2], top_k)
        
        return documents[:top_k]
    
    def _rerank(self, query: str, documents: List[RetrievedDocument],
                top_k: int) -> List[RetrievedDocument]:
        """Rerank using cross-encoder for better relevance."""
        # Use TensorMarketData's rerank endpoint
        reranked = self.client.rerank(
            query=query,
            candidates=documents,
            model="cross-encoder/ms-marco-MiniLM"
        )
        
        return reranked[:top_k]
    
    def format_context(self, documents: List[RetrievedDocument],
                       max_chars: int = 4000) -> str:
        """Format retrieved documents as context for LLM."""
        context_parts = []
        current_length = 0
        
        for doc in documents:
            text = doc.text.strip()
            doc_text = f"[Source {doc.rank}]\n{text}\n"
            
            if current_length + len(doc_text) > max_chars:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "\n\n".join(context_parts)

# Usage
retriever = RAGRetriever(
    api_key="YOUR_API_KEY",
    default_dataset="ds_wikipedia_2023"
)

# Retrieve
docs = retriever.retrieve(
    query="How does transformer attention work?",
    top_k=5,
    search_type=SearchType.HYBRID
)

# Format context
context = retriever.format_context(docs, max_chars=3000)
```

---

## Part 3: Complete RAG Pipeline

Combine retrieval with LLM generation:

```python
from tensormarketdata import Client
from openai import OpenAI
from typing import Tuple

class RAGPipeline:
    def __init__(self, tmd_api_key: str, openai_api_key: str,
                 dataset_id: str):
        self.client = Client(api_key=tmd_api_key)
        self.llm = OpenAI(api_key=openai_api_key)
        self.retriever = RAGRetriever(tmd_api_key, dataset_id)
    
    def generate(self, query: str, system_prompt: Optional[str] = None,
                 max_tokens: int = 1000, temperature: float = 0.7) -> Tuple[str, dict]:
        """Execute RAG pipeline: retrieve → format → generate."""
        # Retrieve relevant documents
        print(f"Retrieving for query: {query}")
        documents = self.retriever.retrieve(
            query=query,
            top_k=5,
            search_type=SearchType.HYBRID
        )
        
        if not documents:
            return "I couldn't find relevant information to answer your question.", {}
        
        # Format context
        context = self.retriever.format_context(documents)
        
        # Build messages
        default_system = """You are a helpful assistant. Use the provided 
context to answer the user's question. If the context doesn't contain 
the answer, say so clearly. Cite sources using [Source N] notation."""
        
        messages = [
            {"role": "system", "content": system_prompt or default_system},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        # Generate response
        print("Generating response...")
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Collect sources
        sources = [
            {
                "rank": doc.rank,
                "id": doc.id,
                "score": doc.score,
                "preview": doc.metadata.get('title', doc.text[:100])
            }
            for doc in documents
        ]
        
        return response.choices[0].message.content, {"sources": sources}
    
    def stream_generate(self, query: str, **kwargs):
        """Stream generation for real-time output."""
        documents = self.retriever.retrieve(query=query, top_k=5)
        context = self.retriever.format_context(documents)
        
        messages = [
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        stream = self.llm.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

# Usage
pipeline = RAGPipeline(
    tmd_api_key="YOUR_TMD_API_KEY",
    openai_api_key="YOUR_OPENAI_API_KEY",
    dataset_id="ds_wikipedia_2023"
)

# Generate answer
answer, metadata = pipeline.generate(
    query="What are the main components of a transformer neural network?"
)

print("Answer:")
print(answer)
print("\nSources:")
for src in metadata['sources']:
    print(f"  [{src['rank']}] {src['preview']} (score: {src['score']:.3f})")

# Stream output
print("\nStreaming response:")
for chunk in pipeline.stream_generate("Explain backpropagation"):
    print(chunk, end="", flush=True)
```

---

## Part 4: Query Processing

Add advanced query processing:

```python
from typing import List
import re

class QueryProcessor:
    """Advanced query processing for better retrieval."""
    
    def __init__(self, client):
        self.client = client
    
    def decompose_query(self, query: str) -> List[str]:
        """Break complex queries into sub-queries."""
        # Simple sentence-based decomposition
        sentences = re.split(r'[.!?]', query)
        subqueries = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Add original query
        if query not in subqueries:
            subqueries.insert(0, query)
        
        return subqueries
    
    def expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        expansions = {
            "ai": ["artificial intelligence", "machine learning"],
            "ml": ["machine learning", "deep learning"],
            "nn": ["neural network", "neural net"],
            "transformer": ["attention mechanism", "self-attention"],
            "gpu": ["graphics processing unit", "cuda"]
        }
        
        expanded = [query]
        for word, synonyms in expansions.items():
            if word.lower() in query.lower():
                for syn in synonyms:
                    expanded.append(query.replace(word, syn))
        
        return expanded
    
    def process(self, query: str, strategy: str = "decompose") -> List[str]:
        """Process query using specified strategy."""
        if strategy == "decompose":
            return self.decompose_query(query)
        elif strategy == "expand":
            return self.expand_query(query)
        elif strategy == "both":
            subqueries = self.decompose_query(query)
            all_queries = []
            for sq in subqueries:
                all_queries.extend(self.expand_query(sq))
            return list(set(all_queries))
        else:
            return [query]

class MultiQueryRetriever:
    """Retrieve using multiple query variations."""
    
    def __init__(self, client, dataset_id: str):
        self.client = client
        self.dataset_id = dataset_id
        self.processor = QueryProcessor(client)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """Retrieve using multiple query variations and merge results."""
        # Generate query variations
        subqueries = self.processor.process(query, strategy="both")
        
        all_results = []
        seen_ids = set()
        
        # Search with each variation
        for sq in subqueries[:5]:  # Limit to 5 variations
            results = self.client.search(
                query=sq,
                dataset_id=self.dataset_id,
                top_k=top_k
            )
            
            for r in results:
                if r.id not in seen_ids:
                    seen_ids.add(r.id)
                    all_results.append({
                        'id': r.id,
                        'score': r.score,
                        'query': sq,
                        'metadata': r.metadata
                    })
        
        # Deduplicate and re-rank
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        return all_results[:top_k]

# Usage
processor = QueryProcessor(client)
subqueries = processor.process(
    "How do transformers use attention mechanisms in NLP?",
    strategy="both"
)

print("Query variations:")
for sq in subqueries:
    print(f"  - {sq}")
```

---

## Part 5: Evaluation

Evaluate your RAG system:

```python
from typing import List, Tuple
import numpy as np

class RAGEvaluator:
    """Evaluate RAG system performance."""
    
    def __init__(self, pipeline, test_queries: List[dict]):
        """
        test_queries: List of {
            'query': str,
            'answer': str,  # Expected answer
            'ground_truth_sources': [ids]  # Relevant document IDs
        }
        """
        self.pipeline = pipeline
        self.test_queries = test_queries
    
    def evaluate_retrieval(self, k_values: List[int] = [1, 5, 10]) -> dict:
        """Evaluate retrieval quality."""
        metrics = {}
        
        for k in k_values:
            hits = 0
            precision_sum = 0
            recall_sum = 0
            mrr_sum = 0  # Mean Reciprocal Rank
            
            for test in self.test_queries:
                results = self.pipeline.retriever.retrieve(
                    query=test['query'],
                    top_k=k
                )
                
                result_ids = {r.id for r in results}
                gt_ids = set(test['ground_truth_sources'])
                
                # Hit@K
                if result_ids & gt_ids:
                    hits += 1
                
                # Precision@K
                precision = len(result_ids & gt_ids) / k
                precision_sum += precision
                
                # Recall@K
                recall = len(result_ids & gt_ids) / len(gt_ids) if gt_ids else 0
                recall_sum += recall
                
                # MRR
                for i, r in enumerate(results, 1):
                    if r.id in gt_ids:
                        mrr_sum += 1 / i
                        break
            
            n = len(self.test_queries)
            metrics[f'hit@{k}'] = hits / n
            metrics[f'precision@{k}'] = precision_sum / n
            metrics[f'recall@{k}'] = recall_sum / n
            metrics[f'mrr@{k}'] = mrr_sum / n
        
        return metrics
    
    def evaluate_answer(self) -> dict:
        """Evaluate answer quality using embedding similarity."""
        scores = []
        
        for test in self.test_queries:
            answer, _ = self.pipeline.generate(test['query'])
            
            # Compute semantic similarity
            embeddings = self.pipeline.client.embed(
                texts=[test['answer'], answer],
                model="text-embedding-3-small"
            )
            
            similarity = self._cosine_sim(embeddings[0], embeddings[1])
            scores.append(similarity)
        
        return {
            'avg_answer_similarity': np.mean(scores),
            'std_answer_similarity': np.std(scores)
        }
    
    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot / (norm1 * norm2)
    
    def run_full_evaluation(self) -> dict:
        """Run complete evaluation."""
        retrieval_metrics = self.evaluate_retrieval()
        answer_metrics = self.evaluate_answer()
        
        return {**retrieval_metrics, **answer_metrics}

# Usage
test_queries = [
    {
        'query': "What is machine learning?",
        'answer': "Machine learning is a subset of AI...",
        'ground_truth_sources': ['doc_1', 'doc_2', 'doc_3']
    },
    {
        'query': "How do neural networks learn?",
        'answer': "Neural networks learn through backpropagation...",
        'ground_truth_sources': ['doc_4', 'doc_5']
    }
]

evaluator = RAGEvaluator(pipeline, test_queries)
metrics = evaluator.run_full_evaluation()

print("RAG Evaluation Metrics:")
for metric, value in metrics.items():
    print(f"  {metric}: {value:.4f}")
```

---

## Production Considerations

### Caching

```python
from functools import lru_cache

class CachedRAGPipeline(RAGPipeline):
    """RAG pipeline with query caching."""
    
    @lru_cache(maxsize=1000)
    def cached_retrieve(self, query: str, top_k: int = 5) -> Tuple[str, dict]:
        # Hash-based cache key
        cache_key = f"{query}:{top_k}"
        return super().retrieve(query, top_k)
```

### Async Processing

```python
import asyncio

class AsyncRAGPipeline:
    """Async RAG pipeline for high throughput."""
    
    async def generate_batch(self, queries: List[str]) -> List[Tuple[str, dict]]:
        client = Client(api_key="YOUR_API_KEY")
        tasks = [self._generate(q, client) for q in queries]
        return await asyncio.gather(*tasks)
    
    async def _generate(self, query: str, client) -> Tuple[str, dict]:
        # Async implementation
        results = await client.search_async(query=query, top_k=5)
        # ... rest of generation
        return answer, metadata
```

---

## Next Steps

- **[Advanced Search Techniques](./advanced-search.md)** - Filters, hybrid search
- **[Dataset Integration](./dataset-integration.md)** - Connect custom datasets
- **[Evaluation Guide](./evaluation.md)** - Comprehensive RAG evaluation
