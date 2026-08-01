import logging
from typing import Any
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.utils.helpers import format_response

logger = logging.getLogger("app.api.routes.ai")

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Enterprise AI RAG Chat",
    description=(
        "Processes user message with RAG document grounding using pgvector cosine similarity search "
        "and Google Gemini LLM API. Automatically persists conversation history."
    ),
    response_description="Structured AI chat response with conversation ID, source citations, and token count"
)
async def ai_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    POST /api/v1/ai/chat
    Enterprise-grade AI chat endpoint.
    """
    try:
        response = await AIService.chat(db=db, current_user=current_user, request=request)
        return response
    except Exception as e:
        logger.error(f"Error processing POST /api/v1/ai/chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your AI chat request."
        )


@router.post("/query", response_model=Any)
async def query_ai(
    payload: dict
) -> Any:
    """
    General endpoint to query Google Gemini provider.
    Payload expectation: { "prompt": "..." }
    """
    prompt = payload.get("prompt", "Hello, Nexora AI!")
    response = await AIService.query_gemini(prompt)
    return format_response(status="success", message="AI query completed", data={"response": response})


@router.post("/agent/teacher", response_model=Any)
async def run_teacher_agent(
    task_description: dict
) -> Any:
    """
    Trigger the teacher assistant agent.
    """
    return format_response(status="success", message="Teacher agent execution triggered stub")
