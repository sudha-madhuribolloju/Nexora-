from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentUpdate

class ParentService:
    """
    Service class managing Parent details architecture.
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, parent_id: uuid.UUID) -> Optional[Parent]:
        pass

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Parent]:
        return []

    @staticmethod
    async def create(db: AsyncSession, parent_in: ParentCreate) -> Parent:
        pass

    @staticmethod
    async def update(db: AsyncSession, parent_id: uuid.UUID, parent_in: ParentUpdate) -> Optional[Parent]:
        pass

    @staticmethod
    async def delete(db: AsyncSession, parent_id: uuid.UUID) -> bool:
        return True
