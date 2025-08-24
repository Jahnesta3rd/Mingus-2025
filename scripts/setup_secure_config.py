#!/usr/bin/env python3
"""
Secure Configuration Setup Script for MINGUS Application
======================================================

This script sets up the secure configuration system for the MINGUS application,
including environment file creation, secret generation, and validation.

Usage:
    python scripts/setup_secure_config.py [--env-file .env] [--interactive] [--auto]

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import argparse
import secrets
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecureConfigSetup:
    """Secure configuration setup manager"""
    
    def __init__(self, env_file: str = '.env', interactive: bool = True):
        """
        Initialize setup manager
        
        Args:
            env_file: Path to environment file
            interactive: Enable interactive mode
        """
        self.env_file = Path(env_file)
        self.interactive = interactive
        self.template_file = Path('env.template')
        
    def run_setup(self):
        """Run the complete setup process"""
        print("\n" + "="*80)
        print("MINGUS APPLICATION - SECURE CONFIGURATION SETUP")
        print("="*80)
        
        try:
            # Step 1: Check prerequisites
            self._check_prerequisites()
            
            # Step 2: Create environment file
            self._create_env_file()
            
            # Step 3: Generate secure secrets
            self._generate_secrets()
            
            # Step 4: Validate configuration
            self._validate_configuration()
            
            # Step 5: Setup instructions
            self._show_setup_instructions()
            
            print("\n✅ Secure configuration setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)
    
    def _check_prerequisites(self):
        """Check setup prerequisites"""
        print("\n🔍 Checking prerequisites...")
        
        # Check if template exists
        if not self.template_file.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_file}")
        
        # Check if .gitignore includes .env
        gitignore_file = Path('.gitignore')
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
                if '.env' not in gitignore_content:
                    print("⚠️  Warning: .env not found in .gitignore")
                    if self.interactive:
                        response = input("Add .env to .gitignore? (y/n): ").lower().strip()
                        if response == 'y':
                            self._update_gitignore()
        
        # Check Python dependencies
        self._check_dependencies()
        
        print("✅ Prerequisites check completed")
    
    def _check_dependencies(self):
        """Check required Python dependencies"""
        required_packages = [
            'cryptography',
            'flask',
            'redis',
            'psycopg2-binary'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
            if self.interactive:
                response = input("Install missing packages? (y/n): ").lower().strip()
                if response == 'y':
                    self._install_packages(missing_packages)
    
    def _install_packages(self, packages: list):
        """Install missing packages"""
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + packages)
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
    
    def _update_gitignore(self):
        """Update .gitignore to include .env"""
        gitignore_file = Path('.gitignore')
        
        with open(gitignore_file, 'a') as f:
            f.write('\n# Environment files\n.env\n*.env\n')
        
        print("✅ Updated .gitignore")
    
    def _create_env_file(self):
        """Create environment file from template"""
        print(f"\n📝 Creating environment file: {self.env_file}")
        
        if self.env_file.exists():
            if self.interactive:
                response = input(f"Environment file {self.env_file} already exists. Overwrite? (y/n): ").lower().strip()
                if response != 'y':
                    print("Skipping environment file creation")
                    return
            else:
                print(f"Environment file {self.env_file} already exists, skipping creation")
                return
        
        # Copy template to env file
        shutil.copy2(self.template_file, self.env_file)
        print(f"✅ Created environment file: {self.env_file}")
        
        if self.interactive:
            print(f"\n📝 Please edit {self.env_file} and fill in your configuration values.")
            response = input("Open file for editing? (y/n): ").lower().strip()
            if response == 'y':
                self._open_file_for_editing()
    
    def _open_file_for_editing(self):
        """Open environment file for editing"""
        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', str(self.env_file)])
            elif sys.platform.startswith('win32'):  # Windows
                subprocess.run(['notepad', str(self.env_file)])
            else:  # Linux
                subprocess.run(['xdg-open', str(self.env_file)])
        except Exception as e:
            print(f"Could not open file automatically: {e}")
            print(f"Please manually edit: {self.env_file}")
    
    def _generate_secrets(self):
        """Generate secure secrets for the environment file"""
        print("\n🔐 Generating secure secrets...")
        
        secrets_to_generate = {
            'SECRET_KEY': self._generate_flask_secret(),
            'FIELD_ENCRYPTION_KEY': self._generate_encryption_key(),
            'DJANGO_SECRET_KEY': self._generate_django_secret(),
            'CONFIG_ENCRYPTION_KEY': self._generate_config_encryption_key(),
        }
        
        # Update environment file with generated secrets
        self._update_env_file_secrets(secrets_to_generate)
        
        print("✅ Generated secure secrets")
    
    def _generate_flask_secret(self) -> str:
        """Generate Flask secret key"""
        return secrets.token_hex(32)
    
    def _generate_encryption_key(self) -> str:
        """Generate encryption key"""
        return secrets.token_hex(32)
    
    def _generate_django_secret(self) -> str:
        """Generate Django secret key"""
        return secrets.token_urlsafe(50)
    
    def _generate_config_encryption_key(self) -> str:
        """Generate configuration encryption key"""
        return secrets.token_urlsafe(32)
    
    def _update_env_file_secrets(self, secrets_dict: Dict[str, str]):
        """Update environment file with generated secrets"""
        if not self.env_file.exists():
            return
        
        # Read current file
        with open(self.env_file, 'r') as f:
            lines = f.readlines()
        
        # Update secrets
        updated_lines = []
        updated_secrets = set()
        
        for line in lines:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                
                if key in secrets_dict:
                    # Update with generated secret
                    new_value = secrets_dict[key]
                    updated_lines.append(f"{key}={new_value}\n")
                    updated_secrets.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Write updated file
        with open(self.env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"Updated {len(updated_secrets)} secrets in {self.env_file}")
    
    def _validate_configuration(self):
        """Validate the configuration"""
        print("\n🔍 Validating configuration...")
        
        try:
            # Run validation script
            result = subprocess.run([
                sys.executable, 'scripts/validate_config.py',
                '--env-file', str(self.env_file),
                '--verbose'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Configuration validation passed")
                if self.interactive:
                    print("\n" + result.stdout)
            else:
                print("⚠️  Configuration validation found issues:")
                print(result.stdout)
                print(result.stderr)
                
                if self.interactive:
                    response = input("Continue anyway? (y/n): ").lower().strip()
                    if response != 'y':
                        raise Exception("Configuration validation failed")
        
        except FileNotFoundError:
            print("⚠️  Validation script not found, skipping validation")
        except Exception as e:
            print(f"⚠️  Validation failed: {e}")
    
    def _show_setup_instructions(self):
        """Show post-setup instructions"""
        print("\n" + "="*80)
        print("SETUP COMPLETED - NEXT STEPS")
        print("="*80)
        
        instructions = [
            "1. Review and update the environment file with your actual values:",
            f"   - Edit {self.env_file}",
            "   - Fill in database connection details",
            "   - Add external service API keys (Stripe, Plaid, etc.)",
            "   - Configure email and SMS settings",
            "",
            "2. Test the configuration:",
            "   python scripts/validate_config.py --env-file .env --verbose",
            "",
            "3. Start the application:",
            "   python backend/app.py",
            "",
            "4. For production deployment:",
            "   - Set FLASK_ENV=production",
            "   - Configure production database",
            "   - Set up SSL certificates",
            "   - Enable monitoring and logging",
            "",
            "5. Regular maintenance:",
            "   - Rotate secrets every 90 days: python scripts/rotate_secrets.py --backup",
            "   - Monitor configuration changes: python scripts/validate_config.py",
            "   - Keep dependencies updated",
            "",
            "🔐 SECURITY REMINDERS:",
            "- Never commit .env files to version control",
            "- Use strong, unique passwords for all services",
            "- Enable 2FA on all external service accounts",
            "- Regularly audit configuration access",
            "- Monitor for suspicious activity",
            "",
            "📚 Documentation:",
            "- See env.template for detailed variable descriptions",
            "- Check config/secure_config.py for advanced features",
            "- Review scripts/validate_config.py for validation options",
        ]
        
        for instruction in instructions:
            print(instruction)
        
        print("\n" + "="*80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Setup secure configuration for MINGUS application')
    parser.add_argument('--env-file', default='.env', help='Path to environment file')
    parser.add_argument('--interactive', action='store_true', default=True, help='Enable interactive mode')
    parser.add_argument('--auto', action='store_true', help='Run in automatic mode (non-interactive)')
    parser.add_argument('--skip-validation', action='store_true', help='Skip configuration validation')
    
    args = parser.parse_args()
    
    # Set interactive mode
    if args.auto:
        args.interactive = False
    
    try:
        # Initialize setup
        setup = SecureConfigSetup(args.env_file, args.interactive)
        
        # Run setup
        setup.run_setup()
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 