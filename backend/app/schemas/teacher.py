import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TeacherBase(BaseModel):
    employee_id: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None

class TeacherCreate(TeacherBase):
    user_id: uuid.UUID

class TeacherUpdate(BaseModel):
    employee_id: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None

class TeacherResponse(TeacherBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
