#!/usr/bin/env python3
"""
Mingus Application - Performance Monitoring System
================================================

Comprehensive performance monitoring and baseline measurement system
for the Mingus Personal Finance Application.

Author: Mingus Performance Team
Date: January 2025
"""

import time
import json
import sqlite3
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: str
    metric_type: str
    metric_name: str
    value: float
    unit: str
    threshold: float
    status: str  # PASS, WARN, FAIL
    metadata: Dict[str, Any]

@dataclass
class BaselineMeasurement:
    """Baseline measurement data structure"""
    metric_name: str
    current_baseline: float
    target: float
    unit: str
    measurement_count: int
    last_updated: str
    trend: str  # IMPROVING, STABLE, DEGRADING
    confidence: float

class PerformanceMonitor:
    """Main performance monitoring class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('database_path', 'performance_metrics.db')
        self.api_base_url = config.get('api_base_url', 'http://localhost:5000')
        self.frontend_url = config.get('frontend_url', 'http://localhost:3000')
        self.alert_thresholds = config.get('alert_thresholds', {})
        self.baselines = {}
        self.metrics_history = []
        
        # Initialize database
        self.init_database()
        
        # Load existing baselines
        self.load_baselines()
    
    def init_database(self):
        """Initialize performance metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                threshold REAL NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create baselines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT UNIQUE NOT NULL,
                current_baseline REAL NOT NULL,
                target REAL NOT NULL,
                unit TEXT NOT NULL,
                measurement_count INTEGER DEFAULT 0,
                last_updated TEXT NOT NULL,
                trend TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                threshold_value REAL NOT NULL,
                actual_value REAL NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Performance monitoring database initialized")
    
    def load_baselines(self):
        """Load existing baselines from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM baselines')
        rows = cursor.fetchall()
        
        for row in rows:
            self.baselines[row[1]] = BaselineMeasurement(
                metric_name=row[1],
                current_baseline=row[2],
                target=row[3],
                unit=row[4],
                measurement_count=row[5],
                last_updated=row[6],
                trend=row[7],
                confidence=row[8]
            )
        
        conn.close()
        logger.info(f"Loaded {len(self.baselines)} baselines")
    
    def measure_page_load_times(self) -> List[PerformanceMetric]:
        """Measure page load times for all routes"""
        metrics = []
        routes = [
            {'name': 'landing_page', 'url': f'{self.frontend_url}/', 'target': 2000},
            {'name': 'assessment_modal', 'url': f'{self.frontend_url}/#assessment', 'target': 1500},
            {'name': 'settings_page', 'url': f'{self.frontend_url}/settings', 'target': 2500},
            {'name': 'dashboard', 'url': f'{self.frontend_url}/dashboard', 'target': 3000}
        ]
        
        for route in routes:
            try:
                start_time = time.time()
                response = requests.get(route['url'], timeout=10)
                end_time = time.time()
                
                load_time = (end_time - start_time) * 1000  # Convert to milliseconds
                status = 'PASS' if load_time <= route['target'] else 'FAIL'
                
                metric = PerformanceMetric(
                    timestamp=datetime.now().isoformat(),
                    metric_type='page_load',
                    metric_name=route['name'],
                    value=load_time,
                    unit='ms',
                    threshold=route['target'],
                    status=status,
                    metadata={
                        'url': route['url'],
                        'status_code': response.status_code,
                        'response_size': len(response.content)
                    }
                )
                metrics.append(metric)
                
            except Exception as e:
                logger.error(f"Error measuring {route['name']}: {e}")
                metric = PerformanceMetric(
                    timestamp=datetime.now().isoformat(),
                    metric_type='page_load',
                    metric_name=route['name'],
                    value=float('inf'),
                    unit='ms',
                    threshold=route['target'],
                    status='FAIL',
                    metadata={'error': str(e)}
                )
                metrics.append(metric)
        
        return metrics
    
    def measure_api_response_times(self) -> List[PerformanceMetric]:
        """Measure API response times for all endpoints"""
        metrics = []
        endpoints = [
            {'name': 'health_check', 'url': f'{self.api_base_url}/health', 'target': 50},
            {'name': 'assessments', 'url': f'{self.api_base_url}/api/assessments', 'target': 200},
            {'name': 'user_meme', 'url': f'{self.api_base_url}/api/user-meme', 'target': 150},
            {'name': 'user_preferences', 'url': f'{self.api_base_url}/api/user-preferences', 'target': 100},
            {'name': 'assessments_analytics', 'url': f'{self.api_base_url}/api/assessments/analytics', 'target': 300},
            {'name': 'meme_analytics', 'url': f'{self.api_base_url}/api/meme-analytics', 'target': 250}
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint['url'], timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                status = 'PASS' if response_time <= endpoint['target'] else 'FAIL'
                
                metric = PerformanceMetric(
                    timestamp=datetime.now().isoformat(),
                    metric_type='api_response',
                    metric_name=endpoint['name'],
                    value=response_time,
                    unit='ms',
                    threshold=endpoint['target'],
                    status=status,
                    metadata={
                        'url': endpoint['url'],
                        'status_code': response.status_code,
                        'response_size': len(response.content)
                    }
                )
                metrics.append(metric)
                
            except Exception as e:
                logger.error(f"Error measuring {endpoint['name']}: {e}")
                metric = PerformanceMetric(
                    timestamp=datetime.now().isoformat(),
                    metric_type='api_response',
                    metric_name=endpoint['name'],
                    value=float('inf'),
                    unit='ms',
                    threshold=endpoint['target'],
                    status='FAIL',
                    metadata={'error': str(e)}
                )
                metrics.append(metric)
        
        return metrics
    
    def measure_system_metrics(self) -> List[PerformanceMetric]:
        """Measure system-level performance metrics"""
        metrics = []
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_type='system',
            metric_name='cpu_usage',
            value=cpu_percent,
            unit='%',
            threshold=80.0,
            status='PASS' if cpu_percent <= 80.0 else 'WARN',
            metadata={'cores': psutil.cpu_count()}
        )
        metrics.append(cpu_metric)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_type='system',
            metric_name='memory_usage',
            value=memory.percent,
            unit='%',
            threshold=85.0,
            status='PASS' if memory.percent <= 85.0 else 'WARN',
            metadata={
                'total': memory.total,
                'available': memory.available,
                'used': memory.used
            }
        )
        metrics.append(memory_metric)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_type='system',
            metric_name='disk_usage',
            value=(disk.used / disk.total) * 100,
            unit='%',
            threshold=90.0,
            status='PASS' if (disk.used / disk.total) * 100 <= 90.0 else 'WARN',
            metadata={
                'total': disk.total,
                'used': disk.used,
                'free': disk.free
            }
        )
        metrics.append(disk_metric)
        
        return metrics
    
    def measure_database_performance(self) -> List[PerformanceMetric]:
        """Measure database performance metrics"""
        metrics = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test basic query performance
            start_time = time.time()
            cursor.execute('SELECT COUNT(*) FROM performance_metrics')
            result = cursor.fetchone()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000
            query_metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_type='database',
                metric_name='basic_query_time',
                value=query_time,
                unit='ms',
                threshold=100.0,
                status='PASS' if query_time <= 100.0 else 'FAIL',
                metadata={'query': 'SELECT COUNT(*) FROM performance_metrics'}
            )
            metrics.append(query_metric)
            
            # Test complex query performance
            start_time = time.time()
            cursor.execute('''
                SELECT metric_name, AVG(value) as avg_value, COUNT(*) as count
                FROM performance_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY metric_name
            ''')
            results = cursor.fetchall()
            end_time = time.time()
            
            complex_query_time = (end_time - start_time) * 1000
            complex_metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_type='database',
                metric_name='complex_query_time',
                value=complex_query_time,
                unit='ms',
                threshold=500.0,
                status='PASS' if complex_query_time <= 500.0 else 'FAIL',
                metadata={'query': 'Complex aggregation query', 'result_count': len(results)}
            )
            metrics.append(complex_metric)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error measuring database performance: {e}")
            error_metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_type='database',
                metric_name='database_error',
                value=float('inf'),
                unit='ms',
                threshold=0.0,
                status='FAIL',
                metadata={'error': str(e)}
            )
            metrics.append(error_metric)
        
        return metrics
    
    def save_metrics(self, metrics: List[PerformanceMetric]):
        """Save performance metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO performance_metrics 
                (timestamp, metric_type, metric_name, value, unit, threshold, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.timestamp,
                metric.metric_type,
                metric.metric_name,
                metric.value,
                metric.unit,
                metric.threshold,
                metric.status,
                json.dumps(metric.metadata)
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(metrics)} performance metrics")
    
    def update_baselines(self, metrics: List[PerformanceMetric]):
        """Update baseline measurements based on new metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Group metrics by name
        metric_groups = {}
        for metric in metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)
        
        for metric_name, values in metric_groups.items():
            # Calculate new baseline (median of recent values)
            new_baseline = statistics.median(values)
            
            # Get existing baseline
            cursor.execute('SELECT * FROM baselines WHERE metric_name = ?', (metric_name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing baseline
                old_baseline = existing[2]
                trend = 'IMPROVING' if new_baseline < old_baseline else 'DEGRADING' if new_baseline > old_baseline else 'STABLE'
                confidence = min(1.0, existing[5] + 0.1)  # Increase confidence over time
                
                cursor.execute('''
                    UPDATE baselines 
                    SET current_baseline = ?, measurement_count = measurement_count + 1, 
                        last_updated = ?, trend = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE metric_name = ?
                ''', (new_baseline, datetime.now().isoformat(), trend, confidence, metric_name))
            else:
                # Create new baseline
                cursor.execute('''
                    INSERT INTO baselines 
                    (metric_name, current_baseline, target, unit, measurement_count, last_updated, trend, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (metric_name, new_baseline, 0.0, 'ms', 1, datetime.now().isoformat(), 'STABLE', 0.1))
        
        conn.commit()
        conn.close()
        
        # Reload baselines
        self.load_baselines()
        logger.info("Updated baselines based on new metrics")
    
    def check_alerts(self, metrics: List[PerformanceMetric]):
        """Check for alert conditions and create alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            # Check if metric exceeds threshold
            if metric.value > metric.threshold * 1.5:  # 150% of threshold
                severity = 'HIGH' if metric.value > metric.threshold * 2 else 'MEDIUM'
                
                cursor.execute('''
                    INSERT INTO alerts 
                    (metric_name, alert_type, threshold_value, actual_value, severity, message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metric.metric_name,
                    'THRESHOLD_EXCEEDED',
                    metric.threshold,
                    metric.value,
                    severity,
                    f'{metric.metric_name} exceeded threshold: {metric.value:.2f}{metric.unit} > {metric.threshold:.2f}{metric.unit}'
                ))
                
                logger.warning(f"ALERT: {metric.metric_name} exceeded threshold")
        
        conn.commit()
        conn.close()
    
    def run_comprehensive_measurement(self) -> Dict[str, Any]:
        """Run comprehensive performance measurement"""
        logger.info("Starting comprehensive performance measurement")
        
        all_metrics = []
        
        # Measure page load times
        logger.info("Measuring page load times...")
        page_metrics = self.measure_page_load_times()
        all_metrics.extend(page_metrics)
        
        # Measure API response times
        logger.info("Measuring API response times...")
        api_metrics = self.measure_api_response_times()
        all_metrics.extend(api_metrics)
        
        # Measure system metrics
        logger.info("Measuring system metrics...")
        system_metrics = self.measure_system_metrics()
        all_metrics.extend(system_metrics)
        
        # Measure database performance
        logger.info("Measuring database performance...")
        db_metrics = self.measure_database_performance()
        all_metrics.extend(db_metrics)
        
        # Save metrics
        self.save_metrics(all_metrics)
        
        # Update baselines
        self.update_baselines(all_metrics)
        
        # Check for alerts
        self.check_alerts(all_metrics)
        
        # Generate summary
        summary = self.generate_summary(all_metrics)
        
        logger.info("Comprehensive performance measurement completed")
        return summary
    
    def generate_summary(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Generate performance measurement summary"""
        total_metrics = len(metrics)
        passed_metrics = len([m for m in metrics if m.status == 'PASS'])
        failed_metrics = len([m for m in metrics if m.status == 'FAIL'])
        warning_metrics = len([m for m in metrics if m.status == 'WARN'])
        
        # Group by metric type
        by_type = {}
        for metric in metrics:
            if metric.metric_type not in by_type:
                by_type[metric.metric_type] = []
            by_type[metric.metric_type].append(metric)
        
        # Calculate averages by type
        type_averages = {}
        for metric_type, type_metrics in by_type.items():
            values = [m.value for m in type_metrics if m.value != float('inf')]
            if values:
                type_averages[metric_type] = {
                    'average': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_metrics': total_metrics,
            'passed': passed_metrics,
            'failed': failed_metrics,
            'warnings': warning_metrics,
            'success_rate': (passed_metrics / total_metrics * 100) if total_metrics > 0 else 0,
            'by_type': type_averages,
            'baselines': {name: asdict(baseline) for name, baseline in self.baselines.items()},
            'alerts': self.get_active_alerts()
        }
        
        return summary
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT metric_name, alert_type, threshold_value, actual_value, severity, message, created_at
            FROM alerts 
            WHERE resolved = FALSE 
            ORDER BY created_at DESC
        ''')
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'metric_name': row[0],
                'alert_type': row[1],
                'threshold_value': row[2],
                'actual_value': row[3],
                'severity': row[4],
                'message': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return alerts
    
    def export_baseline_report(self, output_path: str):
        """Export baseline report to file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'baselines': {name: asdict(baseline) for name, baseline in self.baselines.items()},
            'recent_metrics': self.get_recent_metrics(hours=24),
            'alerts': self.get_active_alerts(),
            'summary': self.generate_summary(self.get_recent_metrics(hours=1))
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Baseline report exported to {output_path}")
    
    def get_recent_metrics(self, hours: int = 24) -> List[PerformanceMetric]:
        """Get recent metrics from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, metric_type, metric_name, value, unit, threshold, status, metadata
            FROM performance_metrics 
            WHERE timestamp > datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        '''.format(hours))
        
        metrics = []
        for row in cursor.fetchall():
            metric = PerformanceMetric(
                timestamp=row[0],
                metric_type=row[1],
                metric_name=row[2],
                value=row[3],
                unit=row[4],
                threshold=row[5],
                status=row[6],
                metadata=json.loads(row[7]) if row[7] else {}
            )
            metrics.append(metric)
        
        conn.close()
        return metrics

def main():
    """Main function for running performance monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mingus Performance Monitor')
    parser.add_argument('--config', default='monitoring_config.json', help='Configuration file path')
    parser.add_argument('--export', help='Export baseline report to file')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=300, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            'database_path': 'performance_metrics.db',
            'api_base_url': 'http://localhost:5000',
            'frontend_url': 'http://localhost:3000',
            'alert_thresholds': {
                'page_load': 1.5,
                'api_response': 1.5,
                'system': 1.2,
                'database': 1.5
            }
        }
    
    # Initialize monitor
    monitor = PerformanceMonitor(config)
    
    if args.continuous:
        logger.info(f"Starting continuous monitoring (interval: {args.interval}s)")
        while True:
            try:
                summary = monitor.run_comprehensive_measurement()
                logger.info(f"Monitoring cycle completed - Success rate: {summary['success_rate']:.1f}%")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait before retrying
    else:
        # Run single measurement
        summary = monitor.run_comprehensive_measurement()
        print(json.dumps(summary, indent=2))
        
        if args.export:
            monitor.export_baseline_report(args.export)

if __name__ == "__main__":
    main()
