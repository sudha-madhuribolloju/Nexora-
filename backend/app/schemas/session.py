import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.session import SessionStatus


class SessionBase(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: uuid.UUID
    subject_id: Optional[uuid.UUID] = None
    teacher_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject_id: Optional[uuid.UUID] = None
    teacher_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    status: Optional[SessionStatus] = None


class SessionResponse(SessionBase):
    id: uuid.UUID
    status: SessionStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[SessionResponse]
