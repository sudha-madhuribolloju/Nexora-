"""
app/repositories/people_repository.py
───────────────────────────────────────
Async repositories for Student, Teacher, Parent, and ParentStudentLink.

Design decisions:
  • StudentRepository.get_by_school() is the primary listing query scoped by
    school_id (using the denormalised column) for fast tenant-scoped access.
  • StudentRepository.get_by_section() supports the attendance module which
    needs all students in a specific section.
  • TeacherRepository.get_by_school() returns active teachers for a school.
  • TeacherRepository.get_class_teachers() returns only is_class_teacher=True
    rows — used by the section/timetable modules.
  • ParentStudentLinkRepository handles the M2M join table: get_parents_for_student
    and get_students_for_parent are the two primary access patterns.
  • All list queries use selectinload for user relationship to avoid N+1 on
    list endpoints.
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.people import Parent, ParentStudentLink, Student, Teacher
from app.repositories.base_repository import BaseRepository


# ── StudentRepository ──────────────────────────────────────────────────────────

class StudentRepository(BaseRepository[Student]):

    def __init__(self) -> None:
        super().__init__(Student)

    async def get_by_id_with_user(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> Optional[Student]:
        """Return the student profile by ID with user eagerly loaded."""
        result = await db.execute(
            select(Student)
            .where(Student.id == student_id, Student.is_deleted == False)  # noqa: E712
            .options(selectinload(Student.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Optional[Student]:
        """Return the student profile for a given user."""
        result = await db.execute(
            select(Student)
            .where(Student.user_id == user_id, Student.is_deleted == False)  # noqa: E712
            .options(selectinload(Student.user))
        )
        return result.scalar_one_or_none()

    async def get_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> Sequence[Student]:
        """Return students for a school, optionally filtering by is_active."""
        stmt = (
            select(Student)
            .where(Student.school_id == school_id, Student.is_deleted == False)  # noqa: E712
            .options(selectinload(Student.user))
            .offset(skip)
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(Student.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> int:
        stmt = select(func.count()).select_from(Student).where(
            Student.school_id == school_id, Student.is_deleted == False  # noqa: E712
        )
        if active_only:
            stmt = stmt.where(Student.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_by_section(
        self, db: AsyncSession, section_id: uuid.UUID
    ) -> Sequence[Student]:
        """Return all active students enrolled in a specific section."""
        result = await db.execute(
            select(Student)
            .where(
                Student.section_id == section_id,
                Student.is_deleted == False,  # noqa: E712
                Student.is_active == True,    # noqa: E712
            )
            .options(selectinload(Student.user))
        )
        return result.scalars().all()

    async def get_by_admission_number(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        admission_number: str,
    ) -> Optional[Student]:
        result = await db.execute(
            select(Student).where(
                Student.school_id == school_id,
                Student.admission_number == admission_number,
                Student.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_roll_number(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        roll_number: str,
    ) -> Optional[Student]:
        result = await db.execute(
            select(Student).where(
                Student.school_id == school_id,
                Student.roll_number == roll_number,
                Student.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_with_parents(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> Optional[Student]:
        """Return student with parent_links eagerly loaded."""
        result = await db.execute(
            select(Student)
            .where(Student.id == student_id, Student.is_deleted == False)  # noqa: E712
            .options(
                selectinload(Student.user),
                selectinload(Student.parent_links).selectinload(ParentStudentLink.parent),
            )
        )
        return result.scalar_one_or_none()


# ── TeacherRepository ──────────────────────────────────────────────────────────

class TeacherRepository(BaseRepository[Teacher]):

    def __init__(self) -> None:
        super().__init__(Teacher)

    async def get_by_id_with_user(
        self, db: AsyncSession, teacher_id: uuid.UUID
    ) -> Optional[Teacher]:
        """Return the teacher profile by ID with user eagerly loaded."""
        result = await db.execute(
            select(Teacher)
            .where(Teacher.id == teacher_id, Teacher.is_deleted == False)  # noqa: E712
            .options(selectinload(Teacher.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Optional[Teacher]:
        """Return the teacher profile for a given user."""
        result = await db.execute(
            select(Teacher)
            .where(Teacher.user_id == user_id, Teacher.is_deleted == False)  # noqa: E712
            .options(selectinload(Teacher.user))
        )
        return result.scalar_one_or_none()

    async def get_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> Sequence[Teacher]:
        """Return teachers for a school."""
        stmt = (
            select(Teacher)
            .where(Teacher.school_id == school_id, Teacher.is_deleted == False)  # noqa: E712
            .options(selectinload(Teacher.user))
            .offset(skip)
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(Teacher.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_by_school(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> int:
        stmt = select(func.count()).select_from(Teacher).where(
            Teacher.school_id == school_id, Teacher.is_deleted == False  # noqa: E712
        )
        if active_only:
            stmt = stmt.where(Teacher.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_class_teachers(
        self, db: AsyncSession, school_id: uuid.UUID
    ) -> Sequence[Teacher]:
        """Return teachers currently assigned as class/homeroom teachers."""
        result = await db.execute(
            select(Teacher)
            .where(
                Teacher.school_id == school_id,
                Teacher.is_class_teacher == True,  # noqa: E712
                Teacher.is_deleted == False,        # noqa: E712
                Teacher.is_active == True,          # noqa: E712
            )
            .options(selectinload(Teacher.user))
        )
        return result.scalars().all()

    async def get_by_employee_id(
        self,
        db: AsyncSession,
        school_id: uuid.UUID,
        employee_id: str,
    ) -> Optional[Teacher]:
        result = await db.execute(
            select(Teacher).where(
                Teacher.school_id == school_id,
                Teacher.employee_id == employee_id,
                Teacher.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()


# ── ParentRepository ───────────────────────────────────────────────────────────

class ParentRepository(BaseRepository[Parent]):

    def __init__(self) -> None:
        super().__init__(Parent)

    async def get_by_id_with_user(
        self, db: AsyncSession, parent_id: uuid.UUID
    ) -> Optional[Parent]:
        """Return the parent profile by ID with user eagerly loaded."""
        result = await db.execute(
            select(Parent)
            .where(Parent.id == parent_id, Parent.is_deleted == False)  # noqa: E712
            .options(selectinload(Parent.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Optional[Parent]:
        """Return the parent profile for a given user."""
        result = await db.execute(
            select(Parent)
            .where(Parent.user_id == user_id, Parent.is_deleted == False)  # noqa: E712
            .options(selectinload(Parent.user))
        )
        return result.scalar_one_or_none()

    async def get_parents_for_student(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> Sequence[ParentStudentLink]:
        """Return all parent links for a student, with parent eagerly loaded."""
        result = await db.execute(
            select(ParentStudentLink)
            .where(ParentStudentLink.student_id == student_id)
            .options(
                selectinload(ParentStudentLink.parent).selectinload(Parent.user)
            )
        )
        return result.scalars().all()


# ── ParentStudentLinkRepository ───────────────────────────────────────────────

class ParentStudentLinkRepository(BaseRepository[ParentStudentLink]):

    def __init__(self) -> None:
        super().__init__(ParentStudentLink)

    async def get_link(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> Optional[ParentStudentLink]:
        """Return an existing link between a parent and a student."""
        result = await db.execute(
            select(ParentStudentLink).where(
                ParentStudentLink.parent_id  == parent_id,
                ParentStudentLink.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_students_for_parent(
        self, db: AsyncSession, parent_id: uuid.UUID
    ) -> Sequence[ParentStudentLink]:
        """Return all student links for a parent, with student eagerly loaded."""
        result = await db.execute(
            select(ParentStudentLink)
            .where(ParentStudentLink.parent_id == parent_id)
            .options(
                selectinload(ParentStudentLink.student).selectinload(Student.user)
            )
        )
        return result.scalars().all()


# ── Module-level singletons ────────────────────────────────────────────────────
student_repo = StudentRepository()
teacher_repo = TeacherRepository()
parent_repo  = ParentRepository()
psl_repo     = ParentStudentLinkRepository()
