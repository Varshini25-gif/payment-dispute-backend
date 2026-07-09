"""add dispute query indexes

Revision ID: 0004_dispute_query_indexes
Revises: 0003_api_request_logging
Create Date: 2026-07-09 00:00:00.000000
"""

from alembic import op


revision = "0004_dispute_query_indexes"
down_revision = "0003_api_request_logging"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_dispute_status_created_at", "dispute", ["status", "created_at"])
    op.create_index("ix_dispute_customer_created_at", "dispute", ["customer_id", "created_at"])
    op.create_index("ix_dispute_currency_created_at", "dispute", ["currency", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_dispute_currency_created_at", table_name="dispute")
    op.drop_index("ix_dispute_customer_created_at", table_name="dispute")
    op.drop_index("ix_dispute_status_created_at", table_name="dispute")
