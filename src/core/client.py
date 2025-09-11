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


# Global client instance
api_client = NaramarketAPIClient()