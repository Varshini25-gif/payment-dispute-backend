"""add api request logging

Revision ID: 0003_api_request_logging
Revises: 0002_confluence_publish_tracking
Create Date: 2026-06-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

from app.database.models.base import GUID


revision = "0003_api_request_logging"
down_revision = "0002_confluence_publish_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apirequestlog",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("query_string", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("request_body", sa.Text(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_api_request_log_correlation_id", "apirequestlog", ["correlation_id"])
    op.create_index("ix_api_request_log_request_id", "apirequestlog", ["request_id"])
    op.create_index("ix_api_request_log_status_code", "apirequestlog", ["status_code"])
    op.create_index("ix_api_request_log_created_at", "apirequestlog", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_api_request_log_created_at", table_name="apirequestlog")
    op.drop_index("ix_api_request_log_status_code", table_name="apirequestlog")
    op.drop_index("ix_api_request_log_request_id", table_name="apirequestlog")
    op.drop_index("ix_api_request_log_correlation_id", table_name="apirequestlog")
    op.drop_table("apirequestlog")
