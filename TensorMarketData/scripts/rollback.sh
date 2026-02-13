#!/bin/bash

# TensorMarketData Rollback Script
# Usage: ./rollback.sh [version]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/../backups"

echo "============================================"
echo "  TensorMarketData Rollback"
echo "============================================"

# List available backups
list_backups() {
    echo ""
    echo "Available backups:"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lt "$BACKUP_DIR" | head -10
    else
        echo "No backups found"
    fi
}

# Rollback to previous version
rollback() {
    local VERSION=${1:-"latest"}
    
    echo "Rolling back to: $VERSION"
    
    # Stop current services
    echo "Stopping services..."
    docker-compose down
    
    # If specific version requested, restore env
    if [ "$VERSION" != "latest" ] && [ -f "$BACKUP_DIR/$VERSION/.env" ]; then
        echo "Restoring environment variables..."
        cp "$BACKUP_DIR/$VERSION/.env" .env.production
    fi
    
    # Pull previous version if specified
    if [ "$VERSION" != "latest" ]; then
        echo "Checking out previous version..."
        git checkout "$VERSION" 2>/dev/null || echo "Version not in git history"
    fi
    
    # Rebuild and start
    echo "Rebuilding and starting services..."
    docker-compose up -d
    
    # Health check
    echo "Running health check..."
    sleep 10
    
    if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
        echo "✓ Rollback successful"
        docker-compose ps
    else
        echo "✗ Rollback may have failed - check logs"
        docker-compose logs --tail=50
    fi
}

# Show usage
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  list          List available backups"
    echo "  rollback [v]  Rollback to specific version (default: previous commit)"
    echo "  help          Show this help message"
    echo ""
}

# Main
case "${1:-help}" in
    list)
        list_backups
        ;;
    rollback)
        rollback "${2:-}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
