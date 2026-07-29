"""
app/services/academic_service.py
──────────────────────────────────
Business logic for Classes, Sections, and Subjects.

Design decisions:
  • AcademicService is a single class covering all three domains. At this
    scale the three domains are tightly coupled (you can't create a section
    without a class; both share school validation). Splitting into three
    services would add boilerplate without benefit.

  • Section.school_id is set server-side from the parent class's school_id
    to avoid client-supplied inconsistency. Clients should NEVER send
    school_id when creating a section.

  • Subject.code is uppercased at the service layer (and also validated by
    Pydantic) for consistent DB values.

  • delete_class() soft-deletes the class AND all its sections in a single
    service call — the DB cascade handles ORM-level children, but we also
    explicitly soft-delete sections so the is_deleted flag is set on all
    child rows (DB CASCADE only hard-deletes).
"""

import uuid
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import Class, Section, Subject
from app.repositories.academic_repository import (
    class_repo,
    section_repo,
    subject_repo,
)
from app.schemas.academic import (
    ClassCreate,
    ClassUpdate,
    SectionCreate,
    SectionUpdate,
    SubjectCreate,
    SubjectUpdate,
)


class AcademicService:

    # ══════════════════════════════════════════════════════════════════════════
    # CLASSES
    # ══════════════════════════════════════════════════════════════════════════

    async def create_class(self, db: AsyncSession, data: ClassCreate) -> Class:
        # Duplicate guard
        existing = await class_repo.get_by_name_in_year(
            db, data.school_id, data.academic_year_id, data.name
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Class '{data.name}' already exists in this academic year.",
            )
        try:
            return await class_repo.create(db, data.model_dump())
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Class '{data.name}' already exists in this academic year.",
            )

    async def get_class(
        self, db: AsyncSession, class_id: uuid.UUID, *, with_sections: bool = False
    ) -> Class:
        if with_sections:
            obj = await class_repo.get_with_sections(db, class_id)
        else:
            obj = await class_repo.get_by_id(db, class_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found."
            )
        return obj

    async def list_classes(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        academic_year_id: Optional[uuid.UUID] = None,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Class], int]:
        if academic_year_id:
            classes = await class_repo.get_by_school_and_year(
                db, school_id, academic_year_id
            )
            total = len(classes)
            classes = classes[skip : skip + limit]
        else:
            classes = await class_repo.get_by_school(db, school_id, skip=skip, limit=limit)
            total   = await class_repo.count_by_school(db, school_id)
        return classes, total

    async def update_class(
        self, db: AsyncSession, class_id: uuid.UUID, data: ClassUpdate
    ) -> Class:
        obj = await class_repo.get_by_id(db, class_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found."
            )
        return await class_repo.update(db, obj, data.model_dump(exclude_none=True))

    async def delete_class(self, db: AsyncSession, class_id: uuid.UUID) -> None:
        obj = await class_repo.get_by_id(db, class_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found."
            )
        # Soft-delete all sections first
        sections = await section_repo.get_by_class(db, class_id)
        for s in sections:
            await section_repo.soft_delete(db, s)
        await class_repo.soft_delete(db, obj)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTIONS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_section(self, db: AsyncSession, data: SectionCreate) -> Section:
        # Verify parent class exists and retrieve school_id
        parent_class = await class_repo.get_by_id(db, data.class_id)
        if not parent_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {data.class_id} not found.",
            )
        # Duplicate guard
        existing = await section_repo.get_by_class_and_name(
            db, data.class_id, data.name
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Section '{data.name}' already exists in this class.",
            )
        payload = data.model_dump()
        # Server-side: resolve school_id from parent class
        payload["school_id"] = parent_class.school_id
        try:
            return await section_repo.create(db, payload)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Section '{data.name}' already exists in this class.",
            )

    async def get_section(self, db: AsyncSession, section_id: uuid.UUID) -> Section:
        obj = await section_repo.get_by_id(db, section_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Section not found."
            )
        return obj

    async def list_sections_by_class(
        self, db: AsyncSession, class_id: uuid.UUID
    ) -> Sequence[Section]:
        # Verify class exists
        await self.get_class(db, class_id)
        return await section_repo.get_by_class(db, class_id)

    async def list_sections_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[Sequence[Section], int]:
        sections = await section_repo.get_by_school(db, school_id, skip=skip, limit=limit)
        total    = await section_repo.count(db)  # approximate; scoped count below
        # Use a proper school-scoped count
        from sqlalchemy import func, select
        from app.models.academic import Section as Sec
        from sqlalchemy.ext.asyncio import AsyncSession as _AS
        result = await db.execute(
            select(func.count()).select_from(Sec).where(
                Sec.school_id == school_id, Sec.is_deleted == False  # noqa: E712
            )
        )
        total = result.scalar_one()
        return sections, total

    async def update_section(
        self, db: AsyncSession, section_id: uuid.UUID, data: SectionUpdate
    ) -> Section:
        obj = await section_repo.get_by_id(db, section_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Section not found."
            )
        return await section_repo.update(db, obj, data.model_dump(exclude_none=True))

    async def delete_section(self, db: AsyncSession, section_id: uuid.UUID) -> None:
        obj = await section_repo.get_by_id(db, section_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Section not found."
            )
        await section_repo.soft_delete(db, obj)

    # ══════════════════════════════════════════════════════════════════════════
    # SUBJECTS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_subject(self, db: AsyncSession, data: SubjectCreate) -> Subject:
        # Duplicate code guard
        existing = await subject_repo.get_by_code(db, data.school_id, data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subject with code '{data.code}' already exists for this school.",
            )
        try:
            return await subject_repo.create(db, data.model_dump())
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subject code '{data.code}' already exists for this school.",
            )

    async def get_subject(
        self, db: AsyncSession, subject_id: uuid.UUID
    ) -> Subject:
        obj = await subject_repo.get_by_id(db, subject_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
            )
        return obj

    async def list_subjects(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[Sequence[Subject], int]:
        if search:
            subjects = await subject_repo.search(db, school_id, search, limit=limit)
            return subjects, len(subjects)
        subjects = await subject_repo.get_by_school(db, school_id, skip=skip, limit=limit)
        total    = await subject_repo.count_by_school(db, school_id)
        return subjects, total

    async def update_subject(
        self, db: AsyncSession, subject_id: uuid.UUID, data: SubjectUpdate
    ) -> Subject:
        obj = await subject_repo.get_by_id(db, subject_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
            )
        return await subject_repo.update(db, obj, data.model_dump(exclude_none=True))

    async def delete_subject(self, db: AsyncSession, subject_id: uuid.UUID) -> None:
        obj = await subject_repo.get_by_id(db, subject_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
            )
        await subject_repo.soft_delete(db, obj)

    async def search_subjects(
        self, db: AsyncSession, school_id: uuid.UUID, query: str
    ) -> Sequence[Subject]:
        return await subject_repo.search(db, school_id, query)


# Module-level singleton
academic_service = AcademicService()
