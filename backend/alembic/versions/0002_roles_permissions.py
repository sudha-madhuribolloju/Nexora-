"""Migration 001 — Create RBAC tables: roles, permissions, role_permissions, user_roles.

Revision ID : 0002_roles_permissions
Revises     : 0001_upgrade_users_uuid
Create Date : 2026-07-23

Design decisions
────────────────
• All PKs use gen_random_uuid() as server_default so psql-direct inserts are
  also UUID-safe.
• Explicit named constraints (pk_, uq_, fk_, ix_) make `alembic check` diffs
  readable and allow targeted ALTER in future migrations.
• System roles and default permissions are seeded at the END of the migration
  inside the same transaction — if any row insert fails, the whole migration
  rolls back, leaving the DB in a clean state.
• ON CONFLICT (name) DO NOTHING makes the seed re-entrant: running the
  migration twice (e.g. on a restored snapshot) won't error.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_roles_permissions"
down_revision: Union[str, Sequence[str], None] = "0001_upgrade_users_uuid"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: roles
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_system_role",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_name",           "roles", ["name"])
    op.create_index("ix_roles_is_system_role",  "roles", ["is_system_role"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: permissions
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("action",   sa.String(50),  nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_permissions"),
        sa.UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_index("ix_permissions_action",   "permissions", ["action"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: role_permissions  (M2M join)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "role_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("role_id",       postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
            name="fk_role_permissions_role_id",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            ondelete="CASCADE",
            name="fk_role_permissions_permission_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_role_permissions"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )
    op.create_index("ix_role_permissions_role_id",       "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE: user_roles  (M2M join)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "user_roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # granted_by is a bare UUID — no FK — so hard-deleting the granter
        # does not break the audit row.
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_user_roles_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
            name="fk_user_roles_role_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    # ══════════════════════════════════════════════════════════════════════════
    # SEED: System Roles
    # ══════════════════════════════════════════════════════════════════════════
    op.execute(
        """
        INSERT INTO roles (name, description, is_system_role)
        VALUES
          ('super_admin',  'Full system access across all schools',     true),
          ('school_admin', 'Full administrative access within a school', true),
          ('teacher',      'Teaching staff access',                      true),
          ('student',      'Student access',                             true),
          ('parent',       'Parent / guardian access',                   true),
          ('staff',        'Non-teaching staff access',                  true)
        ON CONFLICT (name) DO NOTHING;
        """
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SEED: Default Permissions
    # ══════════════════════════════════════════════════════════════════════════
    op.execute(
        """
        INSERT INTO permissions (resource, action, description)
        VALUES
          ('users',           'manage',  'Create, update, deactivate user accounts'),
          ('roles',           'manage',  'Create, assign, and revoke roles'),
          ('schools',         'manage',  'Create and configure schools'),
          ('students',        'read',    'View student profiles and records'),
          ('students',        'write',   'Create and update student records'),
          ('students',        'delete',  'Soft-delete student records'),
          ('teachers',        'read',    'View teacher profiles'),
          ('teachers',        'write',   'Create and update teacher records'),
          ('teachers',        'delete',  'Soft-delete teacher records'),
          ('parents',         'read',    'View parent / guardian profiles'),
          ('parents',         'write',   'Create and update parent records'),
          ('attendance',      'read',    'View attendance records'),
          ('attendance',      'write',   'Mark and edit attendance'),
          ('timetables',      'read',    'View class timetables'),
          ('timetables',      'write',   'Create and update timetables'),
          ('exams',           'read',    'View exam schedules and results'),
          ('exams',           'write',   'Create exams and enter results'),
          ('documents',       'read',    'View uploaded documents'),
          ('documents',       'write',   'Upload and manage documents'),
          ('notifications',   'read',    'View notifications'),
          ('notifications',   'write',   'Send notifications'),
          ('ai',              'use',     'Access AI chat and analysis features'),
          ('knowledge_base',  'read',    'Search the knowledge base'),
          ('knowledge_base',  'write',   'Upload and manage knowledge sources'),
          ('reports',         'read',    'View analytics and reports'),
          ('audit_logs',      'read',    'View audit logs')
        ON CONFLICT (resource, action) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
