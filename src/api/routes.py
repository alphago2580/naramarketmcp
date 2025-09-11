"""FastAPI HTTP routes for Naramarket services."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.config import OUTPUT_DIR
from ..core.models import (
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
from ..services.crawler import crawler_service
from ..services.file_processor import file_processor_service
from ..tools.naramarket import naramarket_tools


# Pydantic models for request bodies
class CrawlListRequest(BaseModel):
    category: str
    page_no: int = 1
    num_rows: int = 100
    days_back: int = 7
    inqry_bgn_date: Optional[str] = None
    inqry_end_date: Optional[str] = None


class CrawlToCSVRequest(BaseModel):
    category: str
    output_csv: str
    total_days: int = 365
    window_days: int = 30
    anchor_end_date: Optional[str] = None
    max_windows_per_call: int = 0
    max_runtime_sec: int = 3600
    append: bool = False
    fail_on_new_columns: bool = True
    explode_attributes: bool = False
    sanitize: bool = True
    delay_sec: float = 0.1
    keep_temp: bool = False


class SaveResultsRequest(BaseModel):
    products: List[Dict[str, Any]]
    filename: str
    directory: str = OUTPUT_DIR


class ConvertRequest(BaseModel):
    json_path: str
    output_parquet: Optional[str] = None
    explode_attributes: bool = False


class MergeRequest(BaseModel):
    input_pattern: str
    output_csv: str


# Create API router
router = APIRouter(prefix="/api/v1", tags=["naramarket"])


@router.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint."""
    return {"message": "Naramarket MCP Server API", "version": "1.0.0"}


@router.get("/server/info", response_model=ServerInfo)
async def get_server_info():
    """Get server information."""
    return naramarket_tools.server_info()


@router.post("/crawl/list", response_model=CrawlListResult)
async def crawl_product_list(request: CrawlListRequest):
    """Crawl product list from Naramarket API."""
    try:
        result = naramarket_tools.crawl_list(
            category=request.category,
            page_no=request.page_no,
            num_rows=request.num_rows,
            days_back=request.days_back,
            inqry_bgn_date=request.inqry_bgn_date,
            inqry_end_date=request.inqry_end_date
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl/attributes", response_model=DetailResult)
async def get_product_attributes(api_item: Dict[str, Any]):
    """Get detailed product attributes."""
    try:
        result = naramarket_tools.get_detailed_attributes(api_item)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl/csv", response_model=CrawlToCSVResult)
async def crawl_to_csv_endpoint(request: CrawlToCSVRequest):
    """Crawl data and save directly to CSV."""
    try:
        result = crawler_service.crawl_to_csv(
            category=request.category,
            output_csv=request.output_csv,
            total_days=request.total_days,
            window_days=request.window_days,
            anchor_end_date=request.anchor_end_date,
            max_windows_per_call=request.max_windows_per_call,
            max_runtime_sec=request.max_runtime_sec,
            append=request.append,
            fail_on_new_columns=request.fail_on_new_columns,
            explode_attributes=request.explode_attributes,
            sanitize=request.sanitize,
            delay_sec=request.delay_sec,
            keep_temp=request.keep_temp
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/save", response_model=SaveResultsResponse)
async def save_results_endpoint(request: SaveResultsRequest):
    """Save products to JSON file."""
    try:
        result = file_processor_service.save_results(
            request.products, 
            request.filename, 
            request.directory
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/convert/parquet", response_model=ConvertResult)
async def convert_to_parquet_endpoint(request: ConvertRequest):
    """Convert JSON file to Parquet format."""
    try:
        result = file_processor_service.convert_json_to_parquet(
            request.json_path,
            request.output_parquet,
            request.explode_attributes
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/merge", response_model=MergeResult)
async def merge_csv_endpoint(request: MergeRequest):
    """Merge multiple CSV files."""
    try:
        result = file_processor_service.merge_csv_files(
            request.input_pattern,
            request.output_csv
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/csv/{csv_path:path}/summary", response_model=SummaryResult)
async def summarize_csv_endpoint(
    csv_path: str,
    max_rows_preview: int = Query(5, ge=1, le=100)
):
    """Get CSV file summary."""
    try:
        result = file_processor_service.summarize_csv(csv_path, max_rows_preview)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/list", response_model=List[FileInfo])
async def list_files_endpoint(
    pattern: str = Query("*.json", description="File pattern to match"),
    directory: str = Query(OUTPUT_DIR, description="Directory to search")
):
    """List files in directory."""
    try:
        return file_processor_service.list_files(pattern, directory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-01-15"}


# SSE endpoint for streaming crawl results
@router.post("/crawl/csv/stream")
async def stream_crawl_to_csv(request: CrawlToCSVRequest):
    """Stream crawling progress via Server-Sent Events."""
    async def event_generator():
        # This would implement streaming progress updates
        # For now, just yield the final result
        result = crawler_service.crawl_to_csv(
            category=request.category,
            output_csv=request.output_csv,
            total_days=request.total_days,
            window_days=request.window_days,
            anchor_end_date=request.anchor_end_date,
            max_windows_per_call=request.max_windows_per_call,
            max_runtime_sec=request.max_runtime_sec,
            append=request.append,
            fail_on_new_columns=request.fail_on_new_columns,
            explode_attributes=request.explode_attributes,
            sanitize=request.sanitize,
            delay_sec=request.delay_sec,
            keep_temp=request.keep_temp
        )
        yield f"data: {result}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )