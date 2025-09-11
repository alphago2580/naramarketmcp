"""Data models and TypedDict definitions for Naramarket MCP Server."""

from typing import Any, Dict, List, TypedDict


class CrawlListResult(TypedDict, total=False):
    """Result structure for crawl list operations."""
    success: bool
    items: List[Dict[str, Any]]
    total_count: int
    current_page: int
    category: str
    error: str


class DetailResult(TypedDict, total=False):
    """Result structure for detailed product attribute operations."""
    success: bool
    api_item: Dict[str, Any]
    attributes: Dict[str, Any]
    error: str


class CrawlToCSVResult(TypedDict, total=False):
    """Result structure for crawl to CSV operations."""
    success: bool
    category: str
    output_csv: str
    rows: int
    windows_processed: int
    pages_processed: int
    total_products: int
    success_details: int
    failed_details: int
    basic_columns: List[str]
    attr_columns: List[str]
    explode_attributes: bool
    sanitize: bool
    temp_file: str
    temp_deleted: bool
    incomplete: bool
    remaining_days: int
    next_anchor_end_date: str
    covered_days: int
    total_requested_days: int
    elapsed_sec: float
    max_windows_per_call: int
    max_runtime_sec: int
    append_mode: bool
    existing_header_used: bool
    new_basic_cols: List[str]
    new_attr_cols: List[str]
    new_columns_ignored: bool
    error: str


class SaveResultsResponse(TypedDict, total=False):
    """Result structure for save results operations."""
    success: bool
    filename: str
    products_count: int
    error: str


class ConvertResult(TypedDict, total=False):
    """Result structure for conversion operations."""
    success: bool
    input_file: str
    output_file: str
    rows_converted: int
    error: str


class MergeResult(TypedDict, total=False):
    """Result structure for merge operations."""
    success: bool
    input_files: List[str]
    output_file: str
    total_rows: int
    error: str


class SummaryResult(TypedDict, total=False):
    """Result structure for CSV summary operations."""
    success: bool
    file_path: str
    rows: int
    columns: int
    headers: List[str]
    preview: List[Dict[str, Any]]
    error: str


class FileInfo(TypedDict, total=False):
    """File information structure."""
    filename: str
    path: str
    size_bytes: int
    modified_time: str


class ServerInfo(TypedDict, total=False):
    """Server information structure."""
    success: bool
    app: str
    version: str
    tools: List[str]