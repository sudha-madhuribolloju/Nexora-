from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepository:
    """
    Repository layer for User model database operations.
    Contains ONLY database queries and writes.
    """

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        hashed_password: str,
        role: str,
        is_active: bool = True,
        is_verified: bool = False,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """
        Persists a new User record to the database.
        """
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Retrieves a User record by its primary key ID.
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Retrieves a User record by email address.
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(db: AsyncSession, db_user: User, updates: Dict[str, Any]) -> User:
        """
        Updates an existing User record with the provided dictionary of changes.
        """
        for key, value in updates.items():
            if hasattr(db_user, key):
                setattr(db_user, key, value)
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
