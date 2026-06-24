"""Generate mock SLA tracking data."""

from datetime import datetime
from typing import List
from random import choice

from sqlalchemy.orm import Session

from app.database.models.sla_tracking import SlaTracking
from app.database.models.enums import SlaStatus
from app.utils.faker_utils import (
    SlaDataGenerator,
    MockDataHelper,
)


def generate_mock_sla_records(session: Session, dispute_ids: List[str]) -> List[SlaTracking]:
    """Generate mock SLA tracking records for disputes.
    
    Args:
        session: SQLAlchemy session
        dispute_ids: List of dispute IDs to create SLA records for
        
    Returns:
        List of created SlaTracking objects
    """
    sla_records = []
    sla_statuses = [SlaStatus.ON_TRACK, SlaStatus.AT_RISK, SlaStatus.BREACHED]

    for dispute_id in dispute_ids:
        # Generate random SLA data for each dispute
        sla_due_date = SlaDataGenerator.generate_sla_due_date(days_from_now=30)
        sla_status = choice(sla_statuses)
        
        # If breached, set breached_at to a date before sla_due_date
        breached_at = None
        breach_detected = False
        if sla_status == SlaStatus.BREACHED:
            breach_detected = True
            breached_at = MockDataHelper.generate_timestamp(days_back=5)

        # If at_risk, generate escalation info
        escalation_flag = False
        escalation_reason = None
        if sla_status == SlaStatus.AT_RISK:
            escalation_flag = True
            escalation_reason = SlaDataGenerator.generate_escalation_reason()

        sla_record = SlaTracking(
            dispute_id=dispute_id,
            sla_due_at=sla_due_date,
            sla_status=sla_status,
            breached_at=breached_at,
            breach_detected=breach_detected,
            escalation_flag=escalation_flag,
            escalation_reason=escalation_reason,
            response_hours=SlaDataGenerator.generate_response_hours(),
            resolution_hours=SlaDataGenerator.generate_resolution_hours(),
            notes=f"SLA tracking for dispute {dispute_id}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        sla_records.append(sla_record)
        session.add(sla_record)

    try:
        session.commit()
        print(f"✓ Generated {len(sla_records)} mock SLA records")
    except Exception as e:
        session.rollback()
        print(f"✗ Error generating SLA records: {e}")
        raise

    return sla_records
