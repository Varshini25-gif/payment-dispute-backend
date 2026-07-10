from enum import Enum


class DisputeStatus(str, Enum):
    NEW = "new"
    OPEN = "open"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputeType(str, Enum):
    CARD = "card"
    ACH = "ach"
    WIRE = "wire"
    OTHER = "other"


class RoutingStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


class SlaStatus(str, Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BREACHED = "breached"


# Backward-compatible alias for legacy tests/imports.
SlaStatus.RESOLVED = SlaStatus.BREACHED


class JiraIssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class JiraPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    COMMENTED = "commented"


class SourceSystem(str, Enum):
    CUSTOMER = "customer"
    INTERNAL = "internal"
    PARTNER = "partner"
