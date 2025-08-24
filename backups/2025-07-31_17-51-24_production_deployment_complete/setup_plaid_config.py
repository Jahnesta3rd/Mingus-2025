#!/usr/bin/env python3
"""
Plaid Configuration Setup Script for MINGUS

This script helps configure Plaid integration for different environments:
- Development/Sandbox setup
- Production setup
- Webhook configuration
- Environment validation
"""

import os
import sys
import json
import requests
import hmac
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
import argparse
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.plaid_config import PlaidConfigManager, PlaidEnvironment, validate_plaid_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaidConfigSetup:
    """Handles Plaid configuration setup and validation"""
    
    def __init__(self):
        self.config_manager = PlaidConfigManager()
        self.setup_dir = project_root / "config" / "environments"
        
    def setup_development_environment(self, interactive: bool = True) -> bool:
        """Set up development/sandbox environment"""
        logger.info("Setting up Plaid Development/Sandbox Environment")
        
        env_file = self.setup_dir / "development.env"
        example_file = self.setup_dir / "development.env.example"
        
        if not example_file.exists():
            logger.error(f"Example file not found: {example_file}")
            return False
        
        # Copy example file if it doesn't exist
        if not env_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            logger.info(f"Created development environment file: {env_file}")
        
        if interactive:
            return self._configure_development_interactive(env_file)
        else:
            logger.info("Development environment file created. Please edit it manually.")
            return True
    
    def setup_production_environment(self, interactive: bool = True) -> bool:
        """Set up production environment"""
        logger.info("Setting up Plaid Production Environment")
        
        env_file = self.setup_dir / "production.env"
        example_file = self.setup_dir / "production.env.example"
        
        if not example_file.exists():
            logger.error(f"Example file not found: {example_file}")
            return False
        
        # Copy example file if it doesn't exist
        if not env_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            logger.info(f"Created production environment file: {env_file}")
        
        if interactive:
            return self._configure_production_interactive(env_file)
        else:
            logger.info("Production environment file created. Please edit it manually.")
            return True
    
    def _configure_development_interactive(self, env_file: Path) -> bool:
        """Interactive development configuration"""
        logger.info("Interactive Development Configuration")
        
        config = {}
        
        # Get Plaid Sandbox credentials
        print("\n=== Plaid Sandbox Configuration ===")
        config['PLAID_ENV'] = 'sandbox'
        config['PLAID_SANDBOX_CLIENT_ID'] = input("Enter your Plaid Sandbox Client ID: ").strip()
        config['PLAID_SANDBOX_SECRET'] = input("Enter your Plaid Sandbox Secret: ").strip()
        
        # Get webhook configuration
        print("\n=== Webhook Configuration ===")
        webhook_url = input("Enter your webhook URL (or press Enter for ngrok setup): ").strip()
        
        if not webhook_url:
            print("Setting up ngrok for local webhook testing...")
            webhook_url = self._setup_ngrok_webhook()
        
        config['PLAID_SANDBOX_WEBHOOK_URL'] = webhook_url
        config['PLAID_SANDBOX_WEBHOOK_SECRET'] = input("Enter your webhook secret (or press Enter to generate): ").strip()
        
        if not config['PLAID_SANDBOX_WEBHOOK_SECRET']:
            config['PLAID_SANDBOX_WEBHOOK_SECRET'] = self._generate_webhook_secret()
            print(f"Generated webhook secret: {config['PLAID_SANDBOX_WEBHOOK_SECRET']}")
        
        # Get redirect URI
        config['PLAID_SANDBOX_REDIRECT_URI'] = input("Enter your redirect URI (or press Enter for default): ").strip()
        if not config['PLAID_SANDBOX_REDIRECT_URI']:
            config['PLAID_SANDBOX_REDIRECT_URI'] = "http://localhost:5000/plaid/callback"
        
        # Security configuration
        print("\n=== Security Configuration ===")
        encryption_key = input("Enter encryption key for access tokens (or press Enter to generate): ").strip()
        if not encryption_key:
            encryption_key = self._generate_encryption_key()
            print(f"Generated encryption key: {encryption_key}")
        config['PLAID_SANDBOX_ENCRYPTION_KEY'] = encryption_key
        
        # Write configuration to file
        return self._write_env_file(env_file, config)
    
    def _configure_production_interactive(self, env_file: Path) -> bool:
        """Interactive production configuration"""
        logger.info("Interactive Production Configuration")
        
        config = {}
        
        # Get Plaid Production credentials
        print("\n=== Plaid Production Configuration ===")
        config['PLAID_ENV'] = 'production'
        config['PLAID_PRODUCTION_CLIENT_ID'] = input("Enter your Plaid Production Client ID: ").strip()
        config['PLAID_PRODUCTION_SECRET'] = input("Enter your Plaid Production Secret: ").strip()
        
        # Get webhook configuration
        print("\n=== Production Webhook Configuration ===")
        webhook_url = input("Enter your production webhook URL (MUST be HTTPS): ").strip()
        
        if not webhook_url.startswith('https://'):
            logger.error("Production webhook URL must use HTTPS")
            return False
        
        config['PLAID_PRODUCTION_WEBHOOK_URL'] = webhook_url
        config['PLAID_PRODUCTION_WEBHOOK_SECRET'] = input("Enter your production webhook secret: ").strip()
        
        if not config['PLAID_PRODUCTION_WEBHOOK_SECRET']:
            logger.error("Production webhook secret is required")
            return False
        
        # Get redirect URI
        config['PLAID_PRODUCTION_REDIRECT_URI'] = input("Enter your production redirect URI (MUST be HTTPS): ").strip()
        
        if not config['PLAID_PRODUCTION_REDIRECT_URI'].startswith('https://'):
            logger.error("Production redirect URI must use HTTPS")
            return False
        
        # Security configuration
        print("\n=== Production Security Configuration ===")
        encryption_key = input("Enter encryption key for access tokens (REQUIRED for production): ").strip()
        
        if not encryption_key:
            logger.error("Encryption key is required for production")
            return False
        
        config['PLAID_PRODUCTION_ENCRYPTION_KEY'] = encryption_key
        
        # Additional production settings
        print("\n=== Additional Production Settings ===")
        config['SECRET_KEY'] = input("Enter Flask secret key (or press Enter to generate): ").strip()
        if not config['SECRET_KEY']:
            config['SECRET_KEY'] = self._generate_secret_key()
            print(f"Generated Flask secret key: {config['SECRET_KEY']}")
        
        # Write configuration to file
        return self._write_env_file(env_file, config)
    
    def _setup_ngrok_webhook(self) -> str:
        """Set up ngrok for local webhook testing"""
        try:
            # Check if ngrok is installed
            import subprocess
            result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("ngrok not found. Please install ngrok from https://ngrok.com/")
                print("After installation, run: ngrok http 5000")
                return input("Enter your ngrok webhook URL: ").strip()
            
            # Start ngrok
            print("Starting ngrok...")
            ngrok_process = subprocess.Popen(
                ['ngrok', 'http', '5000'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment for ngrok to start
            import time
            time.sleep(3)
            
            # Get ngrok URL
            try:
                response = requests.get('http://localhost:4040/api/tunnels')
                tunnels = response.json()['tunnels']
                https_tunnel = next((t for t in tunnels if t['proto'] == 'https'), None)
                
                if https_tunnel:
                    webhook_url = f"{https_tunnel['public_url']}/api/plaid/webhook"
                    print(f"ngrok webhook URL: {webhook_url}")
                    return webhook_url
                else:
                    raise Exception("No HTTPS tunnel found")
                    
            except Exception as e:
                logger.error(f"Error getting ngrok URL: {e}")
                return input("Enter your ngrok webhook URL manually: ").strip()
                
        except Exception as e:
            logger.error(f"Error setting up ngrok: {e}")
            return input("Enter your webhook URL manually: ").strip()
    
    def _generate_webhook_secret(self) -> str:
        """Generate a secure webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _generate_secret_key(self) -> str:
        """Generate a secure Flask secret key"""
        import secrets
        return secrets.token_urlsafe(64)
    
    def _write_env_file(self, env_file: Path, config: Dict[str, str]) -> bool:
        """Write configuration to environment file"""
        try:
            # Read existing file
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()
            else:
                content = ""
            
            # Update configuration values
            for key, value in config.items():
                # Find and replace existing values
                pattern = f"{key}="
                if pattern in content:
                    # Replace existing value
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(pattern):
                            lines[i] = f"{key}={value}"
                            break
                    content = '\n'.join(lines)
                else:
                    # Add new value
                    content += f"\n{key}={value}"
            
            # Write updated content
            with open(env_file, 'w') as f:
                f.write(content)
            
            logger.info(f"Configuration written to {env_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing configuration file: {e}")
            return False
    
    def validate_environment(self, environment: str) -> bool:
        """Validate environment configuration"""
        try:
            if environment.lower() in ['sandbox', 'development']:
                env = PlaidEnvironment.SANDBOX
            elif environment.lower() == 'production':
                env = PlaidEnvironment.PRODUCTION
            else:
                logger.error(f"Invalid environment: {environment}")
                return False
            
            # Load environment variables
            env_file = self.setup_dir / f"{environment.lower()}.env"
            if env_file.exists():
                self._load_env_file(env_file)
            
            # Validate configuration
            config = self.config_manager.get_config(env)
            is_valid = self.config_manager.validate_config(config)
            
            if is_valid:
                logger.info(f"✅ {environment} environment configuration is valid")
                
                # Test Plaid API connection
                if self._test_plaid_connection(config):
                    logger.info("✅ Plaid API connection successful")
                else:
                    logger.warning("⚠️ Plaid API connection failed")
                
                # Test webhook endpoint
                if self._test_webhook_endpoint(config):
                    logger.info("✅ Webhook endpoint is accessible")
                else:
                    logger.warning("⚠️ Webhook endpoint test failed")
                
            else:
                logger.error(f"❌ {environment} environment configuration is invalid")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating environment: {e}")
            return False
    
    def _load_env_file(self, env_file: Path):
        """Load environment variables from file"""
        if not env_file.exists():
            return
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    def _test_plaid_connection(self, config) -> bool:
        """Test Plaid API connection"""
        try:
            import plaid
            from plaid.api import plaid_api
            
            # Configure Plaid client
            plaid_config = plaid.Configuration(
                host=plaid.Environment.Sandbox if config.environment == PlaidEnvironment.SANDBOX else plaid.Environment.Production,
                api_key={
                    'clientId': config.client_id,
                    'secret': config.secret,
                }
            )
            
            api_client = plaid.ApiClient(plaid_config)
            institutions_api = plaid_api.InstitutionsApi(api_client)
            
            # Test API call
            response = institutions_api.institutions_search(
                query="Chase",
                products=["auth"],
                country_codes=["US"]
            )
            
            return len(response.institutions) > 0
            
        except Exception as e:
            logger.error(f"Plaid API connection test failed: {e}")
            return False
    
    def _test_webhook_endpoint(self, config) -> bool:
        """Test webhook endpoint accessibility"""
        try:
            # Send a test request to the webhook endpoint
            test_data = {
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "TRANSACTIONS_DEFAULT_UPDATE",
                "item_id": "test_item_id",
                "environment": config.environment.value,
                "timestamp": "2025-01-27T00:00:00Z",
                "new_transactions": 0
            }
            
            response = requests.post(
                config.webhook.webhook_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"Webhook endpoint test failed: {e}")
            return False
    
    def setup_webhook_verification(self, environment: str) -> bool:
        """Set up webhook verification for the specified environment"""
        try:
            if environment.lower() in ['sandbox', 'development']:
                env = PlaidEnvironment.SANDBOX
            elif environment.lower() == 'production':
                env = PlaidEnvironment.PRODUCTION
            else:
                logger.error(f"Invalid environment: {environment}")
                return False
            
            config = self.config_manager.get_config(env)
            
            print(f"\n=== Webhook Verification Setup for {environment.upper()} ===")
            print(f"Webhook URL: {config.webhook.webhook_url}")
            print(f"Webhook Secret: {config.webhook.webhook_secret}")
            
            # Test webhook signature verification
            test_payload = b'{"test": "data"}'
            test_signature = "v0=test_signature"
            
            if config.webhook.webhook_secret:
                expected_signature = hmac.new(
                    config.webhook.webhook_secret.encode('utf-8'),
                    test_payload,
                    hashlib.sha256
                ).hexdigest()
                
                print(f"Expected signature format: v0={expected_signature}")
                print("✅ Webhook signature verification is configured")
            else:
                print("⚠️ No webhook secret configured - signature verification disabled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up webhook verification: {e}")
            return False

def main():
    """Main function for the setup script"""
    parser = argparse.ArgumentParser(description='Plaid Configuration Setup for MINGUS')
    parser.add_argument('--environment', '-e', choices=['development', 'production', 'both'], 
                       default='both', help='Environment to configure')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('--validate', '-v', action='store_true', 
                       help='Validate existing configuration')
    parser.add_argument('--webhook-setup', '-w', action='store_true', 
                       help='Set up webhook verification')
    
    args = parser.parse_args()
    
    setup = PlaidConfigSetup()
    
    if args.validate:
        if args.environment in ['development', 'both']:
            setup.validate_environment('development')
        if args.environment in ['production', 'both']:
            setup.validate_environment('production')
        return
    
    if args.webhook_setup:
        if args.environment in ['development', 'both']:
            setup.setup_webhook_verification('development')
        if args.environment in ['production', 'both']:
            setup.setup_webhook_verification('production')
        return
    
    # Setup environments
    success = True
    
    if args.environment in ['development', 'both']:
        if not setup.setup_development_environment(args.interactive):
            success = False
    
    if args.environment in ['production', 'both']:
        if not setup.setup_production_environment(args.interactive):
            success = False
    
    if success:
        print("\n✅ Plaid configuration setup completed successfully!")
        print("\nNext steps:")
        print("1. Review and edit the generated .env files")
        print("2. Run validation: python scripts/setup_plaid_config.py --validate")
        print("3. Test webhook setup: python scripts/setup_plaid_config.py --webhook-setup")
        print("4. Start your application and test Plaid integration")
    else:
        print("\n❌ Plaid configuration setup failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 