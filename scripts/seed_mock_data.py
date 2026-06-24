"""Seed mock data into the database with CLI commands."""

import sys
from typing import Optional

import click
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 1)[0] + '/..')

from app.database.session import SessionLocal
from app.database.connection import get_engine
from scripts.generate_disputes import generate_mock_disputes
from scripts.generate_routing_logs import generate_mock_routing_logs
from scripts.generate_sla_data import generate_mock_sla_records
from scripts.generate_jira_records import generate_mock_jira_records
from scripts.generate_confluence_records import generate_mock_confluence_records


def get_session() -> Session:
    """Get a database session."""
    session = SessionLocal(bind=get_engine())
    return session


@click.group()
def cli():
    """Seed mock data into the payment dispute database."""
    pass


@cli.command()
@click.option('--count', default=10, help='Number of disputes to generate')
def seed_disputes(count: int):
    """Generate mock dispute records.
    
    Args:
        count: Number of disputes to generate (default: 10)
    """
    session = get_session()
    try:
        disputes = generate_mock_disputes(session, count=count)
        click.echo(f"✓ Successfully generated {len(disputes)} disputes")
    except Exception as e:
        click.echo(f"✗ Failed to generate disputes: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dispute-count', default=10, help='Number of disputes to generate')
@click.option('--routing-per-dispute', default=3, help='Routing logs per dispute')
def seed_routing_logs(dispute_count: int, routing_per_dispute: int):
    """Generate mock routing log records.
    
    Args:
        dispute_count: Number of disputes to create routing logs for
        routing_per_dispute: Number of routing logs per dispute
    """
    session = get_session()
    try:
        # Generate disputes first
        disputes = generate_mock_disputes(session, count=dispute_count)
        dispute_ids = [d.id for d in disputes]
        
        # Generate routing logs
        routing_logs = generate_mock_routing_logs(
            session, 
            dispute_ids=dispute_ids, 
            count_per_dispute=routing_per_dispute
        )
        click.echo(f"✓ Successfully generated {len(routing_logs)} routing logs")
    except Exception as e:
        click.echo(f"✗ Failed to generate routing logs: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dispute-count', default=10, help='Number of disputes to generate')
def seed_sla_records(dispute_count: int):
    """Generate mock SLA tracking records.
    
    Args:
        dispute_count: Number of disputes to create SLA records for
    """
    session = get_session()
    try:
        # Generate disputes first
        disputes = generate_mock_disputes(session, count=dispute_count)
        dispute_ids = [d.id for d in disputes]
        
        # Generate SLA records
        sla_records = generate_mock_sla_records(session, dispute_ids=dispute_ids)
        click.echo(f"✓ Successfully generated {len(sla_records)} SLA records")
    except Exception as e:
        click.echo(f"✗ Failed to generate SLA records: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dispute-count', default=10, help='Number of disputes to generate')
@click.option('--jira-per-dispute', default=1, help='Jira issues per dispute')
def seed_jira_records(dispute_count: int, jira_per_dispute: int):
    """Generate mock Jira issue records.
    
    Args:
        dispute_count: Number of disputes to create Jira records for
        jira_per_dispute: Number of Jira issues per dispute
    """
    session = get_session()
    try:
        # Generate disputes first
        disputes = generate_mock_disputes(session, count=dispute_count)
        dispute_ids = [d.id for d in disputes]
        
        # Generate Jira records
        jira_records = generate_mock_jira_records(
            session, 
            dispute_ids=dispute_ids, 
            count_per_dispute=jira_per_dispute
        )
        click.echo(f"✓ Successfully generated {len(jira_records)} Jira records")
    except Exception as e:
        click.echo(f"✗ Failed to generate Jira records: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dispute-count', default=10, help='Number of disputes to generate')
@click.option('--confluence-per-dispute', default=1, help='Confluence posts per dispute')
def seed_confluence_records(dispute_count: int, confluence_per_dispute: int):
    """Generate mock Confluence post records.
    
    Args:
        dispute_count: Number of disputes to create Confluence records for
        confluence_per_dispute: Number of Confluence posts per dispute
    """
    session = get_session()
    try:
        # Generate disputes first
        disputes = generate_mock_disputes(session, count=dispute_count)
        dispute_ids = [d.id for d in disputes]
        
        # Generate Confluence records
        confluence_records = generate_mock_confluence_records(
            session, 
            dispute_ids=dispute_ids, 
            count_per_dispute=confluence_per_dispute
        )
        click.echo(f"✓ Successfully generated {len(confluence_records)} Confluence records")
    except Exception as e:
        click.echo(f"✗ Failed to generate Confluence records: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dispute-count', default=10, help='Number of disputes to generate')
@click.option('--routing-per-dispute', default=3, help='Routing logs per dispute')
@click.option('--jira-per-dispute', default=1, help='Jira issues per dispute')
@click.option('--confluence-per-dispute', default=1, help='Confluence posts per dispute')
def seed_all(
    dispute_count: int, 
    routing_per_dispute: int, 
    jira_per_dispute: int,
    confluence_per_dispute: int
):
    """Generate all mock data (disputes, routing, SLA, Jira, Confluence).
    
    Args:
        dispute_count: Number of disputes to generate
        routing_per_dispute: Number of routing logs per dispute
        jira_per_dispute: Number of Jira issues per dispute
        confluence_per_dispute: Number of Confluence posts per dispute
    """
    session = get_session()
    try:
        click.echo("🚀 Starting comprehensive mock data seeding...\n")
        
        # Generate disputes
        click.echo(f"📝 Generating {dispute_count} disputes...")
        disputes = generate_mock_disputes(session, count=dispute_count)
        dispute_ids = [d.id for d in disputes]
        click.echo()
        
        # Generate routing logs
        click.echo(f"📤 Generating {dispute_count * routing_per_dispute} routing logs...")
        generate_mock_routing_logs(session, dispute_ids=dispute_ids, count_per_dispute=routing_per_dispute)
        click.echo()
        
        # Generate SLA records
        click.echo(f"⏱️  Generating {dispute_count} SLA records...")
        generate_mock_sla_records(session, dispute_ids=dispute_ids)
        click.echo()
        
        # Generate Jira records
        click.echo(f"🐛 Generating {dispute_count * jira_per_dispute} Jira records...")
        generate_mock_jira_records(session, dispute_ids=dispute_ids, count_per_dispute=jira_per_dispute)
        click.echo()
        
        # Generate Confluence records
        click.echo(f"📚 Generating {dispute_count * confluence_per_dispute} Confluence records...")
        generate_mock_confluence_records(session, dispute_ids=dispute_ids, count_per_dispute=confluence_per_dispute)
        click.echo()
        
        click.echo("✅ Successfully seeded all mock data!")
        click.echo(f"\n📊 Summary:")
        click.echo(f"   - Disputes: {dispute_count}")
        click.echo(f"   - Routing logs: {dispute_count * routing_per_dispute}")
        click.echo(f"   - SLA records: {dispute_count}")
        click.echo(f"   - Jira records: {dispute_count * jira_per_dispute}")
        click.echo(f"   - Confluence records: {dispute_count * confluence_per_dispute}")
        
    except Exception as e:
        click.echo(f"✗ Failed to seed data: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dispute-count', default=10, help='Number of disputes to generate')
def clean_and_seed(dispute_count: int):
    """Clean all mock data and reseed the database.
    
    Args:
        dispute_count: Number of disputes to generate
    """
    session = get_session()
    try:
        click.echo("🗑️  Cleaning existing mock data...")
        
        # Delete all records in reverse order of dependencies
        from app.database.models.routing_log import RoutingLog
        from app.database.models.sla_tracking import SlaTracking
        from app.database.models.jira_issue import JiraIssue
        from app.database.models.confluence_post import ConfluencePost
        from app.database.models.audit_log import AuditLog
        from app.database.models.dispute import Dispute
        
        session.query(RoutingLog).delete()
        session.query(SlaTracking).delete()
        session.query(JiraIssue).delete()
        session.query(ConfluencePost).delete()
        session.query(AuditLog).delete()
        session.query(Dispute).delete()
        session.commit()
        click.echo("✓ Cleaned existing data\n")
        
        # Now seed all data
        click.echo(f"📝 Generating {dispute_count} disputes...")
        disputes = generate_mock_disputes(session, count=dispute_count)
        dispute_ids = [d.id for d in disputes]
        click.echo()
        
        click.echo("📤 Generating routing logs...")
        generate_mock_routing_logs(session, dispute_ids=dispute_ids, count_per_dispute=3)
        click.echo()
        
        click.echo("⏱️  Generating SLA records...")
        generate_mock_sla_records(session, dispute_ids=dispute_ids)
        click.echo()
        
        click.echo("🐛 Generating Jira records...")
        generate_mock_jira_records(session, dispute_ids=dispute_ids, count_per_dispute=1)
        click.echo()
        
        click.echo("📚 Generating Confluence records...")
        generate_mock_confluence_records(session, dispute_ids=dispute_ids, count_per_dispute=1)
        click.echo()
        
        click.echo("✅ Successfully cleaned and reseeded the database!")
        
    except Exception as e:
        click.echo(f"✗ Failed to clean and seed data: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    cli()
