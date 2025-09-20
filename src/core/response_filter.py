"""API 응답 필터링 및 선택적 필드 반환을 위한 유틸리티."""

from typing import Any, Dict, List, Optional, Union


# 서비스별 핵심 필드 매핑
CORE_FIELDS_MAP = {
    "bid_announcement": {
        "minimal": ["bidNtceNo", "bidNtceNm", "ntceInsttNm"],
        "summary": ["bidNtceNo", "bidNtceNm", "ntceInsttNm", "bidNtceDt", "bidClseDt", "presmptPrce"],
        "key_fields": ["bidNtceNo", "bidNtceNm", "ntceInsttNm", "dminsttNm", "bidNtceDt",
                      "bidClseDt", "opengDt", "presmptPrce", "rgstDt", "bfSpecRgstNo"]
    },
    "successful_bid": {
        "minimal": ["bidNtceNo", "bidNtceNm", "sucsfbidCorpNm"],
        "summary": ["bidNtceNo", "bidNtceNm", "sucsfbidCorpNm", "cntrctCnclsAmt", "sucsfbidMthd"],
        "key_fields": ["bidNtceNo", "bidNtceNm", "ntceInsttNm", "dminsttNm", "sucsfbidCorpNm",
                      "cntrctCnclsAmt", "sucsfbidMthd", "cntrctCnclsDe", "presmptPrce"]
    },
    "contract_info": {
        "minimal": ["cntrctNo", "cntrctNm", "cntrctorCorpNm"],
        "summary": ["cntrctNo", "cntrctNm", "cntrctorCorpNm", "cntrctAmt", "cntrctCnclsDe"],
        "key_fields": ["cntrctNo", "cntrctNm", "cntrctorCorpNm", "cntrctAmt", "cntrctCnclsDe",
                      "dminsttNm", "cntrctMthd", "bidNtceNo", "rgstDt"]
    },
    "procurement_stats": {
        "minimal": ["baseYear", "totlPrcrmntAmt", "entryCount"],
        "summary": ["baseYear", "totlPrcrmntAmt", "entryCount", "instituteNm", "prcrmntDiv"],
        "key_fields": ["baseYear", "totlPrcrmntAmt", "entryCount", "instituteNm", "prcrmntDiv",
                      "cntrctMthd", "rgn", "industryNm"]
    },
    "product_list": {
        "minimal": ["prdctClsfcNo", "prdctClsfcNoNm", "prdctStdrNm"],
        "summary": ["prdctClsfcNo", "prdctClsfcNoNm", "prdctStdrNm", "prdctStdrUnit", "rgstDt"],
        "key_fields": ["prdctClsfcNo", "prdctClsfcNoNm", "prdctStdrNm", "prdctStdrUnit",
                      "rgstDt", "mdfcnDt", "delYn", "rmrk"]
    },
    "shopping_mall": {
        "minimal": ["prdctIdntNo", "prdctIdntNoNm", "cntrctCorpNm"],
        "summary": ["prdctIdntNo", "prdctIdntNoNm", "cntrctCorpNm", "dlvrPrce", "prdctClsfcNoNm"],
        "key_fields": ["prdctIdntNo", "prdctIdntNoNm", "cntrctCorpNm", "dlvrPrce", "prdctClsfcNoNm",
                      "rgstDt", "masYn", "exclcProdctYn", "regtCncelYn"]
    }
}


def filter_response_fields(
    response_data: Dict[str, Any],
    fields: Optional[List[str]] = None,
    response_format: str = "full",
    service_type: str = "bid_announcement"
) -> Dict[str, Any]:
    """API 응답에서 필요한 필드만 선택하여 반환.

    Args:
        response_data: 원본 API 응답 데이터
        fields: 선택할 특정 필드 리스트 (우선순위 높음)
        response_format: 응답 형태 ("full", "summary", "minimal", "key_fields")
        service_type: 서비스 타입 (기본값: "bid_announcement")

    Returns:
        필터링된 응답 데이터
    """
    if not response_data or response_format == "full":
        return response_data

    # response_data 구조 확인
    if "response" in response_data:
        response_body = response_data["response"]
        if "body" in response_body and "items" in response_body["body"]:
            items = response_body["body"]["items"]
        else:
            # items가 없는 경우 원본 반환
            return response_data
    else:
        # 다른 구조인 경우 원본 반환
        return response_data

    # 필드 선택 로직
    if fields:
        # 사용자 지정 필드가 있으면 우선 사용
        selected_fields = fields
    elif service_type in CORE_FIELDS_MAP and response_format in CORE_FIELDS_MAP[service_type]:
        # 프리셋 필드 사용
        selected_fields = CORE_FIELDS_MAP[service_type][response_format]
    else:
        # 해당하는 프리셋이 없으면 원본 반환
        return response_data

    # 아이템들을 필터링
    filtered_items = []
    for item in items:
        if isinstance(item, dict):
            filtered_item = {}
            for field in selected_fields:
                if field in item:
                    filtered_item[field] = item[field]
            filtered_items.append(filtered_item)
        else:
            # dict가 아닌 경우 원본 유지
            filtered_items.append(item)

    # 필터링된 응답 구성
    filtered_response = response_data.copy()
    filtered_response["response"]["body"]["items"] = filtered_items

    # 메타데이터 추가
    if "metadata" not in filtered_response:
        filtered_response["metadata"] = {}

    filtered_response["metadata"].update({
        "filtered": True,
        "response_format": response_format,
        "selected_fields": selected_fields,
        "original_item_count": len(items),
        "filtered_item_count": len(filtered_items),
        "fields_per_item": len(selected_fields) if selected_fields else 0
    })

    return filtered_response


def get_available_fields(service_type: str) -> Dict[str, Any]:
    """특정 서비스 타입에서 사용 가능한 필드 정보 반환.

    Args:
        service_type: 서비스 타입

    Returns:
        사용 가능한 필드 정보
    """
    if service_type not in CORE_FIELDS_MAP:
        return {
            "error": f"Unknown service_type: {service_type}",
            "available_types": list(CORE_FIELDS_MAP.keys())
        }

    return {
        "service_type": service_type,
        "response_formats": list(CORE_FIELDS_MAP[service_type].keys()),
        "field_details": CORE_FIELDS_MAP[service_type]
    }


def get_all_response_formats() -> Dict[str, Any]:
    """모든 서비스의 응답 형태 정보 반환."""
    return {
        "response_formats": {
            "full": "전체 응답 (원본 그대로)",
            "key_fields": "핵심 필드만 (분석용 최적화)",
            "summary": "요약 정보 (주요 식별자 + 핵심 값)",
            "minimal": "최소 정보 (기본 식별자만)"
        },
        "services": {
            service_type: {
                "available_formats": list(fields.keys()),
                "field_counts": {
                    format_name: len(field_list)
                    for format_name, field_list in fields.items()
                }
            }
            for service_type, fields in CORE_FIELDS_MAP.items()
        }
    }


# 컨텍스트 보호를 위한 응답 크기 체크
def check_response_size(response_data: Dict[str, Any], max_size: int = 50000) -> Dict[str, Any]:
    """응답 크기를 체크하고 필요시 자동 압축 제안.

    Args:
        response_data: 응답 데이터
        max_size: 최대 허용 크기 (문자 수)

    Returns:
        크기 체크 결과 및 권장사항
    """
    response_str = str(response_data)
    current_size = len(response_str)

    result = {
        "current_size": current_size,
        "max_size": max_size,
        "size_ok": current_size <= max_size,
        "compression_needed": current_size > max_size
    }

    if result["compression_needed"]:
        result["recommendations"] = [
            "응답 크기가 큽니다. 다음 방법을 고려해보세요:",
            f"1. response_format='summary' 또는 'minimal' 사용",
            f"2. num_rows를 줄여서 페이징 처리",
            f"3. 특정 fields 파라미터로 필요한 필드만 선택",
            f"현재 크기: {current_size:,}자, 권장 크기: {max_size:,}자 이하"
        ]

    return result