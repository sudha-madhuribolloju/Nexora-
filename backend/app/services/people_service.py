"""
app/services/people_service.py
────────────────────────────────
Business logic for Student, Teacher, Parent, and ParentStudentLink operations.

Design decisions:
  • PeopleService is a single class covering all three person types. The domains
    are tightly coupled (e.g. linking parents to students requires both repo
    instances). Splitting would add boilerplate without benefit at this scale.

  • Duplicate guards use repository-level lookups before attempting an insert,
    plus IntegrityError fallback for race conditions.

  • student.school_id is accepted from the client (unlike section.school_id
    which is server-resolved). This is intentional: students are registered
    directly into a school, not through a parent object.

  • link_parent_to_student() is idempotent for the link itself (returns existing
    if already linked) but will update is_primary_contact if requested.

  • set_primary_contact() atomically flips all existing links for a student
    to is_primary_contact=False, then sets the requested link to True.
    This avoids the risk of two primaries if done naively.
"""

import uuid
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.people import Parent, ParentStudentLink, Student, Teacher
from app.repositories.people_repository import (
    parent_repo,
    psl_repo,
    student_repo,
    teacher_repo,
)
from app.schemas.people import (
    ParentCreate,
    ParentStudentLinkCreate,
    ParentUpdate,
    StudentCreate,
    StudentUpdate,
    TeacherCreate,
    TeacherUpdate,
)


class PeopleService:

    # ══════════════════════════════════════════════════════════════════════════
    # STUDENTS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_student(self, db: AsyncSession, data: StudentCreate) -> Student:
        # Check if a profile already exists for this user
        existing = await student_repo.get_by_user_id(db, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student profile already exists for user {data.user_id}.",
            )
        # Check unique admission_number within school
        if data.admission_number:
            dup = await student_repo.get_by_admission_number(
                db, data.school_id, data.admission_number
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Admission number '{data.admission_number}' already used in this school.",
                )
        # Check unique roll_number within school
        if data.roll_number:
            dup = await student_repo.get_by_roll_number(
                db, data.school_id, data.roll_number
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Roll number '{data.roll_number}' already used in this school.",
                )
        try:
            return await student_repo.create(db, data.model_dump())
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student profile could not be created due to a uniqueness conflict.",
            )

    async def get_student(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        *,
        with_parents: bool = False,
    ) -> Student:
        if with_parents:
            obj = await student_repo.get_with_parents(db, student_id)
        else:
            obj = await student_repo.get_by_id_with_user(db, student_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found."
            )
        return obj

    async def get_student_by_user(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Student:
        obj = await student_repo.get_by_user_id(db, user_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No student profile found for user {user_id}.",
            )
        return obj

    async def list_students(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        section_id: Optional[uuid.UUID] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Student], int]:
        if section_id:
            students = await student_repo.get_by_section(db, section_id)
            return students, len(students)
        students = await student_repo.get_by_school(
            db, school_id, skip=skip, limit=limit, active_only=active_only
        )
        total = await student_repo.count_by_school(db, school_id, active_only=active_only)
        return students, total

    async def update_student(
        self, db: AsyncSession, student_id: uuid.UUID, data: StudentUpdate
    ) -> Student:
        obj = await student_repo.get_by_id(db, student_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found."
            )
        updates = data.model_dump(exclude_none=True)
        # Uniqueness check for roll_number if being updated
        if "roll_number" in updates and updates["roll_number"] != obj.roll_number:
            dup = await student_repo.get_by_roll_number(
                db, obj.school_id, updates["roll_number"]
            )
            if dup and dup.id != obj.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Roll number '{updates['roll_number']}' already used in this school.",
                )
        return await student_repo.update(db, obj, updates)

    async def delete_student(self, db: AsyncSession, student_id: uuid.UUID) -> None:
        obj = await student_repo.get_by_id(db, student_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found."
            )
        await student_repo.soft_delete(db, obj)

    # ══════════════════════════════════════════════════════════════════════════
    # TEACHERS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_teacher(self, db: AsyncSession, data: TeacherCreate) -> Teacher:
        # Check if profile already exists
        existing = await teacher_repo.get_by_user_id(db, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Teacher profile already exists for user {data.user_id}.",
            )
        # Check unique employee_id within school
        if data.employee_id:
            dup = await teacher_repo.get_by_employee_id(
                db, data.school_id, data.employee_id
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Employee ID '{data.employee_id}' already used in this school.",
                )
        try:
            return await teacher_repo.create(db, data.model_dump())
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Teacher profile could not be created due to a uniqueness conflict.",
            )

    async def get_teacher(
        self, db: AsyncSession, teacher_id: uuid.UUID
    ) -> Teacher:
        obj = await teacher_repo.get_by_id_with_user(db, teacher_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found."
            )
        return obj

    async def get_teacher_by_user(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Teacher:
        obj = await teacher_repo.get_by_user_id(db, user_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No teacher profile found for user {user_id}.",
            )
        return obj

    async def list_teachers(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Teacher], int]:
        teachers = await teacher_repo.get_by_school(
            db, school_id, skip=skip, limit=limit, active_only=active_only
        )
        total = await teacher_repo.count_by_school(db, school_id, active_only=active_only)
        return teachers, total

    async def update_teacher(
        self, db: AsyncSession, teacher_id: uuid.UUID, data: TeacherUpdate
    ) -> Teacher:
        obj = await teacher_repo.get_by_id(db, teacher_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found."
            )
        updates = data.model_dump(exclude_none=True)
        # Uniqueness check for employee_id if being updated
        if "employee_id" in updates and updates["employee_id"] != obj.employee_id:
            dup = await teacher_repo.get_by_employee_id(
                db, obj.school_id, updates["employee_id"]
            )
            if dup and dup.id != obj.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Employee ID '{updates['employee_id']}' already used in this school.",
                )
        return await teacher_repo.update(db, obj, updates)

    async def delete_teacher(self, db: AsyncSession, teacher_id: uuid.UUID) -> None:
        obj = await teacher_repo.get_by_id(db, teacher_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found."
            )
        await teacher_repo.soft_delete(db, obj)

    # ══════════════════════════════════════════════════════════════════════════
    # PARENTS
    # ══════════════════════════════════════════════════════════════════════════

    async def create_parent(self, db: AsyncSession, data: ParentCreate) -> Parent:
        existing = await parent_repo.get_by_user_id(db, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Parent profile already exists for user {data.user_id}.",
            )
        try:
            return await parent_repo.create(db, data.model_dump())
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Parent profile could not be created due to a uniqueness conflict.",
            )

    async def get_parent(self, db: AsyncSession, parent_id: uuid.UUID) -> Parent:
        obj = await parent_repo.get_by_id_with_user(db, parent_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found."
            )
        return obj

    async def get_parent_by_user(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Parent:
        obj = await parent_repo.get_by_user_id(db, user_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No parent profile found for user {user_id}.",
            )
        return obj

    async def update_parent(
        self, db: AsyncSession, parent_id: uuid.UUID, data: ParentUpdate
    ) -> Parent:
        obj = await parent_repo.get_by_id(db, parent_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found."
            )
        return await parent_repo.update(db, obj, data.model_dump(exclude_none=True))

    async def delete_parent(self, db: AsyncSession, parent_id: uuid.UUID) -> None:
        obj = await parent_repo.get_by_id(db, parent_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found."
            )
        await parent_repo.soft_delete(db, obj)

    # ══════════════════════════════════════════════════════════════════════════
    # PARENT-STUDENT LINKS
    # ══════════════════════════════════════════════════════════════════════════

    async def link_parent_to_student(
        self, db: AsyncSession, data: ParentStudentLinkCreate
    ) -> ParentStudentLink:
        # Verify both exist
        student = await student_repo.get_by_id(db, data.student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {data.student_id} not found.",
            )
        parent = await parent_repo.get_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent {data.parent_id} not found.",
            )
        # Idempotent: return existing link if already present
        existing = await psl_repo.get_link(db, data.parent_id, data.student_id)
        if existing:
            # Update primary contact flag if changed
            if existing.is_primary_contact != data.is_primary_contact:
                return await psl_repo.update(
                    db, existing, {"is_primary_contact": data.is_primary_contact}
                )
            return existing
        # If setting as primary, clear other primary links for this student first
        if data.is_primary_contact:
            await self._clear_primary_contacts(db, data.student_id)
        try:
            return await psl_repo.create(db, data.model_dump())
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Parent-student link already exists.",
            )

    async def unlink_parent_from_student(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> None:
        link = await psl_repo.get_link(db, parent_id, student_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent-student link not found.",
            )
        await psl_repo.hard_delete(db, link)

    async def set_primary_contact(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> ParentStudentLink:
        """Atomically set one parent as primary contact for a student."""
        link = await psl_repo.get_link(db, parent_id, student_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent-student link not found. Link the parent first.",
            )
        await self._clear_primary_contacts(db, student_id)
        return await psl_repo.update(db, link, {"is_primary_contact": True})

    async def _clear_primary_contacts(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> None:
        """Set is_primary_contact=False for all parent links of a student."""
        links = await parent_repo.get_parents_for_student(db, student_id)
        for link in links:
            if link.is_primary_contact:
                await psl_repo.update(db, link, {"is_primary_contact": False})

    async def get_parents_for_student(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> Sequence[ParentStudentLink]:
        # Verify student exists
        await self.get_student(db, student_id)
        return await parent_repo.get_parents_for_student(db, student_id)

    async def get_students_for_parent(
        self, db: AsyncSession, parent_id: uuid.UUID
    ) -> Sequence[ParentStudentLink]:
        # Verify parent exists
        await self.get_parent(db, parent_id)
        return await psl_repo.get_students_for_parent(db, parent_id)


# Module-level singleton
people_service = PeopleService()
