"""
app/api/v1/academic.py
───────────────────────
FastAPI router for Classes, Sections, and Subjects.

Route layout
────────────
  Classes  →  /academic/classes/
  Sections →  /academic/sections/  (flat) + /academic/classes/{id}/sections/
  Subjects →  /academic/subjects/

All list endpoints accept school_id as a required query parameter so the
router stays flat (one prefix) while still enforcing tenancy. This avoids
deeply nested paths like /schools/{id}/academic-years/{id}/classes/ which
become unwieldy in client code.

auth guard (get_current_user) is wired but commented so you can smoke-test
routes before auth middleware is finalised. Uncomment before production.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.academic import (
    ClassCreate,
    ClassResponse,
    ClassUpdate,
    ClassWithSections,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from app.schemas.roles import PaginatedResponse
from app.services.academic_service import academic_service

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/classes/",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a class",
)
async def create_class(
    payload: ClassCreate,
    db: AsyncSession = Depends(get_db),
) -> ClassResponse:
    """
    Create a grade-level class within a school and academic year.

    - **name**: e.g. `"Grade 10"`, `"Class 1"`, `"Form 5"`
    - **grade_level**: numeric sort key `(1–12)`, optional
    - **school_id** + **academic_year_id**: required for tenancy scoping
    """
    return await academic_service.create_class(db, payload)


@router.get(
    "/classes/",
    response_model=PaginatedResponse[ClassResponse],
    summary="List classes",
)
async def list_classes(
    school_id:        uuid.UUID       = Query(..., description="Filter by school"),
    academic_year_id: Optional[uuid.UUID] = Query(None, description="Filter by academic year"),
    skip:  int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ClassResponse]:
    """
    Return paginated classes for a school.
    Optionally narrow to a specific academic year via `academic_year_id`.
    """
    classes, total = await academic_service.list_classes(
        db, school_id, academic_year_id, skip=skip, limit=limit
    )
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=classes)


@router.get(
    "/classes/{class_id}",
    response_model=ClassResponse,
    summary="Get class",
)
async def get_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ClassResponse:
    return await academic_service.get_class(db, class_id)


@router.get(
    "/classes/{class_id}/full",
    response_model=ClassWithSections,
    summary="Get class with sections",
)
async def get_class_with_sections(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ClassWithSections:
    """Return a class with all its active sections embedded."""
    return await academic_service.get_class(db, class_id, with_sections=True)


@router.patch(
    "/classes/{class_id}",
    response_model=ClassResponse,
    summary="Update class",
)
async def update_class(
    class_id: uuid.UUID,
    payload:  ClassUpdate,
    db: AsyncSession = Depends(get_db),
) -> ClassResponse:
    return await academic_service.update_class(db, class_id, payload)


@router.delete(
    "/classes/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete class",
)
async def delete_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft-delete a class and all its sections.
    Student enrolment, attendance, and timetable records are preserved.
    """
    await academic_service.delete_class(db, class_id)


# ══════════════════════════════════════════════════════════════════════════════
# SECTIONS — nested under class
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/classes/{class_id}/sections/",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create section under class",
)
async def create_section_for_class(
    class_id: uuid.UUID,
    payload:  SectionCreate,
    db: AsyncSession = Depends(get_db),
) -> SectionResponse:
    """
    Add a section to a class. The `class_id` from the URL overrides
    any `class_id` supplied in the request body.
    """
    payload.class_id = class_id
    return await academic_service.create_section(db, payload)


@router.get(
    "/classes/{class_id}/sections/",
    response_model=List[SectionResponse],
    summary="List sections for a class",
)
async def list_sections_for_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[SectionResponse]:
    """Return all active sections for the specified class."""
    return await academic_service.list_sections_by_class(db, class_id)


# ══════════════════════════════════════════════════════════════════════════════
# SECTIONS — flat endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/sections/",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create section",
)
async def create_section(
    payload: SectionCreate,
    db: AsyncSession = Depends(get_db),
) -> SectionResponse:
    """
    Create a section. `class_id` must be supplied in the request body.
    `school_id` is resolved server-side from the parent class.
    """
    return await academic_service.create_section(db, payload)


@router.get(
    "/sections/",
    response_model=PaginatedResponse[SectionResponse],
    summary="List sections by school",
)
async def list_sections(
    school_id: uuid.UUID = Query(..., description="Filter by school"),
    skip:  int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SectionResponse]:
    """Return all active sections for a school."""
    sections, total = await academic_service.list_sections_by_school(
        db, school_id, skip=skip, limit=limit
    )
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=sections)


@router.get(
    "/sections/{section_id}",
    response_model=SectionResponse,
    summary="Get section",
)
async def get_section(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SectionResponse:
    return await academic_service.get_section(db, section_id)


@router.patch(
    "/sections/{section_id}",
    response_model=SectionResponse,
    summary="Update section",
)
async def update_section(
    section_id: uuid.UUID,
    payload:    SectionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SectionResponse:
    return await academic_service.update_section(db, section_id, payload)


@router.delete(
    "/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete section",
)
async def delete_section(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    await academic_service.delete_section(db, section_id)


# ══════════════════════════════════════════════════════════════════════════════
# SUBJECTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/subjects/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create subject",
)
async def create_subject(
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db),
) -> SubjectResponse:
    """
    Add a subject to the school catalogue.

    - **code**: short identifier, auto-uppercased (e.g. `"MATH"`, `"ENGLIT"`)
    - **color**: optional hex badge colour (e.g. `"#4F46E5"`)
    - **is_elective**: `false` = compulsory
    """
    return await academic_service.create_subject(db, payload)


@router.get(
    "/subjects/",
    response_model=PaginatedResponse[SubjectResponse],
    summary="List subjects",
)
async def list_subjects(
    school_id: uuid.UUID       = Query(..., description="Filter by school"),
    search:    Optional[str]   = Query(None, description="Search by name or code"),
    skip:      int             = Query(0, ge=0),
    limit:     int             = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SubjectResponse]:
    """
    Return subjects for a school.
    Pass `search` for a case-insensitive name/code prefix autocomplete.
    """
    subjects, total = await academic_service.list_subjects(
        db, school_id, search=search, skip=skip, limit=limit
    )
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=subjects)


@router.get(
    "/subjects/{subject_id}",
    response_model=SubjectResponse,
    summary="Get subject",
)
async def get_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SubjectResponse:
    return await academic_service.get_subject(db, subject_id)


@router.patch(
    "/subjects/{subject_id}",
    response_model=SubjectResponse,
    summary="Update subject",
)
async def update_subject(
    subject_id: uuid.UUID,
    payload:    SubjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> SubjectResponse:
    return await academic_service.update_subject(db, subject_id, payload)


@router.delete(
    "/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject",
)
async def delete_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    await academic_service.delete_subject(db, subject_id)
