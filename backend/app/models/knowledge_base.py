"""
app/models/knowledge_base.py
─────────────────────────────
KnowledgeBaseArticle ORM model.

Migrated to use app.database.base.Base (Alembic-tracked).
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ArticleStatus(str, enum.Enum):
    DRAFT     = "draft"
    PUBLISHED = "published"
    ARCHIVED  = "archived"


class KnowledgeBaseArticle(Base):
    """
    A knowledge base article authored by staff.
    Supports tagging, categorization, view/like counters, and slug-based routing.
    """
    __tablename__ = "kb_articles"
    __table_args__ = (
        Index("ix_kb_articles_author_id", "author_id"),
        Index("ix_kb_articles_category",  "category"),
        Index("ix_kb_articles_status",    "status"),
        Index("ix_kb_articles_slug",      "slug"),
    )

    id:        Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title:       Mapped[str]              = mapped_column(String(500), nullable=False)
    slug:        Mapped[str]              = mapped_column(String(600), nullable=False, unique=True)
    content:     Mapped[str]              = mapped_column(Text, nullable=False)
    summary:     Mapped[Optional[str]]    = mapped_column(Text, nullable=True)
    category:    Mapped[Optional[str]]    = mapped_column(String(100), nullable=True)
    tags:        Mapped[Optional[dict]]   = mapped_column(JSON, nullable=True, doc="List of tag strings.")
    status:      Mapped[ArticleStatus]    = mapped_column(Enum(ArticleStatus, name="articlestatus"), default=ArticleStatus.DRAFT, nullable=False)
    views:       Mapped[int]              = mapped_column(Integer, default=0, nullable=False)
    likes:       Mapped[int]              = mapped_column(Integer, default=0, nullable=False)
    is_featured: Mapped[bool]             = mapped_column(Boolean, default=False, nullable=False)
    created_at:  Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:  Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    author: Mapped["User"] = relationship("User", back_populates="kb_articles")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeBaseArticle slug={self.slug!r} status={self.status}>"
