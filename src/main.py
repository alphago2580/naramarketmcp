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
from .tools.naramarket import naramarket_tools
from .tools.openapi_tools import openapi_tools
from .tools.enhanced_tools import enhanced_tools


# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("naramarket")

# Initialize FastMCP 2.0
try:
    mcp = FastMCP(APP_NAME)
    logger.info(f"FastMCP 2.0 initialized: {APP_NAME}")
except Exception as e:
    raise RuntimeError(f"Failed to init FastMCP 2.0: {e}")


# Register MCP Tools
@mcp.tool()
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


@mcp.tool()
def get_detailed_attributes(api_item: Dict[str, Any]) -> DetailResult:
    """Get detailed product attributes from G2B API.
    
    Args:
        api_item: Product item from list API
        
    Returns:
        DetailResult with attributes or error
    """
    return naramarket_tools.get_detailed_attributes(api_item)


@mcp.tool()
def crawl_to_memory(
    category: str,
    page_no: int = 1,
    num_rows: int = 100,
    days_back: int = 7,
    inqry_bgn_date: Optional[str] = None,
    inqry_end_date: Optional[str] = None,
    include_attributes: bool = True
) -> Dict[str, Any]:
    """Crawl category data and return results in memory (no file saving).
    
    Args:
        category: Product category to crawl
        page_no: Page number to fetch (default 1)
        num_rows: Number of rows per page (default 100)
        days_back: Days to go back if dates not provided (default 7)
        inqry_bgn_date: Start date in YYYYMMDD format
        inqry_end_date: End date in YYYYMMDD format
        include_attributes: Include detailed attributes for each item
        
    Returns:
        Dict with crawled data in memory
    """
    # Get list data
    list_result = naramarket_tools.crawl_list(
        category=category,
        page_no=page_no,
        num_rows=num_rows,
        days_back=days_back,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date
    )
    
    if not list_result.get("success") or not include_attributes:
        return list_result
    
    # Get detailed attributes for each item
    items_with_attributes = []
    for item in list_result.get("items", []):
        detail_result = naramarket_tools.get_detailed_attributes(item)
        if detail_result.get("success"):
            item_with_attrs = item.copy()
            item_with_attrs["detailed_attributes"] = detail_result.get("attributes", {})
            items_with_attributes.append(item_with_attrs)
        else:
            items_with_attributes.append(item)
    
    return {
        "success": True,
        "items": items_with_attributes,
        "total_count": list_result.get("total_count", 0),
        "current_page": page_no,
        "category": category,
        "attributes_included": include_attributes
    }




@mcp.tool()
def server_info() -> ServerInfo:
    """Get server status and available tools list.
    
    Returns:
        ServerInfo with server details
    """
    return naramarket_tools.server_info()


# OpenAPI-based tools
@mcp.tool()
def get_bid_announcement_info(
    num_rows: int = 10,
    page_no: int = 1,
    bid_notice_start_date: Optional[str] = None,
    bid_notice_end_date: Optional[str] = None
) -> Dict[str, Any]:
    """입찰공고정보 조회 (OpenAPI 기반).
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        bid_notice_start_date: 입찰공고시작일시 (YYYYMMDDHHMM)
        bid_notice_end_date: 입찰공고종료일시 (YYYYMMDDHHMM)
        
    Returns:
        입찰공고정보 조회 결과
    """
    return openapi_tools.get_bid_announcement_info(
        num_rows=num_rows,
        page_no=page_no,
        bid_notice_start_date=bid_notice_start_date,
        bid_notice_end_date=bid_notice_end_date
    )


@mcp.tool()
def get_successful_bid_info(
    business_div_code: str,
    num_rows: int = 10,
    page_no: int = 1,
    opening_start_date: Optional[str] = None,
    opening_end_date: Optional[str] = None
) -> Dict[str, Any]:
    """낙찰정보 조회 (OpenAPI 기반).
    
    Args:
        business_div_code: 업무구분코드 (1:물품, 2:외자, 3:공사, 5:용역)
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        opening_start_date: 개찰시작일시 (YYYYMMDDHHMM)
        opening_end_date: 개찰종료일시 (YYYYMMDDHHMM)
        
    Returns:
        낙찰정보 조회 결과
    """
    return openapi_tools.get_successful_bid_info(
        business_div_code=business_div_code,
        num_rows=num_rows,
        page_no=page_no,
        opening_start_date=opening_start_date,
        opening_end_date=opening_end_date
    )


@mcp.tool()
def get_contract_info(
    num_rows: int = 10,
    page_no: int = 1,
    contract_start_date: Optional[str] = None,
    contract_end_date: Optional[str] = None,
    institution_div_code: Optional[str] = None,
    institution_code: Optional[str] = None
) -> Dict[str, Any]:
    """계약정보 조회 (OpenAPI 기반).
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        contract_start_date: 계약체결시작일자 (YYYYMMDD)
        contract_end_date: 계약체결종료일자 (YYYYMMDD)
        institution_div_code: 기관구분코드 (1:계약기관, 2:수요기관)
        institution_code: 기관코드
        
    Returns:
        계약정보 조회 결과
    """
    return openapi_tools.get_contract_info(
        num_rows=num_rows,
        page_no=page_no,
        contract_start_date=contract_start_date,
        contract_end_date=contract_end_date,
        institution_div_code=institution_div_code,
        institution_code=institution_code
    )


@mcp.tool()
def get_total_procurement_status(
    num_rows: int = 10,
    page_no: int = 1,
    search_base_year: Optional[str] = None
) -> Dict[str, Any]:
    """전체 공공조달 현황 조회 (OpenAPI 기반).
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        search_base_year: 검색기준년도 (YYYY)
        
    Returns:
        전체 공공조달 현황 조회 결과
    """
    return openapi_tools.get_total_procurement_status(
        num_rows=num_rows,
        page_no=page_no,
        search_base_year=search_base_year
    )


@mcp.tool()
def get_mas_contract_product_info(
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
    """다수공급자계약 품목정보 조회 (OpenAPI 기반) - 핵심 API.
    
    이 API는 get_detailed_attributes와 연계되어 사용되는 매우 중요한 API입니다.
    
    Args:
        num_rows: 한 페이지 결과 수
        page_no: 페이지 번호
        registration_start_date: 등록일시 시작일시 (YYYYMMDDHH24M)
        registration_end_date: 등록일시 종료일시 (YYYYMMDDHH24M)
        product_name: 품명
        product_id: 물품식별번호
        contract_company_name: 계약업체명
        change_start_date: 변경일시 시작일시 (YYYYMMDDHH24M)
        change_end_date: 변경일시 종료일시 (YYYYMMDDHH24M)
        product_certification: 제품인증여부 (Y/N)
        
    Returns:
        다수공급자계약 품목정보 조회 결과
    """
    return openapi_tools.get_mas_contract_product_info(
        num_rows=num_rows,
        page_no=page_no,
        registration_start_date=registration_start_date,
        registration_end_date=registration_end_date,
        product_name=product_name,
        product_id=product_id,
        contract_company_name=contract_company_name,
        change_start_date=change_start_date,
        change_end_date=change_end_date,
        product_certification=product_certification
    )


# Enhanced Korean Government Procurement APIs (Parameterized)
@mcp.tool()
def call_public_data_standard_api(
    operation: str,
    num_rows: int = 10,
    page_no: int = 1,
    bid_notice_start_date: Optional[str] = None,
    bid_notice_end_date: Optional[str] = None,
    business_div_code: Optional[str] = None,
    opening_start_date: Optional[str] = None,
    opening_end_date: Optional[str] = None,
    contract_start_date: Optional[str] = None,
    contract_end_date: Optional[str] = None,
    institution_div_code: Optional[str] = None,
    institution_code: Optional[str] = None
) -> Dict[str, Any]:
    """공공데이터개방표준서비스 API 호출 (Enhanced parameterized).

    Available operations:
    - getDataSetOpnStdBidPblancInfo: 입찰공고정보 조회
    - getDataSetOpnStdScsbidInfo: 낙찰정보 조회
    - getDataSetOpnStdCntrctInfo: 계약정보 조회

    Args:
        operation: API 오퍼레이션명
        num_rows: 한 페이지 결과 수 (기본값: 10)
        page_no: 페이지 번호 (기본값: 1)
        bid_notice_start_date: 입찰공고시작일시 (YYYYMMDDHHMM)
        bid_notice_end_date: 입찰공고종료일시 (YYYYMMDDHHMM)
        business_div_code: 업무구분코드 (1:물품, 2:외자, 3:공사, 5:용역)
        opening_start_date: 개찰시작일시 (YYYYMMDDHHMM)
        opening_end_date: 개찰종료일시 (YYYYMMDDHHMM)
        contract_start_date: 계약체결시작일자 (YYYYMMDD)
        contract_end_date: 계약체결종료일자 (YYYYMMDD)
        institution_div_code: 기관구분코드 (1:계약기관, 2:수요기관)
        institution_code: 기관코드

    Returns:
        API 응답 데이터
    """
    kwargs = {}
    if bid_notice_start_date: kwargs["bidNtceBgnDt"] = bid_notice_start_date
    if bid_notice_end_date: kwargs["bidNtceEndDt"] = bid_notice_end_date
    if business_div_code: kwargs["bsnsDivCd"] = business_div_code
    if opening_start_date: kwargs["opengBgnDt"] = opening_start_date
    if opening_end_date: kwargs["opengEndDt"] = opening_end_date
    if contract_start_date: kwargs["cntrctCnclsBgnDate"] = contract_start_date
    if contract_end_date: kwargs["cntrctCnclsEndDate"] = contract_end_date
    if institution_div_code: kwargs["insttDivCd"] = institution_div_code
    if institution_code: kwargs["insttCd"] = institution_code

    return enhanced_tools.call_public_data_standard_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
    )


@mcp.tool()
def call_procurement_statistics_api(
    operation: str,
    num_rows: int = 10,
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
    link_system_code: Optional[str] = None
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

    Returns:
        API 응답 데이터
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

    return enhanced_tools.call_procurement_statistics_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
    )


@mcp.tool()
def call_product_list_api(
    operation: str,
    num_rows: int = 10,
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
    change_period_end_date: Optional[str] = None
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

    Returns:
        API 응답 데이터
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

    return enhanced_tools.call_product_list_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
    )


@mcp.tool()
def call_shopping_mall_api(
    operation: str,
    num_rows: int = 10,
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
    procurement_div: Optional[str] = None
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

    Returns:
        API 응답 데이터
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

    return enhanced_tools.call_shopping_mall_api(
        operation=operation,
        numOfRows=num_rows,
        pageNo=page_no,
        **kwargs
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
        
        # Use PORT environment variable (smithery.ai compatible)
        try:
            port = int(os.environ.get("PORT") or os.environ.get("FASTMCP_PORT", "8000"))
        except ValueError:
            logger.error("Invalid PORT value in environment, using default 8000")
            port = 8000
        
        if transport == "http":
            # HTTP mode for smithery.ai deployment
            # Note: FastMCP 2.2.0 uses SSE transport to provide HTTP endpoints
            # This creates HTTP-accessible MCP endpoints for web deployment
            logger.info(f"Starting HTTP-accessible MCP server on {host}:{port}")
            logger.info("Transport mode: HTTP (via SSE transport)")
            import asyncio
            asyncio.run(mcp.run_async("sse", host=host, port=port))
        elif transport == "sse":
            # SSE mode for real-time communication
            logger.info(f"Starting SSE transport on {host}:{port}")
            logger.info("Transport mode: Server-Sent Events")
            import asyncio
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