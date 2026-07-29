from typing import Any, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.rag_service import RAGService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    document_id: Optional[uuid.UUID] = None
    top_k: int = 5


@router.post("/", summary="Student RAG Chat using PostgreSQL pgvector + Gemini")
@router.post("/chat", summary="Student RAG Chat using PostgreSQL pgvector + Gemini")
async def chat_rag(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    RAG Chat endpoint:
    1. Embeds student question via Gemini Embedding API
    2. Searches PostgreSQL via pgvector cosine similarity
    3. Sends retrieved chunks + question to Gemini Chat Model
    4. Returns AI response with source citations
    """
    if not payload.message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message prompt cannot be empty.")

    result = await RAGService.answer_question(
        db=db,
        question=payload.message,
        document_id=payload.document_id,
        uploaded_by=current_user.id,
        top_k=payload.top_k
    )
    return {
        "status": "success",
        "data": result
    }
