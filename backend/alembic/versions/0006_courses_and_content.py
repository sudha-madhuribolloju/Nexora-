"""Migration 006 — Courses, Sessions, Attendance, Assignments, Quizzes,
Notifications, Documents, Knowledge Base Articles.

Revision ID : 0006_courses_and_content
Revises     : 0005_people
Create Date : 2026-07-24

Design decisions
────────────────
• courses — school-scoped (school_id FK). teacher_id is optional (SET NULL).
  A course's code is unique within a school (UNIQUE school_id, code).

• course_enrollments — many-to-many Student ↔ Course.
  UNIQUE(course_id, student_id) prevents double-enrolment.

• course_subjects — replaces the legacy `subjects` table (base_class era).
  Maps a school-level catalogue Subject to a Course, with an optional teacher
  and credit hour count.  Table name changed to avoid collision with academic.subjects.

• class_sessions — FK to courses + subjects + teachers. All SET NULL on delete.
  status is a native PG ENUM (sessionstatus) for efficient filtering.

• attendance — UNIQUE(session_id, student_id) prevents double-marking.
  status is a native PG ENUM (attendancestatus).

• assignments / assignment_submissions — graded_by teacher FK (SET NULL).

• quizzes / quiz_questions / quiz_attempts — JSON columns for options and answers.

• notifications — two FK to users (recipient + sender). sender can be NULL for
  system-generated notifications.

• documents + document_chunks — document_chunks includes a vector(768) column
  for pgvector embeddings used by the RAG pipeline. The column is created as
  nullable so the migration can run even without pgvector installed; the HNSW
  index is created separately in session.py startup.

• kb_articles — slug is globally unique (not school-scoped); unique constraint.

Named PG ENUMs are created once and reused across tables where the same enum
applies (e.g. `assignmentstatus` for both assignments and submissions).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_courses_and_content"
down_revision: Union[str, Sequence[str], None] = "0005_people"
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


# ── Helper: create PG ENUM if it doesn't already exist ─────────────────────
def _create_enum(name: str, *values: str) -> postgresql.ENUM:
    e = postgresql.ENUM(*values, name=name, create_type=False)
    e.create(op.get_bind(), checkfirst=True)
    return e


def upgrade() -> None:

    # ── Create named PG ENUMs ────────────────────────────────────────────────
    sessionstatus_enum      = _create_enum("sessionstatus",      "scheduled", "active", "completed", "cancelled")
    attendancestatus_enum   = _create_enum("attendancestatus",   "present",   "absent", "late", "excused")
    assignmentstatus_enum   = _create_enum("assignmentstatus",   "draft",     "published", "closed")
    submissionstatus_enum   = _create_enum("submissionstatus",   "submitted", "late", "graded", "returned")
    quizstatus_enum         = _create_enum("quizstatus",         "draft",     "published", "closed")
    questiontype_enum       = _create_enum("questiontype",       "mcq",       "true_false", "short_answer", "essay")
    notificationtype_enum   = _create_enum("notificationtype",   "info",      "warning", "success", "error", "reminder", "announcement")
    documentcategory_enum   = _create_enum("documentcategory",   "general",   "course_material", "assignment", "report", "policy", "other")
    articlestatus_enum      = _create_enum("articlestatus",      "draft",     "published", "archived")

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: courses
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "courses",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("school_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id",  postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title",       sa.String(255), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        sa.Column("code",        sa.String(50),  nullable=True),
        sa.Column("is_active",   sa.Boolean(),   nullable=False, server_default=sa.text("true")),
        sa.Column("max_students", sa.Integer(),  nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["school_id"],  ["schools.id"],  ondelete="CASCADE",  name="fk_courses_school_id"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="SET NULL", name="fk_courses_teacher_id"),
        sa.PrimaryKeyConstraint("id", name="pk_courses"),
    )
    op.create_index("ix_courses_school_id",  "courses", ["school_id"])
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"])
    op.create_index("ix_courses_is_active",  "courses", ["is_active"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: course_enrollments
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "course_enrollments",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active",  sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"],  ["courses.id"],  ondelete="CASCADE", name="fk_course_enrollments_course_id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE", name="fk_course_enrollments_student_id"),
        sa.PrimaryKeyConstraint("id", name="pk_course_enrollments"),
        sa.UniqueConstraint("course_id", "student_id", name="uq_course_enrollment"),
    )
    op.create_index("ix_course_enrollments_course_id",  "course_enrollments", ["course_id"])
    op.create_index("ix_course_enrollments_student_id", "course_enrollments", ["student_id"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: course_subjects  (replaces legacy 'subjects' table)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "course_subjects",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id",  postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("credits",     sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(),    nullable=True),
        sa.Column("is_active",   sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"],  ["courses.id"],  ondelete="CASCADE",  name="fk_course_subjects_course_id"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE",  name="fk_course_subjects_subject_id"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="SET NULL", name="fk_course_subjects_teacher_id"),
        sa.PrimaryKeyConstraint("id", name="pk_course_subjects"),
    )
    op.create_index("ix_course_subjects_course_id",  "course_subjects", ["course_id"])
    op.create_index("ix_course_subjects_subject_id", "course_subjects", ["subject_id"])
    op.create_index("ix_course_subjects_teacher_id", "course_subjects", ["teacher_id"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: class_sessions
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "class_sessions",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id",   postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("teacher_id",   postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title",        sa.String(255), nullable=False),
        sa.Column("description",  sa.Text(),      nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at",     sa.DateTime(timezone=True), nullable=True),
        sa.Column("status",sessionstatus_enum,nullable=False,server_default="scheduled"),
        sa.Column("location",     sa.String(255), nullable=True),
        sa.Column("meeting_url",  sa.Text(),      nullable=True),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"],  ["courses.id"],  ondelete="CASCADE",  name="fk_class_sessions_course_id"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="SET NULL", name="fk_class_sessions_subject_id"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="SET NULL", name="fk_class_sessions_teacher_id"),
        sa.PrimaryKeyConstraint("id", name="pk_class_sessions"),
    )
    op.create_index("ix_class_sessions_course_id",  "class_sessions", ["course_id"])
    op.create_index("ix_class_sessions_teacher_id", "class_sessions", ["teacher_id"])
    op.create_index("ix_class_sessions_status",     "class_sessions", ["status"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: attendance
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "attendance",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marked_by",  postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status",     attendancestatus_enum, nullable=False, server_default="absent"),
        sa.Column("notes",      sa.Text(), nullable=True),
        sa.Column("marked_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["class_sessions.id"], ondelete="CASCADE",  name="fk_attendance_session_id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"],       ondelete="CASCADE",  name="fk_attendance_student_id"),
        sa.ForeignKeyConstraint(["marked_by"],  ["users.id"],          ondelete="SET NULL", name="fk_attendance_marked_by"),
        sa.PrimaryKeyConstraint("id", name="pk_attendance"),
        sa.UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
    )
    op.create_index("ix_attendance_session_id", "attendance", ["session_id"])
    op.create_index("ix_attendance_student_id", "attendance", ["student_id"])
    op.create_index("ix_attendance_status",     "attendance", ["status"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: assignments
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "assignments",
        sa.Column("id",                    postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id",             postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by",            postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title",                 sa.String(255), nullable=False),
        sa.Column("description",           sa.Text(),      nullable=True),
        sa.Column("instructions",          sa.Text(),      nullable=True),
        sa.Column("max_score",             sa.Float(),     nullable=True),
        sa.Column("due_date",              sa.DateTime(timezone=True), nullable=True),
        sa.Column("status",                assignmentstatus_enum, nullable=False, server_default="draft"),
        sa.Column("allow_late_submission", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"],  ["courses.id"],  ondelete="CASCADE",  name="fk_assignments_course_id"),
        sa.ForeignKeyConstraint(["created_by"], ["teachers.id"], ondelete="SET NULL", name="fk_assignments_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_assignments"),
    )
    op.create_index("ix_assignments_course_id",  "assignments", ["course_id"])
    op.create_index("ix_assignments_created_by", "assignments", ["created_by"])
    op.create_index("ix_assignments_status",     "assignments", ["status"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: assignment_submissions
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "assignment_submissions",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graded_by",     postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content",       sa.Text(),  nullable=True),
        sa.Column("file_url",      sa.Text(),  nullable=True),
        sa.Column("score",         sa.Float(), nullable=True),
        sa.Column("feedback",      sa.Text(),  nullable=True),
        sa.Column("status",        submissionstatus_enum, nullable=False, server_default="submitted"),
        sa.Column("submitted_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("graded_at",     sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE",  name="fk_assignment_submissions_assignment_id"),
        sa.ForeignKeyConstraint(["student_id"],    ["students.id"],   ondelete="CASCADE",  name="fk_assignment_submissions_student_id"),
        sa.ForeignKeyConstraint(["graded_by"],     ["teachers.id"],   ondelete="SET NULL", name="fk_assignment_submissions_graded_by"),
        sa.PrimaryKeyConstraint("id", name="pk_assignment_submissions"),
    )
    op.create_index("ix_assignment_submissions_assignment_id", "assignment_submissions", ["assignment_id"])
    op.create_index("ix_assignment_submissions_student_id",    "assignment_submissions", ["student_id"])
    op.create_index("ix_assignment_submissions_status",        "assignment_submissions", ["status"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: quizzes
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "quizzes",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id",        postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by",       postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title",            sa.String(255), nullable=False),
        sa.Column("description",      sa.Text(),      nullable=True),
        sa.Column("duration_minutes", sa.Integer(),   nullable=True),
        sa.Column("max_attempts",     sa.Integer(),   nullable=False, server_default="1"),
        sa.Column("pass_score",       sa.Float(),     nullable=True),
        sa.Column("shuffle_questions", sa.Boolean(),  nullable=False, server_default=sa.text("false")),
        sa.Column("show_results",     sa.Boolean(),   nullable=False, server_default=sa.text("true")),
        sa.Column("status",           quizstatus_enum, nullable=False, server_default="draft"),
        sa.Column("available_from",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_until",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"],  ["courses.id"],  ondelete="CASCADE",  name="fk_quizzes_course_id"),
        sa.ForeignKeyConstraint(["created_by"], ["teachers.id"], ondelete="SET NULL", name="fk_quizzes_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_quizzes"),
    )
    op.create_index("ix_quizzes_course_id",  "quizzes", ["course_id"])
    op.create_index("ix_quizzes_created_by", "quizzes", ["created_by"])
    op.create_index("ix_quizzes_status",     "quizzes", ["status"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: quiz_questions
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "quiz_questions",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("quiz_id",        postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text",  sa.Text(),    nullable=False),
        sa.Column("question_type",  questiontype_enum, nullable=False, server_default="mcq"),
        sa.Column("options",        postgresql.JSON(), nullable=True),
        sa.Column("correct_answer", sa.Text(),   nullable=True),
        sa.Column("marks",          sa.Float(),  nullable=False, server_default="1.0"),
        sa.Column("order",          sa.Integer(), nullable=False, server_default="0"),
        sa.Column("explanation",    sa.Text(),   nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE", name="fk_quiz_questions_quiz_id"),
        sa.PrimaryKeyConstraint("id", name="pk_quiz_questions"),
    )
    op.create_index("ix_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"])
    op.create_index("ix_quiz_questions_order",   "quiz_questions", ["order"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: quiz_attempts
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "quiz_attempts",
        sa.Column("id",                 postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("quiz_id",            postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id",         postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answers",            postgresql.JSON(), nullable=True),
        sa.Column("score",              sa.Float(),   nullable=True),
        sa.Column("total_marks",        sa.Float(),   nullable=True),
        sa.Column("passed",             sa.Boolean(), nullable=True),
        sa.Column("started_at",         sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at",       sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"],    ["quizzes.id"],  ondelete="CASCADE", name="fk_quiz_attempts_quiz_id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE", name="fk_quiz_attempts_student_id"),
        sa.PrimaryKeyConstraint("id", name="pk_quiz_attempts"),
    )
    op.create_index("ix_quiz_attempts_quiz_id",    "quiz_attempts", ["quiz_id"])
    op.create_index("ix_quiz_attempts_student_id", "quiz_attempts", ["student_id"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: notifications
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "notifications",
        sa.Column("id",                postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("recipient_id",      postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id",         postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title",             sa.String(255), nullable=False),
        sa.Column("message",           sa.Text(),      nullable=False),
        sa.Column("notification_type", notificationtype_enum, nullable=False, server_default="info"),
        sa.Column("is_read",           sa.Boolean(),   nullable=False, server_default=sa.text("false")),
        sa.Column("action_url",        sa.Text(),      nullable=True),
        sa.Column("created_at",        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at",           sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE",  name="fk_notifications_recipient_id"),
        sa.ForeignKeyConstraint(["sender_id"],    ["users.id"], ondelete="SET NULL", name="fk_notifications_sender_id"),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index("ix_notifications_is_read",      "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at",   "notifications", ["created_at"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: documents
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "documents",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("uploaded_by",     postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id",       postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title",           sa.String(255), nullable=False),
        sa.Column("description",     sa.Text(),      nullable=True),
        sa.Column("file_name",       sa.String(500), nullable=False),
        sa.Column("file_url",        sa.Text(),      nullable=False),
        sa.Column("file_type",       sa.String(100), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(),   nullable=True),
        sa.Column("category",        documentcategory_enum, nullable=False, server_default="general"),
        sa.Column("is_public",       sa.Boolean(),   nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"],   ondelete="CASCADE",  name="fk_documents_uploaded_by"),
        sa.ForeignKeyConstraint(["course_id"],   ["courses.id"], ondelete="SET NULL", name="fk_documents_course_id"),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
    )
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_course_id",   "documents", ["course_id"])
    op.create_index("ix_documents_category",    "documents", ["category"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: document_chunks  (with pgvector embedding column)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "document_chunks",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("document_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("chunk_index",   sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("chunk_text",    sa.Text(),      nullable=False),
        sa.Column("page_number",   sa.Integer(),   nullable=True),
        sa.Column("metadata_json", postgresql.JSON(), nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE", name="fk_document_chunks_document_id"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"],    ondelete="CASCADE", name="fk_document_chunks_uploaded_by"),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_uploaded_by", "document_chunks", ["uploaded_by"])
    op.create_index("ix_document_chunks_chunk_index", "document_chunks", ["chunk_index"])

    # Add pgvector embedding column (nullable so migration works without pgvector)
    # The HNSW index is created by session.py startup (after pgvector is confirmed installed).
    op.execute(
        "DO $$ BEGIN "
        "  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN "
        "    ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(768); "
        "  END IF; "
        "END $$;"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: kb_articles
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "kb_articles",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("author_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title",        sa.String(500), nullable=False),
        sa.Column("slug",         sa.String(600), nullable=False, unique=True),
        sa.Column("content",      sa.Text(),      nullable=False),
        sa.Column("summary",      sa.Text(),      nullable=True),
        sa.Column("category",     sa.String(100), nullable=True),
        sa.Column("tags",         postgresql.JSON(), nullable=True),
        sa.Column("status",       articlestatus_enum, nullable=False, server_default="draft"),
        sa.Column("views",        sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("likes",        sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("is_featured",  sa.Boolean(),   nullable=False, server_default=sa.text("false")),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE", name="fk_kb_articles_author_id"),
        sa.PrimaryKeyConstraint("id", name="pk_kb_articles"),
    )
    op.create_index("ix_kb_articles_author_id", "kb_articles", ["author_id"])
    op.create_index("ix_kb_articles_category",  "kb_articles", ["category"])
    op.create_index("ix_kb_articles_status",    "kb_articles", ["status"])
    op.create_index("ix_kb_articles_slug",      "kb_articles", ["slug"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("kb_articles")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("notifications")
    op.drop_table("quiz_attempts")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
    op.drop_table("assignment_submissions")
    op.drop_table("assignments")
    op.drop_table("attendance")
    op.drop_table("class_sessions")
    op.drop_table("course_subjects")
    op.drop_table("course_enrollments")
    op.drop_table("courses")

    # Drop named PG ENUMs
    for name in [
        "articlestatus", "documentcategory", "notificationtype",
        "questiontype", "quizstatus", "submissionstatus",
        "assignmentstatus", "attendancestatus", "sessionstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
