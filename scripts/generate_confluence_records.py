"""Generate mock Confluence post records."""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.database.models.confluence_post import ConfluencePost
from app.utils.faker_utils import (
    ConfluenceDataGenerator,
    MockDataHelper,
)


def generate_mock_confluence_records(session: Session, dispute_ids: List[str], count_per_dispute: int = 1) -> List[ConfluencePost]:
    """Generate mock Confluence post records for disputes.
    
    Args:
        session: SQLAlchemy session
        dispute_ids: List of dispute IDs to create Confluence records for
        count_per_dispute: Number of Confluence posts per dispute
        
    Returns:
        List of created ConfluencePost objects
    """
    confluence_records = []

    for dispute_id in dispute_ids:
        for _ in range(count_per_dispute):
            page_id = ConfluenceDataGenerator.generate_page_id()
            publish_status = ConfluenceDataGenerator.generate_publish_status()
            
            # Only set publish-related fields if status is not pending
            last_attempted_at = None
            last_published_at = None
            failure_reason = None
            
            if publish_status == "success":
                last_published_at = MockDataHelper.generate_timestamp(days_back=10)
                last_attempted_at = last_published_at
            elif publish_status in ["failed", "retry"]:
                last_attempted_at = MockDataHelper.generate_timestamp(days_back=5)
                failure_reason = ConfluenceDataGenerator.generate_failure_reason()

            confluence_record = ConfluencePost(
                dispute_id=dispute_id,
                page_id=page_id,
                title=ConfluenceDataGenerator.generate_page_title(),
                url=ConfluenceDataGenerator.generate_confluence_url(page_id),
                excerpt=ConfluenceDataGenerator.generate_page_excerpt(),
                publish_status=publish_status,
                publish_attempts=1 if publish_status == "pending" else 1 if publish_status == "success" else 3,
                last_attempted_at=last_attempted_at,
                last_published_at=last_published_at,
                failure_reason=failure_reason,
                created_at=MockDataHelper.generate_timestamp(days_back=30),
                updated_at=datetime.utcnow(),
            )
            confluence_records.append(confluence_record)
            session.add(confluence_record)

    try:
        session.commit()
        print(f"✓ Generated {len(confluence_records)} mock Confluence records")
    except Exception as e:
        session.rollback()
        print(f"✗ Error generating Confluence records: {e}")
        raise

    return confluence_records
