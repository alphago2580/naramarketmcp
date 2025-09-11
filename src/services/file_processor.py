"""File processing service for data conversion and management."""

import csv
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.config import OUTPUT_DIR
from ..core.models import (
    ConvertResult,
    FileInfo, 
    MergeResult,
    SaveResultsResponse,
    SummaryResult
)
from ..core.utils import ensure_dir, format_file_size


class FileProcessorService:
    """Service for handling file operations and conversions."""
    
    def __init__(self):
        ensure_dir(OUTPUT_DIR)
    
    def save_results(
        self,
        products: List[Dict[str, Any]], 
        filename: str,
        directory: str = OUTPUT_DIR
    ) -> SaveResultsResponse:
        """Save products list to JSON file."""
        ensure_dir(directory)
        
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "filename": filename,
                "products_count": len(products)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    def convert_json_to_parquet(
        self,
        json_path: str,
        output_parquet: Optional[str] = None,
        explode_attributes: bool = False
    ) -> ConvertResult:
        """Convert JSON file to Parquet format."""
        
        if not output_parquet:
            base = os.path.splitext(json_path)[0]
            output_parquet = f"{base}.parquet"
        
        try:
            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return {
                    "success": False,
                    "error": "JSON file must contain a list of objects",
                    "input_file": json_path
                }
            
            if not data:
                return {
                    "success": False,
                    "error": "JSON file is empty",
                    "input_file": json_path
                }
            
            # Convert to DataFrame
            df = pd.json_normalize(data)
            
            # Handle attributes column if it exists
            if explode_attributes and 'attributes' in df.columns:
                # Explode attributes into separate columns
                attributes_df = pd.json_normalize(df['attributes'].fillna({}))
                attributes_df.columns = [f"attr_{col}" for col in attributes_df.columns]
                
                # Combine with original DataFrame (excluding attributes column)
                df_without_attrs = df.drop(columns=['attributes'])
                df = pd.concat([df_without_attrs, attributes_df], axis=1)
            
            # Save to Parquet
            df.to_parquet(output_parquet, index=False)
            
            return {
                "success": True,
                "input_file": json_path,
                "output_file": output_parquet,
                "rows_converted": len(df)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "input_file": json_path,
                "output_file": output_parquet or "N/A"
            }
    
    def merge_csv_files(
        self,
        input_pattern: str,
        output_csv: str
    ) -> MergeResult:
        """Merge multiple CSV files matching pattern into single file."""
        
        try:
            input_files = glob.glob(input_pattern)
            
            if not input_files:
                return {
                    "success": False,
                    "error": f"No files found matching pattern: {input_pattern}",
                    "input_files": []
                }
            
            input_files.sort()  # Sort for consistent ordering
            
            all_dataframes = []
            total_rows = 0
            
            for file_path in input_files:
                try:
                    df = pd.read_csv(file_path)
                    all_dataframes.append(df)
                    total_rows += len(df)
                except Exception as e:
                    # Skip problematic files but continue
                    continue
            
            if not all_dataframes:
                return {
                    "success": False,
                    "error": "No valid CSV files found to merge",
                    "input_files": input_files
                }
            
            # Concatenate all DataFrames
            merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
            
            # Save merged file
            merged_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            
            return {
                "success": True,
                "input_files": input_files,
                "output_file": output_csv,
                "total_rows": len(merged_df)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "input_files": input_files if 'input_files' in locals() else [],
                "output_file": output_csv
            }
    
    def summarize_csv(
        self,
        csv_path: str,
        max_rows_preview: int = 5
    ) -> SummaryResult:
        """Provide summary information about a CSV file."""
        
        try:
            # Get file info
            if not os.path.exists(csv_path):
                return {
                    "success": False,
                    "error": f"File not found: {csv_path}",
                    "file_path": csv_path
                }
            
            # Read CSV
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # Get headers and basic info
            headers = df.columns.tolist()
            rows = len(df)
            columns = len(headers)
            
            # Create preview data
            preview_df = df.head(max_rows_preview)
            preview = preview_df.to_dict('records')
            
            return {
                "success": True,
                "file_path": csv_path,
                "rows": rows,
                "columns": columns,
                "headers": headers,
                "preview": preview
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": csv_path
            }
    
    def list_files(
        self,
        pattern: str = "*",
        directory: str = OUTPUT_DIR
    ) -> List[FileInfo]:
        """List files in directory matching pattern."""
        
        ensure_dir(directory)
        files = []
        
        try:
            search_pattern = os.path.join(directory, pattern)
            
            for filepath in glob.glob(search_pattern):
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


# Global service instance
file_processor_service = FileProcessorService()