"""Migration 003 — Create classes, sections, subjects tables.

Revision ID : 0004_classes_sections_subjects
Revises     : 0003_schools_academic_years
Create Date : 2026-07-23

Design decisions
────────────────
• classes.UNIQUE(school_id, academic_year_id, name) — prevents duplicate grade
  names within the same school year (e.g. two "Grade 10" rows in 2025-2026).

• sections.UNIQUE(class_id, name) — prevents "Section A" from appearing twice
  in the same class. school_id is denormalised on sections to avoid a JOIN
  through classes for every school-level section query.

• sections.class_teacher_id — stored as a bare UUID column here (no FK). The
  FK constraint to teachers.id is added in Migration 004 when the teachers
  table exists. This "deferred FK" pattern mirrors how users.school_id was
  handled in Migration 000/002.

• subjects.UNIQUE(school_id, code) — subject codes are unique per school so
  "MATH" can exist in every school without collision.

• subjects.credits uses NUMERIC(4,1): supports values up to 999.9 — enough
  for any credit-hour system.

• subjects.color has no DB-level CHECK constraint (regex on the DB is
  verbose) — validation is enforced by Pydantic (#RRGGBB pattern).

• CASCADE behaviour:
    schools  DELETE → classes  CASCADE → sections CASCADE
    academic_years DELETE → classes CASCADE
    subjects are school-level; deleting a school cascades to subjects.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_classes_sections_subjects"
down_revision: Union[str, Sequence[str], None] = "0003_schools_academic_years"
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: classes
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "classes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign keys
        sa.Column("school_id",        postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Fields
        sa.Column("name",        sa.String(50),  nullable=False),
        sa.Column("grade_level", sa.Integer(),   nullable=True),
        sa.Column("description", sa.Text(),      nullable=True),
        # Soft delete
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["school_id"], ["schools.id"],
            ondelete="CASCADE", name="fk_classes_school_id",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"], ["academic_years.id"],
            ondelete="CASCADE", name="fk_classes_academic_year_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_classes"),
        sa.UniqueConstraint(
            "school_id", "academic_year_id", "name",
            name="uq_classes_school_year_name",
        ),
    )
    op.create_index("ix_classes_school_id",        "classes", ["school_id"])
    op.create_index("ix_classes_academic_year_id", "classes", ["academic_year_id"])
    op.create_index("ix_classes_grade_level",      "classes", ["grade_level"])
    op.create_index("ix_classes_is_deleted",       "classes", ["is_deleted"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: sections
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "sections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign keys
        sa.Column("class_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Deferred FK — FK constraint to teachers.id added in Migration 004
        sa.Column("class_teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Fields
        sa.Column("name",        sa.String(10), nullable=False),
        sa.Column("capacity",    sa.Integer(),  nullable=True),
        sa.Column("room_number", sa.String(20), nullable=True),
        # Soft delete
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["class_id"], ["classes.id"],
            ondelete="CASCADE", name="fk_sections_class_id",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"], ["schools.id"],
            ondelete="CASCADE", name="fk_sections_school_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sections"),
        sa.UniqueConstraint("class_id", "name", name="uq_sections_class_name"),
    )
    op.create_index("ix_sections_class_id",          "sections", ["class_id"])
    op.create_index("ix_sections_school_id",         "sections", ["school_id"])
    op.create_index("ix_sections_class_teacher_id",  "sections", ["class_teacher_id"])
    op.create_index("ix_sections_is_deleted",        "sections", ["is_deleted"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: subjects
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "subjects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign key
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Fields
        sa.Column("name",        sa.String(255),    nullable=False),
        sa.Column("code",        sa.String(20),     nullable=False),
        sa.Column("description", sa.Text(),         nullable=True),
        sa.Column("credits",     sa.Numeric(4, 1),  nullable=True),
        sa.Column("color",       sa.String(7),      nullable=True),
        sa.Column(
            "is_elective",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        # Soft delete
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["school_id"], ["schools.id"],
            ondelete="CASCADE", name="fk_subjects_school_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subjects"),
        sa.UniqueConstraint("school_id", "code", name="uq_subjects_school_code"),
    )
    op.create_index("ix_subjects_school_id", "subjects", ["school_id"])
    op.create_index("ix_subjects_name",      "subjects", ["name"])
    op.create_index("ix_subjects_is_deleted","subjects", ["is_deleted"])


def downgrade() -> None:
    op.drop_table("subjects")
    op.drop_table("sections")
    op.drop_table("classes")
