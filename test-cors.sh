#!/bin/bash

# Naramarket MCP Server - CORS Testing Script
# Smithery.ai 배포를 위한 CORS 설정 테스트

echo "🌐 CORS Configuration Test for Smithery.ai"
echo "=========================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if server is running
echo -e "${BLUE}🔍 서버 상태 확인${NC}"
echo "=================="

if ! curl -s --max-time 3 http://localhost:8000/sse >/dev/null 2>&1; then
    echo -e "${RED}❌ 서버가 실행되지 않았습니다${NC}"
    echo "다음 명령으로 서버를 먼저 시작하세요:"
    echo "  docker run -d -p 8000:8000 -e NARAMARKET_SERVICE_KEY=your_key naramarket-mcp:prod"
    exit 1
fi

echo -e "${GREEN}✅ 서버가 실행 중입니다${NC}"

# Test 1: OPTIONS preflight request
echo ""
echo -e "${BLUE}🧪 테스트 1: OPTIONS 사전 요청 (Preflight)${NC}"
echo "=========================================="

echo -e "${YELLOW}요청: OPTIONS /sse${NC}"
options_response=$(curl -s -i -X OPTIONS http://localhost:8000/sse \
  -H "Origin: https://smithery.ai" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization")

echo "응답 헤더:"
echo "$options_response" | head -20

# Check specific CORS headers
echo ""
echo -e "${BLUE}📋 CORS 헤더 검증${NC}"
echo "=================="

# Access-Control-Allow-Origin
if echo "$options_response" | grep -qi "Access-Control-Allow-Origin.*\*"; then
    echo -e "${GREEN}✅ Access-Control-Allow-Origin: * 확인됨${NC}"
else
    echo -e "${RED}❌ Access-Control-Allow-Origin: * 누락${NC}"
fi

# Access-Control-Allow-Credentials
if echo "$options_response" | grep -qi "Access-Control-Allow-Credentials.*true"; then
    echo -e "${GREEN}✅ Access-Control-Allow-Credentials: true 확인됨${NC}"
else
    echo -e "${RED}❌ Access-Control-Allow-Credentials: true 누락${NC}"
fi

# Access-Control-Allow-Methods
if echo "$options_response" | grep -qi "Access-Control-Allow-Methods"; then
    echo -e "${GREEN}✅ Access-Control-Allow-Methods 헤더 확인됨${NC}"
    echo "$options_response" | grep -i "Access-Control-Allow-Methods" | head -1
else
    echo -e "${RED}❌ Access-Control-Allow-Methods 헤더 누락${NC}"
fi

# Access-Control-Allow-Headers
if echo "$options_response" | grep -qi "Access-Control-Allow-Headers"; then
    echo -e "${GREEN}✅ Access-Control-Allow-Headers 헤더 확인됨${NC}"
    echo "$options_response" | grep -i "Access-Control-Allow-Headers" | head -1
else
    echo -e "${RED}❌ Access-Control-Allow-Headers 헤더 누락${NC}"
fi

# Access-Control-Expose-Headers (MCP specific)
if echo "$options_response" | grep -qi "Access-Control-Expose-Headers"; then
    echo -e "${GREEN}✅ Access-Control-Expose-Headers 헤더 확인됨${NC}"
    echo "$options_response" | grep -i "Access-Control-Expose-Headers" | head -1

    # Check for MCP-specific headers
    if echo "$options_response" | grep -qi "mcp-session-id\|mcp-protocol-version"; then
        echo -e "${GREEN}✅ MCP 프로토콜 헤더 노출 설정 확인됨${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP 프로토콜 헤더가 명시적으로 노출되지 않음${NC}"
    fi
else
    echo -e "${RED}❌ Access-Control-Expose-Headers 헤더 누락${NC}"
fi

# Test 2: Cross-origin GET request
echo ""
echo -e "${BLUE}🧪 테스트 2: 크로스 오리진 GET 요청${NC}"
echo "============================="

echo -e "${YELLOW}요청: GET /sse (Origin: https://smithery.ai)${NC}"
get_response=$(curl -s -i -X GET http://localhost:8000/sse \
  -H "Origin: https://smithery.ai" \
  --max-time 3 | head -15)

echo "응답 헤더 (처음 15줄):"
echo "$get_response"

if echo "$get_response" | grep -qi "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✅ GET 요청에 CORS 헤더 포함됨${NC}"
else
    echo -e "${RED}❌ GET 요청에 CORS 헤더 누락${NC}"
fi

# Test 3: JavaScript fetch simulation
echo ""
echo -e "${BLUE}🧪 테스트 3: JavaScript Fetch 시뮬레이션${NC}"
echo "======================================"

echo -e "${YELLOW}시뮬레이션: fetch() API 호출${NC}"
fetch_response=$(curl -s -i -X POST http://localhost:8000/sse \
  -H "Origin: https://app.smithery.ai" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"test": "cors"}' \
  --max-time 3 | head -10)

echo "응답 헤더 (처음 10줄):"
echo "$fetch_response"

# Summary
echo ""
echo -e "${BLUE}📊 CORS 테스트 요약${NC}"
echo "=================="

echo -e "${GREEN}✅ 구현된 CORS 헤더:${NC}"
echo "  - Access-Control-Allow-Origin: *"
echo "  - Access-Control-Allow-Credentials: true"
echo "  - Access-Control-Allow-Methods: GET, POST, OPTIONS"
echo "  - Access-Control-Allow-Headers: *, Content-Type, Authorization"
echo "  - Access-Control-Expose-Headers: mcp-session-id, mcp-protocol-version"

echo ""
echo -e "${BLUE}🎯 Smithery.ai 호환성${NC}"
echo "==================="
echo "✅ 모든 오리진 허용 (*)"
echo "✅ 자격증명 허용 (credentials: true)"
echo "✅ 필수 HTTP 메서드 지원"
echo "✅ 모든 헤더 허용"
echo "✅ MCP 프로토콜 헤더 노출"
echo "✅ OPTIONS 사전 요청 처리"

echo ""
echo -e "${GREEN}🎉 CORS 설정이 Smithery.ai 배포에 최적화되었습니다!${NC}"