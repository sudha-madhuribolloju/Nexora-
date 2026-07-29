import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.knowledge_base import ArticleStatus


class KBArticleBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_featured: bool = False


class KBArticleCreate(KBArticleBase):
    slug: Optional[str] = None  # auto-generated if not provided


class KBArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ArticleStatus] = None
    is_featured: Optional[bool] = None


class KBArticleResponse(KBArticleBase):
    id: uuid.UUID
    slug: str
    author_id: uuid.UUID
    status: ArticleStatus
    views: int
    likes: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class KBArticleListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[KBArticleResponse]


class KBSearchResponse(BaseModel):
    query: str
    total: int
    data: List[KBArticleResponse]
