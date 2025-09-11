"""Main application entry point for Naramarket MCP Server."""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("fastmcp is required. pip install fastmcp")

from .core.config import APP_NAME, OUTPUT_DIR
from .core.models import (
    ConvertResult,
    CrawlListResult,
    CrawlToCSVResult,
    DetailResult,
    FileInfo,
    MergeResult,
    SaveResultsResponse,
    ServerInfo,
    SummaryResult
)
from .services.crawler import crawler_service
from .services.file_processor import file_processor_service
from .tools.naramarket import naramarket_tools


# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("naramarket")

# Initialize FastMCP
try:
    mcp = FastMCP(APP_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to init FastMCP: {e}")


# Register MCP Tools
@mcp.tool()
def crawl_list(
    category: str,
    page_no: int = 1,
    num_rows: int = 100,
    days_back: int = 7,
    inqry_bgn_date: Optional[str] = None,
    inqry_end_date: Optional[str] = None,
) -> CrawlListResult:
    """Fetch product list for a category from Nara Market API.
    
    Args:
        category: Product category name
        page_no: Page number to fetch (default 1)
        num_rows: Number of rows per page (default 100)
        days_back: Days to go back if dates not provided (default 7)
        inqry_bgn_date: Start date in YYYYMMDD format
        inqry_end_date: End date in YYYYMMDD format
        
    Returns:
        CrawlListResult with success status and data
    """
    return naramarket_tools.crawl_list(
        category=category,
        page_no=page_no,
        num_rows=num_rows,
        days_back=days_back,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date
    )


@mcp.tool()
def get_detailed_attributes(api_item: Dict[str, Any]) -> DetailResult:
    """Get detailed product attributes from G2B API.
    
    Args:
        api_item: Product item from list API
        
    Returns:
        DetailResult with attributes or error
    """
    return naramarket_tools.get_detailed_attributes(api_item)


@mcp.tool()
def crawl_to_csv(
    category: str,
    output_csv: str,
    total_days: int = 365,
    window_days: int = 30,
    anchor_end_date: Optional[str] = None,
    max_windows_per_call: int = 0,
    max_runtime_sec: int = 3600,
    append: bool = False,
    fail_on_new_columns: bool = True,
    explode_attributes: bool = False,
    sanitize: bool = True,
    delay_sec: float = 0.1,
    keep_temp: bool = False
) -> CrawlToCSVResult:
    """Crawl category data in windows and save directly to CSV.
    
    Args:
        category: Product category to crawl
        output_csv: Output CSV file path
        total_days: Total days to crawl backwards (default 365)
        window_days: Days per window/batch (default 30)
        anchor_end_date: End date for continuation (YYYYMMDD)
        max_windows_per_call: Max windows per call (0 = unlimited)
        max_runtime_sec: Max runtime in seconds (default 3600)
        append: Append to existing CSV file
        fail_on_new_columns: Fail if new columns detected in append mode
        explode_attributes: Expand attributes as separate columns
        sanitize: Sanitize column names
        delay_sec: Delay between requests (default 0.1)
        keep_temp: Keep temporary files for debugging
        
    Returns:
        CrawlToCSVResult with detailed execution information
    """
    return crawler_service.crawl_to_csv(
        category=category,
        output_csv=output_csv,
        total_days=total_days,
        window_days=window_days,
        anchor_end_date=anchor_end_date,
        max_windows_per_call=max_windows_per_call,
        max_runtime_sec=max_runtime_sec,
        append=append,
        fail_on_new_columns=fail_on_new_columns,
        explode_attributes=explode_attributes,
        sanitize=sanitize,
        delay_sec=delay_sec,
        keep_temp=keep_temp
    )


@mcp.tool()
def save_results(
    products: List[Dict[str, Any]],
    filename: str,
    directory: str = OUTPUT_DIR
) -> SaveResultsResponse:
    """Save products list to JSON file.
    
    Args:
        products: List of product dictionaries
        filename: Output filename
        directory: Output directory (default configured directory)
        
    Returns:
        SaveResultsResponse with success status
    """
    return file_processor_service.save_results(products, filename, directory)


@mcp.tool()
def convert_json_to_parquet(
    json_path: str,
    output_parquet: Optional[str] = None,
    explode_attributes: bool = False
) -> ConvertResult:
    """Convert JSON file to Parquet format.
    
    Args:
        json_path: Path to input JSON file
        output_parquet: Path to output Parquet file (optional)
        explode_attributes: Expand attributes into separate columns
        
    Returns:
        ConvertResult with conversion status
    """
    return file_processor_service.convert_json_to_parquet(
        json_path, output_parquet, explode_attributes
    )


@mcp.tool()
def merge_csv_files(input_pattern: str, output_csv: str) -> MergeResult:
    """Merge multiple CSV files matching pattern into single file.
    
    Args:
        input_pattern: Glob pattern for input files (e.g., "data_*.csv")
        output_csv: Output CSV file path
        
    Returns:
        MergeResult with merge status
    """
    return file_processor_service.merge_csv_files(input_pattern, output_csv)


@mcp.tool()
def summarize_csv(csv_path: str, max_rows_preview: int = 5) -> SummaryResult:
    """Provide summary information about a CSV file.
    
    Args:
        csv_path: Path to CSV file
        max_rows_preview: Maximum rows to include in preview (default 5)
        
    Returns:
        SummaryResult with file information
    """
    return file_processor_service.summarize_csv(csv_path, max_rows_preview)


@mcp.tool()
def list_saved_json(
    pattern: str = "*.json",
    directory: str = OUTPUT_DIR
) -> List[FileInfo]:
    """List saved JSON files in directory.
    
    Args:
        pattern: File pattern to match (default "*.json")
        directory: Directory to search (default configured directory)
        
    Returns:
        List of FileInfo objects
    """
    return file_processor_service.list_files(pattern, directory)


@mcp.tool()
def server_info() -> ServerInfo:
    """Get server status and available tools list.
    
    Returns:
        ServerInfo with server details
    """
    return naramarket_tools.server_info()


def main():
    """Main entry point for the MCP server."""
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Run the MCP server
    logger.info(f"Starting {APP_NAME} MCP server...")
    
    # Check for SSE transport mode
    transport = os.environ.get("FASTMCP_TRANSPORT", "stdio")
    if transport == "sse":
        # SSE mode with HTTP server
        mcp.run(transport="sse", host="localhost", port=8080)
    else:
        # Default STDIO mode
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()