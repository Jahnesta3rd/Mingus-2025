"""
Enhanced Log Aggregation and Analysis System
Advanced log processing with pattern detection, anomaly detection, and security analysis
"""

import os
import json
import time
import threading
import queue
import re
import hashlib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
from loguru import logger
import sqlite3
from enum import Enum
import ipaddress
import statistics
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogSource(Enum):
    """Log sources"""
    APPLICATION = "application"
    SECURITY = "security"
    SYSTEM = "system"
    DATABASE = "database"
    NETWORK = "network"
    FIREWALL = "firewall"
    IDS = "ids"

class AnalysisType(Enum):
    """Analysis types"""
    PATTERN_DETECTION = "pattern_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_ANALYSIS = "compliance_analysis"

@dataclass
class LogEntry:
    """Log entry structure"""
    timestamp: datetime
    level: LogLevel
    source: LogSource
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None

@dataclass
class LogAggregationConfig:
    """Log aggregation configuration"""
    enabled: bool = True
    log_sources: List[LogSource] = field(default_factory=lambda: [
        LogSource.APPLICATION, LogSource.SECURITY, LogSource.SYSTEM
    ])
    aggregation_interval: int = 60  # seconds
    retention_days: int = 30
    analysis_enabled: bool = True
    anomaly_detection: bool = True
    pattern_detection: bool = True
    security_analysis: bool = True
    performance_analysis: bool = True
    compliance_analysis: bool = True
    
    # Pattern detection settings
    pattern_window_minutes: int = 60
    pattern_threshold: int = 10
    pattern_cooldown_minutes: int = 30
    
    # Anomaly detection settings
    anomaly_window_hours: int = 24
    anomaly_contamination: float = 0.1
    anomaly_threshold: float = 0.8
    
    # Security analysis settings
    security_keywords: List[str] = field(default_factory=lambda: [
        "attack", "breach", "hack", "exploit", "vulnerability", "malware",
        "phishing", "ddos", "brute force", "sql injection", "xss", "csrf"
    ])
    suspicious_ips: List[str] = field(default_factory=list)
    blacklisted_ips: List[str] = field(default_factory=list)
    
    # Performance analysis settings
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "response_time_ms": 5000,
        "error_rate_percent": 5.0,
        "throughput_requests_per_second": 100
    })

class EnhancedLogAggregator:
    """Enhanced log aggregation and analysis system"""
    
    def __init__(self, config: LogAggregationConfig):
        self.config = config
        self.log_queue = queue.Queue()
        self.analysis_queue = queue.Queue()
        self.log_workers = []
        self.analysis_workers = []
        self.log_cache = defaultdict(lambda: deque(maxlen=10000))
        self.pattern_cache = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_detector = None
        self.baseline_metrics = {}
        self.security_events = deque(maxlen=10000)
        self.performance_metrics = defaultdict(lambda: deque(maxlen=1000))
        
        self._init_database()
        self._init_anomaly_detector()
        self._load_security_patterns()
        self.start_workers()
    
    def _init_database(self):
        """Initialize log aggregation database"""
        try:
            db_path = "/var/lib/mingus/logs.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                # Main logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        level TEXT NOT NULL,
                        source TEXT NOT NULL,
                        message TEXT NOT NULL,
                        metadata TEXT,
                        user_id TEXT,
                        ip_address TEXT,
                        session_id TEXT,
                        request_id TEXT,
                        trace_id TEXT,
                        hash TEXT UNIQUE
                    )
                """)
                
                # Pattern detection table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS log_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_hash TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        first_seen TEXT NOT NULL,
                        last_seen TEXT NOT NULL,
                        occurrence_count INTEGER DEFAULT 1,
                        severity TEXT DEFAULT 'low'
                    )
                """)
                
                # Anomaly detection table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS log_anomalies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        anomaly_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT NOT NULL,
                        log_ids TEXT,
                        metadata TEXT
                    )
                """)
                
                # Security events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        source_ip TEXT,
                        user_id TEXT,
                        description TEXT NOT NULL,
                        metadata TEXT,
                        status TEXT DEFAULT 'open'
                    )
                """)
                
                # Performance metrics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        threshold REAL,
                        status TEXT DEFAULT 'normal'
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_ip ON logs(ip_address)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_hash ON log_patterns(pattern_hash)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON log_anomalies(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)")
        
        except Exception as e:
            logger.error(f"Error initializing log database: {e}")
    
    def _init_anomaly_detector(self):
        """Initialize anomaly detection model"""
        try:
            if self.config.anomaly_detection:
                self.anomaly_detector = IsolationForest(
                    contamination=self.config.anomaly_contamination,
                    random_state=42
                )
                self.scaler = StandardScaler()
        except Exception as e:
            logger.error(f"Error initializing anomaly detector: {e}")
    
    def _load_security_patterns(self):
        """Load security patterns and rules"""
        self.security_patterns = {
            "sql_injection": [
                r"(\b(union|select|insert|update|delete|drop|create|alter)\b.*\b(from|into|where|table|database)\b)",
                r"(\b(union|select|insert|update|delete|drop|create|alter)\b.*['\"])",
                r"(\b(union|select|insert|update|delete|drop|create|alter)\b.*\b(exec|execute|script)\b)"
            ],
            "xss_attack": [
                r"(<script[^>]*>.*?</script>)",
                r"(javascript:.*)",
                r"(on\w+\s*=)",
                r"(<iframe[^>]*>)",
                r"(<object[^>]*>)"
            ],
            "path_traversal": [
                r"(\.\./\.\./)",
                r"(\.\.\\\.\.\\)",
                r"(\.\.%2f\.\.%2f)",
                r"(\.\.%5c\.\.%5c)"
            ],
            "command_injection": [
                r"(\b(cmd|command|exec|execute|system|shell)\b)",
                r"(\b(ping|nslookup|traceroute|netstat|ps|top)\b)",
                r"(\b(rm|del|delete|format|fdisk)\b)"
            ],
            "authentication_attack": [
                r"(\b(brute|force|dictionary|rainbow)\b.*\b(attack|crack|hack)\b)",
                r"(failed.*login.*attempt)",
                r"(multiple.*failed.*password)",
                r"(account.*locked.*multiple.*attempts)"
            ],
            "ddos_attack": [
                r"(denial.*of.*service)",
                r"(distributed.*denial.*of.*service)",
                r"(flood.*attack)",
                r"(rate.*limit.*exceeded.*multiple.*times)"
            ]
        }
    
    def start_workers(self):
        """Start log processing and analysis workers"""
        # Start log processing workers
        for i in range(3):
            worker = threading.Thread(target=self._log_worker, daemon=True, name=f"log_worker_{i}")
            worker.start()
            self.log_workers.append(worker)
        
        # Start analysis workers
        for i in range(2):
            worker = threading.Thread(target=self._analysis_worker, daemon=True, name=f"analysis_worker_{i}")
            worker.start()
            self.analysis_workers.append(worker)
    
    def _log_worker(self):
        """Background worker for log processing"""
        while True:
            try:
                log_entry = self.log_queue.get(timeout=1)
                self._process_log_entry(log_entry)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in log worker: {e}")
    
    def _analysis_worker(self):
        """Background worker for log analysis"""
        while True:
            try:
                analysis_task = self.analysis_queue.get(timeout=1)
                self._perform_analysis(analysis_task)
                self.analysis_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}")
    
    def aggregate_logs(self, logs: List[Dict[str, Any]]):
        """Aggregate logs from various sources"""
        try:
            for log_data in logs:
                log_entry = self._parse_log_entry(log_data)
                if log_entry:
                    self.log_queue.put(log_entry)
            
            # Trigger analysis if enabled
            if self.config.analysis_enabled:
                self.analysis_queue.put({
                    "type": "batch_analysis",
                    "timestamp": datetime.utcnow().isoformat(),
                    "log_count": len(logs)
                })
        
        except Exception as e:
            logger.error(f"Error aggregating logs: {e}")
    
    def _parse_log_entry(self, log_data: Dict[str, Any]) -> Optional[LogEntry]:
        """Parse log entry from dictionary"""
        try:
            # Parse timestamp
            timestamp_str = log_data.get("timestamp")
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Parse level
            level_str = log_data.get("level", "info").lower()
            level = LogLevel(level_str) if level_str in [l.value for l in LogLevel] else LogLevel.INFO
            
            # Parse source
            source_str = log_data.get("source", "application").lower()
            source = LogSource(source_str) if source_str in [s.value for s in LogSource] else LogSource.APPLICATION
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                source=source,
                message=log_data.get("message", ""),
                metadata=log_data.get("metadata", {}),
                user_id=log_data.get("user_id"),
                ip_address=log_data.get("ip_address"),
                session_id=log_data.get("session_id"),
                request_id=log_data.get("request_id"),
                trace_id=log_data.get("trace_id")
            )
        
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            return None
    
    def _process_log_entry(self, log_entry: LogEntry):
        """Process individual log entry"""
        try:
            # Store in cache
            cache_key = f"{log_entry.source.value}_{log_entry.level.value}"
            self.log_cache[cache_key].append(log_entry)
            
            # Store in database
            self._store_log_entry(log_entry)
            
            # Check for security events
            if self._is_security_event(log_entry):
                self._process_security_event(log_entry)
            
            # Update performance metrics
            self._update_performance_metrics(log_entry)
            
            # Check for patterns
            if self.config.pattern_detection:
                self._check_patterns(log_entry)
            
        except Exception as e:
            logger.error(f"Error processing log entry: {e}")
    
    def _store_log_entry(self, log_entry: LogEntry):
        """Store log entry in database"""
        try:
            # Create hash for deduplication
            log_hash = hashlib.md5(
                f"{log_entry.timestamp}{log_entry.source}{log_entry.message}".encode()
            ).hexdigest()
            
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO logs 
                    (timestamp, level, source, message, metadata, user_id, ip_address, 
                     session_id, request_id, trace_id, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry.timestamp.isoformat(),
                    log_entry.level.value,
                    log_entry.source.value,
                    log_entry.message,
                    json.dumps(log_entry.metadata),
                    log_entry.user_id,
                    log_entry.ip_address,
                    log_entry.session_id,
                    log_entry.request_id,
                    log_entry.trace_id,
                    log_hash
                ))
        
        except Exception as e:
            logger.error(f"Error storing log entry: {e}")
    
    def _is_security_event(self, log_entry: LogEntry) -> bool:
        """Check if log entry is a security event"""
        # Check for security keywords
        message_lower = log_entry.message.lower()
        for keyword in self.config.security_keywords:
            if keyword.lower() in message_lower:
                return True
        
        # Check for security patterns
        for pattern_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return True
        
        # Check for suspicious IPs
        if log_entry.ip_address:
            if log_entry.ip_address in self.config.suspicious_ips:
                return True
            if log_entry.ip_address in self.config.blacklisted_ips:
                return True
        
        # Check for high severity levels
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return True
        
        return False
    
    def _process_security_event(self, log_entry: LogEntry):
        """Process security event"""
        try:
            # Determine event type
            event_type = self._classify_security_event(log_entry)
            severity = self._determine_security_severity(log_entry)
            
            security_event = {
                "timestamp": log_entry.timestamp.isoformat(),
                "event_type": event_type,
                "severity": severity,
                "source_ip": log_entry.ip_address,
                "user_id": log_entry.user_id,
                "description": log_entry.message,
                "metadata": log_entry.metadata,
                "status": "open"
            }
            
            # Store security event
            self._store_security_event(security_event)
            self.security_events.append(security_event)
            
            logger.warning(f"Security event detected: {event_type} - {severity}")
        
        except Exception as e:
            logger.error(f"Error processing security event: {e}")
    
    def _classify_security_event(self, log_entry: LogEntry) -> str:
        """Classify security event type"""
        message_lower = log_entry.message.lower()
        
        # Check for specific attack types
        for attack_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return attack_type
        
        # Check for authentication issues
        if any(keyword in message_lower for keyword in ["login", "authentication", "password"]):
            return "authentication_failure"
        
        # Check for authorization issues
        if any(keyword in message_lower for keyword in ["access denied", "unauthorized", "forbidden"]):
            return "authorization_failure"
        
        # Check for rate limiting
        if any(keyword in message_lower for keyword in ["rate limit", "too many requests"]):
            return "rate_limiting"
        
        return "suspicious_activity"
    
    def _determine_security_severity(self, log_entry: LogEntry) -> str:
        """Determine security event severity"""
        message_lower = log_entry.message.lower()
        
        # Critical indicators
        if any(keyword in message_lower for keyword in ["breach", "hack", "exploit", "malware"]):
            return "critical"
        
        # High indicators
        if any(keyword in message_lower for keyword in ["attack", "injection", "xss", "csrf"]):
            return "high"
        
        # Medium indicators
        if any(keyword in message_lower for keyword in ["failed", "unauthorized", "suspicious"]):
            return "medium"
        
        # Default to low
        return "low"
    
    def _store_security_event(self, security_event: Dict[str, Any]):
        """Store security event in database"""
        try:
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                conn.execute("""
                    INSERT INTO security_events 
                    (timestamp, event_type, severity, source_ip, user_id, description, metadata, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    security_event["timestamp"],
                    security_event["event_type"],
                    security_event["severity"],
                    security_event["source_ip"],
                    security_event["user_id"],
                    security_event["description"],
                    json.dumps(security_event["metadata"]),
                    security_event["status"]
                ))
        
        except Exception as e:
            logger.error(f"Error storing security event: {e}")
    
    def _update_performance_metrics(self, log_entry: LogEntry):
        """Update performance metrics"""
        try:
            # Extract performance data from metadata
            if "response_time" in log_entry.metadata:
                response_time = log_entry.metadata["response_time"]
                self.performance_metrics["response_time"].append(response_time)
                
                # Check against threshold
                if response_time > self.config.performance_thresholds.get("response_time_ms", 5000):
                    self._record_performance_alert("response_time", response_time)
            
            if "throughput" in log_entry.metadata:
                throughput = log_entry.metadata["throughput"]
                self.performance_metrics["throughput"].append(throughput)
                
                # Check against threshold
                if throughput < self.config.performance_thresholds.get("throughput_requests_per_second", 100):
                    self._record_performance_alert("throughput", throughput)
            
            # Calculate error rate
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self.performance_metrics["errors"].append(1)
            else:
                self.performance_metrics["errors"].append(0)
            
            # Calculate error rate percentage
            if len(self.performance_metrics["errors"]) >= 100:
                error_rate = (sum(list(self.performance_metrics["errors"])[-100:]) / 100) * 100
                if error_rate > self.config.performance_thresholds.get("error_rate_percent", 5.0):
                    self._record_performance_alert("error_rate", error_rate)
        
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _record_performance_alert(self, metric_name: str, value: float):
        """Record performance alert"""
        try:
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                conn.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, metric_name, metric_value, threshold, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    metric_name,
                    value,
                    self.config.performance_thresholds.get(f"{metric_name}_ms", 0),
                    "alert"
                ))
        
        except Exception as e:
            logger.error(f"Error recording performance alert: {e}")
    
    def _check_patterns(self, log_entry: LogEntry):
        """Check for patterns in logs"""
        try:
            # Create pattern signature
            pattern_data = {
                "source": log_entry.source.value,
                "level": log_entry.level.value,
                "message_pattern": self._extract_message_pattern(log_entry.message),
                "user_id": log_entry.user_id,
                "ip_address": log_entry.ip_address
            }
            
            pattern_hash = hashlib.md5(json.dumps(pattern_data, sort_keys=True).encode()).hexdigest()
            
            # Check if pattern exists
            if pattern_hash in self.pattern_cache:
                # Update existing pattern
                pattern = self.pattern_cache[pattern_hash]
                pattern["occurrence_count"] += 1
                pattern["last_seen"] = log_entry.timestamp.isoformat()
                
                # Check if pattern threshold exceeded
                if pattern["occurrence_count"] >= self.config.pattern_threshold:
                    self._trigger_pattern_alert(pattern)
            else:
                # Create new pattern
                new_pattern = {
                    "pattern_hash": pattern_hash,
                    "pattern_data": pattern_data,
                    "first_seen": log_entry.timestamp.isoformat(),
                    "last_seen": log_entry.timestamp.isoformat(),
                    "occurrence_count": 1,
                    "severity": "low"
                }
                self.pattern_cache[pattern_hash] = new_pattern
                self._store_pattern(new_pattern)
        
        except Exception as e:
            logger.error(f"Error checking patterns: {e}")
    
    def _extract_message_pattern(self, message: str) -> str:
        """Extract pattern from message"""
        # Remove dynamic parts like timestamps, IDs, etc.
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}', '<DATE>', message)
        pattern = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', pattern)
        pattern = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', pattern)
        pattern = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', pattern)
        pattern = re.sub(r'\b\d+\b', '<NUMBER>', pattern)
        return pattern
    
    def _store_pattern(self, pattern: Dict[str, Any]):
        """Store pattern in database"""
        try:
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO log_patterns 
                    (pattern_hash, pattern_type, pattern_data, first_seen, last_seen, occurrence_count, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern["pattern_hash"],
                    "recurring",
                    json.dumps(pattern["pattern_data"]),
                    pattern["first_seen"],
                    pattern["last_seen"],
                    pattern["occurrence_count"],
                    pattern["severity"]
                ))
        
        except Exception as e:
            logger.error(f"Error storing pattern: {e}")
    
    def _trigger_pattern_alert(self, pattern: Dict[str, Any]):
        """Trigger alert for pattern detection"""
        try:
            # Check cooldown
            last_seen = datetime.fromisoformat(pattern["last_seen"])
            if (datetime.utcnow() - last_seen).total_seconds() < self.config.pattern_cooldown_minutes * 60:
                return
            
            # Create anomaly record
            anomaly = {
                "timestamp": datetime.utcnow().isoformat(),
                "anomaly_type": "pattern_detection",
                "severity": pattern["severity"],
                "description": f"Recurring pattern detected: {pattern['occurrence_count']} occurrences",
                "log_ids": "[]",
                "metadata": json.dumps(pattern)
            }
            
            self._store_anomaly(anomaly)
            logger.warning(f"Pattern alert triggered: {pattern['occurrence_count']} occurrences")
        
        except Exception as e:
            logger.error(f"Error triggering pattern alert: {e}")
    
    def _perform_analysis(self, analysis_task: Dict[str, Any]):
        """Perform log analysis"""
        try:
            analysis_type = analysis_task.get("type")
            
            if analysis_type == "batch_analysis":
                self._perform_batch_analysis()
            elif analysis_type == "anomaly_detection":
                self._perform_anomaly_detection()
            elif analysis_type == "security_analysis":
                self._perform_security_analysis()
            elif analysis_type == "performance_analysis":
                self._perform_performance_analysis()
        
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
    
    def _perform_batch_analysis(self):
        """Perform batch analysis on recent logs"""
        try:
            # Collect recent logs for analysis
            recent_logs = []
            for cache in self.log_cache.values():
                recent_logs.extend(list(cache)[-100:])  # Last 100 logs from each cache
            
            if not recent_logs:
                return
            
            # Perform anomaly detection
            if self.config.anomaly_detection:
                self._detect_anomalies(recent_logs)
            
            # Perform security analysis
            if self.config.security_analysis:
                self._analyze_security_trends(recent_logs)
            
            # Perform performance analysis
            if self.config.performance_analysis:
                self._analyze_performance_trends(recent_logs)
        
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
    
    def _detect_anomalies(self, logs: List[LogEntry]):
        """Detect anomalies in logs"""
        try:
            if not self.anomaly_detector:
                return
            
            # Prepare features for anomaly detection
            features = []
            for log in logs:
                feature_vector = [
                    hash(log.source.value) % 1000,  # Source hash
                    hash(log.level.value) % 100,    # Level hash
                    len(log.message),               # Message length
                    hash(log.user_id or "") % 1000, # User hash
                    hash(log.ip_address or "") % 1000  # IP hash
                ]
                features.append(feature_vector)
            
            if len(features) < 10:  # Need minimum samples
                return
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Detect anomalies
            anomaly_scores = self.anomaly_detector.fit_predict(features_scaled)
            
            # Find anomalous logs
            for i, score in enumerate(anomaly_scores):
                if score == -1:  # Anomaly detected
                    log = logs[i]
                    anomaly = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "anomaly_type": "behavioral_anomaly",
                        "severity": "medium",
                        "description": f"Anomalous log behavior detected: {log.message[:100]}...",
                        "log_ids": "[]",
                        "metadata": json.dumps({
                            "log_message": log.message,
                            "source": log.source.value,
                            "level": log.level.value,
                            "user_id": log.user_id,
                            "ip_address": log.ip_address
                        })
                    }
                    self._store_anomaly(anomaly)
        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
    
    def _analyze_security_trends(self, logs: List[LogEntry]):
        """Analyze security trends"""
        try:
            # Count security events by type
            security_counts = Counter()
            for log in logs:
                if self._is_security_event(log):
                    event_type = self._classify_security_event(log)
                    security_counts[event_type] += 1
            
            # Check for unusual security activity
            for event_type, count in security_counts.items():
                if count > 5:  # Threshold for unusual activity
                    anomaly = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "anomaly_type": "security_trend",
                        "severity": "high" if count > 10 else "medium",
                        "description": f"Unusual {event_type} activity: {count} events",
                        "log_ids": "[]",
                        "metadata": json.dumps({
                            "event_type": event_type,
                            "count": count,
                            "threshold": 5
                        })
                    }
                    self._store_anomaly(anomaly)
        
        except Exception as e:
            logger.error(f"Error analyzing security trends: {e}")
    
    def _analyze_performance_trends(self, logs: List[LogEntry]):
        """Analyze performance trends"""
        try:
            # Analyze response times
            response_times = []
            for log in logs:
                if "response_time" in log.metadata:
                    response_times.append(log.metadata["response_time"])
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                if avg_response_time > self.config.performance_thresholds.get("response_time_ms", 5000):
                    anomaly = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "anomaly_type": "performance_degradation",
                        "severity": "medium",
                        "description": f"High average response time: {avg_response_time:.2f}ms",
                        "log_ids": "[]",
                        "metadata": json.dumps({
                            "metric": "response_time",
                            "value": avg_response_time,
                            "threshold": self.config.performance_thresholds.get("response_time_ms", 5000)
                        })
                    }
                    self._store_anomaly(anomaly)
        
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
    
    def _store_anomaly(self, anomaly: Dict[str, Any]):
        """Store anomaly in database"""
        try:
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                conn.execute("""
                    INSERT INTO log_anomalies 
                    (timestamp, anomaly_type, severity, description, log_ids, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    anomaly["timestamp"],
                    anomaly["anomaly_type"],
                    anomaly["severity"],
                    anomaly["description"],
                    anomaly["log_ids"],
                    anomaly["metadata"]
                ))
        
        except Exception as e:
            logger.error(f"Error storing anomaly: {e}")
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                # Total logs
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM logs 
                    WHERE timestamp >= ?
                """, (cutoff_time.isoformat(),))
                total_logs = cursor.fetchone()[0]
                
                # Logs by level
                cursor = conn.execute("""
                    SELECT level, COUNT(*) FROM logs 
                    WHERE timestamp >= ?
                    GROUP BY level
                """, (cutoff_time.isoformat(),))
                logs_by_level = dict(cursor.fetchall())
                
                # Logs by source
                cursor = conn.execute("""
                    SELECT source, COUNT(*) FROM logs 
                    WHERE timestamp >= ?
                    GROUP BY source
                """, (cutoff_time.isoformat(),))
                logs_by_source = dict(cursor.fetchall())
                
                # Security events
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_events 
                    WHERE timestamp >= ?
                """, (cutoff_time.isoformat(),))
                security_events = cursor.fetchone()[0]
                
                # Anomalies
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM log_anomalies 
                    WHERE timestamp >= ?
                """, (cutoff_time.isoformat(),))
                anomalies = cursor.fetchone()[0]
                
                # Performance alerts
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM performance_metrics 
                    WHERE timestamp >= ? AND status = 'alert'
                """, (cutoff_time.isoformat(),))
                performance_alerts = cursor.fetchone()[0]
            
            return {
                "total_logs": total_logs,
                "logs_by_level": logs_by_level,
                "logs_by_source": logs_by_source,
                "security_events": security_events,
                "anomalies": anomalies,
                "performance_alerts": performance_alerts,
                "hours": hours
            }
        
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {"error": str(e)}
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent security events"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                cursor = conn.execute("""
                    SELECT timestamp, event_type, severity, source_ip, user_id, description, metadata, status
                    FROM security_events 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time.isoformat(),))
                
                events = []
                for row in cursor.fetchall():
                    event = {
                        "timestamp": row[0],
                        "event_type": row[1],
                        "severity": row[2],
                        "source_ip": row[3],
                        "user_id": row[4],
                        "description": row[5],
                        "metadata": json.loads(row[6]) if row[6] else {},
                        "status": row[7]
                    }
                    events.append(event)
                
                return events
        
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []
    
    def get_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect("/var/lib/mingus/logs.db") as conn:
                cursor = conn.execute("""
                    SELECT timestamp, anomaly_type, severity, description, metadata
                    FROM log_anomalies 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time.isoformat(),))
                
                anomalies = []
                for row in cursor.fetchall():
                    anomaly = {
                        "timestamp": row[0],
                        "anomaly_type": row[1],
                        "severity": row[2],
                        "description": row[3],
                        "metadata": json.loads(row[4]) if row[4] else {}
                    }
                    anomalies.append(anomaly)
                
                return anomalies
        
        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            return []

# Factory function for creating log aggregation configuration
def create_log_aggregation_config() -> LogAggregationConfig:
    """Create log aggregation configuration from environment variables"""
    return LogAggregationConfig(
        enabled=os.getenv('LOG_AGGREGATION_ENABLED', 'true').lower() == 'true',
        log_sources=[LogSource(s) for s in os.getenv('LOG_SOURCES', 'application,security,system').split(',')],
        aggregation_interval=int(os.getenv('LOG_AGGREGATION_INTERVAL', '60')),
        retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30')),
        analysis_enabled=os.getenv('LOG_ANALYSIS_ENABLED', 'true').lower() == 'true',
        anomaly_detection=os.getenv('LOG_ANOMALY_DETECTION', 'true').lower() == 'true',
        pattern_detection=os.getenv('LOG_PATTERN_DETECTION', 'true').lower() == 'true',
        security_analysis=os.getenv('LOG_SECURITY_ANALYSIS', 'true').lower() == 'true',
        performance_analysis=os.getenv('LOG_PERFORMANCE_ANALYSIS', 'true').lower() == 'true',
        compliance_analysis=os.getenv('LOG_COMPLIANCE_ANALYSIS', 'true').lower() == 'true',
        
        pattern_window_minutes=int(os.getenv('LOG_PATTERN_WINDOW_MINUTES', '60')),
        pattern_threshold=int(os.getenv('LOG_PATTERN_THRESHOLD', '10')),
        pattern_cooldown_minutes=int(os.getenv('LOG_PATTERN_COOLDOWN_MINUTES', '30')),
        
        anomaly_window_hours=int(os.getenv('LOG_ANOMALY_WINDOW_HOURS', '24')),
        anomaly_contamination=float(os.getenv('LOG_ANOMALY_CONTAMINATION', '0.1')),
        anomaly_threshold=float(os.getenv('LOG_ANOMALY_THRESHOLD', '0.8')),
        
        security_keywords=os.getenv('LOG_SECURITY_KEYWORDS', '').split(',') if os.getenv('LOG_SECURITY_KEYWORDS') else [],
        suspicious_ips=os.getenv('LOG_SUSPICIOUS_IPS', '').split(',') if os.getenv('LOG_SUSPICIOUS_IPS') else [],
        blacklisted_ips=os.getenv('LOG_BLACKLISTED_IPS', '').split(',') if os.getenv('LOG_BLACKLISTED_IPS') else [],
        
        performance_thresholds=json.loads(os.getenv('LOG_PERFORMANCE_THRESHOLDS', '{"response_time_ms": 5000, "error_rate_percent": 5.0, "throughput_requests_per_second": 100}'))
    )

# Global log aggregator instance
_log_aggregator = None

def get_log_aggregator() -> EnhancedLogAggregator:
    """Get global log aggregator instance"""
    global _log_aggregator
    
    if _log_aggregator is None:
        config = create_log_aggregation_config()
        _log_aggregator = EnhancedLogAggregator(config)
    
    return _log_aggregator 