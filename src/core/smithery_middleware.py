"""Smithery.ai Accept header compatibility middleware for FastMCP."""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("naramarket.smithery")


class SmitheryCompatibilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to fix Accept header compatibility with Smithery.ai.

    Smithery.ai sends Accept: */* but FastMCP HTTP transport requires
    Accept: application/json, text/event-stream for proper SSE handling.
    """

    async def dispatch(self, request: Request, call_next):
        # Check if this is an MCP request with insufficient Accept headers
        if (request.url.path.startswith("/mcp") and
            request.method == "POST" and
            "text/event-stream" not in request.headers.get("accept", "")):

            logger.info(f"Fixing Accept headers for Smithery.ai request: {request.url}")

            # Create new headers with proper SSE support
            new_headers = dict(request.headers)
            new_headers["accept"] = "application/json, text/event-stream"

            # Create a new request with fixed headers
            scope = request.scope.copy()
            scope["headers"] = [
                (name.encode() if isinstance(name, str) else name,
                 value.encode() if isinstance(value, str) else value)
                for name, value in new_headers.items()
            ]

            # Replace the request scope
            request._scope = scope

        # Continue with the request (now with proper headers)
        response = await call_next(request)
        return response