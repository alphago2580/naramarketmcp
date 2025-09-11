"""Authentication service with OAuth 2.0 and JWT support."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

from ..core.config import APP_NAME


class AuthService:
    """Authentication service for OAuth 2.0 and JWT tokens."""
    
    def __init__(self):
        # JWT configuration
        self.secret_key = os.environ.get(
            "JWT_SECRET_KEY", 
            secrets.token_urlsafe(32)
        )
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(
            os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        self.refresh_token_expire_days = int(
            os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30")
        )
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Simple in-memory user store (replace with database in production)
        self.users_db = {
            "admin": {
                "username": "admin",
                "email": "admin@naramarket.local",
                "hashed_password": self.get_password_hash("admin123"),
                "is_active": True,
                "scopes": ["read", "write", "admin"]
            },
            "user": {
                "username": "user",
                "email": "user@naramarket.local", 
                "hashed_password": self.get_password_hash("user123"),
                "is_active": True,
                "scopes": ["read"]
            }
        }
        
        # OAuth 2.0 clients (simple in-memory store)
        self.oauth_clients = {
            "naramarket_client": {
                "client_id": "naramarket_client",
                "client_secret": self.get_password_hash("client_secret_123"),
                "allowed_scopes": ["read", "write"],
                "redirect_uris": ["http://localhost:8000/callback"]
            }
        }
        
        # Active tokens store (in production, use Redis or database)
        self.active_tokens = {}
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password."""
        user = self.users_db.get(username)
        if not user:
            return None
        
        if not self.verify_password(password, user["hashed_password"]):
            return None
        
        if not user.get("is_active", False):
            return None
        
        return user
    
    def authenticate_client(self, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """Authenticate OAuth 2.0 client."""
        client = self.oauth_clients.get(client_id)
        if not client:
            return None
        
        if not self.verify_password(client_secret, client["client_secret"]):
            return None
        
        return client
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": APP_NAME,
            "type": "access"
        })
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store active token
        self.active_tokens[token] = {
            "data": to_encode,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expire
        }
        
        return token
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": APP_NAME,
            "type": "refresh"
        })
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store active token
        self.active_tokens[token] = {
            "data": to_encode,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expire
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            # Check if token is in active tokens
            if token not in self.active_tokens:
                return None
            
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Check if token is expired (additional check)
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                self.revoke_token(token)
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.revoke_token(token)
            return None
        except jwt.JWTError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self.active_tokens:
            del self.active_tokens[token]
            return True
        return False
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from active tokens store."""
        current_time = datetime.now(timezone.utc)
        expired_tokens = [
            token for token, data in self.active_tokens.items()
            if data["expires_at"] < current_time
        ]
        
        for token in expired_tokens:
            del self.active_tokens[token]
        
        return len(expired_tokens)
    
    def generate_authorization_code(
        self,
        client_id: str,
        username: str,
        scopes: list,
        redirect_uri: str
    ) -> str:
        """Generate OAuth 2.0 authorization code."""
        code_data = {
            "client_id": client_id,
            "username": username,
            "scopes": scopes,
            "redirect_uri": redirect_uri,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10)  # Short expiry for auth codes
        }
        
        return jwt.encode(code_data, self.secret_key, algorithm=self.algorithm)
    
    def verify_authorization_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Verify OAuth 2.0 authorization code."""
        try:
            payload = jwt.decode(code, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.JWTError:
            return None
    
    def get_user_scopes(self, username: str) -> list:
        """Get user's authorized scopes."""
        user = self.users_db.get(username)
        return user.get("scopes", []) if user else []


# Global auth service instance
auth_service = AuthService()