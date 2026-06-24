"""Generate mock disputes with related data."""

from datetime import datetime
from decimal import Decimal
from random import choice, randint
from typing import List

from sqlalchemy.orm import Session

from app.database.models.dispute import Dispute
from app.database.models.enums import DisputeStatus, DisputeType
from app.utils.faker_utils import (
    DisputeDataGenerator,
    MockDataHelper,
)


def generate_mock_disputes(session: Session, count: int = 10) -> List[Dispute]:
    """Generate mock disputes and persist to database.
    
    Args:
        session: SQLAlchemy session
        count: Number of disputes to generate
        
    Returns:
        List of created Dispute objects
    """
    disputes = []
    statuses = [DisputeStatus.NEW, DisputeStatus.OPEN, DisputeStatus.ESCALATED, DisputeStatus.RESOLVED]
    types = [DisputeType.CARD, DisputeType.ACH, DisputeType.WIRE, DisputeType.OTHER]

    for _ in range(count):
        dispute = Dispute(
            external_id=DisputeDataGenerator.generate_dispute_id(),
            status=choice(statuses),
            type=choice(types),
            amount=DisputeDataGenerator.generate_amount(),
            currency=DisputeDataGenerator.generate_currency(),
            customer_id=DisputeDataGenerator.generate_customer_id(),
            reason=DisputeDataGenerator.generate_reason(),
            created_at=MockDataHelper.generate_timestamp(days_back=60),
            updated_at=datetime.utcnow(),
        )
        disputes.append(dispute)
        session.add(dispute)

    try:
        session.commit()
        print(f"✓ Generated {count} mock disputes")
    except Exception as e:
        session.rollback()
        print(f"✗ Error generating disputes: {e}")
        raise

    return disputes
