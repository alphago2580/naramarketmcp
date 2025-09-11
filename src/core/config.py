"""Configuration and constants for Naramarket MCP Server."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

APP_NAME = "naramarket-mcp"

try:
    from ... import __version__ as SERVER_VERSION  # type: ignore
except Exception:  # pragma: no cover
    SERVER_VERSION = "0.1.0"

OUTPUT_DIR = os.path.expanduser("~/mycode/naramarket_data")
DEFAULT_NUM_ROWS = 100
DEFAULT_DELAY_SEC = 0.1
DEFAULT_MAX_PAGES = 999
DATE_FMT = "%Y%m%d"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.75

BASE_LIST_URL = "http://apis.data.go.kr/1230000/at/ShoppingMallPrdctInfoService/getShoppingMallPrdctInfoList"
G2B_DETAIL_URL = "https://shop.g2b.go.kr/gm/gms/gmsf/GdsDtlInfo/selectPdctAtrbInfo.do"

G2B_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "Referer": "https://shop.g2b.go.kr/",
    "Origin": "https://shop.g2b.go.kr",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

CATEGORIES = {
    "데스크톱컴퓨터": "desktop_computers",
    "운영체제": "operating_system",
    "DVD드라이브": "dvd_drive",
    "마그네틱카드판독기": "magnetic_card_reader",
}

def get_service_key() -> str:
    """Get Naramarket service key from environment."""
    key = os.environ.get("NARAMARKET_SERVICE_KEY")
    if not key:
        raise ValueError("NARAMARKET_SERVICE_KEY environment variable is required")
    return key