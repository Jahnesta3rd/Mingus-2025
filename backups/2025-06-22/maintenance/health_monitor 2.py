#!/usr/bin/env python3
"""
Health Monitoring and Maintenance System
Monitors application health and performs automated maintenance tasks
"""

import os
import sys
import logging
import schedule
import time
import requests
import psutil
import psycopg2
import redis
from datetime import datetime, timedelta
from pathlib import Path
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/health_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.app_url = os.getenv('APP_URL', 'http://localhost:5002')
        
        # Alert settings
        self.alert_email = os.getenv('ALERT_EMAIL', '')
        self.smtp_server = os.getenv('SMTP_SERVER', '')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        # Thresholds
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 85.0
        self.response_time_threshold = 5.0
        
        # Health status
        self.health_status = {
            'app_healthy': True,
            'db_healthy': True,
            'redis_healthy': True,
            'system_healthy': True,
            'last_check': None
        }
        
    def check_application_health(self):
        """Check application health endpoints"""
        try:
            # Check main health endpoint
            response = requests.get(f"{self.app_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.health_status['app_healthy'] = health_data.get('status') == 'healthy'
                logger.info("Application health check passed")
            else:
                self.health_status['app_healthy'] = False
                logger.error(f"Application health check failed: {response.status_code}")
                
        except Exception as e:
            self.health_status['app_healthy'] = False
            logger.error(f"Application health check error: {str(e)}")
    
    def check_database_health(self):
        """Check database connectivity and performance"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check basic connectivity
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] == 1:
                # Check database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """)
                size_info = cursor.fetchone()
                
                # Check active connections
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                active_connections = cursor.fetchone()[0]
                
                # Check for long-running queries
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND query_start < NOW() - INTERVAL '5 minutes'
                """)
                long_running_queries = cursor.fetchone()[0]
                
                self.health_status['db_healthy'] = True
                logger.info(f"Database health check passed - Size: {size_info[0]}, Active connections: {active_connections}")
                
                # Alert if too many long-running queries
                if long_running_queries > 5:
                    self.send_alert("Database Warning", f"Found {long_running_queries} long-running queries")
                    
            else:
                self.health_status['db_healthy'] = False
                logger.error("Database health check failed")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.health_status['db_healthy'] = False
            logger.error(f"Database health check error: {str(e)}")
    
    def check_redis_health(self):
        """Check Redis connectivity and performance"""
        try:
            r = redis.from_url(self.redis_url)
            
            # Test basic connectivity
            r.ping()
            
            # Check memory usage
            info = r.info()
            used_memory = info['used_memory']
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_usage_percent = (used_memory / max_memory) * 100
                if memory_usage_percent > 80:
                    self.send_alert("Redis Warning", f"Redis memory usage is {memory_usage_percent:.1f}%")
            
            # Check connected clients
            connected_clients = info['connected_clients']
            
            self.health_status['redis_healthy'] = True
            logger.info(f"Redis health check passed - Connected clients: {connected_clients}")
            
        except Exception as e:
            self.health_status['redis_healthy'] = False
            logger.error(f"Redis health check error: {str(e)}")
    
    def check_system_health(self):
        """Check system resources"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.cpu_threshold:
                self.send_alert("System Warning", f"CPU usage is {cpu_percent:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent > self.memory_threshold:
                self.send_alert("System Warning", f"Memory usage is {memory_percent:.1f}%")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.disk_threshold:
                self.send_alert("System Warning", f"Disk usage is {disk_percent:.1f}%")
            
            # Network I/O
            network = psutil.net_io_counters()
            
            self.health_status['system_healthy'] = True
            logger.info(f"System health check passed - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%")
            
        except Exception as e:
            self.health_status['system_healthy'] = False
            logger.error(f"System health check error: {str(e)}")
    
    def check_response_times(self):
        """Check application response times"""
        try:
            endpoints = [
                '/health',
                '/api/auth/check-auth',
                '/api/health/checkin',
                '/api/onboarding/progress'
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{self.app_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response_time > self.response_time_threshold:
                    self.send_alert("Performance Warning", f"Slow response time for {endpoint}: {response_time:.2f}s")
                
                logger.info(f"Response time for {endpoint}: {response_time:.2f}s")
                
        except Exception as e:
            logger.error(f"Response time check error: {str(e)}")
    
    def cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            log_dir = Path('/app/logs')
            if log_dir.exists():
                # Remove logs older than 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for log_file in log_dir.glob('*.log'):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {str(e)}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dirs = ['/tmp', '/app/temp']
            
            for temp_dir in temp_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    # Remove files older than 7 days
                    cutoff_date = datetime.now() - timedelta(days=7)
                    
                    for file_path in temp_path.rglob('*'):
                        if file_path.is_file() and file_path.stat().st_mtime < cutoff_date.timestamp():
                            file_path.unlink()
                            logger.info(f"Deleted temp file: {file_path}")
                            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
    
    def optimize_database(self):
        """Perform database optimization tasks"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Analyze tables for better query planning
            cursor.execute("ANALYZE")
            
            # Vacuum tables to reclaim storage
            cursor.execute("VACUUM ANALYZE")
            
            # Update table statistics
            cursor.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            """)
            
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute(f"ANALYZE {table[0]}.{table[1]}")
            
            cursor.close()
            conn.close()
            
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Error optimizing database: {str(e)}")
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            
            if free_gb < 5:  # Less than 5GB free
                self.send_alert("Critical Alert", f"Low disk space: {free_gb:.1f}GB free")
                
            logger.info(f"Disk space check: {free_gb:.1f}GB free")
            
        except Exception as e:
            logger.error(f"Error checking disk space: {str(e)}")
    
    def send_alert(self, subject, message):
        """Send alert email"""
        if not self.alert_email or not self.smtp_server:
            logger.warning(f"Alert: {subject} - {message}")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = f"Mingus Health Monitor: {subject}"
            
            body = f"""
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Message: {message}
            
            Current Health Status:
            - Application: {'Healthy' if self.health_status['app_healthy'] else 'Unhealthy'}
            - Database: {'Healthy' if self.health_status['db_healthy'] else 'Unhealthy'}
            - Redis: {'Healthy' if self.health_status['redis_healthy'] else 'Unhealthy'}
            - System: {'Healthy' if self.health_status['system_healthy'] else 'Unhealthy'}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
    
    def generate_health_report(self):
        """Generate comprehensive health report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'health_status': self.health_status,
                'system_metrics': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
                },
                'recommendations': []
            }
            
            # Generate recommendations
            if report['system_metrics']['cpu_percent'] > 70:
                report['recommendations'].append("Consider scaling up CPU resources")
            
            if report['system_metrics']['memory_percent'] > 80:
                report['recommendations'].append("Consider increasing memory allocation")
            
            if report['system_metrics']['disk_percent'] > 80:
                report['recommendations'].append("Consider cleaning up disk space or expanding storage")
            
            if not self.health_status['app_healthy']:
                report['recommendations'].append("Investigate application health issues")
            
            if not self.health_status['db_healthy']:
                report['recommendations'].append("Check database connectivity and performance")
            
            # Save report
            report_file = Path('/app/logs/health_report.json')
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Health report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
    
    def run_health_monitor(self):
        """Run comprehensive health checks"""
        try:
            logger.info("Starting health monitoring cycle")
            
            # Update last check time
            self.health_status['last_check'] = datetime.now().isoformat()
            
            # Run all health checks
            self.check_application_health()
            self.check_database_health()
            self.check_redis_health()
            self.check_system_health()
            self.check_response_times()
            self.check_disk_space()
            
            # Send alert if any component is unhealthy
            if not all(self.health_status.values()):
                unhealthy_components = [k for k, v in self.health_status.items() if not v and k != 'last_check']
                self.send_alert("Health Check Failed", f"Unhealthy components: {', '.join(unhealthy_components)}")
            
            logger.info("Health monitoring cycle completed")
            
        except Exception as e:
            logger.error(f"Error in health monitoring cycle: {str(e)}")
    
    def run_maintenance_schedule(self):
        """Run the maintenance schedule"""
        # Health checks every 5 minutes
        schedule.every(5).minutes.do(self.run_health_monitor)
        
        # Daily maintenance tasks at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_old_logs)
        schedule.every().day.at("02:30").do(self.cleanup_temp_files)
        schedule.every().day.at("03:00").do(self.optimize_database)
        
        # Weekly health report on Sunday at 6 AM
        schedule.every().sunday.at("06:00").do(self.generate_health_report)
        
        logger.info("Health monitoring and maintenance schedule started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main function"""
    health_monitor = HealthMonitor()
    
    # Run initial health check
    health_monitor.run_health_monitor()
    
    # Start monitoring schedule
    health_monitor.run_maintenance_schedule()

if __name__ == "__main__":
    main() 