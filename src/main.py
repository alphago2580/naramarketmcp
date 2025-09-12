"""Main application entry point for Naramarket MCP 2.0 Server with OpenAPI integration."""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("fastmcp>=2.0.0 is required. pip install fastmcp>=2.0.0")

from .core.config import APP_NAME
from .core.models import (
    CrawlListResult,
    DetailResult,
    ServerInfo
)
from .tools.naramarket import naramarket_tools
from .tools.openapi_tools import openapi_tools


# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("naramarket")

# Initialize FastMCP 2.0
try:
    mcp = FastMCP(APP_NAME)
    logger.info(f"FastMCP 2.0 initialized: {APP_NAME}")
except Exception as e:
    raise RuntimeError(f"Failed to init FastMCP 2.0: {e}")


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
def crawl_to_memory(
    category: str,
    page_no: int = 1,
    num_rows: int = 100,
    days_back: int = 7,
    inqry_bgn_date: Optional[str] = None,
    inqry_end_date: Optional[str] = None,
    include_attributes: bool = True
) -> Dict[str, Any]:
    """Crawl category data and return results in memory (no file saving).
    
    Args:
        category: Product category to crawl
        page_no: Page number to fetch (default 1)
        num_rows: Number of rows per page (default 100)
        days_back: Days to go back if dates not provided (default 7)
        inqry_bgn_date: Start date in YYYYMMDD format
        inqry_end_date: End date in YYYYMMDD format
        include_attributes: Include detailed attributes for each item
        
    Returns:
        Dict with crawled data in memory
    """
    # Get list data
    list_result = naramarket_tools.crawl_list(
        category=category,
        page_no=page_no,
        num_rows=num_rows,
        days_back=days_back,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date
    )
    
    if not list_result.get("success") or not include_attributes:
        return list_result
    
    # Get detailed attributes for each item
    items_with_attributes = []
    for item in list_result.get("items", []):
        detail_result = naramarket_tools.get_detailed_attributes(item)
        if detail_result.get("success"):
            item_with_attrs = item.copy()
            item_with_attrs["detailed_attributes"] = detail_result.get("attributes", {})
            items_with_attributes.append(item_with_attrs)
        else:
            items_with_attributes.append(item)
    
    return {
        "success": True,
        "items": items_with_attributes,
        "total_count": list_result.get("total_count", 0),
        "current_page": page_no,
        "category": category,
        "attributes_included": include_attributes
    }




@mcp.tool()
def server_info() -> ServerInfo:
    """Get server status and available tools list.
    
    Returns:
        ServerInfo with server details
    """
    return naramarket_tools.server_info()


# OpenAPI-based tools
@mcp.tool()
def get_bid_announcement_info(
    num_rows: int = 10,
    page_no: int = 1,
    bid_notice_start_date: Optional[str] = None,
    bid_notice_end_date: Optional[str] = None
) -> Dict[str, Any]:
    """입찰공고정보 조회 (OpenAPI 기반).
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        bid_notice_start_date: 입찰공고시작일시 (YYYYMMDDHHMM)
        bid_notice_end_date: 입찰공고종료일시 (YYYYMMDDHHMM)
        
    Returns:
        입찰공고정보 조회 결과
    """
    return openapi_tools.get_bid_announcement_info(
        num_rows=num_rows,
        page_no=page_no,
        bid_notice_start_date=bid_notice_start_date,
        bid_notice_end_date=bid_notice_end_date
    )


@mcp.tool()
def get_successful_bid_info(
    business_div_code: str,
    num_rows: int = 10,
    page_no: int = 1,
    opening_start_date: Optional[str] = None,
    opening_end_date: Optional[str] = None
) -> Dict[str, Any]:
    """낙찰정보 조회 (OpenAPI 기반).
    
    Args:
        business_div_code: 업무구분코드 (1:물품, 2:외자, 3:공사, 5:용역)
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        opening_start_date: 개찰시작일시 (YYYYMMDDHHMM)
        opening_end_date: 개찰종료일시 (YYYYMMDDHHMM)
        
    Returns:
        낙찰정보 조회 결과
    """
    return openapi_tools.get_successful_bid_info(
        business_div_code=business_div_code,
        num_rows=num_rows,
        page_no=page_no,
        opening_start_date=opening_start_date,
        opening_end_date=opening_end_date
    )


@mcp.tool()
def get_contract_info(
    num_rows: int = 10,
    page_no: int = 1,
    contract_start_date: Optional[str] = None,
    contract_end_date: Optional[str] = None,
    institution_div_code: Optional[str] = None,
    institution_code: Optional[str] = None
) -> Dict[str, Any]:
    """계약정보 조회 (OpenAPI 기반).
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        contract_start_date: 계약체결시작일자 (YYYYMMDD)
        contract_end_date: 계약체결종료일자 (YYYYMMDD)
        institution_div_code: 기관구분코드 (1:계약기관, 2:수요기관)
        institution_code: 기관코드
        
    Returns:
        계약정보 조회 결과
    """
    return openapi_tools.get_contract_info(
        num_rows=num_rows,
        page_no=page_no,
        contract_start_date=contract_start_date,
        contract_end_date=contract_end_date,
        institution_div_code=institution_div_code,
        institution_code=institution_code
    )


@mcp.tool()
def get_total_procurement_status(
    num_rows: int = 10,
    page_no: int = 1,
    search_base_year: Optional[str] = None
) -> Dict[str, Any]:
    """전체 공공조달 현황 조회 (OpenAPI 기반).
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        search_base_year: 검색기준년도 (YYYY)
        
    Returns:
        전체 공공조달 현황 조회 결과
    """
    return openapi_tools.get_total_procurement_status(
        num_rows=num_rows,
        page_no=page_no,
        search_base_year=search_base_year
    )


@mcp.tool()
def get_mas_contract_product_info(
    num_rows: int = 10,
    page_no: int = 1,
    registration_start_date: Optional[str] = None,
    registration_end_date: Optional[str] = None,
    product_name: Optional[str] = None,
    product_id: Optional[str] = None,
    contract_company_name: Optional[str] = None,
    change_start_date: Optional[str] = None,
    change_end_date: Optional[str] = None,
    product_certification: Optional[str] = None
) -> Dict[str, Any]:
    """다수공급자계약 품목정보 조회 (OpenAPI 기반) - 핵심 API.
    
    이 API는 get_detailed_attributes와 연계되어 사용되는 매우 중요한 API입니다.
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        registration_start_date: 등록일시 시작일시 (YYYYMMDDHH24M)
        registration_end_date: 등록일시 종료일시 (YYYYMMDDHH24M)
        product_name: 품명
        product_id: 물품식별번호
        contract_company_name: 계약업체명
        change_start_date: 변경일시 시작일시 (YYYYMMDDHH24M)
        change_end_date: 변경일시 종료일시 (YYYYMMDDHH24M)
        product_certification: 제품인증여부 (Y/N)
        
    Returns:
        다수공급자계약 품목정보 조회 결과
    """
    return openapi_tools.get_mas_contract_product_info(
        num_rows=num_rows,
        page_no=page_no,
        registration_start_date=registration_start_date,
        registration_end_date=registration_end_date,
        product_name=product_name,
        product_id=product_id,
        contract_company_name=contract_company_name,
        change_start_date=change_start_date,
        change_end_date=change_end_date,
        product_certification=product_certification
    )


def main():
    """Main entry point for the FastMCP 2.0 server with secure configuration."""
    logger.info(f"Starting {APP_NAME} FastMCP 2.0 server...")
    
    try:
        # Validate service key before starting server
        from .core.config import get_service_key
        get_service_key()  # This will raise an exception if key is invalid
        
        # Check for transport mode with security validation
        transport = os.environ.get("FASTMCP_TRANSPORT", "stdio")
        host = os.environ.get("FASTMCP_HOST", "127.0.0.1")
        
        # Validate host for production deployment
        if transport in ["http", "sse"] and host == "0.0.0.0":
            logger.warning("Server will bind to all interfaces (0.0.0.0) - ensure proper firewall configuration")
        
        # Use PORT environment variable (smithery.ai compatible)
        try:
            port = int(os.environ.get("PORT") or os.environ.get("FASTMCP_PORT", "8000"))
        except ValueError:
            logger.error("Invalid PORT value in environment, using default 8000")
            port = 8000
        
        if transport == "http":
            # HTTP mode for smithery.ai deployment
            logger.info(f"Starting HTTP transport on {host}:{port} with /mcp endpoint")
            logger.info("Transport mode: HTTP (production deployment)")
            import asyncio
            asyncio.run(mcp.run_async("sse", host=host, port=port))
        elif transport == "sse":
            # SSE mode for real-time communication
            logger.info(f"Starting SSE transport on {host}:{port}")
            logger.info("Transport mode: Server-Sent Events")
            import asyncio
            asyncio.run(mcp.run_async("sse", host=host, port=port))
        else:
            # Default STDIO mode for local development
            logger.info("Starting STDIO transport")
            logger.info("Transport mode: STDIO (development/local)")
            mcp.run("stdio")
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Server startup failed due to configuration issues")
        return 1
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    main()