import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict
from app.models.quiz import QuizStatus, QuestionType


# ─── Quiz Question ────────────────────────────────────────────────────────────

class QuizQuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType = QuestionType.MCQ
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    marks: float = 1.0
    order: int = 0
    explanation: Optional[str] = None


class QuizQuestionCreate(QuizQuestionBase):
    pass


class QuizQuestionResponse(QuizQuestionBase):
    id: uuid.UUID
    quiz_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ─── Quiz ─────────────────────────────────────────────────────────────────────

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: uuid.UUID
    duration_minutes: Optional[int] = None
    max_attempts: int = 1
    pass_score: Optional[float] = None
    shuffle_questions: bool = False
    show_results: bool = True
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    max_attempts: Optional[int] = None
    pass_score: Optional[float] = None
    shuffle_questions: Optional[bool] = None
    show_results: Optional[bool] = None
    status: Optional[QuizStatus] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None


class QuizResponse(QuizBase):
    id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    status: QuizStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[QuizResponse]


# ─── Quiz Attempt ─────────────────────────────────────────────────────────────

class QuizAttemptCreate(BaseModel):
    """Payload when starting a quiz attempt."""
    pass


class QuizAttemptSubmit(BaseModel):
    answers: Dict[str, str]  # {question_id: answer}


class QuizAttemptResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    student_id: uuid.UUID
    score: Optional[float] = None
    total_marks: Optional[float] = None
    passed: Optional[bool] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class QuizResultResponse(BaseModel):
    quiz_id: uuid.UUID
    title: str
    total_attempts: int
    average_score: Optional[float] = None
    pass_rate: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None


# ─── AI Quiz Generation ────────────────────────────────────────────────────────

class GenerateQuizRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "Intermediate"
    questionCount: Optional[int] = 5


class QuizQuestionGeneratedItem(BaseModel):
    id: str
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str


class GenerateQuizResponse(BaseModel):
    quiz: List[QuizQuestionGeneratedItem]

