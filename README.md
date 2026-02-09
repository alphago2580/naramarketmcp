# 나라장터 MCP 서버

한국 공공조달(G2B) 데이터를 MCP(Model Context Protocol)로 제공하는 FastMCP 2.0 서버입니다.

입찰공고, 낙찰정보, 계약정보, 조달통계, 물품목록, 종합쇼핑몰 등 나라장터의 주요 API를 AI 에이전트가 바로 사용할 수 있도록 통합했습니다.

## 아키텍처

```
┌─────────────────┐     MCP Protocol      ┌──────────────────────┐
│   AI Agent      │ ◄──(stdio/http/sse)──► │  naramarket-mcp      │
│ (Claude, etc.)  │                        │                      │
└─────────────────┘                        │  ┌────────────────┐  │
                                           │  │ MCP Tools (16) │  │
                                           │  │ Resources (3)  │  │
                                           │  │ Prompts (3)    │  │
                                           │  └───────┬────────┘  │
                                           │          │           │
                                           │  ┌───────▼────────┐  │
                                           │  │  API Clients   │  │
                                           │  │  (sync/async)  │  │
                                           │  └───────┬────────┘  │
                                           └──────────┼───────────┘
                                                      │
                                           ┌──────────▼───────────┐
                                           │  data.go.kr APIs     │
                                           │  (공공데이터포털)      │
                                           └──────────────────────┘
```

## MCP 도구

### 기본 도구 (3개)

| 도구 | 설명 |
|------|------|
| `crawl_list` | 나라장터 상품 목록 조회 |
| `get_detailed_attributes` | 상품 상세 속성 조회 |
| `server_info` | 서버 정보 및 사용 가능한 도구 목록 |

### 정부조달 API (4개)

| 도구 | 설명 | 지원 API |
|------|------|---------|
| `call_public_data_standard_api` | 공공데이터개방표준 API | 입찰공고, 낙찰정보, 계약정보 |
| `call_procurement_statistics_api` | 조달통계 API | 전체/기관별/기업별 조달 통계 (14개 오퍼레이션) |
| `call_product_list_api` | 물품목록 API | 물품분류, 품목 조회 (12개 오퍼레이션) |
| `call_shopping_mall_api` | 종합쇼핑몰 API | MAS 계약, 납품요구, 벤처나라 (9개 오퍼레이션) |

### AI 친화 간편 도구 (4개)

| 도구 | 설명 |
|------|------|
| `get_recent_bid_announcements` | 최근 입찰공고 조회 (기간 자동 계산) |
| `get_successful_bids_by_business_type` | 업무구분별 낙찰정보 (한글 → 코드 자동 변환) |
| `get_procurement_statistics_by_year` | 연도별 조달통계 |
| `search_shopping_mall_products` | 쇼핑몰 제품 검색 (제품명/업체명) |

### 탐색 도구 (4개)

| 도구 | 설명 |
|------|------|
| `get_all_api_services_info` | 전체 서비스 및 오퍼레이션 목록 |
| `get_api_operations` | 서비스별 세부 오퍼레이션 조회 |
| `call_api_with_pagination_support` | 페이징 지원 대량 데이터 탐색 |
| `get_data_exploration_guide` | 데이터 탐색 전략 가이드 |

### MCP 리소스 & 프롬프트

- **리소스**: API 파라미터 가이드, 값 예시, 검색 패턴
- **프롬프트**: 워크플로우 가이드, 파라미터 선택 가이드, 실전 쿼리 예제

## 시작하기

### 필수 요구사항

- Python 3.10+
- [공공데이터포털](https://www.data.go.kr/) API 서비스 키

### 설치

```bash
git clone https://github.com/alphago2580/naramarketmcp.git
cd naramarketmcp

# 환경 설정
cp .env.example .env
# .env에서 NARAMARKET_SERVICE_KEY 설정

# 의존성 설치
pip install -r requirements.txt
```

### 실행

```bash
# STDIO 모드 (MCP 클라이언트 연동)
python -m src.main

# HTTP 모드 (웹 서비스)
FASTMCP_TRANSPORT=http FASTMCP_PORT=8000 python -m src.main

# 패키지 설치 후 실행
pip install .
naramarket-mcp
```

### Docker

```bash
docker build -t naramarket-mcp .
docker run --rm -e NARAMARKET_SERVICE_KEY=your-key -p 8000:8000 naramarket-mcp
```

## 환경 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|:---:|--------|------|
| `NARAMARKET_SERVICE_KEY` | ✅ | - | 공공데이터포털 API 키 |
| `FASTMCP_TRANSPORT` | - | `stdio` | 전송 모드 (`stdio`, `http`, `sse`) |
| `FASTMCP_HOST` | - | `127.0.0.1` | HTTP/SSE 바인딩 호스트 |
| `FASTMCP_PORT` | - | `8081` | HTTP/SSE 포트 |
| `LOG_LEVEL` | - | `INFO` | 로깅 레벨 |

## 프로젝트 구조

```
naramarketmcp/
├── src/
│   ├── main.py              # FastMCP 서버 진입점 (도구/리소스/프롬프트 등록)
│   ├── core/                # 핵심 모듈
│   │   ├── config.py        # 설정 관리
│   │   ├── models.py        # 데이터 모델
│   │   ├── client.py        # API 클라이언트
│   │   ├── async_client.py  # 비동기 클라이언트
│   │   └── utils.py         # 유틸리티
│   ├── api/                 # HTTP/REST 인터페이스
│   ├── services/            # 비즈니스 로직 (크롤러, 인증)
│   └── tools/               # MCP 도구 구현
│       ├── naramarket.py    # 기본 나라장터 도구
│       ├── enhanced_tools.py # 확장 API 도구
│       └── openapi_tools.py # G2B OpenAPI 도구
├── tests/                   # 테스트
├── deployments/             # 배포 설정 (docker-compose, nginx)
├── Dockerfile
├── smithery.yaml            # Smithery.ai 배포 설정
├── pyproject.toml
└── requirements.txt
```

## 개발

```bash
# 개발 의존성 설치
pip install .[dev]

# 테스트 실행
pytest tests/

# 타입 체크
mypy src/
```

## 기술 스택

- **FastMCP 2.0** — MCP 서버 프레임워크
- **Requests / Pandas** — API 호출 및 데이터 처리
- **Uvicorn / Starlette** — HTTP/SSE 서빙
- **Docker** — 컨테이너 배포
- **Smithery.ai** — 클라우드 MCP 호스팅

## 라이선스

Apache License 2.0 — [LICENSE](LICENSE) 참조
