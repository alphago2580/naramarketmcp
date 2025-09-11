# Nara Market FastMCP Server (경량화)

나라장터 쇼핑몰(Open API + G2B 상세) 데이터를 **윈도우 단위/페이지 단위/상세 속성**까지 안전하게 수집해 **단일 CSV/Parquet** 로 적재하는 FastMCP 기반 서버.

핵심 목표:

1. LLM 컨텍스트 폭주 방지 (대량 데이터는 메모리 반환 금지, 디스크 직접 저장)
2. 재시작 가능(윈도우 분할 + 앵커 날짜 + 부분 실행)로 타임아웃 회피
3. append 기능으로 한 파일 누적

## 활성 MCP Tools (최소 필수)

| Tool | 목적 |
|------|------|
| crawl_list | 목록 API (소량/디버깅) |
| get_detailed_attributes | 단일 상품 상세 속성 조회 |
| crawl_category_detailed | 소규모 목록+상세 통합 (메모리 products 반환) |
| crawl_to_csv | 대량 윈도우+페이지+상세 수집 → 직접 CSV (컨텍스트 안전, partial/append 지원) |
| save_results | 메모리 products JSON 저장 |
| list_saved_json | 저장된 JSON 파일 나열 |
| convert_json_to_parquet | JSON → Parquet (선택적 attributes 펼치기) |
| merge_csv_files | 여러 CSV 병합 |
| summarize_csv | CSV 헤더/행수/프리뷰 |
| server_info | 서버 버전 & 툴 목록 |



## 요구 환경

- Python 3.11+
- 의존성: `requirements.txt` (버전 고정 권장)
- 환경변수: `NARAMARKET_SERVICE_KEY` (또는 실행 경로 `.env` 파일)

## 설치 & 실행 방법

### 1) pip (소스) 설치

```bash
pip install -r requirements.txt
python server.py
```

### 2) 패키지(배포형) (pyproject 포함)

```bash
pip install .
naramarket-mcp  # console script (stdio)
```

### 3) Docker

```bash
docker build -t naramarket-mcp .
docker run --rm -e NARAMARKET_SERVICE_KEY=발급키 naramarket-mcp
```

### 4) SSE 서버 모드 (선택)

`pyproject.toml` optional extras (`sse`) 설치 후 환경변수:

```bash
pip install .[sse]
FASTMCP_TRANSPORT=sse naramarket-mcp
```
> 기본은 stdio 모드이므로 MCP 호스트(에디터/클라이언트)가 프로세스를 관리해야 합니다.

## .env / 환경 변수

필수:

```env
NARAMARKET_SERVICE_KEY=발급받은_서비스키
```

선택:

```env
FASTMCP_TRANSPORT=stdio   # 또는 sse
```

## crawl_to_csv 주요 파라미터 (대량 수집 핵심)

| 파라미터 | 설명 |
|----------|------|
| total_days | 과거 며칠 치 역행 수집 (기본 365) |
| window_days | 한 윈도우(배치) 크기 (기본 30) |
| anchor_end_date | 이어서 실행할 기준 end 날짜 (YYYYMMDD) |
| max_windows_per_call | 한 호출에서 처리할 최대 윈도우 수 (0=무제한) |
| max_runtime_sec | 최대 실행 시간 초과 시 partial 종료 |
| append | True → 기존 CSV 이어쓰기 (컬럼 구조 동일) |
| fail_on_new_columns | append 중 새 컬럼 발견 시 실패 처리 |
| explode_attributes | 상세 속성 각각 컬럼 확장 (False면 JSON 문자열 1컬럼) |
| sanitize | 컬럼명 특수문자 정리 |

반환 메타 필드 예:
`incomplete`, `remaining_days`, `next_anchor_end_date`, `elapsed_sec`, `append_mode` …

### 예시 워크플로 (1년치 분할 수집, 두 윈도우씩 쌓기)

1) 초기:
```jsonc
call crawl_to_csv {
  "category": "데스크톱컴퓨터",
  "output_csv": "desktop_full.csv",
  "total_days": 365,
  "window_days": 30,
  "max_windows_per_call": 2,
  "append": false
}
```
2) 결과의 `next_anchor_end_date`, `remaining_days` 사용해 반복:
```jsonc
call crawl_to_csv {
  "category": "데스크톱컴퓨터",
  "output_csv": "desktop_full.csv",
  "total_days": REMAINING_DAYS,
  "anchor_end_date": "NEXT_ANCHOR",
  "window_days": 30,
  "max_windows_per_call": 2,
  "append": true
}
```
3) `incomplete=false` 될 때까지 재호출 → 단일 파일 누적 완료.

## 디렉터리 구조

```text
naramarket_server/
  server.py          # FastMCP 서버 (필수 툴)
  requirements.txt   # 런타임 의존성 (버전 핀)
  Dockerfile         # 컨테이너 이미지
  .env.example       # 환경변수 템플릿
  README.md          # 문서
  tests/             # (선택) 향후 테스트 추가 위치
```

## 확장 가이드

- 신규 API → 함수 추가 후 `@mcp.tool()` 적용
- 대량 데이터 → 메모리 products 반환 지양, CSV/Parquet 직접 저장
- 에러 처리 → 재시도(retryable) 데코레이터 / 실패 항목 통계 노출
- 고급 확장 → async(httpx), 캐시(Redis), 메타데이터 인덱스, incremental resume

## 보안

- 서비스키를 코드에 하드코딩하지 않습니다.
- Docker / 인프라 환경에서 secret 주입 (env / secret manager)

## 추후 개선 아이디어

- Redis 캐시 (동일 파라미터 재호출 방지)
- async 전환 (httpx + asyncio) 으로 처리량 향상
- pytest + 샘플 응답 fixture
- OpenAPI/JSON schema 자동 생성

---

## Change Log (요약)
- 0.1.0: 초기 경량 릴리즈, window 기반 crawl_to_csv + partial/append 지원

---

문의 / 확장 요청은 MCP 클라이언트 대화 또는 이슈로 전달하세요.
