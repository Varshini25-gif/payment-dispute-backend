from types import SimpleNamespace

from app.database.models.enums import DisputeStatus
from app.services.dispute.routing_service import DisputeRoutingService


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        return None


def test_routing_service_assigns_queue_priority_and_escalation() -> None:
    dispute = SimpleNamespace(
        id="dispute-1",
        amount=15000,
        type="chargeback",
        customer_id="vip-1",
        reason="fraud case",
        status=DisputeStatus.NEW,
    )

    result = DisputeRoutingService().route_dispute(dispute, persist=False)

    assert result["queue"] == "high_value"
    assert result["priority"] == "critical"
    assert result["escalated"] is True
    assert result["status"] == DisputeStatus.ESCALATED


def test_routing_service_persists_routing_log() -> None:
    dispute = SimpleNamespace(
        id="dispute-2",
        amount=250,
        type="other",
        customer_id="customer-1",
        reason="normal review",
        status=DisputeStatus.NEW,
    )
    session = FakeSession()

    result = DisputeRoutingService().route_dispute(dispute, db=session)

    assert session.committed is True
    assert len(session.added) == 1
    assert result["routing_log"] is session.added[0]
    assert result["queue"] == "standard"
