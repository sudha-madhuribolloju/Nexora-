"""
app/models/otp.py
─────────────────
ORM model for storing 6-digit email OTP verification codes.
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class EmailOTP(TimestampMixin, Base):
    """
    Stores OTP verification codes for email validation.
    """
    __tablename__ = "email_otps"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    otp_code: Mapped[str] = mapped_column(
        String(6), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )

    def __repr__(self) -> str:
        return f"<EmailOTP email={self.email!r} code={self.otp_code!r} used={self.is_used}>"
