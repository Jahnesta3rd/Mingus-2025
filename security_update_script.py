#!/usr/bin/env python3
"""
Mingus Financial Application - Security Update Automation Script
Senior DevOps Engineer Implementation

This script automates the security updates identified in the vulnerability analysis.
It includes proper error handling, rollback procedures, and comprehensive testing.
"""

import subprocess
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'security_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecurityUpdater:
    """Automated security update manager for Mingus financial application"""
    
    def __init__(self, dry_run: bool = False, backup_dir: str = "backups"):
        self.dry_run = dry_run
        self.backup_dir = backup_dir
        self.backup_file = None
        self.rollback_data = {}
        self.update_results = {}
        
        # Define update phases with packages and their target versions
        self.update_phases = {
            "phase1_critical": {
                "description": "Critical Security Updates (24-48 hours)",
                "packages": {
                    "gunicorn": ">=23.0.0",
                    "cryptography": ">=44.0.1",
                    "requests": ">=2.32.4"
                }
            },
            "phase2_web_security": {
                "description": "Web Framework Security Updates",
                "packages": {
                    "Flask-CORS": ">=6.0.0",
                    "aiohttp": ">=3.12.14",
                    "h2": ">=4.3.0"
                }
            },
            "phase3_high_risk": {
                "description": "High-Risk Development Tools",
                "packages": {
                    "black": ">=24.3.0",
                    "jupyter-core": ">=5.8.1",
                    "keras": ">=3.11.0"
                }
            },
            "phase4_medium_low": {
                "description": "Medium-Low Risk Utility Libraries",
                "packages": {
                    "pillow": ">=10.3.0",
                    "protobuf": ">=4.25.8",
                    "pyarrow": ">=17.0.0",
                    "scrapy": ">=2.11.2",
                    "starlette": ">=0.47.2",
                    "tornado": ">=6.5",
                    "twisted": ">=24.7.0rc1",
                    "setuptools": ">=78.1.1"
                }
            }
        }
    
    def run_command(self, command: str, capture_output: bool = True) -> Tuple[int, str, str]:
        """Execute a shell command with proper error handling"""
        try:
            logger.info(f"Executing: {command}")
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would execute: {command}")
                return 0, "[DRY RUN] Command would execute", ""
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return -1, "", "Command timed out"
        except Exception as e:
            logger.error(f"Command failed: {command} - Error: {e}")
            return -1, "", str(e)
    
    def create_backup(self) -> bool:
        """Create backup of current environment"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_file = f"{self.backup_dir}/requirements-backup-{timestamp}.txt"
            
            # Create backup directory if it doesn't exist
            os.makedirs(self.backup_dir, exist_ok=True)
            
            logger.info(f"Creating backup: {self.backup_file}")
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create backup: {self.backup_file}")
                return True
            
            # Create requirements backup
            returncode, stdout, stderr = self.run_command("pip freeze")
            if returncode == 0:
                with open(self.backup_file, 'w') as f:
                    f.write(stdout)
                logger.info(f"Backup created successfully: {self.backup_file}")
                return True
            else:
                logger.error(f"Failed to create backup: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def check_current_vulnerabilities(self) -> Dict:
        """Check current vulnerability status"""
        logger.info("Checking current vulnerability status...")
        
        returncode, stdout, stderr = self.run_command("pip-audit --format=json")
        
        if returncode == 0:
            try:
                vulnerabilities = json.loads(stdout)
                logger.info(f"Current vulnerabilities: {len(vulnerabilities.get('dependencies', []))}")
                return vulnerabilities
            except json.JSONDecodeError:
                logger.error("Failed to parse vulnerability data")
                return {}
        else:
            logger.warning(f"pip-audit failed: {stderr}")
            return {}
    
    def get_package_info(self, package_name: str) -> Dict:
        """Get current package information"""
        returncode, stdout, stderr = self.run_command(f"pip show {package_name}")
        
        if returncode == 0:
            info = {}
            for line in stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            return info
        return {}
    
    def update_package(self, package_name: str, target_version: str) -> bool:
        """Update a single package to target version"""
        try:
            logger.info(f"Updating {package_name} to {target_version}")
            
            # Get current version
            current_info = self.get_package_info(package_name)
            current_version = current_info.get('Version', 'unknown')
            
            # Store rollback information
            self.rollback_data[package_name] = current_version
            
            # Update package
            update_command = f"pip install --upgrade '{package_name}{target_version}'"
            returncode, stdout, stderr = self.run_command(update_command)
            
            if returncode == 0:
                # Verify update
                new_info = self.get_package_info(package_name)
                new_version = new_info.get('Version', 'unknown')
                
                if new_version != current_version:
                    logger.info(f"Successfully updated {package_name}: {current_version} -> {new_version}")
                    self.update_results[package_name] = {
                        'status': 'success',
                        'old_version': current_version,
                        'new_version': new_version
                    }
                    return True
                else:
                    logger.warning(f"Package {package_name} version unchanged: {current_version}")
                    self.update_results[package_name] = {
                        'status': 'no_change',
                        'version': current_version
                    }
                    return True
            else:
                logger.error(f"Failed to update {package_name}: {stderr}")
                self.update_results[package_name] = {
                    'status': 'failed',
                    'error': stderr
                }
                return False
                
        except Exception as e:
            logger.error(f"Error updating {package_name}: {e}")
            self.update_results[package_name] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    def run_phase_tests(self, phase_name: str) -> bool:
        """Run tests for a specific update phase"""
        logger.info(f"Running tests for {phase_name}")
        
        test_commands = [
            "python -m pytest tests/ -v --tb=short",
            "python -m pytest tests/test_security.py -v",
            "python -m pytest tests/test_financial_calculations.py -v",
            "python -m pytest tests/test_payment_processing.py -v"
        ]
        
        all_tests_passed = True
        
        for test_cmd in test_commands:
            logger.info(f"Running test: {test_cmd}")
            returncode, stdout, stderr = self.run_command(test_cmd)
            
            if returncode == 0:
                logger.info(f"Test passed: {test_cmd}")
            else:
                logger.error(f"Test failed: {test_cmd}")
                logger.error(f"Test output: {stdout}")
                logger.error(f"Test errors: {stderr}")
                all_tests_passed = False
        
        return all_tests_passed
    
    def execute_phase(self, phase_name: str) -> bool:
        """Execute a complete update phase"""
        if phase_name not in self.update_phases:
            logger.error(f"Unknown phase: {phase_name}")
            return False
        
        phase = self.update_phases[phase_name]
        logger.info(f"Executing {phase_name}: {phase['description']}")
        
        success_count = 0
        total_count = len(phase['packages'])
        
        for package_name, target_version in phase['packages'].items():
            if self.update_package(package_name, target_version):
                success_count += 1
            else:
                logger.error(f"Failed to update {package_name}, stopping phase")
                return False
        
        logger.info(f"Phase {phase_name} completed: {success_count}/{total_count} packages updated")
        
        # Run tests after phase completion
        if not self.run_phase_tests(phase_name):
            logger.error(f"Tests failed for phase {phase_name}")
            return False
        
        return True
    
    def rollback_package(self, package_name: str) -> bool:
        """Rollback a package to its previous version"""
        if package_name not in self.rollback_data:
            logger.warning(f"No rollback data for {package_name}")
            return False
        
        previous_version = self.rollback_data[package_name]
        logger.info(f"Rolling back {package_name} to {previous_version}")
        
        rollback_command = f"pip install '{package_name}=={previous_version}'"
        returncode, stdout, stderr = self.run_command(rollback_command)
        
        if returncode == 0:
            logger.info(f"Successfully rolled back {package_name}")
            return True
        else:
            logger.error(f"Failed to rollback {package_name}: {stderr}")
            return False
    
    def rollback_phase(self, phase_name: str) -> bool:
        """Rollback all packages in a phase"""
        logger.info(f"Rolling back phase: {phase_name}")
        
        if phase_name not in self.update_phases:
            logger.error(f"Unknown phase: {phase_name}")
            return False
        
        phase = self.update_phases[phase_name]
        success_count = 0
        total_count = len(phase['packages'])
        
        for package_name in phase['packages'].keys():
            if self.rollback_package(package_name):
                success_count += 1
        
        logger.info(f"Phase rollback completed: {success_count}/{total_count} packages rolled back")
        return success_count == total_count
    
    def generate_report(self) -> str:
        """Generate update execution report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# Mingus Security Update Report
Generated: {timestamp}

## Summary
- Total packages processed: {len(self.update_results)}
- Successful updates: {len([r for r in self.update_results.values() if r['status'] == 'success'])}
- Failed updates: {len([r for r in self.update_results.values() if r['status'] == 'failed'])}
- Errors: {len([r for r in self.update_results.values() if r['status'] == 'error'])}

## Update Results
"""
        
        for package, result in self.update_results.items():
            report += f"\n### {package}\n"
            report += f"- Status: {result['status']}\n"
            
            if result['status'] == 'success':
                report += f"- Old Version: {result['old_version']}\n"
                report += f"- New Version: {result['new_version']}\n"
            elif result['status'] == 'no_change':
                report += f"- Version: {result['version']}\n"
            else:
                report += f"- Error: {result['error']}\n"
        
        if self.backup_file:
            report += f"\n## Backup Information\n- Backup file: {self.backup_file}\n"
        
        return report
    
    def run_full_update(self) -> bool:
        """Run the complete security update process"""
        logger.info("Starting comprehensive security update process")
        
        # Create backup
        if not self.create_backup():
            logger.error("Failed to create backup, aborting update")
            return False
        
        # Check initial vulnerabilities
        initial_vulns = self.check_current_vulnerabilities()
        
        # Execute each phase
        phases = list(self.update_phases.keys())
        successful_phases = []
        
        for phase_name in phases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting phase: {phase_name}")
            logger.info(f"{'='*60}")
            
            if self.execute_phase(phase_name):
                successful_phases.append(phase_name)
                logger.info(f"Phase {phase_name} completed successfully")
            else:
                logger.error(f"Phase {phase_name} failed, initiating rollback")
                
                # Rollback this phase
                if self.rollback_phase(phase_name):
                    logger.info(f"Phase {phase_name} rolled back successfully")
                else:
                    logger.error(f"Failed to rollback phase {phase_name}")
                
                # Rollback previous successful phases
                for completed_phase in reversed(successful_phases):
                    logger.info(f"Rolling back completed phase: {completed_phase}")
                    self.rollback_phase(completed_phase)
                
                return False
        
        # Check final vulnerability status
        final_vulns = self.check_current_vulnerabilities()
        
        # Generate final report
        report = self.generate_report()
        report_filename = f"security_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Security update completed successfully!")
        logger.info(f"Report saved to: {report_filename}")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Mingus Security Update Automation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--phase", choices=["phase1_critical", "phase2_web_security", "phase3_high_risk", "phase4_medium_low"], 
                       help="Run specific phase only")
    parser.add_argument("--backup-dir", default="backups", help="Directory for backups")
    
    args = parser.parse_args()
    
    # Create updater instance
    updater = SecurityUpdater(dry_run=args.dry_run, backup_dir=args.backup_dir)
    
    try:
        if args.phase:
            # Run specific phase
            if args.phase in updater.update_phases:
                logger.info(f"Running specific phase: {args.phase}")
                success = updater.execute_phase(args.phase)
                if success:
                    logger.info(f"Phase {args.phase} completed successfully")
                else:
                    logger.error(f"Phase {args.phase} failed")
                    sys.exit(1)
            else:
                logger.error(f"Unknown phase: {args.phase}")
                sys.exit(1)
        else:
            # Run full update
            success = updater.run_full_update()
            if not success:
                logger.error("Security update failed")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
