"""Generate mock Jira issue records."""

from datetime import datetime
from typing import List
from random import choice

from sqlalchemy.orm import Session

from app.database.models.jira_issue import JiraIssue
from app.database.models.enums import JiraIssueStatus, JiraPriority
from app.utils.faker_utils import (
    JiraDataGenerator,
    MockDataHelper,
)


def generate_mock_jira_records(session: Session, dispute_ids: List[str], count_per_dispute: int = 1) -> List[JiraIssue]:
    """Generate mock Jira issue records for disputes.
    
    Args:
        session: SQLAlchemy session
        dispute_ids: List of dispute IDs to create Jira records for
        count_per_dispute: Number of Jira issues per dispute
        
    Returns:
        List of created JiraIssue objects
    """
    jira_records = []
    statuses = [JiraIssueStatus.OPEN, JiraIssueStatus.IN_PROGRESS, JiraIssueStatus.RESOLVED, JiraIssueStatus.CLOSED]
    priorities = [JiraPriority.LOW, JiraPriority.MEDIUM, JiraPriority.HIGH, JiraPriority.CRITICAL]

    for dispute_id in dispute_ids:
        for _ in range(count_per_dispute):
            issue_key = JiraDataGenerator.generate_issue_key()
            
            jira_record = JiraIssue(
                dispute_id=dispute_id,
                issue_key=issue_key,
                project_key=issue_key.split("-")[0],
                status=choice(statuses),
                priority=choice(priorities),
                url=JiraDataGenerator.generate_jira_url(issue_key),
                summary=JiraDataGenerator.generate_issue_summary(),
                created_at=MockDataHelper.generate_timestamp(days_back=30),
                updated_at=datetime.utcnow(),
            )
            jira_records.append(jira_record)
            session.add(jira_record)

    try:
        session.commit()
        print(f"✓ Generated {len(jira_records)} mock Jira records")
    except Exception as e:
        session.rollback()
        print(f"✗ Error generating Jira records: {e}")
        raise

    return jira_records
