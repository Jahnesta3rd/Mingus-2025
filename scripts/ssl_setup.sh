#!/bin/bash

# MINGUS SSL Setup Script
# Comprehensive SSL/HTTPS implementation for financial wellness application
# Target: SSL Labs Grade A+ | Banking-Grade Security

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=""
EMAIL=""
PLATFORM=""
CERTBOT_PATH="/usr/bin/certbot"
NGINX_PATH="/etc/nginx"
SSL_PATH="/etc/nginx/ssl"
WEBROOT_PATH="/var/www/html"

# Logging
LOG_FILE="/var/log/mingus-ssl-setup.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        error "Cannot determine OS"
    fi
    
    log "Detected OS: $OS $VER"
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        error "Nginx is not installed. Please install nginx first."
    fi
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        warn "Certbot is not installed. Installing..."
        install_certbot
    fi
    
    # Check if openssl is installed
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is not installed"
    fi
    
    log "System requirements check passed"
}

# Install certbot
install_certbot() {
    log "Installing certbot..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt update
        apt install -y certbot python3-certbot-nginx
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"RHEL"* ]]; then
        yum install -y certbot python3-certbot-nginx
    else
        error "Unsupported OS for automatic certbot installation"
    fi
    
    log "Certbot installed successfully"
}

# Get user input
get_user_input() {
    echo -e "${BLUE}=== MINGUS SSL Setup ===${NC}"
    echo
    
    # Get domain
    while [[ -z "$DOMAIN" ]]; do
        read -p "Enter your domain name (e.g., yourdomain.com): " DOMAIN
        if [[ -z "$DOMAIN" ]]; then
            echo -e "${RED}Domain name is required${NC}"
        fi
    done
    
    # Get email
    while [[ -z "$EMAIL" ]]; do
        read -p "Enter your email address for SSL notifications: " EMAIL
        if [[ -z "$EMAIL" ]]; then
            echo -e "${RED}Email address is required${NC}"
        fi
    done
    
    # Get platform
    echo "Select your hosting platform:"
    echo "1) Digital Ocean App Platform"
    echo "2) VPS with Nginx (Manual Setup)"
    echo "3) Cloudflare + Any Hosting"
    echo "4) Other (Custom Setup)"
    
    while [[ -z "$PLATFORM" ]]; do
        read -p "Enter your choice (1-4): " PLATFORM
        case $PLATFORM in
            1) PLATFORM="digitalocean" ;;
            2) PLATFORM="vps" ;;
            3) PLATFORM="cloudflare" ;;
            4) PLATFORM="custom" ;;
            *) 
                echo -e "${RED}Invalid choice. Please enter 1-4.${NC}"
                PLATFORM=""
                ;;
        esac
    done
    
    log "Configuration: Domain=$DOMAIN, Email=$EMAIL, Platform=$PLATFORM"
}

# Create SSL directories
create_ssl_directories() {
    log "Creating SSL directories..."
    
    mkdir -p "$SSL_PATH"
    chmod 700 "$SSL_PATH"
    
    log "SSL directories created"
}

# Generate Let's Encrypt certificate
generate_certificate() {
    log "Generating Let's Encrypt certificate for $DOMAIN..."
    
    # Stop nginx temporarily
    systemctl stop nginx
    
    # Generate certificate
    certbot certonly \
        --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN,www.$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log "Certificate generated successfully"
        
        # Create symlinks
        ln -sf /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$SSL_PATH/certificate.crt"
        ln -sf /etc/letsencrypt/live/$DOMAIN/privkey.pem "$SSL_PATH/private.key"
        ln -sf /etc/letsencrypt/live/$DOMAIN/chain.pem "$SSL_PATH/ca_bundle.crt"
        
        # Set proper permissions
        chmod 644 "$SSL_PATH/certificate.crt"
        chmod 600 "$SSL_PATH/private.key"
        chmod 644 "$SSL_PATH/ca_bundle.crt"
        
        log "Certificate files linked and permissions set"
    else
        error "Failed to generate certificate"
    fi
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Backup existing configuration
    if [[ -f "$NGINX_PATH/nginx.conf" ]]; then
        cp "$NGINX_PATH/nginx.conf" "$NGINX_PATH/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
        log "Existing nginx.conf backed up"
    fi
    
    # Copy SSL configuration
    if [[ -f "deployment/nginx/nginx-ssl.conf" ]]; then
        cp "deployment/nginx/nginx-ssl.conf" "$NGINX_PATH/sites-available/mingus-ssl"
        
        # Replace placeholders
        sed -i "s/your-domain.com/$DOMAIN/g" "$NGINX_PATH/sites-available/mingus-ssl"
        
        # Enable site
        ln -sf "$NGINX_PATH/sites-available/mingus-ssl" "$NGINX_PATH/sites-enabled/"
        
        log "Nginx SSL configuration installed"
    else
        warn "SSL configuration file not found, creating basic configuration..."
        create_basic_nginx_config
    fi
    
    # Test configuration
    if nginx -t; then
        log "Nginx configuration test passed"
    else
        error "Nginx configuration test failed"
    fi
}

# Create basic Nginx configuration
create_basic_nginx_config() {
    cat > "$NGINX_PATH/sites-available/mingus-ssl" << EOF
# MINGUS Application - Basic SSL Configuration
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration
    ssl_certificate $SSL_PATH/certificate.crt;
    ssl_certificate_key $SSL_PATH/private.key;
    ssl_trusted_certificate $SSL_PATH/ca_bundle.crt;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Root directory
    root /var/www/mingus;
    index index.html;
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Main location
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
    
    # Enable site
    ln -sf "$NGINX_PATH/sites-available/mingus-ssl" "$NGINX_PATH/sites-enabled/"
}

# Setup automatic renewal
setup_auto_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/mingus-ssl-renew << 'EOF'
#!/bin/bash
# MINGUS SSL Certificate Renewal Script

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> /var/log/mingus-ssl-renewal.log
}

log "Starting certificate renewal check..."

# Renew certificates
if certbot renew --quiet; then
    log "Certificates renewed successfully"
    
    # Reload nginx
    if systemctl reload nginx; then
        log "Nginx reloaded successfully"
    else
        log "ERROR: Failed to reload nginx"
        exit 1
    fi
else
    log "ERROR: Certificate renewal failed"
    exit 1
fi

log "Certificate renewal completed"
EOF
    
    chmod +x /usr/local/bin/mingus-ssl-renew
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/local/bin/mingus-ssl-renew") | crontab -
    
    log "Automatic renewal configured (daily at 12:00 PM)"
}

# Test SSL configuration
test_ssl() {
    log "Testing SSL configuration..."
    
    # Test certificate
    if openssl x509 -in "$SSL_PATH/certificate.crt" -text -noout > /dev/null 2>&1; then
        log "Certificate validation passed"
    else
        error "Certificate validation failed"
    fi
    
    # Test nginx configuration
    if nginx -t; then
        log "Nginx configuration test passed"
    else
        error "Nginx configuration test failed"
    fi
    
    # Start nginx
    if systemctl start nginx; then
        log "Nginx started successfully"
    else
        error "Failed to start nginx"
    fi
    
    # Test HTTPS connection
    sleep 2
    if curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" | grep -q "200\|301\|302"; then
        log "HTTPS connection test passed"
    else
        warn "HTTPS connection test failed (this might be normal if the site is not fully configured)"
    fi
}

# Setup SSL monitoring
setup_monitoring() {
    log "Setting up SSL monitoring..."
    
    # Create monitoring script
    cat > /usr/local/bin/mingus-ssl-monitor << 'EOF'
#!/bin/bash
# MINGUS SSL Monitoring Script

DOMAIN=""
SSL_PATH="/etc/nginx/ssl"
LOG_FILE="/var/log/mingus-ssl-monitor.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check certificate expiry
check_expiry() {
    if [[ -f "$SSL_PATH/certificate.crt" ]]; then
        expiry_date=$(openssl x509 -in "$SSL_PATH/certificate.crt" -noout -enddate | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry_date" +%s)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [[ $days_until_expiry -le 30 ]]; then
            log "WARNING: Certificate expires in $days_until_expiry days"
            # Send alert (implement your alert mechanism here)
        else
            log "Certificate expires in $days_until_expiry days"
        fi
    else
        log "ERROR: Certificate file not found"
    fi
}

# Check SSL Labs grade
check_ssl_labs() {
    # This would require the SSL Labs API
    # For now, just log that we would check it
    log "SSL Labs grade check would run here"
}

# Main monitoring
log "Starting SSL monitoring..."
check_expiry
check_ssl_labs
log "SSL monitoring completed"
EOF
    
    chmod +x /usr/local/bin/mingus-ssl-monitor
    
    # Add to crontab (run every 6 hours)
    (crontab -l 2>/dev/null; echo "0 */6 * * * /usr/local/bin/mingus-ssl-monitor") | crontab -
    
    log "SSL monitoring configured (every 6 hours)"
}

# Platform-specific setup
setup_platform() {
    case $PLATFORM in
        "digitalocean")
            setup_digitalocean
            ;;
        "vps")
            setup_vps
            ;;
        "cloudflare")
            setup_cloudflare
            ;;
        "custom")
            setup_custom
            ;;
    esac
}

# Digital Ocean setup
setup_digitalocean() {
    log "Setting up Digital Ocean App Platform configuration..."
    
    # Create app-spec.yaml
    cat > app-spec.yaml << EOF
name: mingus-app
region: nyc
services:
  - name: mingus-web
    source_dir: /
    github:
      repo: your-username/mingus-app
      branch: main
    run_command: gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 backend.app:app
    environment_slug: python
    instance_count: 2
    instance_size_slug: basic-xxs
    autoscaling:
      min_instance_count: 2
      max_instance_count: 10
      metrics:
        cpu_percent: 70
        memory_percent: 80
    health_check:
      http_path: /health
      initial_delay_seconds: 30
      interval_seconds: 30
      timeout_seconds: 10
      success_threshold: 1
      failure_threshold: 3
    envs:
      - key: FLASK_ENV
        value: production
      - key: SSL_ENABLED
        value: true
      - key: FORCE_HTTPS
        value: true
      - key: HSTS_ENABLED
        value: true
      - key: SESSION_COOKIE_SECURE
        value: true
      - key: SESSION_COOKIE_HTTPONLY
        value: true
      - key: SESSION_COOKIE_SAMESITE
        value: Strict

domains:
  - domain: $DOMAIN
    type: PRIMARY
    ssl:
      type: LETS_ENCRYPT
      redirect_http: true

ssl:
  enabled: true
  force_https: true
  auto_ssl: true
  certificate_provider: letsencrypt
  certificate_email: $EMAIL
EOF
    
    log "Digital Ocean app-spec.yaml created"
    info "To deploy: doctl apps create --spec app-spec.yaml"
}

# VPS setup
setup_vps() {
    log "VPS setup completed (manual configuration)"
    info "SSL certificate and Nginx configuration have been set up"
    info "Make sure to:"
    info "1. Update DNS records to point to this server"
    info "2. Configure your application to run on port 5001"
    info "3. Test the SSL configuration"
}

# Cloudflare setup
setup_cloudflare() {
    log "Setting up Cloudflare configuration..."
    
    info "To complete Cloudflare setup:"
    info "1. Sign up for Cloudflare (free plan)"
    info "2. Add your domain: $DOMAIN"
    info "3. Update nameservers at your registrar"
    info "4. Configure SSL/TLS settings:"
    info "   - Set SSL/TLS encryption mode to 'Full (strict)'"
    info "   - Enable 'Always Use HTTPS'"
    info "   - Enable 'HSTS' with max-age 31536000"
    info "   - Enable 'TLS 1.3'"
    info "   - Enable 'Opportunistic Encryption'"
}

# Custom setup
setup_custom() {
    log "Custom setup mode"
    info "SSL certificate and basic configuration have been set up"
    info "You may need to customize the configuration for your specific hosting platform"
}

# Main execution
main() {
    log "Starting MINGUS SSL setup..."
    
    check_root
    check_requirements
    get_user_input
    create_ssl_directories
    
    case $PLATFORM in
        "digitalocean")
            setup_digitalocean
            ;;
        "vps")
            generate_certificate
            configure_nginx
            setup_auto_renewal
            test_ssl
            setup_monitoring
            setup_vps
            ;;
        "cloudflare")
            setup_cloudflare
            ;;
        "custom")
            generate_certificate
            configure_nginx
            setup_auto_renewal
            test_ssl
            setup_monitoring
            setup_custom
            ;;
    esac
    
    log "MINGUS SSL setup completed successfully!"
    log "Log file: $LOG_FILE"
    
    echo
    echo -e "${GREEN}=== SSL Setup Summary ===${NC}"
    echo -e "Domain: ${BLUE}$DOMAIN${NC}"
    echo -e "Platform: ${BLUE}$PLATFORM${NC}"
    echo -e "Email: ${BLUE}$EMAIL${NC}"
    echo
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Update your DNS records"
    echo "2. Test your SSL configuration"
    echo "3. Monitor certificate expiry"
    echo "4. Check SSL Labs grade"
    echo
    echo -e "${YELLOW}SSL Labs Test:${NC} https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    echo -e "${YELLOW}Certificate Info:${NC} https://$DOMAIN"
}

# Run main function
main "$@"
