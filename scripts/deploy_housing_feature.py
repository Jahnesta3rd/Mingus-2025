#!/usr/bin/env python3
"""
MINGUS Optimal Living Location - Production Deployment Script

Automated deployment script for housing location feature including:
- Environment validation
- Database migration
- Feature flag configuration
- Health checks
- Rollback preparation
"""

import os
import sys
import logging
import subprocess
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/housing_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HousingFeatureDeployer:
    """Deployer for housing location feature"""
    
    def __init__(self):
        self.deployment_config = self._load_deployment_config()
        self.deployment_status = {
            'started_at': datetime.utcnow().isoformat(),
            'steps_completed': [],
            'steps_failed': [],
            'overall_status': 'in_progress'
        }
    
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        return {
            'environment': os.environ.get('DEPLOYMENT_ENV', 'production'),
            'version': os.environ.get('DEPLOYMENT_VERSION', '1.0.0'),
            'region': os.environ.get('DEPLOYMENT_REGION', 'us-east-1'),
            'rollback_enabled': True,
            'health_check_timeout': 300,  # 5 minutes
            'deployment_timeout': 1800,   # 30 minutes
            'notification_webhook': os.environ.get('ROLLBACK_NOTIFICATION_WEBHOOK')
        }
    
    def deploy(self) -> bool:
        """Execute full deployment process"""
        try:
            logger.info("Starting housing feature deployment")
            
            # Step 1: Validate environment
            if not self._validate_environment():
                logger.error("Environment validation failed")
                return False
            
            # Step 2: Run database migration
            if not self._run_database_migration():
                logger.error("Database migration failed")
                return False
            
            # Step 3: Configure feature flags
            if not self._configure_feature_flags():
                logger.error("Feature flag configuration failed")
                return False
            
            # Step 4: Update API configurations
            if not self._update_api_configurations():
                logger.error("API configuration update failed")
                return False
            
            # Step 5: Deploy application
            if not self._deploy_application():
                logger.error("Application deployment failed")
                return False
            
            # Step 6: Run health checks
            if not self._run_health_checks():
                logger.error("Health checks failed")
                return False
            
            # Step 7: Enable feature gradually
            if not self._enable_feature_gradually():
                logger.error("Feature enablement failed")
                return False
            
            # Step 8: Final validation
            if not self._final_validation():
                logger.error("Final validation failed")
                return False
            
            self.deployment_status['overall_status'] = 'completed'
            self.deployment_status['completed_at'] = datetime.utcnow().isoformat()
            
            logger.info("Housing feature deployment completed successfully")
            self._send_deployment_notification('success')
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            self.deployment_status['overall_status'] = 'failed'
            self.deployment_status['failed_at'] = datetime.utcnow().isoformat()
            self.deployment_status['error'] = str(e)
            
            self._send_deployment_notification('failed')
            return False
    
    def _validate_environment(self) -> bool:
        """Validate deployment environment"""
        try:
            logger.info("Validating deployment environment")
            
            # Check required environment variables
            required_vars = [
                'DATABASE_URL',
                'REDIS_URL',
                'SECRET_KEY',
                'RENTALS_API_KEY',
                'ZILLOW_RAPIDAPI_KEY',
                'GOOGLE_MAPS_API_KEY'
            ]
            
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False
            
            # Check database connectivity
            if not self._check_database_connectivity():
                logger.error("Database connectivity check failed")
                return False
            
            # Check Redis connectivity
            if not self._check_redis_connectivity():
                logger.error("Redis connectivity check failed")
                return False
            
            # Check external API keys
            if not self._validate_api_keys():
                logger.error("API key validation failed")
                return False
            
            self.deployment_status['steps_completed'].append('environment_validation')
            logger.info("Environment validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation error: {e}")
            self.deployment_status['steps_failed'].append('environment_validation')
            return False
    
    def _check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            from backend.models.database import db
            with db.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database connectivity: OK")
            return True
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
            return False
    
    def _check_redis_connectivity(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.from_url(os.environ.get('REDIS_URL'))
            r.ping()
            logger.info("Redis connectivity: OK")
            return True
        except Exception as e:
            logger.error(f"Redis connectivity check failed: {e}")
            return False
    
    def _validate_api_keys(self) -> bool:
        """Validate external API keys"""
        try:
            # Test Rentals.com API
            rentals_key = os.environ.get('RENTALS_API_KEY')
            if not rentals_key or len(rentals_key) < 10:
                logger.error("Invalid Rentals.com API key")
                return False
            
            # Test Zillow API
            zillow_key = os.environ.get('ZILLOW_RAPIDAPI_KEY')
            if not zillow_key or len(zillow_key) < 10:
                logger.error("Invalid Zillow API key")
                return False
            
            # Test Google Maps API
            google_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            if not google_key or len(google_key) < 10:
                logger.error("Invalid Google Maps API key")
                return False
            
            logger.info("API key validation: OK")
            return True
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False
    
    def _run_database_migration(self) -> bool:
        """Run database migration"""
        try:
            logger.info("Running database migration")
            
            # Run Alembic migration
            result = subprocess.run([
                'alembic', 'upgrade', 'head'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Migration failed: {result.stderr}")
                return False
            
            # Run custom housing migration
            migration_script = project_root / 'migrations' / '001_housing_production_migration.py'
            if migration_script.exists():
                result = subprocess.run([
                    'python', str(migration_script)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Custom migration failed: {result.stderr}")
                    return False
            
            self.deployment_status['steps_completed'].append('database_migration')
            logger.info("Database migration completed")
            return True
            
        except Exception as e:
            logger.error(f"Database migration error: {e}")
            self.deployment_status['steps_failed'].append('database_migration')
            return False
    
    def _configure_feature_flags(self) -> bool:
        """Configure feature flags"""
        try:
            logger.info("Configuring feature flags")
            
            # Import feature flag manager
            from deployment.feature_flags.housing_feature_flags import housing_feature_flags
            
            # Enable housing feature flags
            housing_feature_flags.update_feature_flag('optimal_location_enabled', {
                'status': 'enabled',
                'rollout_percentage': 100
            })
            
            housing_feature_flags.update_feature_flag('housing_search_enabled', {
                'status': 'enabled',
                'rollout_percentage': 100
            })
            
            housing_feature_flags.update_feature_flag('scenario_creation_enabled', {
                'status': 'enabled',
                'rollout_percentage': 100
            })
            
            self.deployment_status['steps_completed'].append('feature_flag_configuration')
            logger.info("Feature flag configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"Feature flag configuration error: {e}")
            self.deployment_status['steps_failed'].append('feature_flag_configuration')
            return False
    
    def _update_api_configurations(self) -> bool:
        """Update API configurations"""
        try:
            logger.info("Updating API configurations")
            
            # Import API configuration
            from config.production_housing_config import production_config
            
            # Validate API configurations
            for api_name in ['rentals', 'zillow', 'google_maps']:
                config = production_config.get_api_config(api_name)
                if not config.get('api_key'):
                    logger.error(f"Missing API key for {api_name}")
                    return False
            
            self.deployment_status['steps_completed'].append('api_configuration')
            logger.info("API configuration update completed")
            return True
            
        except Exception as e:
            logger.error(f"API configuration error: {e}")
            self.deployment_status['steps_failed'].append('api_configuration')
            return False
    
    def _deploy_application(self) -> bool:
        """Deploy application"""
        try:
            logger.info("Deploying application")
            
            # Build Docker image
            result = subprocess.run([
                'docker', 'build', '-t', 'mingus-housing:latest', '.'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Docker build failed: {result.stderr}")
                return False
            
            # Deploy with Docker Compose
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.yml', 'up', '-d'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Docker Compose deployment failed: {result.stderr}")
                return False
            
            # Wait for application to start
            time.sleep(30)
            
            self.deployment_status['steps_completed'].append('application_deployment')
            logger.info("Application deployment completed")
            return True
            
        except Exception as e:
            logger.error(f"Application deployment error: {e}")
            self.deployment_status['steps_failed'].append('application_deployment')
            return False
    
    def _run_health_checks(self) -> bool:
        """Run health checks"""
        try:
            logger.info("Running health checks")
            
            # Import health checker
            from deployment.rollback.housing_rollback_procedures import housing_health_checker
            
            # Run comprehensive health checks
            health_results = housing_health_checker.run_health_checks()
            
            if health_results['overall_status'] != 'healthy':
                logger.error(f"Health checks failed: {health_results}")
                return False
            
            # Check specific housing endpoints
            if not self._check_housing_endpoints():
                logger.error("Housing endpoint checks failed")
                return False
            
            self.deployment_status['steps_completed'].append('health_checks')
            logger.info("Health checks completed")
            return True
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.deployment_status['steps_failed'].append('health_checks')
            return False
    
    def _check_housing_endpoints(self) -> bool:
        """Check housing-specific endpoints"""
        try:
            base_url = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
            
            # Check housing search endpoint
            response = requests.post(
                f"{base_url}/api/housing/search",
                json={
                    "max_rent": 2000,
                    "bedrooms": 2,
                    "commute_time": 30,
                    "zip_code": "30309"
                },
                timeout=10
            )
            
            if response.status_code not in [200, 401, 403]:  # 401/403 are expected for unauthenticated
                logger.error(f"Housing search endpoint check failed: {response.status_code}")
                return False
            
            # Check housing scenarios endpoint
            response = requests.get(
                f"{base_url}/api/housing/scenarios",
                timeout=10
            )
            
            if response.status_code not in [200, 401, 403]:
                logger.error(f"Housing scenarios endpoint check failed: {response.status_code}")
                return False
            
            logger.info("Housing endpoint checks: OK")
            return True
            
        except Exception as e:
            logger.error(f"Housing endpoint check error: {e}")
            return False
    
    def _enable_feature_gradually(self) -> bool:
        """Enable feature gradually"""
        try:
            logger.info("Enabling feature gradually")
            
            # Import feature flag manager
            from deployment.feature_flags.housing_feature_flags import housing_feature_flags
            
            # Start with 10% rollout
            housing_feature_flags.update_feature_flag('optimal_location_enabled', {
                'rollout_percentage': 10
            })
            
            # Wait and monitor
            time.sleep(60)
            
            # Increase to 25%
            housing_feature_flags.update_feature_flag('optimal_location_enabled', {
                'rollout_percentage': 25
            })
            
            # Wait and monitor
            time.sleep(60)
            
            # Increase to 50%
            housing_feature_flags.update_feature_flag('optimal_location_enabled', {
                'rollout_percentage': 50
            })
            
            # Wait and monitor
            time.sleep(60)
            
            # Full rollout
            housing_feature_flags.update_feature_flag('optimal_location_enabled', {
                'rollout_percentage': 100
            })
            
            self.deployment_status['steps_completed'].append('gradual_enablement')
            logger.info("Gradual feature enablement completed")
            return True
            
        except Exception as e:
            logger.error(f"Gradual enablement error: {e}")
            self.deployment_status['steps_failed'].append('gradual_enablement')
            return False
    
    def _final_validation(self) -> bool:
        """Final validation"""
        try:
            logger.info("Running final validation")
            
            # Check application health
            if not self._check_housing_endpoints():
                return False
            
            # Check feature flags
            from deployment.feature_flags.housing_feature_flags import housing_feature_flags
            flags = housing_feature_flags.get_all_feature_flags()
            
            if not flags['flags']['optimal_location_enabled']['status'] == 'enabled':
                logger.error("Housing feature not enabled")
                return False
            
            # Check database tables
            if not self._check_database_tables():
                return False
            
            self.deployment_status['steps_completed'].append('final_validation')
            logger.info("Final validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Final validation error: {e}")
            self.deployment_status['steps_failed'].append('final_validation')
            return False
    
    def _check_database_tables(self) -> bool:
        """Check database tables"""
        try:
            from backend.models.database import db
            
            with db.engine.connect() as conn:
                # Check housing tables exist
                tables = ['housing_searches', 'housing_scenarios', 'user_housing_preferences', 'commute_route_cache']
                
                for table in tables:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    logger.info(f"Table {table}: {count} records")
            
            return True
            
        except Exception as e:
            logger.error(f"Database table check error: {e}")
            return False
    
    def _send_deployment_notification(self, status: str):
        """Send deployment notification"""
        try:
            webhook_url = self.deployment_config.get('notification_webhook')
            if not webhook_url:
                return
            
            notification = {
                'text': f"🏠 MINGUS Housing Feature Deployment {status.title()}",
                'attachments': [{
                    'color': 'good' if status == 'success' else 'danger',
                    'fields': [
                        {'title': 'Status', 'value': status.title(), 'short': True},
                        {'title': 'Version', 'value': self.deployment_config['version'], 'short': True},
                        {'title': 'Environment', 'value': self.deployment_config['environment'], 'short': True},
                        {'title': 'Steps Completed', 'value': str(len(self.deployment_status['steps_completed'])), 'short': True},
                        {'title': 'Steps Failed', 'value': str(len(self.deployment_status['steps_failed'])), 'short': True}
                    ]
                }]
            }
            
            if status == 'failed':
                notification['attachments'][0]['fields'].append({
                    'title': 'Error',
                    'value': self.deployment_status.get('error', 'Unknown error'),
                    'short': False
                })
            
            requests.post(webhook_url, json=notification, timeout=10)
            
        except Exception as e:
            logger.error(f"Error sending deployment notification: {e}")
    
    def rollback(self) -> bool:
        """Rollback deployment"""
        try:
            logger.info("Initiating rollback")
            
            from deployment.rollback.housing_rollback_procedures import housing_rollback_manager
            
            # Initiate full rollback
            rollback_id = housing_rollback_manager.initiate_rollback(
                severity='high',
                reason='Deployment rollback',
                rollback_type='full',
                initiated_by='deployment_script'
            )
            
            # Execute rollback
            success = housing_rollback_manager.execute_rollback(rollback_id)
            
            if success:
                logger.info("Rollback completed successfully")
            else:
                logger.error("Rollback failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy MINGUS Housing Feature')
    parser.add_argument('--rollback', action='store_true', help='Rollback deployment')
    parser.add_argument('--validate-only', action='store_true', help='Only validate environment')
    
    args = parser.parse_args()
    
    deployer = HousingFeatureDeployer()
    
    if args.rollback:
        success = deployer.rollback()
    elif args.validate_only:
        success = deployer._validate_environment()
    else:
        success = deployer.deploy()
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
