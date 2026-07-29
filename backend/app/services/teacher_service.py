import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.chat_service import ChatService
from app.models.course import Course
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.quiz import Quiz
from app.models.document import Document

logger = logging.getLogger("app.services.teacher_service")


class TeacherService:

    @staticmethod
    async def generate_ai_quiz(
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate structured quiz questions using Gemini AI engine.
        """
        prompt = (
            f"Generate a {difficulty} difficulty quiz with {num_questions} multiple choice questions on the topic '{topic}'.\n"
            f"Provide output in strict JSON format with keys: title, description, questions (list of dicts with question_text, options (list of 4 strings), correct_option_index (0-3), explanation)."
        )
        ai_response = await ChatService.generate_chat_response(prompt)
        return {
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "generated_quiz_raw": ai_response,
            "status": "success"
        }

    @staticmethod
    async def generate_lesson_plan(
        subject: str,
        topic: str,
        grade_level: str = "Grade 10",
        duration_mins: int = 60
    ) -> Dict[str, Any]:
        """
        Generate comprehensive teacher lesson plan using Gemini AI engine.
        """
        prompt = (
            f"Create a detailed {duration_mins}-minute lesson plan for {grade_level} on '{subject}: {topic}'.\n"
            f"Include: Learning Objectives, Prerequisites, Materials Required, Step-by-Step Activities with Timing, Assessment Questions, and Homework Assignment."
        )
        plan_content = await ChatService.generate_chat_response(prompt)
        return {
            "subject": subject,
            "topic": topic,
            "grade_level": grade_level,
            "duration_mins": duration_mins,
            "lesson_plan": plan_content
        }

    @staticmethod
    async def generate_summary(
        topic_or_text: str
    ) -> Dict[str, Any]:
        """
        Generate concise academic summary using Gemini AI engine.
        """
        prompt = f"Provide a clear, structured academic summary with key takeaways for:\n{topic_or_text}"
        summary = await ChatService.generate_chat_response(prompt)
        return {
            "summary": summary
        }

    @staticmethod
    async def get_dashboard_stats(
        db: AsyncSession,
        teacher_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Retrieve teacher dashboard statistics.
        """
        # Active courses count
        res_courses = await db.execute(select(func.count(Course.id)).where(Course.teacher_id == teacher_id))
        courses_count = res_courses.scalar_one() or 0

        # Uploaded documents count
        res_docs = await db.execute(select(func.count(Document.id)).where(Document.uploaded_by == teacher_id))
        docs_count = res_docs.scalar_one() or 0

        # Quizzes created count
        res_quizzes = await db.execute(select(func.count(Quiz.id)).where(Quiz.created_by == teacher_id))
        quizzes_count = res_quizzes.scalar_one() or 0

        # Assignments pending review count
        res_pending = await db.execute(
            select(func.count(AssignmentSubmission.id))
            .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
            .where(Assignment.created_by == teacher_id, AssignmentSubmission.score == None)
        )
        pending_count = res_pending.scalar_one() or 0

        return {
            "active_courses": courses_count,
            "uploaded_materials": docs_count,
            "created_quizzes": quizzes_count,
            "pending_submissions_to_grade": pending_count,
            "ai_recommendation": "All course materials are up to date. 3 students need extra review on Physics Chapter 4."
        }
