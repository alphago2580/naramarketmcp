"""Tests for utility functions."""

import os
import sys
import tempfile
from datetime import datetime, timedelta

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.utils import (
    calculate_elapsed_time,
    date_range_days_back,
    ensure_dir,
    extract_g2b_params,
    format_file_size,
    now_ts,
    sanitize_column_name
)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_ensure_dir(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_subdir")
            assert not os.path.exists(test_dir)
            
            ensure_dir(test_dir)
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
            
            # Should not raise error if directory already exists
            ensure_dir(test_dir)
            assert os.path.exists(test_dir)
    
    def test_now_ts(self):
        """Test timestamp generation."""
        ts = now_ts()
        assert isinstance(ts, str)
        assert len(ts) > 0
        
        # Should be parseable as datetime
        parsed = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        assert isinstance(parsed, datetime)
    
    def test_date_range_days_back(self):
        """Test date range generation."""
        # Test default (7 days)
        range_data = date_range_days_back()
        assert "inqryBgnDt" in range_data
        assert "inqryEndDt" in range_data
        assert len(range_data["inqryBgnDt"]) == 8  # YYYYMMDD format
        assert len(range_data["inqryEndDt"]) == 8
        
        # Test custom days
        range_data = date_range_days_back(30)
        bgn_date = datetime.strptime(range_data["inqryBgnDt"], "%Y%m%d")
        end_date = datetime.strptime(range_data["inqryEndDt"], "%Y%m%d")
        diff = end_date - bgn_date
        assert diff.days == 30
    
    def test_extract_g2b_params(self):
        """Test G2B parameter extraction."""
        api_item = {
            "prdctClsfcNoFst": "123",
            "prdctClsfcNoScnd": "456", 
            "prdctStndrdNo": "STD001",
            "mnfcturCmpnyNm": "Test Company",
            "otherField": "ignored"
        }
        
        params = extract_g2b_params(api_item)
        
        assert params["prdctClsfcNoFst"] == "123"
        assert params["prdctClsfcNoScnd"] == "456"
        assert params["prdctStndrdNo"] == "STD001"
        assert params["mnfcturCmpnyNm"] == "Test Company"
        assert "otherField" not in params
        
        # Test with missing fields
        incomplete_item = {"prdctClsfcNoFst": "123"}
        params = extract_g2b_params(incomplete_item)
        assert params["prdctClsfcNoFst"] == "123"
        assert params["prdctClsfcNoScnd"] == ""  # Should default to empty string
    
    def test_sanitize_column_name(self):
        """Test column name sanitization."""
        # Test special characters
        assert sanitize_column_name("test column!@#") == "test_column___"
        assert sanitize_column_name("test__column") == "test_column"
        assert sanitize_column_name("__test__") == "test"
        assert sanitize_column_name("한글컬럼명") == "한글컬럼명"  # Korean should be preserved
        
        # Test edge cases
        assert sanitize_column_name("") == "unknown"
        assert sanitize_column_name("123") == "123"
        assert sanitize_column_name(None) == "unknown"
        assert sanitize_column_name(123) == "123"
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1536) == "1.5 KB"  # 1.5 KB
    
    def test_calculate_elapsed_time(self):
        """Test elapsed time calculation."""
        import time
        
        start_time = time.time()
        time.sleep(0.1)  # Sleep for 0.1 seconds
        elapsed = calculate_elapsed_time(start_time)
        
        assert isinstance(elapsed, float)
        assert 0.09 <= elapsed <= 0.2  # Should be around 0.1 seconds with some tolerance


@pytest.fixture
def sample_api_item():
    """Sample API item for testing."""
    return {
        "prdctClsfcNoFst": "10",
        "prdctClsfcNoScnd": "101",
        "prdctClsfcNoThrd": "10101",
        "prdctClsfcNoFrth": "1010101", 
        "prdctClsfcNoFfth": "101010101",
        "prdctStndrdNo": "STD-2024-001",
        "mnfcturCmpnyNm": "Samsung Electronics",
        "mfgCmpnyNm": "Samsung",
        "mfgCmpnyNm2": "",
        "mfgCmpnyNm3": "",
        "mfgCmpnyNm4": "",
        "mfgCmpnyNm5": "",
        "prdctNm": "Test Product",
        "prdctPrc": "1000000"
    }


def test_extract_g2b_params_complete(sample_api_item):
    """Test G2B parameter extraction with complete data."""
    params = extract_g2b_params(sample_api_item)
    
    expected_keys = [
        "prdctClsfcNoFst", "prdctClsfcNoScnd", "prdctClsfcNoThrd",
        "prdctClsfcNoFrth", "prdctClsfcNoFfth", "prdctStndrdNo",
        "mnfcturCmpnyNm", "mfgCmpnyNm", "mfgCmpnyNm2",
        "mfgCmpnyNm3", "mfgCmpnyNm4", "mfgCmpnyNm5"
    ]
    
    for key in expected_keys:
        assert key in params
        assert params[key] == sample_api_item.get(key, "")
    
    # Should not include other fields
    assert "prdctNm" not in params
    assert "prdctPrc" not in params


if __name__ == "__main__":
    pytest.main([__file__])