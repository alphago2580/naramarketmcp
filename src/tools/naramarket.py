"""Naramarket MCP tools for data crawling and processing (FastMCP 2.0)."""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.client import get_api_client
from ..core.config import (
    APP_NAME,
    CATEGORIES, 
    DEFAULT_DELAY_SEC,
    DEFAULT_MAX_PAGES,
    DEFAULT_NUM_ROWS,
    SERVER_VERSION
)
from ..core.models import (
    CrawlListResult,
    DetailResult,
    ServerInfo
)
from ..core.utils import (
    calculate_elapsed_time,
    date_range_days_back
)
from .base import BaseTool


class NaramarketTools(BaseTool):
    """Naramarket FastMCP 2.0 tools for data crawling without file operations."""
    
    def crawl_list(
        self,
        category: str,
        page_no: int = 1,
        num_rows: int = DEFAULT_NUM_ROWS,
        days_back: int = 7,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
        delay_sec: float = DEFAULT_DELAY_SEC
    ) -> CrawlListResult:
        """Fetch product list for a category from Nara Market API.
        
        Args:
            category: Product category name
            page_no: Page number to fetch (default 1)
            num_rows: Number of rows per page (default 100)
            days_back: Days to go back if dates not provided (default 7)
            inqry_bgn_date: Start date in YYYYMMDD format
            inqry_end_date: End date in YYYYMMDD format
            delay_sec: Delay between requests (default from config)
            
        Returns:
            CrawlListResult with success status and data
        """
        try:
            start_time = time.time()
            
            # Date calculation
            if not inqry_bgn_date or not inqry_end_date:
                inqry_bgn_date, inqry_end_date = date_range_days_back(days_back)
            
            # API call
            result = get_api_client().fetch_product_list(
                category=category,
                page_no=page_no,
                num_rows=num_rows,
                inqry_bgn_date=inqry_bgn_date,
                inqry_end_date=inqry_end_date
            )
            
            elapsed = calculate_elapsed_time(start_time)
            
            if delay_sec > 0:
                time.sleep(delay_sec)
            
            return {
                "success": True,
                "items": result.get("items", []),
                "total_count": result.get("totalCount", 0),
                "current_page": page_no,
                "category": category,
                "elapsed_time": elapsed
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "current_page": page_no
            }

    def get_detailed_attributes(self, api_item: Dict[str, Any]) -> DetailResult:
        """Get detailed product attributes from G2B API (Enhanced in FastMCP 2.0).
        
        이 함수는 나라마켓 서버의 핵심 기능으로, getMASCntrctPrdctInfoList API와
        연계되어 매우 강력한 기능을 제공합니다. 절대 삭제하지 마세요!
        
        Args:
            api_item: Product item from list API
            
        Returns:
            DetailResult with enhanced attributes and metadata
        """
        try:
            start_time = time.time()
            
            # Enhanced error checking and validation
            if not api_item or not isinstance(api_item, dict):
                return {
                    "success": False,
                    "error": "Invalid api_item: must be a non-empty dictionary",
                    "error_type": "validation_error",
                    "enhanced": True,
                    "api_item": api_item,
                    "payload_attempted": {}
                }
            
            # Get detailed attributes from G2B
            attributes_result = get_api_client().get_detailed_attributes(api_item)
            
            elapsed = calculate_elapsed_time(start_time)
            
            if attributes_result.get("success"):
                return {
                    "success": True,
                    "api_item": api_item,
                    "attributes": attributes_result.get("attributes", {}),
                    "metadata": {
                        "enhanced": True,
                        "version": "2.0",
                        "elapsed_time": elapsed,
                        "timestamp": datetime.now().isoformat(),
                        "item_keys": list(api_item.keys()),
                        "attributes_count": len(attributes_result.get("attributes", {}))
                    },
                    "enhanced": True
                }
            else:
                return {
                    "success": False,
                    "api_item": api_item,
                    "error": attributes_result.get("error", "Unknown error"),
                    "error_type": attributes_result.get("error_type", "api_error"),
                    "enhanced": True,
                    "payload_attempted": attributes_result.get("payload", {}),
                    "metadata": {
                        "enhanced": True,
                        "version": "2.0",
                        "elapsed_time": elapsed,
                        "timestamp": datetime.now().isoformat(),
                        "debug_info": attributes_result.get("debug_info", {})
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception in get_detailed_attributes: {str(e)}",
                "error_type": "exception",
                "api_item": api_item,
                "enhanced": True,
                "metadata": {
                    "enhanced": True,
                    "version": "2.0",
                    "exception_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat()
                }
            }

    def server_info(self) -> ServerInfo:
        """Get server status and available tools list.
        
        Returns:
            ServerInfo with server details
        """
        available_tools = [
            "crawl_list",
            "get_detailed_attributes", 
            "crawl_to_memory",
            "server_info",
            # OpenAPI tools
            "get_bid_announcement_info",
            "get_successful_bid_info", 
            "get_contract_info",
            "get_total_procurement_status",
            "get_mas_contract_product_info"
        ]
        
        return {
            "success": True,
            "app": APP_NAME,
            "version": SERVER_VERSION,
            "tools": available_tools,
            "categories": list(CATEGORIES.keys()),
            "enhanced_features": [
                "FastMCP 2.0 Support",
                "Streamable HTTP Transport",
                "OpenAPI Integration", 
                "Memory-based Processing",
                "Enhanced get_detailed_attributes"
            ]
        }


# Initialize tools instance
naramarket_tools = NaramarketTools()