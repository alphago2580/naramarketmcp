"""Crawling service for large-scale data collection."""

import csv
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.client import get_api_client
from ..core.config import DATE_FMT, DEFAULT_DELAY_SEC, DEFAULT_MAX_PAGES, OUTPUT_DIR
from ..core.models import CrawlToCSVResult
from ..core.utils import (
    calculate_elapsed_time,
    ensure_dir,
    extract_g2b_params,
    sanitize_column_name
)


class CrawlingService:
    """Service for handling large-scale crawling operations."""
    
    def __init__(self):
        self.client = get_api_client()
        ensure_dir(OUTPUT_DIR)
    
    def crawl_to_csv(
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
        delay_sec: float = DEFAULT_DELAY_SEC,
        keep_temp: bool = False
    ) -> CrawlToCSVResult:
        """
        Crawl category data in windows and save directly to CSV.
        
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
            delay_sec: Delay between requests
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
        
        # Create temporary NDJSON file for intermediate storage
        temp_dir = tempfile.mkdtemp()
        temp_ndjson = os.path.join(temp_dir, f"crawl_{int(time.time())}.ndjson")
        
        try:
            result = self._crawl_windows_to_temp(
                category=category,
                start_date=start_date,
                end_date=end_date,
                window_days=window_days,
                max_windows_per_call=max_windows_per_call,
                max_runtime_sec=max_runtime_sec,
                delay_sec=delay_sec,
                temp_ndjson=temp_ndjson,
                start_time=start_time
            )
            
            if not result["success"]:
                return result
            
            # Convert temp NDJSON to CSV
            csv_result = self._convert_temp_to_csv(
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
                "error": f"Crawling failed: {str(e)}",
                "output_csv": output_csv,
                "elapsed_sec": calculate_elapsed_time(start_time)
            }
    
    def _crawl_windows_to_temp(
        self,
        category: str,
        start_date: datetime,
        end_date: datetime,
        window_days: int,
        max_windows_per_call: int,
        max_runtime_sec: int,
        delay_sec: float,
        temp_ndjson: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Crawl data in windows and save to temporary NDJSON file."""
        
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
                
                window_result = self._crawl_window(
                    category=category,
                    window_start=current_start,
                    window_end=current_end,
                    temp_f=temp_f,
                    delay_sec=delay_sec
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
    
    def _crawl_window(
        self,
        category: str,
        window_start: datetime,
        window_end: datetime,
        temp_f,
        delay_sec: float
    ) -> Dict[str, Any]:
        """Crawl a single time window."""
        
        page = 1
        products = 0
        pages = 0
        success_details = 0
        failed_details = 0
        
        start_str = window_start.strftime(DATE_FMT)
        end_str = window_end.strftime(DATE_FMT)
        
        while page <= DEFAULT_MAX_PAGES:
            try:
                params = {
                    "pageNo": page,
                    "numOfRows": 100,
                    "type": "json",
                    "inqryBgnDate": start_str,
                    "inqryEndDate": end_str,
                    "dtilPrdctClsfcNoNm": category,
                    "inqryDiv": 1,
                }
                
                data = self.client.call_list_api(params)
                body = data.get("response", {}).get("body", {})
                items = body.get("items", [])
                
                # Normalize items
                if isinstance(items, dict):
                    items = items.get("item", items)
                    if isinstance(items, dict):
                        items = [items]
                elif not isinstance(items, list):
                    items = []
                
                if not items:
                    break
                
                pages += 1
                products += len(items)
                
                # Process each item for detailed attributes
                for item in items:
                    try:
                        # Get detailed attributes
                        payload = extract_g2b_params(item)
                        detail_response = self.client.call_detail_api(payload)
                        
                        attributes = {}
                        result_list = detail_response.get("resultList", [])
                        
                        if isinstance(result_list, list):
                            for attr_item in result_list:
                                if isinstance(attr_item, dict):
                                    attr_name = attr_item.get("prdctAtrbNm", "")
                                    attr_value = attr_item.get("prdctAtrbVl", "")
                                    if attr_name and attr_value:
                                        attributes[attr_name] = attr_value
                        
                        # Create record
                        record = {
                            **item,
                            "attributes": attributes,
                            "window_start": start_str,
                            "window_end": end_str,
                            "detail_success": True
                        }
                        
                        success_details += 1
                        
                    except Exception:
                        # Create record without attributes
                        record = {
                            **item,
                            "attributes": {},
                            "window_start": start_str,
                            "window_end": end_str,
                            "detail_success": False
                        }
                        failed_details += 1
                    
                    # Write to temp file
                    temp_f.write(json.dumps(record, ensure_ascii=False) + '\n')
                
                page += 1
                
                # Add delay between requests
                if delay_sec > 0:
                    time.sleep(delay_sec)
                
            except Exception:
                break
        
        return {
            "pages": pages,
            "products": products,
            "success_details": success_details,
            "failed_details": failed_details
        }
    
    def _convert_temp_to_csv(
        self,
        temp_ndjson: str,
        output_csv: str,
        existing_header: Optional[List[str]],
        explode_attributes: bool,
        sanitize: bool,
        append: bool,
        fail_on_new_columns: bool
    ) -> Dict[str, Any]:
        """Convert temporary NDJSON file to CSV format."""
        
        try:
            # First pass: determine all columns
            all_basic_cols = set()
            all_attr_cols = set()
            
            with open(temp_ndjson, 'r', encoding='utf-8') as temp_f:
                for line in temp_f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            
                            # Basic columns (excluding attributes)
                            for key in record.keys():
                                if key != "attributes":
                                    all_basic_cols.add(key)
                            
                            # Attribute columns
                            attributes = record.get("attributes", {})
                            if isinstance(attributes, dict):
                                all_attr_cols.update(attributes.keys())
                        
                        except json.JSONDecodeError:
                            continue
            
            # Sort columns for consistency
            basic_cols_sorted = sorted(all_basic_cols)
            attr_cols_sorted = sorted(all_attr_cols)
            
            # Sanitize column names if requested
            if sanitize:
                basic_cols_sorted = [sanitize_column_name(c) for c in basic_cols_sorted]
                attr_cols_sorted = [sanitize_column_name(c) for c in attr_cols_sorted]
            
            # Build final header
            if explode_attributes:
                header = basic_cols_sorted + [f"attr_{c}" for c in attr_cols_sorted]
            else:
                header = basic_cols_sorted + ["attributes_json"]
            
            # Check for new columns in append mode
            if existing_header is not None:
                existing_set = set(existing_header)
                current_set = set(header)
                new_cols = current_set - existing_set
                
                if new_cols and fail_on_new_columns:
                    return {
                        "success": False,
                        "error": f"New columns detected in append mode: {list(new_cols)}",
                        "new_columns": list(new_cols)
                    }
                
                if new_cols:
                    # Use existing header and ignore new columns
                    header = existing_header
            
            # Second pass: write CSV
            file_mode = "a" if (append and existing_header is not None) else "w"
            rows_written = 0
            
            with open(output_csv, file_mode, newline="", encoding="utf-8-sig") as csv_f:
                writer = csv.writer(csv_f)
                
                # Write header only for new files
                if file_mode == "w":
                    writer.writerow(header)
                
                # Write data rows
                with open(temp_ndjson, 'r', encoding='utf-8') as temp_f:
                    for line in temp_f:
                        if line.strip():
                            try:
                                record = json.loads(line)
                                
                                # Build row data
                                row_data = {}
                                
                                # Basic columns
                                for col in basic_cols_sorted:
                                    original_col = col
                                    if sanitize:
                                        # Find original column name
                                        for orig_key in record.keys():
                                            if sanitize_column_name(orig_key) == col:
                                                original_col = orig_key
                                                break
                                    row_data[col] = record.get(original_col, "")
                                
                                # Attribute columns
                                attributes = record.get("attributes", {})
                                if explode_attributes:
                                    for attr_col in attr_cols_sorted:
                                        col_name = f"attr_{attr_col}"
                                        if sanitize:
                                            col_name = f"attr_{sanitize_column_name(attr_col)}"
                                        row_data[col_name] = attributes.get(attr_col, "")
                                else:
                                    row_data["attributes_json"] = json.dumps(attributes, ensure_ascii=False)
                                
                                # Additional metadata
                                row_data["window_start"] = record.get("window_start", "")
                                row_data["window_end"] = record.get("window_end", "")
                                row_data["detail_success"] = "1" if record.get("detail_success") else "0"
                                
                                # Write row in header order
                                row = [row_data.get(col, "") for col in header]
                                writer.writerow(row)
                                rows_written += 1
                                
                            except json.JSONDecodeError:
                                continue
            
            return {
                "success": True,
                "output_csv": output_csv,
                "rows": rows_written,
                "basic_columns": basic_cols_sorted,
                "attr_columns": attr_cols_sorted if explode_attributes else [],
                "explode_attributes": explode_attributes,
                "sanitize": sanitize,
                "append_mode": append,
                "existing_header_used": existing_header is not None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSV conversion failed: {str(e)}",
                "output_csv": output_csv
            }


# Global service instance
crawler_service = CrawlingService()