#!/bin/bash

# Naramarket MCP Server - Docker Build Script
# Docker 이미지를 빌드하는 간단한 스크립트

set -e

echo "🐳 Naramarket MCP Server - Docker 이미지 빌드"
echo "============================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Build mode selection
echo "빌드할 이미지를 선택하세요:"
echo "1) 개발용 (development)"
echo "2) 프로덕션용 (production)"
echo "3) 둘 다"

read -p "선택 (1/2/3): " choice

case $choice in
    1)
        echo -e "${BLUE}개발용 이미지 빌드 중...${NC}"
        docker build -t naramarket-mcp:dev --target development .
        echo -e "${GREEN}✅ 개발용 이미지 빌드 완료${NC}"
        echo "실행: docker run --rm -it -e NARAMARKET_SERVICE_KEY=your_key naramarket-mcp:dev"
        ;;
    2)
        echo -e "${BLUE}프로덕션용 이미지 빌드 중...${NC}"
        docker build -t naramarket-mcp:prod --target production .
        echo -e "${GREEN}✅ 프로덕션용 이미지 빌드 완료${NC}"
        echo "실행: docker run --rm -d -p 8000:8000 -e NARAMARKET_SERVICE_KEY=your_key naramarket-mcp:prod"
        ;;
    3)
        echo -e "${BLUE}개발용 이미지 빌드 중...${NC}"
        docker build -t naramarket-mcp:dev --target development .
        echo -e "${GREEN}✅ 개발용 이미지 빌드 완료${NC}"

        echo -e "${BLUE}프로덕션용 이미지 빌드 중...${NC}"
        docker build -t naramarket-mcp:prod --target production .
        echo -e "${GREEN}✅ 프로덕션용 이미지 빌드 완료${NC}"
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}📋 빌드된 이미지 목록:${NC}"
docker images | grep naramarket-mcp

echo ""
echo -e "${GREEN}🎉 빌드 완료!${NC}"