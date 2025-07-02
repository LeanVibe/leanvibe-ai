#!/bin/bash

# LeanVibe Services Management Script
# This script helps manage Docker Compose services for LeanVibe

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to check if docker-compose.yml exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml not found at $COMPOSE_FILE"
        exit 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting LeanVibe external services..."
    
    check_docker
    check_compose_file
    
    cd "$SCRIPT_DIR"
    docker-compose up -d neo4j chroma redis
    
    print_status "Waiting for services to be ready..."
    
    # Wait for Neo4j
    print_status "Checking Neo4j (http://localhost:7474)..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:7474 >/dev/null 2>&1; then
            print_success "Neo4j is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -eq 0 ]; then
        print_warning "Neo4j may not be fully ready yet"
    fi
    
    # Wait for Chroma
    print_status "Checking Chroma (http://localhost:8001)..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; then
            print_success "Chroma is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -eq 0 ]; then
        print_warning "Chroma may not be fully ready yet"
    fi
    
    # Wait for Redis
    print_status "Checking Redis (localhost:6379)..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if redis-cli -p 6379 ping >/dev/null 2>&1 || docker exec leanvibe-redis redis-cli ping >/dev/null 2>&1; then
            print_success "Redis is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -eq 0 ]; then
        print_warning "Redis may not be fully ready yet"
    fi
    
    print_success "All services started successfully!"
    print_status "Service URLs:"
    echo "  Neo4j:  http://localhost:7474 (username: neo4j, password: password123)"
    echo "  Chroma: http://localhost:8001"
    echo "  Redis:  localhost:6379"
}

# Function to stop services
stop_services() {
    print_status "Stopping LeanVibe external services..."
    
    check_compose_file
    cd "$SCRIPT_DIR"
    docker-compose down
    
    print_success "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_status "Restarting LeanVibe external services..."
    stop_services
    start_services
}

# Function to show service status
status_services() {
    print_status "Checking service status..."
    
    check_compose_file
    cd "$SCRIPT_DIR"
    docker-compose ps
    
    echo ""
    print_status "Service health checks:"
    
    # Check Neo4j
    if curl -f http://localhost:7474 >/dev/null 2>&1; then
        print_success "Neo4j is running (http://localhost:7474)"
    else
        print_error "Neo4j is not responding"
    fi
    
    # Check Chroma
    if curl -f http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; then
        print_success "Chroma is running (http://localhost:8001)"
    else
        print_error "Chroma is not responding"
    fi
    
    # Check Redis
    if redis-cli -p 6379 ping >/dev/null 2>&1 || docker exec leanvibe-redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis is running (localhost:6379)"
    else
        print_error "Redis is not responding"
    fi
}

# Function to show logs
show_logs() {
    service=${1:-}
    
    check_compose_file
    cd "$SCRIPT_DIR"
    
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        docker-compose logs -f "$service"
    else
        print_status "Showing logs for all services..."
        docker-compose logs -f
    fi
}

# Function to reset services (stop, remove volumes, start)
reset_services() {
    print_warning "This will stop services and remove all data. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Resetting services..."
        
        check_compose_file
        cd "$SCRIPT_DIR"
        docker-compose down -v
        docker-compose up -d neo4j chroma redis
        
        print_success "Services reset successfully!"
    else
        print_status "Reset cancelled."
    fi
}

# Function to show help
show_help() {
    echo "LeanVibe Services Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start     Start all external services (Neo4j, Chroma, Redis)"
    echo "  stop      Stop all external services"
    echo "  restart   Restart all external services"
    echo "  status    Show service status and health checks"
    echo "  logs      Show logs for all services or specific service"
    echo "  reset     Stop services and remove all data (destructive)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                 # Start all services"
    echo "  $0 logs neo4j           # Show Neo4j logs"
    echo "  $0 status               # Check service status"
    echo ""
}

# Main script logic
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    reset)
        reset_services
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        print_error "No command provided."
        echo ""
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac