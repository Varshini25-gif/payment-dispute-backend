"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

from app.database.models.base import GUID

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dispute",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dispute_status", "dispute", ["status"])
    op.create_index("ix_dispute_type", "dispute", ["type"])
    op.create_index("ix_dispute_created_at", "dispute", ["created_at"])

    op.create_table(
        "routinglog",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("dispute_id", GUID(), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("destination", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dispute_id"], ["dispute.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_routing_log_dispute_id", "routinglog", ["dispute_id"])
    op.create_index("ix_routing_log_status", "routinglog", ["status"])
    op.create_index("ix_routing_log_dispatched_at", "routinglog", ["dispatched_at"])

    op.create_table(
        "slatracking",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("dispute_id", GUID(), nullable=False, unique=True),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sla_status", sa.String(length=50), nullable=False),
        sa.Column("breached_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dispute_id"], ["dispute.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sla_tracking_sla_due_at", "slatracking", ["sla_due_at"])
    op.create_index("ix_sla_tracking_sla_status", "slatracking", ["sla_status"])

    op.create_table(
        "jiraissue",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("dispute_id", GUID(), nullable=False),
        sa.Column("issue_key", sa.String(length=64), nullable=False, unique=True),
        sa.Column("project_key", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("url", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dispute_id"], ["dispute.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_jira_issue_dispute_id", "jiraissue", ["dispute_id"])
    op.create_index("ix_jira_issue_status", "jiraissue", ["status"])

    op.create_table(
        "confluencepost",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("dispute_id", GUID(), nullable=False),
        sa.Column("page_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=255), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dispute_id"], ["dispute.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_confluence_post_dispute_id", "confluencepost", ["dispute_id"])

    op.create_table(
        "auditlog",
        sa.Column("id", GUID(), primary_key=True, nullable=False),
        sa.Column("dispute_id", GUID(), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("field_name", sa.String(length=128), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dispute_id"], ["dispute.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_audit_log_dispute_id", "auditlog", ["dispute_id"])
    op.create_index("ix_audit_log_action", "auditlog", ["action"])
    op.create_index("ix_audit_log_created_at", "auditlog", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="auditlog")
    op.drop_index("ix_audit_log_action", table_name="auditlog")
    op.drop_index("ix_audit_log_dispute_id", table_name="auditlog")
    op.drop_table("auditlog")

    op.drop_index("ix_confluence_post_dispute_id", table_name="confluencepost")
    op.drop_table("confluencepost")

    op.drop_index("ix_jira_issue_status", table_name="jiraissue")
    op.drop_index("ix_jira_issue_dispute_id", table_name="jiraissue")
    op.drop_table("jiraissue")

    op.drop_index("ix_sla_tracking_sla_status", table_name="slatracking")
    op.drop_index("ix_sla_tracking_sla_due_at", table_name="slatracking")
    op.drop_table("slatracking")

    op.drop_index("ix_routing_log_dispatched_at", table_name="routinglog")
    op.drop_index("ix_routing_log_status", table_name="routinglog")
    op.drop_index("ix_routing_log_dispute_id", table_name="routinglog")
    op.drop_table("routinglog")

    op.drop_index("ix_dispute_created_at", table_name="dispute")
    op.drop_index("ix_dispute_type", table_name="dispute")
    op.drop_index("ix_dispute_status", table_name="dispute")
    op.drop_table("dispute")
