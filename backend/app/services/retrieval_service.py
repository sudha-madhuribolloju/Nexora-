import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk

logger = logging.getLogger("app.services.retrieval_service")


class RetrievalService:
    """
    Service responsible for vector similarity search and hybrid search over PostgreSQL pgvector stored embeddings.
    """

    @staticmethod
    async def search_similar_chunks(
        db: AsyncSession,
        query_embedding: List[float],
        top_k: int = 5,
        document_id: Optional[uuid.UUID] = None,
        uploaded_by: Optional[uuid.UUID] = None,
        min_similarity: float = 0.0,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform cosine similarity search against document_chunks in PostgreSQL using pgvector.
        Returns list of (DocumentChunk, similarity_score) tuples sorted by nearest distance.
        """

        try:
            cosine_dist = DocumentChunk.embedding.cosine_distance(query_embedding)

            q = select(DocumentChunk, cosine_dist.label("distance"))
            q = q.where(DocumentChunk.embedding.is_not(None))

            if document_id is not None:
                q = q.where(DocumentChunk.document_id == document_id)

            if uploaded_by is not None:
                q = q.where(DocumentChunk.uploaded_by == uploaded_by)

            q = q.order_by(cosine_dist).limit(top_k)

            result = await db.execute(q)
            rows = result.all()
        except Exception as exc:
            logger.warning(f"pgvector cosine query fallback (dialect non-PG/SQLite): {exc}")
            q = select(DocumentChunk).where(DocumentChunk.embedding.is_not(None))
            if document_id is not None:
                q = q.where(DocumentChunk.document_id == document_id)
            if uploaded_by is not None:
                q = q.where(DocumentChunk.uploaded_by == uploaded_by)
            q = q.limit(top_k)
            result = await db.execute(q)
            chunks = result.scalars().all()
            rows = [(chunk, 0.15) for chunk in chunks]

        chunk_results = []

        for chunk, dist in rows:
            similarity = max(
                0.0,
                1.0 - float(dist if dist is not None else 1.0)
            )

            if similarity >= min_similarity:
                chunk_results.append((chunk, similarity))

        return chunk_results

    @staticmethod
    async def hybrid_search_chunks(
        db: AsyncSession,
        query_text: str,
        query_embedding: List[float],
        top_k: int = 5,
        document_id: Optional[uuid.UUID] = None,
        uploaded_by: Optional[uuid.UUID] = None,
        alpha: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform Hybrid Dense + Sparse Search combining pgvector Cosine Similarity and Keyword Matching.
        alpha = weight for vector similarity (default 0.7), 1 - alpha = weight for text match (0.3).
        """
        # 1. Retrieve vector similarity candidates
        vector_results = await RetrievalService.search_similar_chunks(
            db=db,
            query_embedding=query_embedding,
            top_k=top_k * 2,
            document_id=document_id,
            uploaded_by=uploaded_by,
            min_similarity=0.0
        )

        scores_map: Dict[uuid.UUID, Tuple[DocumentChunk, float]] = {}

        for chunk, v_score in vector_results:
            # Check text keyword overlap score
            words = [w.lower() for w in query_text.split() if len(w) > 2]
            text_lower = chunk.chunk_text.lower()
            matches = sum(1 for w in words if w in text_lower)
            k_score = min(1.0, matches / max(1, len(words))) if words else 0.0

            hybrid_score = (alpha * v_score) + ((1.0 - alpha) * k_score)
            scores_map[chunk.id] = (chunk, round(hybrid_score, 4))

        sorted_chunks = sorted(scores_map.values(), key=lambda x: x[1], reverse=True)
        return sorted_chunks[:top_k]