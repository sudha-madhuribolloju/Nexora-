"""Migration 000 — Upgrade users table: INTEGER pk → UUID, add profile columns.

Revision ID : 0001_upgrade_users_uuid
Revises     : 2c357a1f30fc
Create Date : 2026-07-23

Design decisions
────────────────
• We DROP and RECREATE the users table rather than ALTER the PK type because
  PostgreSQL cannot change a primary key column type in-place when sequences
  (SERIAL) are attached. This is safe because the table is empty in dev.
• Old stub tables (students, teachers, courses, etc.) created by session.py's
  create_all() are dropped here so the new, properly normalised versions can
  be created by their own migrations without naming conflicts.
• school_id is added as a bare UUID column (no FK constraint). The FK to
  schools.id is added in Migration 002 once the schools table exists.
• All timestamps use TIMESTAMPTZ (timezone=True) — the DB clock is always UTC.
• gen_random_uuid() (pgcrypto / PostgreSQL 13+) is used as server_default so
  rows inserted directly via psql also get valid UUIDs.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = "0001_upgrade_users_uuid"
down_revision: Union[str, Sequence[str], None] = "2c357a1f30fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Old stub tables created by session.py create_all() — drop these first so
# the new, properly-structured migrations can create them cleanly.
_STUB_TABLES = [
    # Order matters: tables with FKs must come before their parents
    "quiz_attempts",
    "quiz_questions",
    "quizzes",
    "assignment_submissions",
    "assignments",
    "course_enrollments",
    "sessions",
    "attendance",
    "document_chunks",
    "documents",
    "notifications",
    "kb_articles",
    "subjects",
    "courses",
    "teachers",
    "students",
    "parents",
]


def upgrade() -> None:
    # ── 1. Drop old stub tables (CASCADE handles any lurking FKs) ─────────────
    for table in _STUB_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    # ── 2. Drop the legacy INTEGER-keyed users table ───────────────────────────
    op.drop_table("users")

    # ── 3. Recreate users with UUID PK and full profile schema ────────────────
    op.create_table(
        "users",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Authentication
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(512), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        # Primary role shorthand (fine-grained RBAC uses user_roles join table)
        sa.Column("role", sa.String(50), nullable=False),
        # Profile
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        # School scoping (FK to schools.id added in Migration 002)
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to schools.id — constraint added in migration 002.",
        ),
        # Soft delete
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Audit timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # ── 4. Indexes ─────────────────────────────────────────────────────────────
    op.create_index("ix_users_email",      "users", ["email"],      unique=True)
    op.create_index("ix_users_role",       "users", ["role"])
    op.create_index("ix_users_school_id",  "users", ["school_id"])
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])


def downgrade() -> None:
    """Restore the original minimal users table with INTEGER PK."""
    op.drop_table("users")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
