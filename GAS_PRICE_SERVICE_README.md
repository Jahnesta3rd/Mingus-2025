# Mingus Gas Price Service

A comprehensive gas price management service for the Mingus application that provides location-based gas pricing with MSA mapping integration and fallback to national average pricing.

## 🚀 Features

### Core Functionality
- **MSA-Based Pricing**: Fetches current gas prices for 10 target MSAs
- **75-Mile Radius Logic**: Uses zipcode-to-MSA mapping service for location-based pricing
- **National Average Fallback**: Provides fallback pricing when users are outside MSA coverage
- **Daily Updates**: Automated daily price updates using Celery background tasks
- **Multiple Data Sources**: Supports GasBuddy API, EIA API, and fallback pricing
- **Error Handling**: Comprehensive error handling and logging
- **Data Quality Tracking**: Confidence scores and data source tracking

### Target MSAs
The service tracks gas prices for these 10 major metropolitan areas:
1. **Atlanta** - Pricing Multiplier: 0.95
2. **Houston** - Pricing Multiplier: 0.92
3. **Washington DC** - Pricing Multiplier: 1.15
4. **Dallas** - Pricing Multiplier: 0.98
5. **New York** - Pricing Multiplier: 1.25
6. **Philadelphia** - Pricing Multiplier: 1.05
7. **Chicago** - Pricing Multiplier: 1.08
8. **Charlotte** - Pricing Multiplier: 0.88
9. **Miami** - Pricing Multiplier: 1.12
10. **Baltimore** - Pricing Multiplier: 1.02

## 📁 File Structure

```
backend/
├── services/
│   └── gas_price_service.py          # Main gas price service
├── tasks/
│   └── gas_price_tasks.py            # Celery background tasks
├── api/
│   └── gas_price_endpoints.py        # REST API endpoints
├── config/
│   └── celery_beat_schedule.py       # Periodic task scheduling
└── models/
    └── vehicle_models.py             # Updated MSAGasPrice model
```

## 🏗️ Architecture

### Service Components

```
GasPriceService
├── MSA Mapping Integration
│   └── ZipcodeToMSAMapper (75-mile radius)
├── Data Sources
│   ├── GasBuddy API (Primary)
│   ├── EIA API (Secondary)
│   └── Fallback Pricing (Tertiary)
├── Database Operations
│   └── MSAGasPrice Model
└── Error Handling & Logging
```

### Celery Tasks

```
Gas Price Tasks
├── update_daily_gas_prices()         # Daily price updates
├── update_specific_msa_price()       # Single MSA updates
├── cleanup_old_gas_price_data()      # Data cleanup
├── health_check_gas_price_service()  # Health monitoring
└── get_gas_price_by_zipcode_task()   # Async zipcode lookups
```

## 🔧 Setup and Configuration

### 1. Environment Variables

Add these environment variables to your `.env` file:

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Gas Price API Keys (Optional)
GASBUDDY_API_KEY=your_gasbuddy_api_key_here
EIA_API_KEY=your_eia_api_key_here
```

### 2. Database Migration

The service uses the existing `MSAGasPrice` model with enhanced fields:

```python
# New fields added to MSAGasPrice model
previous_price = db.Column(db.Numeric(5, 3), nullable=True)
price_change = db.Column(db.Numeric(5, 3), nullable=True)
data_source = db.Column(db.String(50), nullable=True)
confidence_score = db.Column(db.Float, nullable=True)
created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
```

### 3. Celery Worker Setup

Start Celery worker for gas price tasks:

```bash
# Start Celery worker
celery -A backend.tasks.gas_price_tasks worker --loglevel=info --queues=gas_price_queue

# Start Celery Beat for scheduled tasks
celery -A backend.tasks.gas_price_tasks beat --loglevel=info
```

## 📚 API Endpoints

### Gas Price Retrieval

#### Get Gas Price by Zipcode
```http
GET /api/gas-prices/zipcode/{zipcode}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "zipcode": "10001",
    "msa_name": "New York",
    "distance_to_msa": 0.0,
    "gas_price": 4.20,
    "price_change": 0.05,
    "data_source": "GasBuddy API",
    "confidence_score": 0.9,
    "last_updated": "2024-01-15T06:00:00Z",
    "is_fallback": false
  }
}
```

#### Get Gas Price by MSA
```http
GET /api/gas-prices/msa/{msa_name}
```

#### Get All Gas Prices
```http
GET /api/gas-prices/all
```

### Gas Price Updates

#### Trigger Daily Update
```http
POST /api/gas-prices/update
Content-Type: application/json

{
  "force_update": false
}
```

#### Update Specific MSA
```http
POST /api/gas-prices/msa/{msa_name}/update
Content-Type: application/json

{
  "price": 3.45,
  "data_source": "Manual"
}
```

### Status and Monitoring

#### Get Service Status
```http
GET /api/gas-prices/status
```

#### Trigger Health Check
```http
POST /api/gas-prices/health-check
```

#### Get Task Status
```http
GET /api/gas-prices/task/{task_id}/status
```

### Price History

#### Get Price History
```http
GET /api/gas-prices/history/{msa_name}?days=30
```

### Utility Endpoints

#### Get MSA List
```http
GET /api/gas-prices/msa-list
```

#### Get Fallback Prices
```http
GET /api/gas-prices/fallback-prices
```

## 🔄 Usage Examples

### Python Service Usage

```python
from backend.services.gas_price_service import GasPriceService

# Initialize service
gas_service = GasPriceService()

# Get gas price by zipcode
result = gas_service.get_gas_price_by_zipcode("10001")
print(f"Gas price in 10001: ${result['gas_price']}")

# Update all gas prices
update_results = gas_service.update_all_gas_prices()
print(f"Updated {update_results['total_updated']} MSAs")

# Get service status
status = gas_service.get_service_status()
print(f"Service status: {status['service_status']}")
```

### Celery Task Usage

```python
from backend.tasks.gas_price_tasks import update_daily_gas_prices, get_gas_price_by_zipcode_task

# Trigger daily update
task = update_daily_gas_prices.delay(force_update=False)
print(f"Task ID: {task.id}")

# Get gas price asynchronously
task = get_gas_price_by_zipcode_task.delay("10001")
result = task.get()  # Wait for result
```

## 📊 Data Sources

### Primary Sources
1. **GasBuddy API** - Real-time gas prices (confidence: 0.9)
2. **EIA API** - Government energy data (confidence: 0.85)

### Fallback Pricing
When external APIs are unavailable, the service uses fallback prices:

```python
FALLBACK_PRICES = {
    'National Average': 3.50,
    'Atlanta': 3.20,
    'Houston': 3.10,
    'Washington DC': 3.80,
    'Dallas': 3.15,
    'New York': 4.20,
    'Philadelphia': 3.60,
    'Chicago': 3.70,
    'Charlotte': 3.05,
    'Miami': 3.45,
    'Baltimore': 3.55
}
```

## ⏰ Scheduled Tasks

### Daily Schedule
- **6:00 AM UTC**: Daily gas price update
- **Every 2 hours**: Health check
- **Every 30 minutes**: Task monitoring
- **Sunday 2:00 AM UTC**: Data cleanup (keeps 30 days)

### Task Priorities
1. **Priority 5**: Daily updates
2. **Priority 3**: Health checks
3. **Priority 2**: Data cleanup
4. **Priority 1**: Task monitoring

## 🛡️ Error Handling

### Service-Level Errors
- **API Failures**: Automatic fallback to next data source
- **Database Errors**: Rollback and retry logic
- **Invalid Zipcodes**: Fallback to national average
- **Network Timeouts**: Exponential backoff retry

### Task-Level Errors
- **Retry Logic**: Up to 3 retries with exponential backoff
- **Dead Letter Queue**: Failed tasks after max retries
- **Health Monitoring**: Automatic alerting for service issues

## 📈 Monitoring and Logging

### Health Metrics
- Service status (healthy/error)
- Data freshness (good/stale)
- Update success rates
- Task completion rates

### Logging Levels
- **INFO**: Normal operations and updates
- **WARNING**: Fallback usage and retries
- **ERROR**: Service failures and exceptions
- **DEBUG**: Detailed operation tracing

## 🔧 Configuration Options

### Service Configuration
```python
# Data source priorities
DATA_SOURCES = {
    'gasbuddy_api': {'confidence': 0.9},
    'eia_api': {'confidence': 0.85},
    'fallback': {'confidence': 0.5}
}

# Update intervals
DAILY_UPDATE_HOUR = 6  # UTC
HEALTH_CHECK_INTERVAL = 2  # hours
CLEANUP_DAYS_TO_KEEP = 30
```

### Celery Configuration
```python
# Task settings
task_time_limit = 300  # 5 minutes
task_soft_time_limit = 240  # 4 minutes
max_retries = 3
default_retry_delay = 300  # 5 minutes
```

## 🚀 Deployment

### Production Setup
1. **Redis**: Configure Redis for Celery broker and result backend
2. **Workers**: Deploy multiple Celery workers for high availability
3. **Beat Scheduler**: Run Celery Beat on a single instance
4. **Monitoring**: Set up health checks and alerting
5. **API Keys**: Configure external API keys for data sources

### Docker Support
```yaml
# docker-compose.yml
services:
  celery-worker:
    build: .
    command: celery -A backend.tasks.gas_price_tasks worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - redis
      - postgres
```

## 🧪 Testing

### Unit Tests
```python
# Test service functionality
def test_get_gas_price_by_zipcode():
    service = GasPriceService()
    result = service.get_gas_price_by_zipcode("10001")
    assert result['success'] == True
    assert 'gas_price' in result
```

### Integration Tests
```python
# Test API endpoints
def test_gas_price_api():
    response = client.get('/api/gas-prices/zipcode/10001')
    assert response.status_code == 200
    assert response.json['success'] == True
```

## 📝 Changelog

### Version 1.0.0
- Initial implementation
- MSA-based gas pricing
- Zipcode-to-MSA mapping integration
- Celery background tasks
- REST API endpoints
- Fallback pricing system
- Comprehensive error handling

## 🤝 Contributing

1. Follow existing code style and patterns
2. Add comprehensive error handling
3. Include logging for all operations
4. Write unit tests for new features
5. Update documentation for API changes

## 📞 Support

For issues or questions:
1. Check the logs for error details
2. Verify service status endpoint
3. Check Celery task status
4. Review database connectivity
5. Contact the development team
