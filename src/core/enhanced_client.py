"""Enhanced API client for all Korean government procurement APIs."""

import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

import requests

from .config import (
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    get_service_key
)

logger = logging.getLogger("naramarket.enhanced_client")


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


class EnhancedAPIClient:
    """Enhanced API client for all Korean government procurement services."""

    def __init__(self):
        self.service_key = get_service_key()
        self.session = requests.Session()

        # Service base URLs
        self.service_urls = {
            "public_data_standard": "http://apis.data.go.kr/1230000/ao/PubDataOpnStdService",
            "procurement_statistics": "http://apis.data.go.kr/1230000/at/PubPrcrmntStatInfoService",
            "product_list": "http://apis.data.go.kr/1230000/ao/ThngListInfoService",
            "shopping_mall": "http://apis.data.go.kr/1230000/at/ShoppingMallPrdctInfoService"
        }

        # Operation mappings for each service
        self.operation_mappings = {
            "public_data_standard": {
                "getDataSetOpnStdBidPblancInfo": "getDataSetOpnStdBidPblancInfo",
                "getDataSetOpnStdScsbidInfo": "getDataSetOpnStdScsbidInfo",
                "getDataSetOpnStdCntrctInfo": "getDataSetOpnStdCntrctInfo"
            },
            "procurement_statistics": {
                "getTotlPubPrcrmntSttus": "getTotlPubPrcrmntSttus",
                "getInsttDivAccotPrcrmntSttus": "getInsttDivAccotPrcrmntSttus",
                "getEntrprsDivAccotPrcrmntSttus": "getEntrprsDivAccotPrcrmntSttus",
                "getCntrctMthdAccotSttus": "getCntrctMthdAccotSttus",
                "getRgnLmtSttus": "getRgnLmtSttus",
                "getRgnDutyCmmnCntrctSttus": "getRgnDutyCmmnCntrctSttus",
                "getPrcrmntObjectBsnsObjAccotSttus": "getPrcrmntObjectBsnsObjAccotSttus",
                "getDminsttAccotEntrprsDivAccotArslt": "getDminsttAccotEntrprsDivAccotArslt",
                "getDminsttAccotCntrctMthdAccotArslt": "getDminsttAccotCntrctMthdAccotArslt",
                "getDminsttAccotBsnsObjAccotArslt": "getDminsttAccotBsnsObjAccotArslt",
                "getDminsttAccotSystmTyAccotArslt": "getDminsttAccotSystmTyAccotArslt",
                "getPrcrmntEntrprsAccotCntrctMthdAccotArslt": "getPrcrmntEntrprsAccotCntrctMthdAccotArslt",
                "getPrcrmntEntrprsAccotBsnsObjAccotArslt": "getPrcrmntEntrprsAccotBsnsObjAccotArslt",
                "getPrdctIdntNoServcAccotArslt": "getPrdctIdntNoServcAccotArslt"
            },
            "product_list": {
                "getThngGuidanceMapInfo": "getThngGuidanceMapInfo",
                "getThngPrdnmLocplcAccotListInfoInfoPrdlstSearch": "getThngPrdnmLocplcAccotListInfoInfoPrdlstSearch",
                "getThngPrdnmLocplcAccotListInfoInfoPrdnmSearch": "getThngPrdnmLocplcAccotListInfoInfoPrdnmSearch",
                "getThngPrdnmLocplcAccotListInfoInfoLocplcSearch": "getThngPrdnmLocplcAccotListInfoInfoLocplcSearch",
                "getThngListClChangeHistInfo": "getThngListClChangeHistInfo",
                "getLsfgdNdPrdlstChghstlnfoSttus": "getLsfgdNdPrdlstChghstlnfoSttus",
                "getPrdctClsfcNoUnit2Info": "getPrdctClsfcNoUnit2Info",
                "getPrdctClsfcNoUnit4Info": "getPrdctClsfcNoUnit4Info",
                "getPrdctClsfcNoUnit6Info": "getPrdctClsfcNoUnit6Info",
                "getPrdctClsfcNoUnit8Info": "getPrdctClsfcNoUnit8Info",
                "getPrdctClsfcNoUnit10Info": "getPrdctClsfcNoUnit10Info",
                "getPrdctClsfcNoChgHstry": "getPrdctClsfcNoChgHstry"
            },
            "shopping_mall": {
                "getMASCntrctPrdctInfoList": "getMASCntrctPrdctInfoList",
                "getUcntrctPrdctInfoList": "getUcntrctPrdctInfoList",
                "getThptyUcntrctPrdctInfoList": "getThptyUcntrctPrdctInfoList",
                "getDlvrReqInfoList": "getDlvrReqInfoList",
                "getDlvrReqDtlInfoList": "getDlvrReqDtlInfoList",
                "getShoppingMallPrdctInfoList": "getShoppingMallPrdctInfoList",
                "getVntrPrdctOrderDealDtlsInfoList": "getVntrPrdctOrderDealDtlsInfoList",
                "getSpcifyPrdlstPrcureInfoList": "getSpcifyPrdlstPrcureInfoList",
                "getSpcifyPrdlstPrcureTotList": "getSpcifyPrdlstPrcureTotList"
            }
        }

    @retryable
    def call_api(self, service_type: str, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call any Korean government procurement API with operation parameter."""

        # Validate service type
        if service_type not in self.service_urls:
            raise ValueError(f"Invalid service_type: {service_type}. Must be one of: {list(self.service_urls.keys())}")

        # Validate operation
        if operation not in self.operation_mappings[service_type]:
            raise ValueError(f"Invalid operation '{operation}' for service '{service_type}'. Available operations: {list(self.operation_mappings[service_type].keys())}")

        # Build API URL
        base_url = self.service_urls[service_type]
        endpoint_operation = self.operation_mappings[service_type][operation]
        api_url = f"{base_url}/{endpoint_operation}"

        # Prepare API parameters
        api_params = {
            "ServiceKey": self.service_key,
            "numOfRows": params.get("numOfRows", 10),
            "pageNo": params.get("pageNo", 1),
            "type": params.get("type", "json"),
            **{k: v for k, v in params.items() if k not in ["numOfRows", "pageNo", "type"]}
        }

        logger.info(f"Calling {service_type}.{operation} with params: {api_params}")

        try:
            response = self.session.get(api_url, params=api_params, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info(f"API response received: {len(str(data))} chars")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text (first 500 chars): {response.text[:500]}")
            raise
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

    def get_available_operations(self, service_type: str) -> Dict[str, Any]:
        """Get list of available operations for a service type."""
        if service_type not in self.operation_mappings:
            return {"error": f"Invalid service_type: {service_type}"}

        return {
            "service_type": service_type,
            "base_url": self.service_urls[service_type],
            "available_operations": list(self.operation_mappings[service_type].keys()),
            "total_operations": len(self.operation_mappings[service_type])
        }

    def get_all_services_info(self) -> Dict[str, Any]:
        """Get information about all available services."""
        return {
            "services": {
                service_type: {
                    "base_url": self.service_urls[service_type],
                    "operations_count": len(self.operation_mappings[service_type]),
                    "operations": list(self.operation_mappings[service_type].keys())
                }
                for service_type in self.service_urls.keys()
            },
            "total_services": len(self.service_urls),
            "total_operations": sum(len(ops) for ops in self.operation_mappings.values())
        }


# Global enhanced client instance
enhanced_api_client = EnhancedAPIClient()