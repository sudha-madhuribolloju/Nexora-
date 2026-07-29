from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate

class StudentService:
    """
    Service class managing Student details architecture.
    """
    
    @staticmethod
    async def get_by_id(db: AsyncSession, student_id: uuid.UUID) -> Optional[Student]:
        pass

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Student]:
        return []

    @staticmethod
    async def create(db: AsyncSession, student_in: StudentCreate) -> Student:
        pass

    @staticmethod
    async def update(db: AsyncSession, student_id: uuid.UUID, student_in: StudentUpdate) -> Optional[Student]:
        pass

    @staticmethod
    async def delete(db: AsyncSession, student_id: uuid.UUID) -> bool:
        return True
