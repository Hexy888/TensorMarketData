#!/bin/bash

# TensorMarketData Monitoring Check Script
# Usage: ./monitor.sh

set -e

# Configuration
APP_URL="http://localhost:8000"
METRICS_URL="http://localhost:9090"
DOMAIN="tensormarketdata.com"

echo "============================================"
echo "  TensorMarketData Monitoring Check"
echo "============================================"
echo ""

# Check application health
check_health() {
    echo "Checking application health..."
    
    if curl -sf "${APP_URL}/health" > /dev/null 2>&1; then
        echo "✓ Application is healthy"
        return 0
    else
        echo "✗ Application health check failed"
        return 1
    fi
}

# Check API endpoints
check_api() {
    echo ""
    echo "Checking API endpoints..."
    
    ENDPOINTS=("/api/health" "/api/v1/status")
    
    for endpoint in "${ENDPOINTS[@]}"; do
        if curl -sf "${APP_URL}${endpoint}" > /dev/null 2>&1; then
            echo "✓ ${endpoint} - OK"
        else
            echo "✗ ${endpoint} - FAILED"
        fi
    done
}

# Check Prometheus metrics
check_metrics() {
    echo ""
    echo "Checking Prometheus metrics..."
    
    if curl -sf "${METRICS_URL}/api/v1/query?query=up" > /dev/null 2>&1; then
        echo "✓ Prometheus is running"
        
        # Get app metrics
        RESPONSE=$(curl -sf "${METRICS_URL}/api/v1/query?query=up%7Bjob%3D%22tensormarketdata%22%7D" 2>/dev/null)
        if echo "$RESPONSE" | grep -q '"status":"success"'; then
            echo "✓ TensorMarketData metrics available"
        fi
    else
        echo "✗ Prometheus is not accessible"
    fi
}

# Check SSL certificate (if available)
check_ssl() {
    echo ""
    echo "Checking SSL certificate..."
    
    EXPIRY_DATE=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN":443 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null || echo "notAfter=Unknown")
    
    if [ "$EXPIRY_DATE" != "notAfter=Unknown" ]; then
        echo "✓ SSL certificate is configured"
        echo "  Expires: ${EXPIRY_DATE#notAfter=}"
    else
        echo "⚠ SSL certificate check skipped (domain may not be accessible)"
    fi
}

# Check Docker containers
check_docker() {
    echo ""
    echo "Checking Docker containers..."
    
    CONTAINERS=$(docker-compose ps -q 2>/dev/null || echo "")
    
    if [ -n "$CONTAINERS" ]; then
        RUNNING=$(docker-compose ps --filter "status=running" -q 2>/dev/null | wc -l)
        TOTAL=$(echo "$CONTAINERS" | wc -l)
        echo "✓ $RUNNING/$TOTAL containers running"
    else
        echo "⚠ No containers found"
    fi
}

# Check logs for errors
check_logs() {
    echo ""
    echo "Checking recent errors in logs..."
    
    ERRORS=$(docker-compose logs --tail=100 2>&1 | grep -i "error" | tail -5 || echo "")
    
    if [ -n "$ERRORS" ]; then
        echo "⚠ Recent errors found:"
        echo "$ERRORS"
    else
        echo "✓ No recent errors in logs"
    fi
}

# Main monitoring check
main() {
    check_health || exit 1
    check_api
    check_metrics
    check_ssl
    check_docker
    check_logs
    
    echo ""
    echo "============================================"
    echo "  Monitoring check complete"
    echo "============================================"
}

main
