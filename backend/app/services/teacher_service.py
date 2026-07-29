from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate

class TeacherService:
    """
    Service class managing Teacher details architecture.
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, teacher_id: uuid.UUID) -> Optional[Teacher]:
        pass

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Teacher]:
        return []

    @staticmethod
    async def create(db: AsyncSession, teacher_in: TeacherCreate) -> Teacher:
        pass

    @staticmethod
    async def update(db: AsyncSession, teacher_id: uuid.UUID, teacher_in: TeacherUpdate) -> Optional[Teacher]:
        pass

    @staticmethod
    async def delete(db: AsyncSession, teacher_id: uuid.UUID) -> bool:
        return True
