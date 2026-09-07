import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class RecordingBase(BaseModel):
    lecture_id: Optional[uuid.UUID] = None
    teacher_id: Optional[uuid.UUID] = None
    class_id: Optional[uuid.UUID] = None
    section_id: Optional[uuid.UUID] = None
    subject_id: Optional[uuid.UUID] = None
    filename: str
    duration: float = 0.0
    file_size: Optional[int] = 0
    recording_status: Optional[str] = "ready"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    storage_path: str
    transcript: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    thumbnail: Optional[str] = None

class RecordingCreate(RecordingBase):
    pass

class RecordingUpdate(BaseModel):
    filename: Optional[str] = None
    recording_status: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    thumbnail: Optional[str] = None
    is_deleted: Optional[bool] = None

class RecordingResponse(RecordingBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: Optional[bool] = False

    # Optional UI display annotations
    teacher_name: Optional[str] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RecordingListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[RecordingResponse]

class RecordingAnalyticsResponse(BaseModel):
    total_recordings: int
    total_duration_seconds: float
    total_duration_hours: float
    total_storage_bytes: int
    total_storage_mb: float
    top_teachers: List[Dict[str, Any]]
    latest_recordings: List[RecordingResponse]
