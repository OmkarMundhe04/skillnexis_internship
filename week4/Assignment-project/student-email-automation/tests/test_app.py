"""
Unit and integration tests for the FastAPI Web Dashboard backend (app.py).
"""

import io
import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """Create a TestClient for testing FastAPI endpoints."""
    return TestClient(app)


def test_serve_dashboard(client):
    """Verify that GET / returns the HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MailPulse" in response.text
    assert "Student Email Automation" in response.text


def test_api_status(client):
    """Verify GET /api/status returns expected metadata structure."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "sender_email" in data
    assert "smtp_server" in data
    assert "valid_count" in data
    assert "skipped_count" in data
    assert "has_credentials" in data


def test_api_students(client):
    """Verify GET /api/students parses recipient data properly."""
    response = client.get("/api/students")
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "skipped" in data
    assert isinstance(data["valid"], list)
    assert isinstance(data["skipped"], list)


def test_api_template(client):
    """Verify GET /api/template returns raw HTML and personalized preview."""
    response = client.get("/api/template")
    assert response.status_code == 200
    data = response.json()
    assert "raw_html" in data
    assert "sample_preview" in data
    assert "Alex Morgan" in data["sample_preview"]


def test_api_template_update_empty(client):
    """Verify POST /api/template rejects empty templates."""
    response = client.post("/api/template", json={"html": "   "})
    assert response.status_code == 400


def test_api_upload_csv_invalid_extension(client):
    """Verify POST /api/upload-csv rejects non-CSV files."""
    file_content = b"not a csv"
    response = client.post(
        "/api/upload-csv",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 400
    assert "Only .csv files are supported" in response.json()["detail"]


def test_api_logs(client):
    """Verify GET /api/logs returns list of log records."""
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)


def test_stream_campaign_dry_run(client):
    """Verify SSE endpoint streams dry-run campaign events correctly."""
    response = client.get("/api/stream-campaign?mode=dry_run&delay=0")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    assert "event: init" in body
    assert "event: progress" in body
    assert "event: done" in body
    assert "DRY_RUN" in body
