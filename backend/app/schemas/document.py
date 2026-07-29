import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentCategory


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: DocumentCategory = DocumentCategory.GENERAL
    course_id: Optional[uuid.UUID] = None
    is_public: bool = False


class DocumentCreate(DocumentBase):
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None


class DocumentResponse(DocumentBase):
    id: uuid.UUID
    uploaded_by: uuid.UUID
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[DocumentResponse]
