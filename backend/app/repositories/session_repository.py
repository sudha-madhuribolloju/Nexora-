import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import ClassSession as Session, SessionStatus

class SessionRepository:
    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        course_id: Optional[uuid.UUID] = None,
        teacher_id: Optional[uuid.UUID] = None,
        status_val: Optional[SessionStatus] = None,
    ) -> Tuple[int, List[Session]]:
        """
        List sessions filtered by course, teacher, or status with pagination.
        Returns (total_count, sessions_list).
        """
        q = select(Session)
        if course_id:
            q = q.where(Session.course_id == course_id)
        if teacher_id:
            q = q.where(Session.teacher_id == teacher_id)
        if status_val:
            q = q.where(Session.status == status_val)

        # Count total
        count_q = select(func.count()).select_from(q.subquery())
        total_result = await db.execute(count_q)
        total = total_result.scalar_one()

        # Fetch records
        records_q = q.offset(skip).limit(limit)
        records_result = await db.execute(records_q)
        sessions = records_result.scalars().all()

        return total, list(sessions)

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: uuid.UUID) -> Optional[Session]:
        """
        Get a specific session by ID.
        """
        result = await db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, session_data: dict) -> Session:
        """
        Create a new session.
        """
        session = Session(**session_data)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def update(db: AsyncSession, session_id: uuid.UUID, updates: dict) -> Optional[Session]:
        """
        Update an existing session.
        """
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            return None

        for field, value in updates.items():
            setattr(session, field, value)

        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def delete(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """
        Delete a session.
        """
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            return False

        await db.delete(session)
        await db.commit()
        return True
