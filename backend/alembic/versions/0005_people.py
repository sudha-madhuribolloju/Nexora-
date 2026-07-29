"""Migration 005 — Create students, teachers, parents, parent_student_links tables.

Revision ID : 0005_people
Revises     : 0004_classes_sections_subjects
Create Date : 2026-07-24

Design decisions
────────────────
• students/teachers/parents all have a 1-to-1 FK to users.id (CASCADE DELETE).
  Deleting a User hard-removes the profile row; soft-delete on the profile row
  keeps historical records accessible.

• students.section_id → sections.id (SET NULL). When a section is deleted the
  student's section_id becomes NULL (not removed from school). This avoids
  cascade-deleting student records when a section is retired.

• The deferred FK from Migration 004:
    sections.class_teacher_id → teachers.id
  is added here via ALTER TABLE because the teachers table now exists.
  ON DELETE SET NULL: deleting a teacher clears the class_teacher_id reference
  without deleting the section.

• students UNIQUE(school_id, admission_number) + UNIQUE(school_id, roll_number):
  allows the same numbers across different schools.

• teachers UNIQUE(school_id, employee_id): same as above.

• parent_student_links UNIQUE(parent_id, student_id): prevents duplicate links.

• No soft-delete on parent_student_links: links are simply created or destroyed.
  Historical attendance/grade rows reference student_id directly, not the link.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_people"
down_revision: Union[str, Sequence[str], None] = "0004_classes_sections_subjects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: students
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "students",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign keys
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Identity / admission
        sa.Column("admission_number", sa.String(50),  nullable=True),
        sa.Column("roll_number",      sa.String(20),  nullable=True),
        sa.Column("admission_date",   sa.Date(),      nullable=True),
        # Personal
        sa.Column("date_of_birth", sa.Date(),       nullable=True),
        sa.Column("gender",        sa.String(20),   nullable=True),
        sa.Column("blood_group",   sa.String(5),    nullable=True),
        sa.Column("nationality",   sa.String(100),  nullable=True),
        # Address
        sa.Column("address_line1", sa.String(255),  nullable=True),
        sa.Column("address_line2", sa.String(255),  nullable=True),
        sa.Column("city",          sa.String(100),  nullable=True),
        sa.Column("state",         sa.String(100),  nullable=True),
        sa.Column("postal_code",   sa.String(20),   nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("remarks",   sa.Text(),    nullable=True),
        # Soft delete
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            ondelete="CASCADE", name="fk_students_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"], ["schools.id"],
            ondelete="CASCADE", name="fk_students_school_id",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"], ["sections.id"],
            ondelete="SET NULL", name="fk_students_section_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_students"),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
        sa.UniqueConstraint("school_id", "admission_number", name="uq_students_school_admission_number"),
        sa.UniqueConstraint("school_id", "roll_number",      name="uq_students_school_roll_number"),
    )
    op.create_index("ix_students_user_id",    "students", ["user_id"])
    op.create_index("ix_students_school_id",  "students", ["school_id"])
    op.create_index("ix_students_section_id", "students", ["section_id"])
    op.create_index("ix_students_is_deleted", "students", ["is_deleted"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: teachers
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "teachers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign keys
        sa.Column("user_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Professional
        sa.Column("employee_id",    sa.String(50),  nullable=True),
        sa.Column("department",     sa.String(100), nullable=True),
        sa.Column("qualification",  sa.String(255), nullable=True),
        sa.Column("specialization", sa.String(255), nullable=True),
        sa.Column("joining_date",   sa.Date(),      nullable=True),
        sa.Column(
            "is_class_teacher",
            sa.Boolean(), nullable=False, server_default=sa.text("false"),
        ),
        # Personal
        sa.Column("date_of_birth", sa.Date(),    nullable=True),
        sa.Column("gender",        sa.String(20), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("remarks",   sa.Text(),    nullable=True),
        # Soft delete
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            ondelete="CASCADE", name="fk_teachers_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"], ["schools.id"],
            ondelete="CASCADE", name="fk_teachers_school_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_teachers"),
        sa.UniqueConstraint("user_id", name="uq_teachers_user_id"),
        sa.UniqueConstraint("school_id", "employee_id", name="uq_teachers_school_employee_id"),
    )
    op.create_index("ix_teachers_user_id",         "teachers", ["user_id"])
    op.create_index("ix_teachers_school_id",        "teachers", ["school_id"])
    op.create_index("ix_teachers_is_class_teacher", "teachers", ["is_class_teacher"])
    op.create_index("ix_teachers_is_deleted",       "teachers", ["is_deleted"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: parents
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "parents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign key
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Relation meta
        sa.Column("relation_type", sa.String(50),  nullable=True),
        sa.Column("occupation",    sa.String(100), nullable=True),
        # Contact
        sa.Column("address_line1",   sa.String(255), nullable=True),
        sa.Column("address_line2",   sa.String(255), nullable=True),
        sa.Column("city",            sa.String(100), nullable=True),
        sa.Column("state",           sa.String(100), nullable=True),
        sa.Column("postal_code",     sa.String(20),  nullable=True),
        sa.Column("alternate_phone", sa.String(20),  nullable=True),
        # Soft delete
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            ondelete="CASCADE", name="fk_parents_user_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_parents"),
        sa.UniqueConstraint("user_id", name="uq_parents_user_id"),
    )
    op.create_index("ix_parents_user_id",    "parents", ["user_id"])
    op.create_index("ix_parents_is_deleted", "parents", ["is_deleted"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: parent_student_links  (M2M join table)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "parent_student_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("parent_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "is_primary_contact",
            sa.Boolean(), nullable=False, server_default=sa.text("false"),
        ),
        # Timestamps (no soft-delete on join rows)
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(
            ["parent_id"], ["parents.id"],
            ondelete="CASCADE", name="fk_psl_parent_id",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"],
            ondelete="CASCADE", name="fk_psl_student_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_parent_student_links"),
        sa.UniqueConstraint("parent_id", "student_id", name="uq_parent_student_link"),
    )
    op.create_index("ix_psl_parent_id",  "parent_student_links", ["parent_id"])
    op.create_index("ix_psl_student_id", "parent_student_links", ["student_id"])

    # ══════════════════════════════════════════════════════════════════════════
    # DEFERRED FK RESOLUTION: sections.class_teacher_id → teachers.id
    # Added here (Migration 005) because the teachers table now exists.
    # ══════════════════════════════════════════════════════════════════════════
    op.create_foreign_key(
        "fk_sections_class_teacher_id",
        "sections",
        "teachers",
        ["class_teacher_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop deferred FK first
    op.drop_constraint("fk_sections_class_teacher_id", "sections", type_="foreignkey")

    # Drop join table first (references parents and students)
    op.drop_table("parent_student_links")

    # Drop profile tables
    op.drop_table("parents")
    op.drop_table("teachers")
    op.drop_table("students")
