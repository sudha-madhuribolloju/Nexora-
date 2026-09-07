"""create lecture_sessions, transcripts, and lecture_summaries tables

Revision ID: c0418ce059f2
Revises: c0418ce059f1
Create Date: 2026-08-20 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c0418ce059f2'
down_revision: Union[str, Sequence[str], None] = '0007_audit_logs_and_chat'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Table: lecture_sessions ──────────────────────────────────────────────
    op.create_table(
        'lecture_sessions',
        sa.Column('id', sa.String(length=255), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), server_default='Live Classroom Session', nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('teacher_id', sa.UUID(), nullable=True),
        sa.Column('teacher_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='LIVE', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lecture_sessions_status', 'lecture_sessions', ['status'], unique=False)
    op.create_index('ix_lecture_sessions_teacher_id', 'lecture_sessions', ['teacher_id'], unique=False)

    # ── Table: transcripts ───────────────────────────────────────────────────
    op.create_table(
        'transcripts',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('lecture_session_id', sa.String(length=255), nullable=False),
        sa.Column('speaker', sa.String(length=255), server_default='Teacher', nullable=False),
        sa.Column('transcript_text', sa.Text(), nullable=False),
        sa.Column('is_teacher', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sequence', sa.Integer(), server_default='0', nullable=False),
        sa.Column('chunk_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='finalized', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lecture_session_id'], ['lecture_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transcripts_lecture_session_id', 'transcripts', ['lecture_session_id'], unique=False)
    op.create_index('ix_transcripts_created_at', 'transcripts', ['created_at'], unique=False)

    # ── Table: lecture_summaries ─────────────────────────────────────────────
    op.create_table(
        'lecture_summaries',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('lecture_session_id', sa.String(length=255), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('nlp_insights', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='completed', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lecture_session_id'], ['lecture_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lecture_summaries_lecture_session_id', 'lecture_summaries', ['lecture_session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_lecture_summaries_lecture_session_id', table_name='lecture_summaries')
    op.drop_table('lecture_summaries')
    op.drop_index('ix_transcripts_created_at', table_name='transcripts')
    op.drop_index('ix_transcripts_lecture_session_id', table_name='transcripts')
    op.drop_table('transcripts')
    op.drop_index('ix_lecture_sessions_teacher_id', table_name='lecture_sessions')
    op.drop_index('ix_lecture_sessions_status', table_name='lecture_sessions')
    op.drop_table('lecture_sessions')
