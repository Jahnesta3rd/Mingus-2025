# 🚨 **MINGUS Application - 403 Error Complete Troubleshooting Guide**

## 🔍 **Problem Summary**

Your Flask application deployed with Nginx is experiencing **403 Forbidden** errors due to several configuration issues:

1. **Missing SSL Certificates** ✅ **FIXED**
2. **Missing Environment Variables** ⚠️ **NEEDS ATTENTION**
3. **Port Configuration Conflicts** ✅ **RESOLVED**
4. **File Permission Issues** ✅ **RESOLVED**
5. **Missing Configuration Files** ✅ **RESOLVED**

## ✅ **Issues Already Resolved**

### **1. SSL Certificates Generated**
```bash
# SSL certificates created in deployment/nginx/ssl/
- certificate.crt (public certificate)
- private.key (private key with proper permissions)
```

### **2. Nginx Configuration Fixed**
```bash
# New production configuration created:
- deployment/nginx/nginx-production.conf
- Resolves port conflicts
- Proper proxy settings
- Comprehensive security headers
```

### **3. File Permissions Set**
```bash
# SSL files have correct permissions:
- private.key: 600 (owner read/write only)
- certificate.crt: 644 (owner read/write, others read)
```

## ⚠️ **Remaining Issues to Fix**

### **1. Environment Variables Missing**

**Problem**: No `.env` file with required secrets
**Solution**: Create `.env` file from template

```bash
# Copy the example file
cp env.production.example .env

# Edit .env with your actual values
nano .env
```

**Required Environment Variables**:
```bash
# Database
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password

# Application Secrets
SECRET_KEY=your_32+_character_random_string
JWT_SECRET_KEY=your_32+_character_random_string

# Email & External Services
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_email_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
RESEND_API_KEY=your_resend_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
STRIPE_SECRET_KEY=your_stripe_secret
```

### **2. Update Nginx Configuration**

**Problem**: Current nginx.conf may not match production config
**Solution**: Use the new production configuration

```bash
# Backup current config
cp deployment/nginx/nginx.conf deployment/nginx/nginx.conf.backup

# Use production config
cp deployment/nginx/nginx-production.conf deployment/nginx/nginx.conf
```

## 🚀 **Complete Deployment Steps**

### **Step 1: Environment Setup**
```bash
# 1. Create environment file
cp env.production.example .env

# 2. Edit with your actual values
nano .env

# 3. Verify file exists
ls -la .env
```

### **Step 2: SSL Certificate Verification**
```bash
# 1. Check SSL directory
ls -la deployment/nginx/ssl/

# 2. Verify permissions
ls -la deployment/nginx/ssl/private.key
ls -la deployment/nginx/ssl/certificate.crt

# Expected output:
# -rw------- private.key (600 permissions)
# -rw-r--r-- certificate.crt (644 permissions)
```

### **Step 3: Nginx Configuration Update**
```bash
# 1. Backup current config
cp deployment/nginx/nginx.conf deployment/nginx/nginx.conf.backup

# 2. Use production config
cp deployment/nginx/nginx-production.conf deployment/nginx/nginx.conf

# 3. Verify configuration
cat deployment/nginx/nginx.conf | head -20
```

### **Step 4: Docker Deployment**
```bash
# 1. Stop existing services (if running)
docker compose -f deployment/docker-compose.production.yml down

# 2. Build and start services
docker compose -f deployment/docker-compose.production.yml up --build -d

# 3. Check service status
docker compose -f deployment/docker-compose.production.yml ps

# 4. Check logs for errors
docker logs mingus_nginx_prod
docker logs mingus_web_prod
```

## 🔍 **Verification Steps**

### **1. Health Check**
```bash
# HTTP redirect to HTTPS
curl -I http://localhost/health

# HTTPS health check
curl -k https://localhost/health

# Expected: 200 OK
```

### **2. SSL Certificate Verification**
```bash
# Check SSL handshake
openssl s_client -connect localhost:443 -servername localhost

# Verify certificate
openssl x509 -in deployment/nginx/ssl/certificate.crt -text -noout
```

### **3. Security Headers Check**
```bash
# Check security headers
curl -k -I https://localhost/

# Expected headers:
# Strict-Transport-Security
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy
```

### **4. API Endpoint Test**
```bash
# Test API endpoint
curl -k https://localhost/api/health

# Test with rate limiting
for i in {1..15}; do curl -k https://localhost/api/health; done
```

## 🚨 **Common Error Solutions**

### **Error: 502 Bad Gateway**
```bash
# Cause: Flask app not responding
# Solution: Check web container
docker logs mingus_web_prod
docker exec mingus_web_prod curl -f http://localhost:5002/health
```

### **Error: 503 Service Unavailable**
```bash
# Cause: Rate limiting or service down
# Solution: Check rate limiting config
docker exec mingus_nginx_prod nginx -t
docker exec mingus_nginx_prod nginx -s reload
```

### **Error: SSL Handshake Failed**
```bash
# Cause: Certificate issues
# Solution: Regenerate certificates
cd deployment/nginx/ssl
rm -f *.crt *.key
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout private.key -out certificate.crt \
    -subj "/C=US/ST=State/L=City/O=MINGUS/CN=localhost"
chmod 600 private.key
chmod 644 certificate.crt
```

### **Error: Permission Denied**
```bash
# Cause: File permission issues
# Solution: Fix permissions
chmod 644 deployment/nginx/ssl/certificate.crt
chmod 600 deployment/nginx/ssl/private.key
chown -R 101:101 deployment/nginx/ssl/  # nginx user
```

## 📊 **Monitoring & Maintenance**

### **Daily Health Checks**
```bash
# 1. Service status
docker compose -f deployment/docker-compose.production.yml ps

# 2. Health endpoint
curl -k https://localhost/health

# 3. Error log monitoring
docker exec mingus_nginx_prod tail -f /var/log/nginx/error.log
```

### **Weekly Maintenance**
```bash
# 1. SSL certificate expiration
docker exec mingus_nginx_prod openssl x509 \
    -in /etc/nginx/ssl/certificate.crt -noout -dates

# 2. Configuration validation
docker exec mingus_nginx_prod nginx -t

# 3. Log rotation check
ls -la deployment/logs/nginx/
```

### **Monthly Tasks**
```bash
# 1. Update SSL certificates (if using Let's Encrypt)
# 2. Review access logs for security issues
# 3. Update Nginx and base images
# 4. Review rate limiting effectiveness
```

## 🔒 **Security Best Practices**

### **1. SSL Configuration**
- ✅ TLS 1.2+ only
- ✅ Strong cipher suites
- ✅ OCSP stapling enabled
- ✅ HSTS headers

### **2. Security Headers**
- ✅ X-Frame-Options: DENY
- ✅ X-Content-Type-Options: nosniff
- ✅ Content-Security-Policy
- ✅ Permissions Policy

### **3. Rate Limiting**
- ✅ API: 10 req/s
- ✅ Login: 5 req/s
- ✅ Static: 20 req/s
- ✅ General: 30 req/s

### **4. File Access Control**
- ✅ Deny access to hidden files
- ✅ Deny access to config files
- ✅ Deny access to backup files
- ✅ Proper file permissions

## 📞 **Support & Troubleshooting**

### **If Issues Persist**
1. **Run troubleshooting script**:
   ```bash
   python3 deployment/nginx/troubleshoot_403.py
   ```

2. **Check container logs**:
   ```bash
   docker logs mingus_nginx_prod
   docker logs mingus_web_prod
   ```

3. **Verify network connectivity**:
   ```bash
   docker exec mingus_nginx_prod ping web
   docker exec mingus_nginx_prod curl -f http://web:5002/health
   ```

4. **Review this guide** for common solutions

### **Emergency Rollback**
```bash
# If new config causes issues
cp deployment/nginx/nginx.conf.backup deployment/nginx/nginx.conf
docker restart mingus_nginx_prod
```

## 🎯 **Expected Results**

After implementing all fixes:

1. ✅ **403 errors eliminated**
2. ✅ **SSL connections working**
3. ✅ **API endpoints accessible**
4. ✅ **Security headers present**
5. ✅ **Rate limiting functional**
6. ✅ **Performance optimized**

## 📋 **Checklist for Success**

- [ ] Environment variables file created (`.env`)
- [ ] SSL certificates generated and permissions set
- [ ] Nginx configuration updated to production config
- [ ] Docker services built and started
- [ ] Health checks passing
- [ ] SSL handshake successful
- [ ] Security headers present
- [ ] API endpoints responding
- [ ] Rate limiting working
- [ ] Error logs clean

---

**Next Steps**: Follow the deployment steps above in order. If you encounter any issues, refer to the troubleshooting section or run the automated troubleshooting script.

**Support**: Use the troubleshooting script for automated diagnosis: `python3 deployment/nginx/troubleshoot_403.py`
