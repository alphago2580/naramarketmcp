#!/bin/bash

# Naramarket MCP Server Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_requirements() {
    log "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    success "Requirements check passed"
}

# Setup environment file
setup_environment() {
    log "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$SCRIPT_DIR/.env.example" ]; then
            cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
            warning "Created .env file from .env.example. Please configure it with your settings."
        else
            error ".env.example file not found. Cannot create environment file."
        fi
    fi
    
    # Check if required environment variables are set
    if grep -q "your_naramarket_service_key_here" "$ENV_FILE"; then
        warning "Please update NARAMARKET_SERVICE_KEY in $ENV_FILE"
    fi
    
    if grep -q "your-super-secret-jwt-key-change-this-in-production" "$ENV_FILE"; then
        warning "Please update JWT_SECRET_KEY in $ENV_FILE"
    fi
    
    success "Environment setup completed"
}

# Create required directories
create_directories() {
    log "Creating required directories..."
    
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/logs/nginx"
    
    success "Directories created"
}

# Build and start services
deploy() {
    log "Building and starting services..."
    
    cd "$SCRIPT_DIR"
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build custom images
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Services started successfully"
}

# Check service health
check_health() {
    log "Checking service health..."
    
    # Wait for services to start
    sleep 10
    
    # Check main application
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        success "Main application is healthy"
    else
        error "Main application health check failed"
    fi
    
    # Check Redis
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        success "Redis is healthy"
    else
        warning "Redis health check failed"
    fi
}

# Show service status
show_status() {
    log "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    log "\nService URLs:"
    echo "  - Main API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Health Check: http://localhost:8000/api/v1/health"
    echo "  - Grafana: http://localhost:3000 (admin/admin123)"
    echo "  - Prometheus: http://localhost:9090"
}

# Stop services
stop() {
    log "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" down
    success "Services stopped"
}

# Clean up
clean() {
    log "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down -v
    docker system prune -f
    success "Cleanup completed"
}

# Show logs
logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Main script
main() {
    case "${1:-deploy}" in
        "deploy")
            check_requirements
            setup_environment
            create_directories
            deploy
            check_health
            show_status
            ;;
        "stop")
            stop
            ;;
        "restart")
            stop
            sleep 5
            deploy
            check_health
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            logs "${2:-}"
            ;;
        "clean")
            clean
            ;;
        "health")
            check_health
            ;;
        *)
            echo "Usage: $0 {deploy|stop|restart|status|logs [service]|clean|health}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Deploy all services (default)"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  status   - Show service status"
            echo "  logs     - Show logs (optional: specify service name)"
            echo "  clean    - Stop services and clean up volumes"
            echo "  health   - Check service health"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"