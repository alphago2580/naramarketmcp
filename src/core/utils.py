"""Utility functions for Naramarket MCP Server."""

import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict

from .config import DATE_FMT


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def now_ts() -> str:
    """Return current timestamp as string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def date_range_days_back(days_back: int = 7) -> Dict[str, str]:
    """Generate date range for API calls going back specified days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return {
        "inqryBgnDt": start_date.strftime(DATE_FMT),
        "inqryEndDt": end_date.strftime(DATE_FMT)
    }


def extract_g2b_params(api_item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract G2B parameters from API item for detailed attribute lookup."""
    return {
        "prdctClsfcNoFst": api_item.get("prdctClsfcNoFst", ""),
        "prdctClsfcNoScnd": api_item.get("prdctClsfcNoScnd", ""),  
        "prdctClsfcNoThrd": api_item.get("prdctClsfcNoThrd", ""),
        "prdctClsfcNoFrth": api_item.get("prdctClsfcNoFrth", ""),
        "prdctClsfcNoFfth": api_item.get("prdctClsfcNoFfth", ""),
        "prdctStndrdNo": api_item.get("prdctStndrdNo", ""),
        "mnfcturCmpnyNm": api_item.get("mnfcturCmpnyNm", ""),
        "mfgCmpnyNm": api_item.get("mfgCmpnyNm", ""),
        "mfgCmpnyNm2": api_item.get("mfgCmpnyNm2", ""),
        "mfgCmpnyNm3": api_item.get("mfgCmpnyNm3", ""),
        "mfgCmpnyNm4": api_item.get("mfgCmpnyNm4", ""),
        "mfgCmpnyNm5": api_item.get("mfgCmpnyNm5", ""),
    }


def sanitize_column_name(name: str) -> str:
    """Sanitize column name for CSV/DataFrame usage."""
    if not isinstance(name, str):
        name = str(name)
    # Replace problematic characters with underscores
    name = re.sub(r'[^\w가-힣]', '_', name)
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name if name else 'unknown'


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def calculate_elapsed_time(start_time: float) -> float:
    """Calculate elapsed time in seconds."""
    return round(time.time() - start_time, 2)