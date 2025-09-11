"""Async crawling service for high-performance data collection."""

import asyncio
import csv
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.async_client import async_client
from ..core.config import DATE_FMT, DEFAULT_DELAY_SEC, DEFAULT_MAX_PAGES, OUTPUT_DIR
from ..core.models import CrawlToCSVResult
from ..core.utils import (
    calculate_elapsed_time,
    ensure_dir,
    sanitize_column_name
)


class AsyncCrawlingService:
    """High-performance async crawling service."""
    
    def __init__(self):
        ensure_dir(OUTPUT_DIR)
    
    async def crawl_to_csv_async(
        self,
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
        max_concurrent_pages: int = 5,
        keep_temp: bool = False
    ) -> CrawlToCSVResult:
        """
        Async version of crawl_to_csv with concurrent page processing.
        
        Args:
            category: Product category to crawl
            output_csv: Output CSV file path
            total_days: Total days to crawl backwards
            window_days: Days per window/batch
            anchor_end_date: End date for continuation (YYYYMMDD)
            max_windows_per_call: Max windows per call (0 = unlimited)
            max_runtime_sec: Max runtime in seconds
            append: Append to existing CSV file
            fail_on_new_columns: Fail if new columns detected in append mode
            explode_attributes: Expand attributes as separate columns
            sanitize: Sanitize column names
            max_concurrent_pages: Max concurrent pages to process
            keep_temp: Keep temporary files for debugging
            
        Returns:
            CrawlToCSVResult with detailed execution information
        """
        start_time = time.time()
        
        if not output_csv.startswith('/'):
            output_csv = os.path.join(OUTPUT_DIR, output_csv)
        
        # Determine date range
        if anchor_end_date:
            end_date = datetime.strptime(anchor_end_date, DATE_FMT)
        else:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=total_days - 1)
        
        # Check existing file for append mode
        existing_header = None
        if append and os.path.exists(output_csv):
            try:
                with open(output_csv, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    existing_header = next(reader, None)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to read existing CSV header: {e}",
                    "output_csv": output_csv
                }
        
        # Create temporary NDJSON file
        temp_dir = tempfile.mkdtemp()
        temp_ndjson = os.path.join(temp_dir, f"async_crawl_{int(time.time())}.ndjson")
        
        try:
            async with async_client as client:
                result = await self._crawl_windows_async(
                    client=client,
                    category=category,
                    start_date=start_date,
                    end_date=end_date,
                    window_days=window_days,
                    max_windows_per_call=max_windows_per_call,
                    max_runtime_sec=max_runtime_sec,
                    max_concurrent_pages=max_concurrent_pages,
                    temp_ndjson=temp_ndjson,
                    start_time=start_time
                )
                
                if not result["success"]:
                    return result
                
                # Convert temp NDJSON to CSV (reuse sync implementation)
                from .crawler import CrawlingService
                sync_crawler = CrawlingService()
                
                csv_result = sync_crawler._convert_temp_to_csv(
                    temp_ndjson=temp_ndjson,
                    output_csv=output_csv,
                    existing_header=existing_header,
                    explode_attributes=explode_attributes,
                    sanitize=sanitize,
                    append=append,
                    fail_on_new_columns=fail_on_new_columns
                )
                
                if not csv_result["success"]:
                    return csv_result
                
                # Combine results
                result.update(csv_result)
                result["elapsed_sec"] = calculate_elapsed_time(start_time)
                result["async_mode"] = True
                
                # Clean up temp file unless requested to keep
                if not keep_temp:
                    try:
                        os.remove(temp_ndjson)
                        os.rmdir(temp_dir)
                        result["temp_deleted"] = True
                    except OSError:
                        result["temp_deleted"] = False
                else:
                    result["temp_file"] = temp_ndjson
                    result["temp_deleted"] = False
                
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Async crawling failed: {str(e)}",
                "output_csv": output_csv,
                "elapsed_sec": calculate_elapsed_time(start_time),
                "async_mode": True
            }
    
    async def _crawl_windows_async(
        self,
        client,
        category: str,
        start_date: datetime,
        end_date: datetime,
        window_days: int,
        max_windows_per_call: int,
        max_runtime_sec: int,
        max_concurrent_pages: int,
        temp_ndjson: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Async implementation of window crawling."""
        
        current_end = end_date
        windows_processed = 0
        pages_processed = 0
        total_products = 0
        success_details = 0
        failed_details = 0
        
        with open(temp_ndjson, 'w', encoding='utf-8') as temp_f:
            while current_end > start_date:
                # Check runtime limit
                if time.time() - start_time > max_runtime_sec:
                    break
                
                # Check window limit
                if max_windows_per_call > 0 and windows_processed >= max_windows_per_call:
                    break
                
                current_start = max(current_end - timedelta(days=window_days - 1), start_date)
                
                window_result = await self._crawl_window_async(
                    client=client,
                    category=category,
                    window_start=current_start,
                    window_end=current_end,
                    max_concurrent_pages=max_concurrent_pages,
                    temp_f=temp_f
                )
                
                windows_processed += 1
                pages_processed += window_result["pages"]
                total_products += window_result["products"]
                success_details += window_result["success_details"]
                failed_details += window_result["failed_details"]
                
                # Move to next window
                current_end = current_start - timedelta(days=1)
        
        # Calculate completion status
        covered_days = (end_date - current_end).days if current_end < end_date else 0
        remaining_days = max((current_end - start_date).days, 0)
        incomplete = remaining_days > 0
        
        next_anchor_end_date = None
        if incomplete:
            next_anchor_end_date = current_end.strftime(DATE_FMT)
        
        return {
            "success": True,
            "category": category,
            "windows_processed": windows_processed,
            "pages_processed": pages_processed,
            "total_products": total_products,
            "success_details": success_details,
            "failed_details": failed_details,
            "incomplete": incomplete,
            "remaining_days": remaining_days,
            "next_anchor_end_date": next_anchor_end_date,
            "covered_days": covered_days
        }
    
    async def _crawl_window_async(
        self,
        client,
        category: str,
        window_start: datetime,
        window_end: datetime,
        max_concurrent_pages: int,
        temp_f
    ) -> Dict[str, Any]:
        """Async implementation of single window crawling."""
        
        start_str = window_start.strftime(DATE_FMT)
        end_str = window_end.strftime(DATE_FMT)
        
        # First, determine how many pages we need to crawl
        first_page_result = await client.crawl_page_with_details(
            category=category,
            page_no=1,
            num_rows=100,
            inqry_bgn_date=start_str,
            inqry_end_date=end_str
        )
        
        if not first_page_result["success"] or not first_page_result["items"]:
            return {
                "pages": 0,
                "products": 0,
                "success_details": 0,
                "failed_details": 0
            }
        
        # Write first page data
        for item in first_page_result["items"]:
            item["window_start"] = start_str
            item["window_end"] = end_str
            temp_f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        total_pages = 1
        total_products = first_page_result["total_items"]
        total_success_details = first_page_result["success_details"]
        total_failed_details = first_page_result["failed_details"]
        
        # Estimate if there are more pages (heuristic based on items returned)
        if len(first_page_result["items"]) >= 100:  # Full page suggests more data
            # Crawl additional pages concurrently
            max_estimated_pages = min(DEFAULT_MAX_PAGES, 20)  # Reasonable limit for async
            page_tasks = []
            
            for page_no in range(2, max_estimated_pages + 1):
                if len(page_tasks) >= max_concurrent_pages:
                    # Process current batch
                    page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
                    
                    # Process results and write to file
                    for page_result in page_results:
                        if isinstance(page_result, Exception):
                            continue
                        
                        if not page_result.get("success") or not page_result.get("items"):
                            break
                        
                        for item in page_result["items"]:
                            item["window_start"] = start_str
                            item["window_end"] = end_str
                            temp_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                        
                        total_pages += 1
                        total_products += page_result["total_items"]
                        total_success_details += page_result["success_details"]
                        total_failed_details += page_result["failed_details"]
                    
                    page_tasks = []
                
                # Add new task
                task = client.crawl_page_with_details(
                    category=category,
                    page_no=page_no,
                    num_rows=100,
                    inqry_bgn_date=start_str,
                    inqry_end_date=end_str
                )
                page_tasks.append(task)
            
            # Process remaining tasks
            if page_tasks:
                page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
                
                for page_result in page_results:
                    if isinstance(page_result, Exception):
                        continue
                    
                    if not page_result.get("success") or not page_result.get("items"):
                        break
                    
                    for item in page_result["items"]:
                        item["window_start"] = start_str
                        item["window_end"] = end_str
                        temp_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    
                    total_pages += 1
                    total_products += page_result["total_items"]
                    total_success_details += page_result["success_details"]
                    total_failed_details += page_result["failed_details"]
        
        return {
            "pages": total_pages,
            "products": total_products,
            "success_details": total_success_details,
            "failed_details": total_failed_details
        }
    
    async def crawl_category_detailed_async(
        self,
        category: str,
        page_no: int = 1,
        num_rows: int = 100,
        days_back: int = 7,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
        max_concurrent_details: int = 10
    ) -> Dict[str, Any]:
        """Async version of crawl_category_detailed with concurrent detail fetching."""
        
        from ..core.utils import date_range_days_back
        
        if not inqry_bgn_date or not inqry_end_date:
            dr = date_range_days_back(days_back)
            inqry_bgn_date = dr["inqryBgnDt"]
            inqry_end_date = dr["inqryEndDt"]
        
        try:
            async with async_client as client:
                result = await client.crawl_page_with_details(
                    category=category,
                    page_no=page_no,
                    num_rows=num_rows,
                    inqry_bgn_date=inqry_bgn_date,
                    inqry_end_date=inqry_end_date
                )
                
                if result["success"]:
                    return {
                        "success": True,
                        "products": result["items"],
                        "total_count": result["total_items"],
                        "current_page": page_no,
                        "category": category,
                        "success_details": result["success_details"],
                        "failed_details": result["failed_details"],
                        "async_mode": True
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                        "current_page": page_no,
                        "category": category,
                        "async_mode": True
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "current_page": page_no,
                "category": category,
                "async_mode": True
            }


# Global async service instance
async_crawler_service = AsyncCrawlingService()