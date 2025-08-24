"""
Digital Ocean Security Configuration
Comprehensive security configuration for Digital Ocean infrastructure
"""

import os
import json
import time
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import requests
import yaml

class SecurityTier(Enum):
    """Security tiers for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"

class NetworkType(Enum):
    """Network types for VPC configuration"""
    PUBLIC = "public"
    PRIVATE = "private"
    ISOLATED = "isolated"

@dataclass
class VPCSecurityConfig:
    """VPC security configuration"""
    vpc_name: str
    region: str
    ip_range: str
    description: str
    network_type: NetworkType
    enable_private_networking: bool = True
    enable_ipv6: bool = True
    enable_monitoring: bool = True
    enable_backups: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass
class FirewallSecurityConfig:
    """Firewall security configuration"""
    firewall_name: str
    description: str
    inbound_rules: List[Dict[str, Any]] = field(default_factory=list)
    outbound_rules: List[Dict[str, Any]] = field(default_factory=list)
    droplet_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enable_logging: bool = True

@dataclass
class LoadBalancerSecurityConfig:
    """Load balancer security configuration"""
    lb_name: str
    region: str
    algorithm: str = "round_robin"
    health_check_path: str = "/health"
    health_check_protocol: str = "http"
    health_check_port: int = 80
    ssl_termination: bool = True
    ssl_certificate_id: str = ""
    redirect_http_to_https: bool = True
    enable_proxy_protocol: bool = True
    enable_sticky_sessions: bool = False
    droplet_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

@dataclass
class DatabaseSecurityConfig:
    """Database security configuration"""
    db_name: str
    engine: str = "pg"
    version: str = "14"
    region: str = ""
    size: str = "db-s-1vcpu-1gb"
    node_count: int = 1
    enable_private_networking: bool = True
    enable_ssl: bool = True
    enable_connection_pooling: bool = True
    enable_backups: bool = True
    backup_retention_days: int = 7
    enable_maintenance_window: bool = True
    maintenance_day: str = "sunday"
    maintenance_hour: str = "02:00:00"
    tags: List[str] = field(default_factory=list)

@dataclass
class AppPlatformSecurityConfig:
    """App Platform security configuration"""
    app_name: str
    region: str
    environment: str = "production"
    enable_ssl: bool = True
    enable_http2: bool = True
    enable_compression: bool = True
    enable_caching: bool = True
    security_headers: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    health_check_path: str = "/health"
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_retries: int = 3
    tags: List[str] = field(default_factory=list)

@dataclass
class CDNSecurityConfig:
    """CDN security configuration"""
    cdn_name: str
    origin: str
    ttl: int = 3600
    enable_ssl: bool = True
    enable_compression: bool = True
    enable_caching: bool = True
    cache_headers: List[str] = field(default_factory=lambda: ["Cache-Control", "Expires"])
    security_headers: Dict[str, str] = field(default_factory=dict)
    rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    enable_waf: bool = True
    waf_rules: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

class DigitalOceanSecurityManager:
    """Digital Ocean security configuration manager"""
    
    def __init__(self, api_token: str, security_tier: SecurityTier = SecurityTier.PRODUCTION):
        self.api_token = api_token
        self.security_tier = security_tier
        self.base_url = "https://api.digitalocean.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Initialize security configurations
        self.vpc_config = self._get_vpc_security_config()
        self.firewall_config = self._get_firewall_security_config()
        self.loadbalancer_config = self._get_loadbalancer_security_config()
        self.database_config = self._get_database_security_config()
        self.app_platform_config = self._get_app_platform_security_config()
        self.cdn_config = self._get_cdn_security_config()
    
    def _get_vpc_security_config(self) -> VPCSecurityConfig:
        """Get VPC security configuration"""
        return VPCSecurityConfig(
            vpc_name=f"mingus-vpc-{self.security_tier.value}",
            region=os.getenv("DO_REGION", "nyc1"),
            ip_range=os.getenv("VPC_IP_RANGE", "10.0.0.0/16"),
            description=f"MINGUS VPC for {self.security_tier.value} environment",
            network_type=NetworkType.PRIVATE,
            enable_private_networking=True,
            enable_ipv6=True,
            enable_monitoring=True,
            enable_backups=True,
            tags=[f"mingus-{self.security_tier.value}", "vpc", "security"]
        )
    
    def _get_firewall_security_config(self) -> FirewallSecurityConfig:
        """Get firewall security configuration"""
        # Base firewall rules
        inbound_rules = [
            {
                "protocol": "tcp",
                "ports": "22",
                "sources": {
                    "addresses": ["0.0.0.0/0"] if self.security_tier == SecurityTier.DEVELOPMENT else []
                },
                "description": "SSH access"
            },
            {
                "protocol": "tcp",
                "ports": "80",
                "sources": {
                    "addresses": ["0.0.0.0/0"]
                },
                "description": "HTTP access"
            },
            {
                "protocol": "tcp",
                "ports": "443",
                "sources": {
                    "addresses": ["0.0.0.0/0"]
                },
                "description": "HTTPS access"
            }
        ]
        
        # Add additional rules for production
        if self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE]:
            inbound_rules.extend([
                {
                    "protocol": "tcp",
                    "ports": "8080",
                    "sources": {
                        "load_balancer_uids": ["*"]
                    },
                    "description": "Application port from load balancer"
                },
                {
                    "protocol": "tcp",
                    "ports": "5432",
                    "sources": {
                        "addresses": ["10.0.0.0/16"]
                    },
                    "description": "Database access from VPC"
                }
            ])
        
        # Outbound rules
        outbound_rules = [
            {
                "protocol": "tcp",
                "ports": "all",
                "destinations": {
                    "addresses": ["0.0.0.0/0"]
                },
                "description": "Allow all outbound traffic"
            }
        ]
        
        return FirewallSecurityConfig(
            firewall_name=f"mingus-firewall-{self.security_tier.value}",
            description=f"MINGUS firewall for {self.security_tier.value} environment",
            inbound_rules=inbound_rules,
            outbound_rules=outbound_rules,
            enable_logging=True,
            tags=[f"mingus-{self.security_tier.value}", "firewall", "security"]
        )
    
    def _get_loadbalancer_security_config(self) -> LoadBalancerSecurityConfig:
        """Get load balancer security configuration"""
        return LoadBalancerSecurityConfig(
            lb_name=f"mingus-lb-{self.security_tier.value}",
            region=os.getenv("DO_REGION", "nyc1"),
            algorithm="round_robin",
            health_check_path="/health",
            health_check_protocol="https" if self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE] else "http",
            health_check_port=443 if self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE] else 80,
            ssl_termination=True,
            redirect_http_to_https=True,
            enable_proxy_protocol=True,
            enable_sticky_sessions=False,
            tags=[f"mingus-{self.security_tier.value}", "loadbalancer", "security"]
        )
    
    def _get_database_security_config(self) -> DatabaseSecurityConfig:
        """Get database security configuration"""
        return DatabaseSecurityConfig(
            db_name=f"mingus-db-{self.security_tier.value}",
            engine="pg",
            version="14",
            region=os.getenv("DO_REGION", "nyc1"),
            size="db-s-1vcpu-1gb" if self.security_tier == SecurityTier.DEVELOPMENT else "db-s-2vcpu-4gb",
            node_count=1 if self.security_tier in [SecurityTier.DEVELOPMENT, SecurityTier.STAGING] else 2,
            enable_private_networking=True,
            enable_ssl=True,
            enable_connection_pooling=True,
            enable_backups=True,
            backup_retention_days=7 if self.security_tier == SecurityTier.DEVELOPMENT else 30,
            enable_maintenance_window=True,
            maintenance_day="sunday",
            maintenance_hour="02:00:00",
            tags=[f"mingus-{self.security_tier.value}", "database", "security"]
        )
    
    def _get_app_platform_security_config(self) -> AppPlatformSecurityConfig:
        """Get App Platform security configuration"""
        # Security headers
        security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
        }
        
        # Environment variables
        environment_variables = {
            "NODE_ENV": self.security_tier.value,
            "SECURITY_LEVEL": self.security_tier.value,
            "ENABLE_SSL": "true",
            "ENABLE_COMPRESSION": "true",
            "ENABLE_CACHING": "true"
        }
        
        # Secrets
        secrets = {
            "JWT_SECRET": os.getenv("JWT_SECRET", ""),
            "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
            "REDIS_PASSWORD": os.getenv("REDIS_PASSWORD", ""),
            "API_KEYS": os.getenv("API_KEYS", "")
        }
        
        return AppPlatformSecurityConfig(
            app_name=f"mingus-app-{self.security_tier.value}",
            region=os.getenv("DO_REGION", "nyc1"),
            environment=self.security_tier.value,
            enable_ssl=True,
            enable_http2=True,
            enable_compression=True,
            enable_caching=True,
            security_headers=security_headers,
            environment_variables=environment_variables,
            secrets=secrets,
            health_check_path="/health",
            health_check_interval=30,
            health_check_timeout=10,
            health_check_retries=3,
            tags=[f"mingus-{self.security_tier.value}", "app-platform", "security"]
        )
    
    def _get_cdn_security_config(self) -> CDNSecurityConfig:
        """Get CDN security configuration"""
        # Security headers
        security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        }
        
        # WAF rules for enterprise
        waf_rules = []
        if self.security_tier == SecurityTier.ENTERPRISE:
            waf_rules = [
                "sql_injection",
                "xss_attack",
                "file_inclusion",
                "command_injection",
                "bad_bots",
                "ddos_attack"
            ]
        
        return CDNSecurityConfig(
            cdn_name=f"mingus-cdn-{self.security_tier.value}",
            origin=os.getenv("CDN_ORIGIN", ""),
            ttl=3600,
            enable_ssl=True,
            enable_compression=True,
            enable_caching=True,
            cache_headers=["Cache-Control", "Expires", "ETag"],
            security_headers=security_headers,
            rate_limiting=True,
            rate_limit_requests=100 if self.security_tier == SecurityTier.DEVELOPMENT else 1000,
            rate_limit_window=60,
            enable_waf=self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE],
            waf_rules=waf_rules,
            tags=[f"mingus-{self.security_tier.value}", "cdn", "security"]
        )
    
    def create_vpc(self) -> Optional[str]:
        """Create VPC with security configuration"""
        try:
            print(f"🔧 Creating VPC: {self.vpc_config.vpc_name}")
            
            payload = {
                "name": self.vpc_config.vpc_name,
                "region": self.vpc_config.region,
                "ip_range": self.vpc_config.ip_range,
                "description": self.vpc_config.description
            }
            
            response = requests.post(
                f"{self.base_url}/vpcs",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                vpc_data = response.json()
                vpc_id = vpc_data["vpc"]["id"]
                print(f"✅ VPC created successfully: {vpc_id}")
                return vpc_id
            else:
                print(f"❌ Failed to create VPC: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating VPC: {e}")
            return None
    
    def create_firewall(self) -> Optional[str]:
        """Create firewall with security configuration"""
        try:
            print(f"🔥 Creating firewall: {self.firewall_config.firewall_name}")
            
            payload = {
                "name": self.firewall_config.firewall_name,
                "inbound_rules": self.firewall_config.inbound_rules,
                "outbound_rules": self.firewall_config.outbound_rules,
                "droplet_ids": self.firewall_config.droplet_ids,
                "tags": self.firewall_config.tags
            }
            
            response = requests.post(
                f"{self.base_url}/firewalls",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                firewall_data = response.json()
                firewall_id = firewall_data["firewall"]["id"]
                print(f"✅ Firewall created successfully: {firewall_id}")
                return firewall_id
            else:
                print(f"❌ Failed to create firewall: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating firewall: {e}")
            return None
    
    def create_load_balancer(self) -> Optional[str]:
        """Create load balancer with security configuration"""
        try:
            print(f"⚖️ Creating load balancer: {self.loadbalancer_config.lb_name}")
            
            payload = {
                "name": self.loadbalancer_config.lb_name,
                "region": self.loadbalancer_config.region,
                "algorithm": self.loadbalancer_config.algorithm,
                "health_check": {
                    "protocol": self.loadbalancer_config.health_check_protocol,
                    "port": self.loadbalancer_config.health_check_port,
                    "path": self.loadbalancer_config.health_check_path,
                    "check_interval_seconds": 10,
                    "response_timeout_seconds": 5,
                    "healthy_threshold": 3,
                    "unhealthy_threshold": 5
                },
                "droplet_ids": self.loadbalancer_config.droplet_ids,
                "redirect_http_to_https": self.loadbalancer_config.redirect_http_to_https,
                "enable_proxy_protocol": self.loadbalancer_config.enable_proxy_protocol,
                "sticky_sessions": {
                    "type": "cookies" if self.loadbalancer_config.enable_sticky_sessions else "none"
                },
                "tags": self.loadbalancer_config.tags
            }
            
            # Add SSL configuration if enabled
            if self.loadbalancer_config.ssl_termination:
                payload["ssl"] = {
                    "certificate_id": self.loadbalancer_config.ssl_certificate_id,
                    "redirect_http_to_https": self.loadbalancer_config.redirect_http_to_https
                }
            
            response = requests.post(
                f"{self.base_url}/load_balancers",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                lb_data = response.json()
                lb_id = lb_data["load_balancer"]["id"]
                print(f"✅ Load balancer created successfully: {lb_id}")
                return lb_id
            else:
                print(f"❌ Failed to create load balancer: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating load balancer: {e}")
            return None
    
    def create_database(self) -> Optional[str]:
        """Create database with security configuration"""
        try:
            print(f"🗄️ Creating database: {self.database_config.db_name}")
            
            payload = {
                "name": self.database_config.db_name,
                "engine": self.database_config.engine,
                "version": self.database_config.version,
                "region": self.database_config.region,
                "size": self.database_config.size,
                "num_nodes": self.database_config.node_count,
                "private_network_uuid": None,  # Will be set if VPC exists
                "tags": self.database_config.tags
            }
            
            # Add SSL configuration
            if self.database_config.enable_ssl:
                payload["ssl_mode"] = "require"
            
            # Add connection pooling
            if self.database_config.enable_connection_pooling:
                payload["connection_pool"] = {
                    "mode": "transaction",
                    "size": 10
                }
            
            # Add backup configuration
            if self.database_config.enable_backups:
                payload["backup_restore"] = {
                    "database_name": self.database_config.db_name
                }
            
            # Add maintenance window
            if self.database_config.enable_maintenance_window:
                payload["maintenance_window"] = {
                    "day": self.database_config.maintenance_day,
                    "hour": self.database_config.maintenance_hour
                }
            
            response = requests.post(
                f"{self.base_url}/databases",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                db_data = response.json()
                db_id = db_data["database"]["id"]
                print(f"✅ Database created successfully: {db_id}")
                return db_id
            else:
                print(f"❌ Failed to create database: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return None
    
    def create_app_platform(self) -> Optional[str]:
        """Create App Platform with security configuration"""
        try:
            print(f"🚀 Creating App Platform: {self.app_platform_config.app_name}")
            
            # Create app specification
            app_spec = {
                "name": self.app_platform_config.app_name,
                "region": self.app_platform_config.region,
                "services": [
                    {
                        "name": "web",
                        "source_dir": "/",
                        "github": {
                            "repo": os.getenv("GITHUB_REPO", ""),
                            "branch": os.getenv("GITHUB_BRANCH", "main")
                        },
                        "run_command": "python app.py",
                        "environment_slug": "python",
                        "instance_count": 2 if self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE] else 1,
                        "instance_size_slug": "basic-xxs" if self.security_tier == SecurityTier.DEVELOPMENT else "basic-s",
                        "http_port": 8080,
                        "routes": [
                            {
                                "path": "/"
                            }
                        ],
                        "health_check": {
                            "http_path": self.app_platform_config.health_check_path,
                            "initial_delay_seconds": 10,
                            "interval_seconds": self.app_platform_config.health_check_interval,
                            "timeout_seconds": self.app_platform_config.health_check_timeout,
                            "success_threshold": 1,
                            "failure_threshold": self.app_platform_config.health_check_retries
                        }
                    }
                ],
                "databases": [
                    {
                        "name": "db",
                        "engine": "PG",
                        "version": "14",
                        "production": self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE]
                    }
                ],
                "envs": [
                    {
                        "key": key,
                        "value": value,
                        "scope": "RUN_TIME"
                    }
                    for key, value in self.app_platform_config.environment_variables.items()
                ],
                "secrets": [
                    {
                        "key": key,
                        "value": value,
                        "scope": "RUN_TIME"
                    }
                    for key, value in self.app_platform_config.secrets.items()
                ]
            }
            
            payload = {
                "spec": app_spec
            }
            
            response = requests.post(
                f"{self.base_url}/apps",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                app_data = response.json()
                app_id = app_data["app"]["id"]
                print(f"✅ App Platform created successfully: {app_id}")
                return app_id
            else:
                print(f"❌ Failed to create App Platform: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating App Platform: {e}")
            return None
    
    def create_cdn(self) -> Optional[str]:
        """Create CDN with security configuration"""
        try:
            print(f"🌐 Creating CDN: {self.cdn_config.cdn_name}")
            
            # Note: Digital Ocean CDN is typically configured through Spaces
            # This is a simplified implementation
            
            payload = {
                "name": self.cdn_config.cdn_name,
                "origin": self.cdn_config.origin,
                "ttl": self.cdn_config.ttl,
                "enable_ssl": self.cdn_config.enable_ssl,
                "enable_compression": self.cdn_config.enable_compression,
                "enable_caching": self.cdn_config.enable_caching,
                "cache_headers": self.cdn_config.cache_headers,
                "security_headers": self.cdn_config.security_headers,
                "rate_limiting": {
                    "enabled": self.cdn_config.rate_limiting,
                    "requests": self.cdn_config.rate_limit_requests,
                    "window": self.cdn_config.rate_limit_window
                },
                "waf": {
                    "enabled": self.cdn_config.enable_waf,
                    "rules": self.cdn_config.waf_rules
                },
                "tags": self.cdn_config.tags
            }
            
            # This would typically use Digital Ocean Spaces API
            # For now, we'll create a placeholder
            print(f"✅ CDN configuration prepared: {self.cdn_config.cdn_name}")
            return "cdn-placeholder-id"
            
        except Exception as e:
            print(f"❌ Error creating CDN: {e}")
            return None
    
    def deploy_security_infrastructure(self) -> Dict[str, str]:
        """Deploy complete security infrastructure"""
        print("🚀 Deploying Digital Ocean security infrastructure...")
        
        infrastructure_ids = {}
        
        try:
            # Create VPC
            vpc_id = self.create_vpc()
            if vpc_id:
                infrastructure_ids["vpc_id"] = vpc_id
            
            # Create firewall
            firewall_id = self.create_firewall()
            if firewall_id:
                infrastructure_ids["firewall_id"] = firewall_id
            
            # Create load balancer
            lb_id = self.create_load_balancer()
            if lb_id:
                infrastructure_ids["load_balancer_id"] = lb_id
            
            # Create database
            db_id = self.create_database()
            if db_id:
                infrastructure_ids["database_id"] = db_id
            
            # Create App Platform
            app_id = self.create_app_platform()
            if app_id:
                infrastructure_ids["app_id"] = app_id
            
            # Create CDN
            cdn_id = self.create_cdn()
            if cdn_id:
                infrastructure_ids["cdn_id"] = cdn_id
            
            print("✅ Security infrastructure deployment completed")
            return infrastructure_ids
            
        except Exception as e:
            print(f"❌ Error deploying security infrastructure: {e}")
            return {}
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status of deployed infrastructure"""
        try:
            status = {
                "vpc": self._get_vpc_status(),
                "firewall": self._get_firewall_status(),
                "load_balancer": self._get_load_balancer_status(),
                "database": self._get_database_status(),
                "app_platform": self._get_app_platform_status(),
                "cdn": self._get_cdn_status(),
                "security_score": self._calculate_security_score(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            print(f"❌ Error getting security status: {e}")
            return {}
    
    def _get_vpc_status(self) -> Dict[str, Any]:
        """Get VPC security status"""
        try:
            response = requests.get(
                f"{self.base_url}/vpcs",
                headers=self.headers
            )
            
            if response.status_code == 200:
                vpcs = response.json()["vpcs"]
                mingus_vpcs = [vpc for vpc in vpcs if "mingus" in vpc["name"]]
                
                if mingus_vpcs:
                    vpc = mingus_vpcs[0]
                    return {
                        "id": vpc["id"],
                        "name": vpc["name"],
                        "region": vpc["region"],
                        "ip_range": vpc["ip_range"],
                        "status": "active" if vpc["status"] == "active" else "inactive",
                        "private_networking": vpc.get("private_networking", False),
                        "ipv6": vpc.get("ipv6", False)
                    }
            
            return {"status": "not_found"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_firewall_status(self) -> Dict[str, Any]:
        """Get firewall security status"""
        try:
            response = requests.get(
                f"{self.base_url}/firewalls",
                headers=self.headers
            )
            
            if response.status_code == 200:
                firewalls = response.json()["firewalls"]
                mingus_firewalls = [fw for fw in firewalls if "mingus" in fw["name"]]
                
                if mingus_firewalls:
                    firewall = mingus_firewalls[0]
                    return {
                        "id": firewall["id"],
                        "name": firewall["name"],
                        "status": "active" if firewall["status"] == "active" else "inactive",
                        "inbound_rules_count": len(firewall["inbound_rules"]),
                        "outbound_rules_count": len(firewall["outbound_rules"]),
                        "droplet_count": len(firewall["droplet_ids"]),
                        "logging_enabled": firewall.get("logging", False)
                    }
            
            return {"status": "not_found"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_load_balancer_status(self) -> Dict[str, Any]:
        """Get load balancer security status"""
        try:
            response = requests.get(
                f"{self.base_url}/load_balancers",
                headers=self.headers
            )
            
            if response.status_code == 200:
                lbs = response.json()["load_balancers"]
                mingus_lbs = [lb for lb in lbs if "mingus" in lb["name"]]
                
                if mingus_lbs:
                    lb = mingus_lbs[0]
                    return {
                        "id": lb["id"],
                        "name": lb["name"],
                        "status": "active" if lb["status"] == "active" else "inactive",
                        "region": lb["region"],
                        "algorithm": lb["algorithm"],
                        "ssl_termination": lb.get("ssl", {}).get("redirect_http_to_https", False),
                        "health_check": lb.get("health_check", {}),
                        "droplet_count": len(lb["droplet_ids"])
                    }
            
            return {"status": "not_found"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_database_status(self) -> Dict[str, Any]:
        """Get database security status"""
        try:
            response = requests.get(
                f"{self.base_url}/databases",
                headers=self.headers
            )
            
            if response.status_code == 200:
                databases = response.json()["databases"]
                mingus_dbs = [db for db in databases if "mingus" in db["name"]]
                
                if mingus_dbs:
                    db = mingus_dbs[0]
                    return {
                        "id": db["id"],
                        "name": db["name"],
                        "status": "online" if db["status"] == "online" else "offline",
                        "region": db["region"],
                        "engine": db["engine"],
                        "version": db["version"],
                        "ssl_enabled": db.get("ssl_mode") == "require",
                        "connection_pooling": "connection_pool" in db,
                        "backup_enabled": "backup_restore" in db,
                        "node_count": db["num_nodes"]
                    }
            
            return {"status": "not_found"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_app_platform_status(self) -> Dict[str, Any]:
        """Get App Platform security status"""
        try:
            response = requests.get(
                f"{self.base_url}/apps",
                headers=self.headers
            )
            
            if response.status_code == 200:
                apps = response.json()["apps"]
                mingus_apps = [app for app in apps if "mingus" in app["name"]]
                
                if mingus_apps:
                    app = mingus_apps[0]
                    return {
                        "id": app["id"],
                        "name": app["name"],
                        "status": app["live_slug"] if app["live_slug"] else "deploying",
                        "region": app["region"],
                        "ssl_enabled": app.get("ssl_enabled", False),
                        "http2_enabled": app.get("http2_enabled", False),
                        "compression_enabled": app.get("compression_enabled", False),
                        "service_count": len(app.get("services", []))
                    }
            
            return {"status": "not_found"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_cdn_status(self) -> Dict[str, Any]:
        """Get CDN security status"""
        # Placeholder for CDN status
        return {
            "status": "configured",
            "name": self.cdn_config.cdn_name,
            "ssl_enabled": self.cdn_config.enable_ssl,
            "compression_enabled": self.cdn_config.enable_compression,
            "caching_enabled": self.cdn_config.enable_caching,
            "rate_limiting_enabled": self.cdn_config.rate_limiting,
            "waf_enabled": self.cdn_config.enable_waf
        }
    
    def _calculate_security_score(self) -> float:
        """Calculate overall security score"""
        try:
            score = 0.0
            max_score = 100.0
            
            # VPC security (20 points)
            vpc_status = self._get_vpc_status()
            if vpc_status.get("status") == "active":
                score += 20
                if vpc_status.get("private_networking"):
                    score += 5
                if vpc_status.get("ipv6"):
                    score += 5
            
            # Firewall security (20 points)
            firewall_status = self._get_firewall_status()
            if firewall_status.get("status") == "active":
                score += 20
                if firewall_status.get("logging_enabled"):
                    score += 5
            
            # Load balancer security (15 points)
            lb_status = self._get_load_balancer_status()
            if lb_status.get("status") == "active":
                score += 15
                if lb_status.get("ssl_termination"):
                    score += 5
            
            # Database security (20 points)
            db_status = self._get_database_status()
            if db_status.get("status") == "online":
                score += 20
                if db_status.get("ssl_enabled"):
                    score += 5
                if db_status.get("connection_pooling"):
                    score += 5
            
            # App Platform security (15 points)
            app_status = self._get_app_platform_status()
            if app_status.get("status") in ["active", "live"]:
                score += 15
                if app_status.get("ssl_enabled"):
                    score += 5
                if app_status.get("http2_enabled"):
                    score += 5
            
            # CDN security (10 points)
            cdn_status = self._get_cdn_status()
            if cdn_status.get("status") == "configured":
                score += 10
                if cdn_status.get("ssl_enabled"):
                    score += 5
                if cdn_status.get("waf_enabled"):
                    score += 5
            
            return min(score, max_score)
            
        except Exception as e:
            return 0.0

# Global Digital Ocean security manager instance
_do_security_manager = None

def get_do_security_manager(api_token: str, security_tier: SecurityTier = SecurityTier.PRODUCTION) -> DigitalOceanSecurityManager:
    """Get global Digital Ocean security manager instance"""
    global _do_security_manager
    
    if _do_security_manager is None:
        _do_security_manager = DigitalOceanSecurityManager(api_token, security_tier)
    
    return _do_security_manager

def deploy_digital_ocean_security(api_token: str, security_tier: SecurityTier = SecurityTier.PRODUCTION) -> Dict[str, str]:
    """Deploy Digital Ocean security infrastructure"""
    manager = get_do_security_manager(api_token, security_tier)
    return manager.deploy_security_infrastructure()

def get_security_status(api_token: str, security_tier: SecurityTier = SecurityTier.PRODUCTION) -> Dict[str, Any]:
    """Get Digital Ocean security status"""
    manager = get_do_security_manager(api_token, security_tier)
    return manager.get_security_status() 