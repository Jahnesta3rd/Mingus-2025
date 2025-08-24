#!/usr/bin/env python3
"""
MINGUS Digital Ocean SSL Configuration
SSL/TLS configuration and deployment utilities for Digital Ocean App Platform
"""

import os
import json
import yaml
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import subprocess
import logging

logger = logging.getLogger(__name__)

@dataclass
class DigitalOceanSSLConfig:
    """Digital Ocean specific SSL configuration"""
    
    # App Platform Configuration
    app_name: str = "mingus-app"
    region: str = "nyc"
    environment: str = "production"
    
    # SSL/TLS Configuration
    ssl_enabled: bool = True
    force_https: bool = True
    auto_ssl: bool = True
    custom_domain: Optional[str] = None
    
    # Load Balancer Configuration
    load_balancer_enabled: bool = True
    load_balancer_ssl: bool = True
    load_balancer_redirect_http: bool = True
    
    # Certificate Management
    certificate_auto_renewal: bool = True
    certificate_provider: str = "letsencrypt"  # or "digitalocean"
    certificate_email: Optional[str] = None
    
    # Health Checks
    health_check_path: str = "/health"
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_retries: int = 3
    
    # Scaling Configuration
    min_instances: int = 2
    max_instances: int = 10
    instance_size: str = "basic-xxs"
    
    # Environment Variables
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)

class DigitalOceanSSLManager:
    """Digital Ocean SSL management and deployment utilities"""
    
    def __init__(self, config: DigitalOceanSSLConfig):
        self.config = config
        self.api_token = os.getenv('DIGITALOCEAN_API_TOKEN')
        
        if not self.api_token:
            raise ValueError("DIGITALOCEAN_API_TOKEN environment variable is required")
    
    def create_app_spec(self) -> Dict[str, Any]:
        """Create Digital Ocean App Platform specification"""
        return {
            'name': self.config.app_name,
            'region': self.config.region,
            'services': [
                {
                    'name': 'mingus-web',
                    'source_dir': '/',
                    'github': {
                        'repo': os.getenv('GITHUB_REPO', 'your-username/mingus-app'),
                        'branch': os.getenv('GITHUB_BRANCH', 'main')
                    },
                    'run_command': 'gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 app:app',
                    'environment_slug': 'python',
                    'instance_count': self.config.min_instances,
                    'instance_size_slug': self.config.instance_size,
                    'autoscaling': {
                        'min_instance_count': self.config.min_instances,
                        'max_instance_count': self.config.max_instances,
                        'metrics': {
                            'cpu_percent': 70,
                            'memory_percent': 80
                        }
                    },
                    'health_check': {
                        'http_path': self.config.health_check_path,
                        'initial_delay_seconds': 30,
                        'interval_seconds': self.config.health_check_interval,
                        'timeout_seconds': self.config.health_check_timeout,
                        'success_threshold': 1,
                        'failure_threshold': self.config.health_check_retries
                    },
                    'envs': self._get_environment_variables(),
                    'secrets': self._get_secrets()
                }
            ],
            'databases': [
                {
                    'name': 'mingus-db',
                    'engine': 'PG',
                    'version': '14',
                    'production': True,
                    'cluster_name': 'mingus-db-cluster',
                    'db_name': 'mingus_production',
                    'db_user': 'mingus_user'
                }
            ],
            'static_sites': [
                {
                    'name': 'mingus-static',
                    'source_dir': '/static',
                    'github': {
                        'repo': os.getenv('GITHUB_REPO', 'your-username/mingus-app'),
                        'branch': os.getenv('GITHUB_BRANCH', 'main')
                    },
                    'output_dir': '/',
                    'index_document': 'index.html',
                    'error_document': '404.html'
                }
            ],
            'domains': self._get_domains_config(),
            'ssl': self._get_ssl_config()
        }
    
    def _get_environment_variables(self) -> List[Dict[str, str]]:
        """Get environment variables for the app"""
        envs = [
            {'key': 'FLASK_ENV', 'value': self.config.environment},
            {'key': 'DATABASE_URL', 'value': '${mingus-db.DATABASE_URL}'},
            {'key': 'SECRET_KEY', 'value': '${SECRET_KEY}'},
            {'key': 'SSL_ENABLED', 'value': 'true'},
            {'key': 'FORCE_HTTPS', 'value': 'true'},
            {'key': 'HSTS_ENABLED', 'value': 'true'},
            {'key': 'HSTS_MAX_AGE', 'value': '31536000'},
            {'key': 'HSTS_INCLUDE_SUBDOMAINS', 'value': 'true'},
            {'key': 'HSTS_PRELOAD', 'value': 'true'},
            {'key': 'SESSION_COOKIE_SECURE', 'value': 'true'},
            {'key': 'SESSION_COOKIE_HTTPONLY', 'value': 'true'},
            {'key': 'SESSION_COOKIE_SAMESITE', 'value': 'Strict'},
            {'key': 'TLS_MIN_VERSION', 'value': 'TLSv1.2'},
            {'key': 'TLS_MAX_VERSION', 'value': 'TLSv1.3'},
            {'key': 'CERT_PINNING_ENABLED', 'value': 'true'},
            {'key': 'EXPECT_CT_ENABLED', 'value': 'true'},
            {'key': 'EXPECT_CT_MAX_AGE', 'value': '86400'},
            {'key': 'EXPECT_CT_ENFORCE', 'value': 'true'},
            {'key': 'BLOCK_MIXED_CONTENT', 'value': 'true'},
            {'key': 'UPGRADE_INSECURE_REQUESTS', 'value': 'true'},
            {'key': 'SSL_HEALTH_CHECK_ENABLED', 'value': 'true'},
            {'key': 'DIGITAL_OCEAN_ENABLED', 'value': 'true'},
            {'key': 'DO_LOAD_BALANCER_SSL', 'value': 'true'},
            {'key': 'DO_CERTIFICATE_AUTO_RENEWAL', 'value': 'true'}
        ]
        
        # Add custom environment variables
        for key, value in self.config.environment_variables.items():
            envs.append({'key': key, 'value': value})
        
        return envs
    
    def _get_secrets(self) -> List[Dict[str, str]]:
        """Get secrets for the app"""
        secrets = [
            {'key': 'SECRET_KEY', 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'},
            {'key': 'DATABASE_PASSWORD', 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'},
            {'key': 'STRIPE_SECRET_KEY', 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'},
            {'key': 'STRIPE_WEBHOOK_SECRET', 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'},
            {'key': 'SMTP_PASSWORD', 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'},
            {'key': 'JWT_SECRET_KEY', 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'}
        ]
        
        # Add custom secrets
        for key, value in self.config.secrets.items():
            secrets.append({'key': key, 'scope': 'RUN_AND_BUILD_TIME', 'type': 'SECRET'})
        
        return secrets
    
    def _get_domains_config(self) -> List[Dict[str, Any]]:
        """Get domains configuration"""
        domains = []
        
        if self.config.custom_domain:
            domains.append({
                'domain': self.config.custom_domain,
                'type': 'PRIMARY',
                'ssl': {
                    'type': 'LETS_ENCRYPT',
                    'redirect_http': self.config.load_balancer_redirect_http
                }
            })
        
        return domains
    
    def _get_ssl_config(self) -> Dict[str, Any]:
        """Get SSL configuration"""
        return {
            'enabled': self.config.ssl_enabled,
            'force_https': self.config.force_https,
            'auto_ssl': self.config.auto_ssl,
            'certificate_provider': self.config.certificate_provider,
            'certificate_email': self.config.certificate_email
        }
    
    def create_app_spec_file(self, filename: str = 'app-spec.yaml'):
        """Create app-spec.yaml file for Digital Ocean deployment"""
        app_spec = self.create_app_spec()
        
        with open(filename, 'w') as f:
            yaml.dump(app_spec, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Created {filename} for Digital Ocean deployment")
        return filename
    
    def deploy_app(self) -> Dict[str, Any]:
        """Deploy app to Digital Ocean App Platform"""
        try:
            # Create app spec file
            spec_file = self.create_app_spec_file()
            
            # Deploy using doctl
            cmd = [
                'doctl', 'apps', 'create', '--spec', spec_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("App deployed successfully to Digital Ocean")
                return {'success': True, 'output': result.stdout}
            else:
                logger.error(f"Deployment failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_app(self, app_id: str) -> Dict[str, Any]:
        """Update existing app on Digital Ocean"""
        try:
            # Create app spec file
            spec_file = self.create_app_spec_file()
            
            # Update using doctl
            cmd = [
                'doctl', 'apps', 'update', app_id, '--spec', spec_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("App updated successfully")
                return {'success': True, 'output': result.stdout}
            else:
                logger.error(f"Update failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Update error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_app_status(self, app_id: str) -> Dict[str, Any]:
        """Get app status from Digital Ocean"""
        try:
            cmd = ['doctl', 'apps', 'get', app_id, '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get app status: {result.stderr}")
                return {'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Error getting app status: {e}")
            return {'error': str(e)}
    
    def check_ssl_status(self, domain: str) -> Dict[str, Any]:
        """Check SSL certificate status for domain"""
        try:
            import ssl
            import socket
            
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    # Calculate days until expiration
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    return {
                        'domain': domain,
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'valid': days_until_expiry > 0,
                        'expires_soon': days_until_expiry <= 30,
                        'serial_number': cert.get('serialNumber'),
                        'version': cert.get('version'),
                        'san': cert.get('subjectAltName', [])
                    }
                    
        except Exception as e:
            logger.error(f"Error checking SSL status for {domain}: {e}")
            return {
                'domain': domain,
                'error': str(e),
                'valid': False
            }
    
    def renew_certificate(self, domain: str) -> Dict[str, Any]:
        """Renew SSL certificate for domain"""
        try:
            # Use certbot for Let's Encrypt renewal
            cmd = [
                'certbot', 'renew', '--cert-name', domain,
                '--quiet', '--non-interactive'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Certificate renewed successfully for {domain}")
                return {'success': True, 'domain': domain}
            else:
                logger.error(f"Certificate renewal failed for {domain}: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Certificate renewal error for {domain}: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_auto_renewal(self) -> Dict[str, Any]:
        """Setup automatic certificate renewal"""
        try:
            # Create cron job for certificate renewal
            cron_job = "0 12 * * * /usr/bin/certbot renew --quiet --non-interactive"
            
            # Add to crontab
            cmd = f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Auto-renewal cron job created successfully")
                return {'success': True}
            else:
                logger.error(f"Failed to create auto-renewal cron job: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"Auto-renewal setup error: {e}")
            return {'success': False, 'error': str(e)}

def create_digital_ocean_config(
    app_name: str = "mingus-app",
    region: str = "nyc",
    environment: str = "production",
    custom_domain: Optional[str] = None
) -> DigitalOceanSSLConfig:
    """Create Digital Ocean SSL configuration"""
    return DigitalOceanSSLConfig(
        app_name=app_name,
        region=region,
        environment=environment,
        custom_domain=custom_domain,
        ssl_enabled=True,
        force_https=True,
        auto_ssl=True,
        load_balancer_enabled=True,
        load_balancer_ssl=True,
        load_balancer_redirect_http=True,
        certificate_auto_renewal=True,
        certificate_provider="letsencrypt",
        certificate_email=os.getenv('CERTIFICATE_EMAIL'),
        environment_variables={
            'DATABASE_POOL_SIZE': '20',
            'DB_SSL_MODE': 'require',
            'API_RATE_LIMIT': '100',
            'SESSION_LIFETIME': '1800',
            'LOG_LEVEL': 'INFO'
        },
        secrets={
            'DATABASE_PASSWORD': os.getenv('DATABASE_PASSWORD'),
            'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY'),
            'STRIPE_WEBHOOK_SECRET': os.getenv('STRIPE_WEBHOOK_SECRET'),
            'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY')
        }
    )

def validate_digital_ocean_config(config: DigitalOceanSSLConfig) -> List[str]:
    """Validate Digital Ocean configuration"""
    issues = []
    
    # Check required environment variables
    required_env_vars = ['DIGITALOCEAN_API_TOKEN', 'GITHUB_REPO']
    for var in required_env_vars:
        if not os.getenv(var):
            issues.append(f"Required environment variable {var} is not set")
    
    # Check certificate email
    if config.certificate_auto_renewal and not config.certificate_email:
        issues.append("Certificate email is required for auto-renewal")
    
    # Check custom domain
    if config.custom_domain and not config.custom_domain.startswith(('http://', 'https://')):
        issues.append("Custom domain should be a valid domain name")
    
    # Check instance configuration
    if config.min_instances > config.max_instances:
        issues.append("Minimum instances cannot be greater than maximum instances")
    
    if config.min_instances < 1:
        issues.append("Minimum instances must be at least 1")
    
    return issues

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Digital Ocean SSL Configuration')
    parser.add_argument('--app-name', default='mingus-app', help='App name')
    parser.add_argument('--region', default='nyc', help='Digital Ocean region')
    parser.add_argument('--environment', default='production', help='Environment')
    parser.add_argument('--domain', help='Custom domain')
    parser.add_argument('--create-spec', action='store_true', help='Create app-spec.yaml')
    parser.add_argument('--deploy', action='store_true', help='Deploy app')
    parser.add_argument('--check-ssl', help='Check SSL status for domain')
    parser.add_argument('--renew-cert', help='Renew certificate for domain')
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_digital_ocean_config(
        app_name=args.app_name,
        region=args.region,
        environment=args.environment,
        custom_domain=args.domain
    )
    
    # Validate configuration
    issues = validate_digital_ocean_config(config)
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return
    
    # Create manager
    manager = DigitalOceanSSLManager(config)
    
    if args.create_spec:
        spec_file = manager.create_app_spec_file()
        print(f"Created {spec_file}")
    
    if args.deploy:
        result = manager.deploy_app()
        if result['success']:
            print("App deployed successfully")
        else:
            print(f"Deployment failed: {result['error']}")
    
    if args.check_ssl:
        status = manager.check_ssl_status(args.check_ssl)
        print(json.dumps(status, indent=2))
    
    if args.renew_cert:
        result = manager.renew_certificate(args.renew_cert)
        if result['success']:
            print(f"Certificate renewed for {args.renew_cert}")
        else:
            print(f"Certificate renewal failed: {result['error']}")

if __name__ == "__main__":
    main() 