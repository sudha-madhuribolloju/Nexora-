"""Migration 002 — Create schools, academic_years; add FK school_id → schools on users.

Revision ID : 0003_schools_academic_years
Revises     : 0002_roles_permissions
Create Date : 2026-07-23

Design decisions
────────────────
• schools.code has a UNIQUE constraint — it is the human-readable tenant key
  used in URLs, reports, and integrations. Stored upper-case by convention
  (enforced in the service layer, not the DB).

• subscription_tier is a VARCHAR(20) + CheckConstraint, NOT a PostgreSQL ENUM
  type. ENUM types require DROP TYPE CASCADE to rename, making future
  migrations painful. VARCHAR + CHECK is equally safe and ALTER-friendly.

• academic_years has a UNIQUE(school_id, name) constraint to prevent duplicate
  year names per school. A partial unique index on (school_id, is_current)
  WHERE is_current=TRUE would be ideal to guarantee only one current year per
  school at the DB level; however it requires a UNIQUE partial index which
  Alembic cannot express cleanly. The constraint is enforced by the service
  layer via an atomic two-UPDATE pattern instead.

• Deferred FK — users.school_id was added as a bare UUID column in Migration
  000 because the schools table didn't exist yet. This migration adds the
  actual FK constraint using ALTER TABLE … ADD CONSTRAINT. The FK uses
  ON DELETE SET NULL so that soft-deleting a school does not orphan its users
  (their school_id becomes NULL, they retain accounts).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_schools_academic_years"
down_revision: Union[str, Sequence[str], None] = "0002_roles_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: schools
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "schools",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Identity
        sa.Column("name",  sa.String(255), nullable=False),
        sa.Column("code",  sa.String(20),  nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20),  nullable=True),
        # Address
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city",          sa.String(100), nullable=True),
        sa.Column("state",         sa.String(100), nullable=True),
        sa.Column(
            "country",
            sa.String(100),
            nullable=False,
            server_default=sa.text("'India'"),
        ),
        sa.Column("postal_code", sa.String(20), nullable=True),
        # Operational
        sa.Column(
            "timezone",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'Asia/Kolkata'"),
        ),
        sa.Column("logo_url", sa.Text(),       nullable=True),
        sa.Column("website",  sa.String(255),  nullable=True),
        # Subscription
        sa.Column(
            "subscription_tier",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'free'"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        # Soft delete
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
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
        sa.PrimaryKeyConstraint("id", name="pk_schools"),
        sa.UniqueConstraint("code", name="uq_schools_code"),
        sa.CheckConstraint(
            "subscription_tier IN ('free', 'basic', 'pro', 'enterprise')",
            name="ck_schools_subscription_tier",
        ),
    )
    op.create_index("ix_schools_code",      "schools", ["code"])
    op.create_index("ix_schools_name",      "schools", ["name"])
    op.create_index("ix_schools_is_active", "schools", ["is_active"])
    op.create_index("ix_schools_is_deleted","schools", ["is_deleted"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: academic_years
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "academic_years",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("school_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name",        sa.String(100),                 nullable=False),
        sa.Column("start_date",  sa.Date(),                      nullable=False),
        sa.Column("end_date",    sa.Date(),                      nullable=False),
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            ondelete="CASCADE",
            name="fk_academic_years_school_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_academic_years"),
        sa.UniqueConstraint("school_id", "name", name="uq_academic_years_school_name"),
        sa.CheckConstraint("end_date > start_date", name="ck_academic_years_dates"),
    )
    op.create_index("ix_academic_years_school_id",  "academic_years", ["school_id"])
    op.create_index("ix_academic_years_is_current", "academic_years", ["is_current"])

    # ══════════════════════════════════════════════════════════════════════════
    # DEFERRED FK: users.school_id → schools.id
    # (column was created as bare UUID in Migration 000)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_foreign_key(
        "fk_users_school_id",   # constraint name
        "users",                # source table
        "schools",              # referent table
        ["school_id"],          # source columns
        ["id"],                 # referent columns
        ondelete="SET NULL",    # NULL user.school_id when school is deleted
    )


def downgrade() -> None:
    # Remove deferred FK first
    op.drop_constraint("fk_users_school_id", "users", type_="foreignkey")
    op.drop_table("academic_years")
    op.drop_table("schools")
