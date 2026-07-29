"""
app/models/recording.py
────────────────────────
Upgraded Recording ORM model for lecture recordings with RAG, RBAC, and AI summary metadata.
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.session import ClassSession
    from app.models.user import User
    from app.models.academic import Class, Section, Subject


class Recording(TimestampMixin, SoftDeleteMixin, Base):
    """
    Metadata model for saved lecture recordings.
    """
    __tablename__ = "recordings"
    __table_args__ = (
        Index("ix_recordings_lecture_id", "lecture_id"),
        Index("ix_recordings_teacher_id", "teacher_id"),
        Index("ix_recordings_class_id", "class_id"),
        Index("ix_recordings_subject_id", "subject_id"),
        Index("ix_recordings_status", "recording_status"),
    )

    # ── Primary Key ─────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Foreign Keys ────────────────────────────────────────────────────────────
    lecture_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="SET NULL"), nullable=True
    )
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sections.id", ondelete="SET NULL"), nullable=True
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )

    # ── Media & File Details ───────────────────────────────────────────────────
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, server_default="0")
    duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recording_status: Mapped[str] = mapped_column(
        String(50), default="ready", nullable=False, server_default="ready",
        doc="processing | ready | failed | deleted"
    )

    # ── AI Outputs & Metadata ──────────────────────────────────────────────────
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    lecture: Mapped[Optional["ClassSession"]] = relationship("ClassSession", foreign_keys=[lecture_id])
    teacher: Mapped[Optional["User"]] = relationship("User", foreign_keys=[teacher_id])
    class_entity: Mapped[Optional["Class"]] = relationship("Class", foreign_keys=[class_id])
    section: Mapped[Optional["Section"]] = relationship("Section", foreign_keys=[section_id])
    subject: Mapped[Optional["Subject"]] = relationship("Subject", foreign_keys=[subject_id])

    def __repr__(self) -> str:
        return f"<Recording id={self.id} filename={self.filename!r} status={self.recording_status!r}>"
