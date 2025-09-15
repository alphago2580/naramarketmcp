"""
FastMCP CORS patch for Smithery.ai deployment.

This module patches FastMCP to add proper CORS headers for browser-based MCP clients.
"""

import logging
from typing import Any, Callable

logger = logging.getLogger("naramarket.cors_patch")


def patch_fastmcp_for_smithery(mcp_instance: Any) -> None:
    """
    Patch FastMCP instance to add Smithery.ai compatible CORS headers.

    This function modifies the FastMCP server to ensure proper CORS handling
    for browser-based MCP clients deployed on Smithery.ai.
    """
    try:
        # Try to access the underlying FastAPI/Starlette app
        app = None

        if hasattr(mcp_instance, '_server') and hasattr(mcp_instance._server, 'app'):
            app = mcp_instance._server.app
        elif hasattr(mcp_instance, 'app'):
            app = mcp_instance.app
        elif hasattr(mcp_instance, '_app'):
            app = mcp_instance._app

        if app is None:
            logger.warning("Could not access FastMCP underlying app for CORS patching")
            return

        # Add CORS middleware to the app
        from starlette.middleware.cors import CORSMiddleware

        # Check if CORS middleware is already added
        has_cors = any(
            isinstance(middleware, tuple) and
            len(middleware) > 0 and
            (middleware[0].__name__ == 'CORSMiddleware' if hasattr(middleware[0], '__name__') else False)
            for middleware in getattr(app, 'user_middleware', [])
        )

        if not has_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Allow all origins for Smithery.ai
                allow_credentials=True,  # Allow credentials
                allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PUT"],  # All methods
                allow_headers=["*"],  # All headers
                expose_headers=[
                    "mcp-session-id",
                    "mcp-protocol-version",
                    "content-type",
                    "content-length"
                ]  # MCP and standard headers
            )
            logger.info("✅ CORS middleware successfully added to FastMCP app")
            logger.info("   - Origins: * (all)")
            logger.info("   - Credentials: enabled")
            logger.info("   - Methods: GET, POST, OPTIONS, DELETE, PUT")
            logger.info("   - Headers: * (all)")
            logger.info("   - Exposed: mcp-session-id, mcp-protocol-version")
        else:
            logger.info("CORS middleware already present in FastMCP app")

    except ImportError:
        logger.error("Could not import CORSMiddleware - Starlette not available")
    except Exception as e:
        logger.warning(f"Failed to patch FastMCP CORS: {e}")
        logger.info("Falling back to FastMCP built-in CORS handling")


def add_cors_response_headers(response: Any) -> None:
    """
    Manually add CORS headers to any response object.

    This is a fallback method for adding CORS headers when middleware patching fails.
    """
    try:
        if hasattr(response, 'headers'):
            response.headers.update({
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, DELETE, PUT",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "mcp-session-id, mcp-protocol-version",
                "Access-Control-Max-Age": "86400"  # 24 hours
            })
    except Exception as e:
        logger.debug(f"Could not add CORS headers to response: {e}")


# Monkey patch for FastMCP run_async if needed
_original_run_async = None

def cors_enabled_run_async(self, transport: str, **kwargs):
    """
    Enhanced run_async with CORS support for Smithery.ai.
    """
    # Apply CORS patch before starting
    patch_fastmcp_for_smithery(self)

    # Add CORS-related kwargs if not present
    cors_defaults = {
        "cors_origins": ["*"],
        "cors_credentials": True,
        "cors_methods": ["GET", "POST", "OPTIONS"],
        "cors_headers": ["*"]
    }

    for key, value in cors_defaults.items():
        if key not in kwargs:
            kwargs[key] = value

    # Call original run_async
    if _original_run_async:
        return _original_run_async(self, transport, **kwargs)
    else:
        # Fallback - this shouldn't happen if patch is applied correctly
        logger.warning("Original run_async not found, using standard call")
        return self.__class__.run_async(self, transport, **kwargs)


def apply_fastmcp_cors_patch():
    """
    Apply global CORS patch to FastMCP class.

    This modifies the FastMCP class to include CORS support by default.
    """
    try:
        from fastmcp import FastMCP

        global _original_run_async
        if not _original_run_async:
            _original_run_async = FastMCP.run_async
            FastMCP.run_async = cors_enabled_run_async
            logger.info("FastMCP.run_async successfully patched for CORS support")

    except Exception as e:
        logger.warning(f"Could not apply global FastMCP CORS patch: {e}")