# GEMINI.md: Nara Market FastMCP 2.0 Server

## Project Overview

This project is a **FastMCP 2.0 server** designed to provide a unified and simplified interface for accessing data from the **Korean Public Procurement Service (나라장터 G2B)**. It acts as a middleware layer, consolidating multiple complex government APIs into a consistent set of tools that can be easily consumed by other applications, including AI agents.

The server is built with Python 3.11 and is designed for production use, with a strong focus on cloud deployment via Docker and the `smithery.ai` platform.

### Key Technologies

*   **Backend:** Python 3.11
*   **Framework:** FastMCP 2.0
*   **API Communication:** `requests`
*   **Web Server (for HTTP/SSE):** `uvicorn` and `starlette`
*   **Data Processing:** `pandas`
*   **Containerization:** Docker
*   **Deployment:** Smithery.ai

### Architecture

The application is architected around the FastMCP framework, which exposes Python functions as "tools" that can be called remotely.

*   **`src/main.py`**: The main entry point. It initializes the FastMCP server and registers all the available tools, including basic crawlers, enhanced OpenAPI-based tools, and AI-friendly simplified functions.
*   **`src/tools/`**: This directory contains the core business logic, separated into different toolsets:
    *   `naramarket.py`: Implements the original, basic crawling functions.
    *   `enhanced_tools.py`: Provides more sophisticated, parameterized tools that wrap the underlying government OpenAPI specifications.
    *   `openapi_tools.py`: Contains helpers for interacting with the `openapi.yaml` specification.
*   **`src/core/`**: Contains the supporting modules:
    *   `config.py`: Manages all configuration from environment variables (`.env` file) or `smithery.ai` deployment settings. It is the central place for API keys and other constants.
    *   `client.py` (inferred): Handles the low-level HTTP requests to the external government APIs.
*   **`openapi.yaml`**: A full OpenAPI 3.0 specification that defines the available government API endpoints, which the server's tools are built upon.

## Building and Running

The project is designed to be run either locally for development, or as a Docker container for production.

### Prerequisites

*   Python 3.10+
*   Docker (for containerized deployment)
*   An API key for the Nara Market service, obtained from [data.go.kr](https://www.data.go.kr/).

### Local Development

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure API Key:**
    Create a `.env` file in the project root and add your API key:
    ```env
    NARAMARKET_SERVICE_KEY=your-service-key-here
    ```

3.  **Run the Server:**
    *   **STDIO Mode (for local clients/testing):**
        ```bash
        python -m src.main
        ```
    *   **HTTP Mode (for web-based clients):**
        ```bash
        export FASTMCP_TRANSPORT=http
        export FASTMCP_PORT=8000
        python -m src.main
        ```

### Docker Execution

1.  **Build the Docker Image:**
    ```bash
    docker build -t naramarket-mcp .
    ```

2.  **Run the Container:**
    ```bash
    docker run --rm \
      -e NARAMARKET_SERVICE_KEY=your-api-key \
      -p 8000:8000 \
      naramarket-mcp
    ```

### Deployment (smithery.ai)

The project is pre-configured for one-click deployment to `smithery.ai`.

1.  **Set the `NARAMARKET_SERVICE_KEY` secret** in your `smithery.ai` project dashboard.
2.  **Run the deployment script:**
    ```bash
    ./deploy.sh
    ```
    This script handles validation, local testing, and deployment.

## Development Conventions

*   **Code Style:** The project uses **Black** for code formatting and **Flake8** for linting.
*   **Type Checking:** **Mypy** is used for static type analysis. Type hints are mandatory.
*   **Testing:**
    *   Unit tests are located in the `tests/` directory and can be run with `pytest`.
    *   The `test-api.sh` script provides a quick way to perform integration tests against a running HTTP server instance.
*   **Dependencies:** Python dependencies are managed in `requirements.txt` and defined in `pyproject.toml`.
*   **Documentation:** The server includes self-documenting features through MCP prompts and resources (`workflow_guide`, `api_parameter_requirements`, etc.), which provide runtime guidance on how to use the tools.
