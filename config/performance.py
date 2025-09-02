"""
Performance Configuration for AI Calculator
Optimized settings for <2 second load time, <500ms assessment submission, 99.9% uptime
"""

import os
from datetime import timedelta

class PerformanceConfig:
    """Performance optimization configuration"""
    
    # Database Optimization
    DATABASE_CONFIG = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 20)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 30)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 1800)),  # 30 minutes
        'pool_pre_ping': True,
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),
        'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
        
        # Read replica configuration
        'read_replica_url': os.getenv('READ_REPLICA_URL'),
        'read_replica_pool_size': int(os.getenv('READ_REPLICA_POOL_SIZE', 10)),
        'read_replica_max_overflow': int(os.getenv('READ_REPLICA_MAX_OVERFLOW', 20)),
        
        # Analytics pool
        'analytics_pool_size': int(os.getenv('ANALYTICS_POOL_SIZE', 5)),
        'analytics_max_overflow': int(os.getenv('ANALYTICS_MAX_OVERFLOW', 10)),
        
        # Celery pool
        'celery_pool_size': int(os.getenv('CELERY_POOL_SIZE', 10)),
        'celery_max_overflow': int(os.getenv('CELERY_MAX_OVERFLOW', 20))
    }
    
    # Redis Caching Configuration
    CACHE_CONFIG = {
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'default_ttl': int(os.getenv('CACHE_DEFAULT_TTL', 3600)),  # 1 hour
        'max_memory_mb': int(os.getenv('CACHE_MAX_MEMORY_MB', 1000)),
        'compression_enabled': os.getenv('CACHE_COMPRESSION', 'true').lower() == 'true',
        'compression_threshold': int(os.getenv('CACHE_COMPRESSION_THRESHOLD', 1024)),
        
        # Cache strategies
        'job_risk_cache_ttl': int(os.getenv('JOB_RISK_CACHE_TTL', 7200)),  # 2 hours
        'assessment_cache_ttl': int(os.getenv('ASSESSMENT_CACHE_TTL', 1800)),  # 30 minutes
        'user_profile_cache_ttl': int(os.getenv('USER_PROFILE_CACHE_TTL', 3600)),  # 1 hour
        'analytics_cache_ttl': int(os.getenv('ANALYTICS_CACHE_TTL', 300))  # 5 minutes
    }
    
    # Frontend Performance Configuration
    FRONTEND_CONFIG = {
        'bundle_splitting': True,
        'lazy_loading': True,
        'image_optimization': True,
        'cdn_enabled': os.getenv('CDN_ENABLED', 'true').lower() == 'true',
        'service_worker_enabled': True,
        'offline_support': True,
        
        # Progressive web app settings
        'pwa_name': "AI Job Impact Calculator - MINGUS",
        'pwa_short_name': "AI Calculator",
        'pwa_description': "Calculate your AI job impact and risk assessment",
        'pwa_theme_color': "#8A31FF",
        'pwa_background_color': "#FFFFFF"
    }
    
    # Scalability Configuration
    SCALABILITY_CONFIG = {
        'async_processing': True,
        'max_workers': int(os.getenv('MAX_WORKERS', 20)),
        'max_processes': int(os.getenv('MAX_PROCESSES', 4)),
        'queue_size': int(os.getenv('QUEUE_SIZE', 1000)),
        
        # Load balancing
        'load_balancer_enabled': os.getenv('LOAD_BALANCER_ENABLED', 'true').lower() == 'true',
        'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', 30)),
        'failover_enabled': True,
        
        # Auto-scaling
        'auto_scaling_enabled': os.getenv('AUTO_SCALING_ENABLED', 'true').lower() == 'true',
        'cpu_threshold': float(os.getenv('CPU_THRESHOLD', 80.0)),
        'memory_threshold': float(os.getenv('MEMORY_THRESHOLD', 85.0)),
        'scale_up_threshold': float(os.getenv('SCALE_UP_THRESHOLD', 70.0)),
        'scale_down_threshold': float(os.getenv('SCALE_DOWN_THRESHOLD', 30.0))
    }
    
    # Performance Targets
    PERFORMANCE_TARGETS = {
        'load_time_ms': 2000,  # <2 seconds
        'assessment_submission_ms': 500,  # <500ms
        'uptime_percentage': 99.9,  # 99.9% uptime
        'cache_hit_ratio': 0.8,  # 80% cache hit ratio
        'database_query_ms': 100,  # <100ms database queries
        'api_response_ms': 200  # <200ms API responses
    }
    
    # Monitoring Configuration
    MONITORING_CONFIG = {
        'metrics_enabled': True,
        'prometheus_enabled': os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true',
        'health_check_endpoint': '/health',
        'metrics_endpoint': '/metrics',
        'alerting_enabled': True,
        
        # Performance thresholds for alerting
        'alert_thresholds': {
            'load_time_ms': 3000,  # Alert if >3 seconds
            'assessment_submission_ms': 1000,  # Alert if >1 second
            'database_query_ms': 500,  # Alert if >500ms
            'cache_hit_ratio': 0.6,  # Alert if <60%
            'error_rate': 0.01  # Alert if >1% error rate
        }
    }
    
    # CDN Configuration
    CDN_CONFIG = {
        'enabled': os.getenv('CDN_ENABLED', 'true').lower() == 'true',
        'provider': os.getenv('CDN_PROVIDER', 'cloudflare'),
        'domain': os.getenv('CDN_DOMAIN', 'cdn.mingusapp.com'),
        'cache_headers': {
            'static_assets': 'public, max-age=31536000',  # 1 year
            'images': 'public, max-age=86400',  # 1 day
            'api_responses': 'public, max-age=300'  # 5 minutes
        }
    }
    
    # Mobile Optimization
    MOBILE_CONFIG = {
        'touch_targets_min_size': 44,  # Minimum 44px for touch targets
        'image_optimization': True,
        'font_optimization': True,
        'offline_support': True,
        'reduced_data_usage': True
    }
    
    @classmethod
    def get_database_config(cls):
        """Get database configuration"""
        return cls.DATABASE_CONFIG
    
    @classmethod
    def get_cache_config(cls):
        """Get cache configuration"""
        return cls.CACHE_CONFIG
    
    @classmethod
    def get_frontend_config(cls):
        """Get frontend configuration"""
        return cls.FRONTEND_CONFIG
    
    @classmethod
    def get_scalability_config(cls):
        """Get scalability configuration"""
        return cls.SCALABILITY_CONFIG
    
    @classmethod
    def get_performance_targets(cls):
        """Get performance targets"""
        return cls.PERFORMANCE_TARGETS
    
    @classmethod
    def get_monitoring_config(cls):
        """Get monitoring configuration"""
        return cls.MONITORING_CONFIG
    
    @classmethod
    def get_cdn_config(cls):
        """Get CDN configuration"""
        return cls.CDN_CONFIG
    
    @classmethod
    def get_mobile_config(cls):
        """Get mobile optimization configuration"""
        return cls.MOBILE_CONFIG
    
    @classmethod
    def validate_config(cls):
        """Validate performance configuration"""
        errors = []
        
        # Validate database config
        db_config = cls.DATABASE_CONFIG
        if db_config['pool_size'] < 5:
            errors.append("Database pool size should be at least 5")
        if db_config['max_overflow'] < 10:
            errors.append("Database max overflow should be at least 10")
        
        # Validate cache config
        cache_config = cls.CACHE_CONFIG
        if cache_config['default_ttl'] < 60:
            errors.append("Cache TTL should be at least 60 seconds")
        if cache_config['max_memory_mb'] < 100:
            errors.append("Cache max memory should be at least 100MB")
        
        # Validate scalability config
        scalability_config = cls.SCALABILITY_CONFIG
        if scalability_config['max_workers'] < 5:
            errors.append("Max workers should be at least 5")
        if scalability_config['cpu_threshold'] > 100:
            errors.append("CPU threshold cannot exceed 100%")
        
        return errors
