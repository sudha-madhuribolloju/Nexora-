"""
app/models/transcript.py
────────────────────────
ORM models for Lecture Sessions, Transcripts, and Lecture Summaries.
Supports PostgreSQL persistence for live speech-to-text transcripts,
session metadata, and AI-generated summaries.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class LectureSession(TimestampMixin, Base):
    """
    A live classroom or recorded lecture session.
    Supports session IDs such as numeric ('1250'), formatted ('LC-20260820-123'),
    slugs ('sess_abcd1234'), or standard UUIDs.
    """
    __tablename__ = "lecture_sessions"
    __table_args__ = (
        Index("ix_lecture_sessions_status", "status"),
        Index("ix_lecture_sessions_teacher_id", "teacher_id"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="Live Classroom Session", nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    teacher_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="LIVE", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    teacher: Mapped[Optional["User"]] = relationship("User", foreign_keys=[teacher_id])
    transcripts: Mapped[List["Transcript"]] = relationship(
        "Transcript", back_populates="session", cascade="all, delete-orphan", order_by="Transcript.sequence"
    )
    summaries: Mapped[List["LectureSummary"]] = relationship(
        "LectureSummary", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LectureSession id={self.id!r} title={self.title!r} status={self.status!r}>"


class Transcript(TimestampMixin, Base):
    """
    Speech-to-Text transcript entries for a lecture session.
    Stores individual speaker-attributed segments or consolidated transcripts.
    """
    __tablename__ = "transcripts"
    __table_args__ = (
        Index("ix_transcripts_lecture_session_id", "lecture_session_id"),
        Index("ix_transcripts_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lecture_session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False
    )
    speaker: Mapped[str] = mapped_column(String(255), default="Teacher", nullable=False)
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_teacher: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="finalized", nullable=False)

    session: Mapped["LectureSession"] = relationship("LectureSession", back_populates="transcripts")

    def __repr__(self) -> str:
        return f"<Transcript id={self.id} session_id={self.lecture_session_id!r} speaker={self.speaker!r}>"


class LectureSummary(TimestampMixin, Base):
    """
    AI-generated lecture summary and NLP insights associated with a lecture session.
    """
    __tablename__ = "lecture_summaries"
    __table_args__ = (
        Index("ix_lecture_summaries_lecture_session_id", "lecture_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lecture_session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    nlp_insights: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)

    session: Mapped["LectureSession"] = relationship("LectureSession", back_populates="summaries")

    def __repr__(self) -> str:
        return f"<LectureSummary id={self.id} session_id={self.lecture_session_id!r}>"
