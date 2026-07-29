"""
app/repositories/base_repository.py
────────────────────────────────────
Generic async CRUD base for all domain repositories.

Design decisions:
  • Generic[ModelT] gives full type-safety — IDE auto-completes the correct
    model type without casting.
  • All queries use soft-delete awareness by default (filter_deleted=True).
    Pass filter_deleted=False only for admin/audit endpoints.
  • Pagination (skip/limit) is applied at the DB level, never in Python.
  • count() is a separate lightweight query so list endpoints can return
    totals without fetching all rows.
"""

from datetime import datetime, timezone
from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Async CRUD repository. Extend this per domain; add domain-specific
    query methods alongside these generics.
    """

    def __init__(self, model: Type[ModelT]) -> None:
        self.model = model

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_by_id(
        self,
        db: AsyncSession,
        record_id: Any,
        *,
        filter_deleted: bool = True,
    ) -> Optional[ModelT]:
        """Return a single record by PK, or None if not found."""
        stmt = select(self.model).where(self.model.id == record_id)
        if filter_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filter_deleted: bool = True,
    ) -> Sequence[ModelT]:
        """Return a paginated list of active records."""
        stmt = select(self.model)
        if filter_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(self, db: AsyncSession, *, filter_deleted: bool = True) -> int:
        """Return total row count — used for pagination metadata."""
        stmt = select(func.count()).select_from(self.model)
        if filter_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one()

    # ── Write ──────────────────────────────────────────────────────────────────

    async def create(self, db: AsyncSession, obj_in: dict[str, Any]) -> ModelT:
        """Persist a new record and return the refreshed instance."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelT,
        updates: dict[str, Any],
    ) -> ModelT:
        """Apply a partial update dict to an existing record."""
        for key, value in updates.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def soft_delete(self, db: AsyncSession, db_obj: ModelT) -> ModelT:
        """
        Mark a record as deleted without removing it from the database.
        Raises AttributeError if the model does not include SoftDeleteMixin.
        """
        if not hasattr(db_obj, "is_deleted"):
            raise AttributeError(
                f"Model '{self.model.__name__}' does not support soft delete. "
                "Add SoftDeleteMixin to the model."
            )
        db_obj.is_deleted = True  # type: ignore[attr-defined]
        db_obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def hard_delete(self, db: AsyncSession, db_obj: ModelT) -> None:
        """
        Permanently remove a record. Use only for GDPR erasure requests.
        """
        await db.delete(db_obj)
        await db.commit()
