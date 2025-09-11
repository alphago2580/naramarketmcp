"""Naramarket MCP tools for data crawling and processing."""

import csv
import glob
import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.client import api_client
from ..core.config import (
    APP_NAME,
    CATEGORIES, 
    DEFAULT_DELAY_SEC,
    DEFAULT_MAX_PAGES,
    DEFAULT_NUM_ROWS,
    OUTPUT_DIR,
    SERVER_VERSION
)
from ..core.models import (
    CrawlListResult,
    DetailResult,
    FileInfo,
    ServerInfo
)
from ..core.utils import (
    calculate_elapsed_time,
    date_range_days_back,
    ensure_dir,
    extract_g2b_params,
    format_file_size,
    now_ts
)
from .base import BaseTool


class NaramarketTools(BaseTool):
    """MCP tools for Naramarket data crawling."""
    
    def crawl_list(
        self,
        category: str,
        page_no: int = 1,
        num_rows: int = DEFAULT_NUM_ROWS,
        days_back: int = 7,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
    ) -> CrawlListResult:
        """Fetch product list for a category from Nara Market API.
        
        Args:
            category: Product category name
            page_no: Page number to fetch (default 1)
            num_rows: Number of rows per page (default from config)
            days_back: Days to go back if dates not provided (default 7)
            inqry_bgn_date: Start date in YYYYMMDD format
            inqry_end_date: End date in YYYYMMDD format
            
        Returns:
            CrawlListResult with success status and data
        """
        if not inqry_bgn_date or not inqry_end_date:
            dr = date_range_days_back(days_back)
            inqry_bgn_date = dr["inqryBgnDt"]
            inqry_end_date = dr["inqryEndDt"]

        params = {
            "pageNo": page_no,
            "numOfRows": num_rows,
            "type": "json",
            "inqryBgnDate": inqry_bgn_date,
            "inqryEndDate": inqry_end_date,
            "dtilPrdctClsfcNoNm": category,
            "inqryDiv": 1,
        }
        
        try:
            data = self.client.call_list_api(params)
            body = data.get("response", {}).get("body", {})
            items = body.get("items", [])
            total_count = body.get("totalCount", 0)
            
            # Normalize items to list
            if isinstance(items, dict):
                items = items.get("item", items)
                if isinstance(items, dict):
                    items = [items]
            elif not isinstance(items, list):
                items = []
                
            return {
                "success": True,
                "items": items,
                "total_count": int(total_count or 0),
                "current_page": page_no,
                "category": category,
            }
        except Exception as e:
            return {
                "success": False, 
                "error": str(e), 
                "current_page": page_no, 
                "category": category
            }
    
    def get_detailed_attributes(self, api_item: Dict[str, Any]) -> DetailResult:
        """Get detailed product attributes from G2B API.
        
        Args:
            api_item: Product item from list API
            
        Returns:
            DetailResult with attributes or error
        """
        try:
            payload = extract_g2b_params(api_item)
            response = self.client.call_detail_api(payload)
            
            attributes = {}
            result_list = response.get("resultList", [])
            
            if isinstance(result_list, list):
                for item in result_list:
                    if isinstance(item, dict):
                        attr_name = item.get("prdctAtrbNm", "")
                        attr_value = item.get("prdctAtrbVl", "")
                        if attr_name and attr_value:
                            attributes[attr_name] = attr_value
            
            return {
                "success": True,
                "api_item": api_item,
                "attributes": attributes,
            }
        except Exception as e:
            return {
                "success": False,
                "api_item": api_item,
                "error": str(e),
            }
    
    def server_info(self) -> ServerInfo:
        """Get server status and available tools list."""
        return {
            "success": True,
            "app": APP_NAME,
            "version": SERVER_VERSION,
            "tools": [
                "crawl_list",
                "get_detailed_attributes", 
                "crawl_category_detailed",
                "crawl_to_csv",
                "save_results",
                "list_saved_json",
                "convert_json_to_parquet",
                "merge_csv_files",
                "summarize_csv",
                "server_info",
            ],
        }
    
    def list_saved_json(
        self, 
        pattern: str = "*.json", 
        directory: str = OUTPUT_DIR
    ) -> List[FileInfo]:
        """List saved JSON files in directory."""
        ensure_dir(directory)
        files = []
        
        try:
            for filepath in glob.glob(os.path.join(directory, pattern)):
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": os.path.basename(filepath),
                        "path": filepath,
                        "size_bytes": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Sort by modification time, newest first
            files.sort(key=lambda x: x["modified_time"], reverse=True)
            return files
            
        except Exception as e:
            return [{"error": str(e)}]


# Global tools instance
naramarket_tools = NaramarketTools()