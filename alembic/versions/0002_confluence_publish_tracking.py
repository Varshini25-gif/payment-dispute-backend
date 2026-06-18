"""add confluence publish tracking

Revision ID: 0002_confluence_publish_tracking
Revises: 0001_initial
Create Date: 2026-06-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_confluence_publish_tracking"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("confluencepost") as batch_op:
        batch_op.alter_column("page_id", existing_type=sa.String(length=128), nullable=True)
        batch_op.add_column(sa.Column("publish_status", sa.String(length=32), nullable=False, server_default="pending"))
        batch_op.add_column(sa.Column("publish_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_published_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("failure_reason", sa.Text(), nullable=True))

    op.create_index("ix_confluence_post_publish_status", "confluencepost", ["publish_status"])


def downgrade() -> None:
    op.drop_index("ix_confluence_post_publish_status", table_name="confluencepost")

    with op.batch_alter_table("confluencepost") as batch_op:
        batch_op.drop_column("failure_reason")
        batch_op.drop_column("last_published_at")
        batch_op.drop_column("last_attempted_at")
        batch_op.drop_column("publish_attempts")
        batch_op.drop_column("publish_status")
        batch_op.alter_column("page_id", existing_type=sa.String(length=128), nullable=False)