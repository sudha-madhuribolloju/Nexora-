"""
app/database/mixins.py
──────────────────────
Reusable SQLAlchemy 2.0 column mixins shared across all ORM models.

Design decisions:
  • TimestampMixin  — server-side defaults (func.now()) so the DB clock is
    always authoritative; onupdate keeps updated_at in sync automatically.
  • SoftDeleteMixin — is_deleted / deleted_at pattern lets us retain audit
    history while hiding records from normal queries. Partial index on
    is_deleted=false is created at the DB level (in each migration) so
    active-record lookups stay O(log n) even with millions of deleted rows.
  • Both mixins are pure Python: no metaclass magic, just mapped_column().
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Adds created_at and updated_at columns to any model.
    Both use timezone-aware TIMESTAMPTZ in PostgreSQL.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was first created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="UTC timestamp of the most recent update.",
    )


class SoftDeleteMixin:
    """
    Adds is_deleted and deleted_at columns to support soft deletes.

    Usage pattern:
        - Filters in repositories must always include `.where(Model.is_deleted == False)`
          OR use a query helper from BaseRepository.
        - Hard deletes are reserved for GDPR/data-erasure requests only.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        index=True,
        doc="True when the record has been soft-deleted.",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the record was soft-deleted.",
    )
