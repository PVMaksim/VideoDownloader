"""create users and downloads tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-28 12:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("plan", sa.Enum("free", "pro", name="plan"), nullable=False, server_default="free"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_verification_token", "users", ["verification_token"])

    # ── downloads ─────────────────────────────────────────────────
    op.create_table(
        "downloads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "downloading", "ready", "error", name="downloadstatus"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("progress", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("video_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("filename", sa.String(500), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_downloads_id", "downloads", ["id"])
    op.create_index("ix_downloads_task_id", "downloads", ["task_id"], unique=True)
    op.create_index("ix_downloads_user_id", "downloads", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_downloads_user_id", table_name="downloads")
    op.drop_index("ix_downloads_task_id", table_name="downloads")
    op.drop_index("ix_downloads_id", table_name="downloads")
    op.drop_table("downloads")
    op.drop_index("ix_users_verification_token", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS downloadstatus")
    op.execute("DROP TYPE IF EXISTS plan")
