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

# 출력 디렉토리 설정
OUTPUT_DIR = "data"

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
    """Get Naramarket service key with priority: user key > builtin key."""
    import logging
    from .key_utils import get_builtin_service_key

    logger = logging.getLogger(__name__)

    try:
        # 1순위: smithery.ai 설정
        config = parse_smithery_config()
        user_key = config.get("naramarketServiceKey")

        # 2순위: 환경변수
        if not user_key or user_key in ["your-api-key-here", "SECURE_API_KEY_REQUIRED", "", "null", "undefined"]:
            user_key = os.environ.get("NARAMARKET_SERVICE_KEY")

        # 사용자가 유효한 키를 제공한 경우
        if user_key and user_key not in ["your-api-key-here", "SECURE_API_KEY_REQUIRED", "", "null", "undefined"]:
            logger.info(f"Using user-provided API key (length: {len(user_key)})")
            return user_key

        # 3순위: 내장 운영 키 사용
        builtin_key = get_builtin_service_key()
        if builtin_key:
            logger.info(f"Using builtin production API key (length: {len(builtin_key)})")
            return builtin_key

        # 모든 키가 없는 경우
        logger.error("No API service key available")
        raise ValueError("No API key available. Either provide NARAMARKET_SERVICE_KEY or ensure builtin key is configured")

    except Exception as e:
        logger.error(f"Error retrieving service key: {e}")
        raise

def get_api_environment() -> str:
    """Get API environment from smithery.ai config or environment."""
    config = parse_smithery_config()
    return config.get("apiEnvironment", os.environ.get("API_ENVIRONMENT", "production"))