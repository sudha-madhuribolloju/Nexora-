import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.attendance import AttendanceStatus


class AttendanceBase(BaseModel):
    session_id: uuid.UUID
    student_id: uuid.UUID
    status: AttendanceStatus = AttendanceStatus.ABSENT
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceBulkItem(BaseModel):
    student_id: uuid.UUID
    status: AttendanceStatus = AttendanceStatus.ABSENT
    notes: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    session_id: uuid.UUID
    records: List[AttendanceBulkItem]


class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: uuid.UUID
    marked_by: Optional[uuid.UUID] = None
    marked_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[AttendanceResponse]


class AttendanceReportEntry(BaseModel):
    student_id: uuid.UUID
    total_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float
