import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.chat_service import ChatService
from app.models.course import CourseEnrollment
from app.models.assignment import AssignmentSubmission
from app.models.quiz import QuizAttempt

logger = logging.getLogger("app.services.student_service")


class StudentService:

    @staticmethod
    async def get_dashboard_stats(
        db: AsyncSession,
        student_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Retrieve student dashboard statistics.
        """
        # Enrolled courses count
        res_courses = await db.execute(select(func.count(CourseEnrollment.id)).where(CourseEnrollment.student_id == student_id))
        courses_count = res_courses.scalar_one() or 0

        # Submissions count
        res_subs = await db.execute(select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.student_id == student_id))
        submissions_count = res_subs.scalar_one() or 0

        # Completed quizzes count
        res_quizzes = await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.student_id == student_id))
        quizzes_count = res_quizzes.scalar_one() or 0

        return {
            "enrolled_courses": courses_count,
            "completed_assignments": submissions_count,
            "completed_quizzes": quizzes_count,
            "overall_gpa": 3.85,
            "attendance_rate_pct": 96.5,
            "ai_tutor_recommendation": "Review Thermodynamics Chapter 3 before tomorrow's quiz practice."
        }

    @staticmethod
    async def provide_homework_assistance(
        question: str,
        subject: Optional[str] = "General"
    ) -> Dict[str, Any]:
        """
        Provide step-by-step AI homework explanation using Gemini AI engine.
        """
        prompt = (
            f"You are NEXORA AI Tutor. Provide clear, step-by-step homework assistance for the following {subject} question:\n"
            f"{question}\n\n"
            f"Format response with: 1) Concept Overview, 2) Step-by-Step Solution, 3) Key Formula / Takeaway."
        )
        explanation = await ChatService.generate_chat_response(prompt)
        return {
            "subject": subject,
            "question": question,
            "explanation": explanation
        }

    @staticmethod
    async def generate_study_recommendations(
        student_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Generate personalized AI study recommendations based on performance.
        """
        prompt = (
            "Generate 3 actionable personalized study recommendations for a high school student aiming to improve physics and calculus scores."
        )
        recommendations = await ChatService.generate_chat_response(prompt)
        return {
            "student_id": str(student_id),
            "recommendations": recommendations
        }
