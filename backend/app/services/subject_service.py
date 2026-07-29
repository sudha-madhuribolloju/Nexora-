"""
Subject service — CRUD operations for subjects within courses.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.subject import CourseSubject as Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


class SubjectService:

    @staticmethod
    async def list_subjects(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        course_id: Optional[uuid.UUID] = None,
    ) -> Tuple[int, List[Subject]]:
        q = select(Subject)
        if course_id:
            q = q.where(Subject.course_id == course_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        subjects = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(subjects)

    @staticmethod
    async def get_subject(db: AsyncSession, subject_id: uuid.UUID) -> Subject:
        result = await db.execute(select(Subject).where(Subject.id == subject_id))
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        return subject

    @staticmethod
    async def create_subject(db: AsyncSession, data: SubjectCreate) -> Subject:
        subject = Subject(**data.model_dump())
        db.add(subject)
        await db.commit()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def update_subject(db: AsyncSession, subject_id: uuid.UUID, data: SubjectUpdate) -> Subject:
        subject = await SubjectService.get_subject(db, subject_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(subject, field, value)
        await db.commit()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def delete_subject(db: AsyncSession, subject_id: uuid.UUID) -> None:
        subject = await SubjectService.get_subject(db, subject_id)
        await db.delete(subject)
        await db.commit()
