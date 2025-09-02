"""
Comprehensive Performance Optimization System for AI Calculator
Implements database optimization, caching, frontend performance, and scalability features
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
import hashlib
import pickle
import gzip

# Database and caching imports
import redis
from sqlalchemy import create_engine, text, Index, event
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.pool import QueuePool
from sqlalchemy.dialects.postgresql import JSONB
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Flask and web imports
from flask import Flask, request, g, current_app
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

# Celery for async processing
from celery import Celery, Task
from celery.utils.log import get_task_logger

# Monitoring and metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil

logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

# Prometheus metrics
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Cache hit ratio percentage')
DB_CONNECTION_POOL_SIZE = Gauge('db_connection_pool_size', 'Database connection pool size')
REDIS_CONNECTION_COUNT = Gauge('redis_connection_count', 'Active Redis connections')

# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

@dataclass
class DatabaseConfig:
    """Database optimization configuration"""
    pool_size: int = 20
    max_overflow: int = 30
    pool_recycle: int = 1800  # 30 minutes
    pool_pre_ping: bool = True
    pool_timeout: int = 30
    echo: bool = False
    
    # Read replica configuration
    read_replica_url: Optional[str] = None
    read_replica_pool_size: int = 10
    read_replica_max_overflow: int = 20
    
    # Connection pooling for different contexts
    analytics_pool_size: int = 5
    analytics_max_overflow: int = 10
    celery_pool_size: int = 10
    celery_max_overflow: int = 20

@dataclass
class CacheConfig:
    """Caching strategy configuration"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory_mb: int = 1000
    compression_enabled: bool = True
    compression_threshold: int = 1024  # Compress objects > 1KB
    
    # Cache strategies
    job_risk_cache_ttl: int = 7200  # 2 hours for job risk data
    assessment_cache_ttl: int = 1800  # 30 minutes for assessment data
    user_profile_cache_ttl: int = 3600  # 1 hour for user profiles
    analytics_cache_ttl: int = 300  # 5 minutes for analytics

@dataclass
class FrontendConfig:
    """Frontend performance configuration"""
    bundle_splitting: bool = True
    lazy_loading: bool = True
    image_optimization: bool = True
    cdn_enabled: bool = True
    service_worker_enabled: bool = True
    offline_support: bool = True
    
    # Progressive web app settings
    pwa_name: str = "AI Job Impact Calculator"
    pwa_short_name: str = "AI Calculator"
    pwa_description: str = "Calculate your AI job impact and risk assessment"
    pwa_theme_color: str = "#8A31FF"
    pwa_background_color: str = "#FFFFFF"

@dataclass
class ScalabilityConfig:
    """Scalability and load balancing configuration"""
    async_processing: bool = True
    max_workers: int = 20
    max_processes: int = 4
    queue_size: int = 1000
    
    # Load balancing
    load_balancer_enabled: bool = True
    health_check_interval: int = 30
    failover_enabled: bool = True
    
    # Auto-scaling
    auto_scaling_enabled: bool = True
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    scale_up_threshold: float = 70.0
    scale_down_threshold: float = 30.0

# =============================================================================
# DATABASE OPTIMIZATION
# =============================================================================

class DatabaseOptimizer:
    """Database performance optimization and connection management"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engines = {}
        self.session_factories = {}
        self.connection_pools = {}
        self._init_engines()
    
    def _init_engines(self):
        """Initialize database engines with optimized settings"""
        try:
            # Main application engine
            main_engine = create_engine(
                current_app.config['DATABASE_URL'],
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                pool_timeout=self.config.pool_timeout,
                echo=self.config.echo
            )
            
            self.engines['main'] = main_engine
            self.session_factories['main'] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=main_engine
            )
            
            # Read replica engine (if configured)
            if self.config.read_replica_url:
                read_engine = create_engine(
                    self.config.read_replica_url,
                    poolclass=QueuePool,
                    pool_size=self.config.read_replica_pool_size,
                    max_overflow=self.config.read_replica_max_overflow,
                    pool_recycle=self.config.pool_recycle,
                    pool_pre_ping=self.config.pool_pre_ping,
                    pool_timeout=self.config.pool_timeout,
                    echo=self.config.echo
                )
                
                self.engines['read_replica'] = read_engine
                self.session_factories['read_replica'] = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=read_engine
                )
            
            # Analytics engine (for heavy reporting queries)
            analytics_engine = create_engine(
                current_app.config['DATABASE_URL'],
                poolclass=QueuePool,
                pool_size=self.config.analytics_pool_size,
                max_overflow=self.config.analytics_max_overflow,
                pool_recycle=self.config.pool_recycle * 2,  # Longer recycle for analytics
                pool_pre_ping=self.config.pool_pre_ping,
                pool_timeout=self.config.pool_timeout * 2,  # Longer timeout for analytics
                echo=self.config.echo
            )
            
            self.engines['analytics'] = analytics_engine
            self.session_factories['analytics'] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=analytics_engine
            )
            
            logger.info("Database engines initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engines: {e}")
            raise
    
    def get_session(self, engine_type: str = 'main') -> Session:
        """Get database session for specified engine type"""
        if engine_type not in self.session_factories:
            raise ValueError(f"Unknown engine type: {engine_type}")
        
        return self.session_factories[engine_type]()
    
    def optimize_queries(self, session: Session, model_class, **filters):
        """Optimize queries with eager loading and proper indexing"""
        query = session.query(model_class)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(model_class, key):
                query = query.filter(getattr(model_class, key) == value)
        
        # Add eager loading for common relationships
        if hasattr(model_class, 'profile'):
            query = query.options(joinedload(model_class.profile))
        
        if hasattr(model_class, 'assessments'):
            query = query.options(joinedload(model_class.assessments))
        
        return query
    
    def create_performance_indexes(self):
        """Create performance indexes for common queries"""
        indexes = [
            # Job title lookups
            Index('idx_ai_job_assessments_job_title_gin', 'job_title', postgresql_using='gin'),
            Index('idx_ai_job_assessments_industry_job_title', 'industry', 'job_title'),
            
            # Assessment submissions
            Index('idx_ai_job_assessments_email_completed', 'email', 'completed_at'),
            Index('idx_ai_job_assessments_risk_level_score', 'overall_risk_level', 'automation_score'),
            
            # Analytics queries
            Index('idx_ai_job_assessments_created_at_risk', 'created_at', 'overall_risk_level'),
            Index('idx_ai_job_assessments_automation_augmentation', 'automation_score', 'augmentation_score'),
            
            # User tracking
            Index('idx_ai_job_assessments_user_id_created', 'user_id', 'created_at'),
            Index('idx_ai_job_assessments_lead_source_created', 'lead_source', 'created_at'),
        ]
        
        for index in indexes:
            try:
                index.create(current_app.config['DATABASE_URL'])
                logger.info(f"Created index: {index.name}")
            except Exception as e:
                logger.warning(f"Failed to create index {index.name}: {e}")

# =============================================================================
# CACHING STRATEGY
# =============================================================================

class CacheManager:
    """Advanced caching system with Redis and memory fallback"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = None
        self.memory_cache = OrderedDict()
        self.memory_stats = {'hits': 0, 'misses': 0, 'sets': 0}
        self._init_redis()
        self._lock = threading.RLock()
    
    def _init_redis(self):
        """Initialize Redis connection with optimized settings"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                decode_responses=True
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {e}")
            self.redis_client = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with fallback strategy"""
        try:
            # Try Redis first
            if self.redis_client:
                cached_value = self.redis_client.get(key)
                if cached_value:
                    if self.config.compression_enabled:
                        cached_value = self._decompress(cached_value)
                    self._record_metric("cache_hit_redis", 1)
                    return json.loads(cached_value)
            
            # Try memory cache
            with self._lock:
                if key in self.memory_cache:
                    self.memory_cache.move_to_end(key)
                    self.memory_stats['hits'] += 1
                    self._record_metric("cache_hit_memory", 1)
                    return self.memory_cache[key]
            
            self._record_metric("cache_miss", 1)
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with compression"""
        try:
            ttl = ttl or self.config.default_ttl
            serialized_value = json.dumps(value)
            
            # Compress if enabled and value is large enough
            if self.config.compression_enabled and len(serialized_value) > self.config.compression_threshold:
                serialized_value = self._compress(serialized_value)
            
            # Set in Redis
            if self.redis_client:
                self.redis_client.setex(key, ttl, serialized_value)
            
            # Set in memory cache
            with self._lock:
                self.memory_cache[key] = value
                self.memory_cache.move_to_end(key)
                self.memory_stats['sets'] += 1
                
                # Evict if memory limit exceeded
                if len(self.memory_cache) > 1000:  # Simple limit
                    self.memory_cache.popitem(last=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _compress(self, data: str) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data.encode('utf-8'))
    
    def _decompress(self, data: bytes) -> str:
        """Decompress data using gzip"""
        return gzip.decompress(data).decode('utf-8')
    
    def _record_metric(self, metric_name: str, value: int):
        """Record cache metrics"""
        try:
            if metric_name == "cache_hit_redis":
                REDIS_CONNECTION_COUNT.inc()
            elif metric_name == "cache_miss":
                CACHE_HIT_RATIO.set(self._calculate_hit_ratio())
        except Exception as e:
            logger.debug(f"Failed to record metric {metric_name}: {e}")
    
    def _calculate_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total_requests = self.memory_stats['hits'] + self.memory_stats['misses']
        if total_requests == 0:
            return 0.0
        return (self.memory_stats['hits'] / total_requests) * 100

# =============================================================================
# FRONTEND PERFORMANCE
# =============================================================================

class FrontendOptimizer:
    """Frontend performance optimization and asset management"""
    
    def __init__(self, config: FrontendConfig):
        self.config = config
        self.asset_manifest = {}
        self._init_asset_manifest()
    
    def _init_asset_manifest(self):
        """Initialize asset manifest for versioning and caching"""
        self.asset_manifest = {
            'css': {
                'main': '/static/css/main.min.css',
                'calculator': '/static/css/calculator.min.css',
                'responsive': '/static/css/responsive.min.css'
            },
            'js': {
                'main': '/static/js/main.min.js',
                'calculator': '/static/js/calculator.min.js',
                'analytics': '/static/js/analytics.min.js'
            },
            'images': {
                'logo': '/static/images/logo.webp',
                'hero': '/static/images/hero.webp',
                'icons': '/static/images/icons.svg'
            }
        }
    
    def optimize_html(self, html_content: str) -> str:
        """Optimize HTML content for performance"""
        optimizations = [
            self._minify_html,
            self._optimize_images,
            self._add_resource_hints,
            self._add_service_worker,
            self._add_pwa_manifest
        ]
        
        for optimization in optimizations:
            html_content = optimization(html_content)
        
        return html_content
    
    def _minify_html(self, html: str) -> str:
        """Minify HTML content"""
        # Remove unnecessary whitespace and comments
        import re
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        html = re.sub(r'\s+', ' ', html)
        html = re.sub(r'>\s+<', '><', html)
        return html.strip()
    
    def _optimize_images(self, html: str) -> str:
        """Optimize images with lazy loading and WebP format"""
        import re
        
        # Add lazy loading to images
        html = re.sub(
            r'<img([^>]+)>',
            r'<img\1 loading="lazy" decoding="async">',
            html
        )
        
        # Add WebP format with fallback
        html = re.sub(
            r'<img([^>]+src="[^"]+\.(jpg|jpeg|png))([^>]*)>',
            r'<picture><source srcset="\1.webp" type="image/webp"><img\1\3></picture>',
            html
        )
        
        return html
    
    def _add_resource_hints(self, html: str) -> str:
        """Add resource hints for faster loading"""
        hints = [
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            '<link rel="dns-prefetch" href="https://cdnjs.cloudflare.com">',
            '<link rel="dns-prefetch" href="https://fonts.googleapis.com">'
        ]
        
        # Insert hints in head
        head_end = html.find('</head>')
        if head_end != -1:
            html = html[:head_end] + '\n    ' + '\n    '.join(hints) + '\n' + html[head_end:]
        
        return html
    
    def _add_service_worker(self, html: str) -> str:
        """Add service worker for offline support"""
        if not self.config.service_worker_enabled:
            return html
        
        sw_script = '''
        <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js')
                    .then(function(registration) {
                        console.log('SW registered: ', registration);
                    })
                    .catch(function(registrationError) {
                        console.log('SW registration failed: ', registrationError);
                    });
            });
        }
        </script>
        '''
        
        body_end = html.find('</body>')
        if body_end != -1:
            html = html[:body_end] + sw_script + html[body_end:]
        
        return html
    
    def _add_pwa_manifest(self, html: str) -> str:
        """Add PWA manifest link"""
        if not self.config.service_worker_enabled:
            return html
        
        manifest_link = f'''
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="{self.config.pwa_theme_color}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="{self.config.pwa_short_name}">
        '''
        
        head_end = html.find('</head>')
        if head_end != -1:
            html = html[:head_end] + manifest_link + html[head_end:]
        
        return html

# =============================================================================
# SCALABILITY AND LOAD BALANCING
# =============================================================================

class ScalabilityManager:
    """Scalability management with auto-scaling and load balancing"""
    
    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.process_executor = ProcessPoolExecutor(max_processes=config.max_processes)
        self.task_queue = asyncio.Queue(maxsize=config.queue_size)
        self.health_status = {'healthy': True, 'last_check': datetime.now()}
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start system monitoring"""
        if self.config.auto_scaling_enabled:
            threading.Thread(target=self._monitor_resources, daemon=True).start()
    
    def _monitor_resources(self):
        """Monitor system resources for auto-scaling"""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                # Update health status
                self.health_status['healthy'] = (
                    cpu_percent < self.config.cpu_threshold and
                    memory_percent < self.config.memory_threshold
                )
                self.health_status['last_check'] = datetime.now()
                
                # Auto-scaling logic
                if cpu_percent > self.config.scale_up_threshold:
                    self._scale_up()
                elif cpu_percent < self.config.scale_down_threshold:
                    self._scale_down()
                
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _scale_up(self):
        """Scale up resources"""
        logger.info("Scaling up resources due to high load")
        # Implementation would depend on deployment platform
        # For now, just log the action
    
    def _scale_down(self):
        """Scale down resources"""
        logger.info("Scaling down resources due to low load")
        # Implementation would depend on deployment platform
        # For now, just log the action
    
    async def process_async_task(self, task_func: Callable, *args, **kwargs):
        """Process task asynchronously"""
        if not self.config.async_processing:
            return task_func(*args, **kwargs)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, task_func, *args, **kwargs)
    
    def submit_background_task(self, task_func: Callable, *args, **kwargs):
        """Submit task for background processing"""
        return self.executor.submit(task_func, *args, **kwargs)
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self.health_status['healthy']

# =============================================================================
# MAIN PERFORMANCE OPTIMIZER
# =============================================================================

class PerformanceOptimizer:
    """Main performance optimization orchestrator"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.db_optimizer = None
        self.cache_manager = None
        self.frontend_optimizer = None
        self.scalability_manager = None
        self._init_optimizers()
        self._setup_middleware()
    
    def _init_optimizers(self):
        """Initialize all optimization components"""
        # Load configurations
        db_config = DatabaseConfig(
            pool_size=int(self.app.config.get('DB_POOL_SIZE', 20)),
            max_overflow=int(self.app.config.get('DB_MAX_OVERFLOW', 30)),
            read_replica_url=self.app.config.get('READ_REPLICA_URL')
        )
        
        cache_config = CacheConfig(
            redis_url=self.app.config.get('REDIS_URL', 'redis://localhost:6379'),
            default_ttl=int(self.app.config.get('CACHE_DEFAULT_TIMEOUT', 3600))
        )
        
        frontend_config = FrontendConfig(
            bundle_splitting=True,
            lazy_loading=True,
            image_optimization=True
        )
        
        scalability_config = ScalabilityConfig(
            async_processing=True,
            max_workers=int(self.app.config.get('MAX_WORKERS', 20))
        )
        
        # Initialize optimizers
        self.db_optimizer = DatabaseOptimizer(db_config)
        self.cache_manager = CacheManager(cache_config)
        self.frontend_optimizer = FrontendOptimizer(frontend_config)
        self.scalability_manager = ScalabilityManager(scalability_config)
        
        logger.info("Performance optimizers initialized")
    
    def _setup_middleware(self):
        """Setup performance monitoring middleware"""
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(duration)
                
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=response.status_code
                ).inc()
            
            return response
    
    def optimize_assessment_submission(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize assessment submission with caching and async processing"""
        # Cache job risk data
        job_key = f"job_risk:{assessment_data.get('job_title', '')}:{assessment_data.get('industry', '')}"
        cached_risk_data = self.cache_manager.get(job_key)
        
        if cached_risk_data:
            # Use cached data for faster response
            assessment_data['cached_risk_data'] = cached_risk_data
        else:
            # Calculate and cache risk data
            risk_data = self._calculate_job_risk(assessment_data)
            self.cache_manager.set(job_key, risk_data, ttl=7200)  # 2 hours
            assessment_data['calculated_risk_data'] = risk_data
        
        # Submit background tasks for non-critical processing
        if self.scalability_manager.is_healthy():
            self.scalability_manager.submit_background_task(
                self._process_assessment_analytics,
                assessment_data
            )
        
        return assessment_data
    
    def _calculate_job_risk(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate job risk with optimized algorithms"""
        # This would contain the actual risk calculation logic
        # For now, return a placeholder
        return {
            'automation_score': 65,
            'augmentation_score': 75,
            'risk_level': 'medium',
            'confidence': 0.85
        }
    
    def _process_assessment_analytics(self, assessment_data: Dict[str, Any]):
        """Process assessment analytics in background"""
        try:
            # Analytics processing logic
            logger.info("Processing assessment analytics in background")
        except Exception as e:
            logger.error(f"Background analytics processing failed: {e}")
    
    def get_optimized_session(self, engine_type: str = 'main') -> Session:
        """Get optimized database session"""
        return self.db_optimizer.get_session(engine_type)
    
    def get_cached_data(self, key: str, default: Any = None) -> Any:
        """Get data from cache"""
        return self.cache_manager.get(key, default)
    
    def set_cached_data(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set data in cache"""
        return self.cache_manager.set(key, value, ttl)
    
    def optimize_html_response(self, html_content: str) -> str:
        """Optimize HTML response for frontend performance"""
        return self.frontend_optimizer.optimize_html(html_content)

# =============================================================================
# FLASK INTEGRATION
# =============================================================================

def init_performance_optimization(app: Flask) -> PerformanceOptimizer:
    """Initialize performance optimization for Flask app"""
    optimizer = PerformanceOptimizer(app)
    
    # Add metrics endpoint
    @app.route('/metrics')
    def metrics():
        return generate_latest()
    
    # Add health check endpoint
    @app.route('/health')
    def health():
        return {
            'status': 'healthy' if optimizer.scalability_manager.is_healthy() else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'cache_hit_ratio': optimizer.cache_manager._calculate_hit_ratio()
        }
    
    return optimizer
