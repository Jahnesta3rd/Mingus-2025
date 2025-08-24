#!/usr/bin/env python3
"""
Secure MINGUS Deployment Script for Digital Ocean
Deploys MINGUS with maximum security configuration
"""

import os
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import yaml

# Add the security module to path
sys.path.append(str(Path(__file__).parent))

from production_config import (
    get_production_security_config, SecurityLevel, 
    ProductionSecurityConfig
)

class SecureMingusDeployer:
    """Secure MINGUS deployment manager"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.PRODUCTION):
        self.security_level = security_level
        self.security_config = get_production_security_config(security_level)
        self.deployment_config = self._load_deployment_config()
        self.droplet_id = None
        self.droplet_ip = None
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_path = Path(__file__).parent / "deployment_config.yml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_deployment_config()
    
    def _get_default_deployment_config(self) -> Dict[str, Any]:
        """Get default deployment configuration"""
        return {
            "digital_ocean": {
                "api_token": os.getenv("DIGITALOCEAN_API_TOKEN", ""),
                "region": "nyc1",
                "size": "s-2vcpu-4gb",
                "image": "ubuntu-20-04-x64",
                "ssh_keys": [],
                "backups": True,
                "monitoring": True,
                "ipv6": True,
                "private_networking": True
            },
            "application": {
                "name": "mingus-production",
                "domain": os.getenv("MINGUS_DOMAIN", ""),
                "port": 8080,
                "user": "mingus",
                "group": "mingus",
                "install_path": "/opt/mingus",
                "venv_path": "/opt/mingus/venv"
            },
            "database": {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "name": "mingus_production",
                "user": "mingus",
                "password": os.getenv("DB_PASSWORD", ""),
                "ssl_mode": "require"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": os.getenv("REDIS_PASSWORD", ""),
                "ssl": True
            },
            "ssl": {
                "provider": "letsencrypt",
                "email": os.getenv("SSL_EMAIL", ""),
                "cert_path": "/etc/letsencrypt/live/{domain}/fullchain.pem",
                "key_path": "/etc/letsencrypt/live/{domain}/privkey.pem"
            }
        }
    
    def validate_prerequisites(self) -> bool:
        """Validate deployment prerequisites"""
        print("🔍 Validating deployment prerequisites...")
        
        # Check Digital Ocean API token
        if not self.deployment_config["digital_ocean"]["api_token"]:
            print("❌ DIGITALOCEAN_API_TOKEN environment variable is required")
            return False
        
        # Check domain configuration
        if not self.deployment_config["application"]["domain"]:
            print("❌ MINGUS_DOMAIN environment variable is required")
            return False
        
        # Check database password
        if not self.deployment_config["database"]["password"]:
            print("❌ DB_PASSWORD environment variable is required")
            return False
        
        # Check SSL email
        if not self.deployment_config["ssl"]["email"]:
            print("❌ SSL_EMAIL environment variable is required")
            return False
        
        # Check required tools
        required_tools = ["doctl", "ssh-keygen", "openssl"]
        for tool in required_tools:
            if not self._check_tool_exists(tool):
                print(f"❌ Required tool not found: {tool}")
                return False
        
        print("✅ All prerequisites validated successfully")
        return True
    
    def _check_tool_exists(self, tool: str) -> bool:
        """Check if a tool exists in PATH"""
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def create_droplet(self) -> bool:
        """Create Digital Ocean droplet"""
        print("🚀 Creating Digital Ocean droplet...")
        
        try:
            # Create droplet using doctl
            cmd = [
                "doctl", "compute", "droplet", "create",
                self.deployment_config["application"]["name"],
                "--size", self.deployment_config["digital_ocean"]["size"],
                "--image", self.deployment_config["digital_ocean"]["image"],
                "--region", self.deployment_config["digital_ocean"]["region"],
                "--enable-backups" if self.deployment_config["digital_ocean"]["backups"] else "",
                "--enable-monitoring" if self.deployment_config["digital_ocean"]["monitoring"] else "",
                "--enable-ipv6" if self.deployment_config["digital_ocean"]["ipv6"] else "",
                "--enable-private-networking" if self.deployment_config["digital_ocean"]["private_networking"] else "",
                "--format", "ID,PublicIPv4"
            ]
            
            # Filter out empty strings
            cmd = [arg for arg in cmd if arg]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse droplet ID and IP
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                self.droplet_id = lines[1].split()[0]
                self.droplet_ip = lines[1].split()[1]
                
                print(f"✅ Droplet created successfully")
                print(f"   ID: {self.droplet_id}")
                print(f"   IP: {self.droplet_ip}")
                
                # Wait for droplet to be ready
                self._wait_for_droplet_ready()
                return True
            else:
                print("❌ Failed to parse droplet information")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create droplet: {e}")
            return False
    
    def _wait_for_droplet_ready(self, timeout: int = 300):
        """Wait for droplet to be ready"""
        print("⏳ Waiting for droplet to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                cmd = ["doctl", "compute", "droplet", "get", self.droplet_id, "--format", "Status"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                if "active" in result.stdout.lower():
                    print("✅ Droplet is ready")
                    return
                
                time.sleep(10)
            except subprocess.CalledProcessError:
                time.sleep(10)
        
        raise TimeoutError("Droplet did not become ready within timeout")
    
    def setup_ssh_access(self) -> bool:
        """Setup SSH access to droplet"""
        print("🔑 Setting up SSH access...")
        
        try:
            # Generate SSH key if not exists
            ssh_key_path = Path.home() / ".ssh" / "mingus_production"
            if not ssh_key_path.exists():
                subprocess.run([
                    "ssh-keygen", "-t", "ed25519", "-f", str(ssh_key_path),
                    "-N", "", "-C", "mingus-production"
                ], check=True)
            
            # Add SSH key to Digital Ocean
            with open(f"{ssh_key_path}.pub", 'r') as f:
                public_key = f.read().strip()
            
            # Create SSH key in Digital Ocean
            cmd = [
                "doctl", "compute", "ssh-key", "create", "mingus-production",
                "--public-key-file", f"{ssh_key_path}.pub"
            ]
            subprocess.run(cmd, check=True)
            
            # Get SSH key ID
            cmd = ["doctl", "compute", "ssh-key", "list", "--format", "ID,Name"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            ssh_key_id = None
            for line in result.stdout.strip().split('\n')[1:]:
                if "mingus-production" in line:
                    ssh_key_id = line.split()[0]
                    break
            
            if ssh_key_id:
                # Add SSH key to droplet
                cmd = [
                    "doctl", "compute", "droplet", "action", "add-ssh-key",
                    self.droplet_id, "--ssh-key-ids", ssh_key_id
                ]
                subprocess.run(cmd, check=True)
                
                print("✅ SSH access configured successfully")
                return True
            else:
                print("❌ Failed to get SSH key ID")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup SSH access: {e}")
            return False
    
    def deploy_security_configuration(self) -> bool:
        """Deploy security configuration to droplet"""
        print("🔒 Deploying security configuration...")
        
        try:
            # Generate security configuration
            security_config = self.security_config.export_configuration()
            
            # Create deployment scripts
            scripts = self._create_deployment_scripts(security_config)
            
            # Upload and execute scripts
            for script_name, script_content in scripts.items():
                script_path = f"/tmp/{script_name}"
                
                # Upload script
                self._upload_file(script_content, script_path)
                
                # Make executable and run
                self._run_remote_command(f"chmod +x {script_path}")
                self._run_remote_command(f"sudo {script_path}")
            
            print("✅ Security configuration deployed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to deploy security configuration: {e}")
            return False
    
    def _create_deployment_scripts(self, security_config: Dict[str, Any]) -> Dict[str, str]:
        """Create deployment scripts"""
        scripts = {}
        
        # System setup script
        scripts["01_system_setup.sh"] = f"""#!/bin/bash
set -e

echo "🔧 Setting up system..."

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \\
    nginx \\
    postgresql \\
    redis-server \\
    certbot \\
    python3-certbot-nginx \\
    fail2ban \\
    ufw \\
    htop \\
    curl \\
    wget \\
    git \\
    python3 \\
    python3-pip \\
    python3-venv \\
    build-essential \\
    libpq-dev \\
    python3-dev

# Create application user
useradd -m -s /bin/bash {self.deployment_config['application']['user']}
usermod -aG sudo {self.deployment_config['application']['user']}

# Create application directories
mkdir -p {self.deployment_config['application']['install_path']}
mkdir -p /var/lib/mingus
mkdir -p /var/log/mingus
mkdir -p /etc/mingus

# Set permissions
chown -R {self.deployment_config['application']['user']}:{self.deployment_config['application']['group']} {self.deployment_config['application']['install_path']}
chown -R {self.deployment_config['application']['user']}:{self.deployment_config['application']['group']} /var/lib/mingus
chown -R {self.deployment_config['application']['user']}:{self.deployment_config['application']['group']} /var/log/mingus
chmod 700 /var/lib/mingus
chmod 700 /var/log/mingus

echo "✅ System setup completed"
"""
        
        # Security configuration script
        scripts["02_security_config.sh"] = f"""#!/bin/bash
set -e

echo "🔒 Configuring security..."

# Configure firewall
{chr(10).join(security_config['firewall_rules'])}

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = {self.security_config.config['firewall'].fail2ban_ban_time}
findtime = 600
maxretry = {self.security_config.config['firewall'].fail2ban_max_retries}

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# Configure SSH
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart ssh

echo "✅ Security configuration completed"
"""
        
        # Database configuration script
        scripts["03_database_config.sh"] = f"""#!/bin/bash
set -e

echo "🗄️ Configuring database..."

# Configure PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE {self.deployment_config['database']['name']};
CREATE USER {self.deployment_config['database']['user']} WITH PASSWORD '{self.deployment_config['database']['password']}';
GRANT ALL PRIVILEGES ON DATABASE {self.deployment_config['database']['name']} TO {self.deployment_config['database']['user']};
ALTER USER {self.deployment_config['database']['user']} CREATEDB;
EOF

# Configure PostgreSQL SSL
cat > /etc/postgresql/*/main/conf.d/ssl.conf << EOF
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
EOF

systemctl restart postgresql

# Configure Redis
sed -i 's/# requirepass foobared/requirepass {self.deployment_config["redis"]["password"]}/' /etc/redis/redis.conf
sed -i 's/# tls-port 6380/tls-port 6380/' /etc/redis/redis.conf
systemctl restart redis-server

echo "✅ Database configuration completed"
"""
        
        # Nginx configuration script
        scripts["04_nginx_config.sh"] = f"""#!/bin/bash
set -e

echo "🌐 Configuring Nginx..."

# Create Nginx configuration
cat > /etc/nginx/sites-available/mingus << 'EOF'
{security_config['nginx_config']}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/mingus /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

# Enable and start Nginx
systemctl enable nginx
systemctl restart nginx

echo "✅ Nginx configuration completed"
"""
        
        # SSL certificate script
        scripts["05_ssl_cert.sh"] = f"""#!/bin/bash
set -e

echo "🔐 Obtaining SSL certificate..."

# Obtain SSL certificate
certbot --nginx \\
    --non-interactive \\
    --agree-tos \\
    --email {self.deployment_config['ssl']['email']} \\
    --domains {self.deployment_config['application']['domain']} \\
    --redirect

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

echo "✅ SSL certificate obtained"
"""
        
        # Application deployment script
        scripts["06_app_deploy.sh"] = f"""#!/bin/bash
set -e

echo "🚀 Deploying MINGUS application..."

# Switch to application user
su - {self.deployment_config['application']['user']} << 'EOF'

# Clone application (replace with your actual repository)
cd {self.deployment_config['application']['install_path']}
git clone https://github.com/your-org/mingus.git .

# Create virtual environment
python3 -m venv {self.deployment_config['application']['venv_path']}
source {self.deployment_config['application']['venv_path']}/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create application configuration
cat > config.py << 'CONFIG_EOF'
import os

class ProductionConfig:
    SECRET_KEY = '{self.security_config.config['authentication'].jwt_secret}'
    SQLALCHEMY_DATABASE_URI = 'postgresql://{self.deployment_config['database']['user']}:{self.deployment_config['database']['password']}@localhost/{self.deployment_config['database']['name']}?sslmode=require'
    REDIS_URL = 'redis://:{self.deployment_config['redis']['password']}@localhost:6379/0'
    
    # Security settings
    SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/mingus/app.log'
    
    # Monitoring
    MONITORING_ENABLED = True
    ALERT_EMAIL = '{self.deployment_config['ssl']['email']}'
CONFIG_EOF

# Create systemd service
sudo tee /etc/systemd/system/mingus.service << 'SERVICE_EOF'
{security_config['systemd_config']}
SERVICE_EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mingus
sudo systemctl start mingus

EOF

echo "✅ Application deployment completed"
"""
        
        # Final security check script
        scripts["07_security_check.sh"] = f"""#!/bin/bash
set -e

echo "🔍 Running security checks..."

# Check services
systemctl is-active --quiet nginx || echo "❌ Nginx not running"
systemctl is-active --quiet postgresql || echo "❌ PostgreSQL not running"
systemctl is-active --quiet redis-server || echo "❌ Redis not running"
systemctl is-active --quiet mingus || echo "❌ MINGUS not running"
systemctl is-active --quiet fail2ban || echo "❌ Fail2ban not running"

# Check firewall
ufw status | grep -q "Status: active" || echo "❌ Firewall not active"

# Check SSL certificate
if [ -f "/etc/letsencrypt/live/{self.deployment_config['application']['domain']}/fullchain.pem" ]; then
    echo "✅ SSL certificate installed"
else
    echo "❌ SSL certificate not found"
fi

# Check security headers
curl -I https://{self.deployment_config['application']['domain']} | grep -q "Strict-Transport-Security" || echo "❌ HSTS header missing"

echo "✅ Security checks completed"
"""
        
        return scripts
    
    def _upload_file(self, content: str, remote_path: str):
        """Upload file to droplet"""
        # Create temporary local file
        temp_file = f"/tmp/temp_upload_{int(time.time())}"
        with open(temp_file, 'w') as f:
            f.write(content)
        
        # Upload file
        subprocess.run([
            "scp", "-o", "StrictHostKeyChecking=no",
            temp_file, f"root@{self.droplet_ip}:{remote_path}"
        ], check=True)
        
        # Clean up
        os.remove(temp_file)
    
    def _run_remote_command(self, command: str):
        """Run command on remote droplet"""
        subprocess.run([
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"root@{self.droplet_ip}", command
        ], check=True)
    
    def deploy(self) -> bool:
        """Deploy MINGUS with maximum security"""
        print("🚀 Starting secure MINGUS deployment...")
        print(f"🔒 Security Level: {self.security_level.value}")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            return False
        
        # Create droplet
        if not self.create_droplet():
            return False
        
        # Setup SSH access
        if not self.setup_ssh_access():
            return False
        
        # Deploy security configuration
        if not self.deploy_security_configuration():
            return False
        
        print("🎉 MINGUS deployment completed successfully!")
        print(f"🌐 Application URL: https://{self.deployment_config['application']['domain']}")
        print(f"🔑 SSH Access: ssh root@{self.droplet_ip}")
        print(f"📊 Monitoring: https://{self.deployment_config['application']['domain']}/health")
        
        return True
    
    def cleanup(self):
        """Cleanup deployment resources"""
        if self.droplet_id:
            print(f"🧹 Cleaning up droplet {self.droplet_id}...")
            try:
                subprocess.run([
                    "doctl", "compute", "droplet", "delete", self.droplet_id,
                    "--force"
                ], check=True)
                print("✅ Cleanup completed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Cleanup failed: {e}")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy MINGUS with maximum security")
    parser.add_argument(
        "--security-level",
        choices=["production", "high_security"],
        default="production",
        help="Security level for deployment"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup deployment resources"
    )
    
    args = parser.parse_args()
    
    # Map security level
    security_level_map = {
        "production": SecurityLevel.PRODUCTION,
        "high_security": SecurityLevel.HIGH_SECURITY
    }
    
    deployer = SecureMingusDeployer(security_level_map[args.security_level])
    
    if args.cleanup:
        deployer.cleanup()
    else:
        try:
            success = deployer.deploy()
            if not success:
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n⚠️ Deployment interrupted by user")
            deployer.cleanup()
            sys.exit(1)
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            deployer.cleanup()
            sys.exit(1)

if __name__ == "__main__":
    main() 