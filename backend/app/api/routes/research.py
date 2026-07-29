from typing import Any, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.research_service import ResearchService

router = APIRouter()


class ResearchChatRequest(BaseModel):
    query: str
    document_id: Optional[uuid.UUID] = None
    top_k: int = 5


@router.post("/chat", summary="AI Research Assistant chat using pgvector + Gemini")
async def research_chat(
    payload: ResearchChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    AI Research assistant endpoint:
    Performs vector retrieval from PostgreSQL pgvector and deep research synthesis via Gemini.
    """
    if not payload.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")

    result = await ResearchService.research_chat(
        db=db,
        query=payload.query,
        user_id=current_user.id,
        document_id=payload.document_id,
        top_k=payload.top_k
    )
    return {
        "status": "success",
        "data": result
    }
