#!/usr/bin/env python3
"""
MINGUS Optimal Living Location - Production Configuration

Production-specific configuration for the Optimal Living Location feature
including API keys, rate limiting, database pooling, and Redis caching.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
import redis
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

# Configure logging
logger = logging.getLogger(__name__)

class ProductionHousingConfig:
    """
    Production configuration for Optimal Living Location feature
    """
    
    def __init__(self):
        """Initialize production configuration"""
        self._validate_environment()
        self._setup_database_pooling()
        self._setup_redis_config()
        self._setup_api_configs()
        self._setup_rate_limiting()
        logger.info("Production housing configuration initialized")
    
    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = [
            'RENTALS_API_KEY',
            'ZILLOW_RAPIDAPI_KEY', 
            'GOOGLE_MAPS_API_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'SECRET_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("Environment validation passed")
    
    def _setup_database_pooling(self):
        """Setup database connection pooling for housing data"""
        self.database_config = {
            'url': os.environ.get('DATABASE_URL'),
            'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
            'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
            'pool_pre_ping': True,
            'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true'
        }
        
        # Create engine with connection pooling
        self.db_engine = create_engine(
            self.database_config['url'],
            poolclass=QueuePool,
            pool_size=self.database_config['pool_size'],
            max_overflow=self.database_config['max_overflow'],
            pool_timeout=self.database_config['pool_timeout'],
            pool_recycle=self.database_config['pool_recycle'],
            pool_pre_ping=self.database_config['pool_pre_ping'],
            echo=self.database_config['echo']
        )
        
        logger.info(f"Database pooling configured: {self.database_config['pool_size']} connections")
    
    def _setup_redis_config(self):
        """Setup Redis configuration for route caching"""
        self.redis_config = {
            'url': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
            'password': os.environ.get('REDIS_PASSWORD'),
            'max_connections': int(os.environ.get('REDIS_MAX_CONNECTIONS', 50)),
            'socket_timeout': int(os.environ.get('REDIS_SOCKET_TIMEOUT', 5)),
            'socket_connect_timeout': int(os.environ.get('REDIS_CONNECT_TIMEOUT', 5)),
            'retry_on_timeout': True,
            'decode_responses': True
        }
        
        # Create Redis connection pool
        self.redis_pool = redis.ConnectionPool.from_url(
            self.redis_config['url'],
            password=self.redis_config['password'],
            max_connections=self.redis_config['max_connections'],
            socket_timeout=self.redis_config['socket_timeout'],
            socket_connect_timeout=self.redis_config['socket_connect_timeout'],
            retry_on_timeout=self.redis_config['retry_on_timeout'],
            decode_responses=self.redis_config['decode_responses']
        )
        
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        logger.info(f"Redis configuration initialized: {self.redis_config['max_connections']} connections")
    
    def _setup_api_configs(self):
        """Setup production API configurations"""
        self.api_configs = {
            'rentals': {
                'api_key': os.environ.get('RENTALS_API_KEY'),
                'base_url': os.environ.get('RENTALS_BASE_URL', 'https://api.rentals.com/v1'),
                'timeout': int(os.environ.get('RENTALS_TIMEOUT', 30)),
                'retry_attempts': int(os.environ.get('RENTALS_RETRY_ATTEMPTS', 3)),
                'rate_limit_per_minute': int(os.environ.get('RENTALS_RATE_LIMIT', 60)),
                'rate_limit_per_hour': int(os.environ.get('RENTALS_HOURLY_LIMIT', 1000))
            },
            'zillow': {
                'api_key': os.environ.get('ZILLOW_RAPIDAPI_KEY'),
                'base_url': os.environ.get('ZILLOW_BASE_URL', 'https://zillow-com1.p.rapidapi.com'),
                'timeout': int(os.environ.get('ZILLOW_TIMEOUT', 30)),
                'retry_attempts': int(os.environ.get('ZILLOW_RETRY_ATTEMPTS', 3)),
                'rate_limit_per_minute': int(os.environ.get('ZILLOW_RATE_LIMIT', 30)),
                'rate_limit_per_hour': int(os.environ.get('ZILLOW_HOURLY_LIMIT', 500))
            },
            'google_maps': {
                'api_key': os.environ.get('GOOGLE_MAPS_API_KEY'),
                'base_url': os.environ.get('GOOGLE_MAPS_BASE_URL', 'https://maps.googleapis.com/maps/api'),
                'timeout': int(os.environ.get('GOOGLE_MAPS_TIMEOUT', 15)),
                'retry_attempts': int(os.environ.get('GOOGLE_MAPS_RETRY_ATTEMPTS', 2)),
                'rate_limit_per_minute': int(os.environ.get('GOOGLE_MAPS_RATE_LIMIT', 100)),
                'rate_limit_per_hour': int(os.environ.get('GOOGLE_MAPS_HOURLY_LIMIT', 2000))
            }
        }
        
        logger.info("API configurations initialized")
    
    def _setup_rate_limiting(self):
        """Setup production rate limiting configuration"""
        self.rate_limiting = {
            'housing_searches': {
                'budget_tier': int(os.environ.get('BUDGET_TIER_SEARCH_LIMIT', 5)),
                'mid_tier': int(os.environ.get('MID_TIER_SEARCH_LIMIT', -1)),  # -1 = unlimited
                'professional_tier': int(os.environ.get('PROFESSIONAL_TIER_SEARCH_LIMIT', -1))
            },
            'scenario_saves': {
                'budget_tier': int(os.environ.get('BUDGET_TIER_SCENARIO_LIMIT', 3)),
                'mid_tier': int(os.environ.get('MID_TIER_SCENARIO_LIMIT', 10)),
                'professional_tier': int(os.environ.get('PROFESSIONAL_TIER_SCENARIO_LIMIT', -1))
            },
            'api_calls_per_user': {
                'per_minute': int(os.environ.get('USER_API_RATE_LIMIT', 60)),
                'per_hour': int(os.environ.get('USER_API_HOURLY_LIMIT', 1000)),
                'burst_limit': int(os.environ.get('USER_API_BURST_LIMIT', 10))
            }
        }
        
        logger.info("Rate limiting configuration initialized")
    
    def get_database_engine(self) -> Engine:
        """Get database engine with connection pooling"""
        return self.db_engine
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling"""
        return self.redis_client
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """Get API configuration by name"""
        return self.api_configs.get(api_name, {})
    
    def get_rate_limit(self, feature: str, tier: str) -> int:
        """Get rate limit for feature and tier"""
        return self.rate_limiting.get(feature, {}).get(tier, 0)
    
    def get_ssl_config(self) -> Dict[str, Any]:
        """Get SSL configuration for external API calls"""
        return {
            'verify_ssl': os.environ.get('VERIFY_SSL', 'true').lower() == 'true',
            'ssl_cert_path': os.environ.get('SSL_CERT_PATH'),
            'ssl_key_path': os.environ.get('SSL_KEY_PATH'),
            'ca_bundle_path': os.environ.get('CA_BUNDLE_PATH')
        }

class HousingDataRetentionPolicy:
    """Data retention policy for housing data"""
    
    def __init__(self):
        self.retention_periods = {
            'housing_searches': int(os.environ.get('HOUSING_SEARCHES_RETENTION_DAYS', 365)),
            'housing_scenarios': int(os.environ.get('HOUSING_SCENARIOS_RETENTION_DAYS', 1095)),  # 3 years
            'commute_route_cache': int(os.environ.get('ROUTE_CACHE_RETENTION_DAYS', 30)),
            'user_preferences': int(os.environ.get('PREFERENCES_RETENTION_DAYS', 1095))  # 3 years
        }
    
    def get_retention_days(self, data_type: str) -> int:
        """Get retention period in days for data type"""
        return self.retention_periods.get(data_type, 365)
    
    def should_retain_data(self, data_type: str, created_at) -> bool:
        """Check if data should be retained based on age"""
        from datetime import datetime, timedelta
        retention_days = self.get_retention_days(data_type)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return created_at > cutoff_date

class HousingBackupStrategy:
    """Backup strategy for housing data"""
    
    def __init__(self):
        self.backup_config = {
            'enabled': os.environ.get('HOUSING_BACKUP_ENABLED', 'true').lower() == 'true',
            'frequency': os.environ.get('HOUSING_BACKUP_FREQUENCY', 'daily'),
            'retention_days': int(os.environ.get('HOUSING_BACKUP_RETENTION_DAYS', 30)),
            's3_bucket': os.environ.get('HOUSING_BACKUP_S3_BUCKET'),
            'encryption_key': os.environ.get('HOUSING_BACKUP_ENCRYPTION_KEY')
        }
    
    def is_backup_enabled(self) -> bool:
        """Check if backup is enabled"""
        return self.backup_config['enabled']
    
    def get_backup_frequency(self) -> str:
        """Get backup frequency"""
        return self.backup_config['frequency']
    
    def get_retention_days(self) -> int:
        """Get backup retention period"""
        return self.backup_config['retention_days']

# Global instances
production_config = ProductionHousingConfig()
retention_policy = HousingDataRetentionPolicy()
backup_strategy = HousingBackupStrategy()

# Export configurations
__all__ = [
    'production_config',
    'retention_policy', 
    'backup_strategy'
]
