# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

나라장터(G2B) API 대량 데이터 수집 서버. FastMCP와 FastAPI 이중 서버 구조로 윈도우 분할 방식의 재시작 가능한 크롤링 지원.

## Essential Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install with dev dependencies
pip install -e ".[dev]"

# Environment setup (required)
echo "NARAMARKET_SERVICE_KEY=your_api_key" > .env
```

### Running Servers
```bash
# FastMCP Server (primary)
python src/main.py                     # Modular MCP server
python server.py                        # Legacy single-file server

# FastAPI HTTP Server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Package installation
pip install .
naramarket-mcp                         # Run as installed package
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py -v

# Run single test
pytest tests/test_api.py::test_crawl_list -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Docker Operations
```bash
# Development build
docker build --target development -t naramarket-dev .
docker run --rm -e NARAMARKET_SERVICE_KEY=key naramarket-dev

# Production build
docker build --target production -t naramarket-prod .
docker run --rm -p 8000:8000 -e NARAMARKET_SERVICE_KEY=key naramarket-prod

# Docker Compose
cd deployments
docker-compose up -d
```

### Deployment
```bash
cd deployments
./deploy.sh production              # Deploy to production
./deploy.sh staging                 # Deploy to staging
```

## Architecture

### Dual Server Architecture
- **FastMCP Server** (`src/main.py`): MCP protocol for AI tool integration
- **FastAPI HTTP Server** (`src/api/app.py`): REST API with web interface

### Core Modules
```
src/
├── core/                    # Core infrastructure
│   ├── client.py           # Sync HTTP client with retry logic
│   ├── async_client.py     # Async HTTP client for high throughput
│   ├── config.py           # Configuration constants
│   └── models.py           # Pydantic data models
├── services/               # Business logic layer
│   ├── crawler.py          # Sync crawling service
│   ├── async_crawler.py    # Async crawling service
│   └── file_processor.py   # CSV/Parquet/JSON processing
├── tools/                  # MCP tool wrappers
│   └── naramarket.py       # Tool implementations
└── api/                    # HTTP API layer
    ├── routes.py           # Main API endpoints
    └── auth_routes.py      # Authentication endpoints
```

### Window-Based Crawling Strategy

The system uses a sliding window approach to handle large-scale data collection:

1. **Window Division**: Total period divided into manageable chunks (default 30 days)
2. **Anchor Points**: Track progress with `anchor_end_date` for resumability
3. **Append Mode**: Accumulate data in single file across multiple runs
4. **Partial Completion**: Return incomplete status with next anchor for continuation

Key parameters for `crawl_to_csv`:
- `total_days`: Total collection period
- `window_days`: Days per batch (memory optimization)
- `anchor_end_date`: Resume point (YYYYMMDD format)
- `max_windows_per_call`: Batch limit per execution
- `append`: Continue writing to existing file

### Data Flow
1. **List API** → Paginated product listings
2. **Detail API** → Individual product attributes
3. **NDJSON Buffer** → Streaming intermediate format
4. **CSV/Parquet** → Final output (direct disk write, no memory return)

## Critical Implementation Details

### Memory Safety for Large Datasets
- Never return large `products` arrays to MCP context
- Use streaming NDJSON for intermediate storage
- Direct CSV/Parquet writes bypass memory
- `crawl_to_csv` returns only metadata, not data

### Retry and Rate Limiting
```python
MAX_RETRIES = 3
RETRY_DELAY_SEC = 1.0  # Exponential backoff
DEFAULT_DELAY_SEC = 0.1  # Between requests
TIMEOUT_LIST = 20  # List API timeout
TIMEOUT_DETAIL = 15  # Detail API timeout
```

### Resume Pattern
```python
# Initial run
result = crawl_to_csv(category="computers", total_days=365, max_windows_per_call=2)

# Continue from checkpoint
while result["incomplete"]:
    result = crawl_to_csv(
        category="computers",
        total_days=result["remaining_days"],
        anchor_end_date=result["next_anchor_end_date"],
        append=True
    )
```

### Error Handling Hierarchy
1. **Network errors**: Retry with exponential backoff
2. **API errors**: Log and continue with next item
3. **Data errors**: Track in `failed_items` counter
4. **Critical errors**: Raise with partial results

## Environment Variables

Required:
```bash
NARAMARKET_SERVICE_KEY      # G2B API service key
```

Optional:
```bash
FASTMCP_TRANSPORT           # stdio (default) or sse
PYTHONPATH                  # Include src/ for module imports
LOG_LEVEL                   # DEBUG, INFO (default), WARNING, ERROR
```

## API Endpoints (FastAPI Mode)

### Core Endpoints
- `GET /api/v1/health` - Health check
- `POST /api/v1/crawl/list` - Fetch product list
- `POST /api/v1/crawl/detail` - Get product details
- `POST /api/v1/crawl/csv` - Large-scale CSV export
- `GET /api/v1/files` - List saved files
- `POST /api/v1/convert/parquet` - JSON to Parquet conversion

### Authentication (if enabled)
- `POST /api/v1/auth/login` - Get JWT token
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Current user info

## Development Workflow

### Adding New MCP Tools
1. Implement service logic in `src/services/`
2. Create tool wrapper in `src/tools/naramarket.py`
3. Register with `@mcp.tool()` decorator in `src/main.py`
4. Add corresponding API endpoint in `src/api/routes.py`

### Testing Guidelines
- Unit tests: `tests/test_utils.py` - Core utilities
- API tests: `tests/test_api.py` - Endpoint validation
- Auth tests: `tests/test_auth.py` - Security flows
- Use pytest fixtures for mock data and clients

### Type Safety
```bash
# Type checking
mypy src/ --ignore-missing-imports

# Type stubs for requests
pip install types-requests
```

## Performance Considerations

### Async vs Sync Trade-offs
- **Sync** (`crawler.py`): Simple, reliable, suitable for MCP tools
- **Async** (`async_crawler.py`): High throughput for HTTP API mode
- Default: Sync for MCP, Async for FastAPI

### CSV Append Performance
- Check column compatibility before append
- Use `fail_on_new_columns=False` for schema evolution
- Monitor file size for rotation needs

### Docker Resource Limits
```yaml
# docker-compose.yml
resources:
  limits:
    memory: 2G
    cpus: '2.0'
```

## Subagent Creation Guidelines

Claude Code should DIRECTLY create specialized subagents for complex, multi-faceted tasks instead of relying on task-orchestrator (which cannot create its own subagents).

### Direct Subagent Creation Pattern

When the user requests code modifications, feature additions, or complex project changes, Claude Code MUST immediately create multiple specialized subagents for parallel processing:

**Explicit Subagent Invocation Examples:**

```text
"@agent-fastmcp-migration-expert handle the FastMCP version upgrade"
"@agent-openapi-integration-specialist convert OpenAPI schemas to FastMCP tools"  
"@agent-architecture-refactoring-expert maintain modular structure and remove deprecated features"
"@agent-core-function-optimizer preserve and enhance critical functions like get_detailed_attributes"
"@agent-testing-validation-coordinator create comprehensive test suites and validate integrations"
```

**Natural Language Subagent Creation:**

```text
"Use the fastmcp-migration-expert to upgrade FastMCP components"
"Have the openapi-integration-specialist analyze the openapi.yaml file"
"Get the architecture-refactoring-expert to optimize the memory usage"
"Ask the core-function-optimizer to enhance API call patterns"
"Call the testing-validation-coordinator to run regression testing"
```

### Specialized Agent Roles

1. **FastMCP Migration Expert** (`@agent-fastmcp-migration-expert`)
   - Handle FastMCP version upgrades and new transport protocols (Streamable HTTP, SSE)
   - Update server initialization and configuration
   - Apply FastMCP 2.0 API patterns and improve tool definitions

2. **OpenAPI Integration Specialist** (`@agent-openapi-integration-specialist`)
   - Analyze OpenAPI.yaml specifications and convert to FastMCP tools
   - Integrate multiple API endpoints with proper error handling
   - Maintain API compatibility and schema validation

3. **Architecture Refactoring Expert** (`@agent-architecture-refactoring-expert`)
   - Maintain modular structure and remove deprecated features
   - Optimize memory usage for remote server environments
   - Ensure clean separation of concerns and proper dependency injection

4. **Core Function Optimizer** (`@agent-core-function-optimizer`)
   - Preserve and enhance critical functions (e.g., get_detailed_attributes)
   - Optimize API call patterns and implement proper caching
   - Improve error handling, debugging, and maintain backward compatibility

5. **Testing and Validation Coordinator** (`@agent-testing-validation-coordinator`)
   - Create comprehensive test suites with unit, integration, and E2E tests
   - Validate all integrations and perform regression testing
   - Ensure deployment readiness and CI/CD pipeline optimization

### Direct Creation Requirements

- **ALWAYS** create subagents IMMEDIATELY when user requests code changes
- **NEVER** delegate subagent creation to task-orchestrator (limitation: subagents cannot create subagents)
- Each subagent should have specific, focused responsibility with clear boundaries
- Use `@agent-[role-name]` format for explicit invocation
- Coordinate between agents through clear interface definitions and shared context

### Example Workflow for Project Modifications

When user requests "upgrade FastMCP and add new features":

```text
@agent-fastmcp-migration-expert analyze current FastMCP version and plan upgrade path
@agent-openapi-integration-specialist review openapi.yaml and identify new tool opportunities
@agent-architecture-refactoring-expert assess current structure and plan modular improvements
@agent-core-function-optimizer identify performance bottlenecks and enhancement opportunities
@agent-testing-validation-coordinator design comprehensive testing strategy for all changes
```

### Parallel Processing Requirements

- **MULTIPLE** subagent calls in SINGLE message for parallel execution
- **CLEAR** task division with minimal overlap between agents
- **SHARED** context through documentation and interface specifications
- **COORDINATED** output integration with proper error handling

### Subagent Performance Optimization

#### Agent Coordination Strategy

- **Async vs Sync**: Use sync for MCP tools, async for FastAPI mode
- **Resource Management**: Limit memory usage, monitor CPU utilization
- **Error Propagation**: Ensure proper error handling across agent boundaries

#### Data Processing Guidelines

- **CSV Operations**: Check compatibility before append operations
- **Memory Safety**: Use streaming for large datasets
- **File Monitoring**: Track file size for rotation needs

#### Container Resource Limits

```yaml
# docker-compose.yml for subagent coordination
resources:
  limits:
    memory: 2G
    cpus: '2.0'
```

## Troubleshooting

### Common Issues

1. **"Service key not found"**: Set `NARAMARKET_SERVICE_KEY` environment variable
2. **"Timeout during crawl"**: Reduce `window_days` or `max_windows_per_call`
3. **"Column mismatch on append"**: Set `fail_on_new_columns=False` or start fresh file
4. **"Memory error"**: Use `crawl_to_csv` instead of `crawl_category_detailed`

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python src/main.py

# Test single window
python -c "from src.services.crawler import crawler_service; print(crawler_service.crawl_list('computers', days_back=1))"
```

### Health Monitoring

- MCP: Check `server_info` tool response
- HTTP: Monitor `/api/v1/health` endpoint
- Logs: Check `data/logs/` directory for detailed traces
 
 