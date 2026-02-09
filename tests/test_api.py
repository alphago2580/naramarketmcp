"""Tests for FastAPI endpoints."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("NARAMARKET_SERVICE_KEY", "test_service_key")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing")

from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.debug = True
    return TestClient(app)


class TestBasicEndpoints:
    """Test basic API endpoints."""

    def test_root_endpoint(self, client):
        """Test API root endpoint."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_server_info(self, client):
        """Test server info endpoint."""
        response = client.get("/api/v1/server/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "app" in data
        assert "version" in data
        assert "tools" in data


class TestErrorHandling:
    """Test error handling."""

    def test_nonexistent_endpoint(self, client):
        """Test request to non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
