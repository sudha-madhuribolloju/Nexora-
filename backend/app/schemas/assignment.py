import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.assignment import AssignmentStatus, SubmissionStatus


# ─── Assignment ───────────────────────────────────────────────────────────────

class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    course_id: uuid.UUID
    max_score: Optional[float] = 100.0
    due_date: Optional[datetime] = None
    allow_late_submission: bool = False


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    max_score: Optional[float] = None
    due_date: Optional[datetime] = None
    status: Optional[AssignmentStatus] = None
    allow_late_submission: Optional[bool] = None


class AssignmentResponse(AssignmentBase):
    id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    status: AssignmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[AssignmentResponse]


# ─── Submission ───────────────────────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    content: Optional[str] = None
    file_url: Optional[str] = None


class SubmissionGrade(BaseModel):
    score: float
    feedback: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: uuid.UUID
    content: Optional[str] = None
    file_url: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    status: SubmissionStatus
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    graded_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[SubmissionResponse]


# ─── AI Assignment Generation ──────────────────────────────────────────────────

class GenerateAssignmentRequest(BaseModel):
    topic: str


class GenerateAssignmentResponse(BaseModel):
    reply: str

