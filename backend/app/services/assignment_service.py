"""
Assignment service — CRUD, submission, and grading.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.assignment import Assignment, AssignmentSubmission, AssignmentStatus, SubmissionStatus
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionGrade


class AssignmentService:

    @staticmethod
    async def list_assignments(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        course_id: Optional[uuid.UUID] = None,
    ) -> Tuple[int, List[Assignment]]:
        q = select(Assignment)
        if course_id:
            q = q.where(Assignment.course_id == course_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        assignments = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(assignments)

    @staticmethod
    async def get_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
        result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        return assignment

    @staticmethod
    async def create_assignment(
        db: AsyncSession, data: AssignmentCreate, teacher_id: Optional[uuid.UUID] = None
    ) -> Assignment:
        assignment = Assignment(**data.model_dump(), created_by=teacher_id)
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def update_assignment(
        db: AsyncSession, assignment_id: uuid.UUID, data: AssignmentUpdate
    ) -> Assignment:
        assignment = await AssignmentService.get_assignment(db, assignment_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(assignment, field, value)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def delete_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> None:
        assignment = await AssignmentService.get_assignment(db, assignment_id)
        await db.delete(assignment)
        await db.commit()

    @staticmethod
    async def submit_assignment(
        db: AsyncSession,
        assignment_id: uuid.UUID,
        student_id: uuid.UUID,
        data: SubmissionCreate,
    ) -> AssignmentSubmission:
        assignment = await AssignmentService.get_assignment(db, assignment_id)
        if assignment.status != AssignmentStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignment is not open for submission")
        # Check for duplicate submission
        existing = (await db.execute(
            select(AssignmentSubmission).where(
                and_(
                    AssignmentSubmission.assignment_id == assignment_id,
                    AssignmentSubmission.student_id == student_id
                )
            )
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment already submitted")
        now = datetime.now(timezone.utc)
        if assignment.due_date:
            due = assignment.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            is_late = now > due
        else:
            is_late = False
        sub_status = SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            status=sub_status,
            **data.model_dump()
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def list_submissions(
        db: AsyncSession, assignment_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> Tuple[int, List[AssignmentSubmission]]:
        q = select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        submissions = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(submissions)

    @staticmethod
    async def grade_submission(
        db: AsyncSession,
        assignment_id: uuid.UUID,
        submission_id: uuid.UUID,
        data: SubmissionGrade,
        graded_by: uuid.UUID,
    ) -> AssignmentSubmission:
        result = await db.execute(
            select(AssignmentSubmission).where(
                and_(
                    AssignmentSubmission.id == submission_id,
                    AssignmentSubmission.assignment_id == assignment_id
                )
            )
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        submission.score = data.score
        submission.feedback = data.feedback
        submission.status = SubmissionStatus.GRADED
        submission.graded_at = datetime.now(timezone.utc)
        submission.graded_by = graded_by
        await db.commit()
        await db.refresh(submission)
        return submission
