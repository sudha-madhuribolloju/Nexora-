import uuid
import logging
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk

logger = logging.getLogger("app.services.retrieval_service")


class RetrievalService:
    """
    Service responsible for vector similarity search over PostgreSQL pgvector stored embeddings.
    """

    @staticmethod
    async def search_similar_chunks(
        db: AsyncSession,
        query_embedding: List[float],
        top_k: int = 5,
        document_id: Optional[uuid.UUID] = None,
        uploaded_by: Optional[uuid.UUID] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform cosine similarity search against document_chunks in PostgreSQL using pgvector.
        Returns list of (DocumentChunk, similarity_score) tuples sorted by nearest distance.
        """

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

        chunk_results = []

        for chunk, dist in rows:
            similarity = max(
                0.0,
                1.0 - float(dist if dist is not None else 1.0)
            )

            if similarity >= 0.70:
                chunk_results.append((chunk, similarity))

        return chunk_results