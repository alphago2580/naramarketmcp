"""CORS middleware for MCP server Smithery.ai deployment."""

import logging
from typing import Any, Callable, List, Optional

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False
    BaseHTTPMiddleware = object

logger = logging.getLogger("naramarket.cors")


class MCPCORSMiddleware(BaseHTTPMiddleware if STARLETTE_AVAILABLE else object):
    """
    CORS middleware specifically configured for MCP servers on Smithery.ai.

    Implements all required CORS headers for proper MCP protocol support:
    - Access-Control-Allow-Origin: *
    - Access-Control-Allow-Credentials: true
    - Access-Control-Allow-Methods: GET, POST, OPTIONS
    - Access-Control-Allow-Headers: *, Content-Type, Authorization
    - Access-Control-Expose-Headers: mcp-session-id, mcp-protocol-version
    """

    def __init__(
        self,
        app: Callable,
        allow_origins: List[str] = None,
        allow_credentials: bool = True,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        expose_headers: List[str] = None,
        max_age: int = 600,
    ):
        if not STARLETTE_AVAILABLE:
            logger.warning("Starlette not available, CORS middleware disabled")
            return

        super().__init__(app)

        # Smithery.ai optimized defaults
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["GET", "POST", "OPTIONS"]
        self.allow_headers = allow_headers or ["*", "Content-Type", "Authorization"]
        self.expose_headers = expose_headers or ["mcp-session-id", "mcp-protocol-version"]
        self.max_age = max_age

        logger.info("MCP CORS middleware initialized for Smithery.ai deployment")
        logger.info(f"Allow origins: {self.allow_origins}")
        logger.info(f"Allow credentials: {self.allow_credentials}")
        logger.info(f"MCP headers exposed: {self.expose_headers}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process CORS headers for all requests."""
        if not STARLETTE_AVAILABLE:
            return await call_next(request)

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            return response

        # Process normal request
        response = await call_next(request)
        self._add_cors_headers(response, request)
        return response

    def _add_cors_headers(self, response: Response, request: Request) -> None:
        """Add all required CORS headers to response."""
        # Allow all origins for Smithery.ai
        if "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            origin = request.headers.get("Origin")
            if origin and origin in self.allow_origins:
                response.headers["Access-Control-Allow-Origin"] = origin

        # Allow credentials (required for session management)
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        # Allow required HTTP methods
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)

        # Allow all headers including custom ones
        if "*" in self.allow_headers:
            requested_headers = request.headers.get("Access-Control-Request-Headers")
            if requested_headers:
                response.headers["Access-Control-Allow-Headers"] = requested_headers
            else:
                response.headers["Access-Control-Allow-Headers"] = "*"
        else:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)

        # Expose MCP-specific headers
        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

        # Set preflight cache time
        response.headers["Access-Control-Max-Age"] = str(self.max_age)

        # Add MCP protocol headers if not present
        if "mcp-protocol-version" not in response.headers:
            response.headers["mcp-protocol-version"] = "2024-11-05"


def apply_cors_to_fastmcp(mcp_instance: Any) -> None:
    """
    Apply CORS configuration to FastMCP instance if possible.

    This function attempts to apply CORS middleware to FastMCP servers
    for Smithery.ai deployment compatibility.
    """
    if not STARLETTE_AVAILABLE:
        logger.warning("Cannot apply CORS middleware: Starlette not available")
        return

    try:
        # Try to access the underlying Starlette/FastAPI app
        if hasattr(mcp_instance, '_app') and hasattr(mcp_instance._app, 'add_middleware'):
            mcp_instance._app.add_middleware(MCPCORSMiddleware)
            logger.info("CORS middleware successfully applied to FastMCP app")
        elif hasattr(mcp_instance, 'add_middleware'):
            mcp_instance.add_middleware(MCPCORSMiddleware)
            logger.info("CORS middleware successfully applied to FastMCP instance")
        else:
            logger.info("FastMCP CORS will be handled by built-in mechanisms")
    except Exception as e:
        logger.warning(f"Could not apply CORS middleware: {e}")
        logger.info("Relying on FastMCP default CORS handling")