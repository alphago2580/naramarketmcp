"""API client for Naramarket services with retry logic."""

import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict

import requests

from .config import (
    BASE_LIST_URL, 
    G2B_DETAIL_URL, 
    G2B_HEADERS,
    MAX_RETRIES, 
    RETRY_BACKOFF_BASE,
    get_service_key
)

logger = logging.getLogger("naramarket.client")


def retryable(func: Callable) -> Callable:
    """Decorator to add retry logic to API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed for {func.__name__}")
        
        raise last_exception
    return wrapper


class NaramarketAPIClient:
    """API client for Naramarket services."""
    
    def __init__(self):
        self.service_key = get_service_key()
        self.session = requests.Session()
    
    @retryable
    def call_list_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Naramarket list API with retry logic."""
        api_params = {
            "serviceKey": self.service_key,
            "numOfRows": params.get("numOfRows", 100),
            "pageNo": params.get("pageNo", 1),
            **params
        }
        
        logger.info(f"Calling list API with params: {api_params}")
        
        response = self.session.get(BASE_LIST_URL, params=api_params, timeout=30)
        response.raise_for_status()
        
        try:
            data = response.json()
            logger.info(f"List API response received: {len(str(data))} chars")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text (first 500 chars): {response.text[:500]}")
            raise
    
    @retryable 
    def call_detail_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call the G2B detail API with retry logic."""
        logger.info(f"Calling detail API with payload: {payload}")
        
        response = self.session.post(
            G2B_DETAIL_URL,
            headers=G2B_HEADERS,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        
        try:
            data = response.json()
            logger.info(f"Detail API response received: {len(str(data))} chars")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text (first 500 chars): {response.text[:500]}")
            raise
    
    def fetch_product_list(
        self,
        category: str,
        page_no: int = 1,
        num_rows: int = 100,
        inqry_bgn_date: str = None,
        inqry_end_date: str = None
    ) -> Dict[str, Any]:
        """Fetch product list for a category."""
        params = {
            "prdctClsfcNoNm": category,
            "pageNo": page_no,
            "numOfRows": num_rows
        }
        
        if inqry_bgn_date:
            params["inqryBgnDate"] = inqry_bgn_date
        if inqry_end_date:
            params["inqryEndDate"] = inqry_end_date
            
        raw_response = self.call_list_api(params)
        
        # Parse response format
        response = raw_response.get("response", {})
        body = response.get("body", {})
        
        return {
            "items": body.get("items", []),
            "totalCount": body.get("totalCount", 0),
            "pageNo": body.get("pageNo", page_no),
            "numOfRows": body.get("numOfRows", num_rows)
        }
    
    def get_detailed_attributes(self, api_item: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed product attributes from G2B API (Enhanced FastMCP 2.0).
        
        이 함수는 나라마켓 서버의 핵심 기능으로 절대 삭제하지 마세요!
        """
        try:
            # Enhanced validation
            if not api_item or not isinstance(api_item, dict):
                return {
                    "success": False,
                    "error": "Invalid api_item provided",
                    "error_type": "validation_error"
                }
            
            # Build payload for G2B API
            payload = {}
            
            # Extract key fields with enhanced error handling
            if "prdctClsfcNoNm" in api_item:
                payload["prdctClsfcNoNm"] = api_item["prdctClsfcNoNm"]
            
            if "prdctStndrdNm" in api_item:
                payload["prdctStndrdNm"] = api_item["prdctStndrdNm"]
                
            if not payload:
                return {
                    "success": False,
                    "error": "No suitable fields found in api_item for G2B query",
                    "error_type": "missing_fields",
                    "payload": payload,
                    "debug_info": {
                        "available_keys": list(api_item.keys())
                    }
                }
            
            # Call G2B API
            response_data = self.call_detail_api(payload)
            
            # Parse attributes from response
            attributes = {}
            if response_data and "data" in response_data:
                attributes = response_data["data"]
            elif response_data and "result" in response_data:
                attributes = response_data["result"]
            else:
                attributes = response_data
            
            # Enhanced success response
            return {
                "success": True,
                "attributes": attributes,
                "payload": payload,
                "debug_info": {
                    "response_size": len(str(response_data)),
                    "attributes_keys": list(attributes.keys()) if isinstance(attributes, dict) else []
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_error",
                "payload": payload if 'payload' in locals() else {},
                "debug_info": {
                    "exception_type": type(e).__name__
                }
            }


# Global client instance - lazy initialization
_api_client = None

def get_api_client() -> NaramarketAPIClient:
    """Get or create API client instance with lazy initialization."""
    global _api_client
    if _api_client is None:
        _api_client = NaramarketAPIClient()
    return _api_client

# For backward compatibility
def api_client():
    """Backward compatible property access."""
    return get_api_client()