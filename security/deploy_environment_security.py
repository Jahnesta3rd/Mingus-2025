#!/usr/bin/env python3
"""
Environment-Specific Security Deployment Script
Deploys comprehensive security configuration for different environments
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from datetime import datetime, timedelta
import secrets
from cryptography.fernet import Fernet

# Add the security module to path
sys.path.append(str(Path(__file__).parent))

from environment_security import (
    get_environment_security_manager, Environment, SecurityLevel, SecretType,
    EnvironmentSecurityManager
)

class EnvironmentSecurityDeployer:
    """Environment-specific security deployment manager"""
    
    def __init__(self, environment: Environment, base_path: str = "/var/lib/mingus/security"):
        self.environment = environment
        self.base_path = base_path
        self.security_manager = get_environment_security_manager(base_path)
        self.deployment_config = self._load_deployment_config()
        self.secrets_configured = {}
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_path = Path(__file__).parent / f"env_security_config_{self.environment.value}.yml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_deployment_config()
    
    def _get_default_deployment_config(self) -> Dict[str, Any]:
        """Get default deployment configuration"""
        return {
            "environment": {
                "name": self.environment.value,
                "security_level": "high" if self.environment == Environment.PRODUCTION else "medium",
                "base_path": self.base_path
            },
            "secrets": {
                "database": {
                    "enabled": True,
                    "secret_id": f"db_password_{self.environment.value}",
                    "description": f"Database password for {self.environment.value} environment"
                },
                "jwt": {
                    "enabled": True,
                    "secret_id": f"jwt_secret_{self.environment.value}",
                    "description": f"JWT secret for {self.environment.value} environment"
                },
                "api_keys": {
                    "enabled": True,
                    "secret_id": f"api_keys_{self.environment.value}",
                    "description": f"API keys for {self.environment.value} environment"
                },
                "encryption": {
                    "enabled": True,
                    "secret_id": f"encryption_key_{self.environment.value}",
                    "description": f"Encryption key for {self.environment.value} environment"
                }
            },
            "policies": {
                "password_policy": {
                    "enabled": True,
                    "min_length": 12 if self.environment == Environment.PRODUCTION else 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_special": self.environment == Environment.PRODUCTION,
                    "max_age_days": 60 if self.environment == Environment.PRODUCTION else 365
                },
                "session_policy": {
                    "enabled": True,
                    "timeout_minutes": 15 if self.environment == Environment.PRODUCTION else 60,
                    "max_concurrent_sessions": 1 if self.environment == Environment.PRODUCTION else 5,
                    "require_secure_cookies": True,
                    "require_https": True
                },
                "rate_limiting_policy": {
                    "enabled": True,
                    "requests_per_minute": 50 if self.environment == Environment.PRODUCTION else 1000,
                    "burst_limit": 100 if self.environment == Environment.PRODUCTION else 2000,
                    "block_duration_minutes": 30 if self.environment == Environment.PRODUCTION else 5
                },
                "encryption_policy": {
                    "enabled": True,
                    "require_ssl": True,
                    "min_tls_version": "1.3" if self.environment == Environment.PRODUCTION else "1.2",
                    "require_encryption_at_rest": True,
                    "require_encryption_in_transit": True
                }
            },
            "monitoring": {
                "enabled": True,
                "log_level": "WARNING" if self.environment == Environment.PRODUCTION else "INFO",
                "audit_logging": True,
                "security_alerts": True
            }
        }
    
    def validate_prerequisites(self) -> bool:
        """Validate deployment prerequisites"""
        print(f"🔍 Validating {self.environment.value} environment security prerequisites...")
        
        # Check base path
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
                print(f"✅ Created base path: {self.base_path}")
            except Exception as e:
                print(f"❌ Failed to create base path: {e}")
                return False
        
        # Check environment variables
        required_vars = self._get_required_environment_variables()
        for var in required_vars:
            if not os.getenv(var):
                print(f"❌ Environment variable {var} is required for {self.environment.value}")
                return False
        
        # Check required tools
        required_tools = ["openssl", "python3"]
        for tool in required_tools:
            if not self._check_tool_exists(tool):
                print(f"❌ Required tool not found: {tool}")
                return False
        
        print("✅ All prerequisites validated successfully")
        return True
    
    def _get_required_environment_variables(self) -> List[str]:
        """Get required environment variables for environment"""
        base_vars = ["MINGUS_ENV"]
        
        if self.environment == Environment.DEVELOPMENT:
            return base_vars
        elif self.environment == Environment.STAGING:
            return base_vars + ["STAGING_DB_PASSWORD", "STAGING_JWT_SECRET"]
        elif self.environment == Environment.PRODUCTION:
            return base_vars + [
                "PROD_DB_PASSWORD", "PROD_JWT_SECRET", "PROD_API_KEYS",
                "PROD_ENCRYPTION_KEY", "PROD_SSL_CERT_PATH", "PROD_SSL_KEY_PATH"
            ]
        
        return base_vars
    
    def _check_tool_exists(self, tool: str) -> bool:
        """Check if a tool exists in PATH"""
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def configure_environment_secrets(self) -> bool:
        """Configure environment-specific secrets"""
        print(f"🔐 Configuring secrets for {self.environment.value} environment...")
        
        try:
            secrets_config = self.deployment_config["secrets"]
            
            for secret_name, secret_config in secrets_config.items():
                if not secret_config.get("enabled", False):
                    continue
                
                secret_id = secret_config["secret_id"]
                description = secret_config["description"]
                
                # Get secret value from environment or generate
                secret_value = self._get_secret_value(secret_name, secret_id)
                
                if secret_value:
                    # Set secret
                    secret_type = self._get_secret_type(secret_name)
                    expires_at = self._get_secret_expiry(secret_name)
                    
                    success = self.security_manager.set_secret(
                        secret_id, secret_type, secret_value, 
                        self.environment, description, expires_at
                    )
                    
                    if success:
                        self.secrets_configured[secret_id] = True
                        print(f"✅ Secret {secret_id} configured successfully")
                    else:
                        print(f"❌ Failed to configure secret {secret_id}")
                        return False
                else:
                    print(f"⚠️ Skipping secret {secret_id} (no value provided)")
            
            print(f"✅ All secrets configured for {self.environment.value} environment")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring secrets: {e}")
            return False
    
    def _get_secret_value(self, secret_name: str, secret_id: str) -> Optional[str]:
        """Get secret value from environment or generate"""
        # Try to get from environment variable
        env_var = f"{self.environment.value.upper()}_{secret_name.upper()}"
        value = os.getenv(env_var)
        
        if value:
            return value
        
        # Generate default values for development
        if self.environment == Environment.DEVELOPMENT:
            if secret_name == "database":
                return "dev_password_123"
            elif secret_name == "jwt":
                return secrets.token_urlsafe(32)
            elif secret_name == "api_keys":
                return json.dumps({"default": "dev_api_key_123"})
            elif secret_name == "encryption":
                return Fernet.generate_key().decode()
        
        return None
    
    def _get_secret_type(self, secret_name: str) -> SecretType:
        """Get secret type from name"""
        type_mapping = {
            "database": SecretType.DATABASE_PASSWORD,
            "jwt": SecretType.JWT_SECRET,
            "api_keys": SecretType.API_KEY,
            "encryption": SecretType.ENCRYPTION_KEY,
            "ssl": SecretType.SSL_CERTIFICATE,
            "oauth": SecretType.OAUTH_SECRET,
            "ssh": SecretType.SSH_KEY,
            "access_token": SecretType.ACCESS_TOKEN
        }
        return type_mapping.get(secret_name, SecretType.API_KEY)
    
    def _get_secret_expiry(self, secret_name: str) -> Optional[datetime]:
        """Get secret expiry date"""
        if self.environment == Environment.PRODUCTION:
            # Production secrets expire in 90 days
            return datetime.utcnow() + timedelta(days=90)
        elif self.environment == Environment.STAGING:
            # Staging secrets expire in 180 days
            return datetime.utcnow() + timedelta(days=180)
        else:
            # Development secrets don't expire
            return None
    
    def configure_security_policies(self) -> bool:
        """Configure security policies for environment"""
        print(f"🛡️ Configuring security policies for {self.environment.value} environment...")
        
        try:
            policies_config = self.deployment_config["policies"]
            
            for policy_name, policy_config in policies_config.items():
                if not policy_config.get("enabled", False):
                    continue
                
                policy_id = f"{policy_name}_{self.environment.value}"
                
                # Create policy
                success = self.security_manager.policy_enforcer.create_policy(
                    policy_id,
                    self.environment,
                    policy_config.get("name", policy_name.replace("_", " ").title()),
                    policy_config.get("type", "general"),
                    policy_config
                )
                
                if success:
                    print(f"✅ Policy {policy_name} configured successfully")
                else:
                    print(f"❌ Failed to configure policy {policy_name}")
                    return False
            
            print(f"✅ All security policies configured for {self.environment.value} environment")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring security policies: {e}")
            return False
    
    def configure_environment_variables(self) -> bool:
        """Configure environment-specific variables"""
        print(f"🔧 Configuring environment variables for {self.environment.value} environment...")
        
        try:
            # Get environment configuration
            env_config = self.security_manager.get_environment_config(self.environment)
            
            if not env_config:
                print(f"❌ No configuration found for {self.environment.value} environment")
                return False
            
            # Create environment file
            env_file_path = os.path.join(self.base_path, f".env.{self.environment.value}")
            
            env_vars = {
                "MINGUS_ENV": self.environment.value,
                "SECURITY_LEVEL": env_config.security_level.value,
                "DEBUG": str(env_config.debug_enabled).lower(),
                "LOG_LEVEL": env_config.logging_level,
                "SSL_REQUIRED": str(env_config.ssl_required).lower(),
                "SESSION_TIMEOUT": str(env_config.session_timeout),
                "MAX_LOGIN_ATTEMPTS": str(env_config.max_login_attempts),
                "PASSWORD_MIN_LENGTH": str(env_config.password_min_length),
                "MFA_REQUIRED": str(env_config.mfa_required).lower(),
                "RATE_LIMITING_ENABLED": str(env_config.rate_limiting_enabled).lower(),
                "BACKUP_ENABLED": str(env_config.backup_enabled).lower(),
                "MONITORING_ENABLED": str(env_config.monitoring_enabled).lower(),
                "AUDIT_LOGGING_ENABLED": str(env_config.audit_logging_enabled).lower(),
                "ENCRYPTION_REQUIRED": str(env_config.encryption_required).lower(),
                "ALLOWED_HOSTS": ",".join(env_config.allowed_hosts),
                "CORS_ORIGINS": ",".join(env_config.cors_origins)
            }
            
            # Add security headers
            for header, value in env_config.security_headers.items():
                env_vars[f"SECURITY_HEADER_{header.replace('-', '_')}"] = value
            
            # Write environment file
            with open(env_file_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            print(f"✅ Environment variables configured: {env_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring environment variables: {e}")
            return False
    
    def validate_environment_configuration(self) -> bool:
        """Validate environment configuration"""
        print(f"🔍 Validating {self.environment.value} environment configuration...")
        
        try:
            # Validate environment config
            errors = self.security_manager.validate_environment_config(self.environment)
            
            if errors:
                print(f"❌ Environment configuration validation failed:")
                for error in errors:
                    print(f"   - {error}")
                return False
            
            # Validate secrets
            secrets_config = self.deployment_config["secrets"]
            for secret_name, secret_config in secrets_config.items():
                if secret_config.get("enabled", False):
                    secret_id = secret_config["secret_id"]
                    secret_value = self.security_manager.get_secret(secret_id, self.environment)
                    
                    if not secret_value:
                        print(f"❌ Secret {secret_id} not found or invalid")
                        return False
            
            # Validate policies
            policies_config = self.deployment_config["policies"]
            for policy_name, policy_config in policies_config.items():
                if policy_config.get("enabled", False):
                    policy_id = f"{policy_name}_{self.environment.value}"
                    policy = self.security_manager.policy_enforcer.get_policy(policy_id, self.environment)
                    
                    if not policy:
                        print(f"❌ Policy {policy_id} not found")
                        return False
            
            print(f"✅ {self.environment.value} environment configuration validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error validating environment configuration: {e}")
            return False
    
    def configure_monitoring(self) -> bool:
        """Configure monitoring for environment"""
        print(f"📊 Configuring monitoring for {self.environment.value} environment...")
        
        try:
            monitoring_config = self.deployment_config["monitoring"]
            
            if not monitoring_config.get("enabled", False):
                print("⏭️ Monitoring disabled for this environment")
                return True
            
            # Create monitoring configuration
            monitoring_file_path = os.path.join(self.base_path, f"monitoring_{self.environment.value}.yml")
            
            monitoring_config_data = {
                "environment": self.environment.value,
                "log_level": monitoring_config["log_level"],
                "audit_logging": monitoring_config["audit_logging"],
                "security_alerts": monitoring_config["security_alerts"],
                "alerts": {
                    "email": os.getenv("ALERT_EMAIL", ""),
                    "slack": os.getenv("SLACK_WEBHOOK_URL", ""),
                    "sms": os.getenv("SMS_NUMBER", "")
                },
                "metrics": {
                    "enabled": True,
                    "interval": 60,
                    "retention_days": 30 if self.environment == Environment.PRODUCTION else 7
                }
            }
            
            with open(monitoring_file_path, 'w') as f:
                yaml.dump(monitoring_config_data, f, default_flow_style=False)
            
            print(f"✅ Monitoring configured: {monitoring_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring monitoring: {e}")
            return False
    
    def run_security_tests(self) -> bool:
        """Run security tests for environment"""
        print(f"🧪 Running security tests for {self.environment.value} environment...")
        
        try:
            # Test environment configuration
            if not self._test_environment_config():
                return False
            
            # Test secrets
            if not self._test_secrets():
                return False
            
            # Test policies
            if not self._test_policies():
                return False
            
            # Test monitoring
            if not self._test_monitoring():
                return False
            
            print(f"✅ All security tests passed for {self.environment.value} environment")
            return True
            
        except Exception as e:
            print(f"❌ Error running security tests: {e}")
            return False
    
    def _test_environment_config(self) -> bool:
        """Test environment configuration"""
        try:
            env_config = self.security_manager.get_environment_config(self.environment)
            
            if not env_config:
                print("❌ Environment configuration not found")
                return False
            
            # Test security level
            if self.environment == Environment.PRODUCTION and env_config.security_level != SecurityLevel.HIGH:
                print("❌ Production environment must have HIGH security level")
                return False
            
            # Test SSL requirements
            if self.environment in [Environment.STAGING, Environment.PRODUCTION] and not env_config.ssl_required:
                print(f"❌ {self.environment.value} environment must require SSL")
                return False
            
            print("✅ Environment configuration test passed")
            return True
            
        except Exception as e:
            print(f"❌ Environment configuration test failed: {e}")
            return False
    
    def _test_secrets(self) -> bool:
        """Test secrets configuration"""
        try:
            secrets_config = self.deployment_config["secrets"]
            
            for secret_name, secret_config in secrets_config.items():
                if secret_config.get("enabled", False):
                    secret_id = secret_config["secret_id"]
                    secret_value = self.security_manager.get_secret(secret_id, self.environment)
                    
                    if not secret_value:
                        print(f"❌ Secret {secret_id} test failed")
                        return False
            
            print("✅ Secrets test passed")
            return True
            
        except Exception as e:
            print(f"❌ Secrets test failed: {e}")
            return False
    
    def _test_policies(self) -> bool:
        """Test security policies"""
        try:
            policies_config = self.deployment_config["policies"]
            
            for policy_name, policy_config in policies_config.items():
                if policy_config.get("enabled", False):
                    policy_id = f"{policy_name}_{self.environment.value}"
                    policy = self.security_manager.policy_enforcer.get_policy(policy_id, self.environment)
                    
                    if not policy:
                        print(f"❌ Policy {policy_id} test failed")
                        return False
            
            print("✅ Security policies test passed")
            return True
            
        except Exception as e:
            print(f"❌ Security policies test failed: {e}")
            return False
    
    def _test_monitoring(self) -> bool:
        """Test monitoring configuration"""
        try:
            monitoring_config = self.deployment_config["monitoring"]
            
            if monitoring_config.get("enabled", False):
                monitoring_file_path = os.path.join(self.base_path, f"monitoring_{self.environment.value}.yml")
                
                if not os.path.exists(monitoring_file_path):
                    print("❌ Monitoring configuration file not found")
                    return False
            
            print("✅ Monitoring test passed")
            return True
            
        except Exception as e:
            print(f"❌ Monitoring test failed: {e}")
            return False
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate security report for environment"""
        print(f"📋 Generating security report for {self.environment.value} environment...")
        
        try:
            # Get environment configuration
            env_config = self.security_manager.get_environment_config(self.environment)
            
            # Get secrets list
            secrets_list = self.security_manager.secret_manager.list_secrets(self.environment)
            
            # Get policies list
            policies_list = self.security_manager.policy_enforcer._get_applicable_policies(
                self.environment, "all"
            )
            
            # Generate report
            report = {
                "environment": self.environment.value,
                "deployment_time": datetime.utcnow().isoformat(),
                "configuration": {
                    "security_level": env_config.security_level.value if env_config else "unknown",
                    "ssl_required": env_config.ssl_required if env_config else False,
                    "mfa_required": env_config.mfa_required if env_config else False,
                    "encryption_required": env_config.encryption_required if env_config else False,
                    "audit_logging_enabled": env_config.audit_logging_enabled if env_config else False
                },
                "secrets": {
                    "total_secrets": len(secrets_list),
                    "configured_secrets": len(self.secrets_configured),
                    "secret_types": list(set([s["secret_type"] for s in secrets_list]))
                },
                "policies": {
                    "total_policies": len(policies_list),
                    "enabled_policies": len([p for p in policies_list if p["enabled"]]),
                    "policy_types": list(set([p["policy_type"] for p in policies_list]))
                },
                "monitoring": {
                    "enabled": self.deployment_config["monitoring"]["enabled"],
                    "log_level": self.deployment_config["monitoring"]["log_level"],
                    "audit_logging": self.deployment_config["monitoring"]["audit_logging"]
                },
                "security_score": self._calculate_security_score(env_config, secrets_list, policies_list)
            }
            
            # Save report
            report_path = os.path.join(self.base_path, f"security_report_{self.environment.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Security report generated: {report_path}")
            return report
            
        except Exception as e:
            print(f"❌ Error generating security report: {e}")
            return {}
    
    def _calculate_security_score(self, env_config, secrets_list, policies_list) -> float:
        """Calculate security score for environment"""
        try:
            score = 0.0
            max_score = 100.0
            
            # Environment configuration (30 points)
            if env_config:
                score += 30
                if env_config.security_level == SecurityLevel.HIGH:
                    score += 10
                if env_config.ssl_required:
                    score += 5
                if env_config.mfa_required:
                    score += 5
                if env_config.encryption_required:
                    score += 5
                if env_config.audit_logging_enabled:
                    score += 5
            
            # Secrets (25 points)
            if secrets_list:
                score += min(len(secrets_list) * 5, 25)
            
            # Policies (25 points)
            if policies_list:
                enabled_policies = [p for p in policies_list if p["enabled"]]
                score += min(len(enabled_policies) * 5, 25)
            
            # Monitoring (20 points)
            if self.deployment_config["monitoring"]["enabled"]:
                score += 20
            
            return min(score, max_score)
            
        except Exception as e:
            return 0.0
    
    def deploy(self) -> bool:
        """Deploy environment-specific security configuration"""
        print(f"🚀 Starting {self.environment.value} environment security deployment...")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            return False
        
        try:
            # Configure environment secrets
            if not self.configure_environment_secrets():
                return False
            
            # Configure security policies
            if not self.configure_security_policies():
                return False
            
            # Configure environment variables
            if not self.configure_environment_variables():
                return False
            
            # Configure monitoring
            if not self.configure_monitoring():
                return False
            
            # Validate configuration
            if not self.validate_environment_configuration():
                return False
            
            # Run security tests
            if not self.run_security_tests():
                return False
            
            # Generate security report
            report = self.generate_security_report()
            
            print(f"🎉 {self.environment.value} environment security deployment completed successfully!")
            print(f"📊 Security Score: {report.get('security_score', 0)}/100")
            print(f"🔐 Secrets Configured: {len(self.secrets_configured)}")
            print(f"🛡️ Policies Enabled: {report.get('policies', {}).get('enabled_policies', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy environment-specific security configuration")
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        required=True,
        help="Environment to deploy"
    )
    parser.add_argument(
        "--base-path",
        default="/var/lib/mingus/security",
        help="Base path for security configuration"
    )
    
    args = parser.parse_args()
    
    # Map environment
    environment_map = {
        "development": Environment.DEVELOPMENT,
        "staging": Environment.STAGING,
        "production": Environment.PRODUCTION
    }
    
    deployer = EnvironmentSecurityDeployer(environment_map[args.environment], args.base_path)
    
    try:
        success = deployer.deploy()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 