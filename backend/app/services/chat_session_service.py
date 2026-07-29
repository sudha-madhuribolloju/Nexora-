import uuid
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionCreate

logger = logging.getLogger("app.services.chat_session_service")


class ChatSessionService:

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: Optional[str] = "New AI Chat Session"
    ) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            title=title or "New AI Chat Session",
            is_active=True
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def list_user_sessions(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.is_active == True)
            .order_by(desc(ChatSession.updated_at))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> ChatSession:
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        if user_id:
            stmt = stmt.where(ChatSession.user_id == user_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found."
            )
        return session

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        session = await ChatSessionService.get_session(db, session_id, user_id)
        await db.delete(session)
        await db.commit()

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: uuid.UUID,
        sender_type: str,
        content: str,
        sources_json: Optional[List[Dict[str, Any]]] = None
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            sender_type=sender_type,
            content=content,
            sources_json=sources_json
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_recent_history(
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 6
    ) -> List[Dict[str, str]]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        messages = list(reversed(res.scalars().all()))
        return [
            {"role": "user" if m.sender_type == "user" else "model", "content": m.content}
            for m in messages
        ]
