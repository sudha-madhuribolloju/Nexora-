"""
app/models/recording.py
────────────────────────
Recording ORM model strictly matching PostgreSQL recordings table schema.
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.session import ClassSession
    from app.models.user import User


class Recording(TimestampMixin, Base):
    """
    Metadata model for saved lecture recordings matching PostgreSQL recordings table.
    """
    __tablename__ = "recordings"
    __table_args__ = (
        Index("ix_recordings_lecture_id", "lecture_id"),
        Index("ix_recordings_teacher_id", "teacher_id"),
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

    # ── Media & File Details ───────────────────────────────────────────────────
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── AI Outputs & Metadata ──────────────────────────────────────────────────
    summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    lecture: Mapped[Optional["ClassSession"]] = relationship("ClassSession", foreign_keys=[lecture_id])
    teacher: Mapped[Optional["User"]] = relationship("User", foreign_keys=[teacher_id])

    def __repr__(self) -> str:
        return f"<Recording id={self.id} filename={self.filename!r}>"
