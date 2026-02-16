#!/bin/bash

# TensorMarketData Deployment Script
# Usage: ./deploy.sh [environment]
# Environments: production, staging

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT=${1:-production}
DOMAIN="tensormarketdata.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check for required tools
check_requirements() {
    echo "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo_error "Docker Compose is not installed"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo_warning "curl is not installed - some health checks may fail"
    fi
    
    echo_status "All requirements met"
}

# Backup current deployment
backup() {
    if [ -f ".env.$ENVIRONMENT" ]; then
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        cp ".env.$ENVIRONMENT" "$BACKUP_DIR/.env"
        echo_status "Backup created at $BACKUP_DIR"
    fi
}

# Pull latest code
pull_code() {
    echo "Pulling latest code..."
    git pull origin main || echo_warning "Git pull failed - continuing with local code"
    echo_status "Code updated"
}

# Build Docker images
build_images() {
    echo "Building Docker images..."
    docker-compose -f docker-compose.yml build --no-cache
    echo_status "Images built"
}

# Start services
start_services() {
    echo "Starting services..."
    docker-compose -f docker-compose.yml down || true
    docker-compose -f docker-compose.yml up -d
    echo_status "Services started"
}

# Health check
health_check() {
    echo "Running health checks..."
    MAX_RETRIES=5
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
            echo_status "Application health check passed"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Waiting for application... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 5
    done
    
    echo_error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Show service status
show_status() {
    echo ""
    echo "=== Service Status ==="
    docker-compose -f docker-compose.yml ps
    echo ""
    echo "=== Logs (last 50 lines) ==="
    docker-compose -f docker-compose.yml logs --tail=50
}

# Main deployment flow
main() {
    echo "============================================"
    echo "  TensorMarketData Deployment"
    echo "  Environment: $ENVIRONMENT"
    echo "  Domain: $DOMAIN"
    echo "============================================"
    echo ""
    
    check_requirements
    backup
    pull_code
    build_images
    start_services
    
    if health_check; then
        show_status
        echo ""
        echo_status "Deployment successful!"
        echo "Application: https://$DOMAIN"
        echo "Health Check: https://$DOMAIN/health"
        echo "Metrics: http://localhost:9090"
    else
        echo_error "Deployment failed - check logs above"
        exit 1
    fi
}

# Run main function
main
