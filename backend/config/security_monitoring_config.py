"""
Security Monitoring Configuration
Configuration settings for comprehensive security monitoring system
"""

import os
from typing import Dict, Any

class SecurityMonitoringConfig:
    """Configuration for security monitoring system"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/mingus')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging Configuration
    SECURITY_LOG_PATH = os.getenv('SECURITY_LOG_PATH', '/secure/logs/security_events.log')
    SECURITY_LOG_LEVEL = os.getenv('SECURITY_LOG_LEVEL', 'INFO')
    SECURITY_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Email Alerting Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'security@mingus.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ALERT_RECIPIENTS = os.getenv('ALERT_RECIPIENTS', 'security@mingus.com,admin@mingus.com').split(',')
    
    # Alert Thresholds Configuration
    ALERT_THRESHOLDS = {
        'failed_logins': {
            'count': int(os.getenv('FAILED_LOGINS_THRESHOLD', '5')),
            'window': int(os.getenv('FAILED_LOGINS_WINDOW', '300')),  # 5 minutes
            'severity': 'WARNING'
        },
        'injection_attempts': {
            'count': int(os.getenv('INJECTION_ATTEMPTS_THRESHOLD', '3')),
            'window': int(os.getenv('INJECTION_ATTEMPTS_WINDOW', '300')),  # 5 minutes
            'severity': 'CRITICAL'
        },
        'rate_limit_violations': {
            'count': int(os.getenv('RATE_LIMIT_VIOLATIONS_THRESHOLD', '10')),
            'window': int(os.getenv('RATE_LIMIT_VIOLATIONS_WINDOW', '600')),  # 10 minutes
            'severity': 'WARNING'
        },
        'assessment_anomalies': {
            'count': int(os.getenv('ASSESSMENT_ANOMALIES_THRESHOLD', '2')),
            'window': int(os.getenv('ASSESSMENT_ANOMALIES_WINDOW', '3600')),  # 1 hour
            'severity': 'WARNING'
        },
        'suspicious_activities': {
            'count': int(os.getenv('SUSPICIOUS_ACTIVITIES_THRESHOLD', '5')),
            'window': int(os.getenv('SUSPICIOUS_ACTIVITIES_WINDOW', '1800')),  # 30 minutes
            'severity': 'WARNING'
        },
        'brute_force_attempts': {
            'count': int(os.getenv('BRUTE_FORCE_ATTEMPTS_THRESHOLD', '10')),
            'window': int(os.getenv('BRUTE_FORCE_ATTEMPTS_WINDOW', '300')),  # 5 minutes
            'severity': 'CRITICAL'
        }
    }
    
    # Anomaly Detection Configuration
    ANOMALY_DETECTION = {
        'baseline_window': int(os.getenv('ANOMALY_BASELINE_WINDOW', '7')),  # days
        'anomaly_threshold': float(os.getenv('ANOMALY_THRESHOLD', '2.5')),  # standard deviations
        'completion_time_threshold': float(os.getenv('COMPLETION_TIME_THRESHOLD', '0.1')),  # 10% of average
        'score_range_threshold': float(os.getenv('SCORE_RANGE_THRESHOLD', '0.05'))  # 5% outside normal range
    }
    
    # Assessment Type Configuration
    ASSESSMENT_CONFIGS = {
        'ai_job_risk': {
            'avg_completion_time': 240,  # 4 minutes
            'score_range': (20, 80),     # 20-80% risk
            'min_questions': 5,
            'max_questions': 20
        },
        'relationship_impact': {
            'avg_completion_time': 300,  # 5 minutes
            'score_range': (10, 90),     # 10-90% impact
            'min_questions': 8,
            'max_questions': 25
        },
        'tax_impact': {
            'avg_completion_time': 180,  # 3 minutes
            'score_range': (15, 85),     # 15-85% impact
            'min_questions': 6,
            'max_questions': 15
        },
        'income_comparison': {
            'avg_completion_time': 210,  # 3.5 minutes
            'score_range': (25, 75),     # 25-75% comparison
            'min_questions': 4,
            'max_questions': 12
        }
    }
    
    # Security Patterns Configuration
    SECURITY_PATTERNS = {
        'sql_injection': [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(\b(exec|execute)\b\s+(sp_|xp_|procedure|function))",
            r"(--\s|#\s|/\*|\*/|--\s*$|--\s*;)",
            r"(\b(or|and)\b\s*['\"]?\w*['\"]?\s*[=<>])",
            r"(\b(char|ascii|substring|length)\b\s*\([^)]*\))",
            r"(waitfor\s+delay|benchmark\s*\()",
            r"(\b(declare|cast|convert)\b)",
            r"(\b(xp_cmdshell|sp_executesql)\b)",
            r"(\b(backup|restore|attach|detach)\b\s+(database|table|file))",
            r"(\b(grant|revoke|deny)\b)"
        ],
        'xss_attack': [
            r"(<script[^>]*>.*?</script>)",
            r"(<script[^>]*>)",
            r"(javascript:.*)",
            r"(on\w+\s*=)",
            r"(<iframe[^>]*>)",
            r"(<object[^>]*>)",
            r"(<embed[^>]*>)",
            r"(<link[^>]*>)",
            r"(<meta[^>]*>)",
            r"(<form[^>]*>)",
            r"(<input[^>]*>)",
            r"(<textarea[^>]*>)",
            r"(<select[^>]*>)",
            r"(<button[^>]*>)",
            r"(<a[^>]*href\s*=\s*[\"']javascript:)",
            r"(<img[^>]*on\w+\s*=)",
            r"(<svg[^>]*on\w+\s*=)",
            r"(<math[^>]*on\w+\s*=)",
            r"(<link[^>]*on\w+\s*=)",
            r"(<body[^>]*on\w+\s*=)",
            r"(<div[^>]*on\w+\s*=)"
        ],
        'command_injection': [
            r"(\b(cat|ls|pwd|whoami|id|uname)\b)",
            r"(\b(rm|del|mkdir|touch|chmod)\b)",
            r"(\b(wget|curl|nc|telnet|ssh)\b)",
            r"(\b(python|perl|ruby|php|bash|sh)\b)",
            r"(&&|\|\||`|\$\()",
            r"(\b(sudo|su|sudoers)\b)",
            r"(\b(kill|ps|top|htop)\b)",
            r"(\b(netstat|ifconfig|ipconfig)\b)",
            r"(\b(ping|traceroute|nslookup)\b)",
            r"(\b(find|grep|sed|awk)\b)",
            r"(\b(tar|zip|unzip|gzip|gunzip)\b)",
            r"(\b(docker|kubectl|helm)\b)"
        ],
        'suspicious_user_agents': [
            'bot', 'crawler', 'spider', 'scraper',
            'curl', 'wget', 'python-requests',
            'masscan', 'nmap', 'sqlmap',
            'nikto', 'dirb', 'gobuster'
        ],
        'suspicious_headers': [
            'X-Forwarded-For', 'X-Real-IP', 'X-Client-IP',
            'CF-Connecting-IP', 'True-Client-IP',
            'X-Originating-IP', 'X-Remote-IP'
        ]
    }
    
    # Data Retention Configuration
    DATA_RETENTION = {
        'security_events_days': int(os.getenv('SECURITY_EVENTS_RETENTION_DAYS', '90')),
        'security_alerts_days': int(os.getenv('SECURITY_ALERTS_RETENTION_DAYS', '90')),
        'assessment_anomalies_days': int(os.getenv('ASSESSMENT_ANOMALIES_RETENTION_DAYS', '90')),
        'security_metrics_days': int(os.getenv('SECURITY_METRICS_RETENTION_DAYS', '90')),
        'audit_log_days': int(os.getenv('AUDIT_LOG_RETENTION_DAYS', '365'))
    }
    
    # Rate Limiting Configuration
    RATE_LIMITING = {
        'assessment_submissions_per_minute': int(os.getenv('ASSESSMENT_SUBMISSIONS_PER_MINUTE', '10')),
        'authentication_attempts_per_minute': int(os.getenv('AUTH_ATTEMPTS_PER_MINUTE', '5')),
        'api_requests_per_minute': int(os.getenv('API_REQUESTS_PER_MINUTE', '100')),
        'block_duration_minutes': int(os.getenv('BLOCK_DURATION_MINUTES', '30'))
    }
    
    # Monitoring Configuration
    MONITORING = {
        'enable_real_time_monitoring': os.getenv('ENABLE_REAL_TIME_MONITORING', 'true').lower() == 'true',
        'enable_email_alerts': os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true',
        'enable_anomaly_detection': os.getenv('ENABLE_ANOMALY_DETECTION', 'true').lower() == 'true',
        'enable_rate_limiting': os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
        'enable_ip_blocking': os.getenv('ENABLE_IP_BLOCKING', 'true').lower() == 'true',
        'monitoring_interval_seconds': int(os.getenv('MONITORING_INTERVAL_SECONDS', '60'))
    }
    
    # Dashboard Configuration
    DASHBOARD = {
        'refresh_interval_seconds': int(os.getenv('DASHBOARD_REFRESH_INTERVAL', '30')),
        'max_displayed_events': int(os.getenv('MAX_DISPLAYED_EVENTS', '100')),
        'max_displayed_alerts': int(os.getenv('MAX_DISPLAYED_ALERTS', '50')),
        'chart_time_range_hours': int(os.getenv('CHART_TIME_RANGE_HOURS', '24'))
    }
    
    @classmethod
    def get_assessment_config(cls, assessment_type: str) -> Dict[str, Any]:
        """Get configuration for specific assessment type"""
        return cls.ASSESSMENT_CONFIGS.get(assessment_type, {
            'avg_completion_time': 240,
            'score_range': (0, 100),
            'min_questions': 1,
            'max_questions': 50
        })
    
    @classmethod
    def get_alert_threshold(cls, threshold_type: str) -> Dict[str, Any]:
        """Get alert threshold configuration"""
        return cls.ALERT_THRESHOLDS.get(threshold_type, {
            'count': 5,
            'window': 300,
            'severity': 'WARNING'
        })
    
    @classmethod
    def is_monitoring_enabled(cls, feature: str) -> bool:
        """Check if specific monitoring feature is enabled"""
        return cls.MONITORING.get(f'enable_{feature}', True)
    
    @classmethod
    def get_retention_days(cls, data_type: str) -> int:
        """Get retention period for data type"""
        return cls.DATA_RETENTION.get(f'{data_type}_days', 90)
