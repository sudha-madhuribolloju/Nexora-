"""
app/models/notification.py
────────────────────────────
Notification ORM model.

Migrated to use app.database.base.Base (Alembic-tracked).
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, enum.Enum):
    INFO         = "info"
    WARNING      = "warning"
    SUCCESS      = "success"
    ERROR        = "error"
    REMINDER     = "reminder"
    ANNOUNCEMENT = "announcement"
    ASSIGNMENT   = "assignment"
    EXAM         = "exam"
    ATTENDANCE   = "attendance"
    AI_COMPLETION = "ai_completion"
    SYSTEM_ALERT = "system_alert"
    ROLE_CHANGE  = "role_change"


class Notification(Base):
    """
    In-app notification sent to a user.
    Can be system-generated (sender_id=None) or user-to-user.
    Tracks read, unread, archived, and deleted states.
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_recipient_id", "recipient_id"),
        Index("ix_notifications_is_read",      "is_read"),
        Index("ix_notifications_created_at",   "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),  nullable=False)
    sender_id:    Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title:             Mapped[str]              = mapped_column(String(255), nullable=False)
    message:           Mapped[str]              = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notificationtype"), default=NotificationType.INFO, nullable=False)
    is_read:           Mapped[bool]             = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    status:            Mapped[str]              = mapped_column(String(20), default="unread", nullable=False, server_default="unread")
    action_url:        Mapped[Optional[str]]    = mapped_column(Text, nullable=True)
    created_at:        Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at:           Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id], back_populates="notifications_received")
    sender:    Mapped[Optional["User"]] = relationship("User", foreign_keys=[sender_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification type={self.notification_type} read={self.is_read} to={self.recipient_id}>"
