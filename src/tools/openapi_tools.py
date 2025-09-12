"""OpenAPI-based MCP tools for Naramarket APIs."""

import os
from typing import Any, Dict, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("fastmcp>=2.0.0 is required for OpenAPI integration")

from ..core.config import get_service_key

# OpenAPI 기반 FastMCP 서버 생성
def create_openapi_mcp() -> FastMCP:
    """Create FastMCP server from OpenAPI specification."""
    openapi_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "openapi.yaml"
    )
    
    if not os.path.exists(openapi_path):
        raise FileNotFoundError(f"OpenAPI spec not found: {openapi_path}")
    
    # FastMCP 2.0의 OpenAPI 자동 생성 기능 사용
    mcp = FastMCP.from_openapi(openapi_path)
    
    return mcp


class OpenAPITools:
    """Enhanced tools for OpenAPI-based Naramarket operations."""
    
    def __init__(self):
        self.service_key = get_service_key()
        self.base_url = "http://apis.data.go.kr/1230000"
    
    def get_bid_announcement_info(
        self,
        num_rows: int = 10,
        page_no: int = 1,
        bid_notice_start_date: Optional[str] = None,
        bid_notice_end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """입찰공고정보 조회 (getDataSetOpnStdBidPblancInfo)."""
        endpoint = f"{self.base_url}/ao/PubDataOpnStdService/getDataSetOpnStdBidPblancInfo"
        
        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_rows,
            "pageNo": page_no,
            "type": "json"
        }
        
        if bid_notice_start_date:
            params["bidNtceBgnDt"] = bid_notice_start_date
        if bid_notice_end_date:
            params["bidNtceEndDt"] = bid_notice_end_date
            
        # FastMCP의 자동 생성된 클라이언트 사용 시뮬레이션
        return {
            "endpoint": endpoint,
            "params": params,
            "description": "입찰공고정보 조회",
            "method": "GET"
        }
    
    def get_successful_bid_info(
        self,
        business_div_code: str,
        num_rows: int = 10,
        page_no: int = 1,
        opening_start_date: Optional[str] = None,
        opening_end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """낙찰정보 조회 (getDataSetOpnStdScsbidInfo)."""
        endpoint = f"{self.base_url}/ao/PubDataOpnStdService/getDataSetOpnStdScsbidInfo"
        
        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_rows,
            "pageNo": page_no,
            "bsnsDivCd": business_div_code,
            "type": "json"
        }
        
        if opening_start_date:
            params["opengBgnDt"] = opening_start_date
        if opening_end_date:
            params["opengEndDt"] = opening_end_date
            
        return {
            "endpoint": endpoint,
            "params": params,
            "description": "낙찰정보 조회",
            "method": "GET"
        }
    
    def get_contract_info(
        self,
        num_rows: int = 10,
        page_no: int = 1,
        contract_start_date: Optional[str] = None,
        contract_end_date: Optional[str] = None,
        institution_div_code: Optional[str] = None,
        institution_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """계약정보 조회 (getDataSetOpnStdCntrctInfo)."""
        endpoint = f"{self.base_url}/ao/PubDataOpnStdService/getDataSetOpnStdCntrctInfo"
        
        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_rows,
            "pageNo": page_no,
            "type": "json"
        }
        
        if contract_start_date:
            params["cntrctCnclsBgnDate"] = contract_start_date
        if contract_end_date:
            params["cntrctCnclsEndDate"] = contract_end_date
        if institution_div_code:
            params["insttDivCd"] = institution_div_code
        if institution_code:
            params["insttCd"] = institution_code
            
        return {
            "endpoint": endpoint,
            "params": params,
            "description": "계약정보 조회",
            "method": "GET"
        }
    
    def get_total_procurement_status(
        self,
        num_rows: int = 10,
        page_no: int = 1,
        search_base_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """전체 공공조달 현황 (getTotlPubPrcrmntSttus)."""
        endpoint = f"{self.base_url}/at/PubPrcrmntStatInfoService/getTotlPubPrcrmntSttus"
        
        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_rows,
            "pageNo": page_no,
            "type": "json"
        }
        
        if search_base_year:
            params["srchBssYear"] = search_base_year
            
        return {
            "endpoint": endpoint,
            "params": params,
            "description": "전체 공공조달 현황",
            "method": "GET"
        }
    
    def get_mas_contract_product_info(
        self,
        num_rows: int = 10,
        page_no: int = 1,
        registration_start_date: Optional[str] = None,
        registration_end_date: Optional[str] = None,
        product_name: Optional[str] = None,
        product_id: Optional[str] = None,
        contract_company_name: Optional[str] = None,
        change_start_date: Optional[str] = None,
        change_end_date: Optional[str] = None,
        product_certification: Optional[str] = None
    ) -> Dict[str, Any]:
        """다수공급자계약 품목정보 조회 (getMASCntrctPrdctInfoList) - 핵심 API."""
        endpoint = f"{self.base_url}/at/ShoppingMallPrdctInfoService/getMASCntrctPrdctInfoList"
        
        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_rows,
            "pageNo": page_no,
            "type": "json"
        }
        
        if registration_start_date:
            params["rgstDtBgnDt"] = registration_start_date
        if registration_end_date:
            params["rgstDtEndDt"] = registration_end_date
        if product_name:
            params["prdctClsfcNoNm"] = product_name
        if product_id:
            params["prdctIdntNo"] = product_id
        if contract_company_name:
            params["cntrctCorpNm"] = contract_company_name
        if change_start_date:
            params["chgDtBgnDt"] = change_start_date
        if change_end_date:
            params["chgDtEndDt"] = change_end_date
        if product_certification:
            params["prodctCertYn"] = product_certification
            
        return {
            "endpoint": endpoint,
            "params": params,
            "description": "다수공급자계약 품목정보 조회 - 핵심 API",
            "method": "GET"
        }


# Global instance
openapi_tools = OpenAPITools()