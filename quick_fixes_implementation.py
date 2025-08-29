#!/usr/bin/env python3
"""
Quick Fixes Implementation for MINGUS Application
================================================

This script helps implement critical fixes identified in the technical health check:
- Accessibility improvements
- Mobile optimization
- Basic security enhancements
"""

import re
import os
from datetime import datetime

def apply_accessibility_fixes(html_content):
    """Apply accessibility fixes to HTML content"""
    fixes_applied = []
    
    # Fix 1: Add lang attribute if missing
    if 'lang="' not in html_content:
        html_content = re.sub(r'<html([^>]*)>', r'<html\1 lang="en">', html_content)
        fixes_applied.append("Added lang='en' attribute to HTML tag")
    
    # Fix 2: Add meta description if missing
    if 'name="description"' not in html_content:
        meta_description = '    <meta name="description" content="MINGUS - AI-powered personal finance app designed for black professionals. Transform your financial future with intelligent income comparison and career advancement tools.">'
        html_content = re.sub(r'(<meta[^>]*>)', r'\1\n' + meta_description, html_content, count=1)
        fixes_applied.append("Added meta description")
    
    # Fix 3: Add alt attributes to images without them
    def add_alt_to_img(match):
        img_tag = match.group(0)
        if 'alt=' not in img_tag:
            # Extract src to create meaningful alt text
            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
            if src_match:
                src = src_match.group(1)
                filename = os.path.basename(src)
                alt_text = filename.replace('.', ' ').replace('-', ' ').replace('_', ' ')
                return img_tag.replace('<img', '<img alt="' + alt_text + '"')
        return img_tag
    
    html_content = re.sub(r'<img[^>]*>', add_alt_to_img, html_content)
    fixes_applied.append("Added alt attributes to images")
    
    # Fix 4: Add ARIA labels to interactive elements
    def add_aria_to_buttons(match):
        button_tag = match.group(0)
        if 'aria-label=' not in button_tag and 'aria-labelledby=' not in button_tag:
            # Extract button text or create generic label
            text_match = re.search(r'>([^<]+)<', button_tag)
            if text_match:
                label = text_match.group(1).strip()
                return button_tag.replace('<button', '<button aria-label="' + label + '"')
            else:
                return button_tag.replace('<button', '<button aria-label="Button"')
        return button_tag
    
    html_content = re.sub(r'<button[^>]*>.*?</button>', add_aria_to_buttons, html_content, flags=re.DOTALL)
    fixes_applied.append("Added ARIA labels to buttons")
    
    # Fix 5: Add semantic HTML structure
    if '<nav>' not in html_content and 'navigation' in html_content.lower():
        # Add nav wrapper around navigation elements
        html_content = re.sub(r'(<div[^>]*class="[^"]*nav[^"]*"[^>]*>)', r'<nav>\1', html_content)
        html_content = re.sub(r'(</div>\s*<!--.*nav.*-->)', r'\1</nav>', html_content)
        fixes_applied.append("Added semantic nav element")
    
    # Fix 6: Add skip navigation link
    if 'skip' not in html_content.lower():
        skip_link = '''    <a href="#main-content" class="skip-link" style="position: absolute; top: -40px; left: 6px; background: #000; color: #fff; padding: 8px; text-decoration: none; z-index: 10000;">Skip to main content</a>'''
        html_content = re.sub(r'(<body[^>]*>)', r'\1\n' + skip_link, html_content)
        fixes_applied.append("Added skip navigation link")
    
    return html_content, fixes_applied

def apply_mobile_fixes(html_content):
    """Apply mobile optimization fixes to HTML content"""
    fixes_applied = []
    
    # Fix 1: Add viewport meta tag if missing
    if 'name="viewport"' not in html_content:
        viewport_meta = '    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
        html_content = re.sub(r'(<meta[^>]*>)', r'\1\n' + viewport_meta, html_content, count=1)
        fixes_applied.append("Added viewport meta tag")
    
    # Fix 2: Add responsive CSS
    responsive_css = '''
    <style>
        /* Mobile-first responsive design */
        @media (max-width: 768px) {
            body { font-size: 16px; }
            button, a { min-height: 44px; min-width: 44px; }
            .container { padding: 0 15px; }
            img { max-width: 100%; height: auto; }
        }
        
        /* Touch-friendly improvements */
        button, a { 
            padding: 12px 16px; 
            margin: 4px; 
            border-radius: 4px; 
        }
        
        /* Prevent horizontal scroll */
        body { overflow-x: hidden; }
        
        /* Skip link styling */
        .skip-link:focus {
            top: 6px;
            transition: top 0.3s;
        }
    </style>'''
    
    if '<style>' not in html_content:
        html_content = re.sub(r'(</head>)', responsive_css + r'\1', html_content)
        fixes_applied.append("Added responsive CSS")
    
    return html_content, fixes_applied

def apply_security_fixes(html_content):
    """Apply basic security fixes to HTML content"""
    fixes_applied = []
    
    # Fix 1: Add Content Security Policy meta tag
    if 'Content-Security-Policy' not in html_content:
        csp_meta = '    <meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: https:;">'
        html_content = re.sub(r'(<meta[^>]*>)', r'\1\n' + csp_meta, html_content, count=1)
        fixes_applied.append("Added Content Security Policy meta tag")
    
    # Fix 2: Add referrer policy
    if 'referrer' not in html_content.lower():
        referrer_meta = '    <meta name="referrer" content="strict-origin-when-cross-origin">'
        html_content = re.sub(r'(<meta[^>]*>)', r'\1\n' + referrer_meta, html_content, count=1)
        fixes_applied.append("Added referrer policy")
    
    return html_content, fixes_applied

def create_improved_landing_page():
    """Create an improved version of the landing page with all fixes applied"""
    
    # Read the original landing page
    try:
        with open('landing.html', 'r', encoding='utf-8') as f:
            original_content = f.read()
    except FileNotFoundError:
        print("❌ Error: landing.html not found in current directory")
        return
    
    print("🔧 Applying technical health check fixes...")
    
    # Apply all fixes
    content = original_content
    
    # Apply accessibility fixes
    content, accessibility_fixes = apply_accessibility_fixes(content)
    
    # Apply mobile fixes
    content, mobile_fixes = apply_mobile_fixes(content)
    
    # Apply security fixes
    content, security_fixes = apply_security_fixes(content)
    
    # Create backup of original file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"landing_backup_{timestamp}.html"
    
    with open(backup_filename, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    # Write improved version
    improved_filename = f"landing_improved_{timestamp}.html"
    with open(improved_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Print summary
    print(f"\n✅ Fixes applied successfully!")
    print(f"📁 Original file backed up as: {backup_filename}")
    print(f"📁 Improved file saved as: {improved_filename}")
    
    print(f"\n🔧 Accessibility Fixes Applied ({len(accessibility_fixes)}):")
    for fix in accessibility_fixes:
        print(f"  ✅ {fix}")
    
    print(f"\n📱 Mobile Fixes Applied ({len(mobile_fixes)}):")
    for fix in mobile_fixes:
        print(f"  ✅ {fix}")
    
    print(f"\n🔒 Security Fixes Applied ({len(security_fixes)}):")
    for fix in security_fixes:
        print(f"  ✅ {fix}")
    
    print(f"\n📋 Next Steps:")
    print("1. Review the improved file and test it")
    print("2. Implement HTTPS/SSL certificate")
    print("3. Add server-side security headers")
    print("4. Test with actual mobile devices")
    print("5. Run accessibility testing tools")
    print("6. Validate with screen readers")

def create_nginx_config():
    """Create a sample Nginx configuration with security headers"""
    
    nginx_config = """# MINGUS Application - Nginx Configuration with Security Headers
server {
    listen 80;
    server_name mingus.com www.mingus.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mingus.com www.mingus.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self'; frame-ancestors 'none';" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # Root directory
    root /var/www/mingus;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Cache static assets
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main location
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
"""
    
    with open('nginx_mingus_config.conf', 'w') as f:
        f.write(nginx_config)
    
    print("📄 Nginx configuration with security headers created: nginx_mingus_config.conf")

def create_htaccess_config():
    """Create a sample .htaccess configuration for Apache with security headers"""
    
    htaccess_config = """# MINGUS Application - Apache .htaccess with Security Headers

# Enable HTTPS redirect
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Security Headers
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
Header always set X-Frame-Options "DENY"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self'; frame-ancestors 'none';"
Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"

# Enable Gzip compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# Cache static assets
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/ico "access plus 1 year"
    ExpiresByType image/icon "access plus 1 year"
    ExpiresByType text/plain "access plus 1 month"
    ExpiresByType application/pdf "access plus 1 month"
    ExpiresByType application/x-shockwave-flash "access plus 1 month"
</IfModule>
"""
    
    with open('.htaccess', 'w') as f:
        f.write(htaccess_config)
    
    print("📄 Apache .htaccess configuration created: .htaccess")

def main():
    """Main function to run the quick fixes"""
    print("🔧 MINGUS Application - Quick Fixes Implementation")
    print("=" * 50)
    
    print("\nChoose an option:")
    print("1. Apply fixes to landing page")
    print("2. Create Nginx configuration")
    print("3. Create Apache .htaccess configuration")
    print("4. Apply all fixes")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        create_improved_landing_page()
    elif choice == "2":
        create_nginx_config()
    elif choice == "3":
        create_htaccess_config()
    elif choice == "4":
        create_improved_landing_page()
        print("\n" + "="*50)
        create_nginx_config()
        print("\n" + "="*50)
        create_htaccess_config()
    else:
        print("❌ Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
