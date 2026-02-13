#!/bin/bash

# TensorMarketData Production Setup Script
# Run this on a fresh VPS server

set -e

echo "============================================"
echo "  TensorMarketData Server Setup"
echo "============================================"

# Variables
DOMAIN="tensormarketdata.com"
PROJECT_DIR="/opt/tensormarketdata"
APP_USER="deploy"

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker $APP_USER

# Install Docker Compose
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install utilities
echo "Installing utilities..."
apt-get install -y curl vim htop iotop git

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/ssl
mkdir -p $PROJECT_DIR/backups
mkdir -p /var/www/certbot
chown -R $APP_USER:$APP_USER $PROJECT_DIR

# Setup firewall
echo "Configuring firewall..."
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw --force enable

# Create swap file (for low memory servers)
echo "Creating swap file..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

# Create .env file template
echo "Creating environment template..."
cat > $PROJECT_DIR/.env.production << EOF
ENV=production
DEBUG=false

SUPABASE_URL=https://nsuzvbjrdrzhmdjfuzle.supabase.co
SUPABASE_KEY=your_supabase_key

API_HOST=0.0.0.0
API_PORT=8000

SECRET_KEY=$(openssl rand -base64 32)

STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret

ALLOWED_ORIGINS=https://$DOMAIN
EOF

echo ""
echo "============================================"
echo "  Server Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Clone repository: git clone <repo> $PROJECT_DIR"
echo "2. Configure SSL: cd $PROJECT_DIR && ./scripts/setup-ssl.sh"
echo "3. Deploy: cd $PROJECT_DIR && ./scripts/deploy.sh"
echo "4. Enable systemd service (optional)"
echo ""
echo "Files created:"
echo "  - $PROJECT_DIR/.env.production (template)"
echo ""
