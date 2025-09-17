"""Base classes and utilities for MCP tools."""

from typing import Any, Dict

from ..core.client import get_api_client
from ..core.config import APP_NAME, SERVER_VERSION
from ..core.utils import ensure_dir, now_ts


class BaseTool:
    """Base class for all MCP tools."""
    
    def __init__(self):
        self.client = get_api_client()
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "success": True,
            "app": APP_NAME,
            "version": SERVER_VERSION,
            "timestamp": now_ts()
        }