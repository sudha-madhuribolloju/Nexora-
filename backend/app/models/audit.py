import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, JSON, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


class AuditLog(TimestampMixin, Base):
    """
    Model representing system audit logs for diagnostics, security compliance,
    and monitoring user actions across NEXORA.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Action performed (e.g., USER_LOGIN, DOCUMENT_UPLOAD, ROLE_CHANGE)",
    )
    resource: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Target resource entity name or endpoint path",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="Client IP address",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Browser / Client User Agent string",
    )
    details_json: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="Structured metadata payload associated with event",
    )

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action!r} user_id={self.user_id}>"
