import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ParentBase(BaseModel):
    occupation: Optional[str] = None
    address: Optional[str] = None

class ParentCreate(ParentBase):
    user_id: uuid.UUID

class ParentUpdate(BaseModel):
    occupation: Optional[str] = None
    address: Optional[str] = None

class ParentResponse(ParentBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
