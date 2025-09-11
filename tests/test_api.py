"""Tests for FastAPI endpoints."""

import json
import os
import sys
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock environment variables before importing
os.environ.setdefault("NARAMARKET_SERVICE_KEY", "test_service_key")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing")

from api.app import create_app
from services.auth import auth_service


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = create_app()
    app.debug = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing."""
    # Login to get token
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    token_data = response.json()
    
    return {"Authorization": f"Bearer {token_data['access_token']}"}


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
        assert "timestamp" in data
    
    def test_server_info(self, client):
        """Test server info endpoint."""
        response = client.get("/api/v1/server/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "app" in data
        assert "version" in data
        assert "tools" in data
        assert isinstance(data["tools"], list)


class TestAuthenticationEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/auth/login", json={
            "username": "admin", 
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "refresh_token" in data
    
    def test_login_failure(self, client):
        """Test login with wrong credentials."""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrong_password"
        })
        assert response.status_code == 401
    
    def test_oauth_token_endpoint(self, client):
        """Test OAuth 2.0 token endpoint."""
        response = client.post("/auth/token", data={
            "username": "admin",
            "password": "admin123",
            "grant_type": "password"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_protected_endpoint_without_auth(self, client):
        """Test protected endpoint without authentication."""
        response = client.get("/auth/protected")
        assert response.status_code == 403  # Forbidden due to missing auth
    
    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Test protected endpoint with authentication."""
        response = client.get("/auth/protected", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_admin_only_endpoint(self, client, auth_headers):
        """Test admin-only endpoint."""
        response = client.get("/auth/admin-only", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_get_current_user(self, client, auth_headers):
        """Test get current user endpoint."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "is_active" in data
        assert "scopes" in data


class TestCrawlEndpoints:
    """Test crawling endpoints."""
    
    @patch('src.tools.naramarket.naramarket_tools.crawl_list')
    def test_crawl_list_success(self, mock_crawl, client):
        """Test crawl list endpoint."""
        # Mock successful response
        mock_crawl.return_value = {
            "success": True,
            "items": [{"id": 1, "name": "test"}],
            "total_count": 1,
            "current_page": 1,
            "category": "test_category"
        }
        
        response = client.post("/api/v1/crawl/list", json={
            "category": "test_category",
            "page_no": 1,
            "num_rows": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data
        assert len(data["items"]) == 1
    
    @patch('src.tools.naramarket.naramarket_tools.crawl_list')
    def test_crawl_list_failure(self, mock_crawl, client):
        """Test crawl list endpoint with API failure."""
        # Mock failed response
        mock_crawl.return_value = {
            "success": False,
            "error": "API error"
        }
        
        response = client.post("/api/v1/crawl/list", json={
            "category": "test_category"
        })
        
        assert response.status_code == 400
    
    @patch('src.tools.naramarket.naramarket_tools.get_detailed_attributes')
    def test_get_attributes_success(self, mock_details, client):
        """Test get product attributes endpoint."""
        # Mock successful response
        mock_details.return_value = {
            "success": True,
            "attributes": {"color": "red", "size": "large"},
            "api_item": {"id": 1}
        }
        
        response = client.post("/api/v1/crawl/attributes", json={
            "id": 1,
            "name": "test_product"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "attributes" in data


class TestFileEndpoints:
    """Test file processing endpoints."""
    
    @patch('src.services.file_processor.file_processor_service.save_results')
    def test_save_results_success(self, mock_save, client):
        """Test save results endpoint."""
        mock_save.return_value = {
            "success": True,
            "filename": "test.json",
            "products_count": 5
        }
        
        response = client.post("/api/v1/files/save", json={
            "products": [{"id": 1}, {"id": 2}],
            "filename": "test.json"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "test.json"
    
    @patch('src.services.file_processor.file_processor_service.list_files')
    def test_list_files(self, mock_list, client):
        """Test list files endpoint."""
        mock_list.return_value = [
            {
                "filename": "test.json",
                "path": "/path/to/test.json",
                "size_bytes": 1024,
                "modified_time": "2024-01-01 12:00:00"
            }
        ]
        
        response = client.get("/api/v1/files/list?pattern=*.json")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["filename"] == "test.json"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_json_request(self, client):
        """Test invalid JSON in request body."""
        response = client.post(
            "/api/v1/crawl/list",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client):
        """Test request with missing required fields."""
        response = client.post("/api/v1/crawl/list", json={
            # Missing required 'category' field
            "page_no": 1
        })
        assert response.status_code == 422
    
    def test_nonexistent_endpoint(self, client):
        """Test request to non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


@pytest.fixture(autouse=True)
def cleanup_auth_tokens():
    """Clean up authentication tokens after each test."""
    yield
    # Clear active tokens
    auth_service.active_tokens.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])