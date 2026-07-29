import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ─── Course Enrollment ───────────────────────────────────────────────────────

class EnrollmentBase(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID


class EnrollmentResponse(EnrollmentBase):
    id: uuid.UUID
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ─── Course ───────────────────────────────────────────────────────────────────

class CourseBase(BaseModel):
    school_id: uuid.UUID
    title: str
    description: Optional[str] = None
    code: Optional[str] = None
    teacher_id: Optional[uuid.UUID] = None
    max_students: Optional[int] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    teacher_id: Optional[uuid.UUID] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[CourseResponse]
