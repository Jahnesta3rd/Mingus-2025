# Comprehensive Rate Limiting System for Financial Application

This system provides advanced rate limiting with Redis support, multiple strategies, and cultural sensitivity for African American professionals. It protects against brute force attacks, API abuse, and ensures fair resource usage.

## Features

- **Multiple Rate Limiting Strategies**: Per-user, per-IP, and per-endpoint specific limits
- **Redis-Based**: High-performance Redis backend with memory fallback
- **Sliding Window Algorithm**: More accurate rate limiting than fixed windows
- **Cultural Sensitivity**: Culturally appropriate error messages for African American professionals
- **Admin Bypass**: Whitelisted IPs and admin users bypass rate limiting
- **Comprehensive Monitoring**: Real-time alerts, metrics, and suspicious activity detection
- **Flexible Decorators**: Easy-to-use decorators for different use cases
- **Environment-Specific**: Different limits for development, testing, and production

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask Routes  │───▶│ Rate Limiting    │───▶│   Redis Store   │
│                 │    │   Decorators     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Rate Limiting    │
                       │   Core Logic     │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Monitoring &   │
                       │    Alerting      │
                       └──────────────────┘
```

## Quick Start

### 1. Basic Usage

```python
from backend.middleware.rate_limit_decorators import rate_limit

@app.route('/api/data')
@rate_limit('financial_api')
def get_financial_data():
    return {'data': 'financial information'}

@app.route('/api/auth/login', methods=['POST'])
@rate_limit_auth('login')
def login():
    return {'message': 'Login successful'}
```

### 2. User-Based Rate Limiting

```python
from backend.middleware.rate_limit_decorators import rate_limit_by_user

@app.route('/api/user/profile')
@rate_limit_by_user('api_general')
def get_user_profile():
    return {'profile': 'user data'}
```

### 3. IP-Based Rate Limiting

```python
from backend.middleware.rate_limit_decorators import rate_limit_by_ip

@app.route('/api/public/data')
@rate_limit_by_ip('api_general')
def get_public_data():
    return {'data': 'public information'}
```

## Rate Limit Types

### Authentication Endpoints
- **login**: 5 attempts per 15 minutes
- **register**: 5 attempts per 15 minutes  
- **password_reset**: 3 attempts per hour

### Financial Data Endpoints
- **financial_api**: 100 requests per minute per user
- **financial_hourly**: 1000 requests per hour per user

### Payment Endpoints
- **payment**: 10 requests per hour per user
- **stripe_webhook**: 200 requests per hour per IP

### General API Endpoints
- **api_general**: 1000 requests per hour per IP
- **api_per_minute**: 100 requests per minute per IP

### Assessment Endpoints
- **assessment_submit**: 3 submissions per 5 minutes
- **assessment_view**: 20 views per 5 minutes

## Decorators Reference

### Main Decorators

```python
# General rate limiting
@rate_limit('endpoint_type', custom_limits={'requests': 50, 'window': 300})

# User-based rate limiting (requires authentication)
@rate_limit_by_user('endpoint_type', custom_limits={'requests': 100, 'window': 3600})

# IP-based rate limiting
@rate_limit_by_ip('endpoint_type', custom_limits={'requests': 200, 'window': 3600})
```

### Specialized Decorators

```python
# Financial endpoints
@rate_limit_financial('financial_api')

# Payment endpoints
@rate_limit_payment('payment')

# Authentication endpoints
@rate_limit_auth('login')

# Assessment endpoints
@rate_limit_assessment('assessment_submit')

# Webhook endpoints
@rate_limit_webhook('stripe_webhook')
```

### Convenience Decorators

```python
# Pre-configured for common use cases
@login_rate_limit
@register_rate_limit
@password_reset_rate_limit
@financial_rate_limit
@payment_rate_limit
@assessment_submit_rate_limit
@assessment_view_rate_limit
@webhook_rate_limit
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Admin and Whitelisted IPs
ADMIN_IPS=192.168.1.100,10.0.0.50
WHITELISTED_IPS=203.0.113.0/24,198.51.100.0/24

# Rate Limiting Configuration
RATE_LIMIT_EXTERNAL_ALERTS=true
RATE_LIMIT_ALERT_CHANNELS=email,slack,webhook
```

### Custom Rate Limits

```python
from backend.config.rate_limits import RateLimitConfig

# Create custom configuration
custom_limits = RateLimitConfig(
    requests=25,
    window=1800,  # 30 minutes
    message="Custom rate limit message",
    cultural_message="We're processing your requests. Please wait before your next attempt.",
    priority="high"
)

# Apply to endpoint
@app.route('/api/custom')
@rate_limit('custom_endpoint', custom_limits)
def custom_endpoint():
    return {'message': 'Custom endpoint'}
```

## Integration with Existing Routes

### 1. Apply to Individual Routes

```python
from backend.middleware.rate_limit_integration import apply_rate_limiting_to_existing_route

# Existing route function
def existing_route():
    return {'data': 'existing logic'}

# Apply rate limiting
protected_route = apply_rate_limiting_to_existing_route(existing_route, 'financial_api')
```

### 2. Apply to Blueprints

```python
from backend.middleware.rate_limit_integration import integrate_with_existing_blueprint

# Configuration for blueprint routes
route_config = {
    'user_profile': 'api_general',
    'update_profile': 'api_general',
    'delete_account': 'critical_operation'
}

# Apply to blueprint
integrate_with_existing_blueprint(user_blueprint, route_config)
```

### 3. Full Application Integration

```python
from backend.middleware.rate_limit_integration import create_rate_limit_middleware

# In your Flask app factory
def create_app():
    app = Flask(__name__)
    
    # ... other initialization ...
    
    # Integrate rate limiting
    create_rate_limit_middleware(app)
    
    return app
```

## Monitoring and Alerting

### 1. View Metrics

```python
from backend.monitoring.rate_limit_monitoring import get_rate_limit_monitor

monitor = get_rate_limit_monitor()
metrics = monitor.get_metrics()
alerts = monitor.get_alerts(hours=24)
events = monitor.get_events(hours=24)
```

### 2. Custom Alerting

```python
# Configure external alerting
app.config['RATE_LIMIT_EXTERNAL_ALERTS'] = True
app.config['RATE_LIMIT_ALERT_CHANNELS'] = ['email', 'slack', 'webhook']

# Custom alert thresholds
monitor.thresholds = {
    'warning': 0.6,      # 60% of limit
    'alert': 0.8,        # 80% of limit
    'critical': 0.95     # 95% of limit
}
```

### 3. Suspicious Activity Detection

The system automatically detects:
- **Rapid Requests**: 10+ requests in 1 minute
- **Multiple Endpoints**: 5+ different endpoints in 5 minutes
- **Failed Authentication**: 3+ failed auth attempts in 5 minutes

## Cultural Sensitivity

### Error Messages

The system provides culturally appropriate error messages:

```python
# Standard message
"Too many login attempts. Please wait before trying again."

# Cultural message
"We understand the importance of secure access to your financial information. Please take a moment before your next attempt."
```

### Cultural Context

The system automatically detects cultural context:
- African American focused applications
- Financial professional users
- Mobile users
- Preferred language settings

## Testing

### Run Unit Tests

```bash
# Run all rate limiting tests
pytest backend/tests/test_rate_limiting.py -v

# Run specific test class
pytest backend/tests/test_rate_limiting.py::TestComprehensiveRateLimiter -v

# Run with coverage
pytest backend/tests/test_rate_limiting.py --cov=backend.middleware.rate_limiter --cov-report=html
```

### Test Rate Limiting

```python
import time
import requests

# Test rate limiting
base_url = 'http://localhost:5000'

# Make multiple requests to trigger rate limiting
for i in range(10):
    response = requests.post(f'{base_url}/api/auth/login', json={'email': 'test@example.com'})
    print(f'Request {i+1}: {response.status_code}')
    
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')
        print(f'Rate limited. Retry after {retry_after} seconds')
        break
    
    time.sleep(0.1)  # Small delay between requests
```

## Performance Considerations

### Redis Configuration

```python
# Optimize Redis for rate limiting
redis_config = {
    'max_connections': 20,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True
}

# Use connection pooling
from redis import ConnectionPool
pool = ConnectionPool.from_url('redis://localhost:6379/0', **redis_config)
redis_client = redis.Redis(connection_pool=pool)
```

### Memory Fallback

When Redis is unavailable, the system automatically falls back to in-memory storage:

```python
# Memory fallback is automatic
limiter = ComprehensiveRateLimiter(None)  # No Redis client
result = limiter.is_rate_limited('user:123', 'login')
```

## Security Features

### 1. IP Address Detection

The system handles various proxy configurations:
- `X-Forwarded-For` header
- `X-Real-IP` header
- Direct connection IP

### 2. Admin Bypass

```python
# Admin IPs bypass all rate limiting
ADMIN_IPS=192.168.1.100,10.0.0.50

# Whitelisted IPs bypass rate limiting
WHITELISTED_IPS=203.0.113.0/24,198.51.100.0/24
```

### 3. Rate Limit Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check Redis server status
   - Verify connection URL
   - System falls back to memory storage

2. **Rate Limiting Not Working**
   - Check decorator placement
   - Verify endpoint type configuration
   - Check Redis connectivity

3. **False Positives**
   - Adjust rate limit thresholds
   - Check for proxy configuration issues
   - Verify IP address detection

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('backend.middleware.rate_limiter').setLevel(logging.DEBUG)

# Check rate limiter status
limiter = get_rate_limiter()
print(f"Redis client: {limiter.redis_client is not None}")
print(f"Strategy: {limiter.strategy is not None}")
```

## Best Practices

### 1. Rate Limit Design

- **Authentication**: Strict limits (5 attempts per 15 minutes)
- **Financial Data**: Moderate limits (100 per minute)
- **Payment Operations**: Conservative limits (10 per hour)
- **General API**: Liberal limits (1000 per hour)

### 2. Error Handling

```python
@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Please wait before trying again',
        'retry_after': request.headers.get('Retry-After', 60)
    }), 429
```

### 3. Monitoring

- Set up alerts for 80% threshold
- Monitor suspicious activity patterns
- Track rate limit violations
- Use metrics for capacity planning

## Migration Guide

### From Existing Rate Limiting

1. **Replace old decorators**:
   ```python
   # Old
   @rate_limit('action', 10, 300)
   
   # New
   @rate_limit('api_general')
   ```

2. **Update configuration**:
   ```python
   # Old config
   RATE_LIMITS = {'login': {'max': 5, 'window': 900}}
   
   # New config (automatic)
   # Uses built-in configuration
   ```

3. **Add monitoring**:
   ```python
   # Enable monitoring
   app.config['RATE_LIMIT_EXTERNAL_ALERTS'] = True
   ```

## Support

For issues and questions:

1. Check the test files for examples
2. Review the configuration options
3. Enable debug logging
4. Check Redis connectivity
5. Verify decorator placement

## License

This rate limiting system is part of the MINGUS Financial Application and follows the same licensing terms.
