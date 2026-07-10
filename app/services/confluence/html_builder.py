from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from app.services.confluence.templates import (
    render_dispute_details,
    render_footer,
    render_header,
    render_resolution_notes,
)


def build_resolution_html(dispute: Any, *, published_at: datetime) -> str:
    parts = [
        render_header(getattr(dispute, "external_id", "UNKNOWN"), published_at),
        render_dispute_details(dispute),
        render_resolution_notes(dispute),
        render_footer(),
    ]
    return "".join(parts)


def build_page_title(dispute: Any) -> str:
    external_id = getattr(dispute, "external_id", "UNKNOWN")
    return f"Dispute Case Summary - {external_id}"


def build_dispute_html(dispute: Any) -> str:
    """Backward-compatible lightweight HTML renderer used by legacy tests."""
    if isinstance(dispute, dict):
        get_value = dispute.get
    else:
        get_value = lambda key, default=None: getattr(dispute, key, default)

    external_id = escape(str(get_value("external_id", "UNKNOWN")))
    dispute_id = escape(str(get_value("id", "")))
    amount = escape(str(get_value("amount", "")))
    dispute_type = escape(str(get_value("type", "other")))
    status = escape(str(get_value("status", "")))

    return (
        "<h1>Dispute Summary</h1>"
        f"<p><strong>Dispute ID:</strong> {dispute_id}</p>"
        f"<p><strong>External ID:</strong> {external_id}</p>"
        f"<p><strong>Amount:</strong> {amount}</p>"
        f"<p><strong>Type:</strong> {dispute_type}</p>"
        f"<p><strong>Status:</strong> {status}</p>"
    )