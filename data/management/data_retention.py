#!/usr/bin/env python3
"""
Data Retention and Archival Management System
Handles data lifecycle, retention policies, and archival procedures
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
import boto3
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import gzip
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/data_retention.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataRetentionManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.s3_bucket = os.getenv('ARCHIVE_S3_BUCKET', 'mingus-archives')
        self.archive_dir = Path('/app/archives')
        self.archive_dir.mkdir(exist_ok=True)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Retention policies (in days)
        self.retention_policies = {
            'user_sessions': 30,
            'health_checkins': 90,
            'job_security_predictions': 365,
            'analytics_events': 180,
            'audit_logs': 2555,  # 7 years for compliance
            'error_logs': 30,
            'performance_metrics': 90,
            'backup_logs': 30
        }
        
        # Database engine
        self.engine = create_engine(self.db_url)
        
    def archive_old_data(self):
        """Archive data that exceeds retention policies"""
        try:
            logger.info("Starting data archival process")
            
            # Archive user sessions
            self.archive_user_sessions()
            
            # Archive health checkins
            self.archive_health_checkins()
            
            # Archive job security predictions
            self.archive_job_security_predictions()
            
            # Archive analytics events
            self.archive_analytics_events()
            
            # Archive audit logs
            self.archive_audit_logs()
            
            # Archive error logs
            self.archive_error_logs()
            
            # Archive performance metrics
            self.archive_performance_metrics()
            
            logger.info("Data archival process completed")
            
        except Exception as e:
            logger.error(f"Error in data archival process: {str(e)}")
    
    def archive_user_sessions(self):
        """Archive old user sessions"""
        try:
            retention_days = self.retention_policies['user_sessions']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Query old sessions
            query = text("""
                SELECT * FROM user_sessions 
                WHERE created_at < :cutoff_date
                ORDER BY created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                sessions = result.fetchall()
                
                if sessions:
                    # Create archive file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_file = self.archive_dir / f"user_sessions_{timestamp}.csv.gz"
                    
                    # Convert to DataFrame and save
                    df = pd.DataFrame(sessions)
                    df.to_csv(archive_file, compression='gzip', index=False)
                    
                    # Upload to S3
                    self.upload_archive_to_s3(archive_file, 'user_sessions')
                    
                    # Delete from database
                    delete_query = text("""
                        DELETE FROM user_sessions 
                        WHERE created_at < :cutoff_date
                    """)
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})
                    conn.commit()
                    
                    logger.info(f"Archived {len(sessions)} user sessions")
                    
        except Exception as e:
            logger.error(f"Error archiving user sessions: {str(e)}")
    
    def archive_health_checkins(self):
        """Archive old health checkins"""
        try:
            retention_days = self.retention_policies['health_checkins']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            query = text("""
                SELECT * FROM health_checkins 
                WHERE created_at < :cutoff_date
                ORDER BY created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                checkins = result.fetchall()
                
                if checkins:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_file = self.archive_dir / f"health_checkins_{timestamp}.csv.gz"
                    
                    df = pd.DataFrame(checkins)
                    df.to_csv(archive_file, compression='gzip', index=False)
                    
                    self.upload_archive_to_s3(archive_file, 'health_checkins')
                    
                    delete_query = text("""
                        DELETE FROM health_checkins 
                        WHERE created_at < :cutoff_date
                    """)
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})
                    conn.commit()
                    
                    logger.info(f"Archived {len(checkins)} health checkins")
                    
        except Exception as e:
            logger.error(f"Error archiving health checkins: {str(e)}")
    
    def archive_job_security_predictions(self):
        """Archive old job security predictions"""
        try:
            retention_days = self.retention_policies['job_security_predictions']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            query = text("""
                SELECT * FROM job_security_predictions 
                WHERE created_at < :cutoff_date
                ORDER BY created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                predictions = result.fetchall()
                
                if predictions:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_file = self.archive_dir / f"job_security_predictions_{timestamp}.csv.gz"
                    
                    df = pd.DataFrame(predictions)
                    df.to_csv(archive_file, compression='gzip', index=False)
                    
                    self.upload_archive_to_s3(archive_file, 'job_security_predictions')
                    
                    delete_query = text("""
                        DELETE FROM job_security_predictions 
                        WHERE created_at < :cutoff_date
                    """)
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})
                    conn.commit()
                    
                    logger.info(f"Archived {len(predictions)} job security predictions")
                    
        except Exception as e:
            logger.error(f"Error archiving job security predictions: {str(e)}")
    
    def archive_analytics_events(self):
        """Archive old analytics events"""
        try:
            retention_days = self.retention_policies['analytics_events']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            query = text("""
                SELECT * FROM analytics_events 
                WHERE created_at < :cutoff_date
                ORDER BY created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                events = result.fetchall()
                
                if events:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_file = self.archive_dir / f"analytics_events_{timestamp}.csv.gz"
                    
                    df = pd.DataFrame(events)
                    df.to_csv(archive_file, compression='gzip', index=False)
                    
                    self.upload_archive_to_s3(archive_file, 'analytics_events')
                    
                    delete_query = text("""
                        DELETE FROM analytics_events 
                        WHERE created_at < :cutoff_date
                    """)
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})
                    conn.commit()
                    
                    logger.info(f"Archived {len(events)} analytics events")
                    
        except Exception as e:
            logger.error(f"Error archiving analytics events: {str(e)}")
    
    def archive_audit_logs(self):
        """Archive old audit logs"""
        try:
            retention_days = self.retention_policies['audit_logs']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            query = text("""
                SELECT * FROM audit_logs 
                WHERE created_at < :cutoff_date
                ORDER BY created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                logs = result.fetchall()
                
                if logs:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_file = self.archive_dir / f"audit_logs_{timestamp}.csv.gz"
                    
                    df = pd.DataFrame(logs)
                    df.to_csv(archive_file, compression='gzip', index=False)
                    
                    self.upload_archive_to_s3(archive_file, 'audit_logs')
                    
                    delete_query = text("""
                        DELETE FROM audit_logs 
                        WHERE created_at < :cutoff_date
                    """)
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})
                    conn.commit()
                    
                    logger.info(f"Archived {len(logs)} audit logs")
                    
        except Exception as e:
            logger.error(f"Error archiving audit logs: {str(e)}")
    
    def archive_error_logs(self):
        """Archive old error logs"""
        try:
            retention_days = self.retention_policies['error_logs']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Archive log files
            log_dir = Path('/app/logs')
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        archive_file = self.archive_dir / f"{log_file.stem}_{timestamp}.log.gz"
                        
                        # Compress and archive
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(archive_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        self.upload_archive_to_s3(archive_file, 'error_logs')
                        
                        # Delete original file
                        log_file.unlink()
                        
                        logger.info(f"Archived log file: {log_file}")
                        
        except Exception as e:
            logger.error(f"Error archiving error logs: {str(e)}")
    
    def archive_performance_metrics(self):
        """Archive old performance metrics"""
        try:
            retention_days = self.retention_policies['performance_metrics']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            query = text("""
                SELECT * FROM performance_metrics 
                WHERE created_at < :cutoff_date
                ORDER BY created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                metrics = result.fetchall()
                
                if metrics:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_file = self.archive_dir / f"performance_metrics_{timestamp}.csv.gz"
                    
                    df = pd.DataFrame(metrics)
                    df.to_csv(archive_file, compression='gzip', index=False)
                    
                    self.upload_archive_to_s3(archive_file, 'performance_metrics')
                    
                    delete_query = text("""
                        DELETE FROM performance_metrics 
                        WHERE created_at < :cutoff_date
                    """)
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})
                    conn.commit()
                    
                    logger.info(f"Archived {len(metrics)} performance metrics")
                    
        except Exception as e:
            logger.error(f"Error archiving performance metrics: {str(e)}")
    
    def upload_archive_to_s3(self, file_path, data_type):
        """Upload archive file to S3"""
        try:
            key = f"{data_type}/{datetime.now().strftime('%Y/%m/%d')}/{file_path.name}"
            
            self.s3_client.upload_file(
                str(file_path),
                self.s3_bucket,
                key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'GLACIER'
                }
            )
            
            logger.info(f"Archive uploaded to S3: s3://{self.s3_bucket}/{key}")
            
            # Clean up local file
            file_path.unlink()
            
        except Exception as e:
            logger.error(f"Error uploading archive to S3: {str(e)}")
    
    def cleanup_old_archives(self):
        """Clean up old archive files from S3"""
        try:
            # Clean up archives older than 7 years
            cutoff_date = datetime.now() - timedelta(days=2555)
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            self.s3_client.delete_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            logger.info(f"Deleted old archive: {obj['Key']}")
                            
        except Exception as e:
            logger.error(f"Error cleaning up old archives: {str(e)}")
    
    def generate_retention_report(self):
        """Generate a report of data retention status"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'retention_policies': self.retention_policies,
                'data_counts': {},
                'archival_status': {}
            }
            
            # Get data counts for each table
            tables = [
                'user_sessions', 'health_checkins', 'job_security_predictions',
                'analytics_events', 'audit_logs', 'performance_metrics'
            ]
            
            for table in tables:
                try:
                    query = text(f"SELECT COUNT(*) as count FROM {table}")
                    with self.engine.connect() as conn:
                        result = conn.execute(query)
                        count = result.fetchone()[0]
                        report['data_counts'][table] = count
                except Exception as e:
                    report['data_counts'][table] = f"Error: {str(e)}"
            
            # Save report
            report_file = self.archive_dir / f"retention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Retention report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating retention report: {str(e)}")
    
    def run_retention_schedule(self):
        """Run the data retention schedule"""
        # Schedule daily archival at 3 AM
        schedule.every().day.at("03:00").do(self.archive_old_data)
        
        # Schedule weekly cleanup at 4 AM on Sunday
        schedule.every().sunday.at("04:00").do(self.cleanup_old_archives)
        
        # Schedule monthly report generation
        schedule.every().month.at("05:00").do(self.generate_retention_report)
        
        logger.info("Data retention schedule started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main function"""
    retention_manager = DataRetentionManager()
    
    # Generate initial report
    retention_manager.generate_retention_report()
    
    # Start retention schedule
    retention_manager.run_retention_schedule()

if __name__ == "__main__":
    main() 