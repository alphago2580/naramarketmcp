"""FastAPI HTTP routes for Naramarket services."""

from typing import Any, Dict

from fastapi import APIRouter
from ..core.config import APP_NAME, SERVER_VERSION
from ..tools.naramarket import naramarket_tools

router = APIRouter(prefix="/api/v1", tags=["naramarket"])


@router.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint."""
    return {"message": f"{APP_NAME} API", "version": SERVER_VERSION}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "server": APP_NAME, "version": SERVER_VERSION}


@router.get("/server/info")
async def get_server_info():
    """Get server information."""
    return naramarket_tools.server_info()
