"""Tests for health check functionality."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("NARAMARKET_SERVICE_KEY", "DUMMY")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing")

from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_structure(client):
    """Test that the health endpoint returns the expected structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert data["status"] == "healthy"
