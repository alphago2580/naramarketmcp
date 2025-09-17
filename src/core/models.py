"""Data models and TypedDict definitions for Naramarket FastMCP 2.0 Server."""

from typing import Any, Dict, List
from typing_extensions import TypedDict


class CrawlListResult(TypedDict, total=False):
    """Result structure for crawl list operations."""
    success: bool
    items: List[Dict[str, Any]]
    total_count: int
    current_page: int
    category: str
    error: str


class DetailResult(TypedDict, total=False):
    """Result structure for detailed product attribute operations (enhanced in FastMCP 2.0)."""
    success: bool
    api_item: Dict[str, Any]
    attributes: Dict[str, Any]
    metadata: Dict[str, Any]  # 추가된 메타데이터 지원
    enhanced: bool  # 개선된 버전 여부
    error: str
    error_type: str
    payload_attempted: Dict[str, Any]


class MemoryCrawlResult(TypedDict, total=False):
    """Result structure for memory-based crawl operations (FastMCP 2.0)."""
    success: bool
    items: List[Dict[str, Any]]
    total_count: int
    current_page: int
    category: str
    attributes_included: bool
    error: str


class OpenAPIResponse(TypedDict, total=False):
    """Generic OpenAPI response structure."""
    endpoint: str
    params: Dict[str, Any]
    description: str
    method: str


class EnhancedDetailResult(TypedDict, total=False):
    """Enhanced result structure for detailed product attributes (improved version)."""
    success: bool
    api_item: Dict[str, Any]
    attributes: Dict[str, Any]
    metadata: Dict[str, Any]
    enhanced: bool  # 개선된 버전 표시
    error: str
    error_type: str
    payload_attempted: Dict[str, Any]


class ServerInfo(TypedDict, total=False):
    """Server information structure."""
    success: bool
    app: str
    version: str
    tools: List[str]