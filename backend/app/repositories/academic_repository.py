"""
app/repositories/academic_repository.py
─────────────────────────────────────────
Async repositories for Class, Section, and Subject.

Design decisions:
  • ClassRepository.get_by_school_and_year() is the primary listing query —
    classes are almost always filtered by both school AND academic year.
  • SectionRepository.get_by_school() includes school_id in the WHERE clause
    (using the denormalised column) to avoid the JOIN through classes.
  • SubjectRepository.search() does a case-insensitive prefix match on name
    and code — useful for autocomplete dropdowns on the frontend.
  • All list queries honour the soft-delete flag (is_deleted=False).
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.academic import Class, Section, Subject
from app.repositories.base_repository import BaseRepository


# ── ClassRepository ────────────────────────────────────────────────────────────

class ClassRepository(BaseRepository[Class]):

    def __init__(self) -> None:
        super().__init__(Class)

    async def get_by_school_and_year(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> Sequence[Class]:
        """Return all active classes for a school + year, ordered by grade_level."""
        result = await db.execute(
            select(Class)
            .where(
                Class.school_id == school_id,
                Class.academic_year_id == academic_year_id,
                Class.is_deleted == False,  # noqa: E712
            )
            .order_by(Class.grade_level.asc().nulls_last(), Class.name)
        )
        return result.scalars().all()

    async def get_by_school(
        self, db: AsyncSession, school_id: uuid.UUID, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Class]:
        """Return all active classes for a school across all years."""
        result = await db.execute(
            select(Class)
            .where(Class.school_id == school_id, Class.is_deleted == False)  # noqa: E712
            .order_by(Class.grade_level.asc().nulls_last(), Class.name)
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_with_sections(
        self, db: AsyncSession, class_id: uuid.UUID
    ) -> Optional[Class]:
        """Return a class with its sections eagerly loaded."""
        result = await db.execute(
            select(Class)
            .where(Class.id == class_id, Class.is_deleted == False)  # noqa: E712
            .options(
                selectinload(Class.sections.and_(Section.is_deleted == False))  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name_in_year(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        name: str,
    ) -> Optional[Class]:
        result = await db.execute(
            select(Class).where(
                Class.school_id == school_id,
                Class.academic_year_id == academic_year_id,
                Class.name == name,
                Class.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def count_by_school(self, db: AsyncSession, school_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(Class).where(
                Class.school_id == school_id, Class.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()


# ── SectionRepository ──────────────────────────────────────────────────────────

class SectionRepository(BaseRepository[Section]):

    def __init__(self) -> None:
        super().__init__(Section)

    async def get_by_class(
        self, db: AsyncSession, class_id: uuid.UUID
    ) -> Sequence[Section]:
        """Return all active sections for a class, alphabetically."""
        result = await db.execute(
            select(Section)
            .where(Section.class_id == class_id, Section.is_deleted == False)  # noqa: E712
            .order_by(Section.name)
        )
        return result.scalars().all()

    async def get_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[Section]:
        """Return all active sections for a school (uses denormalized column)."""
        result = await db.execute(
            select(Section)
            .where(Section.school_id == school_id, Section.is_deleted == False)  # noqa: E712
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_class_and_name(
        self, db: AsyncSession, class_id: uuid.UUID, name: str
    ) -> Optional[Section]:
        result = await db.execute(
            select(Section).where(
                Section.class_id == class_id,
                Section.name == name,
                Section.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def count_by_class(self, db: AsyncSession, class_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(Section).where(
                Section.class_id == class_id, Section.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()


# ── SubjectRepository ──────────────────────────────────────────────────────────

class SubjectRepository(BaseRepository[Subject]):

    def __init__(self) -> None:
        super().__init__(Subject)

    async def get_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[Subject]:
        """Return all active subjects for a school, alphabetically."""
        result = await db.execute(
            select(Subject)
            .where(Subject.school_id == school_id, Subject.is_deleted == False)  # noqa: E712
            .order_by(Subject.name)
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_code(
        self, db: AsyncSession, school_id: uuid.UUID, code: str
    ) -> Optional[Subject]:
        """Return subject by unique (school_id, code) pair."""
        result = await db.execute(
            select(Subject).where(
                Subject.school_id == school_id,
                Subject.code == code.upper(),
                Subject.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        query: str,
        *,
        limit: int = 20,
    ) -> Sequence[Subject]:
        """Case-insensitive prefix search across name and code."""
        pattern = f"{query.upper()}%"
        result = await db.execute(
            select(Subject)
            .where(
                Subject.school_id == school_id,
                Subject.is_deleted == False,  # noqa: E712
                or_(
                    func.upper(Subject.name).like(pattern),
                    Subject.code.like(pattern),
                ),
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_school(self, db: AsyncSession, school_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(Subject).where(
                Subject.school_id == school_id, Subject.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()


# ── Module-level singletons ────────────────────────────────────────────────────
class_repo   = ClassRepository()
section_repo = SectionRepository()
subject_repo = SubjectRepository()
