"""
app/models/document.py
───────────────────────
Document and DocumentChunk ORM models.

Migrated to use app.database.base.Base (Alembic-tracked).
DocumentChunk uses pgvector for embedding storage.
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
    VECTOR_TYPE = Vector(768)
except ImportError:  # pragma: no cover
    VECTOR_TYPE = None  # type: ignore

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course


class DocumentCategory(str, enum.Enum):
    GENERAL         = "general"
    COURSE_MATERIAL = "course_material"
    ASSIGNMENT      = "assignment"
    REPORT          = "report"
    POLICY          = "policy"
    OTHER           = "other"


class Document(TimestampMixin, Base):
    """
    Uploaded document / file reference.
    Full text extracted and chunked into DocumentChunk rows for RAG.
    """
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_uploaded_by", "uploaded_by"),
        Index("ix_documents_course_id",   "course_id"),
        Index("ix_documents_category",    "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by: Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id",   ondelete="CASCADE"),  nullable=False)
    course_id:   Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)

    title:           Mapped[str]                = mapped_column(String(255), nullable=False)
    description:     Mapped[Optional[str]]      = mapped_column(Text, nullable=True)
    file_name:       Mapped[str]                = mapped_column(String(500), nullable=False)
    file_url:        Mapped[str]                = mapped_column(Text, nullable=False)
    file_type:       Mapped[Optional[str]]      = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]]      = mapped_column(Integer, nullable=True)
    category:        Mapped[DocumentCategory]   = mapped_column(Enum(DocumentCategory, name="documentcategory"), default=DocumentCategory.GENERAL, nullable=False)
    is_public:       Mapped[bool]               = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    uploader: Mapped["User"]              = relationship("User",   foreign_keys=[uploaded_by], back_populates="documents")
    course:   Mapped[Optional["Course"]]  = relationship("Course", back_populates="documents")
    chunks:   Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Document title={self.title!r} type={self.file_type}>"


class DocumentChunk(Base):
    """
    A chunked text segment of a Document with a pgvector embedding for RAG.
    The embedding column is only present when pgvector is installed.
    """
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_document_id",  "document_id"),
        Index("ix_document_chunks_uploaded_by",  "uploaded_by"),
        Index("ix_document_chunks_chunk_index",  "chunk_index"),
    )

    id:          Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id",     ondelete="CASCADE"), nullable=False)

    document_name: Mapped[str]            = mapped_column(String(255), nullable=False)
    chunk_index:   Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    chunk_text:    Mapped[str]            = mapped_column(Text, nullable=False)
    page_number:   Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at:    Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # pgvector embedding — column is defined conditionally to avoid import errors
    # on environments without pgvector. Migration 006 adds this as a vector(768) column.
    if VECTOR_TYPE is not None:
        embedding = mapped_column(VECTOR_TYPE, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentChunk document={self.document_id} idx={self.chunk_index}>"
