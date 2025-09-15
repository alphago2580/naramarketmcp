#!/bin/bash

# Naramarket MCP Server - Local Docker Testing Script
# 로컬 환경에서 Docker 이미지를 빌드하고 테스트하는 스크립트

set -e  # Exit on any error

echo "🐳 Naramarket MCP Server - Docker 테스트"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 파일이 없습니다!${NC}"
    echo "   .env.example을 복사해서 .env 파일을 만들고 API 키를 설정해주세요."
    echo "   cp .env.example .env"
    exit 1
fi

# Load environment variables
source .env

# Check if API key is set
if [ -z "$NARAMARKET_SERVICE_KEY" ] || [ "$NARAMARKET_SERVICE_KEY" = "your_service_key_here" ]; then
    echo -e "${RED}❌ NARAMARKET_SERVICE_KEY가 설정되지 않았습니다!${NC}"
    echo "   .env 파일에서 실제 API 키를 설정해주세요."
    exit 1
fi

echo -e "${GREEN}✅ API 키 확인 완료${NC}"

# Function to cleanup containers
cleanup() {
    echo -e "${YELLOW}🧹 컨테이너 정리 중...${NC}"
    docker stop naramarket-dev-test 2>/dev/null || true
    docker stop naramarket-prod-test 2>/dev/null || true
    docker rm naramarket-dev-test 2>/dev/null || true
    docker rm naramarket-prod-test 2>/dev/null || true
}

# Cleanup on script exit
trap cleanup EXIT

echo ""
echo -e "${BLUE}📦 1단계: Docker 이미지 빌드${NC}"
echo "==============================="

# Build development image
echo -e "${YELLOW}개발용 이미지 빌드 중...${NC}"
docker build -t naramarket-mcp:dev --target development .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 개발용 이미지 빌드 성공${NC}"
else
    echo -e "${RED}❌ 개발용 이미지 빌드 실패${NC}"
    exit 1
fi

# Build production image
echo -e "${YELLOW}프로덕션용 이미지 빌드 중...${NC}"
docker build -t naramarket-mcp:prod --target production .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 프로덕션용 이미지 빌드 성공${NC}"
else
    echo -e "${RED}❌ 프로덕션용 이미지 빌드 실패${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🧪 2단계: 프로덕션 모드 테스트 (HTTP)${NC}"
echo "=================================="

# Start production container
echo -e "${YELLOW}프로덕션 컨테이너 시작 중...${NC}"
docker run -d \
  --name naramarket-prod-test \
  -e NARAMARKET_SERVICE_KEY="$NARAMARKET_SERVICE_KEY" \
  -e FASTMCP_TRANSPORT=http \
  -e FASTMCP_HOST=0.0.0.0 \
  -e PORT=8000 \
  -p 8000:8000 \
  naramarket-mcp:prod

# Wait for container to start
echo -e "${YELLOW}컨테이너 시작 대기 중... (10초)${NC}"
sleep 10

# Test health endpoint
echo -e "${YELLOW}헬스체크 테스트 중...${NC}"
if curl -f --max-time 10 http://localhost:8000/mcp > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 헬스체크 성공${NC}"
else
    echo -e "${RED}❌ 헬스체크 실패${NC}"
    echo "컨테이너 로그:"
    docker logs naramarket-prod-test
    exit 1
fi

# Test server_info tool
echo -e "${YELLOW}server_info 도구 테스트 중...${NC}"
response=$(curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "server_info", "arguments": {}}}' \
  | jq -r '.result.content[0].text' 2>/dev/null || echo "failed")

if [[ "$response" == *"naramarket-fastmcp"* ]]; then
    echo -e "${GREEN}✅ server_info 도구 테스트 성공${NC}"
else
    echo -e "${RED}❌ server_info 도구 테스트 실패${NC}"
    echo "응답: $response"
fi

# Test API call with actual data
echo -e "${YELLOW}실제 API 호출 테스트 중...${NC}"
api_response=$(curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_recent_bid_announcements",
      "arguments": {
        "business_type": "물품",
        "days_back": 7,
        "num_rows": 3
      }
    }
  }' | jq -r '.result.content[0].text' 2>/dev/null || echo "failed")

if [[ "$api_response" == *"success"* ]] && [[ "$api_response" == *"items"* ]]; then
    echo -e "${GREEN}✅ 실제 API 호출 테스트 성공${NC}"
    echo "   입찰공고 데이터를 성공적으로 조회했습니다."
else
    echo -e "${YELLOW}⚠️  API 호출 테스트 결과 확인 필요${NC}"
    echo "   응답 일부: ${api_response:0:100}..."
fi

# Show container logs for debugging
echo ""
echo -e "${BLUE}📋 컨테이너 로그 (마지막 20줄)${NC}"
echo "=========================="
docker logs --tail 20 naramarket-prod-test

echo ""
echo -e "${BLUE}🎯 3단계: 인터랙티브 테스트 가이드${NC}"
echo "=============================="
echo "컨테이너가 계속 실행 중입니다. 다음 명령어들로 추가 테스트할 수 있습니다:"
echo ""
echo -e "${YELLOW}기본 헬스체크:${NC}"
echo "  curl http://localhost:8000/mcp"
echo ""
echo -e "${YELLOW}서버 정보 조회:${NC}"
echo '  curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '"'"'{"method": "tools/call", "params": {"name": "server_info", "arguments": {}}}'"'"''
echo ""
echo -e "${YELLOW}AI 친화 도구 테스트:${NC}"
echo '  curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '"'"'{"method": "tools/call", "params": {"name": "get_recent_bid_announcements", "arguments": {"business_type": "물품", "num_rows": 5}}}'"'"''
echo ""
echo -e "${YELLOW}컨테이너 로그 실시간 확인:${NC}"
echo "  docker logs -f naramarket-prod-test"
echo ""
echo -e "${YELLOW}테스트 완료 후 컨테이너 정리:${NC}"
echo "  docker stop naramarket-prod-test"
echo ""

read -p "Enter를 눌러 컨테이너를 정리하고 종료하거나, Ctrl+C로 컨테이너를 유지하세요..."

echo -e "${GREEN}🎉 Docker 테스트 완료!${NC}"