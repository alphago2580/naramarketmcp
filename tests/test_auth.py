"""Tests for authentication service."""

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock environment variables
os.environ.setdefault("NARAMARKET_SERVICE_KEY", "test_service_key")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing")

from services.auth import AuthService


@pytest.fixture
def auth_service():
    """Create auth service instance for testing."""
    return AuthService()


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing(self, auth_service):
        """Test password hashing and verification."""
        password = "test_password_123"
        
        # Hash password
        hashed = auth_service.get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be different from plain text
        
        # Verify correct password
        assert auth_service.verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert auth_service.verify_password("wrong_password", hashed) is False
    
    def test_different_hashes_for_same_password(self, auth_service):
        """Test that same password produces different hashes."""
        password = "same_password"
        hash1 = auth_service.get_password_hash(password)
        hash2 = auth_service.get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert auth_service.verify_password(password, hash1) is True
        assert auth_service.verify_password(password, hash2) is True


class TestUserAuthentication:
    """Test user authentication."""
    
    def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication."""
        user = auth_service.authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        assert user["is_active"] is True
        assert "scopes" in user
    
    def test_authenticate_user_wrong_password(self, auth_service):
        """Test authentication with wrong password."""
        user = auth_service.authenticate_user("admin", "wrong_password")
        assert user is None
    
    def test_authenticate_user_nonexistent(self, auth_service):
        """Test authentication with non-existent user."""
        user = auth_service.authenticate_user("nonexistent", "password")
        assert user is None
    
    def test_authenticate_inactive_user(self, auth_service):
        """Test authentication with inactive user."""
        # Add inactive user to test db
        auth_service.users_db["inactive_user"] = {
            "username": "inactive_user",
            "email": "inactive@test.com",
            "hashed_password": auth_service.get_password_hash("password"),
            "is_active": False,
            "scopes": ["read"]
        }
        
        user = auth_service.authenticate_user("inactive_user", "password")
        assert user is None


class TestClientAuthentication:
    """Test OAuth 2.0 client authentication."""
    
    def test_authenticate_client_success(self, auth_service):
        """Test successful client authentication."""
        client = auth_service.authenticate_client("naramarket_client", "client_secret_123")
        assert client is not None
        assert client["client_id"] == "naramarket_client"
        assert "allowed_scopes" in client
        assert "redirect_uris" in client
    
    def test_authenticate_client_wrong_secret(self, auth_service):
        """Test client authentication with wrong secret."""
        client = auth_service.authenticate_client("naramarket_client", "wrong_secret")
        assert client is None
    
    def test_authenticate_client_nonexistent(self, auth_service):
        """Test authentication with non-existent client."""
        client = auth_service.authenticate_client("nonexistent_client", "secret")
        assert client is None


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self, auth_service):
        """Test access token creation."""
        data = {"sub": "testuser", "scopes": ["read", "write"]}
        token = auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should be stored in active tokens
        assert token in auth_service.active_tokens
    
    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        data = {"sub": "testuser", "scopes": ["read"]}
        token = auth_service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token in auth_service.active_tokens
    
    def test_verify_token_valid(self, auth_service):
        """Test verification of valid token."""
        data = {"sub": "testuser", "scopes": ["read"]}
        token = auth_service.create_access_token(data)
        
        payload = auth_service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["scopes"] == ["read"]
        assert payload["type"] == "access"
    
    def test_verify_token_invalid(self, auth_service):
        """Test verification of invalid token."""
        payload = auth_service.verify_token("invalid_token")
        assert payload is None
    
    def test_verify_token_expired(self, auth_service):
        """Test verification of expired token."""
        data = {"sub": "testuser"}
        # Create token with very short expiry
        token = auth_service.create_access_token(
            data, 
            expires_delta=timedelta(milliseconds=1)
        )
        
        # Wait for token to expire
        import time
        time.sleep(0.002)
        
        payload = auth_service.verify_token(token)
        assert payload is None
        
        # Token should be removed from active tokens
        assert token not in auth_service.active_tokens
    
    def test_revoke_token(self, auth_service):
        """Test token revocation."""
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(data)
        
        # Verify token exists and is valid
        assert token in auth_service.active_tokens
        assert auth_service.verify_token(token) is not None
        
        # Revoke token
        success = auth_service.revoke_token(token)
        assert success is True
        
        # Token should no longer exist
        assert token not in auth_service.active_tokens
        assert auth_service.verify_token(token) is None
        
        # Revoking again should return False
        success = auth_service.revoke_token(token)
        assert success is False


class TestAuthorizationCode:
    """Test OAuth 2.0 authorization code flow."""
    
    def test_generate_authorization_code(self, auth_service):
        """Test authorization code generation."""
        code = auth_service.generate_authorization_code(
            client_id="test_client",
            username="testuser",
            scopes=["read"],
            redirect_uri="http://localhost/callback"
        )
        
        assert isinstance(code, str)
        assert len(code) > 0
    
    def test_verify_authorization_code_valid(self, auth_service):
        """Test verification of valid authorization code."""
        code = auth_service.generate_authorization_code(
            client_id="test_client",
            username="testuser", 
            scopes=["read", "write"],
            redirect_uri="http://localhost/callback"
        )
        
        payload = auth_service.verify_authorization_code(code)
        assert payload is not None
        assert payload["client_id"] == "test_client"
        assert payload["username"] == "testuser"
        assert payload["scopes"] == ["read", "write"]
        assert payload["redirect_uri"] == "http://localhost/callback"
    
    def test_verify_authorization_code_invalid(self, auth_service):
        """Test verification of invalid authorization code."""
        payload = auth_service.verify_authorization_code("invalid_code")
        assert payload is None


class TestTokenCleanup:
    """Test token cleanup functionality."""
    
    def test_cleanup_expired_tokens(self, auth_service):
        """Test cleanup of expired tokens."""
        # Create some tokens with short expiry
        data = {"sub": "testuser"}
        token1 = auth_service.create_access_token(
            data, 
            expires_delta=timedelta(milliseconds=1)
        )
        token2 = auth_service.create_access_token(
            data,
            expires_delta=timedelta(hours=1)  # Valid for 1 hour
        )
        
        # Wait for first token to expire
        import time
        time.sleep(0.002)
        
        # Both tokens should be in active tokens initially
        assert token1 in auth_service.active_tokens
        assert token2 in auth_service.active_tokens
        
        # Clean up expired tokens
        cleaned_count = auth_service.cleanup_expired_tokens()
        assert cleaned_count == 1
        
        # Only token2 should remain
        assert token1 not in auth_service.active_tokens
        assert token2 in auth_service.active_tokens


class TestUserScopes:
    """Test user scope management."""
    
    def test_get_user_scopes_existing_user(self, auth_service):
        """Test getting scopes for existing user."""
        scopes = auth_service.get_user_scopes("admin")
        assert isinstance(scopes, list)
        assert "admin" in scopes
        assert "read" in scopes
        assert "write" in scopes
    
    def test_get_user_scopes_nonexistent_user(self, auth_service):
        """Test getting scopes for non-existent user."""
        scopes = auth_service.get_user_scopes("nonexistent")
        assert scopes == []


@pytest.fixture(autouse=True)
def cleanup_tokens(auth_service):
    """Clean up tokens after each test."""
    yield
    if hasattr(auth_service, 'active_tokens'):
        auth_service.active_tokens.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])