# Multi-stage Docker build for optimized production image
FROM python:3.11-slim as base

# Install system dependencies including ca-certificates for HTTPS
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (important for API timestamp validation)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r naramarket && useradd -r -g naramarket naramarket

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FASTMCP_TRANSPORT=stdio

COPY . .
RUN chown -R naramarket:naramarket /app
USER naramarket

CMD ["python", "src/main.py"]

# Production stage
FROM base as production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV FASTMCP_TRANSPORT=http
ENV FASTMCP_HOST=0.0.0.0

# Copy only necessary files
COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Create data directory
RUN mkdir -p /app/data && chown -R naramarket:naramarket /app
USER naramarket

# Set dynamic port handling for smithery.ai
ENV FASTMCP_PORT=${PORT:-8000}

# Health check for MCP server (simplified for compatibility)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f --max-time 5 http://localhost:${FASTMCP_PORT}/ || exit 1

# Expose port (will be set by smithery.ai via PORT env var)
EXPOSE ${FASTMCP_PORT}

# Default command for MCP server (smithery.ai compatible)
CMD ["python", "src/main.py"]
