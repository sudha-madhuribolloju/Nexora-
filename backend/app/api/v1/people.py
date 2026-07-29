"""
app/api/v1/people.py
──────────────────────
FastAPI router for Students, Teachers, Parents, and Parent-Student links.

Route layout
────────────
  Students →  /people/students/
  Teachers →  /people/teachers/
  Parents  →  /people/parents/
  Links    →  /people/links/

All list endpoints accept school_id as a required query parameter to keep
routes flat while enforcing multi-tenancy. This mirrors the pattern established
in academic.py.

The auth guard (get_current_user) is wired but commented for smoke-testing.
Uncomment before production.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.people import (
    ParentCreate,
    ParentResponse,
    ParentStudentLinkCreate,
    ParentStudentLinkResponse,
    ParentUpdate,
    ParentWithUser,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
    StudentWithParents,
    StudentWithUser,
    TeacherCreate,
    TeacherResponse,
    TeacherUpdate,
    TeacherWithUser,
)
from app.schemas.roles import PaginatedResponse
from app.services.people_service import people_service

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# STUDENTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/students/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a student profile",
)
async def create_student(
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db),
) -> StudentResponse:
    """
    Create a student profile for an existing User.

    - **user_id**: UUID of the User with role='student'
    - **school_id**: School the student belongs to
    - **section_id**: Optional — assign section at creation or later via PATCH
    - **admission_number**: Must be unique within the school
    - **roll_number**: Must be unique within the school
    """
    return await people_service.create_student(db, payload)


@router.get(
    "/students/",
    response_model=PaginatedResponse[StudentResponse],
    summary="List students",
)
async def list_students(
    school_id:  uuid.UUID            = Query(..., description="Filter by school"),
    section_id: Optional[uuid.UUID]  = Query(None, description="Filter by section"),
    active_only: bool                = Query(True, description="Return only active students"),
    skip:  int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[StudentResponse]:
    """
    Return paginated students for a school.
    Optionally narrow to a specific section via `section_id`.
    Pass `active_only=false` to include alumni/ex-students.
    """
    students, total = await people_service.list_students(
        db, school_id,
        section_id=section_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=students)


@router.get(
    "/students/{student_id}",
    response_model=StudentWithUser,
    summary="Get student",
)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StudentWithUser:
    """Return a student with embedded user profile."""
    return await people_service.get_student(db, student_id)


@router.get(
    "/students/{student_id}/with-parents",
    response_model=StudentWithParents,
    summary="Get student with parents",
)
async def get_student_with_parents(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StudentWithParents:
    """Return a student with all their parent links embedded."""
    return await people_service.get_student(db, student_id, with_parents=True)


@router.get(
    "/students/by-user/{user_id}",
    response_model=StudentWithUser,
    summary="Get student by user ID",
)
async def get_student_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StudentWithUser:
    """Return the student profile for a given user UUID."""
    return await people_service.get_student_by_user(db, user_id)


@router.patch(
    "/students/{student_id}",
    response_model=StudentResponse,
    summary="Update student",
)
async def update_student(
    student_id: uuid.UUID,
    payload:    StudentUpdate,
    db: AsyncSession = Depends(get_db),
) -> StudentResponse:
    """Partially update a student profile. All fields are optional."""
    return await people_service.update_student(db, student_id, payload)


@router.delete(
    "/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student",
)
async def delete_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft-delete a student profile.
    The User record and historical attendance/grade rows are preserved.
    """
    await people_service.delete_student(db, student_id)


# ══════════════════════════════════════════════════════════════════════════════
# TEACHERS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/teachers/",
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a teacher profile",
)
async def create_teacher(
    payload: TeacherCreate,
    db: AsyncSession = Depends(get_db),
) -> TeacherResponse:
    """
    Create a teacher profile for an existing User.

    - **user_id**: UUID of the User with role='teacher'
    - **school_id**: School this teacher belongs to
    - **employee_id**: Must be unique within the school
    """
    return await people_service.create_teacher(db, payload)


@router.get(
    "/teachers/",
    response_model=PaginatedResponse[TeacherResponse],
    summary="List teachers",
)
async def list_teachers(
    school_id:   uuid.UUID = Query(..., description="Filter by school"),
    active_only: bool      = Query(True, description="Return only active teachers"),
    skip:  int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TeacherResponse]:
    """Return paginated teachers for a school."""
    teachers, total = await people_service.list_teachers(
        db, school_id, active_only=active_only, skip=skip, limit=limit
    )
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=teachers)


@router.get(
    "/teachers/{teacher_id}",
    response_model=TeacherWithUser,
    summary="Get teacher",
)
async def get_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TeacherWithUser:
    """Return a teacher with embedded user profile."""
    return await people_service.get_teacher(db, teacher_id)


@router.get(
    "/teachers/by-user/{user_id}",
    response_model=TeacherWithUser,
    summary="Get teacher by user ID",
)
async def get_teacher_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TeacherWithUser:
    """Return the teacher profile for a given user UUID."""
    return await people_service.get_teacher_by_user(db, user_id)


@router.patch(
    "/teachers/{teacher_id}",
    response_model=TeacherResponse,
    summary="Update teacher",
)
async def update_teacher(
    teacher_id: uuid.UUID,
    payload:    TeacherUpdate,
    db: AsyncSession = Depends(get_db),
) -> TeacherResponse:
    """Partially update a teacher profile."""
    return await people_service.update_teacher(db, teacher_id, payload)


@router.delete(
    "/teachers/{teacher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete teacher",
)
async def delete_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft-delete a teacher profile.
    The sections.class_teacher_id FK will be SET NULL automatically.
    """
    await people_service.delete_teacher(db, teacher_id)


# ══════════════════════════════════════════════════════════════════════════════
# PARENTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/parents/",
    response_model=ParentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a parent profile",
)
async def create_parent(
    payload: ParentCreate,
    db: AsyncSession = Depends(get_db),
) -> ParentResponse:
    """
    Create a parent profile for an existing User.

    - **user_id**: UUID of the User with role='parent'
    """
    return await people_service.create_parent(db, payload)


@router.get(
    "/parents/{parent_id}",
    response_model=ParentWithUser,
    summary="Get parent",
)
async def get_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ParentWithUser:
    """Return a parent with embedded user profile."""
    return await people_service.get_parent(db, parent_id)


@router.get(
    "/parents/by-user/{user_id}",
    response_model=ParentWithUser,
    summary="Get parent by user ID",
)
async def get_parent_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ParentWithUser:
    """Return the parent profile for a given user UUID."""
    return await people_service.get_parent_by_user(db, user_id)


@router.patch(
    "/parents/{parent_id}",
    response_model=ParentResponse,
    summary="Update parent",
)
async def update_parent(
    parent_id: uuid.UUID,
    payload:   ParentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ParentResponse:
    """Partially update a parent profile."""
    return await people_service.update_parent(db, parent_id, payload)


@router.delete(
    "/parents/{parent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete parent",
)
async def delete_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a parent profile."""
    await people_service.delete_parent(db, parent_id)


@router.get(
    "/parents/{parent_id}/students",
    response_model=List[ParentStudentLinkResponse],
    summary="Get students linked to a parent",
)
async def get_students_for_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ParentStudentLinkResponse]:
    """Return all students linked to this parent."""
    return await people_service.get_students_for_parent(db, parent_id)


# ══════════════════════════════════════════════════════════════════════════════
# PARENT-STUDENT LINKS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/links/",
    response_model=ParentStudentLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link a parent to a student",
)
async def link_parent_to_student(
    payload: ParentStudentLinkCreate,
    db: AsyncSession = Depends(get_db),
) -> ParentStudentLinkResponse:
    """
    Create or update a parent ↔ student relationship.

    - **parent_id**: Existing parent profile UUID
    - **student_id**: Existing student profile UUID
    - **is_primary_contact**: Set to `true` to designate this as the primary contact.
      Only one parent per student can be primary — existing primary is automatically
      cleared if this is set to `true`.

    This operation is **idempotent** — calling it again with the same
    parent_id + student_id will update `is_primary_contact` if changed.
    """
    return await people_service.link_parent_to_student(db, payload)


@router.delete(
    "/links/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink a parent from a student",
)
async def unlink_parent_from_student(
    parent_id:  uuid.UUID = Query(...),
    student_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove the parent ↔ student link. Does not delete the parent or student."""
    await people_service.unlink_parent_from_student(db, parent_id, student_id)


@router.patch(
    "/links/primary-contact",
    response_model=ParentStudentLinkResponse,
    summary="Set primary contact for a student",
)
async def set_primary_contact(
    parent_id:  uuid.UUID = Query(...),
    student_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> ParentStudentLinkResponse:
    """
    Designate a specific parent as the primary contact for a student.
    All other parent links for the same student will be updated to
    `is_primary_contact=false`.
    """
    return await people_service.set_primary_contact(db, parent_id, student_id)


@router.get(
    "/students/{student_id}/parents",
    response_model=List[ParentStudentLinkResponse],
    summary="Get parents linked to a student",
)
async def get_parents_for_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ParentStudentLinkResponse]:
    """Return all parent links for this student."""
    return await people_service.get_parents_for_student(db, student_id)
