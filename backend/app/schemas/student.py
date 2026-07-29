import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class StudentBase(BaseModel):
    roll_number: Optional[str] = None
    class_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class StudentCreate(StudentBase):
    user_id: uuid.UUID

class StudentUpdate(BaseModel):
    roll_number: Optional[str] = None
    class_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class StudentResponse(StudentBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
