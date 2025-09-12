"""Configuration and constants for Naramarket FastMCP 2.0 Server."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

APP_NAME = "naramarket-fastmcp-2"
SERVER_VERSION = "2.0.0"  # FastMCP 2.0 버전

# API 설정 (파일 저장 제거로 인해 더 간단해짐)
DEFAULT_NUM_ROWS = 100
DEFAULT_DELAY_SEC = 0.1
DEFAULT_MAX_PAGES = 999
DATE_FMT = "%Y%m%d"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.75

# 기존 API 엔드포인트 (호환성 유지)
BASE_LIST_URL = "http://apis.data.go.kr/1230000/at/ShoppingMallPrdctInfoService/getShoppingMallPrdctInfoList"
G2B_DETAIL_URL = "https://shop.g2b.go.kr/gm/gms/gmsf/GdsDtlInfo/selectPdctAtrbInfo.do"

# OpenAPI 기본 URL
OPENAPI_BASE_URL = "http://apis.data.go.kr/1230000"
OPENAPI_SPEC_PATH = "openapi.yaml"

G2B_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "Referer": "https://shop.g2b.go.kr/",
    "Origin": "https://shop.g2b.go.kr",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

# 기존 카테고리 (호환성 유지)
CATEGORIES = {
    "데스크톱컴퓨터": "desktop_computers",
    "운영체제": "operating_system",
    "DVD드라이브": "dvd_drive",
    "마그네틱카드판독기": "magnetic_card_reader",
}

# OpenAPI 업무 구분 코드
BUSINESS_DIVISION_CODES = {
    "GOODS": "1",      # 물품
    "FOREIGN": "2",    # 외자
    "CONSTRUCTION": "3", # 공사
    "SERVICE": "5"      # 용역
}

# 기관 구분 코드
INSTITUTION_DIVISION_CODES = {
    "CONTRACT": "1",   # 계약기관
    "DEMAND": "2"       # 수요기관
}

def parse_smithery_config() -> Dict[str, Any]:
    """Parse configuration from smithery.ai query parameters with error handling."""
    import urllib.parse
    from typing import Any, Dict
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get query string from environment (smithery.ai passes this)
    query_string = os.environ.get("QUERY_STRING", "")
    
    if not query_string:
        # Fallback to standard environment variables
        return {
            "naramarketServiceKey": os.environ.get("NARAMARKET_SERVICE_KEY", ""),
            "apiEnvironment": os.environ.get("API_ENVIRONMENT", "production")
        }
    
    try:
        # Parse query parameters with error handling
        params = urllib.parse.parse_qs(query_string)
        config = {}
        
        # Handle dot notation (e.g., config.naramarketServiceKey=value)
        for key, values in params.items():
            if key.startswith("config.") or "." in key:
                try:
                    # Convert dot notation to nested structure
                    parts = key.replace("config.", "").split(".")
                    current = config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = values[0] if values else ""
                except (IndexError, KeyError) as e:
                    logger.warning(f"Error parsing config key '{key}': {e}")
                    continue
            else:
                config[key] = values[0] if values else ""
        
        # Flatten if nested under config
        if "config" in config and isinstance(config["config"], dict):
            config = config["config"]
        
        return config
    
    except Exception as e:
        logger.error(f"Error parsing smithery config from query string: {e}")
        # Return safe fallback configuration
        return {
            "naramarketServiceKey": os.environ.get("NARAMARKET_SERVICE_KEY", ""),
            "apiEnvironment": os.environ.get("API_ENVIRONMENT", "production")
        }

def get_service_key() -> str:
    """Get Naramarket service key from environment or smithery.ai config with secure handling."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # First try smithery.ai configuration
        config = parse_smithery_config()
        key = config.get("naramarketServiceKey")
        
        if not key:
            # Fallback to environment variable
            key = os.environ.get("NARAMARKET_SERVICE_KEY")
        
        if not key:
            logger.error("API service key not found in configuration")
            raise ValueError("naramarketServiceKey is required. Set via smithery.ai config or NARAMARKET_SERVICE_KEY environment variable")
        
        # Validate key format (should not be placeholder)
        if key in ["your-api-key-here", "SECURE_API_KEY_REQUIRED", "", "null", "undefined"]:
            logger.error("Invalid or placeholder API key detected")
            raise ValueError("Invalid API key. Please provide a valid naramarketServiceKey")
        
        # Log success without exposing the key
        logger.info(f"API service key loaded successfully (length: {len(key)})")
        return key
        
    except Exception as e:
        logger.error(f"Error retrieving service key: {e}")
        raise

def get_api_environment() -> str:
    """Get API environment from smithery.ai config or environment."""
    config = parse_smithery_config()
    return config.get("apiEnvironment", os.environ.get("API_ENVIRONMENT", "production"))