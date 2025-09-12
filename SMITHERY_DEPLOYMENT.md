# Smithery.ai Deployment Guide

## naramarket-mcp MCP Server

한국 정부조달시장(G2B/나라장터) 데이터를 수집하는 FastMCP 2.0 서버입니다.

### 🚀 Smithery.ai 배포 준비 완료

이 프로젝트는 smithery.ai 배포를 위해 다음과 같이 구성되어 있습니다:

#### 📁 핵심 파일들
- `smithery.yaml`: Smithery.ai 배포 설정
- `Dockerfile`: 멀티스테이지 빌드로 최적화된 컨테이너
- `src/main.py`: FastMCP 2.0 서버 엔트리포인트 
- `requirements.txt`: Python 의존성 정의

#### 🔧 설정된 기능들

**MCP Tools:**
- `crawl_list`: 카테고리별 상품 목록 수집
- `get_detailed_attributes`: 상세 속성 정보 조회
- `crawl_to_memory`: 메모리 내 데이터 수집
- `server_info`: 서버 상태 확인
- OpenAPI 기반 정부조달 API 통합:
  - `get_bid_announcement_info`: 입찰공고정보 조회
  - `get_successful_bid_info`: 낙찰정보 조회
  - `get_contract_info`: 계약정보 조회
  - `get_total_procurement_status`: 전체 공공조달 현황
  - `get_mas_contract_product_info`: 다수공급자계약 품목정보

**기술 스택:**
- FastMCP 2.0 프레임워크
- HTTP/SSE transport 지원
- Pydantic 데이터 모델
- 비동기 요청 처리
- 환경설정 파라미터 자동 처리

#### 🌐 Smithery.ai 배포 방법

1. **GitHub에 코드 푸시**
   ```bash
   git add .
   git commit -m "Ready for smithery.ai deployment"
   git push origin main
   ```

2. **Smithery.ai에서 배포**
   - https://smithery.ai 로그인
   - "New Server" 또는 "Deploy" 클릭
   - GitHub 리포지토리 연결
   - `smithery.yaml` 자동 감지
   - 배포 실행

3. **필수 환경변수 설정**
   - `naramarketServiceKey`: 나라장터 API 서비스키
   - `apiEnvironment`: production/development

#### 🔐 API 키 발급

나라장터 API 키는 다음에서 발급받으세요:
- 공공데이터포털: https://www.data.go.kr/
- 나라장터 OpenAPI 신청 필요

#### 📊 사용 예시

```python
# MCP 클라이언트에서 호출
result = await client.call_tool("crawl_list", {
    "category": "데스크톱컴퓨터",
    "days_back": 30
})

# 입찰공고 조회
bids = await client.call_tool("get_bid_announcement_info", {
    "num_rows": 10,
    "page_no": 1
})
```

#### 🚀 배포 상태 확인

배포 후 다음 엔드포인트들을 통해 상태를 확인할 수 있습니다:

- **Health Check**: `GET /mcp`
- **MCP Protocol**: `POST /mcp`
- **서버 정보**: `server_info` 도구 호출

#### 📈 모니터링 및 로깅

- 구조화된 JSON 로깅
- 요청/응답 추적
- 오류 처리 및 재시도 로직
- 성능 메트릭 수집

#### 🔧 문제 해결

**일반적인 문제들:**
1. **API 키 오류**: `naramarketServiceKey` 확인
2. **연결 시간초과**: 네트워크 설정 확인  
3. **데이터 형식 오류**: OpenAPI 스펙 준수 확인

**디버깅:**
```bash
# 로컬 테스트
FASTMCP_TRANSPORT=http python -m src.main

# Docker 테스트 (Docker 설치 필요)
docker build --target production -t naramarket-mcp .
docker run -e NARAMARKET_SERVICE_KEY=your_key -p 8000:8000 naramarket-mcp
```

#### 📝 라이센스

Apache-2.0 License

---

## 다음 단계

1. 코드를 GitHub에 푸시
2. smithery.ai에서 배포 설정
3. API 키 구성
4. MCP 클라이언트에서 테스트
5. 프로덕션 모니터링 설정

이 서버는 Claude Code를 통해 smithery.ai 배포에 최적화되어 있습니다.