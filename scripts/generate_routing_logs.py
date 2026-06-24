"""Generate mock routing logs with related data."""

from datetime import datetime
from typing import List
from random import choice

from sqlalchemy.orm import Session

from app.database.models.routing_log import RoutingLog
from app.database.models.enums import SourceSystem, RoutingStatus
from app.utils.faker_utils import (
    RoutingDataGenerator,
    MockDataHelper,
)


def generate_mock_routing_logs(session: Session, dispute_ids: List[str], count_per_dispute: int = 3) -> List[RoutingLog]:
    """Generate mock routing logs for disputes.
    
    Args:
        session: SQLAlchemy session
        dispute_ids: List of dispute IDs to create routing logs for
        count_per_dispute: Number of routing logs per dispute
        
    Returns:
        List of created RoutingLog objects
    """
    routing_logs = []
    source_systems = [SourceSystem.INTERNAL, SourceSystem.CUSTOMER, SourceSystem.PARTNER]
    routing_statuses = [RoutingStatus.PENDING, RoutingStatus.SENT, RoutingStatus.FAILED, RoutingStatus.RETRY]

    for dispute_id in dispute_ids:
        for _ in range(count_per_dispute):
            routing_log = RoutingLog(
                dispute_id=dispute_id,
                source_system=choice(source_systems),
                destination=RoutingDataGenerator.generate_destination(),
                status=choice(routing_statuses),
                dispatched_at=MockDataHelper.generate_timestamp(days_back=30),
                details=RoutingDataGenerator.generate_routing_details(),
                created_at=datetime.utcnow(),
            )
            routing_logs.append(routing_log)
            session.add(routing_log)

    try:
        session.commit()
        print(f"✓ Generated {len(routing_logs)} mock routing logs")
    except Exception as e:
        session.rollback()
        print(f"✗ Error generating routing logs: {e}")
        raise

    return routing_logs
