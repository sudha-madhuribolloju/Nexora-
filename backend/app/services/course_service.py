"""
Course service — all database CRUD operations for courses and enrollment.
"""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.course import Course, CourseEnrollment
from app.models.student import Student
from app.schemas.course import CourseCreate, CourseUpdate, EnrollmentCreate


class CourseService:

    @staticmethod
    async def list_courses(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        teacher_id: Optional[uuid.UUID] = None,
    ) -> Tuple[int, List[Course]]:
        q = select(Course)
        if is_active is not None:
            q = q.where(Course.is_active == is_active)
        if teacher_id:
            q = q.where(Course.teacher_id == teacher_id)
        count_q = select(func.count()).select_from(q.subquery())
        total = (await db.execute(count_q)).scalar_one()
        courses = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(courses)

    @staticmethod
    async def get_course(db: AsyncSession, course_id: uuid.UUID) -> Course:
        result = await db.execute(select(Course).where(Course.id == course_id))
        course = result.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    @staticmethod
    async def create_course(db: AsyncSession, data: CourseCreate) -> Course:
        course = Course(**data.model_dump())
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    @staticmethod
    async def update_course(db: AsyncSession, course_id: uuid.UUID, data: CourseUpdate) -> Course:
        course = await CourseService.get_course(db, course_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(course, field, value)
        await db.commit()
        await db.refresh(course)
        return course

    @staticmethod
    async def delete_course(db: AsyncSession, course_id: uuid.UUID) -> None:
        course = await CourseService.get_course(db, course_id)
        await db.delete(course)
        await db.commit()

    @staticmethod
    async def enroll_student(db: AsyncSession, course_id: uuid.UUID, data: EnrollmentCreate) -> CourseEnrollment:
        # Verify course exists
        await CourseService.get_course(db, course_id)
        # Verify student exists
        student = (await db.execute(select(Student).where(Student.id == data.student_id))).scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        # Check not already enrolled
        existing = (await db.execute(
            select(CourseEnrollment).where(
                and_(CourseEnrollment.course_id == course_id, CourseEnrollment.student_id == data.student_id)
            )
        )).scalar_one_or_none()
        if existing:
            if existing.is_active:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already enrolled")
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
            return existing
        enrollment = CourseEnrollment(course_id=course_id, student_id=data.student_id)
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    @staticmethod
    async def unenroll_student(db: AsyncSession, course_id: uuid.UUID, student_id: uuid.UUID) -> None:
        enrollment = (await db.execute(
            select(CourseEnrollment).where(
                and_(CourseEnrollment.course_id == course_id, CourseEnrollment.student_id == student_id)
            )
        )).scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
        enrollment.is_active = False
        await db.commit()

    @staticmethod
    async def get_enrolled_students(db: AsyncSession, course_id: uuid.UUID) -> List[CourseEnrollment]:
        result = await db.execute(
            select(CourseEnrollment).where(
                and_(CourseEnrollment.course_id == course_id, CourseEnrollment.is_active == True)
            )
        )
        return list(result.scalars().all())
