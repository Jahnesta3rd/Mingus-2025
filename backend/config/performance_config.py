#!/usr/bin/env python3
"""
Mingus Application - Performance Configuration
Comprehensive configuration for Daily Outlook system performance optimization
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    redis_url: str = "redis://localhost:6379/0"
    max_connections: int = 20
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    
    # Cache TTL settings (seconds)
    daily_outlook_ttl: int = 86400  # 24 hours
    balance_score_ttl: int = 3600   # 1 hour
    content_template_ttl: int = 604800  # 7 days
    peer_comparison_ttl: int = 1800  # 30 minutes
    user_aggregation_ttl: int = 1800  # 30 minutes
    analytics_data_ttl: int = 3600  # 1 hour
    
    # Compression settings
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    compression_level: int = 6

@dataclass
class DatabaseConfig:
    """Database optimization configuration"""
    # Connection pool settings
    max_connections: int = 20
    min_connections: int = 5
    connection_timeout: int = 30
    
    # Query optimization
    enable_query_cache: bool = True
    query_cache_ttl: int = 300  # 5 minutes
    
    # Read replica settings
    read_replica_url: Optional[str] = None
    use_read_replica_for_analytics: bool = True
    
    # Index optimization
    auto_create_indexes: bool = True
    index_maintenance_interval: int = 3600  # 1 hour

@dataclass
class APIConfig:
    """API performance configuration"""
    # Rate limiting
    enable_rate_limiting: bool = True
    default_rate_limit: int = 100  # requests per hour
    tier_rate_limits: Dict[str, int] = None
    
    # Response optimization
    enable_compression: bool = True
    enable_etags: bool = True
    compression_level: int = 6
    
    # Batch API settings
    max_batch_size: int = 50
    batch_timeout: int = 30  # seconds
    
    # Performance monitoring
    enable_performance_monitoring: bool = True
    prometheus_port: int = 8000

@dataclass
class BackgroundProcessingConfig:
    """Background processing configuration"""
    # Cache warming
    enable_cache_warming: bool = True
    cache_warming_schedule: str = "0 5 * * *"  # 5:00 AM daily
    warming_batch_size: int = 50
    warming_delay_between_batches: float = 2.0
    
    # Analytics pre-computation
    enable_analytics_precompute: bool = True
    precompute_schedule: str = "0 2 * * *"  # 2:00 AM daily
    precompute_batch_size: int = 20
    
    # Task processing
    max_workers: int = 4
    task_timeout: int = 300  # 5 minutes
    max_retries: int = 3

@dataclass
class FrontendConfig:
    """Frontend optimization configuration"""
    # Service worker
    enable_service_worker: bool = True
    sw_cache_strategy: str = "cache-first"
    sw_cache_ttl: int = 86400  # 24 hours
    
    # Progressive loading
    enable_progressive_loading: bool = True
    loading_batch_size: int = 3
    loading_delay: int = 100  # milliseconds
    
    # Image optimization
    enable_image_optimization: bool = True
    image_quality: int = 80
    image_format: str = "webp"
    lazy_loading_threshold: int = 50  # pixels
    
    # Component lazy loading
    enable_lazy_loading: bool = True
    preload_critical_components: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    # Performance monitoring
    enable_performance_monitoring: bool = True
    metrics_retention_days: int = 30
    alert_thresholds: Dict[str, float] = None
    
    # Health checks
    enable_health_checks: bool = True
    health_check_interval: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    enable_structured_logging: bool = True
    
    # Prometheus
    enable_prometheus: bool = True
    prometheus_port: int = 8000

class PerformanceConfig:
    """
    Main performance configuration class
    
    Consolidates all performance-related settings and provides
    environment-based configuration management
    """
    
    def __init__(self, environment: str = None):
        """
        Initialize performance configuration
        
        Args:
            environment: Environment name (development, staging, production)
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        
        # Initialize configuration sections
        self.cache = self._get_cache_config()
        self.database = self._get_database_config()
        self.api = self._get_api_config()
        self.background_processing = self._get_background_processing_config()
        self.frontend = self._get_frontend_config()
        self.monitoring = self._get_monitoring_config()
        
        # Performance targets
        self.performance_targets = self._get_performance_targets()
        
        logger.info(f"Performance configuration initialized for {self.environment} environment")
    
    def _get_cache_config(self) -> CacheConfig:
        """Get cache configuration based on environment"""
        base_config = CacheConfig()
        
        if self.environment == 'production':
            base_config.max_connections = 50
            base_config.daily_outlook_ttl = 86400  # 24 hours
            base_config.balance_score_ttl = 1800   # 30 minutes
            base_config.enable_compression = True
            base_config.compression_level = 9
        elif self.environment == 'staging':
            base_config.max_connections = 30
            base_config.daily_outlook_ttl = 43200  # 12 hours
            base_config.balance_score_ttl = 3600   # 1 hour
        else:  # development
            base_config.max_connections = 10
            base_config.daily_outlook_ttl = 3600   # 1 hour
            base_config.balance_score_ttl = 1800  # 30 minutes
        
        # Override with environment variables
        base_config.redis_url = os.getenv('REDIS_URL', base_config.redis_url)
        base_config.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', base_config.max_connections))
        
        return base_config
    
    def _get_database_config(self) -> DatabaseConfig:
        """Get database configuration based on environment"""
        base_config = DatabaseConfig()
        
        if self.environment == 'production':
            base_config.max_connections = 50
            base_config.min_connections = 10
            base_config.connection_timeout = 30
            base_config.use_read_replica_for_analytics = True
        elif self.environment == 'staging':
            base_config.max_connections = 30
            base_config.min_connections = 5
            base_config.connection_timeout = 20
        else:  # development
            base_config.max_connections = 10
            base_config.min_connections = 2
            base_config.connection_timeout = 10
            base_config.use_read_replica_for_analytics = False
        
        # Override with environment variables
        base_config.read_replica_url = os.getenv('DATABASE_READ_REPLICA_URL')
        
        return base_config
    
    def _get_api_config(self) -> APIConfig:
        """Get API configuration based on environment"""
        base_config = APIConfig()
        
        # Set tier-based rate limits
        base_config.tier_rate_limits = {
            'budget': 50,
            'mid_tier': 100,
            'professional': 200,
            'enterprise': 500
        }
        
        if self.environment == 'production':
            base_config.default_rate_limit = 200
            base_config.max_batch_size = 100
            base_config.compression_level = 9
        elif self.environment == 'staging':
            base_config.default_rate_limit = 150
            base_config.max_batch_size = 75
            base_config.compression_level = 6
        else:  # development
            base_config.default_rate_limit = 1000  # More lenient for development
            base_config.max_batch_size = 50
            base_config.compression_level = 4
        
        return base_config
    
    def _get_background_processing_config(self) -> BackgroundProcessingConfig:
        """Get background processing configuration based on environment"""
        base_config = BackgroundProcessingConfig()
        
        if self.environment == 'production':
            base_config.max_workers = 8
            base_config.warming_batch_size = 100
            base_config.precompute_batch_size = 50
            base_config.task_timeout = 600  # 10 minutes
        elif self.environment == 'staging':
            base_config.max_workers = 4
            base_config.warming_batch_size = 50
            base_config.precompute_batch_size = 20
            base_config.task_timeout = 300  # 5 minutes
        else:  # development
            base_config.max_workers = 2
            base_config.warming_batch_size = 10
            base_config.precompute_batch_size = 5
            base_config.task_timeout = 120  # 2 minutes
            base_config.enable_cache_warming = False  # Disable in development
            base_config.enable_analytics_precompute = False
        
        return base_config
    
    def _get_frontend_config(self) -> FrontendConfig:
        """Get frontend configuration based on environment"""
        base_config = FrontendConfig()
        
        if self.environment == 'production':
            base_config.image_quality = 85
            base_config.loading_batch_size = 5
            base_config.preload_critical_components = True
        elif self.environment == 'staging':
            base_config.image_quality = 80
            base_config.loading_batch_size = 3
            base_config.preload_critical_components = True
        else:  # development
            base_config.image_quality = 70
            base_config.loading_batch_size = 2
            base_config.preload_critical_components = False
            base_config.enable_service_worker = False  # Disable in development
        
        return base_config
    
    def _get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration based on environment"""
        base_config = MonitoringConfig()
        
        # Set alert thresholds
        base_config.alert_thresholds = {
            'daily_outlook_load_time': 0.5,  # 500ms
            'balance_score_calculation_time': 0.2,  # 200ms
            'cache_hit_rate': 0.95,  # 95%
            'memory_usage': 0.8,  # 80%
            'cpu_usage': 0.8,  # 80%
            'error_rate': 0.05  # 5%
        }
        
        if self.environment == 'production':
            base_config.metrics_retention_days = 90
            base_config.health_check_interval = 30
            base_config.log_level = "WARNING"
        elif self.environment == 'staging':
            base_config.metrics_retention_days = 30
            base_config.health_check_interval = 60
            base_config.log_level = "INFO"
        else:  # development
            base_config.metrics_retention_days = 7
            base_config.health_check_interval = 300
            base_config.log_level = "DEBUG"
            base_config.enable_performance_monitoring = False  # Disable in development
        
        return base_config
    
    def _get_performance_targets(self) -> Dict[str, Any]:
        """Get performance targets based on environment"""
        targets = {
            'daily_outlook_load_time': 0.5,  # 500ms
            'balance_score_calculation_time': 0.2,  # 200ms
            'cache_hit_rate': 0.95,  # 95%
            'concurrent_users': 10000,
            'api_response_time': 0.1,  # 100ms
            'database_query_time': 0.05,  # 50ms
            'memory_usage': 0.8,  # 80%
            'cpu_usage': 0.8  # 80%
        }
        
        if self.environment == 'production':
            targets['concurrent_users'] = 10000
            targets['daily_outlook_load_time'] = 0.3  # 300ms
            targets['balance_score_calculation_time'] = 0.1  # 100ms
        elif self.environment == 'staging':
            targets['concurrent_users'] = 1000
            targets['daily_outlook_load_time'] = 0.5  # 500ms
            targets['balance_score_calculation_time'] = 0.2  # 200ms
        else:  # development
            targets['concurrent_users'] = 100
            targets['daily_outlook_load_time'] = 1.0  # 1 second
            targets['balance_score_calculation_time'] = 0.5  # 500ms
        
        return targets
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary"""
        return {
            'url': self.cache.redis_url,
            'max_connections': self.cache.max_connections,
            'socket_timeout': self.cache.socket_timeout,
            'retry_on_timeout': self.cache.retry_on_timeout
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary"""
        return {
            'max_connections': self.database.max_connections,
            'min_connections': self.database.min_connections,
            'connection_timeout': self.database.connection_timeout,
            'read_replica_url': self.database.read_replica_url,
            'use_read_replica_for_analytics': self.database.use_read_replica_for_analytics
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration dictionary"""
        return {
            'rate_limiting': {
                'enabled': self.api.enable_rate_limiting,
                'default_limit': self.api.default_rate_limit,
                'tier_limits': self.api.tier_rate_limits
            },
            'compression': {
                'enabled': self.api.enable_compression,
                'level': self.api.compression_level
            },
            'etags': {
                'enabled': self.api.enable_etags
            },
            'batch': {
                'max_size': self.api.max_batch_size,
                'timeout': self.api.batch_timeout
            }
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration dictionary"""
        return {
            'performance_monitoring': {
                'enabled': self.monitoring.enable_performance_monitoring,
                'retention_days': self.monitoring.metrics_retention_days,
                'alert_thresholds': self.monitoring.alert_thresholds
            },
            'health_checks': {
                'enabled': self.monitoring.enable_health_checks,
                'interval': self.monitoring.health_check_interval
            },
            'prometheus': {
                'enabled': self.monitoring.enable_prometheus,
                'port': self.monitoring.prometheus_port
            },
            'logging': {
                'level': self.monitoring.log_level,
                'structured': self.monitoring.enable_structured_logging
            }
        }
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return any issues
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # Validate cache configuration
        if self.cache.max_connections < 1:
            issues.append("Cache max_connections must be at least 1")
        
        if self.cache.daily_outlook_ttl < 0:
            issues.append("Daily outlook TTL must be non-negative")
        
        # Validate database configuration
        if self.database.max_connections < self.database.min_connections:
            issues.append("Database max_connections must be >= min_connections")
        
        # Validate API configuration
        if self.api.max_batch_size < 1:
            issues.append("API max_batch_size must be at least 1")
        
        if self.api.compression_level < 1 or self.api.compression_level > 9:
            issues.append("API compression_level must be between 1 and 9")
        
        # Validate performance targets
        if self.performance_targets['daily_outlook_load_time'] <= 0:
            issues.append("Daily outlook load time target must be positive")
        
        if self.performance_targets['cache_hit_rate'] < 0 or self.performance_targets['cache_hit_rate'] > 1:
            issues.append("Cache hit rate target must be between 0 and 1")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'environment': self.environment,
            'cache': self.cache.__dict__,
            'database': self.database.__dict__,
            'api': self.api.__dict__,
            'background_processing': self.background_processing.__dict__,
            'frontend': self.frontend.__dict__,
            'monitoring': self.monitoring.__dict__,
            'performance_targets': self.performance_targets
        }

# Global configuration instance
performance_config = None

def get_performance_config(environment: str = None) -> PerformanceConfig:
    """Get global performance configuration instance"""
    global performance_config
    if performance_config is None:
        performance_config = PerformanceConfig(environment)
    return performance_config

def initialize_performance_system(environment: str = None) -> Dict[str, Any]:
    """
    Initialize the complete performance optimization system
    
    Args:
        environment: Environment name
        
    Returns:
        Dictionary containing initialization status
    """
    try:
        # Get configuration
        config = get_performance_config(environment)
        
        # Validate configuration
        issues = config.validate_config()
        if issues:
            logger.warning(f"Configuration issues found: {issues}")
        
        # Initialize Redis connection
        import redis
        redis_client = redis.from_url(config.cache.redis_url)
        
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize database optimizer
        from backend.optimization.database_optimization import DatabaseOptimizer
        from backend.models.database import db
        
        db_optimizer = DatabaseOptimizer(db.session)
        
        # Create database indexes
        if config.database.auto_create_indexes:
            db_optimizer.create_daily_outlook_indexes()
            db_optimizer.create_user_aggregation_indexes()
            logger.info("Database indexes created")
        
        # Initialize API optimizer
        from backend.optimization.api_performance import APIPerformanceOptimizer
        
        api_optimizer = APIPerformanceOptimizer(redis_client)
        
        # Initialize performance monitoring
        from backend.monitoring.performance_monitoring import initialize_performance_monitoring
        
        performance_monitor = initialize_performance_monitoring(
            redis_client, 
            db.session, 
            config.monitoring.prometheus_port
        )
        
        # Initialize background processing
        from backend.tasks.background_processing import CacheWarmingScheduler, AnalyticsPreComputer
        
        cache_warming_scheduler = CacheWarmingScheduler(redis_client, db.session)
        analytics_precomputer = AnalyticsPreComputer(redis_client, db.session)
        
        logger.info("Performance optimization system initialized successfully")
        
        return {
            'status': 'success',
            'environment': config.environment,
            'components': {
                'cache': 'initialized',
                'database': 'initialized',
                'api': 'initialized',
                'monitoring': 'initialized',
                'background_processing': 'initialized'
            },
            'performance_targets': config.performance_targets,
            'configuration_issues': issues
        }
        
    except Exception as e:
        logger.error(f"Error initializing performance system: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'components': {}
        }
