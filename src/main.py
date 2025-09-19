"""Main application entry point for Naramarket MCP 2.0 Server with OpenAPI integration."""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("fastmcp>=2.0.0 is required. pip install fastmcp>=2.0.0")

from .core.config import APP_NAME
from .core.models import (
    CrawlListResult,
    DetailResult,
    ServerInfo
)
from .core.response_filter import filter_response_fields, get_available_fields, get_all_response_formats
from .core.key_utils import get_key_status
from .tools.naramarket import naramarket_tools
from .tools.enhanced_tools import enhanced_tools
from .tools.naramarket_search_apis import naramarket_search_apis
from .core.cors_middleware import apply_cors_to_fastmcp
from .core.fastmcp_cors_patch import patch_fastmcp_for_smithery, apply_fastmcp_cors_patch


# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("naramarket")

# Initialize FastMCP 2.0 with CORS configuration for Smithery.ai
try:
    mcp = FastMCP(APP_NAME)

    # Configure CORS for Smithery.ai deployment
    # This ensures proper browser access to MCP endpoints
    cors_config = {
        "allow_origins": ["*"],  # Allow all origins for Smithery.ai
        "allow_credentials": True,  # Allow credentials
        "allow_methods": ["GET", "POST", "OPTIONS"],  # Required HTTP methods
        "allow_headers": ["*", "Content-Type", "Authorization"],  # All headers including custom ones
        "expose_headers": ["mcp-session-id", "mcp-protocol-version"]  # MCP-specific headers
    }

    # Note: CORS configuration for Smithery.ai
    # FastMCP 2.0 has built-in CORS support that should handle browser requests
    # Additional CORS headers will be managed by Smithery.ai infrastructure
    logger.info("✅ CORS configuration ready for Smithery.ai deployment")
    logger.info("   - FastMCP 2.0 built-in CORS support enabled")
    logger.info("   - Smithery.ai infrastructure will handle additional CORS requirements")

    logger.info(f"FastMCP 2.0 initialized: {APP_NAME}")
except Exception as e:
    raise RuntimeError(f"Failed to init FastMCP 2.0: {e}")


# Register MCP Tools
@mcp.tool(
    name="crawl_list",
    description="Fetch product list for a category from Nara Market API"
)
def crawl_list(
    category: str,
    page_no: int = 1,
    num_rows: int = 100,
    days_back: int = 7,
    inqry_bgn_date: Optional[str] = None,
    inqry_end_date: Optional[str] = None,
) -> CrawlListResult:
    """Fetch product list for a category from Nara Market API.
    
    Args:
        category: Product category name
        page_no: Page number to fetch (default 1)
        num_rows: Number of rows per page (default 100)
        days_back: Days to go back if dates not provided (default 7)
        inqry_bgn_date: Start date in YYYYMMDD format
        inqry_end_date: End date in YYYYMMDD format
        
    Returns:
        CrawlListResult with success status and data
    """
    return naramarket_tools.crawl_list(
        category=category,
        page_no=page_no,
        num_rows=num_rows,
        days_back=days_back,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date
    )


@mcp.tool(
    name="get_detailed_attributes",
    description="Get detailed product attributes from G2B API"
)
def get_detailed_attributes(api_item: Dict[str, Any]) -> DetailResult:
    """Get detailed product attributes from G2B API.
    
    Args:
        api_item: Product item from list API
        
    Returns:
        DetailResult with attributes or error
    """
    return naramarket_tools.get_detailed_attributes(api_item)


@mcp.tool()
def server_info() -> ServerInfo:
    """Get server status and available tools list.

    Returns:
        ServerInfo with server details
    """
    return naramarket_tools.server_info()


# Enhanced Korean Government Procurement APIs (Parameterized)
@mcp.tool()
def call_procurement_statistics_api(
    operation: str,
    num_rows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
    page_no: int = 1,
    search_base_year: Optional[str] = None,
    search_base_month_start: Optional[str] = None,
    search_base_month_end: Optional[str] = None,
    demand_institution_code: Optional[str] = None,
    demand_institution_name: Optional[str] = None,
    corp_unity_no: Optional[str] = None,
    corp_name: Optional[str] = None,
    product_classification_no: Optional[str] = None,
    product_classification_name: Optional[str] = None,
    lower_institution_result_inclusion: Optional[str] = None,
    link_system_code: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """공공조달통계정보서비스 API 호출 (Enhanced parameterized).

    Available operations (14개):
    - getTotlPubPrcrmntSttus: 전체 공공조달 현황
    - getInsttDivAccotPrcrmntSttus: 기관구분별 조달 현황
    - getEntrprsDivAccotPrcrmntSttus: 기업구분별 조달 현황
    - getCntrctMthdAccotSttus: 계약방법별 현황
    - getRgnLmtSttus: 지역제한 현황
    - getRgnDutyCmmnCntrctSttus: 지역의무공동계약 현황
    - getPrcrmntObjectBsnsObjAccotSttus: 조달목적물(업무대상)별 현황
    - getDminsttAccotEntrprsDivAccotArslt: 수요기관별 기업구분별 실적
    - getDminsttAccotCntrctMthdAccotArslt: 수요기관별 계약방법별 실적
    - getDminsttAccotBsnsObjAccotArslt: 수요기관별 업무대상별 실적
    - getDminsttAccotSystmTyAccotArslt: 수요기관별 시스템유형별 실적
    - getPrcrmntEntrprsAccotCntrctMthdAccotArslt: 조달기업별 계약방법별 실적
    - getPrcrmntEntrprsAccotBsnsObjAccotArslt: 조달기업별 업무대상별 실적
    - getPrdctIdntNoServcAccotArslt: 품목 및 서비스별 실적

    Args:
        operation: API 오퍼레이션명
        num_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        search_base_year: 검색기준년도 (YYYY)
        search_base_month_start: 기준년월 시작 (YYYYMM)
        search_base_month_end: 기준년월 종료 (YYYYMM)
        demand_institution_code: 수요기관코드
        demand_institution_name: 수요기관명
        corp_unity_no: 업체통합번호
        corp_name: 업체명
        product_classification_no: 물품분류번호
        product_classification_name: 물품분류명
        lower_institution_result_inclusion: 하위기관실적포함여부
        link_system_code: 연계시스템코드
        fields: 선택할 필드 목록 (예: ["기관명", "조달금액"])
        response_format: 응답 형식 ("full", "compact", "minimal")

    Returns:
        API 응답 데이터 (필드 선택 적용됨)
    """
    kwargs = {}
    if search_base_year: kwargs["srchBssYear"] = search_base_year
    if search_base_month_start: kwargs["srchBssYmBgn"] = search_base_month_start
    if search_base_month_end: kwargs["srchBssYmEnd"] = search_base_month_end
    if demand_institution_code: kwargs["dminsttCd"] = demand_institution_code
    if demand_institution_name: kwargs["dminsttNm"] = demand_institution_name
    if corp_unity_no: kwargs["corpUntyNo"] = corp_unity_no
    if corp_name: kwargs["corpNm"] = corp_name
    if product_classification_no: kwargs["prdctClsfcNo"] = product_classification_no
    if product_classification_name: kwargs["prdctClsfcNm"] = product_classification_name
    if lower_institution_result_inclusion: kwargs["lwrInsttArsltInclsnYn"] = lower_institution_result_inclusion
    if link_system_code: kwargs["linkSystmCd"] = link_system_code

    # API 호출
    result = enhanced_tools.call_procurement_statistics_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="procurement_stats"
    )


@mcp.tool()
def call_product_list_api(
    operation: str,
    num_rows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
    page_no: int = 1,
    upper_product_classification_no: Optional[str] = None,
    product_classification_no: Optional[str] = None,
    product_id_no: Optional[str] = None,
    detail_product_classification_no: Optional[str] = None,
    product_classification_name: Optional[str] = None,
    product_classification_eng_name: Optional[str] = None,
    korean_product_name: Optional[str] = None,
    manufacturer_corp_name: Optional[str] = None,
    region_code: Optional[str] = None,
    inquiry_div: Optional[str] = None,
    inquiry_start_date: Optional[str] = None,
    inquiry_end_date: Optional[str] = None,
    change_period_start_date: Optional[str] = None,
    change_period_end_date: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """조달청 물품목록정보서비스 API 호출 (Enhanced parameterized).

    Available operations (12개):
    - getThngGuidanceMapInfo: 물품안내지도 조회
    - getThngPrdnmLocplcAccotListInfoInfoPrdlstSearch: 품목 목록 조회
    - getThngPrdnmLocplcAccotListInfoInfoPrdnmSearch: 품명 목록 조회
    - getThngPrdnmLocplcAccotListInfoInfoLocplcSearch: 소재지 목록 조회
    - getThngListClChangeHistInfo: 분류변경이력 조회
    - getLsfgdNdPrdlstChghstlnfoSttus: 품목변경이력 조회
    - getPrdctClsfcNoUnit2Info: 물품분류2단위 내역조회
    - getPrdctClsfcNoUnit4Info: 물품분류4단위 내역조회
    - getPrdctClsfcNoUnit6Info: 물품분류6단위 내역조회
    - getPrdctClsfcNoUnit8Info: 물품분류8단위 내역조회
    - getPrdctClsfcNoUnit10Info: 물품분류10단위 내역조회
    - getPrdctClsfcNoChgHstry: 물품분류변경 이력조회

    Args:
        operation: API 오퍼레이션명
        num_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        upper_product_classification_no: 상위 물품분류번호
        product_classification_no: 물품분류번호
        product_id_no: 물품식별번호
        detail_product_classification_no: 세부품명번호
        product_classification_name: 품명
        product_classification_eng_name: 영문품명
        korean_product_name: 한글품목명
        manufacturer_corp_name: 제조업체명
        region_code: 지역코드
        inquiry_div: 조회구분
        inquiry_start_date: 조회시작일시 (YYYYMMDDHHMM)
        inquiry_end_date: 조회종료일시 (YYYYMMDDHHMM)
        change_period_start_date: 변경기간 시작일자 (YYYYMMDD)
        change_period_end_date: 변경기간 종료일자 (YYYYMMDD)
        fields: 선택할 필드 목록 (예: ["품목명", "제조업체명"])
        response_format: 응답 형식 ("full", "compact", "minimal")

    Returns:
        API 응답 데이터 (필드 선택 적용됨)
    """
    kwargs = {}
    if upper_product_classification_no: kwargs["upPrdctClsfcNo"] = upper_product_classification_no
    if product_classification_no: kwargs["prdctClsfcNo"] = product_classification_no
    if product_id_no: kwargs["prdctIdntNo"] = product_id_no
    if detail_product_classification_no: kwargs["dtilPrdctClsfcNo"] = detail_product_classification_no
    if product_classification_name: kwargs["prdctClsfcNoNm"] = product_classification_name
    if product_classification_eng_name: kwargs["prdctClsfcNoEngNm"] = product_classification_eng_name
    if korean_product_name: kwargs["krnPrdctNm"] = korean_product_name
    if manufacturer_corp_name: kwargs["mnfctCorpNm"] = manufacturer_corp_name
    if region_code: kwargs["rgnCd"] = region_code
    if inquiry_div: kwargs["inqryDiv"] = inquiry_div
    if inquiry_start_date: kwargs["inqryBgnDt"] = inquiry_start_date
    if inquiry_end_date: kwargs["inqryEndDt"] = inquiry_end_date
    if change_period_start_date: kwargs["chgPrdBgnDt"] = change_period_start_date
    if change_period_end_date: kwargs["chgPrdEndDt"] = change_period_end_date

    # API 호출
    result = enhanced_tools.call_product_list_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="product_list"
    )


@mcp.tool()
def call_shopping_mall_api(
    operation: str,
    num_rows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
    page_no: int = 1,
    registration_start_date: Optional[str] = None,
    registration_end_date: Optional[str] = None,
    change_start_date: Optional[str] = None,
    change_end_date: Optional[str] = None,
    product_classification_name: Optional[str] = None,
    product_id_no: Optional[str] = None,
    contract_corp_name: Optional[str] = None,
    product_certification: Optional[str] = None,
    inquiry_div: Optional[str] = None,
    inquiry_start_date: Optional[str] = None,
    inquiry_end_date: Optional[str] = None,
    detail_product_classification_name: Optional[str] = None,
    product_id_name: Optional[str] = None,
    excellent_product: Optional[str] = None,
    mas_yn: Optional[str] = None,
    shopping_contract_no: Optional[str] = None,
    registration_cancel: Optional[str] = None,
    demand_institution_name: Optional[str] = None,
    demand_institution_region_name: Optional[str] = None,
    delivery_request_no: Optional[str] = None,
    inquiry_product_div: Optional[str] = None,
    procurement_div: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터 종합쇼핑몰 품목정보 서비스 API 호출 (Enhanced parameterized).

    Available operations (9개):
    - getMASCntrctPrdctInfoList: 다수공급자계약 품목정보 조회
    - getUcntrctPrdctInfoList: 일반단가계약 품목정보 조회
    - getThptyUcntrctPrdctInfoList: 제3자단가계약 품목정보 조회
    - getDlvrReqInfoList: 납품요구정보 현황 목록조회
    - getDlvrReqDtlInfoList: 납품요구상세 현황 목록조회
    - getShoppingMallPrdctInfoList: 종합쇼핑몰 품목 정보 목록 조회
    - getVntrPrdctOrderDealDtlsInfoList: 벤처나라 물품 주문거래 내역 조회
    - getSpcifyPrdlstPrcureInfoList: 특정품목조달내역 목록 조회
    - getSpcifyPrdlstPrcureTotList: 특정품목조달집계 목록 조회

    Args:
        operation: API 오퍼레이션명
        num_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        registration_start_date: 등록시작일시 (YYYYMMDDHH24M)
        registration_end_date: 등록종료일시 (YYYYMMDDHH24M)
        change_start_date: 변경시작일시 (YYYYMMDDHH24M)
        change_end_date: 변경종료일시 (YYYYMMDDHH24M)
        product_classification_name: 품명
        product_id_no: 물품식별번호
        contract_corp_name: 계약업체명
        product_certification: 제품인증여부
        inquiry_div: 조회구분
        inquiry_start_date: 조회시작일자 (YYYYMMDD)
        inquiry_end_date: 조회종료일자 (YYYYMMDD)
        detail_product_classification_name: 세부분류품명
        product_id_name: 품목명(식별명)
        excellent_product: 우수제품여부
        mas_yn: 다수공급경쟁자여부
        shopping_contract_no: 쇼핑계약번호
        registration_cancel: 등록해지상품포함여부
        demand_institution_name: 수요기관명
        demand_institution_region_name: 수요기관관할지역명
        delivery_request_no: 납품요구번호
        inquiry_product_div: 조회상품구분
        procurement_div: 조달방식구분
        fields: 선택할 필드 목록 (예: ["품목명", "계약업체명"])
        response_format: 응답 형식 ("full", "compact", "minimal")

    Returns:
        API 응답 데이터 (필드 선택 적용됨)
    """
    kwargs = {}
    if registration_start_date: kwargs["rgstDtBgnDt"] = registration_start_date
    if registration_end_date: kwargs["rgstDtEndDt"] = registration_end_date
    if change_start_date: kwargs["chgDtBgnDt"] = change_start_date
    if change_end_date: kwargs["chgDtEndDt"] = change_end_date
    if product_classification_name: kwargs["prdctClsfcNoNm"] = product_classification_name
    if product_id_no: kwargs["prdctIdntNo"] = product_id_no
    if contract_corp_name: kwargs["cntrctCorpNm"] = contract_corp_name
    if product_certification: kwargs["prodctCertYn"] = product_certification
    if inquiry_div: kwargs["inqryDiv"] = inquiry_div
    if inquiry_start_date: kwargs["inqryBgnDate"] = inquiry_start_date
    if inquiry_end_date: kwargs["inqryEndDate"] = inquiry_end_date
    if detail_product_classification_name: kwargs["dtilPrdctClsfcNoNm"] = detail_product_classification_name
    if product_id_name: kwargs["prdctIdntNoNm"] = product_id_name
    if excellent_product: kwargs["exclcProdctYn"] = excellent_product
    if mas_yn: kwargs["masYn"] = mas_yn
    if shopping_contract_no: kwargs["shopngCntrctNo"] = shopping_contract_no
    if registration_cancel: kwargs["regtCncelYn"] = registration_cancel
    if demand_institution_name: kwargs["dminsttNm"] = demand_institution_name
    if demand_institution_region_name: kwargs["dminsttRgnNm"] = demand_institution_region_name
    if delivery_request_no: kwargs["dlvrReqNo"] = delivery_request_no
    if inquiry_product_div: kwargs["inqryPrdctDiv"] = inquiry_product_div
    if procurement_div: kwargs["prcrmntDiv"] = procurement_div

    # API 호출
    result = enhanced_tools.call_shopping_mall_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="shopping_mall"
    )


@mcp.tool()
def get_all_api_services_info() -> Dict[str, Any]:
    """모든 API 서비스 정보 조회 (Enhanced).

    Returns:
        전체 서비스 및 오퍼레이션 정보
    """
    return enhanced_tools.get_all_api_services_info()


@mcp.tool()
def get_api_operations(service_type: str) -> Dict[str, Any]:
    """특정 서비스의 사용 가능한 오퍼레이션 목록 조회 (Enhanced).

    Args:
        service_type: 서비스 타입 (public_data_standard, procurement_statistics, product_list, shopping_mall)

    Returns:
        서비스별 오퍼레이션 목록
    """
    return enhanced_tools.get_api_operations(service_type)


@mcp.tool()
def get_response_field_info(service_type: str = "bid_announcement") -> Dict[str, Any]:
    """API 응답 필드 선택 기능 정보 조회.

    Args:
        service_type: 서비스 타입 (bid_announcement, successful_bid, contract_info, procurement_stats, product_list, shopping_mall)

    Returns:
        필드 선택 가능한 정보 및 사용법
    """
    return get_available_fields(service_type)


@mcp.tool()
def get_all_response_format_info() -> Dict[str, Any]:
    """모든 서비스의 응답 형태 정보 조회.

    Returns:
        전체 응답 형태 정보 및 사용 가이드
    """
    return get_all_response_formats()


@mcp.tool()
def get_api_key_status() -> Dict[str, Any]:
    """API 키 설정 상태 및 구성 정보 조회.

    Returns:
        키 설정 상태와 사용 방법 안내
    """
    status = get_key_status()

    return {
        "key_configuration": status,
        "usage_priority": [
            "1순위: 사용자 제공 키 (환경변수 NARAMARKET_SERVICE_KEY)",
            "2순위: Smithery.ai 설정 키",
            "3순위: 내장 운영 키 (자동 사용)"
        ],
        "setup_guide": {
            "no_key_needed": "내장 운영 키가 설정되어 있어 별도 키 설정 없이 사용 가능" if status.get("builtin_key_configured") else "API 키 설정이 필요합니다",
            "user_key_setup": "고객 전용 키 사용시: NARAMARKET_SERVICE_KEY 환경변수 설정",
            "builtin_key_info": "내장 키는 하루 10만건 제한, 무료 사용 가능"
        }
    }


@mcp.tool()
def call_api_with_pagination_support(
    service_type: str,
    operation: str,
    num_rows: int = 10,  # 리모트 서버에서는 적당한 크기 유지
    page_no: int = 1,
    # Common parameters for all services
    bid_notice_start_date: Optional[str] = None,
    bid_notice_end_date: Optional[str] = None,
    search_base_year: Optional[str] = None,
    upper_product_classification_no: Optional[str] = None,
    registration_start_date: Optional[str] = None,
    registration_end_date: Optional[str] = None,
    # Additional optional parameters
    bid_announcement_notice_type: Optional[str] = None,
    business_type: Optional[str] = None,
    company_name: Optional[str] = None,
    product_name: Optional[str] = None
) -> Dict[str, Any]:
    """페이징 지원 API 호출 (리모트 서버 환경 최적화).

    이 도구는 리모트 서버 환경에서 많은 데이터를 효율적으로 탐색할 때 사용하세요.
    컨텍스트 보호와 함께 다음 페이지 요청 방법을 자동으로 제공합니다.

    Args:
        service_type: 서비스 타입 (public_data_standard, procurement_statistics, product_list, shopping_mall)
        operation: API 오퍼레이션명
        num_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_notice_start_date: 입찰공고 시작일 (YYYYMMDDHHMM)
        bid_notice_end_date: 입찰공고 종료일 (YYYYMMDDHHMM)
        search_base_year: 검색 기준년도 (YYYY)
        upper_product_classification_no: 상위물품분류번호
        registration_start_date: 등록 시작일 (YYYYMMDDHHMM)
        registration_end_date: 등록 종료일 (YYYYMMDDHHMM)
        bid_announcement_notice_type: 입찰공고유형
        business_type: 업종
        company_name: 업체명
        product_name: 상품명

    Returns:
        컨텍스트 보호된 API 응답 데이터 + 페이징 안내
    """
    # Build params dict from non-None values
    params = {
        "numOfRows": num_rows,
        "pageNo": page_no,
    }

    # Add optional parameters if provided
    optional_params = {
        "bidNoticeStartDate": bid_notice_start_date,
        "bidNoticeEndDate": bid_notice_end_date,
        "searchBaseYear": search_base_year,
        "upperProductClassificationNo": upper_product_classification_no,
        "registrationStartDate": registration_start_date,
        "registrationEndDate": registration_end_date,
        "bidAnnouncementNoticeType": bid_announcement_notice_type,
        "businessType": business_type,
        "companyName": company_name,
        "productName": product_name
    }

    for key, value in optional_params.items():
        if value is not None:
            params[key] = value

    return enhanced_tools.call_api_with_pagination_guidance(
        service_type=service_type,
        operation=operation,
        params=params
    )


@mcp.tool()
def get_data_exploration_guide(
    service_type: str,
    operation: str,
    expected_data_size: str = "medium"
) -> Dict[str, Any]:
    """데이터 탐색을 위한 최적화된 매개변수 가이드 제공.

    리모트 서버 환경에서 효율적인 데이터 탐색을 위한 권장 설정을 제공합니다.

    Args:
        service_type: 서비스 타입
        operation: API 오퍼레이션명
        expected_data_size: 예상 데이터 크기 ("small", "medium", "large")

    Returns:
        최적화된 탐색 가이드
    """
    size_configs = {
        "small": {"num_rows": 10, "strategy": "단일 요청으로 충분"},
        "medium": {"num_rows": 5, "strategy": "2-3회 페이징 권장"},
        "large": {"num_rows": 3, "strategy": "다중 페이징으로 점진적 탐색"}
    }

    config = size_configs.get(expected_data_size, size_configs["medium"])

    return {
        "service_type": service_type,
        "operation": operation,
        "recommended_config": config,
        "sample_first_request": {
            "num_rows": config["num_rows"],
            "page_no": 1
        },
        "exploration_tips": [
            "첫 번째 요청으로 데이터 구조 파악",
            "pagination 정보로 전체 규모 확인",
            "필요한 경우 검색 조건 추가로 범위 축소",
            "컨텍스트 윈도우 보호를 위해 작은 페이지 크기 유지"
        ],
        "context_protection": {
            "auto_applied": True,
            "max_items_shown": 5,
            "key_fields_only": True
        }
    }


# AI-Friendly Simplified Tools (자주 사용되는 기능들)

# ===================
# 입찰공고서비스 API
# ===================

@mcp.tool()
def get_bid_announcement_construction(
    inqry_div: str = "1",
    days_back: int = 7,
    num_of_rows: int = 10,
    page_no: int = 1,
    bid_ntce_nm: Optional[str] = None,
    ntce_instt_nm: Optional[str] = None,
    dminst_nm: Optional[str] = None,
    prtcpt_lmt_rgn_cd: Optional[str] = None,
    indstryty_nm: Optional[str] = None,
    presmpt_prce_bgn: Optional[int] = None,
    presmpt_prce_end: Optional[int] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 입찰공고공사조회 (AI 친화적 도구).

    공사부문의 입찰공고정보를 조회합니다. 자동으로 날짜 범위를 계산합니다.

    Args:
        inqry_div: 조회구분 (1:공고게시일시, 2:개찰일시)
        days_back: 며칠 전까지 조회할지 (기본값: 7일)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_ntce_nm: 입찰공고명 (부분검색 가능)
        ntce_instt_nm: 공고기관명 (부분검색 가능)
        dminst_nm: 수요기관명 (부분검색 가능)
        prtcpt_lmt_rgn_cd: 참가제한지역코드 (11:서울, 41:경기도 등)
        indstryty_nm: 업종명 (부분검색 가능)
        presmpt_prce_bgn: 추정가격 시작금액 (원)
        presmpt_prce_end: 추정가격 종료금액 (원)
        fields: 선택할 특정 필드 리스트 (예: ["bidNtceNo", "bidNtceNm", "presmptPrce"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        입찰공고 공사 목록 (필터링된 필드)
    """
    # 자동으로 날짜 범위 계산
    inqry_bgn_dt, inqry_end_dt = naramarket_search_apis.format_date_range(days_back)

    # API 호출
    result = naramarket_search_apis.get_bid_announcement_construction(
        inqry_div=inqry_div,
        inqry_bgn_dt=inqry_bgn_dt,
        inqry_end_dt=inqry_end_dt,
        num_of_rows=num_of_rows,
        page_no=page_no,
        bid_ntce_nm=bid_ntce_nm,
        ntce_instt_nm=ntce_instt_nm,
        dminst_nm=dminst_nm,
        prtcpt_lmt_rgn_cd=prtcpt_lmt_rgn_cd,
        indstryty_nm=indstryty_nm,
        presmpt_prce_bgn=presmpt_prce_bgn,
        presmpt_prce_end=presmpt_prce_end
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="bid_announcement"
    )


@mcp.tool()
def get_bid_announcement_service(
    inqry_div: str = "1",
    days_back: int = 7,
    num_of_rows: int = 10,
    page_no: int = 1,
    bid_ntce_nm: Optional[str] = None,
    ntce_instt_nm: Optional[str] = None,
    dminst_nm: Optional[str] = None,
    prtcpt_lmt_rgn_cd: Optional[str] = None,
    indstryty_nm: Optional[str] = None,
    presmpt_prce_bgn: Optional[int] = None,
    presmpt_prce_end: Optional[int] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 입찰공고용역조회 (AI 친화적 도구).

    용역부문의 입찰공고정보를 조회합니다. 자동으로 날짜 범위를 계산합니다.

    Args:
        inqry_div: 조회구분 (1:공고게시일시, 2:개찰일시)
        days_back: 며칠 전까지 조회할지 (기본값: 7일)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_ntce_nm: 입찰공고명 (부분검색 가능)
        ntce_instt_nm: 공고기관명 (부분검색 가능)
        dminst_nm: 수요기관명 (부분검색 가능)
        prtcpt_lmt_rgn_cd: 참가제한지역코드 (11:서울, 41:경기도 등)
        indstryty_nm: 업종명 (부분검색 가능)
        presmpt_prce_bgn: 추정가격 시작금액 (원)
        presmpt_prce_end: 추정가격 종료금액 (원)
        fields: 선택할 특정 필드 리스트 (예: ["bidNtceNo", "bidNtceNm", "presmptPrce"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        입찰공고 용역 목록 (필터링된 필드)
    """
    # 자동으로 날짜 범위 계산
    inqry_bgn_dt, inqry_end_dt = naramarket_search_apis.format_date_range(days_back)

    # API 호출
    result = naramarket_search_apis.get_bid_announcement_service(
        inqry_div=inqry_div,
        inqry_bgn_dt=inqry_bgn_dt,
        inqry_end_dt=inqry_end_dt,
        num_of_rows=num_of_rows,
        page_no=page_no,
        bid_ntce_nm=bid_ntce_nm,
        ntce_instt_nm=ntce_instt_nm,
        dminst_nm=dminst_nm,
        prtcpt_lmt_rgn_cd=prtcpt_lmt_rgn_cd,
        indstryty_nm=indstryty_nm,
        presmpt_prce_bgn=presmpt_prce_bgn,
        presmpt_prce_end=presmpt_prce_end
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="bid_announcement"
    )


@mcp.tool()
def get_bid_announcement_goods(
    inqry_div: str = "1",
    days_back: int = 7,
    num_of_rows: int = 10,
    page_no: int = 1,
    bid_ntce_nm: Optional[str] = None,
    ntce_instt_nm: Optional[str] = None,
    dminst_nm: Optional[str] = None,
    prtcpt_lmt_rgn_cd: Optional[str] = None,
    mas_yn: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 입찰공고물품조회 (AI 친화적 도구).

    물품부문의 입찰공고정보를 조회합니다. 자동으로 날짜 범위를 계산합니다.

    Args:
        inqry_div: 조회구분 (1:공고게시일시, 2:개찰일시)
        days_back: 며칠 전까지 조회할지 (기본값: 7일)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_ntce_nm: 입찰공고명 (부분검색 가능)
        ntce_instt_nm: 공고기관명 (부분검색 가능)
        dminst_nm: 수요기관명 (부분검색 가능)
        prtcpt_lmt_rgn_cd: 참가제한지역코드 (11:서울, 41:경기도 등)
        mas_yn: 다수공급경쟁자여부 (Y/N)
        fields: 선택할 특정 필드 리스트 (예: ["bidNtceNo", "bidNtceNm", "presmptPrce"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        입찰공고 물품 목록 (필터링된 필드)
    """
    # 자동으로 날짜 범위 계산
    inqry_bgn_dt, inqry_end_dt = naramarket_search_apis.format_date_range(days_back)

    # API 호출
    result = naramarket_search_apis.get_bid_announcement_goods(
        inqry_div=inqry_div,
        inqry_bgn_dt=inqry_bgn_dt,
        inqry_end_dt=inqry_end_dt,
        num_of_rows=num_of_rows,
        page_no=page_no,
        bid_ntce_nm=bid_ntce_nm,
        ntce_instt_nm=ntce_instt_nm,
        dminst_nm=dminst_nm,
        prtcpt_lmt_rgn_cd=prtcpt_lmt_rgn_cd,
        mas_yn=mas_yn
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="bid_announcement"
    )


# ===================
# 낙찰정보서비스 API
# ===================

@mcp.tool()
def get_successful_bid_list_goods(
    inqry_div: str,
    days_back: int = 30,
    bid_ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    bid_ntce_nm: Optional[str] = None,
    ntce_instt_nm: Optional[str] = None,
    dminst_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터 검색조건에 의한 낙찰된 목록 현황 물품조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:공고게시일시, 2:개찰일시, 3:입찰공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div가 1,2일 때만 사용, 기본값: 30일)
        bid_ntce_no: 입찰공고번호 (inqry_div=3일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_ntce_nm: 입찰공고명 (부분검색 가능)
        ntce_instt_nm: 공고기관명 (부분검색 가능)
        dminst_nm: 수요기관명 (부분검색 가능)
        fields: 선택할 특정 필드 리스트 (예: ["bidNtceNo", "bidNtceNm", "scsbidPrce"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        낙찰정보 물품 목록 (필터링된 필드)
    """
    inqry_bgn_dt = None
    inqry_end_dt = None

    # 날짜 기반 조회인 경우에만 날짜 범위 계산
    if inqry_div in ["1", "2"]:
        inqry_bgn_dt, inqry_end_dt = naramarket_search_apis.format_date_range(days_back)

    # API 호출
    result = naramarket_search_apis.get_successful_bid_list_goods(
        inqry_div=inqry_div,
        inqry_bgn_dt=inqry_bgn_dt,
        inqry_end_dt=inqry_end_dt,
        bid_ntce_no=bid_ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        bid_ntce_nm=bid_ntce_nm,
        ntce_instt_nm=ntce_instt_nm,
        dminst_nm=dminst_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="successful_bid"
    )


@mcp.tool()
def get_successful_bid_list_construction(
    inqry_div: str,
    days_back: int = 30,
    bid_ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    bid_ntce_nm: Optional[str] = None,
    ntce_instt_nm: Optional[str] = None,
    dminst_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터 검색조건에 의한 낙찰된 목록 현황 공사조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:공고게시일시, 2:개찰일시, 3:입찰공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div가 1,2일 때만 사용, 기본값: 30일)
        bid_ntce_no: 입찰공고번호 (inqry_div=3일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_ntce_nm: 입찰공고명 (부분검색 가능)
        ntce_instt_nm: 공고기관명 (부분검색 가능)
        dminst_nm: 수요기관명 (부분검색 가능)
        fields: 선택할 특정 필드 리스트 (예: ["bidNtceNo", "bidNtceNm", "scsbidPrce"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        낙찰정보 공사 목록 (필터링된 필드)
    """
    inqry_bgn_dt = None
    inqry_end_dt = None

    # 날짜 기반 조회인 경우에만 날짜 범위 계산
    if inqry_div in ["1", "2"]:
        inqry_bgn_dt, inqry_end_dt = naramarket_search_apis.format_date_range(days_back)

    # API 호출
    result = naramarket_search_apis.get_successful_bid_list_construction(
        inqry_div=inqry_div,
        inqry_bgn_dt=inqry_bgn_dt,
        inqry_end_dt=inqry_end_dt,
        bid_ntce_no=bid_ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        bid_ntce_nm=bid_ntce_nm,
        ntce_instt_nm=ntce_instt_nm,
        dminst_nm=dminst_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="successful_bid"
    )


@mcp.tool()
def get_successful_bid_list_service(
    inqry_div: str,
    days_back: int = 30,
    bid_ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    bid_ntce_nm: Optional[str] = None,
    ntce_instt_nm: Optional[str] = None,
    dminst_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터 검색조건에 의한 낙찰된 목록 현황 용역조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:공고게시일시, 2:개찰일시, 3:입찰공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div가 1,2일 때만 사용, 기본값: 30일)
        bid_ntce_no: 입찰공고번호 (inqry_div=3일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_ntce_nm: 입찰공고명 (부분검색 가능)
        ntce_instt_nm: 공고기관명 (부분검색 가능)
        dminst_nm: 수요기관명 (부분검색 가능)
        fields: 선택할 특정 필드 리스트 (예: ["bidNtceNo", "bidNtceNm", "scsbidPrce"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        낙찰정보 용역 목록 (필터링된 필드)
    """
    inqry_bgn_dt = None
    inqry_end_dt = None

    # 날짜 기반 조회인 경우에만 날짜 범위 계산
    if inqry_div in ["1", "2"]:
        inqry_bgn_dt, inqry_end_dt = naramarket_search_apis.format_date_range(days_back)

    # API 호출
    result = naramarket_search_apis.get_successful_bid_list_service(
        inqry_div=inqry_div,
        inqry_bgn_dt=inqry_bgn_dt,
        inqry_end_dt=inqry_end_dt,
        bid_ntce_no=bid_ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        bid_ntce_nm=bid_ntce_nm,
        ntce_instt_nm=ntce_instt_nm,
        dminst_nm=dminst_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="successful_bid"
    )


# ===================
# 계약정보서비스 API
# ===================

@mcp.tool()
def get_contract_info_goods(
    inqry_div: str,
    days_back: int = 30,
    dcsn_cntrct_no: Optional[str] = None,
    req_no: Optional[str] = None,
    ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    instt_nm: Optional[str] = None,
    prdct_clsfc_no_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 계약현황 물품조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:계약체결일자, 2:확정계약번호, 3:요청번호, 4:공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div=1일 때만 사용, 기본값: 30일)
        dcsn_cntrct_no: 확정계약번호 (inqry_div=2일 때 필수)
        req_no: 요청번호 (inqry_div=3일 때 필수)
        ntce_no: 공고번호 (inqry_div=4일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        instt_nm: 기관명
        prdct_clsfc_no_nm: 품명
        fields: 선택할 특정 필드 리스트 (예: ["cntrctNo", "cntrctAmt", "prdctNm"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        계약정보 물품 목록 (필터링된 필드)
    """
    inqry_bgn_date = None
    inqry_end_date = None

    # 계약체결일자 기반 조회인 경우에만 날짜 범위 계산 (YYYYMMDD 형식)
    if inqry_div == "1":
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        inqry_bgn_date = start_date.strftime("%Y%m%d")
        inqry_end_date = end_date.strftime("%Y%m%d")

    # API 호출
    result = naramarket_search_apis.get_contract_info_goods(
        inqry_div=inqry_div,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date,
        dcsn_cntrct_no=dcsn_cntrct_no,
        req_no=req_no,
        ntce_no=ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        instt_nm=instt_nm,
        prdct_clsfc_no_nm=prdct_clsfc_no_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="contract_info"
    )


@mcp.tool()
def get_contract_info_construction(
    inqry_div: str,
    days_back: int = 30,
    dcsn_cntrct_no: Optional[str] = None,
    req_no: Optional[str] = None,
    ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    cnstty_nm: Optional[str] = None,
    cnstwk_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 계약현황 공사조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:계약체결일자, 2:확정계약번호, 3:요청번호, 4:공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div=1일 때만 사용, 기본값: 30일)
        dcsn_cntrct_no: 확정계약번호 (inqry_div=2일 때 필수)
        req_no: 요청번호 (inqry_div=3일 때 필수)
        ntce_no: 공고번호 (inqry_div=4일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        cnstty_nm: 공종명
        cnstwk_nm: 공사명
        fields: 선택할 특정 필드 리스트 (예: ["cntrctNo", "cntrctAmt", "cnstwkNm"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        계약정보 공사 목록 (필터링된 필드)
    """
    inqry_bgn_date = None
    inqry_end_date = None

    # 계약체결일자 기반 조회인 경우에만 날짜 범위 계산 (YYYYMMDD 형식)
    if inqry_div == "1":
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        inqry_bgn_date = start_date.strftime("%Y%m%d")
        inqry_end_date = end_date.strftime("%Y%m%d")

    # API 호출
    result = naramarket_search_apis.get_contract_info_construction(
        inqry_div=inqry_div,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date,
        dcsn_cntrct_no=dcsn_cntrct_no,
        req_no=req_no,
        ntce_no=ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        cnstty_nm=cnstty_nm,
        cnstwk_nm=cnstwk_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="contract_info"
    )


@mcp.tool()
def get_contract_info_service(
    inqry_div: str,
    days_back: int = 30,
    dcsn_cntrct_no: Optional[str] = None,
    req_no: Optional[str] = None,
    ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    cnstty_nm: Optional[str] = None,
    cntrct_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 계약현황 용역조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:계약체결일자, 2:확정계약번호, 3:요청번호, 4:공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div=1일 때만 사용, 기본값: 30일)
        dcsn_cntrct_no: 확정계약번호 (inqry_div=2일 때 필수)
        req_no: 요청번호 (inqry_div=3일 때 필수)
        ntce_no: 공고번호 (inqry_div=4일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        cnstty_nm: 공종명
        cntrct_nm: 계약명(용역명)
        fields: 선택할 특정 필드 리스트 (예: ["cntrctNo", "cntrctAmt", "cntrctNm"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        계약정보 용역 목록 (필터링된 필드)
    """
    inqry_bgn_date = None
    inqry_end_date = None

    # 계약체결일자 기반 조회인 경우에만 날짜 범위 계산 (YYYYMMDD 형식)
    if inqry_div == "1":
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        inqry_bgn_date = start_date.strftime("%Y%m%d")
        inqry_end_date = end_date.strftime("%Y%m%d")

    # API 호출
    result = naramarket_search_apis.get_contract_info_service(
        inqry_div=inqry_div,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date,
        dcsn_cntrct_no=dcsn_cntrct_no,
        req_no=req_no,
        ntce_no=ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        cnstty_nm=cnstty_nm,
        cntrct_nm=cntrct_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="contract_info"
    )


@mcp.tool()
def get_contract_info_foreign(
    inqry_div: str,
    days_back: int = 30,
    dcsn_cntrct_no: Optional[str] = None,
    req_no: Optional[str] = None,
    ntce_no: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    prdct_clsfc_no_nm: Optional[str] = None,
    sply_corp_nm: Optional[str] = None,
    make_corp_nm: Optional[str] = None,
    fields: Optional[List[str]] = None,
    response_format: str = "full"
) -> Dict[str, Any]:
    """나라장터검색조건에 의한 계약현황 외자조회 (AI 친화적 도구).

    Args:
        inqry_div: 조회구분 (1:계약체결일자, 2:확정계약번호, 3:요청번호, 4:공고번호)
        days_back: 며칠 전까지 조회할지 (inqry_div=1일 때만 사용, 기본값: 30일)
        dcsn_cntrct_no: 확정계약번호 (inqry_div=2일 때 필수)
        req_no: 요청번호 (inqry_div=3일 때 필수)
        ntce_no: 공고번호 (inqry_div=4일 때 필수)
        num_of_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        prdct_clsfc_no_nm: 품명(영문물품명)
        sply_corp_nm: 공급업체명
        make_corp_nm: 제작업체명
        fields: 선택할 특정 필드 리스트 (예: ["cntrctNo", "cntrctAmt", "prdctClsfcNoNm"])
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")

    Returns:
        계약정보 외자 목록 (필터링된 필드)
    """
    inqry_bgn_date = None
    inqry_end_date = None

    # 계약체결일자 기반 조회인 경우에만 날짜 범위 계산 (YYYYMMDD 형식)
    if inqry_div == "1":
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        inqry_bgn_date = start_date.strftime("%Y%m%d")
        inqry_end_date = end_date.strftime("%Y%m%d")

    # API 호출
    result = naramarket_search_apis.get_contract_info_foreign(
        inqry_div=inqry_div,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date,
        dcsn_cntrct_no=dcsn_cntrct_no,
        req_no=req_no,
        ntce_no=ntce_no,
        num_of_rows=num_of_rows,
        page_no=page_no,
        prdct_clsfc_no_nm=prdct_clsfc_no_nm,
        sply_corp_nm=sply_corp_nm,
        make_corp_nm=make_corp_nm
    )

    # 응답 필터링 적용
    return filter_response_fields(
        response_data=result,
        fields=fields,
        response_format=response_format,
        service_type="contract_info"
    )


# ===================
# 유틸리티 도구
# ===================

@mcp.tool()
def get_region_codes() -> Dict[str, str]:
    """나라장터 참가제한지역코드 목록 조회.

    Returns:
        지역코드와 지역명의 매핑 딕셔너리
    """
    return naramarket_search_apis.get_region_codes()


@mcp.prompt()
def workflow_guide() -> str:
    """정부조달 데이터 분석을 위한 단계별 워크플로우 가이드"""
    return """
# 정부조달 데이터 분석 워크플로우 가이드

## 1. 기본 데이터 탐색 단계

### 1-1. 입찰공고 현황 파악
- **목적**: 최신 입찰 동향 파악
- **도구**:
  - `get_bid_announcement_construction()` - 공사 입찰
  - `get_bid_announcement_service()` - 용역 입찰
  - `get_bid_announcement_goods()` - 물품 입찰
- **권장설정**: days_back=7-30, 기관명/지역 필터 활용
- **활용**: 시장 트렌드, 입찰 빈도 분석

### 1-2. 낙찰결과 분석
- **목적**: 성공한 입찰의 패턴 분석
- **도구**:
  - `get_successful_bid_list_goods()` - 물품 낙찰정보
  - `get_successful_bid_list_construction()` - 공사 낙찰정보
  - `get_successful_bid_list_service()` - 용역 낙찰정보
- **권장설정**: inqry_div="1", days_back=30
- **활용**: 가격 범위, 선정 기준 분석

## 2. 심화 분석 단계

### 2-1. 계약정보 분석
- **목적**: 실제 체결된 계약 현황 파악
- **도구**:
  - `get_contract_info_goods()` - 물품 계약정보
  - `get_contract_info_construction()` - 공사 계약정보
  - `get_contract_info_service()` - 용역 계약정보
  - `get_contract_info_foreign()` - 외자 계약정보
- **권장설정**: inqry_div="1", days_back=30-90
- **활용**: 계약 규모, 기관별 조달 패턴

### 2-2. 통계 기반 시장 분석
- **목적**: 연도별/기관별 조달 규모 파악
- **도구**: `call_procurement_statistics_api()`
- **권장설정**: 최근 2-3년 데이터 비교
- **활용**: 시장 규모 변화, 성장률 분석

## 3. 검색 전략 및 팁

### 3-1. 조회구분 활용법
- **1: 공고게시일시/계약체결일자** - 기간별 트렌드 분석
- **2: 개찰일시/확정계약번호** - 특정 일정/계약 추적
- **3: 입찰공고번호/요청번호** - 개별 건 상세 조회
- **4: 공고번호** - 공고 기반 연계 분석

### 3-2. 날짜 범위 최적화
- **최신 동향**: 7-14일 (입찰공고)
- **트렌드 분석**: 30-90일 (낙찰/계약)
- **시장 분석**: 365일 (통계 API)

### 3-3. 필드 선택 및 응답 최적화 (신규 기능)
#### 응답 형태 선택
- **response_format="full"**: 전체 응답 (기본값)
- **response_format="summary"**: 주요 정보만 (입찰번호, 제목, 금액 등)
- **response_format="minimal"**: 최소 정보 (식별자만)
- **response_format="key_fields"**: 분석용 핵심 필드

#### 맞춤형 필드 선택
```python
# 특정 필드만 선택
fields=["bidNtceNo", "bidNtceNm", "presmptPrce"]

# 입찰공고 핵심 필드 예시
fields=["bidNtceNo", "bidNtceNm", "ntceInsttNm", "presmptPrce", "bidClseDt"]

# 낙찰정보 핵심 필드 예시
fields=["bidNtceNo", "sucsfbidCorpNm", "cntrctCnclsAmt", "sucsfbidMthd"]
```

#### 사용 시나리오별 권장 설정
- **빠른 개요 파악**: response_format="summary"
- **대용량 데이터 분석**: response_format="key_fields" + 작은 페이지 크기
- **특정 필드 분석**: fields 파라미터로 필요 필드만 선택
- **AI 처리 최적화**: response_format="minimal"로 컨텍스트 절약

## 4. 결과 해석 및 활용

### 4-1. 컨텍스트 보호 이해
- 기본 5개 결과로 제한됨 (컨텍스트 보호)
- 더 많은 데이터 필요시 페이징 가이드 활용
- 핵심 필드 위주로 정보 제공됨

### 4-2. 후속 분석 방향
- 특정 패턴 발견시 관련 카테고리 추가 탐색
- 이상 데이터 발견시 다른 기간/조건으로 재검색
- 통계 데이터와 실제 입찰 데이터 교차 검증

## 5. 일반적인 분석 시나리오

### 시나리오 A: 신규 시장 진입 검토
1. 관련 업무구분의 최근 입찰공고 조회
2. 해당 분야 낙찰 현황 및 가격대 파악
3. 연도별 시장 규모 변화 분석
4. 경쟁사 참여 패턴 분석

### 시나리오 B: 기존 제품 시장 모니터링
1. 해당 품목 코드로 MAS 상품 현황 조회
2. 가격 변동 및 계약 조건 추적
3. 신규 참여 업체 및 변화 감지
4. 계절성 또는 주기적 패턴 파악

### 시나리오 C: 전략적 시장 분석
1. 여러 업무구분별 전체 시장 현황 파악
2. 기관별/지역별 조달 특성 분석
3. 정책 변화가 시장에 미친 영향 추적
4. 미래 시장 기회 및 위험 요소 식별

## 6. 필드 선택 기능 사용 예제

### 예제 1: 입찰공고 요약 정보만 조회
```python
get_bid_announcement_construction(
    days_back=7,
    response_format="summary",
    ntce_instt_nm="서울시"
)
# 결과: 입찰번호, 제목, 기관명, 금액, 마감일만 포함
```

### 예제 2: 특정 필드만 선택하여 조회
```python
get_successful_bid_list_goods(
    days_back=30,
    fields=["bidNtceNo", "sucsfbidCorpNm", "cntrctCnclsAmt"],
    num_of_rows=20
)
# 결과: 입찰번호, 낙찰업체명, 계약금액만 포함
```

### 예제 3: AI 분석을 위한 최적화된 조회
```python
get_contract_info_construction(
    days_back=90,
    response_format="key_fields",
    num_of_rows=5
)
# 결과: 분석에 핵심적인 필드들만 포함하여 컨텍스트 절약
```

### 예제 4: 필드 정보 확인
```python
get_response_field_info("bid_announcement")
# 결과: 입찰공고 서비스에서 사용 가능한 필드 목록과 응답 형태 정보

get_all_response_format_info()
# 결과: 모든 서비스의 응답 형태 정보
```
"""

@mcp.tool()
def get_procurement_statistics_by_year(
    year: str,
    num_rows: int = 10
) -> Dict[str, Any]:
    """연도별 공공조달 통계 조회 (AI 친화적 단순 도구).

    Args:
        year: 조회할 연도 (예: "2024")
        num_rows: 조회할 결과 수 (기본값: 10)

    Returns:
        연도별 공공조달 통계
    """
    return enhanced_tools.call_procurement_statistics_api(
        operation="getTotlPubPrcrmntSttus",
        numOfRows=num_rows,
        pageNo=1,
        srchBssYear=year
    )


@mcp.prompt()
def parameter_selection_guide() -> str:
    """API 파라미터 선택 및 최적화 가이드"""
    return """
# API 파라미터 선택 및 최적화 가이드

## 1. 필수 vs 선택 파라미터 구분

### 필수 파라미터 (Required)
- **numOfRows**: 결과 수 제한 (기본값: 5-10 권장)
- **pageNo**: 페이지 번호 (기본값: 1)
- **operation**: API 작업 유형 (각 서비스별 필수)

### 중요한 선택 파라미터 (Important Optional)
#### 날짜 관련
- **조회 시작일/종료일**: 데이터 범위 제한에 핵심
- **공고일/개찰일**: 입찰 일정 기준 설정
- **기준연도**: 통계 데이터 조회시 필수적

#### 분류 관련
- **업무구분코드**: "1"(물품), "2"(외자), "3"(공사), "5"(용역)
- **기관코드**: 특정 기관 데이터만 조회
- **분류코드**: 상품/서비스 카테고리 지정

## 2. 파라미터 값 선택 전략

### 2-1. 날짜 범위 설정
```
최신 동향 파악: 7-30일 이내
트렌드 분석: 3-6개월 범위
연간 비교: 전체 연도 단위
```

### 2-2. 결과 수 최적화
```
초기 탐색: 5-10개 (컨텍스트 보호)
상세 분석: 10-20개 (필요시)
전체 조회: 50-100개 (페이징 활용)
```

### 2-3. 업무구분 선택 기준
```
물품(1): 일반 용품, 장비, 소모품
외자(2): 해외 조달, 수입품
공사(3): 건설, 시설 공사
용역(5): 서비스, 컨설팅, 유지보수
```

## 3. 서비스별 최적 파라미터 조합

### 3-1. 공공데이터개방표준 (Public Data)
#### 입찰공고 조회시
- **필수**: operation, numOfRows, pageNo
- **권장**: bsnsDivCd(업무구분), bidNtceOdr(공고차수)
- **날짜**: opengBgnDt, opengEndDt (공고기간)

#### 낙찰정보 조회시
- **필수**: operation, numOfRows, pageNo
- **권장**: bsnsDivCd(업무구분), dminsttCd(기관코드)
- **날짜**: opengBgnDt, opengEndDt (개찰기간)

### 3-2. 공공조달통계정보 (Procurement Stats)
#### 기본 통계 조회시
- **필수**: operation, numOfRows, srchBssYear(기준연도)
- **선택**: dminsttCd(기관코드), bsnsDivCd(업무구분)

### 3-3. 물품목록정보 (Product List)
#### 상품 조회시
- **필수**: operation, numOfRows
- **권장**: prdctClsfcLclasCode(대분류), prdctClsfcMlsfcCode(중분류)
- **검색**: prdctNm(상품명), entrpsNm(업체명)

### 3-4. 종합쇼핑몰품목정보 (Shopping Mall)
#### 제품 검색시
- **필수**: operation, numOfRows
- **검색**: prdctClsfcNoNm(제품명), cntrctCnclsCompanyNm(업체명)
- **필터**: dtlPrdctClsfcNo(상세분류번호)

## 4. 파라미터 값 형식 가이드

### 4-1. 날짜 형식
```
YYYYMMDD0000: 시작일 (0시)
YYYYMMDD2359: 종료일 (23시 59분)
YYYY: 연도 (통계 조회시)
YYYYMM: 년월 (월별 조회시)
```

### 4-2. 코드 형식
```
업무구분: "1", "2", "3", "5" (문자열)
기관코드: 6자리 숫자 문자열
분류코드: 계층적 숫자 코드 (2-8자리)
```

### 4-3. 검색어 형식
```
한글: UTF-8 인코딩, 부분 매칭 지원
영문: 대소문자 구분 없음
숫자: 문자열로 전달
특수문자: URL 인코딩 필요
```

## 5. 성능 최적화 팁

### 5-1. 요청 최적화
- 필요한 필드만 조회 (컨텍스트 보호 자동 적용)
- 적절한 페이지 크기 설정 (5-20개)
- 날짜 범위 제한으로 결과 축소

### 5-2. 에러 방지
- 필수 파라미터 누락 확인
- 날짜 형식 정확성 검증
- 코드 값 유효성 사전 확인
- 특수문자 인코딩 처리

### 5-3. 결과 해석
- 빈 결과시 조건 완화 시도
- 너무 많은 결과시 필터 강화
- 오류 응답시 파라미터 재검토

## 6. 일반적인 파라미터 실수와 해결책

### 실수 1: 날짜 범위 과도하게 넓게 설정
**해결**: 최근 30-90일로 제한하여 시작

### 실수 2: 필수 파라미터 누락
**해결**: operation별 필수 파라미터 체크리스트 확인

### 실수 3: 결과 수 과다 요청
**해결**: 초기엔 5-10개로 시작, 필요시 점진적 증가

### 실수 4: 잘못된 코드 값 사용
**해결**: 코드 매핑 테이블 참조 또는 유효 값 조회 먼저 실행
"""

@mcp.tool()
def search_shopping_mall_products(
    product_name: Optional[str] = None,
    company_name: Optional[str] = None,
    num_rows: int = 5
) -> Dict[str, Any]:
    """나라장터 쇼핑몰 제품 검색 (AI 친화적 단순 도구).

    Args:
        product_name: 검색할 제품명 (선택사항)
        company_name: 검색할 업체명 (선택사항)
        num_rows: 조회할 결과 수 (기본값: 5)

    Returns:
        쇼핑몰 제품 검색 결과
    """
    kwargs = {}
    if product_name:
        kwargs["prdctClsfcNoNm"] = product_name
    if company_name:
        kwargs["cntrctCorpNm"] = company_name

    return enhanced_tools.call_shopping_mall_api(
        operation="getMASCntrctPrdctInfoList",
        numOfRows=num_rows,
        pageNo=1,
        **kwargs
    )


# MCP Resources - API 사용 가이드
@mcp.resource("guide://api-parameter-requirements")
def api_parameter_requirements() -> str:
    """정부조달 API 파라미터 요구사항 가이드.

    각 API별 필수/선택/권장 파라미터와 상황별 사용법을 제공합니다.
    """
    return """
# 정부조달 API 파라미터 가이드

## 공공데이터개방표준서비스 (call_public_data_standard_api)

### 입찰공고정보 조회 (getDataSetOpnStdBidPblancInfo)
- **필수**: operation="getDataSetOpnStdBidPblancInfo"
- **강력 권장**: bid_notice_start_date, bid_notice_end_date (날짜 범위)
- **선택**: num_rows, page_no, 기관 관련 파라미터

### 낙찰정보 조회 (getDataSetOpnStdScsbidInfo)
- **필수**: operation="getDataSetOpnStdScsbidInfo", business_div_code
- **business_div_code 값**: "1"=물품, "2"=외자, "3"=공사, "5"=용역
- **권장**: opening_start_date, opening_end_date (개찰일시 범위)
- **선택**: num_rows, page_no

### 계약정보 조회 (getDataSetOpnStdCntrctInfo)
- **필수**: operation="getDataSetOpnStdCntrctInfo"
- **권장**: contract_start_date, contract_end_date (계약체결일자 범위)
- **선택**: institution_div_code ("1"=계약기관, "2"=수요기관), institution_code

## 공공조달통계정보서비스 (call_procurement_statistics_api)

### 전체 공공조달 현황 (getTotlPubPrcrmntSttus)
- **필수**: operation="getTotlPubPrcrmntSttus"
- **강력 권장**: search_base_year (YYYY 형식, 예: "2024")
- **선택**: num_rows, page_no

### 기관별/기업별 실적 조회
- **필수**: operation (해당 오퍼레이션명)
- **권장**: search_base_year, demand_institution_code 또는 corp_unity_no
- **선택**: 기타 필터 파라미터

## 종합쇼핑몰품목정보서비스 (call_shopping_mall_api)

### 다수공급자계약 품목정보 (getMASCntrctPrdctInfoList)
- **필수**: operation="getMASCntrctPrdctInfoList"
- **효과적 검색을 위한 권장**: product_name(품명) OR company_name(업체명) 중 하나 이상
- **선택**: registration_start_date, registration_end_date, 기타 필터

## 물품목록정보서비스 (call_product_list_api)

### 품목 분류 조회
- **필수**: operation (getPrdctClsfcNoUnit2Info, getPrdctClsfcNoUnit4Info 등)
- **계층별 조회시 권장**: upper_product_classification_no (상위 분류번호)
- **선택**: num_rows, page_no

## 일반적인 사용 원칙
1. **날짜 형식**: YYYYMMDDHHMM (예: "202409151430") 또는 YYYYMMDD
2. **페이징**: num_rows는 5-10개 권장 (컨텍스트 보호)
3. **검색 범위**: 너무 넓은 범위보다는 적절한 필터 사용 권장
4. **결과 없음**: 파라미터 조합이 잘못되었을 가능성, 더 넓은 조건으로 재시도
"""


@mcp.resource("guide://parameter-value-examples")
def parameter_value_examples() -> str:
    """정부조달 API 파라미터별 실제 사용 가능한 값들의 예시.

    각 파라미터에 입력할 수 있는 구체적인 값들과 형식을 제공합니다.
    """
    return """
# 정부조달 API 파라미터 값 예시

## 코드값 참조

### 업무구분코드 (business_div_code)
- "1": 물품 (가장 많이 사용됨)
- "2": 외자
- "3": 공사
- "5": 용역

### 기관구분코드 (institution_div_code)
- "1": 계약기관
- "2": 수요기관

### 조회구분 (inquiry_div)
- "1": 전체
- "2": 신규등록
- "3": 변경등록

## 날짜 형식 예시

### YYYYMMDDHHMM 형식 (시분까지)
- "202409151430": 2024년 9월 15일 14시 30분
- "202401010000": 2024년 1월 1일 00시 00분
- "202412312359": 2024년 12월 31일 23시 59분

### YYYYMMDD 형식 (일자만)
- "20240915": 2024년 9월 15일
- "20240101": 2024년 1월 1일

### YYYYMM 형식 (년월)
- "202409": 2024년 9월
- "202401": 2024년 1월

### YYYY 형식 (연도)
- "2024": 2024년
- "2023": 2023년

## 검색어 예시

### 품명 검색 (product_name, prdctClsfcNoNm)
- "컴퓨터": 컴퓨터 관련 제품
- "프린터": 프린터 관련 제품
- "사무용품": 사무용품 전반
- "의료기기": 의료장비
- "소프트웨어": SW 제품

### 업체명 검색 (company_name, cntrctCorpNm)
- "삼성전자": 삼성전자 관련 계약
- "LG전자": LG전자 관련 계약
- "현대": 현대 관련 계약 (현대자동차, 현대건설 등)
- "대한": 대한 관련 기업들

### 기관명 검색 (dminsttNm)
- "교육부": 교육부 관련
- "국방부": 국방부 관련
- "행정안전부": 행안부 관련
- "서울시": 서울특별시 관련

## 일반적인 수치값

### 페이지 관련
- num_rows: 5, 10, 20 (권장: 5-10, 컨텍스트 보호)
- page_no: 1, 2, 3... (1부터 시작)

### 물품분류번호 (예시)
- "432": 컴퓨터 관련 대분류
- "44": 사무용품 관련 대분류
- "453": 의료기기 관련 대분류

## 자주 사용되는 조합

### 최근 7일 입찰공고
- bid_notice_start_date: "202409080000"
- bid_notice_end_date: "202409152359"

### 당해년도 통계
- search_base_year: "2024"

### 물품 관련 낙찰정보
- business_div_code: "1"
- opening_start_date: "202409010000"
- opening_end_date: "202409152359"
"""


@mcp.resource("guide://common-search-patterns")
def common_search_patterns() -> str:
    """자주 사용되는 정부조달 검색 패턴과 최적화된 파라미터 조합.

    실제 업무에서 많이 사용되는 검색 시나리오별 최적 파라미터 조합을 제공합니다.
    """
    return """
# 자주 사용되는 정부조달 검색 패턴

## 시간 기반 검색 패턴

### 최근 공고/계약 조회
```
목적: 최근 일주일 입찰공고 확인
API: call_public_data_standard_api
필수: operation="getDataSetOpnStdBidPblancInfo"
권장: bid_notice_start_date=(7일전), bid_notice_end_date=(현재)
기본: num_rows=5
```

### 특정 기간 통계 조회
```
목적: 월별/연도별 조달 현황 파악
API: call_procurement_statistics_api
필수: operation="getTotlPubPrcrmntSttus"
필수: search_base_year="2024"
```

## 업종별 검색 패턴

### IT/컴퓨터 관련 조회
```
1단계: 분류 확인
API: call_product_list_api
operation="getPrdctClsfcNoUnit2Info" (대분류부터)

2단계: 실제 계약 조회
API: call_shopping_mall_api
operation="getMASCntrctPrdctInfoList"
권장: product_name="컴퓨터" 또는 "소프트웨어"
```

### 공사/건설 관련 조회
```
API: call_public_data_standard_api
operation="getDataSetOpnStdScsbidInfo" (낙찰정보)
필수: business_div_code="3" (공사)
권장: 날짜 범위 설정
```

## 기업 분석 패턴

### 특정 기업 계약 현황 조회
```
1단계: 기업명으로 계약품목 검색
API: call_shopping_mall_api
operation="getMASCntrctPrdctInfoList"
핵심: company_name="삼성전자" (정확한 업체명)

2단계: 상세 계약정보 확인 (필요시)
API: call_public_data_standard_api
operation="getDataSetOpnStdCntrctInfo"
```

### 경쟁업체 분석
```
API: call_shopping_mall_api
operation="getMASCntrctPrdctInfoList"
전략: product_name 동일하게 설정하여 경쟁업체 파악
```

## 기관별 분석 패턴

### 특정 기관 조달 현황
```
API: call_procurement_statistics_api
operation="getDminsttAccotEntrprsDivAccotArslt" (수요기관별 실적)
권장: search_base_year="2024"
선택: demand_institution_name="교육부" (기관명 검색)
```

### 지역별 조달 현황
```
API: call_procurement_statistics_api
operation="getRgnLmtSttus" (지역제한 현황)
필수: search_base_year="2024"
```

## 효율적인 검색 전략

### 점진적 범위 축소 전략
```
1단계: 넓은 범위로 시작
- 연도별 또는 월별 통계로 전체 규모 파악

2단계: 카테고리 필터링
- 업무구분(물품/공사/용역) 또는 품목분류로 범위 축소

3단계: 세부 조건 적용
- 기업명, 기관명, 구체적 날짜 범위로 정밀 검색
```

### 결과 없을 때 대응 전략
```
1. 날짜 범위 확대 (7일 → 30일 → 90일)
2. 검색어 단순화 ("삼성전자주식회사" → "삼성전자" → "삼성")
3. 상위 분류로 확대 (세부품목 → 대분류)
4. 필터 조건 완화 (업무구분 제거, 기관 제한 해제)
```

## 페이징 최적화 패턴

### 탐색 단계별 페이지 크기
```
1단계 (개요 파악): num_rows=3~5
2단계 (상세 확인): num_rows=10~20
3단계 (전수 조사): pagination_support 도구 활용
```

### 대용량 데이터 처리
```
API: call_api_with_pagination_support
전략: 작은 페이지 크기로 시작하여 패턴 파악 후 확대
```
"""

# Health check and server info endpoints for Smithery.ai deployment
@mcp.tool()
def health_check() -> Dict[str, Any]:
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "server": APP_NAME,
        "version": "2.0",
        "transport": "HTTP/SSE",
        "cors": "enabled",
        "tools_available": True,
        "deployment": "smithery_ready"
    }

@mcp.prompt()
def real_world_query_examples() -> str:
    """실제 정부조달 데이터 분석 시나리오별 쿼리 예제"""
    return """
# 실제 정부조달 데이터 분석 쿼리 예제

## 1. 사업 기회 탐색 시나리오

### 시나리오 1: IT 장비 공급업체 신규 진입
```python
# 1단계: 최근 IT 관련 입찰공고 파악
get_recent_bid_announcements(
    business_type="물품",  # 물품 카테고리
    days_back=30,         # 최근 한달
    num_rows=10
)

# 2단계: IT 분야 낙찰 현황 및 가격대 조사
get_successful_bids_by_business(
    business_type="물품",
    days_back=90,
    num_rows=15
)

# 3단계: 쇼핑몰에서 컴퓨터 관련 제품 현황 확인
search_shopping_mall_products(
    product_name="컴퓨터",
    num_rows=10
)
```

### 시나리오 2: 특정 지역 공사업체 시장 분석
```python
# 1단계: 공사 분야 전반적 시장 규모 파악
get_procurement_statistics_by_year(
    year="2024",
    num_rows=20
)

# 2단계: 최근 공사 입찰공고 동향
get_recent_bid_announcements(
    business_type="공사",
    days_back=60,
    num_rows=15
)

# 3단계: 공사 분야 실제 낙찰 결과 분석
get_successful_bids_by_business(
    business_type="공사",
    days_back=180,
    num_rows=20
)
```

## 2. 경쟁 분석 시나리오

### 시나리오 3: 특정 업체 계약 실적 추적
```python
# 1단계: 쇼핑몰에서 특정 업체 제품 확인
search_shopping_mall_products(
    company_name="삼성전자",
    num_rows=15
)

# 2단계: 해당 업체 관련 낙찰 정보 조회 (간접적)
# (업체명으로 직접 검색은 제한적이므로 카테고리 기반 접근)
get_successful_bids_by_business(
    business_type="물품",
    days_back=180,
    num_rows=30
)
```

### 시나리오 4: 가격 경쟁력 분석
```python
# 1단계: 특정 품목의 MAS 계약 현황
search_shopping_mall_products(
    product_name="프린터",
    num_rows=20
)

# 2단계: 동일 품목 입찰 공고 현황
get_recent_bid_announcements(
    business_type="물품",
    days_back=90,
    num_rows=20
)

# 3단계: 실제 낙찰가격 범위 파악
get_successful_bids_by_business(
    business_type="물품",
    days_back=120,
    num_rows=25
)
```

## 3. 시장 트렌드 분석 시나리오

### 시나리오 5: 연도별 조달 시장 변화 추이
```python
# 1단계: 2023년 통계
get_procurement_statistics_by_year(
    year="2023",
    num_rows=30
)

# 2단계: 2024년 통계 비교
get_procurement_statistics_by_year(
    year="2024",
    num_rows=30
)

# 3단계: 최근 실제 계약 동향으로 검증
get_successful_bids_by_business(
    business_type="물품",
    days_back=60,
    num_rows=20
)
```

### 시나리오 6: 특정 분야 계절성 분석
```python
# 1단계: 현재 시점 입찰 현황
get_recent_bid_announcements(
    business_type="용역",
    days_back=30,
    num_rows=15
)

# 2단계: 3개월 전 동일 기간과 비교
get_successful_bids_by_business(
    business_type="용역",
    days_back=120,
    num_rows=25
)

# 3단계: 연간 통계로 전체 맥락 파악
get_procurement_statistics_by_year(
    year="2024",
    num_rows=20
)
```

## 4. 리스크 관리 시나리오

### 시나리오 7: 시장 포화도 분석
```python
# 1단계: 특정 분야 전체 공급업체 현황
search_shopping_mall_products(
    product_name="사무용품",
    num_rows=30
)

# 2단계: 해당 분야 입찰 경쟁 현황
get_recent_bid_announcements(
    business_type="물품",
    days_back=45,
    num_rows=20
)

# 3단계: 실제 낙찰률 및 경쟁강도 파악
get_successful_bids_by_business(
    business_type="물품",
    days_back=90,
    num_rows=25
)
```

## 5. 전략 수립 시나리오

### 시나리오 8: 신제품 출시 타이밍 분석
```python
# 1단계: 기존 유사 제품 계약 현황
search_shopping_mall_products(
    product_name="네트워크장비",
    num_rows=20
)

# 2단계: 관련 분야 최근 입찰 빈도
get_recent_bid_announcements(
    business_type="물품",
    days_back=60,
    num_rows=25
)

# 3단계: 시장 규모 및 성장성 판단
get_procurement_statistics_by_year(
    year="2024",
    num_rows=25
)
```

## 6. 매개변수 최적화 팁

### 효율적인 탐색 전략
1. **처음엔 작게 시작**: num_rows=5-10으로 전체 패턴 파악
2. **점진적 확장**: 필요시 num_rows 증가 및 기간 확장
3. **교차 검증**: 여러 API 결과를 조합하여 신뢰성 확보

### 컨텍스트 보호 활용
1. **자동 압축 기능**: 대용량 결과는 자동으로 핵심 정보만 추출
2. **페이징 가이드**: 더 많은 데이터 필요시 안내 메시지 활용
3. **키 필드 집중**: 입찰번호, 계약금액 등 핵심 정보 우선 확인

### 실무 활용 노하우
1. **코드 변환 자동화**: 한글 입력시 자동 코드 매핑 활용
2. **날짜 계산 자동화**: days_back 파라미터로 간편한 기간 설정
3. **결과 해석**: 빈 결과시 조건 완화, 과다 결과시 필터 강화
"""


def main():
    """Main entry point for the FastMCP 2.0 server with secure configuration."""
    logger.info(f"Starting {APP_NAME} FastMCP 2.0 server...")
    
    try:
        # Validate service key before starting server
        from .core.config import get_service_key
        get_service_key()  # This will raise an exception if key is invalid
        
        # Check for transport mode with security validation
        transport = os.environ.get("FASTMCP_TRANSPORT", "stdio")
        host = os.environ.get("FASTMCP_HOST", "127.0.0.1")
        
        # Validate host for production deployment
        if transport in ["http", "sse"] and host == "0.0.0.0":
            logger.warning("Server will bind to all interfaces (0.0.0.0) - ensure proper firewall configuration")
        
        # Use PORT environment variable (smithery.ai compatible - defaults to 8081)
        try:
            port = int(os.environ.get("PORT") or os.environ.get("FASTMCP_PORT", "8081"))
        except ValueError:
            logger.error("Invalid PORT value in environment, using default 8081")
            port = 8081
        
        if transport == "http":
            # HTTP mode for smithery.ai deployment - Pure FastMCP approach
            logger.info(f"Starting HTTP-accessible MCP server on {host}:{port}")
            logger.info("Transport mode: HTTP (Pure FastMCP with CORS)")
            logger.info("CORS enabled for Smithery.ai: *origins, credentials, MCP headers")

            # Use FastMCP's built-in HTTP app with Smithery.ai compatibility
            import asyncio
            import uvicorn
            from starlette.middleware.cors import CORSMiddleware
            from .core.smithery_middleware import SmitheryCompatibilityMiddleware

            # Create FastMCP HTTP app (FastMCP 2.12+ standard)
            try:
                app = mcp.http_app()
                logger.info("Using FastMCP 2.12+ http_app")
            except AttributeError:
                app = mcp.sse_app()
                logger.info("Fallback to FastMCP sse_app")

            # Add Smithery.ai compatibility middleware FIRST (before CORS)
            app.add_middleware(SmitheryCompatibilityMiddleware)
            logger.info("✅ Smithery.ai compatibility middleware added")

            # Add comprehensive CORS middleware for Smithery.ai
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["mcp-session-id", "mcp-protocol-version"],
                max_age=86400,
            )

            logger.info("Pure FastMCP server ready with enhanced CORS")
            uvicorn.run(app, host=host, port=port)
        elif transport == "sse":
            # SSE mode for real-time communication
            logger.info(f"Starting SSE transport on {host}:{port}")
            logger.info("Transport mode: Server-Sent Events")
            logger.info("CORS enabled for Smithery.ai: *origins, credentials, MCP headers")
            import asyncio

            # Start FastMCP server with CORS handled by middleware patches
            asyncio.run(mcp.run_async("sse", host=host, port=port))
        else:
            # Default STDIO mode for local development
            logger.info("Starting STDIO transport")
            logger.info("Transport mode: STDIO (development/local)")
            mcp.run("stdio")
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Server startup failed due to configuration issues")
        return 1
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    main()