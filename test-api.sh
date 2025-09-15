#!/bin/bash

# Naramarket MCP Server - API Testing Script
# HTTP 모드로 실행 중인 컨테이너의 API를 테스트하는 스크립트

echo "🧪 Naramarket MCP Server - API 테스트"
echo "===================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test server_info tool via MCP protocol
echo -e "${BLUE}📋 1. server_info 도구 테스트${NC}"
echo "=============================="

response=$(curl -s -X POST http://localhost:8000/sse \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "server_info",
      "arguments": {}
    }
  }' | head -20)

echo "응답 (첫 20줄):"
echo "$response"

echo ""
echo -e "${BLUE}📋 2. get_recent_bid_announcements 도구 테스트${NC}"
echo "================================================"

response2=$(curl -s -X POST http://localhost:8000/sse \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_recent_bid_announcements",
      "arguments": {
        "business_type": "물품",
        "days_back": 7,
        "num_rows": 3
      }
    }
  }' | head -20)

echo "응답 (첫 20줄):"
echo "$response2"

echo ""
echo -e "${YELLOW}💡 참고사항:${NC}"
echo "- FastMCP SSE 모드에서는 Server-Sent Events를 사용합니다"
echo "- 응답이 스트리밍 형태로 오므로 전체 응답을 보려면 적절한 SSE 클라이언트가 필요합니다"
echo "- 위 출력은 응답의 시작 부분만 보여줍니다"

echo ""
echo -e "${BLUE}📋 3. 컨테이너 상태 확인${NC}"
echo "========================"
docker ps | grep naramarket

echo ""
echo -e "${BLUE}📋 4. 최근 로그 확인${NC}"
echo "===================="
docker logs --tail 10 naramarket-prod-test

echo ""
echo -e "${GREEN}✅ API 테스트 완료${NC}"
echo "서버가 정상적으로 응답하고 있으면 MCP 프로토콜로 통신이 가능합니다."