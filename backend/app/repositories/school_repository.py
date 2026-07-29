"""
app/repositories/school_repository.py
───────────────────────────────────────
Async repositories for School and AcademicYear.

Design decisions:
  • SchoolRepository.get_active() filters is_deleted=False AND is_active=True
    (a suspended school is still soft-alive but functionally hidden).
  • AcademicYearRepository.set_current_year() updates ALL rows for a school
    in a single UPDATE statement before setting the target row — this avoids
    a transient state where two rows have is_current=True, which could
    confuse concurrent readers.
  • get_current_year() returns Optional[AcademicYear] — callers must handle
    the None case (school has no active year configured yet).
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.school import AcademicYear, School
from app.repositories.base_repository import BaseRepository


# ── SchoolRepository ───────────────────────────────────────────────────────────

class SchoolRepository(BaseRepository[School]):

    def __init__(self) -> None:
        super().__init__(School)

    async def get_by_code(
        self, db: AsyncSession, code: str
    ) -> Optional[School]:
        """Return the school with this unique code, or None."""
        result = await db.execute(
            select(School).where(School.code == code, School.is_deleted == False)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def get_active(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[School]:
        """Return active (not deleted, not suspended) schools."""
        result = await db.execute(
            select(School)
            .where(School.is_deleted == False, School.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_active(self, db: AsyncSession) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count()).select_from(School).where(
                School.is_deleted == False, School.is_active == True  # noqa: E712
            )
        )
        return result.scalar_one()

    async def get_with_academic_years(
        self, db: AsyncSession, school_id: uuid.UUID
    ) -> Optional[School]:
        """Return a school with its academic_years eagerly loaded."""
        result = await db.execute(
            select(School)
            .where(School.id == school_id, School.is_deleted == False)  # noqa: E712
            .options(selectinload(School.academic_years))
        )
        return result.scalar_one_or_none()


# ── AcademicYearRepository ─────────────────────────────────────────────────────

class AcademicYearRepository(BaseRepository[AcademicYear]):

    def __init__(self) -> None:
        super().__init__(AcademicYear)

    async def get_by_school(
        self, db: AsyncSession, school_id: uuid.UUID
    ) -> Sequence[AcademicYear]:
        """Return all academic years for a school, newest first."""
        result = await db.execute(
            select(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .order_by(AcademicYear.start_date.desc())
        )
        return result.scalars().all()

    async def get_current_year(
        self, db: AsyncSession, school_id: uuid.UUID
    ) -> Optional[AcademicYear]:
        """Return the academic year marked is_current=True for this school."""
        result = await db.execute(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_current == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_school_and_name(
        self, db: AsyncSession, school_id: uuid.UUID, name: str
    ) -> Optional[AcademicYear]:
        result = await db.execute(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def set_current_year(
        self, db: AsyncSession, school_id: uuid.UUID, year_id: uuid.UUID
    ) -> AcademicYear:
        """
        Atomically mark year_id as current and clear all other years for
        this school. Uses two UPDATE statements in the same transaction.
        """
        # Step 1: clear all current flags for this school
        await db.execute(
            update(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .values(is_current=False)
        )
        # Step 2: set the target year
        await db.execute(
            update(AcademicYear)
            .where(
                AcademicYear.school_id == school_id,
                AcademicYear.id == year_id,
            )
            .values(is_current=True)
        )
        await db.commit()

        result = await db.execute(
            select(AcademicYear).where(AcademicYear.id == year_id)
        )
        return result.scalar_one()


# ── Module-level singletons ────────────────────────────────────────────────────
school_repo       = SchoolRepository()
academic_year_repo = AcademicYearRepository()
