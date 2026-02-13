#!/bin/bash

# TensorMarketData SSL Setup Script
# Usage: ./setup-ssl.sh email@example.com

set -e

DOMAIN="tensormarketdata.com"
EMAIL=${1:-"admin@tensormarketdata.com"}
SSL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../ssl"

echo "Setting up SSL for $DOMAIN"

# Create SSL directory
mkdir -p "$SSL_DIR"
mkdir -p /var/www/certbot

# Stop nginx if running
docker-compose stop nginx || true

# Run certbot to obtain certificate
docker run --rm \
    -v "$SSL_DIR:/etc/letsencrypt/live/$DOMAIN" \
    -v "/var/www/certbot:/var/www/certbot/data" \
    certbot/certbot \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot/data \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Copy certificates to expected location
cp "$SSL_DIR/fullchain.pem" "$SSL_DIR/cert.pem"
cp "$SSL_DIR/privkey.pem" "$SSL_DIR/key.pem"

echo "SSL certificates generated successfully!"
echo "Certificate: $SSL_DIR/cert.pem"
echo "Private Key: $SSL_DIR/key.pem"

# Restart nginx
docker-compose start nginx

echo "Nginx restarted with SSL"
