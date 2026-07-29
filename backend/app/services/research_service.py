import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag_service import RAGService

logger = logging.getLogger("app.services.research_service")


class ResearchService:
    """
    Service for AI Research assistance combining vector retrieval and research synthesis using Gemini.
    """

    @staticmethod
    async def research_chat(
        db: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        document_id: Optional[uuid.UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Execute an AI Research synthesis query across pgvector document chunks.
        """
        rag_result = await RAGService.answer_question(
            db=db,
            question=query,
            document_id=document_id,
            uploaded_by=user_id,
            top_k=top_k
        )

        return {
            "research_query": query,
            "findings": rag_result["answer"],
            "cited_sources": rag_result["sources"],
            "status": "completed"
        }
