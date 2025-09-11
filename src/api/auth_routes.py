"""Authentication routes for OAuth 2.0 and JWT."""

from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from pydantic import BaseModel

from ..services.auth import auth_service


# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    username: str
    email: str
    is_active: bool
    scopes: List[str]


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Security schemes
bearer_scheme = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Create auth router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    payload = auth_service.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.users_db.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user."""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


def check_scopes(required_scopes: List[str]):
    """Dependency to check if user has required scopes."""
    async def _check_scopes(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ):
        user_scopes = current_user.get("scopes", [])
        for scope in required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required scope: {scope}"
                )
        return current_user
    return _check_scopes


@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default="password"),
    scope: str = Form(default="")
):
    """OAuth 2.0 token endpoint (password grant)."""
    
    if grant_type != "password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type"
        )
    
    user = auth_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse requested scopes
    requested_scopes = scope.split() if scope else []
    user_scopes = user.get("scopes", [])
    
    # Grant only scopes that user has
    granted_scopes = [s for s in requested_scopes if s in user_scopes]
    if not requested_scopes:  # If no scopes requested, grant all user scopes
        granted_scopes = user_scopes
    
    # Create tokens
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user["username"], "scopes": granted_scopes},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user["username"], "scopes": granted_scopes}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60,
        "refresh_token": refresh_token,
        "scope": " ".join(granted_scopes)
    }


@auth_router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Login with username and password (alternative to OAuth 2.0 token endpoint)."""
    
    user = auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Grant all user scopes
    user_scopes = user.get("scopes", [])
    
    # Create tokens
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user["username"], "scopes": user_scopes},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user["username"], "scopes": user_scopes}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer", 
        "expires_in": auth_service.access_token_expire_minutes * 60,
        "refresh_token": refresh_token,
        "scope": " ".join(user_scopes)
    }


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    
    payload = auth_service.verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    scopes = payload.get("scopes", [])
    
    # Create new access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": username, "scopes": scopes},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60,
        "scope": " ".join(scopes)
    }


@auth_router.post("/revoke")
async def revoke_token(
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """Revoke current token."""
    token = credentials.credentials
    success = auth_service.revoke_token(token)
    
    return {"revoked": success}


@auth_router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user information."""
    return User(
        username=current_user["username"],
        email=current_user["email"],
        is_active=current_user["is_active"],
        scopes=current_user["scopes"]
    )


@auth_router.get("/protected")
async def protected_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Example protected endpoint."""
    return {"message": f"Hello {current_user['username']}, this is a protected endpoint!"}


@auth_router.get("/admin-only")
async def admin_only_endpoint(
    current_user: Dict[str, Any] = Depends(check_scopes(["admin"]))
):
    """Example admin-only endpoint."""
    return {"message": f"Hello admin {current_user['username']}! This is an admin-only endpoint."}


# OAuth 2.0 Authorization Code Flow endpoints
@auth_router.get("/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    scope: str = "",
    state: Optional[str] = None
):
    """OAuth 2.0 authorization endpoint (simplified implementation)."""
    # In a real implementation, this would render a consent page
    # For now, we'll return the authorization parameters
    
    client = auth_service.oauth_clients.get(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    requested_scopes = scope.split() if scope else []
    allowed_scopes = [s for s in requested_scopes if s in client["allowed_scopes"]]
    
    return {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "requested_scopes": requested_scopes,
        "allowed_scopes": allowed_scopes,
        "state": state,
        "message": "In a real implementation, this would show a consent page"
    }


@auth_router.post("/token/client_credentials", response_model=Token)
async def client_credentials_token(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    grant_type: str = Form(default="client_credentials"),
    scope: str = Form(default="")
):
    """OAuth 2.0 client credentials grant."""
    
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type"
        )
    
    client = auth_service.authenticate_client(client_id, client_secret)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    requested_scopes = scope.split() if scope else []
    allowed_scopes = client.get("allowed_scopes", [])
    granted_scopes = [s for s in requested_scopes if s in allowed_scopes]
    
    if not requested_scopes:
        granted_scopes = allowed_scopes
    
    # Create access token for client
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": client_id, "scopes": granted_scopes, "type": "client"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60,
        "scope": " ".join(granted_scopes)
    }