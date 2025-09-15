"""Enhanced MCP tools for all Korean government procurement APIs (FastMCP 2.0)."""

import logging
import sys
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.enhanced_client import enhanced_api_client
from ..core.config import SERVER_VERSION
from .base import BaseTool

logger = logging.getLogger("naramarket.enhanced_tools")

# 컨텍스트 보호 설정
MAX_RESPONSE_SIZE_CHARS = 50000  # 최대 응답 크기 (문자 수)
MAX_ITEMS_DEFAULT = 5  # 기본 아이템 수 제한
SUMMARY_FIELDS_LIMIT = 10  # 요약 시 최대 필드 수


class EnhancedProcurementTools(BaseTool):
    """Enhanced MCP tools for Korean government procurement APIs with parameterized operations."""

    def __init__(self):
        super().__init__()
        self.client = enhanced_api_client

    def _get_response_size(self, data: Any) -> int:
        """응답 데이터의 크기(문자 수)를 계산합니다."""
        try:
            import json
            return len(json.dumps(data, ensure_ascii=False))
        except:
            return len(str(data))

    def _extract_key_fields(self, item: Dict[str, Any], service_type: str) -> Dict[str, Any]:
        """서비스 타입별 핵심 필드만 추출합니다."""
        key_fields_map = {
            "public_data_standard": [
                "bidNtceNo", "bidNtceNm", "ntceKindNm", "bidNtceDt", "bidClseDt",
                "opengDt", "bidBeginDt", "bidEndDt", "cmmnSpldmdAgrmntRcptdtEndDt",
                "cntrctCnclsDate", "cntrctamt", "sucsfbidAmt", "presmptPrce"
            ],
            "procurement_statistics": [
                "bssMnth", "statDivNm", "bssYearAmt", "dminsttNm", "entrprsNm",
                "cntrctMthdNm", "bsnsObjNm", "prdctClsfcNm"
            ],
            "product_list": [
                "prdctClsfcNo", "prdctClsfcNoNm", "prdctIdntNo", "dtilPrdctClsfcNo",
                "mnfctCorpNm", "rgnNm", "chgDt"
            ],
            "shopping_mall": [
                "prdctIdntNo", "prdctClsfcNoNm", "cntrctCorpNm", "cntrctUntprc",
                "rgstDt", "chgDt", "dlvrReqNo", "dminsttNm", "prcrmntDiv"
            ]
        }

        key_fields = key_fields_map.get(service_type, [])
        if not key_fields:
            # 알려진 서비스가 아닌 경우 처음 10개 필드만 반환
            return dict(list(item.items())[:SUMMARY_FIELDS_LIMIT])

        # 핵심 필드만 추출
        summary = {}
        for field in key_fields:
            if field in item:
                summary[field] = item[field]

        # 핵심 필드가 부족한 경우 추가 필드 보충
        if len(summary) < 5:
            remaining_fields = [k for k in item.keys() if k not in summary][:5-len(summary)]
            for field in remaining_fields:
                summary[field] = item[field]

        return summary

    def _summarize_items(self, items: list, service_type: str, max_items: int = MAX_ITEMS_DEFAULT) -> Dict[str, Any]:
        """아이템 목록을 요약합니다."""
        if not items:
            return {"items": [], "total_items": 0, "summary": "데이터 없음"}

        total_items = len(items)

        # 아이템 수 제한
        limited_items = items[:max_items]

        # 각 아이템의 핵심 필드만 추출
        summarized_items = []
        for item in limited_items:
            if isinstance(item, dict):
                summarized_items.append(self._extract_key_fields(item, service_type))
            else:
                summarized_items.append(item)

        return {
            "items": summarized_items,
            "total_items": total_items,
            "showing_items": len(summarized_items),
            "summary": f"총 {total_items}개 중 {len(summarized_items)}개 항목 표시 (핵심 필드만)"
        }

    def _protect_context_response(self, result: Dict[str, Any], service_type: str, operation: str) -> Dict[str, Any]:
        """컨텍스트 윈도우 보호를 위해 응답 데이터를 압축합니다."""
        if not result or not isinstance(result, dict):
            return result

        # 응답 크기 확인
        response_size = self._get_response_size(result)

        # 크기가 제한을 초과하지 않으면 그대로 반환
        if response_size <= MAX_RESPONSE_SIZE_CHARS:
            return result

        logger.warning(f"Response size ({response_size} chars) exceeds limit. Applying context protection.")

        # 응답 구조 분석 및 압축
        protected_result = result.copy()

        # body.items 배열이 있는 경우 압축
        if "response" in result and "body" in result["response"]:
            body = result["response"]["body"]
            if "items" in body and isinstance(body["items"], list):
                # 아이템 요약
                summarized = self._summarize_items(body["items"], service_type)
                protected_result["response"]["body"]["items"] = summarized["items"]
                protected_result["response"]["body"]["context_protection"] = {
                    "applied": True,
                    "original_size_chars": response_size,
                    "compression_summary": summarized["summary"],
                    "total_items": summarized["total_items"],
                    "showing_items": summarized["showing_items"]
                }

        # 최종 크기 재확인
        final_size = self._get_response_size(protected_result)
        if final_size > MAX_RESPONSE_SIZE_CHARS:
            # 더 강력한 압축 필요
            logger.warning(f"Still too large ({final_size} chars). Applying stronger compression.")

            # 메타데이터만 반환
            return {
                "success": True,
                "service": f"서비스타입: {service_type}",
                "operation": operation,
                "context_protection": {
                    "applied": True,
                    "reason": "응답 데이터가 너무 큼",
                    "original_size_chars": response_size,
                    "final_size_chars": final_size,
                    "data_available": "데이터가 존재하지만 크기 제한으로 인해 요약됨"
                },
                "summary": "응답 데이터가 컨텍스트 윈도우를 초과하여 메타데이터만 반환됨",
                "recommendation": "더 작은 페이지 크기(numOfRows)나 더 구체적인 검색 조건을 사용하세요"
            }

        return protected_result

    def _create_pagination_info(self, result: Dict[str, Any], service_type: str, operation: str, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """페이징 정보와 다음 요청 가이드를 생성합니다."""
        try:
            # API 응답에서 페이징 정보 추출
            body = result.get("response", {}).get("body", {})
            total_count = body.get("totalCount", 0)
            current_page = current_params.get("pageNo", 1)
            num_rows = current_params.get("numOfRows", 5)

            total_pages = (total_count + num_rows - 1) // num_rows if total_count > 0 else 1
            has_next = current_page < total_pages

            pagination_info = {
                "current_page": current_page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": num_rows,
                "has_next_page": has_next,
                "next_page": current_page + 1 if has_next else None
            }

            # 다음 요청을 위한 파라미터 제안
            if has_next:
                next_params = current_params.copy()
                next_params["pageNo"] = current_page + 1

                pagination_info["next_request_example"] = {
                    "service_type": service_type,
                    "operation": operation,
                    "suggested_params": next_params
                }

            return pagination_info

        except Exception as e:
            logger.error(f"Failed to create pagination info: {e}")
            return {
                "error": "페이징 정보 생성 실패",
                "current_page": current_params.get("pageNo", 1)
            }

    def call_api_with_pagination_guidance(
        self,
        service_type: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """API 호출 후 페이징 안내와 함께 컨텍스트 보호된 응답을 제공합니다."""
        try:
            result = self.client.call_api(service_type, operation, params)

            # 컨텍스트 보호 적용
            protected_result = self._protect_context_response(result, service_type, operation)

            # 페이징 정보 생성
            pagination_info = self._create_pagination_info(result, service_type, operation, params)

            return {
                "success": True,
                "service": service_type,
                "operation": operation,
                "data": protected_result,
                "pagination": pagination_info,
                "params_used": params,
                "remote_server_note": "리모트 서버 환경에서는 전체 데이터 접근을 위해 페이징을 사용하세요"
            }

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {
                "success": False,
                "service": service_type,
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def call_public_data_standard_api(
        self,
        operation: str,
        numOfRows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
        pageNo: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """공공데이터개방표준서비스 API 호출.

        Available operations:
        - getDataSetOpnStdBidPblancInfo: 입찰공고정보 조회
        - getDataSetOpnStdScsbidInfo: 낙찰정보 조회
        - getDataSetOpnStdCntrctInfo: 계약정보 조회

        Args:
            operation: API 오퍼레이션명
            numOfRows: 한 페이지 결과 수 (기본값: 10)
            pageNo: 페이지 번호 (기본값: 1)
            **kwargs: 각 오퍼레이션별 추가 파라미터
                - bidNtceBgnDt/bidNtceEndDt: 입찰공고일시 범위 (YYYYMMDDHHMM)
                - bsnsDivCd: 업무구분코드 (1:물품, 2:외자, 3:공사, 5:용역)
                - opengBgnDt/opengEndDt: 개찰일시 범위 (YYYYMMDDHHMM)
                - cntrctCnclsBgnDate/cntrctCnclsEndDate: 계약체결일자 범위 (YYYYMMDD)
                - insttDivCd: 기관구분코드 (1:계약기관, 2:수요기관)
                - insttCd: 기관코드

        Returns:
            API 응답 데이터
        """
        try:
            params = {
                "numOfRows": numOfRows,
                "pageNo": pageNo,
                **kwargs
            }

            result = self.client.call_api("public_data_standard", operation, params)

            # 컨텍스트 보호 적용
            protected_result = self._protect_context_response(result, "public_data_standard", operation)

            return {
                "success": True,
                "service": "공공데이터개방표준서비스",
                "operation": operation,
                "data": protected_result,
                "params_used": params
            }

        except Exception as e:
            logger.error(f"Public data standard API call failed: {e}")
            return {
                "success": False,
                "service": "공공데이터개방표준서비스",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def call_procurement_statistics_api(
        self,
        operation: str,
        numOfRows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
        pageNo: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """공공조달통계정보서비스 API 호출.

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
            numOfRows: 한 페이지 결과 수 (기본값: 10)
            pageNo: 페이지 번호 (기본값: 1)
            **kwargs: 각 오퍼레이션별 추가 파라미터
                - srchBssYear: 검색기준년도 (YYYY)
                - srchBssYmBgn/srchBssYmEnd: 기준년월 범위 (YYYYMM)
                - dminsttCd/dminsttNm: 수요기관코드/명
                - corpUntyNo/corpNm: 업체통합번호/명
                - prdctClsfcNo/prdctClsfcNm: 물품분류번호/명
                - lwrInsttArsltInclsnYn: 하위기관실적포함여부
                - linkSystmCd: 연계시스템코드

        Returns:
            API 응답 데이터
        """
        try:
            params = {
                "numOfRows": numOfRows,
                "pageNo": pageNo,
                **kwargs
            }

            result = self.client.call_api("procurement_statistics", operation, params)

            # 컨텍스트 보호 적용
            protected_result = self._protect_context_response(result, "procurement_statistics", operation)

            return {
                "success": True,
                "service": "공공조달통계정보서비스",
                "operation": operation,
                "data": protected_result,
                "params_used": params
            }

        except Exception as e:
            logger.error(f"Procurement statistics API call failed: {e}")
            return {
                "success": False,
                "service": "공공조달통계정보서비스",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def call_product_list_api(
        self,
        operation: str,
        numOfRows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
        pageNo: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """조달청 물품목록정보서비스 API 호출.

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
            numOfRows: 한 페이지 결과 수 (기본값: 10)
            pageNo: 페이지 번호 (기본값: 1)
            **kwargs: 각 오퍼레이션별 추가 파라미터
                - upPrdctClsfcNo: 상위 물품분류번호
                - prdctClsfcNo: 물품분류번호
                - prdctIdntNo: 물품식별번호
                - dtilPrdctClsfcNo: 세부품명번호
                - prdctClsfcNoNm/prdctClsfcNoEngNm: 품명/영문품명
                - krnPrdctNm: 한글품목명
                - mnfctCorpNm: 제조업체명
                - rgnCd: 지역코드
                - inqryDiv: 조회구분
                - inqryBgnDt/inqryEndDt: 조회일시 범위 (YYYYMMDDHHMM)
                - chgPrdBgnDt/chgPrdEndDt: 변경기간 범위 (YYYYMMDD)

        Returns:
            API 응답 데이터
        """
        try:
            params = {
                "numOfRows": numOfRows,
                "pageNo": pageNo,
                **kwargs
            }

            result = self.client.call_api("product_list", operation, params)

            # 컨텍스트 보호 적용
            protected_result = self._protect_context_response(result, "product_list", operation)

            return {
                "success": True,
                "service": "조달청 물품목록정보서비스",
                "operation": operation,
                "data": protected_result,
                "params_used": params
            }

        except Exception as e:
            logger.error(f"Product list API call failed: {e}")
            return {
                "success": False,
                "service": "조달청 물품목록정보서비스",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def call_shopping_mall_api(
        self,
        operation: str,
        numOfRows: int = 5,  # 컨텍스트 보호를 위해 기본값 감소
        pageNo: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """나라장터 종합쇼핑몰 품목정보 서비스 API 호출.

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
            numOfRows: 한 페이지 결과 수 (기본값: 10)
            pageNo: 페이지 번호 (기본값: 1)
            **kwargs: 각 오퍼레이션별 추가 파라미터
                - rgstDtBgnDt/rgstDtEndDt: 등록일시 범위 (YYYYMMDDHH24M)
                - chgDtBgnDt/chgDtEndDt: 변경일시 범위 (YYYYMMDDHH24M)
                - prdctClsfcNoNm: 품명
                - prdctIdntNo: 물품식별번호
                - cntrctCorpNm: 계약업체명
                - prodctCertYn: 제품인증여부
                - inqryDiv: 조회구분
                - inqryBgnDate/inqryEndDate: 조회일자 범위 (YYYYMMDD)
                - dtilPrdctClsfcNoNm: 세부분류품명
                - prdctIdntNoNm: 품목명(식별명)
                - exclcProdctYn: 우수제품여부
                - masYn: 다수공급경쟁자여부
                - shopngCntrctNo: 쇼핑계약번호
                - regtCncelYn: 등록해지상품포함여부
                - dminsttNm: 수요기관명
                - dminsttRgnNm: 수요기관관할지역명
                - dlvrReqNo: 납품요구번호
                - inqryPrdctDiv: 조회상품구분
                - prcrmntDiv: 조달방식구분

        Returns:
            API 응답 데이터
        """
        try:
            params = {
                "numOfRows": numOfRows,
                "pageNo": pageNo,
                **kwargs
            }

            result = self.client.call_api("shopping_mall", operation, params)

            # 컨텍스트 보호 적용
            protected_result = self._protect_context_response(result, "shopping_mall", operation)

            return {
                "success": True,
                "service": "나라장터 종합쇼핑몰 품목정보 서비스",
                "operation": operation,
                "data": protected_result,
                "params_used": params
            }

        except Exception as e:
            logger.error(f"Shopping mall API call failed: {e}")
            return {
                "success": False,
                "service": "나라장터 종합쇼핑몰 품목정보 서비스",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_all_api_services_info(self) -> Dict[str, Any]:
        """모든 API 서비스 정보 조회.

        Returns:
            전체 서비스 및 오퍼레이션 정보
        """
        try:
            services_info = self.client.get_all_services_info()

            return {
                "success": True,
                "server_version": SERVER_VERSION,
                "enhanced_tools_enabled": True,
                **services_info,
                "description": "Enhanced Korean Government Procurement APIs with parameterized operations"
            }

        except Exception as e:
            logger.error(f"Failed to get services info: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_api_operations(self, service_type: str) -> Dict[str, Any]:
        """특정 서비스의 사용 가능한 오퍼레이션 목록 조회.

        Args:
            service_type: 서비스 타입 (public_data_standard, procurement_statistics, product_list, shopping_mall)

        Returns:
            서비스별 오퍼레이션 목록
        """
        try:
            operations_info = self.client.get_available_operations(service_type)

            return {
                "success": True,
                **operations_info
            }

        except Exception as e:
            logger.error(f"Failed to get operations for {service_type}: {e}")
            return {
                "success": False,
                "service_type": service_type,
                "error": str(e),
                "error_type": type(e).__name__
            }


# Global enhanced tools instance
enhanced_tools = EnhancedProcurementTools()