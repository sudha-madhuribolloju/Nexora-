import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document_chunk import DocumentChunk
from app.services.ai_service import AIService

logger = logging.getLogger("app.services.lecture_summary_service")


class LectureSummaryService:
    """
    Service for generating structured lecture summaries and key takeaways using Gemini AI.
    """

    @staticmethod
    async def summarize_lecture(
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None,
        lecture_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured lecture summary based on document ID (retrieved from pgvector chunks) or provided text.
        """
        content_to_summarize = lecture_text or ""

        if document_id and not content_to_summarize:
            # Retrieve all text chunks for this document from pgvector
            q = select(DocumentChunk.chunk_text).where(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index)
            result = await db.execute(q)
            chunks = result.scalars().all()
            if chunks:
                content_to_summarize = "\n\n".join(chunks)

        if not content_to_summarize:
            return {
                "summary": "No document content or text provided for summarization.",
                "key_takeaways": [],
                "topics_covered": []
            }

        summary_response = await AIService.summarize(transcript=content_to_summarize)

        return {
            "document_id": str(document_id) if document_id else None,
            "summary": summary_response,
            "status": "success"
        }
