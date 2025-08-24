# Enhanced Salary Data Service Documentation

## Overview

The Enhanced Salary Data Service provides comprehensive, real-time salary data integration with intelligent caching, data validation, and confidence scoring. This service integrates with multiple external APIs to provide accurate, up-to-date salary information for the Mingus income comparison calculator.

## Architecture

### Core Components

1. **SalaryDataService** - Main service orchestrating data fetching and processing
2. **AsyncAPIClient** - Async HTTP client with rate limiting and retry logic
3. **DataValidator** - Data quality validation and outlier detection
4. **DataRefreshTasks** - Celery background tasks for data maintenance

### Data Flow

```
User Request → SalaryDataService → AsyncAPIClient → External APIs
                ↓
            Redis Cache ← DataValidator ← Response Processing
                ↓
            ComprehensiveSalaryData → User Response
```

## Features

### 🚀 **Async Data Fetching**
- Concurrent API calls to multiple data sources
- Non-blocking I/O operations
- Automatic retry logic with exponential backoff
- Rate limiting to respect API quotas

### 🗄️ **Intelligent Caching**
- Redis-based caching with configurable TTL
- Cache key generation for different data types
- Automatic cache invalidation
- Cache hit/miss monitoring

### ✅ **Data Validation**
- Statistical outlier detection (IQR, Z-score, Modified Z-score)
- Data quality scoring
- Confidence level assessment
- Validation result reporting

### 🔄 **Background Tasks**
- Periodic data refresh
- Cache maintenance
- Data quality monitoring
- Health reporting

### 🛡️ **Error Handling**
- Graceful degradation with fallback data
- API failure isolation
- Comprehensive error logging
- User-friendly error messages

## API Integration

### Supported Data Sources

| Source | API | Rate Limit | Data Type | Cache TTL |
|--------|-----|------------|-----------|-----------|
| BLS | Bureau of Labor Statistics | 10/min, 500/hour | Salary Data | 24 hours |
| Census | US Census Bureau | 20/min, 1000/hour | Demographics | 24 hours |
| FRED | Federal Reserve Economic Data | 15/min, 800/hour | Cost of Living | 24 hours |
| Indeed | Indeed Job Search | 5/min, 100/hour | Job Market | 12 hours |

### Target Locations

The service supports 10 major Metropolitan Statistical Areas (MSAs):

- Atlanta, GA
- Houston, TX
- Washington DC
- Dallas-Fort Worth, TX
- New York City, NY
- Philadelphia, PA
- Chicago, IL
- Charlotte, NC
- Miami, FL
- Baltimore, MD

## Data Structures

### SalaryDataPoint

```python
@dataclass
class SalaryDataPoint:
    source: DataSource
    location: str
    occupation: str
    median_salary: float
    mean_salary: float
    percentile_25: float
    percentile_75: float
    sample_size: int
    year: int
    confidence_score: float
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = None
    cache_key: Optional[str] = None
```

### CostOfLivingDataPoint

```python
@dataclass
class CostOfLivingDataPoint:
    location: str
    overall_cost_index: float
    housing_cost_index: float
    transportation_cost_index: float
    food_cost_index: float
    healthcare_cost_index: float
    utilities_cost_index: float
    year: int
    confidence_score: float
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = None
    cache_key: Optional[str] = None
```

### JobMarketDataPoint

```python
@dataclass
class JobMarketDataPoint:
    location: str
    occupation: str
    job_count: int
    average_salary: float
    salary_range_min: float
    salary_range_max: float
    demand_score: float
    confidence_score: float
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = None
    cache_key: Optional[str] = None
```

### ComprehensiveSalaryData

```python
@dataclass
class ComprehensiveSalaryData:
    location: str
    occupation: str
    salary_data: List[SalaryDataPoint]
    cost_of_living_data: Optional[CostOfLivingDataPoint] = None
    job_market_data: Optional[JobMarketDataPoint] = None
    overall_confidence_score: float = 0.0
    data_quality_score: float = 0.0
    recommendations: List[str] = None
    last_updated: datetime = None
```

## Usage Examples

### Basic Usage

```python
from services.salary_data_service import SalaryDataService

# Initialize service
service = SalaryDataService()

# Get comprehensive salary data
async def get_salary_data():
    comprehensive_data = await service.get_comprehensive_salary_data(
        location='Atlanta',
        occupation='Software Engineer'
    )
    
    print(f"Location: {comprehensive_data.location}")
    print(f"Overall Confidence: {comprehensive_data.overall_confidence_score}")
    print(f"Data Quality: {comprehensive_data.data_quality_score}")
    
    for salary_point in comprehensive_data.salary_data:
        print(f"Source: {salary_point.source}")
        print(f"Median Salary: ${salary_point.median_salary:,}")
        print(f"Confidence: {salary_point.confidence_score}")
```

### Individual API Calls

```python
# Fetch BLS data
bls_data = await service.fetch_bls_salary_data('Atlanta', 'Software Engineer')

# Fetch Census data
census_data = await service.fetch_census_salary_data('Atlanta')

# Fetch cost of living data
col_data = await service.fetch_fred_cost_of_living_data('Atlanta')

# Fetch job market data
job_data = await service.fetch_indeed_job_market_data('Atlanta', 'Software Engineer')
```

### Cache Management

```python
# Get cache status
cache_status = service.get_cache_status()
print(f"Cache Status: {cache_status['status']}")
print(f"Memory Usage: {cache_status['used_memory_human']}")

# Clear cache
success = service.clear_cache('salary_data:bls:*')
print(f"Cache cleared: {success}")
```

## API Endpoints

### Enhanced Income Comparison API

#### POST `/api/income-comparison/comprehensive`

Comprehensive income analysis with real-time data integration.

**Request Body:**
```json
{
    "current_salary": 75000,
    "location": "Atlanta",
    "education_level": "bachelors",
    "occupation": "Software Engineer",
    "include_real_time_data": true
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "income_comparison": {
            "demographic_analysis": {...},
            "real_time_insights": {
                "available": true,
                "data_quality": 0.85,
                "confidence": 0.90,
                "salary_comparison": {
                    "real_time_median": 72000,
                    "salary_ratio": 1.04,
                    "percentile_estimate": "50th_to_75th",
                    "market_position": "at_market"
                },
                "cost_of_living_impact": {
                    "overall_cost_index": 110.0,
                    "cost_adjusted_salary": 68182,
                    "relative_affordability": "moderately_affordable"
                },
                "job_market_insights": {
                    "job_count": 150,
                    "demand_score": 85.0,
                    "market_competitiveness": "high_demand_competitive_salary"
                }
            }
        },
        "real_time_data": {...},
        "analysis_metadata": {...}
    }
}
```

#### POST `/api/income-comparison/real-time-data`

Get real-time salary data for a location and occupation.

**Request Body:**
```json
{
    "location": "Atlanta",
    "occupation": "Software Engineer"
}
```

#### GET `/api/income-comparison/health`

Health check endpoint.

#### GET `/api/income-comparison/cache/status`

Get cache status and statistics.

#### POST `/api/income-comparison/cache/clear`

Clear cache entries.

## Background Tasks

### Data Refresh Tasks

The service includes Celery background tasks for data maintenance:

```python
from tasks.data_refresh_tasks import DataRefreshTasks

tasks = DataRefreshTasks()

# Refresh all salary data
refresh_summary = tasks.refresh_all_salary_data()

# Refresh specific location
location_summary = tasks.refresh_location_data('Atlanta', 'Software Engineer')

# Validate cached data
validation_summary = tasks.validate_cached_data()

# Clean up expired cache
cleanup_summary = tasks.cleanup_expired_cache(max_age_hours=24)

# Monitor data quality
health_report = tasks.monitor_data_quality()

# Generate data report
data_report = tasks.generate_data_report()
```

### Task Scheduling

Configure Celery beat schedule for automatic data refresh:

```python
# celery.py
CELERY_BEAT_SCHEDULE = {
    'refresh-salary-data': {
        'task': 'tasks.data_refresh_tasks.refresh_all_salary_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'validate-cached-data': {
        'task': 'tasks.data_refresh_tasks.validate_cached_data',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'cleanup-expired-cache': {
        'task': 'tasks.data_refresh_tasks.cleanup_expired_cache',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'monitor-data-quality': {
        'task': 'tasks.data_refresh_tasks.monitor_data_quality',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    }
}
```

## Configuration

### Environment Variables

```bash
# API Keys
BLS_API_KEY=your_bls_api_key
CENSUS_API_KEY=your_census_api_key
FRED_API_KEY=your_fred_api_key
INDEED_API_KEY=your_indeed_api_key

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# Service Configuration
SALARY_DATA_CACHE_TTL=86400  # 24 hours
SALARY_DATA_JOB_MARKET_TTL=43200  # 12 hours
SALARY_DATA_MAX_RETRIES=3
SALARY_DATA_RETRY_DELAY=1
```

### Validation Thresholds

```python
# Data validation thresholds
VALIDATION_THRESHOLDS = {
    'min_salary': 20000,
    'max_salary': 500000,
    'min_sample_size': 10,
    'max_age_days': 365,
    'min_confidence': 0.5,
    'outlier_threshold': 2.0
}
```

## Data Validation

### Validation Levels

- **HIGH** (0.8-1.0): Excellent data quality, high confidence
- **MEDIUM** (0.6-0.8): Good data quality, moderate confidence
- **LOW** (0.4-0.6): Fair data quality, low confidence
- **INVALID** (0.0-0.4): Poor data quality, unreliable

### Outlier Detection Methods

1. **IQR Method**: Uses interquartile range to detect outliers
2. **Z-Score Method**: Uses standard deviations from mean
3. **Modified Z-Score Method**: Uses median absolute deviation

### Validation Checks

- Required field presence
- Salary range validation
- Sample size validation
- Data age validation
- Logical consistency checks
- Outlier detection

## Performance Optimization

### Caching Strategy

- **Salary Data**: 24-hour TTL
- **Job Market Data**: 12-hour TTL
- **Cost of Living Data**: 24-hour TTL
- **Cache Key Pattern**: `salary_data:{type}:{location}:{occupation}`

### Rate Limiting

- **BLS**: 10 requests/minute, 500/hour
- **Census**: 20 requests/minute, 1000/hour
- **FRED**: 15 requests/minute, 800/hour
- **Indeed**: 5 requests/minute, 100/hour

### Async Processing

- Concurrent API calls
- Non-blocking I/O
- Connection pooling
- Automatic retry with exponential backoff

## Monitoring and Health Checks

### Health Check Endpoint

```bash
GET /api/income-comparison/health
```

**Response:**
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "service": "enhanced_income_comparison",
        "available_locations": [...],
        "real_time_integration": {
            "status": "available",
            "apis": ["BLS", "Census", "FRED", "Indeed"],
            "api_health": {
                "bls_configured": true,
                "census_configured": true,
                "fred_configured": true,
                "indeed_configured": true
            },
            "cache_status": "available"
        }
    }
}
```

### Data Quality Metrics

- Cache hit rate
- API response times
- Data freshness
- Validation success rate
- Error rates by API

## Error Handling

### Fallback Strategy

1. **Primary**: Real-time API data
2. **Secondary**: Cached data
3. **Tertiary**: Static fallback data
4. **Final**: Error response with explanation

### Error Types

- **API Errors**: Network issues, rate limits, invalid responses
- **Validation Errors**: Data quality issues, outliers
- **Cache Errors**: Redis connection issues
- **Processing Errors**: Data parsing issues

### Error Response Format

```json
{
    "success": false,
    "error": "Error description",
    "fallback_used": true,
    "data_quality": "low",
    "recommendations": ["Consider using cached data", "Check API status"]
}
```

## Testing

### Test Coverage

- Unit tests for all service methods
- Integration tests for API calls
- Async testing with mocked responses
- Cache testing with Redis mocks
- Validation testing with various data scenarios

### Running Tests

```bash
# Run all tests
python -m pytest tests/test_enhanced_salary_data_service.py -v

# Run specific test class
python -m pytest tests/test_enhanced_salary_data_service.py::TestSalaryDataService -v

# Run with coverage
python -m pytest tests/test_enhanced_salary_data_service.py --cov=services.salary_data_service --cov-report=html
```

### Test Categories

1. **Service Tests**: Core functionality testing
2. **API Client Tests**: HTTP client and rate limiting
3. **Validation Tests**: Data quality and outlier detection
4. **Cache Tests**: Redis operations and TTL
5. **Integration Tests**: End-to-end workflows
6. **Async Tests**: Concurrent operations

## Deployment

### Requirements

- Python 3.8+
- Redis 6.0+
- Celery 5.0+
- aiohttp 3.8+
- numpy 1.20+

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp env.example .env
# Edit .env with your API keys

# Start Redis
redis-server

# Start Celery worker
celery -A backend.celery worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A backend.celery beat --loglevel=info
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
      - celery-worker
      - celery-beat
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
  
  celery-worker:
    build: .
    command: celery -A backend.celery worker --loglevel=info
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
  
  celery-beat:
    build: .
    command: celery -A backend.celery beat --loglevel=info
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
```

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   - Check Redis server status
   - Verify connection parameters
   - Check firewall settings

2. **API Rate Limiting**
   - Monitor rate limit headers
   - Implement exponential backoff
   - Consider API key rotation

3. **Data Quality Issues**
   - Check validation results
   - Review outlier detection
   - Verify data freshness

4. **Async Operation Errors**
   - Check event loop configuration
   - Verify async/await usage
   - Monitor concurrent connections

### Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Check service status
service = SalaryDataService()
cache_status = service.get_cache_status()
print(f"Cache Status: {cache_status}")

# Test API connectivity
async def test_apis():
    async with AsyncAPIClient() as client:
        health_status = await client.health_check()
        print(f"API Health: {health_status}")
```

## Future Enhancements

### Planned Features

1. **Additional Data Sources**
   - Glassdoor API integration
   - LinkedIn Salary data
   - Local government data sources

2. **Advanced Analytics**
   - Salary trend analysis
   - Predictive modeling
   - Market forecasting

3. **Enhanced Validation**
   - Machine learning-based outlier detection
   - Cross-source data validation
   - Real-time quality monitoring

4. **Performance Improvements**
   - GraphQL API support
   - WebSocket real-time updates
   - CDN integration for static data

### API Extensions

- GraphQL endpoint for flexible queries
- Webhook support for data updates
- Real-time streaming API
- Bulk data export endpoints

## Support

For technical support or questions about the Enhanced Salary Data Service:

- **Documentation**: See this document and inline code comments
- **Issues**: Create GitHub issues for bugs or feature requests
- **Testing**: Run the comprehensive test suite
- **Monitoring**: Use health check endpoints and logging

---

*This documentation covers the Enhanced Salary Data Service v2.0 with async data fetching, intelligent caching, and comprehensive validation.* 