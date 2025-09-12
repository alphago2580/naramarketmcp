#!/bin/bash
# Deployment script for smithery.ai

set -e

echo "🚀 Deploying Naramarket MCP Server to smithery.ai..."

# Check if smithery CLI is installed
if ! command -v smithery &> /dev/null; then
    echo "❌ Smithery CLI not found. Installing..."
    npm install -g @smithery/cli
fi

# Validate smithery.yaml
echo "✅ Validating smithery.yaml configuration..."
if [ ! -f "smithery.yaml" ]; then
    echo "❌ smithery.yaml not found!"
    exit 1
fi

# Check environment variables
if [ -z "$NARAMARKET_SERVICE_KEY" ]; then
    echo "⚠️  Warning: NARAMARKET_SERVICE_KEY environment variable not set"
    echo "   Make sure to set this secret in smithery.ai dashboard"
fi

# Build and test locally (optional)
echo "🔨 Building Docker image for testing..."
docker build -t naramarket-mcp:latest --target production .

# Test the container locally
echo "🧪 Testing container locally..."
docker run --rm -d -p 8000:8000 \
  -e FASTMCP_TRANSPORT=http \
  -e FASTMCP_HOST=0.0.0.0 \
  -e PORT=8000 \
  --name naramarket-test \
  naramarket-mcp:latest

# Wait for container to start
sleep 5

# Test health endpoint
if curl -f http://localhost:8000/mcp > /dev/null 2>&1; then
    echo "✅ Local container test passed"
else
    echo "❌ Local container test failed"
    docker logs naramarket-test
    docker stop naramarket-test
    exit 1
fi

# Clean up test container
docker stop naramarket-test

# Deploy to smithery.ai
echo "🌐 Deploying to smithery.ai..."
smithery deploy

echo "✅ Deployment completed!"
echo "📋 Next steps:"
echo "   1. Set NARAMARKET_SERVICE_KEY secret in smithery.ai dashboard"
echo "   2. Test your deployed MCP server"
echo "   3. Monitor logs and metrics in smithery.ai"