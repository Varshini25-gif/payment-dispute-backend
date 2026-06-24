"""Faker utilities for generating realistic mock data."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from random import choice, randint, random

from faker import Faker

fake = Faker()


class SourceSystemGenerator:
    """Generate mock source system data."""

    SOURCE_SYSTEMS = ["customer", "internal", "partner"]

    @staticmethod
    def generate_source_system() -> str:
        """Generate a random source system."""
        return choice(SourceSystemGenerator.SOURCE_SYSTEMS)


class DisputeDataGenerator:
    """Generate mock dispute data."""

    DISPUTE_REASONS = [
        "Unauthorized transaction",
        "Duplicate charge",
        "Billing error",
        "Goods not received",
        "Service not provided",
        "Item not as described",
        "Refund not processed",
        "Quality issue",
        "Payment not authorized",
        "Incorrect amount charged",
    ]

    CUSTOMER_INDUSTRIES = [
        "Technology",
        "Healthcare",
        "Finance",
        "Retail",
        "Manufacturing",
        "Education",
        "Transportation",
        "Hospitality",
        "Real Estate",
        "Entertainment",
    ]

    @staticmethod
    def generate_dispute_id() -> str:
        """Generate a unique dispute ID."""
        return f"DISP-{fake.bothify(text='##??##??##', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ').upper()}"

    @staticmethod
    def generate_customer_id() -> str:
        """Generate a customer ID."""
        return f"CUST-{fake.numerify(text='###########')}"

    @staticmethod
    def generate_amount() -> Decimal:
        """Generate a dispute amount between 10 and 10000."""
        return Decimal(str(round(randint(1000, 1000000) / 100, 2)))

    @staticmethod
    def generate_reason() -> str:
        """Generate a random dispute reason."""
        return choice(DisputeDataGenerator.DISPUTE_REASONS)

    @staticmethod
    def generate_currency() -> str:
        """Generate a currency code."""
        return choice(["USD", "EUR", "GBP", "CAD", "AUD", "JPY"])


class RoutingDataGenerator:
    """Generate mock routing log data."""

    DESTINATIONS = [
        "jira_queue",
        "confluence_wiki",
        "internal_review",
        "external_partner",
        "escalation_queue",
        "automated_resolution",
    ]

    ROUTING_STATUSES = ["pending", "sent", "failed", "retry"]

    @staticmethod
    def generate_destination() -> str:
        """Generate a routing destination."""
        return choice(RoutingDataGenerator.DESTINATIONS)

    @staticmethod
    def generate_routing_details() -> str:
        """Generate routing details."""
        return fake.sentence(nb_words=10)

    @staticmethod
    def generate_routing_status() -> str:
        """Generate a routing status."""
        return choice(RoutingDataGenerator.ROUTING_STATUSES)


class SlaDataGenerator:
    """Generate mock SLA tracking data."""

    ESCALATION_REASONS = [
        "VIP customer",
        "High dispute amount",
        "Repeat offender",
        "Regulatory escalation",
        "Media attention",
        "Complex case",
        "Time sensitive",
        "Customer complaint",
    ]

    SLA_STATUSES = ["on_track", "at_risk", "breached"]

    @staticmethod
    def generate_sla_due_date(days_from_now: int = 30) -> datetime:
        """Generate an SLA due date."""
        return datetime.utcnow() + timedelta(days=days_from_now)

    @staticmethod
    def generate_escalation_reason() -> str:
        """Generate an escalation reason."""
        return choice(SlaDataGenerator.ESCALATION_REASONS)

    @staticmethod
    def generate_response_hours() -> Decimal:
        """Generate response hours (0-24)."""
        return Decimal(str(round(random() * 24, 2)))

    @staticmethod
    def generate_resolution_hours() -> Decimal:
        """Generate resolution hours (0-720 = 30 days)."""
        return Decimal(str(round(random() * 720, 2)))

    @staticmethod
    def generate_sla_status() -> str:
        """Generate an SLA status."""
        return choice(SlaDataGenerator.SLA_STATUSES)


class JiraDataGenerator:
    """Generate mock Jira issue data."""

    JIRA_PROJECTS = ["DIS", "PAY", "SUP", "OPS", "BIL"]
    JIRA_PRIORITIES = ["low", "medium", "high", "critical"]
    JIRA_STATUSES = ["open", "in_progress", "resolved", "closed"]

    @staticmethod
    def generate_issue_key() -> str:
        """Generate a Jira issue key."""
        project = choice(JiraDataGenerator.JIRA_PROJECTS)
        return f"{project}-{fake.numerify(text='#####')}"

    @staticmethod
    def generate_jira_url(issue_key: str) -> str:
        """Generate a Jira URL."""
        return f"https://jira.company.com/browse/{issue_key}"

    @staticmethod
    def generate_issue_summary() -> str:
        """Generate a Jira issue summary."""
        prefixes = [
            "Payment dispute",
            "Customer complaint",
            "Transaction issue",
            "Billing problem",
            "Refund request",
        ]
        return f"{choice(prefixes)}: {fake.sentence(nb_words=6)}"

    @staticmethod
    def generate_priority() -> str:
        """Generate a Jira priority."""
        return choice(JiraDataGenerator.JIRA_PRIORITIES)

    @staticmethod
    def generate_status() -> str:
        """Generate a Jira status."""
        return choice(JiraDataGenerator.JIRA_STATUSES)


class ConfluenceDataGenerator:
    """Generate mock Confluence post data."""

    PUBLISH_STATUSES = ["pending", "success", "failed", "retry"]

    @staticmethod
    def generate_page_id() -> str:
        """Generate a Confluence page ID."""
        return f"PAGE-{fake.numerify(text='##########')}"

    @staticmethod
    def generate_confluence_url(page_id: str) -> str:
        """Generate a Confluence URL."""
        return f"https://confluence.company.com/pages/viewpage.action?pageId={page_id}"

    @staticmethod
    def generate_page_title() -> str:
        """Generate a Confluence page title."""
        return f"Dispute Case: {fake.word().title()} - {fake.numerify(text='####')}"

    @staticmethod
    def generate_page_excerpt() -> str:
        """Generate a Confluence page excerpt."""
        return fake.paragraph(nb_sentences=3)

    @staticmethod
    def generate_failure_reason() -> str:
        """Generate a failure reason for publishing."""
        reasons = [
            "Authentication failed",
            "Page already exists",
            "Space not accessible",
            "Invalid page format",
            "Network timeout",
        ]
        return choice(reasons)

    @staticmethod
    def generate_publish_status() -> str:
        """Generate a publish status."""
        return choice(ConfluenceDataGenerator.PUBLISH_STATUSES)


class MockDataHelper:
    """Helper class for generating related mock data."""

    @staticmethod
    def generate_timestamp(days_back: int = 30) -> datetime:
        """Generate a timestamp within the last N days."""
        return datetime.utcnow() - timedelta(days=randint(0, days_back))

    @staticmethod
    def generate_future_timestamp(days_ahead: int = 30) -> datetime:
        """Generate a timestamp N days in the future."""
        return datetime.utcnow() + timedelta(days=randint(1, days_ahead))

    @staticmethod
    def generate_actor_name() -> str:
        """Generate an actor name (user)."""
        return fake.user_name()

    @staticmethod
    def generate_email() -> str:
        """Generate an email address."""
        return fake.email()

    @staticmethod
    def generate_phone() -> str:
        """Generate a phone number."""
        return fake.phone_number()
