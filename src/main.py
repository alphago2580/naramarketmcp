"""Main application entry point for Naramarket MCP 2.0 Server with OpenAPI integration."""

import logging
import os
from typing import Any, Dict, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("fastmcp>=2.0.0 is required. pip install fastmcp>=2.0.0")

from .core.config import APP_NAME
from .core.models import CrawlListResult, DetailResult, ServerInfo
from .tools.naramarket import naramarket_tools
from .tools.enhanced_tools import enhanced_tools
from .guides import (
    WORKFLOW_GUIDE,
    PARAMETER_SELECTION_GUIDE,
    API_PARAMETER_REQUIREMENTS,
    PARAMETER_VALUE_EXAMPLES,
    COMMON_SEARCH_PATTERNS,
    REAL_WORLD_QUERY_EXAMPLES,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("naramarket")

try:
    mcp = FastMCP(APP_NAME)
    logger.info(f"FastMCP 2.0 initialized: {APP_NAME}")
except Exception as e:
    raise RuntimeError(f"Failed to init FastMCP 2.0: {e}")


# ── Basic Tools ─────────────────────────────────────────────────────────────


@mcp.tool(name="crawl_list", description="Fetch product list for a category from Nara Market API")
def crawl_list(
    category: str,
    page_no: int = 1,
    num_rows: int = 100,
    days_back: int = 7,
    inqry_bgn_date: Optional[str] = None,
    inqry_end_date: Optional[str] = None,
) -> CrawlListResult:
    """Fetch product list for a category from Nara Market API."""
    return naramarket_tools.crawl_list(
        category=category,
        page_no=page_no,
        num_rows=num_rows,
        days_back=days_back,
        inqry_bgn_date=inqry_bgn_date,
        inqry_end_date=inqry_end_date,
    )


@mcp.tool(name="get_detailed_attributes", description="Get detailed product attributes from G2B API")
def get_detailed_attributes(api_item: Dict[str, Any]) -> DetailResult:
    """Get detailed product attributes from G2B API."""
    return naramarket_tools.get_detailed_attributes(api_item)


@mcp.tool()
def server_info() -> ServerInfo:
    """Get server status and available tools list."""
    return naramarket_tools.server_info()


# ── Government Procurement API Tools ────────────────────────────────────────


@mcp.tool()
def call_public_data_standard_api(
    operation: str,
    num_rows: int = 5,
    page_no: int = 1,
    bid_notice_start_date: Optional[str] = None,
    bid_notice_end_date: Optional[str] = None,
    business_div_code: Optional[str] = None,
    opening_start_date: Optional[str] = None,
    opening_end_date: Optional[str] = None,
    contract_start_date: Optional[str] = None,
    contract_end_date: Optional[str] = None,
    institution_div_code: Optional[str] = None,
    institution_code: Optional[str] = None,
) -> Dict[str, Any]:
    """공공데이터개방표준서비스 API 호출.

    Operations: getDataSetOpnStdBidPblancInfo (입찰공고), getDataSetOpnStdScsbidInfo (낙찰),
    getDataSetOpnStdCntrctInfo (계약)

    Args:
        operation: API 오퍼레이션명
        num_rows: 결과 수 (기본 5)
        page_no: 페이지 번호
        bid_notice_start_date: 입찰공고시작일 (YYYYMMDDHHMM)
        bid_notice_end_date: 입찰공고종료일 (YYYYMMDDHHMM)
        business_div_code: 업무구분코드 (1:물품, 2:외자, 3:공사, 5:용역)
        opening_start_date: 개찰시작일 (YYYYMMDDHHMM)
        opening_end_date: 개찰종료일 (YYYYMMDDHHMM)
        contract_start_date: 계약체결시작일 (YYYYMMDD)
        contract_end_date: 계약체결종료일 (YYYYMMDD)
        institution_div_code: 기관구분 (1:계약기관, 2:수요기관)
        institution_code: 기관코드
    """
    kwargs = {}
    if bid_notice_start_date:
        kwargs["bidNtceBgnDt"] = bid_notice_start_date
    if bid_notice_end_date:
        kwargs["bidNtceEndDt"] = bid_notice_end_date
    if business_div_code:
        kwargs["bsnsDivCd"] = business_div_code
    if opening_start_date:
        kwargs["opengBgnDt"] = opening_start_date
    if opening_end_date:
        kwargs["opengEndDt"] = opening_end_date
    if contract_start_date:
        kwargs["cntrctCnclsBgnDate"] = contract_start_date
    if contract_end_date:
        kwargs["cntrctCnclsEndDate"] = contract_end_date
    if institution_div_code:
        kwargs["insttDivCd"] = institution_div_code
    if institution_code:
        kwargs["insttCd"] = institution_code

    return enhanced_tools.call_public_data_standard_api(
        operation=operation, numOfRows=num_rows, pageNo=page_no, **kwargs
    )


@mcp.tool()
def call_procurement_statistics_api(
    operation: str,
    num_rows: int = 5,
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
) -> Dict[str, Any]:
    """공공조달통계정보서비스 API 호출 (14개 오퍼레이션 지원).

    Args:
        operation: API 오퍼레이션명
        search_base_year: 검색기준년도 (YYYY)
        search_base_month_start: 기준년월 시작 (YYYYMM)
        search_base_month_end: 기준년월 종료 (YYYYMM)
        demand_institution_code: 수요기관코드
        demand_institution_name: 수요기관명
        corp_unity_no: 업체통합번호
        corp_name: 업체명
    """
    kwargs = {}
    if search_base_year:
        kwargs["srchBssYear"] = search_base_year
    if search_base_month_start:
        kwargs["srchBssYmBgn"] = search_base_month_start
    if search_base_month_end:
        kwargs["srchBssYmEnd"] = search_base_month_end
    if demand_institution_code:
        kwargs["dminsttCd"] = demand_institution_code
    if demand_institution_name:
        kwargs["dminsttNm"] = demand_institution_name
    if corp_unity_no:
        kwargs["corpUntyNo"] = corp_unity_no
    if corp_name:
        kwargs["corpNm"] = corp_name
    if product_classification_no:
        kwargs["prdctClsfcNo"] = product_classification_no
    if product_classification_name:
        kwargs["prdctClsfcNm"] = product_classification_name
    if lower_institution_result_inclusion:
        kwargs["lwrInsttArsltInclsnYn"] = lower_institution_result_inclusion
    if link_system_code:
        kwargs["linkSystmCd"] = link_system_code

    return enhanced_tools.call_procurement_statistics_api(
        operation=operation, numOfRows=num_rows, pageNo=page_no, **kwargs
    )


@mcp.tool()
def call_product_list_api(
    operation: str,
    num_rows: int = 5,
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
) -> Dict[str, Any]:
    """물품목록정보서비스 API 호출 (12개 오퍼레이션 지원).

    Args:
        operation: API 오퍼레이션명
        upper_product_classification_no: 상위 물품분류번호
        product_classification_no: 물품분류번호
        product_id_no: 물품식별번호
        product_classification_name: 품명
        korean_product_name: 한글품목명
        manufacturer_corp_name: 제조업체명
    """
    kwargs = {}
    if upper_product_classification_no:
        kwargs["upPrdctClsfcNo"] = upper_product_classification_no
    if product_classification_no:
        kwargs["prdctClsfcNo"] = product_classification_no
    if product_id_no:
        kwargs["prdctIdntNo"] = product_id_no
    if detail_product_classification_no:
        kwargs["dtilPrdctClsfcNo"] = detail_product_classification_no
    if product_classification_name:
        kwargs["prdctClsfcNoNm"] = product_classification_name
    if product_classification_eng_name:
        kwargs["prdctClsfcNoEngNm"] = product_classification_eng_name
    if korean_product_name:
        kwargs["krnPrdctNm"] = korean_product_name
    if manufacturer_corp_name:
        kwargs["mnfctCorpNm"] = manufacturer_corp_name
    if region_code:
        kwargs["rgnCd"] = region_code
    if inquiry_div:
        kwargs["inqryDiv"] = inquiry_div
    if inquiry_start_date:
        kwargs["inqryBgnDt"] = inquiry_start_date
    if inquiry_end_date:
        kwargs["inqryEndDt"] = inquiry_end_date
    if change_period_start_date:
        kwargs["chgPrdBgnDt"] = change_period_start_date
    if change_period_end_date:
        kwargs["chgPrdEndDt"] = change_period_end_date

    return enhanced_tools.call_product_list_api(
        operation=operation, numOfRows=num_rows, pageNo=page_no, **kwargs
    )


@mcp.tool()
def call_shopping_mall_api(
    operation: str,
    num_rows: int = 5,
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
) -> Dict[str, Any]:
    """종합쇼핑몰 품목정보 서비스 API 호출 (9개 오퍼레이션 지원).

    Args:
        operation: API 오퍼레이션명
        product_classification_name: 품명
        contract_corp_name: 계약업체명
        product_id_no: 물품식별번호
        registration_start_date: 등록시작일 (YYYYMMDDHH24M)
        registration_end_date: 등록종료일 (YYYYMMDDHH24M)
    """
    kwargs = {}
    if registration_start_date:
        kwargs["rgstDtBgnDt"] = registration_start_date
    if registration_end_date:
        kwargs["rgstDtEndDt"] = registration_end_date
    if change_start_date:
        kwargs["chgDtBgnDt"] = change_start_date
    if change_end_date:
        kwargs["chgDtEndDt"] = change_end_date
    if product_classification_name:
        kwargs["prdctClsfcNoNm"] = product_classification_name
    if product_id_no:
        kwargs["prdctIdntNo"] = product_id_no
    if contract_corp_name:
        kwargs["cntrctCorpNm"] = contract_corp_name
    if product_certification:
        kwargs["prodctCertYn"] = product_certification
    if inquiry_div:
        kwargs["inqryDiv"] = inquiry_div
    if inquiry_start_date:
        kwargs["inqryBgnDate"] = inquiry_start_date
    if inquiry_end_date:
        kwargs["inqryEndDate"] = inquiry_end_date
    if detail_product_classification_name:
        kwargs["dtilPrdctClsfcNoNm"] = detail_product_classification_name
    if product_id_name:
        kwargs["prdctIdntNoNm"] = product_id_name
    if excellent_product:
        kwargs["exclcProdctYn"] = excellent_product
    if mas_yn:
        kwargs["masYn"] = mas_yn
    if shopping_contract_no:
        kwargs["shopngCntrctNo"] = shopping_contract_no
    if registration_cancel:
        kwargs["regtCncelYn"] = registration_cancel
    if demand_institution_name:
        kwargs["dminsttNm"] = demand_institution_name
    if demand_institution_region_name:
        kwargs["dminsttRgnNm"] = demand_institution_region_name
    if delivery_request_no:
        kwargs["dlvrReqNo"] = delivery_request_no
    if inquiry_product_div:
        kwargs["inqryPrdctDiv"] = inquiry_product_div
    if procurement_div:
        kwargs["prcrmntDiv"] = procurement_div

    return enhanced_tools.call_shopping_mall_api(
        operation=operation, numOfRows=num_rows, pageNo=page_no, **kwargs
    )


# ── Exploration Tools ───────────────────────────────────────────────────────


@mcp.tool()
def get_all_api_services_info() -> Dict[str, Any]:
    """모든 API 서비스 및 오퍼레이션 정보 조회."""
    return enhanced_tools.get_all_api_services_info()


@mcp.tool()
def get_api_operations(service_type: str) -> Dict[str, Any]:
    """특정 서비스의 오퍼레이션 목록 조회.

    Args:
        service_type: public_data_standard, procurement_statistics, product_list, shopping_mall
    """
    return enhanced_tools.get_api_operations(service_type)


@mcp.tool()
def call_api_with_pagination_support(
    service_type: str,
    operation: str,
    num_rows: int = 10,
    page_no: int = 1,
    bid_notice_start_date: Optional[str] = None,
    bid_notice_end_date: Optional[str] = None,
    search_base_year: Optional[str] = None,
    upper_product_classification_no: Optional[str] = None,
    registration_start_date: Optional[str] = None,
    registration_end_date: Optional[str] = None,
    bid_announcement_notice_type: Optional[str] = None,
    business_type: Optional[str] = None,
    company_name: Optional[str] = None,
    product_name: Optional[str] = None,
) -> Dict[str, Any]:
    """페이징 지원 API 호출.

    Args:
        service_type: 서비스 타입
        operation: 오퍼레이션명
        num_rows: 페이지 크기 (기본 10)
        page_no: 페이지 번호
    """
    params: Dict[str, Any] = {"numOfRows": num_rows, "pageNo": page_no}
    optional = {
        "bidNoticeStartDate": bid_notice_start_date,
        "bidNoticeEndDate": bid_notice_end_date,
        "searchBaseYear": search_base_year,
        "upperProductClassificationNo": upper_product_classification_no,
        "registrationStartDate": registration_start_date,
        "registrationEndDate": registration_end_date,
        "bidAnnouncementNoticeType": bid_announcement_notice_type,
        "businessType": business_type,
        "companyName": company_name,
        "productName": product_name,
    }
    for key, value in optional.items():
        if value is not None:
            params[key] = value

    return enhanced_tools.call_api_with_pagination_guidance(
        service_type=service_type, operation=operation, params=params
    )


@mcp.tool()
def get_data_exploration_guide(
    service_type: str,
    operation: str,
    expected_data_size: str = "medium",
) -> Dict[str, Any]:
    """데이터 탐색을 위한 최적화된 가이드 제공.

    Args:
        service_type: 서비스 타입
        operation: 오퍼레이션명
        expected_data_size: 예상 크기 ("small", "medium", "large")
    """
    configs = {
        "small": {"num_rows": 10, "strategy": "단일 요청으로 충분"},
        "medium": {"num_rows": 5, "strategy": "2-3회 페이징 권장"},
        "large": {"num_rows": 3, "strategy": "다중 페이징으로 점진적 탐색"},
    }
    config = configs.get(expected_data_size, configs["medium"])

    return {
        "service_type": service_type,
        "operation": operation,
        "recommended_config": config,
        "sample_first_request": {"num_rows": config["num_rows"], "page_no": 1},
        "exploration_tips": [
            "첫 요청으로 데이터 구조 파악",
            "pagination 정보로 전체 규모 확인",
            "필요시 검색 조건 추가로 범위 축소",
        ],
    }


# ── AI-Friendly Simplified Tools ────────────────────────────────────────────


@mcp.tool()
def get_recent_bid_announcements(num_rows: int = 5, days_back: int = 7) -> Dict[str, Any]:
    """최근 입찰공고 조회 (날짜 자동 계산).

    Args:
        num_rows: 조회할 공고 수 (기본 5)
        days_back: 며칠 전까지 조회 (기본 7일)
    """
    from datetime import datetime, timedelta

    end = datetime.now()
    start = end - timedelta(days=days_back)
    return enhanced_tools.call_public_data_standard_api(
        operation="getDataSetOpnStdBidPblancInfo",
        numOfRows=num_rows,
        pageNo=1,
        bidNtceBgnDt=start.strftime("%Y%m%d0000"),
        bidNtceEndDt=end.strftime("%Y%m%d2359"),
    )


@mcp.tool()
def get_successful_bids_by_business_type(
    business_type: str, num_rows: int = 5, days_back: int = 30
) -> Dict[str, Any]:
    """업무구분별 낙찰정보 조회 (한글 → 코드 자동 변환).

    Args:
        business_type: "물품", "외자", "공사", "용역" 중 선택
        num_rows: 결과 수 (기본 5)
        days_back: 기간 (기본 30일)
    """
    from datetime import datetime, timedelta

    codes = {"물품": "1", "외자": "2", "공사": "3", "용역": "5"}
    code = codes.get(business_type, "1")
    end = datetime.now()
    start = end - timedelta(days=days_back)
    return enhanced_tools.call_public_data_standard_api(
        operation="getDataSetOpnStdScsbidInfo",
        numOfRows=num_rows,
        pageNo=1,
        bsnsDivCd=code,
        opengBgnDt=start.strftime("%Y%m%d0000"),
        opengEndDt=end.strftime("%Y%m%d2359"),
    )


@mcp.tool()
def get_procurement_statistics_by_year(year: str, num_rows: int = 10) -> Dict[str, Any]:
    """연도별 공공조달 통계 조회.

    Args:
        year: 조회 연도 (예: "2024")
        num_rows: 결과 수 (기본 10)
    """
    return enhanced_tools.call_procurement_statistics_api(
        operation="getTotlPubPrcrmntSttus", numOfRows=num_rows, pageNo=1, srchBssYear=year
    )


@mcp.tool()
def search_shopping_mall_products(
    product_name: Optional[str] = None,
    company_name: Optional[str] = None,
    num_rows: int = 5,
) -> Dict[str, Any]:
    """나라장터 쇼핑몰 제품 검색.

    Args:
        product_name: 제품명 (선택)
        company_name: 업체명 (선택)
        num_rows: 결과 수 (기본 5)
    """
    kwargs = {}
    if product_name:
        kwargs["prdctClsfcNoNm"] = product_name
    if company_name:
        kwargs["cntrctCorpNm"] = company_name
    return enhanced_tools.call_shopping_mall_api(
        operation="getMASCntrctPrdctInfoList", numOfRows=num_rows, pageNo=1, **kwargs
    )


# ── Health Check ────────────────────────────────────────────────────────────


@mcp.tool()
def health_check() -> Dict[str, Any]:
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "server": APP_NAME,
        "version": "2.0",
        "transport": "HTTP/SSE",
        "tools_available": True,
    }


# ── MCP Prompts & Resources ────────────────────────────────────────────────


@mcp.prompt()
def workflow_guide() -> str:
    """정부조달 데이터 분석을 위한 단계별 워크플로우 가이드"""
    return WORKFLOW_GUIDE


@mcp.prompt()
def parameter_selection_guide() -> str:
    """API 파라미터 선택 및 최적화 가이드"""
    return PARAMETER_SELECTION_GUIDE


@mcp.prompt()
def real_world_query_examples() -> str:
    """실제 업무 시나리오별 쿼리 예제"""
    return REAL_WORLD_QUERY_EXAMPLES


@mcp.resource("guide://api-parameter-requirements")
def api_parameter_requirements() -> str:
    """API별 필수/선택/권장 파라미터 가이드"""
    return API_PARAMETER_REQUIREMENTS


@mcp.resource("guide://parameter-value-examples")
def parameter_value_examples() -> str:
    """파라미터별 실제 사용 가능한 값 예시"""
    return PARAMETER_VALUE_EXAMPLES


@mcp.resource("guide://common-search-patterns")
def common_search_patterns() -> str:
    """자주 사용되는 검색 패턴 및 최적화 전략"""
    return COMMON_SEARCH_PATTERNS


# ── Server Entry Point ──────────────────────────────────────────────────────


def main():
    """Start the FastMCP 2.0 server."""
    logger.info(f"Starting {APP_NAME} FastMCP 2.0 server...")

    try:
        from .core.config import get_service_key

        get_service_key()

        transport = os.environ.get("FASTMCP_TRANSPORT", "stdio")
        host = os.environ.get("FASTMCP_HOST", "127.0.0.1")

        try:
            port = int(os.environ.get("PORT") or os.environ.get("FASTMCP_PORT", "8081"))
        except ValueError:
            logger.error("Invalid PORT value, using default 8081")
            port = 8081

        if transport == "http":
            logger.info(f"Starting HTTP server on {host}:{port}")
            import uvicorn
            from starlette.middleware.cors import CORSMiddleware
            from .core.smithery_middleware import SmitheryCompatibilityMiddleware

            try:
                app = mcp.http_app()
            except AttributeError:
                app = mcp.sse_app()

            app.add_middleware(SmitheryCompatibilityMiddleware)
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["mcp-session-id", "mcp-protocol-version"],
                max_age=86400,
            )
            uvicorn.run(app, host=host, port=port)

        elif transport == "sse":
            logger.info(f"Starting SSE transport on {host}:{port}")
            import asyncio

            asyncio.run(mcp.run_async("sse", host=host, port=port))
        else:
            logger.info("Starting STDIO transport")
            mcp.run("stdio")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()
