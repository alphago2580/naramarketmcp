# 🚀 Nara Market FastMCP 2.0 Server

한국 정부조달(G2B) 및 나라장터 쇼핑몰 데이터를 수집하는 **프로덕션 준비 완료** FastMCP 2.0 서버입니다.

## ⭐ 주요 특징

- **🏭 Smithery.ai 배포 준비 완료**: 원클릭 클라우드 배포 지원
- **⚡ FastMCP 2.0**: 최신 MCP 프로토콜 지원 (STDIO + SSE + HTTP)
- **🔗 OpenAPI 통합**: 5개의 G2B API 도구 추가
- **📊 대량 데이터 처리**: 윈도우 분할로 안전한 대용량 수집
- **🔄 재시작 가능**: 부분 실행 및 이어받기 기능
- **💾 유연한 저장**: CSV/Parquet 직접 저장으로 메모리 효율성

## 🛠️ 사용 가능한 MCP 도구

### 📦 나라장터 쇼핑몰 데이터 수집

| Tool | 기능 | 용도 |
|------|------|------|
| `crawl_list` | 상품 목록 조회 | 소량 데이터 수집 및 디버깅 |
| `get_detailed_attributes` | 상품 상세 속성 조회 | 개별 상품의 세부 정보 수집 |
| `crawl_to_memory` | 메모리 기반 수집 | 소규모 목록+상세 데이터 통합 수집 |

### 🏢 G2B 정부조달 데이터 수집 (OpenAPI 통합)

| Tool | 기능 | 데이터 종류 |
|------|------|-------------|
| `get_bid_announcement_info` | 입찰공고정보 조회 | 공개경쟁입찰, 제한경쟁입찰 등 |
| `get_successful_bid_info` | 낙찰정보 조회 | 계약체결 결과 데이터 |
| `get_contract_info` | 계약정보 조회 | 체결된 계약의 상세 정보 |
| `get_total_procurement_status` | 조달현황 조회 | 전체 조달 통계 및 현황 |
| `get_mas_contract_product_info` | MAS계약 상품정보 | 다수공급자계약 상품 데이터 |

### 💾 데이터 관리 도구

| Tool | 기능 | 설명 |
|------|------|------|
| `save_results` | JSON 파일 저장 | 메모리 데이터를 JSON으로 저장 |
| `list_saved_json` | 저장 파일 목록 | 저장된 JSON 파일 리스트 조회 |
| `convert_json_to_parquet` | 형식 변환 | JSON → Parquet (속성 펼치기 옵션) |
| `merge_csv_files` | CSV 병합 | 여러 CSV 파일을 하나로 통합 |
| `summarize_csv` | CSV 요약 | 헤더, 행 수, 데이터 미리보기 |
| `server_info` | 서버 정보 | 버전 및 사용 가능한 도구 목록 |

## 🔧 설치 및 실행

### 시스템 요구사항

- **Python**: 3.10 이상
- **메모리**: 최소 2GB (대량 데이터 수집 시 4GB+ 권장)
- **디스크**: 수집 데이터 크기에 따라 조정

### 1. 로컬 설치 (개발/테스트)

```bash
# 저장소 클론
git clone <repository-url>
cd naramarketmcp

# 환경 설정
cp .env.example .env
# .env 파일에서 NARAMARKET_SERVICE_KEY 설정

# 의존성 설치
pip install -r requirements.txt

# STDIO 모드로 실행 (MCP 클라이언트용)
python -m src.main

# HTTP 서버 모드로 실행 (테스트용)
export FASTMCP_TRANSPORT=http
export FASTMCP_HOST=127.0.0.1
export FASTMCP_PORT=8000
python -m src.main
```

### 2. 패키지 설치

```bash
# 패키지 설치
pip install .

# 콘솔 스크립트로 실행
naramarket-mcp

# SSE 모드 지원 (선택사항)
pip install .[sse]
export FASTMCP_TRANSPORT=sse
naramarket-mcp
```

### 3. Docker 실행

```bash
# 이미지 빌드
docker build -t naramarket-mcp .

# 컨테이너 실행
docker run --rm \
  -e NARAMARKET_SERVICE_KEY=your-api-key \
  -p 8000:8000 \
  naramarket-mcp
```

## 🏭 Smithery.ai 클라우드 배포

### 빠른 배포

1. **Smithery CLI 설치**
   ```bash
   npm install -g @smithery/cli
   ```

2. **API 키 준비**
   - [data.go.kr](https://www.data.go.kr/)에서 나라장터 API 키 발급
   - Smithery.ai 대시보드에서 `NARAMARKET_SERVICE_KEY` 시크릿 설정

3. **배포 실행**
   ```bash
   ./deploy.sh
   # 또는 수동: smithery deploy
   ```

### 배포 구성

- ✅ **`smithery.yaml`**: 메인 배포 설정
- ✅ **`Dockerfile`**: 프로덕션 최적화 컨테이너
- ✅ **`.env.example`**: 환경변수 템플릿
- ✅ **`deploy.sh`**: 자동 배포 스크립트

### 주요 배포 특징

- **HTTP Transport**: Smithery.ai의 HTTP 기반 MCP 프로토콜
- **동적 포트**: `PORT` 환경변수 자동 감지
- **헬스체크**: `/mcp` 엔드포인트 모니터링
- **시크릿 관리**: 환경변수 기반 API 키 설정
- **오토스케일링**: 로드에 따른 1-10 인스턴스 자동 확장

### MCP 엔드포인트

배포 완료 후 다음 엔드포인트 사용 가능:

- `GET /mcp` - 헬스체크 및 서버 정보
- `POST /mcp` - MCP 도구 호출
- `DELETE /mcp` - 리셋/정리 작업

## 🌐 API 사용 예시

### 나라장터 상품 목록 조회

```json
{
  "method": "tools/call",
  "params": {
    "name": "crawl_list",
    "arguments": {
      "category": "데스크톱컴퓨터",
      "page_no": 1,
      "num_rows": 50,
      "days_back": 30
    }
  }
}
```

### G2B 입찰공고 정보 조회

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_bid_announcement_info",
    "arguments": {
      "num_rows": 20,
      "page_no": 1,
      "start_date": "20240101",
      "end_date": "20240131"
    }
  }
}
```

### 대량 데이터 CSV 수집 (분할 처리)

```json
{
  "method": "tools/call",
  "params": {
    "name": "crawl_to_csv",
    "arguments": {
      "category": "노트북컴퓨터",
      "output_csv": "laptops_2024.csv",
      "total_days": 365,
      "window_days": 30,
      "max_windows_per_call": 2,
      "append": false,
      "explode_attributes": true
    }
  }
}
```

## ⚙️ 환경 변수 설정

### 필수 환경 변수

```env
# 나라장터 API 서비스 키 (필수)
NARAMARKET_SERVICE_KEY=your-service-key-here
```

### 선택 환경 변수

```env
# FastMCP Transport 모드
FASTMCP_TRANSPORT=stdio  # stdio, sse, http

# HTTP 모드 설정 (FASTMCP_TRANSPORT=http일 때)
FASTMCP_HOST=127.0.0.1
FASTMCP_PORT=8000

# API 환경 설정
API_ENVIRONMENT=production  # production, development

# 로깅 레벨
LOG_LEVEL=INFO
```

## 🔍 대용량 데이터 수집 가이드

### 윈도우 분할 전략

대량 데이터 수집 시 메모리 효율성과 재시작 가능성을 위해 윈도우 분할을 사용합니다.

```json
{
  "method": "tools/call",
  "params": {
    "name": "crawl_to_csv",
    "arguments": {
      "category": "데스크톱컴퓨터",
      "output_csv": "desktop_full.csv",
      "total_days": 365,
      "window_days": 30,
      "max_windows_per_call": 2,
      "max_runtime_sec": 1800,
      "append": false
    }
  }
}
```

### 이어받기 실행

```json
{
  "method": "tools/call",
  "params": {
    "name": "crawl_to_csv",
    "arguments": {
      "category": "데스크톱컴퓨터",
      "output_csv": "desktop_full.csv",
      "total_days": 300,
      "anchor_end_date": "20240301",
      "window_days": 30,
      "max_windows_per_call": 2,
      "append": true
    }
  }
}
```

### 주요 파라미터 설명

| 파라미터 | 설명 | 기본값 |
|----------|------|--------|
| `total_days` | 수집할 총 일수 (역순) | 365 |
| `window_days` | 윈도우 크기 (일) | 30 |
| `anchor_end_date` | 시작 기준 날짜 (YYYYMMDD) | 오늘 |
| `max_windows_per_call` | 호출당 최대 윈도우 수 | 0 (무제한) |
| `max_runtime_sec` | 최대 실행 시간 (초) | None |
| `append` | 기존 파일에 추가 여부 | false |
| `explode_attributes` | 속성 컬럼 펼치기 | false |

## 📁 프로젝트 구조

```
naramarketmcp/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastMCP 서버 진입점
│   ├── core/                # 핵심 모듈
│   │   ├── __init__.py
│   │   ├── config.py        # 설정 관리
│   │   └── models.py        # 데이터 모델
│   ├── api/                 # API 클라이언트
│   │   ├── __init__.py
│   │   └── client.py        # API 호출 로직
│   ├── services/            # 비즈니스 로직
│   │   ├── __init__.py
│   │   └── data_service.py  # 데이터 처리 서비스
│   └── tools/               # MCP 도구
│       ├── __init__.py
│       ├── base.py          # 기본 도구 클래스
│       ├── naramarket.py    # 나라장터 도구
│       └── openapi_tools.py # G2B OpenAPI 도구
├── tests/                   # 테스트 코드
├── deployments/             # 배포 설정
├── .env.example             # 환경변수 템플릿
├── .gitignore
├── Dockerfile               # 컨테이너 이미지
├── deploy.sh                # 배포 스크립트
├── pyproject.toml           # 프로젝트 설정
├── requirements.txt         # 의존성
├── smithery.yaml            # Smithery 배포 설정
└── README.md                # 프로젝트 문서
```

## 🔧 문제 해결

### 일반적인 문제

#### 1. API 키 오류
```
Error: Missing or invalid NARAMARKET_SERVICE_KEY
```
**해결방법**: `.env` 파일 또는 환경변수에 올바른 API 키 설정

#### 2. 메모리 부족
```
MemoryError: Unable to allocate array
```
**해결방법**: `window_days` 줄이기, `max_windows_per_call` 감소

#### 3. 네트워크 타임아웃
```
requests.exceptions.Timeout
```
**해결방법**: `max_runtime_sec` 설정, 재시작 가능한 배치로 분할

### 로그 분석

```bash
# 로그 레벨 조정
export LOG_LEVEL=DEBUG

# 실행 로그 확인
python -m src.main 2>&1 | tee server.log
```

### 성능 최적화

- **메모리**: 큰 데이터셋은 CSV 직접 저장 사용
- **네트워크**: 적절한 `window_days` 설정으로 배치 크기 조정
- **디스크**: SSD 사용 권장, 충분한 여유 공간 확보

## 🤝 기여 방법

### 개발 환경 설정

```bash
# 개발 의존성 설치
pip install .[dev]

# 테스트 실행
pytest tests/

# 타입 체크
mypy src/
```

### 기여 가이드라인

1. **이슈 생성**: 버그 리포트 또는 기능 요청
2. **포크 & 브랜치**: `feature/your-feature-name` 브랜치 생성
3. **개발**: 테스트 코드와 함께 구현
4. **테스트**: 모든 테스트 통과 확인
5. **Pull Request**: 상세한 설명과 함께 PR 생성

### 코드 스타일

- **포매팅**: Black 사용
- **린팅**: Flake8 준수
- **타입**: Type hints 필수
- **문서**: Docstring 작성

## 📄 라이선스

Apache License 2.0 - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🔗 관련 링크

- **Smithery.ai**: https://smithery.ai
- **FastMCP**: https://github.com/jlowin/fastmcp
- **나라장터 Open API**: https://www.data.go.kr/
- **G2B 전자조달시스템**: http://www.g2b.go.kr/

## 📊 변경 이력

### v0.1.0 (Latest)
- ✅ FastMCP 2.0 업그레이드
- ✅ Smithery.ai 배포 지원 추가
- ✅ G2B OpenAPI 5개 도구 통합
- ✅ HTTP Transport 지원
- ✅ 프로덕션 준비 완료

---

💡 **문의사항이나 기술 지원이 필요하시면 이슈를 생성해 주세요.**