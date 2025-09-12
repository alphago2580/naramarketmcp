# Smithery.ai Deployment Guide

**Production deployment guide for Nara Market FastMCP Server**

Deploy your Korean government procurement data collection server to smithery.ai cloud platform in minutes.

## 🚀 Quick Deploy (5 minutes)

### Step 1: Prerequisites  
- [Smithery.ai account](https://smithery.ai) 
- [Nara Market API key](https://www.data.go.kr/) - Korean gov procurement API access
- GitHub repository with your code

### Step 2: Deploy to Smithery.ai
```bash
# Connect GitHub repository in smithery.ai dashboard
# Auto-detects smithery.yaml configuration
# Click "Deploy" - done!
```

### Step 3: Configure Environment
In smithery.ai dashboard, set required secrets:
```
NARAMARKET_SERVICE_KEY = your_nara_market_api_key
```

## ✅ Pre-configured Features

**Production-Ready MCP Tools:**
- `crawl_list` - Product catalog collection
- `get_detailed_attributes` - Detailed product data  
- `crawl_to_csv` - Large-scale data export
- `server_info` - Health monitoring
- G2B OpenAPI integration (bidding, contracts, procurement data)

**Cloud-Optimized Configuration:**
- HTTP transport for smithery.ai
- Auto-scaling (1-10 instances)
- Health monitoring via `/mcp` endpoint  
- Structured JSON logging
- Container-optimized Docker build

## 🔐 API Key Setup

### Get Nara Market API Key
1. Visit [공공데이터포털](https://www.data.go.kr/)
2. Search for "나라장터" APIs
3. Apply for API access
4. Get your service key

## 📊 Usage Examples

**Basic product collection:**
```python
# Collect computer listings (last 30 days)
result = crawl_list(category="데스크톱컴퓨터", days_back=30)

# Get product details  
details = get_detailed_attributes(product_id="1234567890")
```

**Large-scale data collection:**  
```python
# Export to CSV (memory-safe)
result = crawl_to_csv(
    category="데스크톱컴퓨터",
    output_csv="computers.csv", 
    total_days=365
)
```

## 📍 Deployment Endpoints

Once deployed, your server provides:
- `GET /mcp` - Health check and server info
- `POST /mcp` - MCP tool execution  
- Built-in monitoring via smithery.ai dashboard

## 🔧 Troubleshooting

### Common Issues  
1. **API Key Error** → Verify `NARAMARKET_SERVICE_KEY` in smithery.ai secrets
2. **Connection Timeout** → Check smithery.ai server status
3. **Tool Not Found** → Verify deployment completed successfully

### Local Testing (Before Deploy)
```bash
# Test locally with HTTP transport
FASTMCP_TRANSPORT=http python src/main.py

# Test Docker build
docker build --target production -t test-naramarket .
docker run -e NARAMARKET_SERVICE_KEY=your_key test-naramarket
```

## ✅ Post-Deployment Checklist

- [ ] Verify server health at `/mcp` endpoint  
- [ ] Test core tools: `crawl_list`, `server_info`
- [ ] Monitor smithery.ai dashboard for performance
- [ ] Set up alerts for production usage

## 📞 Support

- **Smithery.ai**: [docs.smithery.ai](https://docs.smithery.ai)
- **Nara Market APIs**: [data.go.kr](https://www.data.go.kr/)
- **Project Issues**: GitHub repository issues

**License:** Apache-2.0