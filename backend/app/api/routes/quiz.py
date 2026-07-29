from typing import Any, Optional
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.quiz_service import QuizService

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    document_id: Optional[uuid.UUID] = None
    topic: Optional[str] = None
    num_questions: int = 5
    difficulty: str = "medium"


@router.post("/generate", summary="Generate AI Quiz using Gemini")
async def generate_quiz(
    payload: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Generate multiple-choice quiz questions based on indexed document or topic using Gemini.
    """
    result = await QuizService.generate_quiz(
        db=db,
        document_id=payload.document_id,
        topic=payload.topic,
        num_questions=payload.num_questions,
        difficulty=payload.difficulty
    )
    return result
