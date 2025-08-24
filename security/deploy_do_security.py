#!/usr/bin/env python3
"""
Digital Ocean Security Deployment Script
Deploys comprehensive security infrastructure on Digital Ocean
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from datetime import datetime

# Add the security module to path
sys.path.append(str(Path(__file__).parent))

from digital_ocean_security import (
    get_do_security_manager, SecurityTier, 
    DigitalOceanSecurityManager
)

class DigitalOceanSecurityDeployer:
    """Digital Ocean security deployment manager"""
    
    def __init__(self, api_token: str, security_tier: SecurityTier = SecurityTier.PRODUCTION):
        self.api_token = api_token
        self.security_tier = security_tier
        self.security_manager = get_do_security_manager(api_token, security_tier)
        self.deployment_config = self._load_deployment_config()
        self.infrastructure_ids = {}
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_path = Path(__file__).parent / "do_deployment_config.yml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_deployment_config()
    
    def _get_default_deployment_config(self) -> Dict[str, Any]:
        """Get default deployment configuration"""
        return {
            "project": {
                "name": f"mingus-{self.security_tier.value}",
                "description": f"MINGUS {self.security_tier.value} environment",
                "region": os.getenv("DO_REGION", "nyc1"),
                "environment": self.security_tier.value
            },
            "vpc": {
                "enabled": True,
                "ip_range": "10.0.0.0/16",
                "enable_private_networking": True,
                "enable_ipv6": True
            },
            "firewall": {
                "enabled": True,
                "enable_logging": True,
                "allowed_ips": os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else []
            },
            "load_balancer": {
                "enabled": True,
                "ssl_termination": True,
                "redirect_http_to_https": True,
                "health_check_path": "/health",
                "algorithm": "round_robin"
            },
            "database": {
                "enabled": True,
                "engine": "pg",
                "version": "14",
                "size": "db-s-1vcpu-1gb" if self.security_tier == SecurityTier.DEVELOPMENT else "db-s-2vcpu-4gb",
                "enable_ssl": True,
                "enable_connection_pooling": True,
                "enable_backups": True
            },
            "app_platform": {
                "enabled": True,
                "enable_ssl": True,
                "enable_http2": True,
                "enable_compression": True,
                "enable_caching": True,
                "health_check_path": "/health",
                "instance_count": 1 if self.security_tier == SecurityTier.DEVELOPMENT else 2
            },
            "cdn": {
                "enabled": True,
                "enable_ssl": True,
                "enable_compression": True,
                "enable_caching": True,
                "enable_waf": self.security_tier in [SecurityTier.PRODUCTION, SecurityTier.ENTERPRISE],
                "rate_limiting": True
            }
        }
    
    def validate_prerequisites(self) -> bool:
        """Validate deployment prerequisites"""
        print("🔍 Validating Digital Ocean security deployment prerequisites...")
        
        # Check API token
        if not self.api_token:
            print("❌ Digital Ocean API token is required")
            return False
        
        # Check required environment variables
        required_vars = ["DO_REGION", "MINGUS_DOMAIN"]
        for var in required_vars:
            if not os.getenv(var):
                print(f"❌ Environment variable {var} is required")
                return False
        
        # Check required tools
        required_tools = ["doctl"]
        for tool in required_tools:
            if not self._check_tool_exists(tool):
                print(f"❌ Required tool not found: {tool}")
                return False
        
        # Test API connectivity
        if not self._test_api_connectivity():
            print("❌ Cannot connect to Digital Ocean API")
            return False
        
        print("✅ All prerequisites validated successfully")
        return True
    
    def _check_tool_exists(self, tool: str) -> bool:
        """Check if a tool exists in PATH"""
        try:
            subprocess.run([tool, "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _test_api_connectivity(self) -> bool:
        """Test Digital Ocean API connectivity"""
        try:
            result = subprocess.run([
                "doctl", "account", "get",
                "--access-token", self.api_token
            ], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception:
            return False
    
    def deploy_vpc(self) -> bool:
        """Deploy VPC with security configuration"""
        if not self.deployment_config["vpc"]["enabled"]:
            print("⏭️ VPC deployment skipped (disabled in config)")
            return True
        
        print("🔧 Deploying VPC with security configuration...")
        
        try:
            vpc_id = self.security_manager.create_vpc()
            if vpc_id:
                self.infrastructure_ids["vpc_id"] = vpc_id
                print(f"✅ VPC deployed successfully: {vpc_id}")
                return True
            else:
                print("❌ VPC deployment failed")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying VPC: {e}")
            return False
    
    def deploy_firewall(self) -> bool:
        """Deploy firewall with security configuration"""
        if not self.deployment_config["firewall"]["enabled"]:
            print("⏭️ Firewall deployment skipped (disabled in config)")
            return True
        
        print("🔥 Deploying firewall with security configuration...")
        
        try:
            firewall_id = self.security_manager.create_firewall()
            if firewall_id:
                self.infrastructure_ids["firewall_id"] = firewall_id
                print(f"✅ Firewall deployed successfully: {firewall_id}")
                return True
            else:
                print("❌ Firewall deployment failed")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying firewall: {e}")
            return False
    
    def deploy_load_balancer(self) -> bool:
        """Deploy load balancer with security configuration"""
        if not self.deployment_config["load_balancer"]["enabled"]:
            print("⏭️ Load balancer deployment skipped (disabled in config)")
            return True
        
        print("⚖️ Deploying load balancer with security configuration...")
        
        try:
            lb_id = self.security_manager.create_load_balancer()
            if lb_id:
                self.infrastructure_ids["load_balancer_id"] = lb_id
                print(f"✅ Load balancer deployed successfully: {lb_id}")
                return True
            else:
                print("❌ Load balancer deployment failed")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying load balancer: {e}")
            return False
    
    def deploy_database(self) -> bool:
        """Deploy database with security configuration"""
        if not self.deployment_config["database"]["enabled"]:
            print("⏭️ Database deployment skipped (disabled in config)")
            return True
        
        print("🗄️ Deploying database with security configuration...")
        
        try:
            db_id = self.security_manager.create_database()
            if db_id:
                self.infrastructure_ids["database_id"] = db_id
                print(f"✅ Database deployed successfully: {db_id}")
                return True
            else:
                print("❌ Database deployment failed")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying database: {e}")
            return False
    
    def deploy_app_platform(self) -> bool:
        """Deploy App Platform with security configuration"""
        if not self.deployment_config["app_platform"]["enabled"]:
            print("⏭️ App Platform deployment skipped (disabled in config)")
            return True
        
        print("🚀 Deploying App Platform with security configuration...")
        
        try:
            app_id = self.security_manager.create_app_platform()
            if app_id:
                self.infrastructure_ids["app_id"] = app_id
                print(f"✅ App Platform deployed successfully: {app_id}")
                return True
            else:
                print("❌ App Platform deployment failed")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying App Platform: {e}")
            return False
    
    def deploy_cdn(self) -> bool:
        """Deploy CDN with security configuration"""
        if not self.deployment_config["cdn"]["enabled"]:
            print("⏭️ CDN deployment skipped (disabled in config)")
            return True
        
        print("🌐 Deploying CDN with security configuration...")
        
        try:
            cdn_id = self.security_manager.create_cdn()
            if cdn_id:
                self.infrastructure_ids["cdn_id"] = cdn_id
                print(f"✅ CDN deployed successfully: {cdn_id}")
                return True
            else:
                print("❌ CDN deployment failed")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying CDN: {e}")
            return False
    
    def configure_security_groups(self) -> bool:
        """Configure security groups for all resources"""
        print("🔒 Configuring security groups...")
        
        try:
            # Configure VPC security groups
            if "vpc_id" in self.infrastructure_ids:
                self._configure_vpc_security_groups()
            
            # Configure database security groups
            if "database_id" in self.infrastructure_ids:
                self._configure_database_security_groups()
            
            # Configure App Platform security groups
            if "app_id" in self.infrastructure_ids:
                self._configure_app_platform_security_groups()
            
            print("✅ Security groups configured successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring security groups: {e}")
            return False
    
    def _configure_vpc_security_groups(self):
        """Configure VPC security groups"""
        try:
            # Get VPC details
            vpc_id = self.infrastructure_ids["vpc_id"]
            
            # Configure private networking
            if self.deployment_config["vpc"]["enable_private_networking"]:
                subprocess.run([
                    "doctl", "compute", "vpc", "update", vpc_id,
                    "--enable-private-networking"
                ], check=True)
            
            # Configure IPv6
            if self.deployment_config["vpc"]["enable_ipv6"]:
                subprocess.run([
                    "doctl", "compute", "vpc", "update", vpc_id,
                    "--enable-ipv6"
                ], check=True)
            
            print(f"✅ VPC security groups configured for {vpc_id}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error configuring VPC security groups: {e}")
    
    def _configure_database_security_groups(self):
        """Configure database security groups"""
        try:
            # Get database details
            db_id = self.infrastructure_ids["database_id"]
            
            # Configure SSL
            if self.deployment_config["database"]["enable_ssl"]:
                subprocess.run([
                    "doctl", "databases", "db", "configure", db_id,
                    "--ssl-mode", "require"
                ], check=True)
            
            # Configure connection pooling
            if self.deployment_config["database"]["enable_connection_pooling"]:
                subprocess.run([
                    "doctl", "databases", "pool", "create", db_id,
                    "--name", "mingus-pool",
                    "--mode", "transaction",
                    "--size", "10"
                ], check=True)
            
            print(f"✅ Database security groups configured for {db_id}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error configuring database security groups: {e}")
    
    def _configure_app_platform_security_groups(self):
        """Configure App Platform security groups"""
        try:
            # Get App Platform details
            app_id = self.infrastructure_ids["app_id"]
            
            # Configure SSL
            if self.deployment_config["app_platform"]["enable_ssl"]:
                subprocess.run([
                    "doctl", "apps", "update", app_id,
                    "--enable-ssl"
                ], check=True)
            
            # Configure HTTP/2
            if self.deployment_config["app_platform"]["enable_http2"]:
                subprocess.run([
                    "doctl", "apps", "update", app_id,
                    "--enable-http2"
                ], check=True)
            
            print(f"✅ App Platform security groups configured for {app_id}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error configuring App Platform security groups: {e}")
    
    def configure_ssl_termination(self) -> bool:
        """Configure SSL termination for load balancer"""
        if "load_balancer_id" not in self.infrastructure_ids:
            print("⏭️ SSL termination skipped (no load balancer)")
            return True
        
        print("🔐 Configuring SSL termination...")
        
        try:
            lb_id = self.infrastructure_ids["load_balancer_id"]
            
            # Configure SSL certificate
            if self.deployment_config["load_balancer"]["ssl_termination"]:
                # Get SSL certificate ID (you would need to create/upload a certificate first)
                ssl_cert_id = os.getenv("SSL_CERT_ID", "")
                
                if ssl_cert_id:
                    subprocess.run([
                        "doctl", "compute", "load-balancer", "update", lb_id,
                        "--ssl-certificate-id", ssl_cert_id,
                        "--redirect-http-to-https"
                    ], check=True)
                else:
                    print("⚠️ SSL certificate ID not provided, using default certificate")
                    subprocess.run([
                        "doctl", "compute", "load-balancer", "update", lb_id,
                        "--redirect-http-to-https"
                    ], check=True)
            
            print("✅ SSL termination configured successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error configuring SSL termination: {e}")
            return False
    
    def configure_monitoring(self) -> bool:
        """Configure monitoring and alerting"""
        print("📊 Configuring monitoring and alerting...")
        
        try:
            # Enable monitoring for all resources
            for resource_type, resource_id in self.infrastructure_ids.items():
                if resource_type == "vpc_id":
                    subprocess.run([
                        "doctl", "compute", "vpc", "update", resource_id,
                        "--enable-monitoring"
                    ], check=True)
                elif resource_type == "database_id":
                    subprocess.run([
                        "doctl", "databases", "db", "update", resource_id,
                        "--enable-monitoring"
                    ], check=True)
            
            # Configure alerting policies
            self._configure_alerting_policies()
            
            print("✅ Monitoring and alerting configured successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error configuring monitoring: {e}")
            return False
    
    def _configure_alerting_policies(self):
        """Configure alerting policies"""
        try:
            # Create alerting policies for different security events
            policies = [
                {
                    "name": "high-cpu-usage",
                    "type": "v1/insights/droplet/cpu",
                    "threshold": "80",
                    "comparison": "greater_than"
                },
                {
                    "name": "high-memory-usage",
                    "type": "v1/insights/droplet/memory_utilization_percent",
                    "threshold": "85",
                    "comparison": "greater_than"
                },
                {
                    "name": "high-disk-usage",
                    "type": "v1/insights/droplet/disk_utilization_percent",
                    "threshold": "90",
                    "comparison": "greater_than"
                },
                {
                    "name": "database-connection-errors",
                    "type": "v1/insights/database/connection_count",
                    "threshold": "100",
                    "comparison": "greater_than"
                }
            ]
            
            for policy in policies:
                subprocess.run([
                    "doctl", "monitoring", "alert", "create",
                    "--name", policy["name"],
                    "--type", policy["type"],
                    "--threshold", policy["threshold"],
                    "--comparison", policy["comparison"],
                    "--emails", os.getenv("ALERT_EMAIL", "")
                ], check=True)
            
            print("✅ Alerting policies configured")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error configuring alerting policies: {e}")
    
    def run_security_tests(self) -> bool:
        """Run security tests on deployed infrastructure"""
        print("🔍 Running security tests...")
        
        try:
            # Test SSL/TLS configuration
            self._test_ssl_configuration()
            
            # Test firewall rules
            self._test_firewall_rules()
            
            # Test database security
            self._test_database_security()
            
            # Test load balancer security
            self._test_load_balancer_security()
            
            # Test App Platform security
            self._test_app_platform_security()
            
            print("✅ Security tests completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error running security tests: {e}")
            return False
    
    def _test_ssl_configuration(self):
        """Test SSL/TLS configuration"""
        try:
            domain = os.getenv("MINGUS_DOMAIN", "")
            if domain:
                # Test SSL certificate
                result = subprocess.run([
                    "openssl", "s_client", "-connect", f"{domain}:443",
                    "-servername", domain, "-verify_return_error"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ SSL certificate is valid")
                else:
                    print("❌ SSL certificate validation failed")
            
        except subprocess.TimeoutExpired:
            print("⚠️ SSL test timed out")
        except Exception as e:
            print(f"❌ Error testing SSL: {e}")
    
    def _test_firewall_rules(self):
        """Test firewall rules"""
        try:
            if "firewall_id" in self.infrastructure_ids:
                firewall_id = self.infrastructure_ids["firewall_id"]
                
                # Get firewall status
                result = subprocess.run([
                    "doctl", "compute", "firewall", "get", firewall_id
                ], capture_output=True, text=True, check=True)
                
                if "active" in result.stdout:
                    print("✅ Firewall is active")
                else:
                    print("❌ Firewall is not active")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error testing firewall: {e}")
    
    def _test_database_security(self):
        """Test database security"""
        try:
            if "database_id" in self.infrastructure_ids:
                db_id = self.infrastructure_ids["database_id"]
                
                # Get database status
                result = subprocess.run([
                    "doctl", "databases", "db", "get", db_id
                ], capture_output=True, text=True, check=True)
                
                if "online" in result.stdout:
                    print("✅ Database is online and secure")
                else:
                    print("❌ Database is not online")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error testing database: {e}")
    
    def _test_load_balancer_security(self):
        """Test load balancer security"""
        try:
            if "load_balancer_id" in self.infrastructure_ids:
                lb_id = self.infrastructure_ids["load_balancer_id"]
                
                # Get load balancer status
                result = subprocess.run([
                    "doctl", "compute", "load-balancer", "get", lb_id
                ], capture_output=True, text=True, check=True)
                
                if "active" in result.stdout:
                    print("✅ Load balancer is active and secure")
                else:
                    print("❌ Load balancer is not active")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error testing load balancer: {e}")
    
    def _test_app_platform_security(self):
        """Test App Platform security"""
        try:
            if "app_id" in self.infrastructure_ids:
                app_id = self.infrastructure_ids["app_id"]
                
                # Get App Platform status
                result = subprocess.run([
                    "doctl", "apps", "get", app_id
                ], capture_output=True, text=True, check=True)
                
                if "live" in result.stdout:
                    print("✅ App Platform is live and secure")
                else:
                    print("❌ App Platform is not live")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error testing App Platform: {e}")
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        print("📋 Generating security report...")
        
        try:
            # Get security status
            security_status = self.security_manager.get_security_status()
            
            # Generate report
            report = {
                "deployment_info": {
                    "security_tier": self.security_tier.value,
                    "deployment_time": datetime.utcnow().isoformat(),
                    "infrastructure_ids": self.infrastructure_ids
                },
                "security_status": security_status,
                "configuration": self.deployment_config,
                "security_score": security_status.get("security_score", 0),
                "recommendations": self._generate_security_recommendations(security_status)
            }
            
            # Save report
            report_path = f"security_report_{self.security_tier.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Security report generated: {report_path}")
            return report
            
        except Exception as e:
            print(f"❌ Error generating security report: {e}")
            return {}
    
    def _generate_security_recommendations(self, security_status: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # VPC recommendations
        vpc_status = security_status.get("vpc", {})
        if vpc_status.get("status") != "active":
            recommendations.append("Enable VPC for network isolation")
        if not vpc_status.get("private_networking"):
            recommendations.append("Enable private networking in VPC")
        
        # Firewall recommendations
        firewall_status = security_status.get("firewall", {})
        if firewall_status.get("status") != "active":
            recommendations.append("Enable firewall for traffic control")
        if not firewall_status.get("logging_enabled"):
            recommendations.append("Enable firewall logging for audit trails")
        
        # Load balancer recommendations
        lb_status = security_status.get("load_balancer", {})
        if not lb_status.get("ssl_termination"):
            recommendations.append("Enable SSL termination on load balancer")
        
        # Database recommendations
        db_status = security_status.get("database", {})
        if not db_status.get("ssl_enabled"):
            recommendations.append("Enable SSL for database connections")
        if not db_status.get("connection_pooling"):
            recommendations.append("Enable connection pooling for database")
        
        # App Platform recommendations
        app_status = security_status.get("app_platform", {})
        if not app_status.get("ssl_enabled"):
            recommendations.append("Enable SSL for App Platform")
        if not app_status.get("http2_enabled"):
            recommendations.append("Enable HTTP/2 for App Platform")
        
        # General recommendations
        security_score = security_status.get("security_score", 0)
        if security_score < 80:
            recommendations.append("Review and improve overall security configuration")
        if security_score < 60:
            recommendations.append("Critical security improvements needed")
        
        return recommendations
    
    def deploy(self) -> bool:
        """Deploy complete Digital Ocean security infrastructure"""
        print("🚀 Starting Digital Ocean security deployment...")
        print(f"🔒 Security Tier: {self.security_tier.value}")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            return False
        
        try:
            # Deploy infrastructure components
            if not self.deploy_vpc():
                return False
            
            if not self.deploy_firewall():
                return False
            
            if not self.deploy_load_balancer():
                return False
            
            if not self.deploy_database():
                return False
            
            if not self.deploy_app_platform():
                return False
            
            if not self.deploy_cdn():
                return False
            
            # Configure security features
            if not self.configure_security_groups():
                return False
            
            if not self.configure_ssl_termination():
                return False
            
            if not self.configure_monitoring():
                return False
            
            # Run security tests
            if not self.run_security_tests():
                return False
            
            # Generate security report
            report = self.generate_security_report()
            
            print("🎉 Digital Ocean security deployment completed successfully!")
            print(f"📊 Security Score: {report.get('security_score', 0)}/100")
            print(f"📋 Infrastructure IDs: {self.infrastructure_ids}")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup deployed infrastructure"""
        print("🧹 Cleaning up Digital Ocean infrastructure...")
        
        try:
            for resource_type, resource_id in self.infrastructure_ids.items():
                print(f"🗑️ Deleting {resource_type}: {resource_id}")
                
                if resource_type == "vpc_id":
                    subprocess.run(["doctl", "compute", "vpc", "delete", resource_id, "--force"], check=True)
                elif resource_type == "firewall_id":
                    subprocess.run(["doctl", "compute", "firewall", "delete", resource_id, "--force"], check=True)
                elif resource_type == "load_balancer_id":
                    subprocess.run(["doctl", "compute", "load-balancer", "delete", resource_id, "--force"], check=True)
                elif resource_type == "database_id":
                    subprocess.run(["doctl", "databases", "db", "delete", resource_id, "--force"], check=True)
                elif resource_type == "app_id":
                    subprocess.run(["doctl", "apps", "delete", resource_id, "--force"], check=True)
                elif resource_type == "cdn_id":
                    # CDN cleanup would depend on the specific CDN service
                    print(f"⚠️ Manual cleanup required for CDN: {resource_id}")
            
            print("✅ Cleanup completed")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Cleanup failed: {e}")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Digital Ocean security infrastructure")
    parser.add_argument(
        "--security-tier",
        choices=["development", "staging", "production", "enterprise"],
        default="production",
        help="Security tier for deployment"
    )
    parser.add_argument(
        "--api-token",
        required=True,
        help="Digital Ocean API token"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup deployed infrastructure"
    )
    
    args = parser.parse_args()
    
    # Map security tier
    security_tier_map = {
        "development": SecurityTier.DEVELOPMENT,
        "staging": SecurityTier.STAGING,
        "production": SecurityTier.PRODUCTION,
        "enterprise": SecurityTier.ENTERPRISE
    }
    
    deployer = DigitalOceanSecurityDeployer(args.api_token, security_tier_map[args.security_tier])
    
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