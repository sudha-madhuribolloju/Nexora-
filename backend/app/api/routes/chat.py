import uuid
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.rag_service import RAGService
from app.services.chat_session_service import ChatSessionService
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatQueryRequest,
    ChatQueryResponse
)

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED, summary="Create AI Chat Session")
async def create_session(
    payload: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Initialize a fresh AI chat session thread for the authenticated user.
    """
    return await ChatSessionService.create_session(
        db=db, user_id=current_user.id, title=payload.title
    )


@router.get("/sessions", response_model=List[ChatSessionResponse], summary="List User Chat Sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all active chat sessions for the authenticated user sorted by recent activity.
    """
    return await ChatSessionService.list_user_sessions(db=db, user_id=current_user.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse, summary="Get Chat Session & Message History")
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve chat session details and conversation message history.
    """
    return await ChatSessionService.get_session(db=db, session_id=session_id, user_id=current_user.id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Chat Session")
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a chat session thread and associated messages.
    """
    await ChatSessionService.delete_session(db=db, session_id=session_id, user_id=current_user.id)


@router.post("/", summary="RAG Chat Query")
@router.post("/query", summary="RAG Chat Query Endpoint")
async def chat_query(
    payload: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Context-Grounded RAG Chat Endpoint:
    1. Embeds question prompt using Gemini Embedding API
    2. Performs top-K vector cosine similarity search in PostgreSQL via pgvector
    3. Calculates confidence score and label (High / Medium / Low)
    4. Evaluates prompt against strict hallucination-suppression instructions
    5. Stores user question and AI answer in chat history
    6. Returns AI response with confidence & document source citations
    """
    if not payload.message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message prompt cannot be empty."
        )

    parsed_session_id = payload.session_id

    result = await RAGService.answer_question(
        db=db,
        question=payload.message,
        session_id=parsed_session_id,
        document_id=payload.document_id,
        uploaded_by=current_user.id,
        top_k=payload.top_k
    )

    return {
        "status": "success",
        "data": result
    }
