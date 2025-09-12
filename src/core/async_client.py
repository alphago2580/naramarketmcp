"""Async API client for improved performance."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .config import (
    BASE_LIST_URL,
    G2B_DETAIL_URL, 
    G2B_HEADERS,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    get_service_key
)

logger = logging.getLogger("naramarket.async_client")


class AsyncNaramarketClient:
    """Async API client for better performance with concurrent requests."""
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.service_key = get_service_key()
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(
            limit=50,  # Total connection pool size
            limit_per_host=20,  # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=60,  # Total timeout
            connect=10,  # Connection timeout
            sock_read=30,  # Socket read timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'NaramarketMCP/1.0 (aiohttp)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _retry_request(self, coro, *args, **kwargs):
        """Retry logic wrapper for async requests."""
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed")
        
        raise last_exception
    
    async def call_list_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call list API with async/await."""
        return await self._retry_request(self._call_list_api_impl, params)
    
    async def _call_list_api_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of async list API call."""
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async with statement.")
        
        api_params = {
            "serviceKey": self.service_key,
            "numOfRows": params.get("numOfRows", 100),
            "pageNo": params.get("pageNo", 1),
            **params
        }
        
        logger.debug(f"Calling async list API with params: {api_params}")
        
        async with self.semaphore:  # Limit concurrent requests
            async with self.session.get(BASE_LIST_URL, params=api_params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"Async list API response received: {len(str(data))} chars")
                return data
    
    async def call_detail_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call detail API with async/await."""
        return await self._retry_request(self._call_detail_api_impl, payload)
    
    async def _call_detail_api_impl(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of async detail API call."""
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async with statement.")
        
        logger.debug(f"Calling async detail API with payload: {payload}")
        
        async with self.semaphore:  # Limit concurrent requests
            async with self.session.post(
                G2B_DETAIL_URL,
                headers=G2B_HEADERS,
                data=json.dumps(payload)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"Async detail API response received: {len(str(data))} chars")
                return data
    
    async def call_multiple_detail_apis(
        self,
        payloads: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Call multiple detail APIs concurrently."""
        tasks = [self.call_detail_api(payload) for payload in payloads]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stream_list_api(self, params: Dict[str, Any]):
        """
        list API를 호출하고 응답을 청크(chunk) 단위로 스트리밍합니다.
        메모리에 담기 어려운 대용량 응답을 처리하는 데 적합합니다.
        """
        if not self.session:
            raise RuntimeError("클라이언트 세션이 초기화되지 않았습니다. async with 구문을 사용하세요.")

        api_params = {
            "serviceKey": self.service_key,
            "numOfRows": params.get("numOfRows", 100),
            "pageNo": params.get("pageNo", 1),
            **params
        }

        logger.debug(f"스트리밍 (async list API) 파라미터: {api_params}")

        async with self.semaphore:
            try:
                async with self.session.get(BASE_LIST_URL, params=api_params) as response:
                    response.raise_for_status()
                    # 응답 콘텐츠의 청크를 순회하며 반환(yield)합니다.
                    async for chunk in response.content.iter_chunked(8192):
                        yield chunk
            except aiohttp.ClientError as e:
                logger.error(f"API 스트림 중 에러 발생: {e}")
                raise # 예외를 다시 발생시켜 호출자가 처리하도록 함
    
    async def crawl_page_with_details(
        self,
        category: str,
        page_no: int,
        num_rows: int,
        inqry_bgn_date: str,
        inqry_end_date: str
    ) -> Dict[str, Any]:
        """Crawl a single page and get details for all items concurrently."""
        
        # First get the list
        list_params = {
            "pageNo": page_no,
            "numOfRows": num_rows,
            "type": "json",
            "inqryBgnDate": inqry_bgn_date,
            "inqryEndDate": inqry_end_date,
            "dtilPrdctClsfcNoNm": category,
            "inqryDiv": 1,
        }
        
        try:
            list_data = await self.call_list_api(list_params)
            body = list_data.get("response", {}).get("body", {})
            items = body.get("items", [])
            
            # Normalize items to list
            if isinstance(items, dict):
                items = items.get("item", items)
                if isinstance(items, dict):
                    items = [items]
            elif not isinstance(items, list):
                items = []
            
            if not items:
                return {
                    "success": True,
                    "page_no": page_no,
                    "items": [],
                    "total_items": 0,
                    "success_details": 0,
                    "failed_details": 0
                }
            
            # Get details for all items concurrently
            from .utils import extract_g2b_params
            
            detail_payloads = [extract_g2b_params(item) for item in items]
            detail_responses = await self.call_multiple_detail_apis(detail_payloads)
            
            # Combine list items with detail responses
            enhanced_items = []
            success_details = 0
            failed_details = 0
            
            for i, (item, detail_response) in enumerate(zip(items, detail_responses)):
                enhanced_item = item.copy()
                
                if isinstance(detail_response, Exception):
                    # Detail API failed
                    enhanced_item["attributes"] = {}
                    enhanced_item["detail_success"] = False
                    enhanced_item["detail_error"] = str(detail_response)
                    failed_details += 1
                else:
                    # Parse detail response
                    attributes = {}
                    result_list = detail_response.get("resultList", [])
                    
                    if isinstance(result_list, list):
                        for attr_item in result_list:
                            if isinstance(attr_item, dict):
                                attr_name = attr_item.get("prdctAtrbNm", "")
                                attr_value = attr_item.get("prdctAtrbVl", "")
                                if attr_name and attr_value:
                                    attributes[attr_name] = attr_value
                    
                    enhanced_item["attributes"] = attributes
                    enhanced_item["detail_success"] = True
                    success_details += 1
                
                enhanced_items.append(enhanced_item)
            
            return {
                "success": True,
                "page_no": page_no,
                "items": enhanced_items,
                "total_items": len(enhanced_items),
                "success_details": success_details,
                "failed_details": failed_details
            }
            
        except Exception as e:
            logger.error(f"Error crawling page {page_no}: {e}")
            return {
                "success": False,
                "page_no": page_no,
                "error": str(e),
                "items": [],
                "total_items": 0,
                "success_details": 0,
                "failed_details": 0
            }
    
    async def crawl_multiple_pages(
        self,
        category: str,
        start_page: int,
        end_page: int,
        num_rows: int,
        inqry_bgn_date: str,
        inqry_end_date: str
    ) -> List[Dict[str, Any]]:
        """Crawl multiple pages concurrently."""
        
        tasks = [
            self.crawl_page_with_details(
                category=category,
                page_no=page_no,
                num_rows=num_rows,
                inqry_bgn_date=inqry_bgn_date,
                inqry_end_date=inqry_end_date
            )
            for page_no in range(start_page, end_page + 1)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)


# Global async client instance (to be used with async context manager)
async_client = AsyncNaramarketClient()