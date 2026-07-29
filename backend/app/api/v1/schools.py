"""
app/api/v1/schools.py
──────────────────────
FastAPI router for Schools and AcademicYears.

Route design:
  • Schools are top-level resources: POST /schools/, GET /schools/, etc.
  • Academic years are nested under their school: 
      POST /schools/{school_id}/academic-years/
      GET  /schools/{school_id}/academic-years/
      POST /schools/{school_id}/academic-years/{year_id}/set-current
  • GET /schools/{school_id} returns school WITHOUT years (fast).
  • GET /schools/{school_id}/full returns school WITH years embedded.
  • All list endpoints return PaginatedResponse envelopes.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.roles import PaginatedResponse
from app.schemas.school import (
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
    SchoolCreate,
    SchoolResponse,
    SchoolSummary,
    SchoolUpdate,
    SchoolWithAcademicYears,
)
from app.services.school_service import school_service

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# SCHOOLS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/",
    response_model=SchoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a school",
)
async def create_school(
    payload: SchoolCreate,
    db: AsyncSession = Depends(get_db),
) -> SchoolResponse:
    """
    Register a new school. The `code` field becomes the tenant identifier
    and must be globally unique (e.g. `"GHS001"`).
    School codes are stored and matched in UPPER case.
    """
    return await school_service.create_school(db, payload)


@router.get(
    "/",
    response_model=PaginatedResponse[SchoolSummary],
    summary="List active schools",
)
async def list_schools(
    skip:  int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[SchoolSummary]:
    """Return paginated list of all active (non-deleted, non-suspended) schools."""
    schools, total = await school_service.list_schools(db, skip=skip, limit=limit)
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=schools)


@router.get(
    "/code/{code}",
    response_model=SchoolResponse,
    summary="Get school by code",
)
async def get_school_by_code(
    code: str,
    db:   AsyncSession = Depends(get_db),
) -> SchoolResponse:
    """Fetch a school by its unique code (case-insensitive)."""
    return await school_service.get_school_by_code(db, code)


@router.get(
    "/{school_id}",
    response_model=SchoolResponse,
    summary="Get school detail",
)
async def get_school(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SchoolResponse:
    """Fetch a single school without its academic years."""
    return await school_service.get_school(db, school_id)


@router.get(
    "/{school_id}/full",
    response_model=SchoolWithAcademicYears,
    summary="Get school with academic years",
)
async def get_school_full(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SchoolWithAcademicYears:
    """Fetch school detail including all academic years (nested)."""
    return await school_service.get_school(db, school_id, with_years=True)


@router.patch(
    "/{school_id}",
    response_model=SchoolResponse,
    summary="Update school",
)
async def update_school(
    school_id: uuid.UUID,
    payload:   SchoolUpdate,
    db: AsyncSession = Depends(get_db),
) -> SchoolResponse:
    """Partially update school fields. Only supplied fields are changed."""
    return await school_service.update_school(db, school_id, payload)


@router.delete(
    "/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a school",
)
async def delete_school(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft-delete a school. The school record is retained for audit purposes.
    Associated users retain their accounts; school_id is SET NULL by the FK.
    """
    await school_service.delete_school(db, school_id)


# ══════════════════════════════════════════════════════════════════════════════
# ACADEMIC YEARS  (nested under /{school_id}/academic-years)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{school_id}/academic-years/",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create academic year",
)
async def create_academic_year(
    school_id: uuid.UUID,
    payload:   AcademicYearCreate,
    db: AsyncSession = Depends(get_db),
) -> AcademicYearResponse:
    """
    Add an academic year to a school.
    Set `is_current: true` to immediately mark it as the active year
    (this demotes any previously current year).
    """
    return await school_service.create_academic_year(db, school_id, payload)


@router.get(
    "/{school_id}/academic-years/",
    response_model=List[AcademicYearResponse],
    summary="List academic years",
)
async def list_academic_years(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[AcademicYearResponse]:
    """Return all academic years for a school, newest first."""
    return await school_service.list_academic_years(db, school_id)


@router.get(
    "/{school_id}/academic-years/current",
    response_model=Optional[AcademicYearResponse],
    summary="Get current academic year",
)
async def get_current_academic_year(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Optional[AcademicYearResponse]:
    """Return the academic year currently marked as active, or null."""
    return await school_service.get_current_academic_year(db, school_id)


@router.get(
    "/{school_id}/academic-years/{year_id}",
    response_model=AcademicYearResponse,
    summary="Get academic year detail",
)
async def get_academic_year(
    school_id: uuid.UUID,
    year_id:   uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AcademicYearResponse:
    return await school_service.get_academic_year(db, school_id, year_id)


@router.patch(
    "/{school_id}/academic-years/{year_id}",
    response_model=AcademicYearResponse,
    summary="Update academic year",
)
async def update_academic_year(
    school_id: uuid.UUID,
    year_id:   uuid.UUID,
    payload:   AcademicYearUpdate,
    db: AsyncSession = Depends(get_db),
) -> AcademicYearResponse:
    return await school_service.update_academic_year(db, school_id, year_id, payload)


@router.post(
    "/{school_id}/academic-years/{year_id}/set-current",
    response_model=AcademicYearResponse,
    summary="Set current academic year",
)
async def set_current_academic_year(
    school_id: uuid.UUID,
    year_id:   uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AcademicYearResponse:
    """
    Atomically promote year_id to is_current=True and demote all other
    academic years for this school to is_current=False.
    """
    return await school_service.set_current_academic_year(db, school_id, year_id)
