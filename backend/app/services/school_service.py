"""
app/services/school_service.py
───────────────────────────────
Business logic for schools and academic years.

Design decisions:
  • school_code is forced to UPPER case before persistence to avoid
    duplicate entries that differ only in case (e.g. "ghs001" vs "GHS001").
  • Soft-delete on School cascades to users via school_id=NULL (SET NULL FK),
    NOT to academic years (those are CASCADE DELETE in the DB). This preserves
    historical user data while freeing the school namespace.
  • set_current_year is a single service-layer operation that delegates the
    two-UPDATE atomic pattern to AcademicYearRepository — the service doesn't
    touch raw SQL.
  • All list methods return (items, total) tuples so routes can construct
    PaginatedResponse without extra round-trips.
"""

import uuid
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import AcademicYear, School
from app.repositories.school_repository import academic_year_repo, school_repo
from app.schemas.school import (
    AcademicYearCreate,
    AcademicYearUpdate,
    SchoolCreate,
    SchoolUpdate,
)


class SchoolService:

    # ══════════════════════════════════════════════════════════════════════════
    # SCHOOLS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_school(self, db: AsyncSession, data: SchoolCreate) -> School:
        """Create a new school. Raises 409 if the school code already exists."""
        code = data.code.upper()
        existing = await school_repo.get_by_code(db, code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A school with code '{code}' already exists.",
            )
        payload = data.model_dump()
        payload["code"] = code
        try:
            return await school_repo.create(db, payload)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"School code '{code}' is already taken.",
            )

    async def get_school(
        self, db: AsyncSession, school_id: uuid.UUID, *, with_years: bool = False
    ) -> School:
        """Return a school by ID. Raises 404 if not found or soft-deleted."""
        if with_years:
            school = await school_repo.get_with_academic_years(db, school_id)
        else:
            school = await school_repo.get_by_id(db, school_id)
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="School not found."
            )
        return school

    async def get_school_by_code(self, db: AsyncSession, code: str) -> School:
        school = await school_repo.get_by_code(db, code.upper())
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"School with code '{code.upper()}' not found.",
            )
        return school

    async def list_schools(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[School], int]:
        schools = await school_repo.get_active(db, skip=skip, limit=limit)
        total   = await school_repo.count_active(db)
        return schools, total

    async def update_school(
        self, db: AsyncSession, school_id: uuid.UUID, data: SchoolUpdate
    ) -> School:
        school = await school_repo.get_by_id(db, school_id)
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="School not found."
            )
        updates = data.model_dump(exclude_none=True)
        # Preserve code-case invariant
        if "code" in updates:
            updates["code"] = updates["code"].upper()
        return await school_repo.update(db, school, updates)

    async def delete_school(self, db: AsyncSession, school_id: uuid.UUID) -> None:
        """Soft-delete a school. Users retain their accounts; school_id is SET NULL by FK."""
        school = await school_repo.get_by_id(db, school_id)
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="School not found."
            )
        await school_repo.soft_delete(db, school)

    # ══════════════════════════════════════════════════════════════════════════
    # ACADEMIC YEARS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_academic_year(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        data: AcademicYearCreate,
    ) -> AcademicYear:
        """Create a new academic year scoped to a school."""
        # School must exist
        await self.get_school(db, school_id)

        # Duplicate name check
        existing = await academic_year_repo.get_by_school_and_name(
            db, school_id, data.name
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Academic year '{data.name}' already exists for this school.",
            )

        payload = data.model_dump()
        payload["school_id"] = school_id

        # If this year is being set as current, clear existing current flag first
        if data.is_current:
            current = await academic_year_repo.get_current_year(db, school_id)
            if current:
                await academic_year_repo.update(db, current, {"is_current": False})

        try:
            return await academic_year_repo.create(db, payload)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Academic year '{data.name}' already exists for this school.",
            )

    async def list_academic_years(
        self, db: AsyncSession, school_id: uuid.UUID
    ) -> Sequence[AcademicYear]:
        await self.get_school(db, school_id)
        return await academic_year_repo.get_by_school(db, school_id)

    async def get_academic_year(
        self, db: AsyncSession, school_id: uuid.UUID, year_id: uuid.UUID
    ) -> AcademicYear:
        year = await academic_year_repo.get_by_id(db, year_id)
        if not year or year.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic year not found for this school.",
            )
        return year

    async def update_academic_year(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        year_id: uuid.UUID,
        data: AcademicYearUpdate,
    ) -> AcademicYear:
        year = await self.get_academic_year(db, school_id, year_id)
        updates = data.model_dump(exclude_none=True)

        # If promoting to current, demote the existing current year first
        if updates.get("is_current") is True:
            current = await academic_year_repo.get_current_year(db, school_id)
            if current and current.id != year_id:
                await academic_year_repo.update(db, current, {"is_current": False})

        return await academic_year_repo.update(db, year, updates)

    async def set_current_academic_year(
        self, db: AsyncSession, school_id: uuid.UUID, year_id: uuid.UUID
    ) -> AcademicYear:
        """
        Mark year_id as the current academic year for this school.
        All other years for this school are atomically set to is_current=False.
        """
        await self.get_school(db, school_id)
        year = await academic_year_repo.get_by_id(db, year_id)
        if not year or year.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic year not found for this school.",
            )
        return await academic_year_repo.set_current_year(db, school_id, year_id)

    async def get_current_academic_year(
        self, db: AsyncSession, school_id: uuid.UUID
    ) -> Optional[AcademicYear]:
        await self.get_school(db, school_id)
        return await academic_year_repo.get_current_year(db, school_id)


# Module-level singleton
school_service = SchoolService()
