#!/usr/bin/env python3
"""
Backup Scheduler Script
Comprehensive backup scheduling and coordination for the MINGUS financial application
"""

import os
import sys
import logging
import json
import time
import datetime
import subprocess
import signal
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import schedule
import threading
import croniter
import psutil

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backup.database_backup import PostgreSQLBackupManager, create_backup_config_from_env
from backup.redis_backup import RedisBackupManager, create_redis_backup_config_from_env
from backup.file_backup import FileBackupManager, create_file_backup_config_from_env
from backup.monitoring import BackupMonitoringManager, create_monitoring_config_from_env
from recovery.database_recovery import DatabaseRecoveryManager, create_recovery_config_from_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupScheduler:
    """Comprehensive backup scheduling and coordination system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.running = False
        self.backup_managers = {}
        self.monitoring_manager = None
        self.recovery_manager = None
        self.scheduler_thread = None
        self.backup_jobs = {}
        
        # Load configuration
        self._load_configuration()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
    def _load_configuration(self):
        """Load backup configuration from environment or config file"""
        try:
            # Initialize backup managers
            self.backup_managers['database'] = PostgreSQLBackupManager(
                create_backup_config_from_env()
            )
            
            self.backup_managers['redis'] = RedisBackupManager(
                create_redis_backup_config_from_env()
            )
            
            self.backup_managers['files'] = FileBackupManager(
                create_file_backup_config_from_env()
            )
            
            # Initialize monitoring manager
            self.monitoring_manager = BackupMonitoringManager(
                create_monitoring_config_from_env()
            )
            
            # Initialize recovery manager
            self.recovery_manager = DatabaseRecoveryManager(
                create_recovery_config_from_env()
            )
            
            logger.info("Backup configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load backup configuration: {e}")
            raise
            
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        
    def _create_backup_job(self, job_type: str, schedule_time: str, 
                          backup_type: str, manager_name: str):
        """Create a backup job with specified schedule"""
        try:
            # Parse schedule time (e.g., "02:00", "every 6 hours", "0 2 * * *")
            if schedule_time.startswith("0 "):  # Cron format
                cron = croniter.croniter(schedule_time, datetime.datetime.now())
                next_run = cron.get_next(datetime.datetime)
                job_id = f"{job_type}_{backup_type}_{manager_name}_{hash(schedule_time)}"
                
                # Schedule using cron format
                schedule.every().day.at(next_run.strftime("%H:%M")).do(
                    self._execute_backup_job, job_type, backup_type, manager_name
                )
                
            elif schedule_time.startswith("every"):
                # Parse "every X hours/minutes"
                parts = schedule_time.split()
                if len(parts) >= 3:
                    interval = int(parts[1])
                    unit = parts[2]
                    
                    if unit.startswith("hour"):
                        schedule.every(interval).hours.do(
                            self._execute_backup_job, job_type, backup_type, manager_name
                        )
                    elif unit.startswith("minute"):
                        schedule.every(interval).minutes.do(
                            self._execute_backup_job, job_type, backup_type, manager_name
                        )
                        
            else:
                # Assume time format (HH:MM)
                schedule.every().day.at(schedule_time).do(
                    self._execute_backup_job, job_type, backup_type, manager_name
                )
                
            job_id = f"{job_type}_{backup_type}_{manager_name}_{hash(schedule_time)}"
            self.backup_jobs[job_id] = {
                'type': job_type,
                'schedule': schedule_time,
                'backup_type': backup_type,
                'manager': manager_name,
                'last_run': None,
                'next_run': None,
                'status': 'scheduled'
            }
            
            logger.info(f"Backup job created: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to create backup job: {e}")
            
    def _execute_backup_job(self, job_type: str, backup_type: str, manager_name: str):
        """Execute a backup job"""
        job_id = f"{job_type}_{backup_type}_{manager_name}"
        start_time = time.time()
        
        try:
            logger.info(f"Executing backup job: {job_id}")
            
            # Update job status
            if job_id in self.backup_jobs:
                self.backup_jobs[job_id]['status'] = 'running'
                self.backup_jobs[job_id]['last_run'] = datetime.datetime.now()
                
            # Execute backup based on type and manager
            if manager_name == 'database':
                if backup_type == 'full':
                    metadata = self.backup_managers['database'].create_full_backup()
                elif backup_type == 'incremental':
                    metadata = self.backup_managers['database'].create_incremental_backup()
                    
            elif manager_name == 'redis':
                if backup_type == 'rdb':
                    metadata = self.backup_managers['redis'].create_rdb_backup()
                elif backup_type == 'aof':
                    metadata = self.backup_managers['redis'].create_aof_backup()
                elif backup_type == 'session':
                    metadata = self.backup_managers['redis'].create_session_backup()
                    
            elif manager_name == 'files':
                if backup_type == 'documents':
                    metadata = self.backup_managers['files'].create_documents_backup("./documents")
                elif backup_type == 'configs':
                    metadata = self.backup_managers['files'].create_configs_backup("./config")
                elif backup_type == 'code':
                    metadata = self.backup_managers['files'].create_code_backup("./backend")
                    
            # Record metrics
            if hasattr(metadata, 'status') and metadata.status == 'success':
                duration = time.time() - start_time
                size = getattr(metadata, 'size_bytes', 0)
                
                self.monitoring_manager.record_backup_success(
                    f"{backup_type}_{manager_name}", duration, size
                )
                
                logger.info(f"Backup job completed successfully: {job_id}")
                
            else:
                error_msg = getattr(metadata, 'error_message', 'Unknown error')
                self.monitoring_manager.record_backup_failure(
                    f"{backup_type}_{manager_name}", error_msg
                )
                
                logger.error(f"Backup job failed: {job_id} - {error_msg}")
                
        except Exception as e:
            duration = time.time() - start_time
            self.monitoring_manager.record_backup_failure(
                f"{backup_type}_{manager_name}", str(e)
            )
            
            logger.error(f"Backup job execution failed: {job_id} - {e}")
            
        finally:
            # Update job status
            if job_id in self.backup_jobs:
                self.backup_jobs[job_id]['status'] = 'completed'
                
    def _execute_recovery_test_job(self):
        """Execute automated recovery testing"""
        try:
            logger.info("Executing automated recovery test")
            
            # Get latest backup ID from database
            backup_metadata_dir = Path(self.backup_managers['database'].config.backup_dir) / "metadata"
            if backup_metadata_dir.exists():
                backup_files = list(backup_metadata_dir.glob("*.json"))
                if backup_files:
                    # Get most recent backup
                    latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                    
                    with open(latest_backup, 'r') as f:
                        backup_data = json.load(f)
                        backup_id = backup_data.get('backup_id')
                        
                    if backup_id:
                        # Execute recovery test
                        test_result = self.recovery_manager.test_recovery_procedure(backup_id)
                        
                        if test_result.test_status == 'success':
                            self.monitoring_manager.record_recovery_success(
                                'test', test_result.test_duration_seconds
                            )
                        else:
                            self.monitoring_manager.record_recovery_failure(
                                'test', test_result.error_message or 'Test failed'
                            )
                            
                        logger.info(f"Recovery test completed: {test_result.test_status}")
                        
        except Exception as e:
            logger.error(f"Recovery test job failed: {e}")
            
    def _execute_cleanup_job(self):
        """Execute cleanup of old backups"""
        try:
            logger.info("Executing backup cleanup")
            
            # Cleanup old backups for all managers
            for manager_name, manager in self.backup_managers.items():
                try:
                    manager.cleanup_old_backups()
                    logger.info(f"Cleanup completed for {manager_name}")
                except Exception as e:
                    logger.error(f"Cleanup failed for {manager_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Cleanup job failed: {e}")
            
    def _execute_health_check_job(self):
        """Execute system health check"""
        try:
            logger.info("Executing system health check")
            
            # Collect system health metrics
            health = self.monitoring_manager.collect_system_health()
            
            if health:
                logger.info(f"Health check completed - CPU: {health.cpu_usage}%, "
                          f"Memory: {health.memory_usage}%, Disk: {health.disk_usage}%")
                          
        except Exception as e:
            logger.error(f"Health check job failed: {e}")
            
    def _execute_compliance_report_job(self, report_period: str = "daily"):
        """Execute compliance report generation"""
        try:
            logger.info(f"Generating {report_period} compliance report")
            
            report = self.monitoring_manager.generate_compliance_report(report_period)
            
            if report:
                logger.info(f"Compliance report generated: {report.compliance_score}%")
                
        except Exception as e:
            logger.error(f"Compliance report job failed: {e}")
            
    def setup_backup_schedule(self):
        """Setup comprehensive backup schedule"""
        try:
            logger.info("Setting up backup schedule")
            
            # Database backups
            self._create_backup_job("daily", "02:00", "full", "database")
            self._create_backup_job("hourly", "every 1 hour", "incremental", "database")
            
            # Redis backups
            self._create_backup_job("frequent", "every 6 hours", "rdb", "redis")
            self._create_backup_job("hourly", "every 1 hour", "aof", "redis")
            self._create_backup_job("frequent", "every 30 minutes", "session", "redis")
            
            # File backups
            self._create_backup_job("daily", "01:00", "documents", "files")
            self._create_backup_job("daily", "01:30", "configs", "files")
            self._create_backup_job("daily", "02:00", "code", "files")
            self._create_backup_job("hourly", "every 1 hour", "incremental", "files")
            
            # Maintenance jobs
            schedule.every().day.at("03:00").do(self._execute_cleanup_job)
            schedule.every().day.at("04:00").do(self._execute_health_check_job)
            
            # Recovery testing
            schedule.every().sunday.at("02:00").do(self._execute_recovery_test_job)
            
            # Compliance reporting
            schedule.every().day.at("06:00").do(self._execute_compliance_report_job, "daily")
            schedule.every().sunday.at("07:00").do(self._execute_compliance_report_job, "weekly")
            schedule.every().month.at("01:00").do(self._execute_compliance_report_job, "monthly")
            
            logger.info("Backup schedule setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup backup schedule: {e}")
            raise
            
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
                
    def start(self):
        """Start the backup scheduler"""
        try:
            logger.info("Starting backup scheduler")
            
            # Start monitoring
            if self.monitoring_manager:
                self.monitoring_manager.start_monitoring()
                
            # Setup backup schedule
            self.setup_backup_schedule()
            
            # Start scheduler thread
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Backup scheduler started successfully")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start backup scheduler: {e}")
            raise
            
    def stop(self):
        """Stop the backup scheduler"""
        try:
            logger.info("Stopping backup scheduler")
            
            self.running = False
            
            # Stop monitoring
            if self.monitoring_manager:
                self.monitoring_manager.stop_monitoring()
                
            # Wait for scheduler thread to finish
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=10)
                
            logger.info("Backup scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping backup scheduler: {e}")
            
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            'running': self.running,
            'jobs': self.backup_jobs,
            'managers': list(self.backup_managers.keys()),
            'monitoring_enabled': self.monitoring_manager is not None,
            'recovery_enabled': self.recovery_manager is not None
        }
        
    def run_manual_backup(self, backup_type: str, manager_name: str) -> bool:
        """Run a manual backup"""
        try:
            logger.info(f"Running manual backup: {backup_type} on {manager_name}")
            
            if manager_name not in self.backup_managers:
                raise ValueError(f"Unknown manager: {manager_name}")
                
            # Execute backup
            self._execute_backup_job("manual", "now", backup_type, manager_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Manual backup failed: {e}")
            return False
            
    def run_manual_recovery_test(self) -> bool:
        """Run a manual recovery test"""
        try:
            logger.info("Running manual recovery test")
            
            self._execute_recovery_test_job()
            
            return True
            
        except Exception as e:
            logger.error(f"Manual recovery test failed: {e}")
            return False


def create_cron_jobs():
    """Create system cron jobs for backup operations"""
    try:
        cron_content = f"""# MINGUS Backup System Cron Jobs
# Generated on {datetime.datetime.now()}

# Database backups
0 2 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=database_full
0 */1 9-18 * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=database_incremental

# Redis backups
0 */6 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=redis_rdb
0 */1 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=redis_aof
*/30 * * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=redis_session

# File backups
0 1 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=files_documents
30 1 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=files_configs
0 2 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=files_code

# Maintenance
0 3 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=cleanup
0 4 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=health_check

# Recovery testing
0 2 * * 0 cd {os.getcwd()} && python scripts/backup_scheduler.py --job=recovery_test

# Compliance reporting
0 6 * * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=compliance_daily
0 7 * * 0 cd {os.getcwd()} && python scripts/backup_scheduler.py --job=compliance_weekly
0 1 1 * * cd {os.getcwd()} && python scripts/backup_scheduler.py --job=compliance_monthly
"""
        
        # Write cron file
        cron_file = Path("backup_cron.txt")
        with open(cron_file, 'w') as f:
            f.write(cron_content)
            
        logger.info(f"Cron jobs written to {cron_file}")
        logger.info("To install, run: crontab backup_cron.txt")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create cron jobs: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MINGUS Backup Scheduler")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--job", help="Execute specific job type")
    parser.add_argument("--manual-backup", help="Run manual backup (format: type:manager)")
    parser.add_argument("--recovery-test", action="store_true", help="Run recovery test")
    parser.add_argument("--status", action="store_true", help="Show scheduler status")
    parser.add_argument("--create-cron", action="store_true", help="Create cron job file")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    try:
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        if args.create_cron:
            create_cron_jobs()
            return
            
        # Initialize scheduler
        scheduler = BackupScheduler(args.config)
        
        if args.status:
            status = scheduler.get_status()
            print(json.dumps(status, indent=2, default=str))
            return
            
        if args.manual_backup:
            backup_type, manager_name = args.manual_backup.split(':')
            success = scheduler.run_manual_backup(backup_type, manager_name)
            sys.exit(0 if success else 1)
            
        if args.recovery_test:
            success = scheduler.run_manual_recovery_test()
            sys.exit(0 if success else 1)
            
        if args.job:
            # Execute specific job
            if args.job == "database_full":
                scheduler._execute_backup_job("scheduled", "now", "full", "database")
            elif args.job == "database_incremental":
                scheduler._execute_backup_job("scheduled", "now", "incremental", "database")
            elif args.job == "redis_rdb":
                scheduler._execute_backup_job("scheduled", "now", "rdb", "redis")
            elif args.job == "redis_aof":
                scheduler._execute_backup_job("scheduled", "now", "aof", "redis")
            elif args.job == "redis_session":
                scheduler._execute_backup_job("scheduled", "now", "session", "redis")
            elif args.job == "files_documents":
                scheduler._execute_backup_job("scheduled", "now", "documents", "files")
            elif args.job == "files_configs":
                scheduler._execute_backup_job("scheduled", "now", "configs", "files")
            elif args.job == "files_code":
                scheduler._execute_backup_job("scheduled", "now", "code", "files")
            elif args.job == "cleanup":
                scheduler._execute_cleanup_job()
            elif args.job == "health_check":
                scheduler._execute_health_check_job()
            elif args.job == "recovery_test":
                scheduler._execute_recovery_test_job()
            elif args.job == "compliance_daily":
                scheduler._execute_compliance_report_job("daily")
            elif args.job == "compliance_weekly":
                scheduler._execute_compliance_report_job("weekly")
            elif args.job == "compliance_monthly":
                scheduler._execute_compliance_report_job("monthly")
            return
            
        # Start scheduler
        if args.daemon:
            # Run as daemon
            import daemon
            with daemon.DaemonContext():
                scheduler.start()
        else:
            # Run in foreground
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        if 'scheduler' in locals():
            scheduler.stop()
    except Exception as e:
        logger.error(f"Backup scheduler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
