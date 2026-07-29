"""
Session service — CRUD and lifecycle (start/end) for class sessions.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.session import ClassSession as Session, SessionStatus
from app.schemas.session import SessionCreate, SessionUpdate


class SessionService:

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        course_id: Optional[uuid.UUID] = None,
        teacher_id: Optional[uuid.UUID] = None,
        session_status: Optional[SessionStatus] = None,
    ) -> Tuple[int, List[Session]]:
        q = select(Session)
        if course_id:
            q = q.where(Session.course_id == course_id)
        if teacher_id:
            q = q.where(Session.teacher_id == teacher_id)
        if session_status:
            q = q.where(Session.status == session_status)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        sessions = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(sessions)

    @staticmethod
    async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    @staticmethod
    async def create_session(db: AsyncSession, data: SessionCreate) -> Session:
        session = Session(**data.model_dump())
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def update_session(db: AsyncSession, session_id: uuid.UUID, data: SessionUpdate) -> Session:
        session = await SessionService.get_session(db, session_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(session, field, value)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> None:
        session = await SessionService.get_session(db, session_id)
        await db.delete(session)
        await db.commit()

    @staticmethod
    async def start_session(db: AsyncSession, session_id: uuid.UUID) -> Session:
        session = await SessionService.get_session(db, session_id)
        if session.status == SessionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already active")
        if session.status == SessionStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already completed")
        session.status = SessionStatus.ACTIVE
        session.started_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def end_session(db: AsyncSession, session_id: uuid.UUID) -> Session:
        session = await SessionService.get_session(db, session_id)
        if session.status != SessionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not active")
        session.status = SessionStatus.COMPLETED
        session.ended_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session
