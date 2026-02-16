# TensorMarketData Deployment Guide

**Domain:** tensormarketdata.com  
**Application:** B2B Data Marketplace for AI Agents  
**Tech Stack:** FastAPI, Python 3.11, Supabase, Docker, Nginx

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [SSL/HTTPS Setup](#sslhttps-setup)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring](#monitoring)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Docker
brew install docker
docker --version  # Should be 20.x+

# Docker Compose
brew install docker-compose
docker-compose --version  # Should be 2.x+

# Git
brew install git

# Optionally: kubectl, terraform (for cloud deployments)
```

### Domain Requirements

- **Domain:** tensormarketdata.com
- **DNS:** A record pointing to server IP
- **SSL:** Let's Encrypt (free) or commercial certificate

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/tensormarketdata.git
cd tensormarketdata

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.production.example .env.production
```

### 2. Local Development

```bash
# Start with Docker Compose (development)
docker-compose -f docker-compose.dev.yml up -d

# Or run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access

- **Local:** http://localhost:8000
- **Health:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs

---

## Production Deployment

### Option 1: VPS Server (Recommended)

#### Server Setup

```bash
# SSH into your server
ssh deploy@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment directory
sudo mkdir -p /opt/tensormarketdata
sudo chown $USER:$USER /opt/tensormarketdata
cd /opt/tensormarketdata
```

#### Deploy Application

```bash
# Clone repository
git clone https://github.com/your-org/tensormarketdata.git .
git checkout main

# Configure environment
cp .env.production.example .env.production
nano .env.production  # Edit with your values

# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

#### Setup SSL (Let's Encrypt)

```bash
# Stop services temporarily
docker-compose stop nginx

# Run SSL setup
chmod +x scripts/setup-ssl.sh
./scripts/setup-ssl.sh admin@tensormarketdata.com

# Restart services
docker-compose start nginx
```

### Option 2: Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Configure environment
railway variables set SUPABASE_URL=your_url
railway variables set SUPABASE_KEY=your_key
railway variables set STRIPE_SECRET_KEY=your_key

# Deploy
railway up
```

### Option 3: Render

1. Connect GitHub repository
2. Create Web Service
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** Add from `.env.production.example`

---

## Environment Configuration

### Required Variables

```bash
# .env.production

# Environment
ENV=production
DEBUG=false

# Supabase (from your Supabase dashboard)
SUPABASE_URL=https://nsuzvbjrdrzhmdjfuzle.supabase.co
SUPABASE_KEY=your_service_role_key

# Database (optional - can use Supabase URL above)
DATABASE_URL=postgresql+asyncpg://...

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY_HEADER=X-API-Key

# Security (generate: openssl rand -base64 32)
SECRET_KEY=your-32-character-secret-key

# Stripe (from Stripe dashboard)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# CORS
ALLOWED_ORIGINS=https://tensormarketdata.com
```

### Generating Secrets

```bash
# Generate secure secret key
openssl rand -base64 32

# Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Free)

```bash
# Stop nginx temporarily
docker-compose stop nginx

# Run certbot
docker run --rm \
    -v $(pwd)/ssl:/etc/letsencrypt/live/tensormarketdata.com \
    -v $(pwd)/ssl:/var/lib/letsencrypt \
    -p 80:80 \
    certbot/certbot certonly \
    --standalone \
    --email admin@tensormarketdata.com \
    --agree-tos \
    -d tensormarketdata.com \
    -d www.tensormarketdata.com

# Copy certificates
cp ssl/fullchain.pem ssl/cert.pem
cp ssl/privkey.pem ssl/key.pem

# Start nginx
docker-compose start nginx
```

### Manual Certificate Installation

```bash
# Copy certificate files to ssl/
cp your_domain.crt ssl/cert.pem
cp your_domain.key ssl/key.pem

# Restart nginx
docker-compose restart nginx
```

### Verify SSL

```bash
# Check certificate
openssl s_client -connect tensormarketdata.com:443 -servername tensormarketdata.com

# Test SSL configuration
curl -I https://tensormarketdata.com
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci-cd.yml` file configures:

1. **Test Job:** Runs linters, type checking, and tests
2. **Build Job:** Builds and pushes Docker image
3. **Deploy Jobs:**
   - Railway deployment (automatic)
   - VPS deployment (via SSH)
4. **Notification:** Reports deployment status

### Setup GitHub Actions

```bash
# Create GitHub repository
gh repo create tensormarketdata --public --source=. --push

# Add secrets (GitHub → Settings → Secrets and variables → Actions)
gh secret set RAILWAY_TOKEN -b"your_railway_token"
gh secret set SERVER_HOST -b"your_server_ip"
gh secret set SSH_PRIVATE_KEY -b"$(cat ~/.ssh/id_rsa)"
```

### Manual Trigger

```bash
# Trigger workflow manually
gh workflow run ci-cd.yml -f environment=production
```

---

## Monitoring

### Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Application | https://tensormarketdata.com | Main app |
| Health | https://tensormarketdata.com/health | Health check |
| Prometheus | http://localhost:9090 | Metrics |
| cAdvisor | http://localhost:8080 | Container metrics |

### Health Checks

```bash
# Run monitoring check
./scripts/monitor.sh

# Check individual endpoints
curl https://tensormarketdata.com/health
curl https://tensormarketdata.com/metrics
```

### Key Metrics

- **Request rate:** `rate(http_requests_total[5m])`
- **Error rate:** `rate(http_requests_total{status=~"5.."}[5m])`
- **Latency:** `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Active users:** `sum(active_users)`

### Alerts (Prometheus)

Configure in `prometheus.rules.yml`:

```yaml
groups:
  - name: tensormarketdata
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

---

## Rollback Procedures

### Quick Rollback (Previous Version)

```bash
# Rollback to previous deployment
./scripts/rollback.sh

# List available backups
./scripts/rollback.sh list
```

### Manual Rollback

```bash
# Check previous git tag
git tag -l

# Checkout previous version
git checkout v1.0.0

# Rebuild and deploy
docker-compose down
docker-compose up -d --build
```

### Database Rollback

If database migration is needed:

```bash
# Supabase migrations (run via Supabase CLI)
supabase migration up

# Or manually apply rollback SQL
psql -f migrations/rollback_001.sql
```

---

## Troubleshooting

### Container Issues

```bash
# View logs
docker-compose logs -f app

# Check container status
docker-compose ps

# Restart container
docker-compose restart app

# View resource usage
docker stats
```

### Application Issues

```bash
# Check application logs
tail -f logs/app.log

# Test health endpoint
curl http://localhost:8000/health

# Check Python dependencies
pip list

# Rebuild container
docker-compose build --no-cache app
```

### SSL Issues

```bash
# Check certificate expiry
openssl x509 -enddate -noout -in ssl/cert.pem

# Renew Let's Encrypt certificate
./scripts/setup-ssl.sh admin@tensormarketdata.com

# Verify nginx config
docker-compose exec nginx nginx -t
```

### Performance Issues

```bash
# Check memory usage
docker stats

# View slow queries (Supabase)
# Check Supabase dashboard → Performance

# Check nginx logs
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

### Common Solutions

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check app container: `docker-compose logs app` |
| SSL certificate error | Renew: `./scripts/setup-ssl.sh` |
| Database connection failed | Verify `DATABASE_URL` in `.env.production` |
| CORS errors | Add domain to `ALLOWED_ORIGINS` |
| Memory issues | Scale down or add swap space |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (443)                       │
│              SSL Termination + Proxy                 │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼───────┐    ┌─────────▼─────────┐
│  Prometheus   │    │   FastAPI App     │
│   (9090)      │    │    (8000)         │
└───────────────┘    └─────────┬─────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼───────┐    ┌───────▼───────┐
            │   Supabase    │    │    Stripe     │
            │   Database    │    │   Payments    │
            └───────────────┘    └───────────────┘
```

---

## Support

- **Documentation:** `/docs` endpoint in app
- **Logs:** `docker-compose logs`
- **Health:** `/health` endpoint
- **Metrics:** `/metrics` endpoint

---

*Last Updated: 2024-01-15*  
*Version: 1.0.0*
