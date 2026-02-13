"""
Vector search service using pgvector.
Provides semantic search capabilities for suppliers.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.domain import Supplier


class VectorSearchService:
    """
    Handles vector similarity search using pgvector.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text using local LLM.
        Replace with actual embedding model (Ollama, HuggingFace, etc.)
        """
        # TODO: Implement actual embedding generation
        # For now, return mock embedding
        import random
        return [random.uniform(-1, 1) for _ in range(settings.vector_size)]

    async def search_by_text(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> List[Tuple[Supplier, float]]:
        """
        Search suppliers by natural language query.
        Returns list of (supplier, similarity_score) tuples.
        """
        # Generate query embedding
        query_embedding = await self.embed_text(query)

        # pgvector similarity search query
        # Note: Adjust operator based on pgvector version (<0.7.0 uses <#>, >=0.7.0 uses <=>)
        query_text = """
            SELECT id, name, contact_json, verification_score,
                   last_verified_at, created_at, updated_at,
                   (industry_vector <=> :embedding) AS similarity
            FROM suppliers
            WHERE industry_vector IS NOT NULL
            AND (industry_vector <=> :embedding) < :threshold
            ORDER BY similarity ASC
            LIMIT :limit
        """

        result = await self.session.execute(
            text(query_text),
            {
                "embedding": str(query_embedding),
                "threshold": 1 - min_score,  # Convert similarity to distance
                "limit": limit,
            },
        )
        rows = result.fetchall()

        suppliers = []
        for row in rows:
            supplier = Supplier(
                id=row[0],
                name=row[1],
                contact_json=row[2],
                verification_score=row[3],
                last_verified_at=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            similarity = 1 - row[7]  # Convert distance back to similarity
            suppliers.append((supplier, similarity))

        return suppliers

    async def search_by_vector(
        self,
        embedding: List[float],
        limit: int = 10,
        min_score: float = 0.5,
    ) -> List[Tuple[Supplier, float]]:
        """
        Search suppliers by raw vector embedding.
        """
        query_text = """
            SELECT id, name, contact_json, verification_score,
                   last_verified_at, created_at, updated_at,
                   (industry_vector <=> :embedding) AS similarity
            FROM suppliers
            WHERE industry_vector IS NOT NULL
            AND (industry_vector <=> :embedding) < :threshold
            ORDER BY similarity ASC
            LIMIT :limit
        """

        result = await self.session.execute(
            text(query_text),
            {
                "embedding": str(embedding),
                "threshold": 1 - min_score,
                "limit": limit,
            },
        )
        rows = result.fetchall()

        suppliers = []
        for row in rows:
            supplier = Supplier(
                id=row[0],
                name=row[1],
                contact_json=row[2],
                verification_score=row[3],
                last_verified_at=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            similarity = 1 - row[7]
            suppliers.append((supplier, similarity))

        return suppliers

    async def update_supplier_embedding(
        self,
        supplier_id: UUID,
        text: str,
    ) -> None:
        """
        Generate and store embedding for a supplier.
        """
        embedding = await self.embed_text(text)

        await self.session.execute(
            text("UPDATE suppliers SET industry_vector = :embedding WHERE id = :id"),
            {"embedding": str(embedding), "id": str(supplier_id)},
        )
        await self.session.commit()


async def get_search_service(session: AsyncSession) -> VectorSearchService:
    """
    Factory function to get search service instance.
    """
    return VectorSearchService(session)
