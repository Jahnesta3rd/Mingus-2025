"""
Performance Monitoring System
Tracks API response times, database performance, score calculations, and user engagement
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from loguru import logger
import json
import sqlite3
from contextlib import contextmanager

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class APIMetric:
    """API performance metric"""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_size: Optional[int] = None
    response_size: Optional[int] = None

@dataclass
class DatabaseMetric:
    """Database performance metric"""
    query: str
    execution_time: float
    rows_returned: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None

@dataclass
class ScoreCalculationMetric:
    """Score calculation performance metric"""
    calculation_type: str
    execution_time: float
    input_data_size: int
    output_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None

class PerformanceMonitor:
    """Main performance monitoring class"""
    
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=1000)
        self.api_metrics = deque(maxlen=500)
        self.db_metrics = deque(maxlen=500)
        self.score_metrics = deque(maxlen=500)
        self.user_engagement = defaultdict(lambda: {
            'session_count': 0,
            'total_time': 0,
            'last_activity': None,
            'feature_usage': defaultdict(int)
        })
        
        self._lock = threading.Lock()
        self._init_database()
        self._start_background_processor()
    
    def _init_database(self):
        """Initialize performance metrics database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        endpoint TEXT NOT NULL,
                        method TEXT NOT NULL,
                        response_time REAL NOT NULL,
                        status_code INTEGER NOT NULL,
                        user_id TEXT,
                        timestamp DATETIME NOT NULL,
                        request_size INTEGER,
                        response_size INTEGER
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS database_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        rows_returned INTEGER,
                        timestamp DATETIME NOT NULL,
                        user_id TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS score_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        calculation_type TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        input_data_size INTEGER NOT NULL,
                        output_score REAL NOT NULL,
                        timestamp DATETIME NOT NULL,
                        user_id TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_engagement (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        feature_name TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 1,
                        total_time REAL DEFAULT 0,
                        timestamp DATETIME NOT NULL
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_timestamp ON api_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_endpoint ON api_metrics(endpoint)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_db_timestamp ON database_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_score_timestamp ON score_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_engagement_user ON user_engagement(user_id)")
                
        except Exception as e:
            logger.error(f"Failed to initialize performance database: {e}")
    
    def _start_background_processor(self):
        """Start background thread for processing metrics"""
        def processor():
            while True:
                try:
                    time.sleep(30)  # Process every 30 seconds
                    self._process_metrics_buffer()
                except Exception as e:
                    logger.error(f"Background processor error: {e}")
        
        thread = threading.Thread(target=processor, daemon=True)
        thread.start()
    
    def _process_metrics_buffer(self):
        """Process buffered metrics and save to database"""
        with self._lock:
            if not self.metrics_buffer:
                return
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Process API metrics
                    api_batch = list(self.api_metrics)
                    self.api_metrics.clear()
                    
                    if api_batch:
                        conn.executemany("""
                            INSERT INTO api_metrics 
                            (endpoint, method, response_time, status_code, user_id, timestamp, request_size, response_size)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, [
                            (m.endpoint, m.method, m.response_time, m.status_code, 
                             m.user_id, m.timestamp, m.request_size, m.response_size)
                            for m in api_batch
                        ])
                    
                    # Process database metrics
                    db_batch = list(self.db_metrics)
                    self.db_metrics.clear()
                    
                    if db_batch:
                        conn.executemany("""
                            INSERT INTO database_metrics 
                            (query, execution_time, rows_returned, timestamp, user_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, [
                            (m.query, m.execution_time, m.rows_returned, m.timestamp, m.user_id)
                            for m in db_batch
                        ])
                    
                    # Process score metrics
                    score_batch = list(self.score_metrics)
                    self.score_metrics.clear()
                    
                    if score_batch:
                        conn.executemany("""
                            INSERT INTO score_metrics 
                            (calculation_type, execution_time, input_data_size, output_score, timestamp, user_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, [
                            (m.calculation_type, m.execution_time, m.input_data_size, 
                             m.output_score, m.timestamp, m.user_id)
                            for m in score_batch
                        ])
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Failed to process metrics buffer: {e}")
    
    @contextmanager
    def api_timer(self, endpoint: str, method: str, user_id: Optional[str] = None):
        """Context manager for timing API calls"""
        start_time = time.time()
        request_size = None
        response_size = None
        
        try:
            yield
        finally:
            response_time = time.time() - start_time
            metric = APIMetric(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=200,  # Default, should be updated by caller
                user_id=user_id,
                request_size=request_size,
                response_size=response_size
            )
            
            with self._lock:
                self.api_metrics.append(metric)
    
    @contextmanager
    def db_timer(self, query: str, user_id: Optional[str] = None):
        """Context manager for timing database queries"""
        start_time = time.time()
        rows_returned = None
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            metric = DatabaseMetric(
                query=query,
                execution_time=execution_time,
                rows_returned=rows_returned,
                user_id=user_id
            )
            
            with self._lock:
                self.db_metrics.append(metric)
    
    @contextmanager
    def score_timer(self, calculation_type: str, input_data_size: int, user_id: Optional[str] = None):
        """Context manager for timing score calculations"""
        start_time = time.time()
        output_score = 0.0
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            metric = ScoreCalculationMetric(
                calculation_type=calculation_type,
                execution_time=execution_time,
                input_data_size=input_data_size,
                output_score=output_score,
                user_id=user_id
            )
            
            with self._lock:
                self.score_metrics.append(metric)
    
    def track_user_engagement(self, user_id: str, session_id: str, feature_name: str, 
                            usage_time: float = 0.0):
        """Track user engagement with features"""
        with self._lock:
            self.user_engagement[user_id]['session_count'] += 1
            self.user_engagement[user_id]['total_time'] += usage_time
            self.user_engagement[user_id]['last_activity'] = datetime.now()
            self.user_engagement[user_id]['feature_usage'][feature_name] += 1
            
            # Add to buffer for database storage
            self.metrics_buffer.append({
                'type': 'user_engagement',
                'user_id': user_id,
                'session_id': session_id,
                'feature_name': feature_name,
                'usage_time': usage_time,
                'timestamp': datetime.now()
            })
    
    def get_api_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get API performance summary for the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Get overall stats
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        AVG(response_time) as avg_response_time,
                        MAX(response_time) as max_response_time,
                        MIN(response_time) as min_response_time,
                        COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
                    FROM api_metrics 
                    WHERE timestamp >= ?
                """, (cutoff_time,))
                
                overall_stats = cursor.fetchone()
                
                # Get endpoint breakdown
                cursor = conn.execute("""
                    SELECT 
                        endpoint,
                        method,
                        COUNT(*) as request_count,
                        AVG(response_time) as avg_response_time,
                        MAX(response_time) as max_response_time
                    FROM api_metrics 
                    WHERE timestamp >= ?
                    GROUP BY endpoint, method
                    ORDER BY request_count DESC
                """, (cutoff_time,))
                
                endpoint_stats = cursor.fetchall()
                
                return {
                    'overall': {
                        'total_requests': overall_stats[0],
                        'avg_response_time': overall_stats[1],
                        'max_response_time': overall_stats[2],
                        'min_response_time': overall_stats[3],
                        'error_rate': overall_stats[4] / overall_stats[0] if overall_stats[0] > 0 else 0
                    },
                    'endpoints': [
                        {
                            'endpoint': row[0],
                            'method': row[1],
                            'request_count': row[2],
                            'avg_response_time': row[3],
                            'max_response_time': row[4]
                        }
                        for row in endpoint_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get API performance summary: {e}")
            return {}
    
    def get_database_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get database performance summary for the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(execution_time) as avg_execution_time,
                        MAX(execution_time) as max_execution_time,
                        SUM(rows_returned) as total_rows_returned
                    FROM database_metrics 
                    WHERE timestamp >= ?
                """, (cutoff_time,))
                
                stats = cursor.fetchone()
                
                # Get slowest queries
                cursor = conn.execute("""
                    SELECT query, execution_time, rows_returned, timestamp
                    FROM database_metrics 
                    WHERE timestamp >= ?
                    ORDER BY execution_time DESC
                    LIMIT 10
                """, (cutoff_time,))
                
                slowest_queries = cursor.fetchall()
                
                return {
                    'overall': {
                        'total_queries': stats[0],
                        'avg_execution_time': stats[1],
                        'max_execution_time': stats[2],
                        'total_rows_returned': stats[3]
                    },
                    'slowest_queries': [
                        {
                            'query': row[0][:100] + '...' if len(row[0]) > 100 else row[0],
                            'execution_time': row[1],
                            'rows_returned': row[2],
                            'timestamp': row[3]
                        }
                        for row in slowest_queries
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get database performance summary: {e}")
            return {}
    
    def get_score_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get score calculation performance summary for the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        calculation_type,
                        COUNT(*) as calculation_count,
                        AVG(execution_time) as avg_execution_time,
                        MAX(execution_time) as max_execution_time,
                        AVG(input_data_size) as avg_input_size,
                        AVG(output_score) as avg_output_score
                    FROM score_metrics 
                    WHERE timestamp >= ?
                    GROUP BY calculation_type
                """, (cutoff_time,))
                
                stats = cursor.fetchall()
                
                return {
                    'calculations': [
                        {
                            'type': row[0],
                            'count': row[1],
                            'avg_execution_time': row[2],
                            'max_execution_time': row[3],
                            'avg_input_size': row[4],
                            'avg_output_score': row[5]
                        }
                        for row in stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get score performance summary: {e}")
            return {}
    
    def get_user_engagement_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get user engagement summary for the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as active_users,
                        COUNT(DISTINCT session_id) as total_sessions,
                        SUM(usage_count) as total_feature_uses,
                        SUM(total_time) as total_engagement_time
                    FROM user_engagement 
                    WHERE timestamp >= ?
                """, (cutoff_time,))
                
                overall_stats = cursor.fetchone()
                
                # Get feature usage breakdown
                cursor = conn.execute("""
                    SELECT 
                        feature_name,
                        COUNT(DISTINCT user_id) as unique_users,
                        SUM(usage_count) as total_uses,
                        AVG(total_time) as avg_time_per_use
                    FROM user_engagement 
                    WHERE timestamp >= ?
                    GROUP BY feature_name
                    ORDER BY total_uses DESC
                """, (cutoff_time,))
                
                feature_stats = cursor.fetchall()
                
                return {
                    'overall': {
                        'active_users': overall_stats[0],
                        'total_sessions': overall_stats[1],
                        'total_feature_uses': overall_stats[2],
                        'total_engagement_time': overall_stats[3]
                    },
                    'features': [
                        {
                            'feature_name': row[0],
                            'unique_users': row[1],
                            'total_uses': row[2],
                            'avg_time_per_use': row[3]
                        }
                        for row in feature_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get user engagement summary: {e}")
            return {}
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get current system health metrics"""
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            process_cpu = current_process.cpu_percent()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_free': disk.free
                },
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process_cpu
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health metrics: {e}")
            return {}
    
    def export_metrics(self, start_date: datetime, end_date: datetime, 
                      metric_types: List[str] = None) -> Dict[str, List]:
        """Export metrics for analysis"""
        if metric_types is None:
            metric_types = ['api', 'database', 'score', 'engagement']
        
        export_data = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if 'api' in metric_types:
                    cursor = conn.execute("""
                        SELECT * FROM api_metrics 
                        WHERE timestamp BETWEEN ? AND ?
                        ORDER BY timestamp
                    """, (start_date, end_date))
                    export_data['api_metrics'] = cursor.fetchall()
                
                if 'database' in metric_types:
                    cursor = conn.execute("""
                        SELECT * FROM database_metrics 
                        WHERE timestamp BETWEEN ? AND ?
                        ORDER BY timestamp
                    """, (start_date, end_date))
                    export_data['database_metrics'] = cursor.fetchall()
                
                if 'score' in metric_types:
                    cursor = conn.execute("""
                        SELECT * FROM score_metrics 
                        WHERE timestamp BETWEEN ? AND ?
                        ORDER BY timestamp
                    """, (start_date, end_date))
                    export_data['score_metrics'] = cursor.fetchall()
                
                if 'engagement' in metric_types:
                    cursor = conn.execute("""
                        SELECT * FROM user_engagement 
                        WHERE timestamp BETWEEN ? AND ?
                        ORDER BY timestamp
                    """, (start_date, end_date))
                    export_data['user_engagement'] = cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
        
        return export_data

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorators for easy integration
def monitor_api_performance(endpoint: str, method: str = "GET"):
    """Decorator to monitor API performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or (args[0].user_id if hasattr(args[0], 'user_id') else None)
            
            with performance_monitor.api_timer(endpoint, method, user_id):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def monitor_database_performance(query: str):
    """Decorator to monitor database performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or (args[0].user_id if hasattr(args[0], 'user_id') else None)
            
            with performance_monitor.db_timer(query, user_id):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def monitor_score_calculation(calculation_type: str):
    """Decorator to monitor score calculation performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or (args[0].user_id if hasattr(args[0], 'user_id') else None)
            input_data_size = len(args) + len(kwargs)  # Simple approximation
            
            with performance_monitor.score_timer(calculation_type, input_data_size, user_id):
                result = func(*args, **kwargs)
                # Update the output score in the metric
                return result
        return wrapper
    return decorator 