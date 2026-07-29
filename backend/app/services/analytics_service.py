"""
Analytics service — aggregated statistics across the system.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.course import Course, CourseEnrollment
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.session import ClassSession as Session, SessionStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.quiz import Quiz, QuizAttempt
from app.schemas.analytics import (
    OverviewStats,
    AttendanceAnalytics,
    PerformanceAnalytics,
    CourseAnalytics,
    TeacherAnalytics,
)
from typing import List


class AnalyticsService:

    @staticmethod
    async def get_overview(db: AsyncSession) -> OverviewStats:
        total_students = (await db.execute(select(func.count(Student.id)))).scalar_one()
        total_teachers = (await db.execute(select(func.count(Teacher.id)))).scalar_one()
        total_courses = (await db.execute(select(func.count(Course.id)))).scalar_one()
        active_courses = (await db.execute(select(func.count(Course.id)).where(Course.is_active == True))).scalar_one()
        total_sessions = (await db.execute(select(func.count(Session.id)))).scalar_one()
        pending_assignments = (await db.execute(
            select(func.count(Assignment.id)).where(Assignment.status == "published")
        )).scalar_one()
        return OverviewStats(
            total_students=total_students,
            total_teachers=total_teachers,
            total_courses=total_courses,
            total_sessions=total_sessions,
            active_courses=active_courses,
            pending_assignments=pending_assignments,
        )

    @staticmethod
    async def get_attendance_analytics(db: AsyncSession) -> AttendanceAnalytics:
        rows = (await db.execute(
            select(Attendance.status, func.count(Attendance.id)).group_by(Attendance.status)
        )).all()
        counts = {r[0]: r[1] for r in rows}
        present = counts.get(AttendanceStatus.PRESENT, 0)
        absent = counts.get(AttendanceStatus.ABSENT, 0)
        late = counts.get(AttendanceStatus.LATE, 0)
        excused = counts.get(AttendanceStatus.EXCUSED, 0)
        total = present + absent + late + excused
        return AttendanceAnalytics(
            overall_attendance_rate=round(present / total * 100, 2) if total else 0.0,
            present_count=present,
            absent_count=absent,
            late_count=late,
            excused_count=excused,
        )

    @staticmethod
    async def get_performance_analytics(db: AsyncSession) -> PerformanceAnalytics:
        avg_assignment = (await db.execute(
            select(func.avg(AssignmentSubmission.score)).where(AssignmentSubmission.score.is_not(None))
        )).scalar_one()
        avg_quiz = (await db.execute(
            select(func.avg(QuizAttempt.score)).where(QuizAttempt.score.is_not(None))
        )).scalar_one()
        total_students = (await db.execute(select(func.count(Student.id)))).scalar_one()
        submitted = (await db.execute(
            select(func.count(AssignmentSubmission.student_id.distinct()))
        )).scalar_one()
        quiz_students = (await db.execute(
            select(func.count(QuizAttempt.student_id.distinct()))
        )).scalar_one()
        return PerformanceAnalytics(
            average_assignment_score=round(avg_assignment, 2) if avg_assignment else None,
            average_quiz_score=round(avg_quiz, 2) if avg_quiz else None,
            assignment_submission_rate=round(submitted / total_students * 100, 2) if total_students else 0.0,
            quiz_completion_rate=round(quiz_students / total_students * 100, 2) if total_students else 0.0,
        )

    @staticmethod
    async def get_course_analytics(db: AsyncSession) -> List[CourseAnalytics]:
        courses = (await db.execute(select(Course))).scalars().all()
        result = []
        for course in courses:
            enrolled = (await db.execute(
                select(func.count(CourseEnrollment.id)).where(
                    and_(CourseEnrollment.course_id == course.id, CourseEnrollment.is_active == True)
                )
            )).scalar_one()
            total_sess = (await db.execute(
                select(func.count(Session.id)).where(Session.course_id == course.id)
            )).scalar_one()
            completed_sess = (await db.execute(
                select(func.count(Session.id)).where(
                    and_(Session.course_id == course.id, Session.status == SessionStatus.COMPLETED)
                )
            )).scalar_one()
            # Attendance for this course's sessions
            att_rows = (await db.execute(
                select(Attendance.status, func.count(Attendance.id))
                .join(Session, Attendance.session_id == Session.id)
                .where(Session.course_id == course.id)
                .group_by(Attendance.status)
            )).all()
            att_counts = {r[0]: r[1] for r in att_rows}
            present = att_counts.get(AttendanceStatus.PRESENT, 0)
            total_att = sum(att_counts.values())
            result.append(CourseAnalytics(
                course_id=str(course.id),
                title=course.title,
                enrolled_students=enrolled,
                completed_sessions=completed_sess,
                total_sessions=total_sess,
                average_attendance=round(present / total_att * 100, 2) if total_att else 0.0,
            ))
        return result

    @staticmethod
    async def get_teacher_analytics(db: AsyncSession) -> List[TeacherAnalytics]:
        from app.models.user import User
        teachers = (await db.execute(select(Teacher))).scalars().all()
        result = []
        for teacher in teachers:
            user = (await db.execute(select(User).where(User.id == teacher.user_id))).scalar_one_or_none()
            total_courses = (await db.execute(
                select(func.count(Course.id)).where(Course.teacher_id == teacher.id)
            )).scalar_one()
            total_sessions = (await db.execute(
                select(func.count(Session.id)).where(
                    and_(Session.teacher_id == teacher.id, Session.status == SessionStatus.COMPLETED)
                )
            )).scalar_one()
            result.append(TeacherAnalytics(
                teacher_id=str(teacher.id),
                full_name=user.full_name if user else "Unknown",
                total_courses=total_courses,
                total_sessions_conducted=total_sessions,
            ))
        return result
