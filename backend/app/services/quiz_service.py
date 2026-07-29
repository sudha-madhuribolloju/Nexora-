"""
Quiz service — CRUD, question management, student attempt submission, auto-grading, reporting, and AI quiz generation.
"""
import uuid
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizStatus, QuestionType
from app.models.document_chunk import DocumentChunk
from app.services.chat_service import ChatService
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizQuestionCreate, QuizAttemptSubmit, QuizResultResponse
)

logger = logging.getLogger("app.services.quiz_service")


class QuizService:

    @staticmethod
    async def list_quizzes(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        course_id: Optional[uuid.UUID] = None,
    ) -> Tuple[int, List[Quiz]]:
        q = select(Quiz)
        if course_id:
            q = q.where(Quiz.course_id == course_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        quizzes = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(quizzes)

    @staticmethod
    async def get_quiz(db: AsyncSession, quiz_id: uuid.UUID) -> Quiz:
        result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return quiz

    @staticmethod
    async def create_quiz(
        db: AsyncSession, data: QuizCreate, teacher_id: Optional[uuid.UUID] = None
    ) -> Quiz:
        quiz = Quiz(**data.model_dump(), created_by=teacher_id)
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)
        return quiz

    @staticmethod
    async def update_quiz(
        db: AsyncSession, quiz_id: uuid.UUID, data: QuizUpdate
    ) -> Quiz:
        quiz = await QuizService.get_quiz(db, quiz_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(quiz, field, value)
        await db.commit()
        await db.refresh(quiz)
        return quiz

    @staticmethod
    async def delete_quiz(db: AsyncSession, quiz_id: uuid.UUID) -> None:
        quiz = await QuizService.get_quiz(db, quiz_id)
        await db.delete(quiz)
        await db.commit()

    @staticmethod
    async def add_question(
        db: AsyncSession, quiz_id: uuid.UUID, data: QuizQuestionCreate
    ) -> QuizQuestion:
        quiz = await QuizService.get_quiz(db, quiz_id)
        question = QuizQuestion(quiz_id=quiz.id, **data.model_dump())
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question

    @staticmethod
    async def start_attempt(
        db: AsyncSession, quiz_id: uuid.UUID, student_id: uuid.UUID
    ) -> QuizAttempt:
        quiz = await QuizService.get_quiz(db, quiz_id)
        if quiz.status != QuizStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz is not open for attempts"
            )
        # Check maximum attempts limit
        if quiz.max_attempts:
            attempts_count = (await db.execute(
                select(func.count()).select_from(QuizAttempt).where(
                    and_(QuizAttempt.quiz_id == quiz_id, QuizAttempt.student_id == student_id)
                )
            )).scalar_one()
            if attempts_count >= quiz.max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Maximum quiz attempts reached"
                )
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=student_id,
            started_at=datetime.now(timezone.utc)
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        return attempt

    @staticmethod
    async def submit_attempt(
        db: AsyncSession,
        quiz_id: uuid.UUID,
        attempt_id: uuid.UUID,
        student_id: uuid.UUID,
        data: QuizAttemptSubmit,
    ) -> QuizAttempt:
        quiz = await QuizService.get_quiz(db, quiz_id)
        result = await db.execute(
            select(QuizAttempt).where(
                and_(
                    QuizAttempt.id == attempt_id,
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.student_id == student_id
                )
            )
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found")
        if attempt.submitted_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt already submitted")

        # Fetch questions for scoring
        questions_result = await db.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
        )
        questions = questions_result.scalars().all()

        total_marks = 0.0
        score = 0.0
        answers = data.answers
        for q in questions:
            total_marks += q.marks
            student_ans = answers.get(str(q.id))
            if student_ans and q.correct_answer:
                if student_ans.strip().lower() == q.correct_answer.strip().lower():
                    score += q.marks

        now = datetime.now(timezone.utc)
        started = attempt.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        time_taken_seconds = int((now - started).total_seconds())

        passed = (score >= quiz.pass_score) if quiz.pass_score is not None else True

        attempt.answers = answers
        attempt.score = score
        attempt.total_marks = total_marks
        attempt.passed = passed
        attempt.submitted_at = now
        attempt.time_taken_seconds = time_taken_seconds

        await db.commit()
        await db.refresh(attempt)
        return attempt

    @staticmethod
    async def get_results(db: AsyncSession, quiz_id: uuid.UUID) -> QuizResultResponse:
        quiz = await QuizService.get_quiz(db, quiz_id)
        attempts_result = await db.execute(
            select(QuizAttempt).where(
                and_(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.submitted_at.isnot(None)
                )
            )
        )
        attempts = attempts_result.scalars().all()
        total_attempts = len(attempts)
        if total_attempts == 0:
            return QuizResultResponse(
                quiz_id=quiz_id,
                title=quiz.title,
                total_attempts=0,
                average_score=0.0,
                pass_rate=0.0,
                highest_score=0.0,
                lowest_score=0.0,
            )

        scores = [a.score for a in attempts if a.score is not None]
        passed_count = sum(1 for a in attempts if a.passed)
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        pass_rate = round((passed_count / total_attempts) * 100, 2)

        return QuizResultResponse(
            quiz_id=quiz_id,
            title=quiz.title,
            total_attempts=total_attempts,
            average_score=avg_score,
            pass_rate=pass_rate,
            highest_score=max(scores) if scores else 0.0,
            lowest_score=min(scores) if scores else 0.0,
        )

    @staticmethod
    async def generate_quiz(
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None,
        topic: Optional[str] = None,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate multiple-choice quiz questions based on indexed document or topic.
        """
        context_str = ""

        if document_id:
            q = select(DocumentChunk.chunk_text).where(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).limit(10)
            result = await db.execute(q)
            chunks = result.scalars().all()
            if chunks:
                context_str = "\n\n".join(chunks)

        prompt = (
            f"Generate a {difficulty} level multiple-choice quiz with exactly {num_questions} questions. "
            f"Topic: {topic or 'Classroom Material'}\n"
            f"Document Context:\n{context_str[:8000]}\n\n"
            "Return the output as a valid JSON object with the structure:\n"
            "{\n"
            '  "title": "Quiz Title",\n'
            '  "questions": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "question": "Question text?",\n'
            '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
            '      "correct_answer": "Option A",\n'
            '      "explanation": "Why this is correct."\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        response_str = await ChatService.generate_chat_response(prompt)
        
        # Parse JSON if valid, or return wrapped result
        try:
            cleaned = response_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
            return {
                "status": "success",
                "quiz": data
            }
        except Exception:
            return {
                "status": "success",
                "raw_quiz": response_str
            }
