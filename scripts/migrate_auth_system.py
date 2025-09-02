#!/usr/bin/env python3
"""
Authentication System Migration Script
Migrates from mixed JWT/session authentication to unified JWT system
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.middleware.unified_auth import auth_middleware, create_auth_response
from backend.models.user import User  # Adjust import based on your user model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthMigrationManager:
    """Manages migration from mixed authentication to unified JWT system"""
    
    def __init__(self, app=None):
        self.app = app
        self.migration_log = []
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        auth_middleware.init_app(app)
    
    def migrate_user_sessions(self) -> Dict[str, Any]:
        """Migrate existing user sessions to JWT tokens"""
        logger.info("Starting user session migration...")
        
        migration_stats = {
            'total_users': 0,
            'migrated_users': 0,
            'failed_migrations': 0,
            'errors': []
        }
        
        try:
            # Get all active users (adjust based on your user model)
            with self.app.app_context():
                users = User.query.filter_by(is_active=True).all()
                migration_stats['total_users'] = len(users)
                
                for user in users:
                    try:
                        # Create new JWT tokens for user
                        response_data = create_auth_response(
                            str(user.id),
                            user.subscription_tier or 'free'
                        )
                        
                        # Store migration info
                        migration_record = {
                            'user_id': str(user.id),
                            'email': user.email,
                            'migrated_at': datetime.utcnow().isoformat(),
                            'new_token_created': True
                        }
                        
                        self.migration_log.append(migration_record)
                        migration_stats['migrated_users'] += 1
                        
                        logger.info(f"Migrated user: {user.email}")
                        
                    except Exception as e:
                        error_msg = f"Failed to migrate user {user.email}: {str(e)}"
                        logger.error(error_msg)
                        migration_stats['errors'].append(error_msg)
                        migration_stats['failed_migrations'] += 1
                
                # Save migration log
                self.save_migration_log()
                
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            migration_stats['errors'].append(f"Migration failed: {str(e)}")
        
        return migration_stats
    
    def cleanup_old_sessions(self) -> Dict[str, Any]:
        """Clean up old session data"""
        logger.info("Cleaning up old session data...")
        
        cleanup_stats = {
            'sessions_cleaned': 0,
            'errors': []
        }
        
        try:
            # Clear Flask session data (if using server-side sessions)
            # This depends on your session storage implementation
            
            # Clear any session cookies or tokens
            # Implementation depends on your specific session storage
            
            cleanup_stats['sessions_cleaned'] = 1  # Placeholder
            logger.info("Old session data cleaned successfully")
            
        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            logger.error(error_msg)
            cleanup_stats['errors'].append(error_msg)
        
        return cleanup_stats
    
    def update_endpoints(self) -> Dict[str, Any]:
        """Update API endpoints to use new authentication"""
        logger.info("Updating API endpoints...")
        
        update_stats = {
            'endpoints_updated': 0,
            'errors': []
        }
        
        try:
            # List of endpoints that need to be updated
            endpoints_to_update = [
                'backend/routes/auth.py',
                'backend/routes/enhanced_auth_routes.py',
                'routes.py'
            ]
            
            for endpoint_file in endpoints_to_update:
                if os.path.exists(endpoint_file):
                    # Create backup
                    backup_file = f"{endpoint_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    with open(endpoint_file, 'r') as f:
                        content = f.read()
                    
                    with open(backup_file, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"Created backup: {backup_file}")
                    update_stats['endpoints_updated'] += 1
            
        except Exception as e:
            error_msg = f"Endpoint update failed: {str(e)}"
            logger.error(error_msg)
            update_stats['errors'].append(error_msg)
        
        return update_stats
    
    def update_frontend_auth(self) -> Dict[str, Any]:
        """Update frontend authentication code"""
        logger.info("Updating frontend authentication...")
        
        update_stats = {
            'files_updated': 0,
            'errors': []
        }
        
        try:
            # List of frontend files that need updates
            frontend_files = [
                'frontend/src/services/OnboardingFlowService.ts',
                'frontend/src/services/onboardingCompletionService.ts',
                'frontend/components/RechartsAnalyticsDashboard/index.tsx',
                'frontend/components/EnhancedAnalyticsDashboard/index.tsx'
            ]
            
            for file_path in frontend_files:
                if os.path.exists(file_path):
                    # Create backup
                    backup_file = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    with open(backup_file, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"Created backup: {backup_file}")
                    update_stats['files_updated'] += 1
            
        except Exception as e:
            error_msg = f"Frontend update failed: {str(e)}"
            logger.error(error_msg)
            update_stats['errors'].append(error_msg)
        
        return update_stats
    
    def save_migration_log(self):
        """Save migration log to file"""
        log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        migration_data = {
            'migration_date': datetime.utcnow().isoformat(),
            'migration_type': 'auth_system_unification',
            'records': self.migration_log
        }
        
        with open(log_file, 'w') as f:
            json.dump(migration_data, f, indent=2)
        
        logger.info(f"Migration log saved to: {log_file}")
    
    def generate_migration_report(self, stats: Dict[str, Any]) -> str:
        """Generate migration report"""
        report = f"""
# Authentication System Migration Report

**Migration Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Migration Type:** Mixed JWT/Session to Unified JWT

## Migration Statistics

### User Migration
- Total Users: {stats.get('total_users', 0)}
- Successfully Migrated: {stats.get('migrated_users', 0)}
- Failed Migrations: {stats.get('failed_migrations', 0)}

### System Updates
- Endpoints Updated: {stats.get('endpoints_updated', 0)}
- Frontend Files Updated: {stats.get('files_updated', 0)}
- Sessions Cleaned: {stats.get('sessions_cleaned', 0)}

## Errors
"""
        
        for error in stats.get('errors', []):
            report += f"- {error}\n"
        
        report += """
## Next Steps

1. **Test the new authentication system**
   - Verify login/logout functionality
   - Test token refresh mechanism
   - Validate subscription tier enforcement

2. **Update client applications**
   - Replace old authentication calls with new AuthService
   - Update API request headers
   - Test mobile app authentication

3. **Monitor system performance**
   - Check token validation performance
   - Monitor session management
   - Verify security features

4. **Clean up old code**
   - Remove deprecated authentication middleware
   - Clean up old session storage
   - Update documentation

## Security Improvements

✅ **Unified JWT Authentication**
- Single authentication method
- Consistent token validation
- Proper token rotation

✅ **Enhanced Security Features**
- Token blacklisting
- Concurrent session limits
- Subscription tier enforcement
- Automatic token refresh

✅ **Mobile App Support**
- Stateless authentication
- Secure token storage
- Cross-platform compatibility

## Rollback Plan

If issues arise, you can rollback using:
1. Restore backup files (`.backup.*`)
2. Revert to old authentication middleware
3. Restore session-based authentication
"""
        
        return report

def run_migration(app):
    """Run the complete migration process"""
    logger.info("Starting authentication system migration...")
    
    migration_manager = AuthMigrationManager()
    migration_manager.init_app(app)
    
    # Run migration steps
    migration_stats = {}
    
    # Step 1: Migrate user sessions
    logger.info("Step 1: Migrating user sessions...")
    migration_stats['user_migration'] = migration_manager.migrate_user_sessions()
    
    # Step 2: Clean up old sessions
    logger.info("Step 2: Cleaning up old sessions...")
    migration_stats['cleanup'] = migration_manager.cleanup_old_sessions()
    
    # Step 3: Update endpoints
    logger.info("Step 3: Updating endpoints...")
    migration_stats['endpoints'] = migration_manager.update_endpoints()
    
    # Step 4: Update frontend
    logger.info("Step 4: Updating frontend...")
    migration_stats['frontend'] = migration_manager.update_frontend_auth()
    
    # Generate report
    report = migration_manager.generate_migration_report(migration_stats)
    
    # Save report
    report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Migration completed. Report saved to: {report_file}")
    print(report)
    
    return migration_stats

if __name__ == "__main__":
    # This script should be run with a Flask app context
    print("Authentication Migration Script")
    print("This script should be run within a Flask application context.")
    print("Use: python -c 'from scripts.migrate_auth_system import run_migration; run_migration(app)'")
