# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

나라장터(G2B) API를 통해 대량의 상품 데이터를 수집하고 CSV/Parquet 형태로 저장하는 하이브리드 서버입니다. FastMCP 서버와 FastAPI HTTP 서버 두 가지 모드로 실행 가능하며, 윈도우 분할 방식으로 재시작 가능한 대용량 데이터 수집을 지원합니다.

## 주요 명령어

### 개발 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성 필요)
NARAMARKET_SERVICE_KEY=발급받은_서비스키
```

### 서버 실행
```bash
# 1. FastMCP 서버 실행 (기본)
python server.py                    # 레거시 단일 파일 서버
python src/main.py                  # 새로운 모듈화된 MCP 서버

# 2. FastAPI HTTP 서버 실행
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# 3. 패키지 설치 후 실행
pip install .
naramarket-mcp                      # MCP 서버로 실행

# 4. SSE 모드 (선택사항)
pip install .[sse]
FASTMCP_TRANSPORT=sse naramarket-mcp
```

### 테스트 실행
```bash
# 기본 테스트 실행
pytest

# 상세 출력으로 실행
pytest -v

# 특정 테스트 파일 실행
pytest tests/test_api.py
pytest tests/test_auth.py
```

### Docker 실행
```bash
# 개발 모드
docker build --target development -t naramarket-dev .
docker run --rm -e NARAMARKET_SERVICE_KEY=발급키 naramarket-dev

# 프로덕션 모드
docker build --target production -t naramarket-prod .
docker run --rm -p 8000:8000 -e NARAMARKET_SERVICE_KEY=발급키 naramarket-prod

# Docker Compose 실행
cd deployments
docker-compose up -d
```

## 핵심 아키텍처

### 이중 서버 구조
프로젝트는 두 가지 서버 모드를 지원합니다:

1. **FastMCP 서버** (`server.py`, `src/main.py`): MCP 도구 기반 데이터 수집
2. **FastAPI HTTP 서버** (`src/api/app.py`): REST API + 웹 인터페이스

### 모듈 구조
```
src/
├── main.py              # FastMCP 엔트리포인트
├── core/               # 핵심 설정 및 모델
│   ├── config.py       # 설정 상수
│   ├── models.py       # 데이터 모델
│   ├── client.py       # 동기 HTTP 클라이언트
│   ├── async_client.py # 비동기 HTTP 클라이언트
│   └── utils.py        # 유틸리티 함수
├── services/           # 비즈니스 로직
│   ├── crawler.py      # 동기 크롤링 서비스
│   ├── async_crawler.py # 비동기 크롤링 서비스
│   ├── file_processor.py # 파일 처리 서비스
│   └── auth.py         # 인증 서비스
├── tools/              # MCP 도구 구현
│   ├── base.py         # 기본 도구 클래스
│   └── naramarket.py   # 나라시장 도구들
└── api/                # FastAPI HTTP API
    ├── app.py          # FastAPI 앱 설정
    ├── routes.py       # 주요 API 라우트
    └── auth_routes.py  # 인증 관련 라우트
```

### 핵심 MCP 도구들
- `crawl_to_csv`: 대량 데이터 수집의 핵심 도구 (윈도우+페이지+상세속성)
- `crawl_list`: 소량 디버깅용 목록 API
- `get_detailed_attributes`: 단일 상품 상세 속성 조회
- `save_results`: JSON 파일 저장
- `convert_json_to_parquet`: JSON → Parquet 변환
- `merge_csv_files`: CSV 파일 병합
- `summarize_csv`: CSV 파일 요약

### 윈도우 기반 분할 처리
- `total_days`: 전체 수집 기간
- `window_days`: 한 번에 처리할 일 수
- `anchor_end_date`: 이어서 실행할 기준 날짜
- `max_windows_per_call`: 한 호출당 최대 윈도우 수
- `append`: 기존 파일에 이어 쓰기 모드

### 데이터 처리 흐름
1. 윈도우 단위로 API 호출
2. 페이지네이션으로 목록 수집
3. 각 상품의 상세 속성 개별 조회
4. CSV/Parquet으로 직접 저장 (메모리 우회)

## 환경 변수

**필수**:
- `NARAMARKET_SERVICE_KEY`: 나라장터 API 서비스 키

**선택**:
- `FASTMCP_TRANSPORT`: stdio(기본) 또는 sse
- `PYTHONPATH`: src 디렉토리를 포함

## 개발 시 주의사항

### 코드 구조 및 패턴
- **서비스 레이어**: 비즈니스 로직은 `services/` 디렉토리에 구현
- **도구 래퍼**: MCP 도구는 `tools/` 디렉토리에서 서비스를 래핑
- **타입 힌트**: 모든 함수에 타입 힌트 사용 (`typing` 모듈 활용)
- **에러 처리**: `retryable` 데코레이터와 예외 처리 적용

### 메모리 관리
- 대량 데이터는 메모리에 products를 반환하지 않음
- CSV/Parquet 직접 저장으로 컨텍스트 안전성 확보
- NDJSON 임시 파일 활용으로 스트리밍 처리

### 재시작 가능 설계
- `incomplete=true/false`로 작업 완료 여부 확인
- `next_anchor_end_date`와 `remaining_days`로 이어서 실행 가능
- `append=true`로 기존 파일에 누적 저장

### API 제한 준수
- 재시도 로직 (`MAX_RETRIES=3`, 지수 백오프)
- 요청 간 지연 (`DEFAULT_DELAY_SEC=0.1`)
- 타임아웃 설정 (목록 API: 20초, 상세 API: 15초)

## 배포 및 운영

### Docker 멀티 스테이지 빌드
- **development**: 개발 환경용 (전체 소스 복사)
- **production**: 프로덕션 환경용 (최적화된 이미지)

### 인프라 구성
- `deployments/docker-compose.yml`: 컨테이너 오케스트레이션
- `deployments/nginx/nginx.conf`: 리버스 프록시 설정
- `deployments/deploy.sh`: 배포 스크립트

### 헬스 체크
- FastAPI 서버: `/api/v1/health` 엔드포인트
- Docker 헬스 체크 설정 포함