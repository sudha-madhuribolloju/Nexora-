import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentCategory


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: DocumentCategory = DocumentCategory.GENERAL
    course_id: Optional[uuid.UUID] = None
    is_public: bool = False
    tags: Optional[List[str]] = None


class DocumentCreate(DocumentBase):
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: uuid.UUID
    uploaded_by: uuid.UUID
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    version: int = 1
    file_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[DocumentResponse]
