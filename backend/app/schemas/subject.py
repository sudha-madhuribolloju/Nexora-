import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SubjectBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    course_id: uuid.UUID
    teacher_id: Optional[uuid.UUID] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    teacher_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubjectListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[SubjectResponse]
