from __future__ import annotations

from datetime import datetime
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