"""MCP 프롬프트 및 리소스 텍스트 정의.

main.py에서 등록되는 MCP 프롬프트/리소스의 가이드 텍스트를 모아둔 모듈입니다.
"""

WORKFLOW_GUIDE = """
# 정부조달 데이터 분석 워크플로우 가이드

## 1. 기본 데이터 탐색

### 입찰공고 현황 파악
- **도구**: `get_recent_bid_announcements(days_back=7)`
- **활용**: 시장 트렌드, 입찰 빈도 분석

### 낙찰결과 분석
- **도구**: `get_successful_bids_by_business_type(business_type="물품")`
- **활용**: 가격 범위, 선정 기준 분석

## 2. 심화 분석

### 통계 기반 시장 분석
- **도구**: `get_procurement_statistics_by_year(year="2024")`
- **활용**: 연도별 시장 규모 변화, 성장률

### 쇼핑몰 제품 검색
- **도구**: `search_shopping_mall_products(product_name="컴퓨터")`
- **활용**: 품목별 가격 비교, MAS 계약 현황

## 3. 검색 전략

### 날짜 범위 최적화
- 최신 동향: 7-30일
- 트렌드 분석: 3-12개월
- 연도별 비교: 전체 연도 단위

### 컨텍스트 보호
- 기본 5개 결과로 제한 (자동)
- 페이징 가이드로 대량 데이터 탐색
- `call_api_with_pagination_support` 활용

## 4. 분석 시나리오

### A: 신규 시장 진입
1. 입찰공고 조회 → 2. 낙찰 현황 파악 → 3. 시장 규모 분석

### B: 제품 시장 모니터링
1. MAS 상품 현황 → 2. 가격 변동 추적 → 3. 계절성 패턴 파악

### C: 전략적 분석
1. 업무구분별 현황 → 2. 기관/지역별 특성 → 3. 기회/위험 식별
"""

PARAMETER_SELECTION_GUIDE = """
# API 파라미터 선택 가이드

## 필수 파라미터
- **operation**: API 오퍼레이션명 (각 서비스별 필수)
- **num_rows**: 결과 수 (기본 5-10 권장)
- **page_no**: 페이지 번호 (1부터)

## 업무구분코드
- `"1"`: 물품 | `"2"`: 외자 | `"3"`: 공사 | `"5"`: 용역

## 날짜 형식
- `YYYYMMDDHHMM`: 시분까지 (예: "202409151430")
- `YYYYMMDD`: 일자 (예: "20240915")
- `YYYY`: 연도 (통계 조회)

## 서비스별 권장 조합

### 입찰공고 조회
- operation + bid_notice_start/end_date + business_div_code

### 낙찰정보 조회
- operation + business_div_code + opening_start/end_date

### 조달통계
- operation + search_base_year

### 쇼핑몰 검색
- operation + product_name 또는 company_name

## 결과 최적화
- 초기 탐색: num_rows=5
- 상세 분석: num_rows=10-20
- 결과 없으면 조건 완화, 과다면 필터 강화
"""

API_PARAMETER_REQUIREMENTS = """
# 정부조달 API 파라미터 요구사항

## 공공데이터개방표준 (call_public_data_standard_api)

### 입찰공고 (getDataSetOpnStdBidPblancInfo)
- 강력 권장: bid_notice_start_date, bid_notice_end_date

### 낙찰정보 (getDataSetOpnStdScsbidInfo)
- 권장: business_div_code ("1"=물품, "2"=외자, "3"=공사, "5"=용역)
- 권장: opening_start_date, opening_end_date

### 계약정보 (getDataSetOpnStdCntrctInfo)
- 권장: contract_start_date, contract_end_date
- 선택: institution_div_code ("1"=계약기관, "2"=수요기관)

## 조달통계 (call_procurement_statistics_api)
- 14개 오퍼레이션 지원
- 강력 권장: search_base_year (YYYY)
- 선택: demand_institution_code, corp_unity_no

## 물품목록 (call_product_list_api)
- 12개 오퍼레이션 지원
- 권장: upper_product_classification_no (계층 조회)

## 종합쇼핑몰 (call_shopping_mall_api)
- 9개 오퍼레이션 지원
- 검색: product_classification_name, contract_corp_name

## 일반 원칙
1. 날짜: YYYYMMDDHHMM 또는 YYYYMMDD
2. 페이징: num_rows 5-10 권장
3. 빈 결과 → 조건 완화, 과다 → 필터 강화
"""

PARAMETER_VALUE_EXAMPLES = """
# API 파라미터 값 예시

## 코드값
- 업무구분: "1"(물품), "2"(외자), "3"(공사), "5"(용역)
- 기관구분: "1"(계약기관), "2"(수요기관)
- 조회구분: "1"(전체), "2"(신규), "3"(변경)

## 날짜 형식
- "202409151430": 2024-09-15 14:30 (YYYYMMDDHHMM)
- "20240915": 2024-09-15 (YYYYMMDD)
- "202409": 2024-09 (YYYYMM)
- "2024": 2024년 (YYYY)

## 검색어 예시
- 품명: "컴퓨터", "프린터", "소프트웨어", "의료기기"
- 업체: "삼성전자", "LG전자"
- 기관: "교육부", "국방부", "서울시"

## 물품분류번호
- "432": 컴퓨터 | "44": 사무용품 | "453": 의료기기

## 자주 쓰는 조합
- 최근 7일 입찰: start="202409080000", end="202409152359"
- 당해 통계: search_base_year="2024"
- 물품 낙찰: business_div_code="1" + 날짜 범위
"""

COMMON_SEARCH_PATTERNS = """
# 자주 사용되는 검색 패턴

## 시간 기반 검색
- 최근 공고: call_public_data_standard_api + 날짜 범위
- 연도별 통계: call_procurement_statistics_api + search_base_year

## 업종별 검색
- IT/컴퓨터: call_product_list_api로 분류 확인 → call_shopping_mall_api로 검색
- 공사: call_public_data_standard_api + business_div_code="3"

## 기업 분석
- 특정 기업: search_shopping_mall_products(company_name="...")
- 경쟁 분석: 동일 product_name으로 업체 비교

## 기관별 분석
- 기관 실적: call_procurement_statistics_api + demand_institution_name
- 지역 현황: operation="getRgnLmtSttus"

## 검색 전략
1. 넓은 범위 → 카테고리 필터링 → 세부 조건
2. 결과 없으면: 기간 확대, 검색어 단순화
3. 탐색 단계: num_rows=3~5 → 상세: 10~20
"""

REAL_WORLD_QUERY_EXAMPLES = """
# 실전 쿼리 예제

## 1. IT 장비 시장 진입
```python
# 최근 입찰공고 확인
get_recent_bid_announcements(days_back=30, num_rows=10)

# 낙찰 가격대 조사
get_successful_bids_by_business_type(business_type="물품", days_back=90)

# 쇼핑몰 제품 현황
search_shopping_mall_products(product_name="컴퓨터", num_rows=10)
```

## 2. 경쟁업체 분석
```python
# 특정 업체 계약 확인
search_shopping_mall_products(company_name="삼성전자", num_rows=15)

# 동일 품목 경쟁 현황
search_shopping_mall_products(product_name="프린터", num_rows=20)
```

## 3. 시장 트렌드 분석
```python
# 연도별 비교
get_procurement_statistics_by_year(year="2023", num_rows=30)
get_procurement_statistics_by_year(year="2024", num_rows=30)
```

## 4. 분야별 시장 규모
```python
# 용역 분야 현황
get_recent_bid_announcements(days_back=30, num_rows=15)
get_successful_bids_by_business_type(business_type="용역", days_back=120)
```

## 탐색 팁
1. num_rows=5로 시작 → 필요시 확대
2. 여러 API 결과 조합으로 교차 검증
3. 빈 결과 → 조건 완화 (기간 확대, 키워드 단순화)
"""
