# 🚀 Mingus Meme Splash Page - Production Deployment Guide

This comprehensive guide will walk you through deploying the Mingus Meme Splash Page to production environments including Heroku, AWS, and DigitalOcean.

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] Git installed and configured
- [ ] Docker installed (for containerized deployment)
- [ ] AWS account (for S3 and CloudFront)
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (Let's Encrypt recommended)

## 🐳 Docker Deployment (Recommended)

### 1. Local Development Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd mingus-meme-app

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env

# Start development environment
docker-compose -f docker-compose.dev.yml up --build
```

### 2. Production Deployment

```bash
# Build and start production containers
docker-compose up --build -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f mingus-meme-app
```

## ☁️ Heroku Deployment

### 1. Prepare for Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY="your-super-secret-key"
heroku config:set FLASK_ENV=production
heroku config:set AWS_ACCESS_KEY_ID="your-aws-key"
heroku config:set AWS_SECRET_ACCESS_KEY="your-aws-secret"
heroku config:set AWS_S3_BUCKET="your-bucket-name"
```

### 2. Deploy to Heroku

```bash
# Add Heroku remote
git remote add heroku https://git.heroku.com/your-app-name.git

# Deploy
git push heroku main

# Run database migrations
heroku run python migrations/migrate.py

# Open app
heroku open
```

### 3. Heroku Add-ons

```bash
# Add Redis for caching
heroku addons:create heroku-redis:hobby-dev

# Add monitoring
heroku addons:create newrelic:wayne

# Add error tracking
heroku addons:create sentry:sentry
```

## 🌐 AWS Deployment

### 1. EC2 Instance Setup

```bash
# Launch EC2 instance (Ubuntu 20.04 LTS)
# Instance type: t3.medium or larger
# Security groups: HTTP (80), HTTPS (443), SSH (22)

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Application Deployment

```bash
# Clone repository
git clone <your-repo-url>
cd mingus-meme-app

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env

# Start application
docker-compose up -d

# Set up SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

### 3. AWS S3 Setup

```bash
# Create S3 bucket
aws s3 mb s3://your-bucket-name

# Configure bucket policy
aws s3api put-bucket-policy --bucket your-bucket-name --policy file://s3-policy.json

# Set up CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

## 🐙 DigitalOcean Deployment

### 1. Droplet Setup

```bash
# Create Droplet (Ubuntu 20.04, 2GB RAM minimum)
# Add SSH key during creation

# Connect to droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Application Deployment

```bash
# Clone and setup (same as AWS)
git clone <your-repo-url>
cd mingus-meme-app
cp env.example .env
nano .env

# Start application
docker-compose up -d

# Setup SSL
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=sqlite:///app/mingus_memes.db

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_S3_REGION=us-east-1

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1

# Monitoring
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-new-relic-key
```

## 📊 Database Setup

### 1. Run Migrations

```bash
# Local development
python migrations/migrate.py

# Production (Docker)
docker-compose exec mingus-meme-app python migrations/migrate.py

# Heroku
heroku run python migrations/migrate.py
```

### 2. Verify Database

```bash
# Check database health
python migrations/migrate.py --check-health

# View database stats
sqlite3 mingus_memes.db "SELECT COUNT(*) FROM memes;"
```

## 🖼️ Image Storage Setup

### 1. AWS S3 Configuration

```bash
# Create S3 bucket
aws s3 mb s3://mingus-memes-production

# Set bucket policy for public read
aws s3api put-bucket-policy --bucket mingus-memes-production --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::mingus-memes-production/memes/*"
    }
  ]
}'
```

### 2. CloudFront CDN Setup

```bash
# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "mingus-memes-cdn",
  "Comment": "Mingus Meme CDN",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-mingus-memes-production",
        "DomainName": "mingus-memes-production.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-mingus-memes-production",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "Enabled": true
}'
```

## 📈 Monitoring Setup

### 1. Sentry Error Tracking

```bash
# Sign up at https://sentry.io
# Create new project
# Copy DSN to environment variables

# Test error tracking
curl -X POST https://your-app.com/api/test-error
```

### 2. New Relic Performance Monitoring

```bash
# Sign up at https://newrelic.com
# Create new application
# Copy license key to environment variables

# Verify monitoring
curl https://your-app.com/health
```

## 🔒 Security Configuration

### 1. SSL Certificate

```bash
# Using Let's Encrypt
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 2. Firewall Setup

```bash
# UFW (Ubuntu)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Fail2ban
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificate obtained
- [ ] Domain DNS configured
- [ ] Monitoring services set up
- [ ] Backup strategy implemented

### Post-Deployment

- [ ] Application accessible via HTTPS
- [ ] Database migrations applied
- [ ] Image uploads working
- [ ] Analytics tracking functional
- [ ] Error monitoring active
- [ ] Performance monitoring active
- [ ] Backup system tested

## 🔄 Continuous Deployment

### GitHub Actions (Optional)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "your-app-name"
          heroku_email: "your-email@example.com"
```

## 📞 Support

If you encounter issues during deployment:

1. Check the troubleshooting guide
2. Review application logs
3. Verify environment variables
4. Test database connectivity
5. Check AWS service status

For additional help, refer to the troubleshooting section or create an issue in the repository.
