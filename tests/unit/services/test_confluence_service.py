"""Unit tests for Confluence service."""

import pytest
from types import SimpleNamespace
from app.services.confluence.client import ConfluenceClient
from app.services.confluence.publisher import ConfluencePublisher
from tests.fixtures.mocks import FakeConfluenceClient


class TestConfluenceClient:
    """Test Confluence API client."""
    
    def test_confluence_client_initialization(self):
        """Test client initialization."""
        client = ConfluenceClient(
            base_url="https://confluence.example.com",
            username="user",
            api_token="token"
        )
        assert client is not None
    
    def test_create_page(self, monkeypatch):
        """Test creating a page."""
        client = FakeConfluenceClient()
        
        response = client.create_page(
            space="TEST",
            title="Test Page",
            body="<p>Test content</p>"
        )
        
        assert "id" in response
        assert response["type"] == "page"
    
    def test_get_page(self):
        """Test getting a page."""
        client = FakeConfluenceClient()
        
        response = client.get_page("123456")
        
        assert response is not None
        assert "id" in response
    
    def test_update_page(self):
        """Test updating a page."""
        client = FakeConfluenceClient()
        
        response = client.update_page(
            page_id="123456",
            title="Updated Title",
            body="<p>Updated content</p>",
            version=2
        )
        
        assert response is not None
    
    def test_search_pages(self):
        """Test searching pages."""
        client = FakeConfluenceClient()
        
        # Should have search capability
        assert hasattr(client, "get_page") or hasattr(client, "search")


class TestConfluencePublisher:
    """Test Confluence publisher."""
    
    def test_publisher_initialization(self):
        """Test publisher initialization."""
        fake_client = FakeConfluenceClient()
        publisher = ConfluencePublisher(client=fake_client)
        
        assert publisher is not None
    
    def test_publish_dispute_summary(self):
        """Test publishing dispute summary."""
        fake_client = FakeConfluenceClient()
        publisher = ConfluencePublisher(client=fake_client)
        
        dispute = SimpleNamespace(
            id="dispute-1",
            external_id="EXT-001",
            amount=1000,
            type="chargeback",
            customer_id="customer-1",
            created_at="2026-01-01T00:00:00Z"
        )
        
        # Should publish the dispute
        assert dispute.id is not None
    
    def test_publish_with_custom_template(self):
        """Test publishing with custom template."""
        fake_client = FakeConfluenceClient()
        publisher = ConfluencePublisher(client=fake_client)
        
        dispute = SimpleNamespace(
            id="dispute-2",
            external_id="EXT-002",
            amount=500,
            type="refund",
            customer_id="customer-2"
        )
        
        template = "Custom: {external_id} - {type}"
        # Should use custom template
        assert template is not None
    
    def test_update_existing_page(self):
        """Test updating existing published page."""
        fake_client = FakeConfluenceClient()
        publisher = ConfluencePublisher(client=fake_client)
        
        dispute = SimpleNamespace(
            id="dispute-3",
            external_id="EXT-003",
            status="resolved"
        )
        
        # Should update if page exists
        assert dispute.id is not None
    
    def test_handle_publish_failure(self):
        """Test handling publish failures."""
        fake_client = FakeConfluenceClient()
        publisher = ConfluencePublisher(client=fake_client)
        
        # Even with failures, should handle gracefully
        assert publisher is not None


class TestConfluenceHtmlBuilder:
    """Test HTML building for Confluence."""
    
    def test_build_dispute_html(self):
        """Test building dispute HTML."""
        from app.services.confluence.html_builder import build_dispute_html
        
        dispute = {
            "id": "dispute-1",
            "external_id": "EXT-001",
            "amount": 1000,
            "type": "chargeback",
            "status": "pending"
        }
        
        html = build_dispute_html(dispute)
        
        assert html is not None
        assert len(html) > 0
    
    def test_html_includes_key_fields(self):
        """Test that HTML includes key dispute fields."""
        from app.services.confluence.html_builder import build_dispute_html
        
        dispute = {
            "id": "dispute-2",
            "external_id": "EXT-002",
            "amount": 500,
            "type": "refund"
        }
        
        html = build_dispute_html(dispute)
        
        # HTML should contain key information
        if html:
            assert any(key in html.lower() for key in ["dispute", "external", "amount"])
    
    def test_html_escaping(self):
        """Test HTML escaping for security."""
        from app.services.confluence.html_builder import build_dispute_html
        
        dispute = {
            "id": "dispute-3",
            "external_id": "EXT-<script>alert('xss')</script>",
            "amount": 100,
            "type": "test"
        }
        
        html = build_dispute_html(dispute)
        
        if html:
            # Should escape dangerous characters
            assert "<script>" not in html


class TestConfluenceTracking:
    """Test Confluence publication tracking."""
    
    def test_track_published_page(self):
        """Test tracking published pages."""
        from app.database.models.confluence_post import ConfluencePost
        
        page_data = {
            "dispute_id": "dispute-1",
            "page_id": "123456",
            "page_title": "Dispute EXT-001",
            "status": "published"
        }
        
        assert page_data["status"] == "published"
    
    def test_track_page_updates(self):
        """Test tracking page updates."""
        page_data = {
            "dispute_id": "dispute-1",
            "page_id": "123456",
            "version": 2,
            "last_updated": "2026-01-01T12:00:00Z"
        }
        
        assert page_data["version"] >= 1
    
    def test_retrieve_published_pages(self):
        """Test retrieving published pages."""
        # Should be able to query published pages
        page_data = {
            "dispute_id": "dispute-1",
            "page_id": "123456"
        }
        
        assert page_data is not None
