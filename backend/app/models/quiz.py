"""
app/models/quiz.py
──────────────────
Quiz, QuizQuestion, and QuizAttempt ORM models.

Migrated to use app.database.base.Base (Alembic-tracked).
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.people import Teacher, Student


class QuizStatus(str, enum.Enum):
    DRAFT     = "draft"
    PUBLISHED = "published"
    CLOSED    = "closed"


class QuestionType(str, enum.Enum):
    MCQ          = "mcq"
    TRUE_FALSE   = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY        = "essay"


class Quiz(TimestampMixin, Base):
    """Quiz belonging to a course, authored by a teacher."""
    __tablename__ = "quizzes"
    __table_args__ = (
        Index("ix_quizzes_course_id",  "course_id"),
        Index("ix_quizzes_created_by", "created_by"),
        Index("ix_quizzes_status",     "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id:  Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("courses.id",  ondelete="CASCADE"),  nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    title:              Mapped[str]            = mapped_column(String(255), nullable=False)
    description:        Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    duration_minutes:   Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    max_attempts:       Mapped[int]            = mapped_column(Integer, default=1, nullable=False)
    pass_score:         Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shuffle_questions:  Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    show_results:       Mapped[bool]           = mapped_column(Boolean, default=True,  nullable=False)
    status:             Mapped[QuizStatus]     = mapped_column(Enum(QuizStatus, name="quizstatus"), default=QuizStatus.DRAFT, nullable=False)
    available_from:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    available_until:    Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    course:    Mapped["Course"]             = relationship("Course",   back_populates="quizzes")
    questions: Mapped[List["QuizQuestion"]] = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts:  Mapped[List["QuizAttempt"]]  = relationship("QuizAttempt",  back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Quiz title={self.title!r} status={self.status}>"


class QuizQuestion(Base):
    """A single question within a quiz."""
    __tablename__ = "quiz_questions"
    __table_args__ = (
        Index("ix_quiz_questions_quiz_id", "quiz_id"),
        Index("ix_quiz_questions_order",   "order"),
    )

    id:     Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)

    question_text: Mapped[str]            = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType]   = mapped_column(Enum(QuestionType, name="questiontype"), default=QuestionType.MCQ, nullable=False)
    options:        Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, doc="List of option strings for MCQ/True-False.")
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    marks:          Mapped[float]         = mapped_column(Float, default=1.0, nullable=False)
    order:          Mapped[int]           = mapped_column(Integer, default=0, nullable=False)
    explanation:    Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuizQuestion quiz={self.quiz_id} type={self.question_type} marks={self.marks}>"


class QuizAttempt(Base):
    """A student's attempt at a quiz (one row per attempt)."""
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("ix_quiz_attempts_quiz_id",    "quiz_id"),
        Index("ix_quiz_attempts_student_id", "student_id"),
    )

    id:         Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id:    Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("quizzes.id",  ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    answers:             Mapped[Optional[dict]]     = mapped_column(JSON, nullable=True, doc="{question_id: answer_text}")
    score:               Mapped[Optional[float]]    = mapped_column(Float, nullable=True)
    total_marks:         Mapped[Optional[float]]    = mapped_column(Float, nullable=True)
    passed:              Mapped[Optional[bool]]     = mapped_column(Boolean, nullable=True)
    started_at:          Mapped[datetime]           = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at:        Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_taken_seconds:  Mapped[Optional[int]]      = mapped_column(Integer, nullable=True)

    quiz:    Mapped["Quiz"]    = relationship("Quiz",    back_populates="attempts")
    student: Mapped["Student"] = relationship("Student", back_populates="quiz_attempts")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuizAttempt quiz={self.quiz_id} student={self.student_id} score={self.score}>"
