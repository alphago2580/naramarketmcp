"""나라장터 검색조건 기반 API 도구들 (수동 구현)."""

import logging
import httpx
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from ..core.config import get_service_key

logger = logging.getLogger("naramarket.search_apis")


class NaraMarketSearchAPIs:
    """나라장터 검색조건 기반 API 클라이언트."""

    def __init__(self):
        self.service_key = get_service_key()
        self.base_url = "http://apis.data.go.kr/1230000"
        self.timeout = 30.0

    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """공통 HTTP 요청 처리."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()

                result = response.json()

                # API 응답 구조 확인
                if "response" in result:
                    header = result["response"].get("header", {})
                    body = result["response"].get("body", {})

                    return {
                        "resultCode": header.get("resultCode"),
                        "resultMsg": header.get("resultMsg"),
                        "numOfRows": body.get("numOfRows"),
                        "pageNo": body.get("pageNo"),
                        "totalCount": body.get("totalCount"),
                        "items": body.get("items", [])
                    }
                else:
                    return result

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    # ===================
    # 입찰공고서비스 (3개)
    # ===================

    def get_bid_announcement_construction(
        self,
        inqry_div: str = "1",
        inqry_bgn_dt: Optional[str] = None,
        inqry_end_dt: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        bid_ntce_nm: Optional[str] = None,
        ntce_instt_cd: Optional[str] = None,
        ntce_instt_nm: Optional[str] = None,
        dminst_cd: Optional[str] = None,
        dminst_nm: Optional[str] = None,
        ref_no: Optional[str] = None,
        prtcpt_lmt_rgn_cd: Optional[str] = None,
        prtcpt_lmt_rgn_nm: Optional[str] = None,
        indstryty_cd: Optional[str] = None,
        indstryty_nm: Optional[str] = None,
        presmpt_prce_bgn: Optional[int] = None,
        presmpt_prce_end: Optional[int] = None,
        prcrmnt_req_no: Optional[str] = None,
        bid_clse_excp_yn: Optional[str] = None,
        intrntnl_div_cd: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 입찰공고공사조회."""

        url = f"{self.base_url}/ad/BidPublicInfoService/getBidPblancListInfoCnstwkPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "inqryDiv": inqry_div,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "type": "json"
        }

        # 선택적 파라미터 추가
        optional_params = {
            "inqryBgnDt": inqry_bgn_dt,
            "inqryEndDt": inqry_end_dt,
            "bidNtceNm": bid_ntce_nm,
            "ntceInsttCd": ntce_instt_cd,
            "ntceInsttNm": ntce_instt_nm,
            "dminsttCd": dminst_cd,
            "dminsttNm": dminst_nm,
            "refNo": ref_no,
            "prtcptLmtRgnCd": prtcpt_lmt_rgn_cd,
            "prtcptLmtRgnNm": prtcpt_lmt_rgn_nm,
            "indstrytyCd": indstryty_cd,
            "indstrytyNm": indstryty_nm,
            "presmptPrceBgn": presmpt_prce_bgn,
            "presmptPrceEnd": presmpt_prce_end,
            "prcrmntReqNo": prcrmnt_req_no,
            "bidClseExcpYn": bid_clse_excp_yn,
            "intrntnlDivCd": intrntnl_div_cd
        }

        # None이 아닌 값만 파라미터에 추가
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_bid_announcement_service(
        self,
        inqry_div: str = "1",
        inqry_bgn_dt: Optional[str] = None,
        inqry_end_dt: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        bid_ntce_nm: Optional[str] = None,
        ntce_instt_cd: Optional[str] = None,
        ntce_instt_nm: Optional[str] = None,
        dminst_cd: Optional[str] = None,
        dminst_nm: Optional[str] = None,
        ref_no: Optional[str] = None,
        prtcpt_lmt_rgn_cd: Optional[str] = None,
        prtcpt_lmt_rgn_nm: Optional[str] = None,
        indstryty_cd: Optional[str] = None,
        indstryty_nm: Optional[str] = None,
        presmpt_prce_bgn: Optional[int] = None,
        presmpt_prce_end: Optional[int] = None,
        prcrmnt_req_no: Optional[str] = None,
        bid_clse_excp_yn: Optional[str] = None,
        intrntnl_div_cd: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 입찰공고용역조회."""

        url = f"{self.base_url}/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "inqryDiv": inqry_div,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "type": "json"
        }

        # 선택적 파라미터 추가 (용역은 masYn 파라미터 제외)
        optional_params = {
            "inqryBgnDt": inqry_bgn_dt,
            "inqryEndDt": inqry_end_dt,
            "bidNtceNm": bid_ntce_nm,
            "ntceInsttCd": ntce_instt_cd,
            "ntceInsttNm": ntce_instt_nm,
            "dminsttCd": dminst_cd,
            "dminsttNm": dminst_nm,
            "refNo": ref_no,
            "prtcptLmtRgnCd": prtcpt_lmt_rgn_cd,
            "prtcptLmtRgnNm": prtcpt_lmt_rgn_nm,
            "indstrytyCd": indstryty_cd,
            "indstrytyNm": indstryty_nm,
            "presmptPrceBgn": presmpt_prce_bgn,
            "presmptPrceEnd": presmpt_prce_end,
            "prcrmntReqNo": prcrmnt_req_no,
            "bidClseExcpYn": bid_clse_excp_yn,
            "intrntnlDivCd": intrntnl_div_cd
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_bid_announcement_goods(
        self,
        inqry_div: str = "1",
        inqry_bgn_dt: Optional[str] = None,
        inqry_end_dt: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        bid_ntce_nm: Optional[str] = None,
        ntce_instt_cd: Optional[str] = None,
        ntce_instt_nm: Optional[str] = None,
        dminst_cd: Optional[str] = None,
        dminst_nm: Optional[str] = None,
        ref_no: Optional[str] = None,
        prtcpt_lmt_rgn_cd: Optional[str] = None,
        prtcpt_lmt_rgn_nm: Optional[str] = None,
        indstryty_cd: Optional[str] = None,
        indstryty_nm: Optional[str] = None,
        presmpt_prce_bgn: Optional[int] = None,
        presmpt_prce_end: Optional[int] = None,
        dtil_prdct_clsfc_no: Optional[str] = None,
        mas_yn: Optional[str] = None,
        prcrmnt_req_no: Optional[str] = None,
        bid_clse_excp_yn: Optional[str] = None,
        intrntnl_div_cd: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 입찰공고물품조회."""

        url = f"{self.base_url}/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "inqryDiv": inqry_div,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "type": "json"
        }

        optional_params = {
            "inqryBgnDt": inqry_bgn_dt,
            "inqryEndDt": inqry_end_dt,
            "bidNtceNm": bid_ntce_nm,
            "ntceInsttCd": ntce_instt_cd,
            "ntceInsttNm": ntce_instt_nm,
            "dminsttCd": dminst_cd,
            "dminsttNm": dminst_nm,
            "refNo": ref_no,
            "prtcptLmtRgnCd": prtcpt_lmt_rgn_cd,
            "prtcptLmtRgnNm": prtcpt_lmt_rgn_nm,
            "indstrytyCd": indstryty_cd,
            "indstrytyNm": indstryty_nm,
            "presmptPrceBgn": presmpt_prce_bgn,
            "presmptPrceEnd": presmpt_prce_end,
            "dtilPrdctClsfcNo": dtil_prdct_clsfc_no,
            "masYn": mas_yn,
            "prcrmntReqNo": prcrmnt_req_no,
            "bidClseExcpYn": bid_clse_excp_yn,
            "intrntnlDivCd": intrntnl_div_cd
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    # ===================
    # 낙찰정보서비스 (3개)
    # ===================

    def get_successful_bid_list_goods(
        self,
        inqry_div: str,
        inqry_bgn_dt: Optional[str] = None,
        inqry_end_dt: Optional[str] = None,
        bid_ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        bid_ntce_nm: Optional[str] = None,
        ntce_instt_cd: Optional[str] = None,
        ntce_instt_nm: Optional[str] = None,
        dminst_cd: Optional[str] = None,
        dminst_nm: Optional[str] = None,
        ref_no: Optional[str] = None,
        prtcpt_lmt_rgn_cd: Optional[str] = None,
        prtcpt_lmt_rgn_nm: Optional[str] = None,
        indstryty_cd: Optional[str] = None,
        indstryty_nm: Optional[str] = None,
        presmpt_prce_bgn: Optional[int] = None,
        presmpt_prce_end: Optional[int] = None,
        dtil_prdct_clsfc_no: Optional[str] = None,
        mltspły_cmpt_yn: Optional[str] = None,
        prcrmnt_req_no: Optional[str] = None,
        intrntnl_div_cd: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터 검색조건에 의한 낙찰된 목록 현황 물품조회."""

        # 조건부 필수 파라미터 검증
        if inqry_div in ["1", "2"]:
            if not inqry_bgn_dt or not inqry_end_dt:
                return {"error": "조회구분이 1 또는 2일 때는 조회시작일시와 조회종료일시가 필수입니다."}
        elif inqry_div == "3":
            if not bid_ntce_no:
                return {"error": "조회구분이 3일 때는 입찰공고번호가 필수입니다."}

        url = f"{self.base_url}/as/ScsbidInfoService/getScsbidListSttusThngPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "type": "json",
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div
        }

        # 선택적 파라미터 추가
        optional_params = {
            "inqryBgnDt": inqry_bgn_dt,
            "inqryEndDt": inqry_end_dt,
            "bidNtceNo": bid_ntce_no,
            "bidNtceNm": bid_ntce_nm,
            "ntceInsttCd": ntce_instt_cd,
            "ntceInsttNm": ntce_instt_nm,
            "dminsttCd": dminst_cd,
            "dminsttNm": dminst_nm,
            "refNo": ref_no,
            "prtcptLmtRgnCd": prtcpt_lmt_rgn_cd,
            "prtcptLmtRgnNm": prtcpt_lmt_rgn_nm,
            "indstrytyCd": indstryty_cd,
            "indstrytyNm": indstryty_nm,
            "presmptPrceBgn": presmpt_prce_bgn,
            "presmptPrceEnd": presmpt_prce_end,
            "dtilPrdctClsfcNo": dtil_prdct_clsfc_no,
            "mltsplyCmptYn": mltspły_cmpt_yn,
            "prcrmntReqNo": prcrmnt_req_no,
            "intrntnlDivCd": intrntnl_div_cd
        }

        # None이 아닌 값만 추가
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_successful_bid_list_construction(
        self,
        inqry_div: str,
        inqry_bgn_dt: Optional[str] = None,
        inqry_end_dt: Optional[str] = None,
        bid_ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        bid_ntce_nm: Optional[str] = None,
        ntce_instt_cd: Optional[str] = None,
        ntce_instt_nm: Optional[str] = None,
        dminst_cd: Optional[str] = None,
        dminst_nm: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터 검색조건에 의한 낙찰된 목록 현황 공사조회."""

        # 동일한 검증 로직
        if inqry_div in ["1", "2"]:
            if not inqry_bgn_dt or not inqry_end_dt:
                return {"error": "조회구분이 1 또는 2일 때는 조회시작일시와 조회종료일시가 필수입니다."}
        elif inqry_div == "3":
            if not bid_ntce_no:
                return {"error": "조회구분이 3일 때는 입찰공고번호가 필수입니다."}

        url = f"{self.base_url}/as/ScsbidInfoService/getScsbidListSttusCnstwkPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "type": "json",
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div
        }

        optional_params = {
            "inqryBgnDt": inqry_bgn_dt,
            "inqryEndDt": inqry_end_dt,
            "bidNtceNo": bid_ntce_no,
            "bidNtceNm": bid_ntce_nm,
            "ntceInsttCd": ntce_instt_cd,
            "ntceInsttNm": ntce_instt_nm,
            "dminsttCd": dminst_cd,
            "dminsttNm": dminst_nm
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_successful_bid_list_service(
        self,
        inqry_div: str,
        inqry_bgn_dt: Optional[str] = None,
        inqry_end_dt: Optional[str] = None,
        bid_ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        bid_ntce_nm: Optional[str] = None,
        ntce_instt_cd: Optional[str] = None,
        ntce_instt_nm: Optional[str] = None,
        dminst_cd: Optional[str] = None,
        dminst_nm: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터 검색조건에 의한 낙찰된 목록 현황 용역조회."""

        # 동일한 검증 로직
        if inqry_div in ["1", "2"]:
            if not inqry_bgn_dt or not inqry_end_dt:
                return {"error": "조회구분이 1 또는 2일 때는 조회시작일시와 조회종료일시가 필수입니다."}
        elif inqry_div == "3":
            if not bid_ntce_no:
                return {"error": "조회구분이 3일 때는 입찰공고번호가 필수입니다."}

        url = f"{self.base_url}/as/ScsbidInfoService/getScsbidListSttusServcPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "type": "json",
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div
        }

        optional_params = {
            "inqryBgnDt": inqry_bgn_dt,
            "inqryEndDt": inqry_end_dt,
            "bidNtceNo": bid_ntce_no,
            "bidNtceNm": bid_ntce_nm,
            "ntceInsttCd": ntce_instt_cd,
            "ntceInsttNm": ntce_instt_nm,
            "dminsttCd": dminst_cd,
            "dminsttNm": dminst_nm
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    # ===================
    # 계약정보서비스 (4개)
    # ===================

    def get_contract_info_goods(
        self,
        inqry_div: str,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
        dcsn_cntrct_no: Optional[str] = None,
        req_no: Optional[str] = None,
        ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        instt_div_cd: Optional[str] = None,
        instt_clsfc_cd: Optional[str] = None,
        instt_cd: Optional[str] = None,
        instt_nm: Optional[str] = None,
        prdct_clsfc_no_nm: Optional[str] = None,
        cntrct_mthd_cd: Optional[str] = None,
        cntrct_ref_no: Optional[str] = None,
        cntrct_div_cd: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 계약현황 물품조회."""

        # 조건부 필수 파라미터 검증
        if inqry_div == "1" and (not inqry_bgn_date or not inqry_end_date):
            return {"error": "조회구분이 1일 때는 조회시작일자와 조회종료일자가 필수입니다."}
        elif inqry_div == "2" and not dcsn_cntrct_no:
            return {"error": "조회구분이 2일 때는 확정계약번호가 필수입니다."}
        elif inqry_div == "3" and not req_no:
            return {"error": "조회구분이 3일 때는 요청번호가 필수입니다."}
        elif inqry_div == "4" and not ntce_no:
            return {"error": "조회구분이 4일 때는 공고번호가 필수입니다."}

        url = f"{self.base_url}/ao/CntrctInfoService/getCntrctInfoListThngPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div,
            "type": "json"
        }

        optional_params = {
            "inqryBgnDate": inqry_bgn_date,
            "inqryEndDate": inqry_end_date,
            "dcsnCntrctNo": dcsn_cntrct_no,
            "reqNo": req_no,
            "ntceNo": ntce_no,
            "insttDivCd": instt_div_cd,
            "insttClsfcCd": instt_clsfc_cd,
            "insttCd": instt_cd,
            "insttNm": instt_nm,
            "prdctClsfcNoNm": prdct_clsfc_no_nm,
            "cntrctMthdCd": cntrct_mthd_cd,
            "cntrctRefNo": cntrct_ref_no,
            "cntrctDivCd": cntrct_div_cd
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_contract_info_construction(
        self,
        inqry_div: str,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
        dcsn_cntrct_no: Optional[str] = None,
        req_no: Optional[str] = None,
        ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        cnstty_nm: Optional[str] = None,
        cnstwk_nm: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 계약현황 공사조회."""

        # 동일한 검증 로직
        if inqry_div == "1" and (not inqry_bgn_date or not inqry_end_date):
            return {"error": "조회구분이 1일 때는 조회시작일자와 조회종료일자가 필수입니다."}
        elif inqry_div == "2" and not dcsn_cntrct_no:
            return {"error": "조회구분이 2일 때는 확정계약번호가 필수입니다."}
        elif inqry_div == "3" and not req_no:
            return {"error": "조회구분이 3일 때는 요청번호가 필수입니다."}
        elif inqry_div == "4" and not ntce_no:
            return {"error": "조회구분이 4일 때는 공고번호가 필수입니다."}

        url = f"{self.base_url}/ao/CntrctInfoService/getCntrctInfoListCnstwkPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div,
            "type": "json"
        }

        optional_params = {
            "inqryBgnDate": inqry_bgn_date,
            "inqryEndDate": inqry_end_date,
            "dcsnCntrctNo": dcsn_cntrct_no,
            "reqNo": req_no,
            "ntceNo": ntce_no,
            "cnsttyNm": cnstty_nm,
            "cnstwkNm": cnstwk_nm
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_contract_info_service(
        self,
        inqry_div: str,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
        dcsn_cntrct_no: Optional[str] = None,
        req_no: Optional[str] = None,
        ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        cnstty_nm: Optional[str] = None,
        cntrct_nm: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 계약현황 용역조회."""

        # 동일한 검증 로직
        if inqry_div == "1" and (not inqry_bgn_date or not inqry_end_date):
            return {"error": "조회구분이 1일 때는 조회시작일자와 조회종료일자가 필수입니다."}
        elif inqry_div == "2" and not dcsn_cntrct_no:
            return {"error": "조회구분이 2일 때는 확정계약번호가 필수입니다."}
        elif inqry_div == "3" and not req_no:
            return {"error": "조회구분이 3일 때는 요청번호가 필수입니다."}
        elif inqry_div == "4" and not ntce_no:
            return {"error": "조회구분이 4일 때는 공고번호가 필수입니다."}

        url = f"{self.base_url}/ao/CntrctInfoService/getCntrctInfoListServcPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div,
            "type": "json"
        }

        optional_params = {
            "inqryBgnDate": inqry_bgn_date,
            "inqryEndDate": inqry_end_date,
            "dcsnCntrctNo": dcsn_cntrct_no,
            "reqNo": req_no,
            "ntceNo": ntce_no,
            "cnsttyNm": cnstty_nm,
            "cntrctNm": cntrct_nm
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    def get_contract_info_foreign(
        self,
        inqry_div: str,
        inqry_bgn_date: Optional[str] = None,
        inqry_end_date: Optional[str] = None,
        dcsn_cntrct_no: Optional[str] = None,
        req_no: Optional[str] = None,
        ntce_no: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
        prdct_clsfc_no_nm: Optional[str] = None,
        sply_corp_nm: Optional[str] = None,
        make_corp_nm: Optional[str] = None
    ) -> Dict[str, Any]:
        """나라장터검색조건에 의한 계약현황 외자조회."""

        # 동일한 검증 로직
        if inqry_div == "1" and (not inqry_bgn_date or not inqry_end_date):
            return {"error": "조회구분이 1일 때는 조회시작일자와 조회종료일자가 필수입니다."}
        elif inqry_div == "2" and not dcsn_cntrct_no:
            return {"error": "조회구분이 2일 때는 확정계약번호가 필수입니다."}
        elif inqry_div == "3" and not req_no:
            return {"error": "조회구분이 3일 때는 요청번호가 필수입니다."}
        elif inqry_div == "4" and not ntce_no:
            return {"error": "조회구분이 4일 때는 공고번호가 필수입니다."}

        url = f"{self.base_url}/ao/CntrctInfoService/getCntrctInfoListFrgcptPPSSrch"

        params = {
            "ServiceKey": self.service_key,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": inqry_div,
            "type": "json"
        }

        optional_params = {
            "inqryBgnDate": inqry_bgn_date,
            "inqryEndDate": inqry_end_date,
            "dcsnCntrctNo": dcsn_cntrct_no,
            "reqNo": req_no,
            "ntceNo": ntce_no,
            "prdctClsfcNoNm": prdct_clsfc_no_nm,
            "splyCorpNm": sply_corp_nm,
            "makeCorpNm": make_corp_nm
        }

        for key, value in optional_params.items():
            if value is not None:
                params[key] = value

        return self._make_request(url, params)

    # ===================
    # 유틸리티 메서드
    # ===================

    def get_region_codes(self) -> Dict[str, str]:
        """참가제한지역코드 목록 조회."""
        return {
            "11": "서울특별시", "26": "부산광역시", "27": "대구광역시", "28": "인천광역시",
            "29": "광주광역시", "30": "대전광역시", "31": "울산광역시", "36": "세종특별자치시",
            "41": "경기도", "42": "강원도", "43": "충청북도", "44": "충청남도",
            "45": "전라북도", "46": "전라남도", "47": "경상북도", "48": "경상남도",
            "50": "제주도", "51": "강원특별자치도", "52": "전북특별자치도", "99": "기타"
        }

    def format_date_range(self, days_back: int = 7) -> tuple[str, str]:
        """날짜 범위를 자동으로 계산합니다."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        return (
            start_date.strftime("%Y%m%d0000"),
            end_date.strftime("%Y%m%d2359")
        )


# 글로벌 인스턴스
naramarket_search_apis = NaraMarketSearchAPIs()