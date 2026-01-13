# VIN Lookup Service for Mingus Flask Application

A comprehensive VIN (Vehicle Identification Number) lookup service that integrates with the free NHTSA VIN decoder API to retrieve detailed vehicle information.

## Features

- **NHTSA API Integration**: Uses the free NHTSA VIN decoder API (https://vpic.nhtsa.dot.gov/api/)
- **Error Handling & Timeout Management**: Robust error handling with configurable timeouts and retry logic
- **Fallback Mechanism**: Graceful degradation when the API is unavailable
- **Standardized Vehicle Information**: Returns consistent vehicle data structure
- **Comprehensive Logging**: Full logging integration with Mingus logging setup
- **Caching**: Built-in caching to improve performance and reduce API calls
- **Service Management**: Health checks, status monitoring, and cache management
- **RESTful API Endpoints**: Complete API integration with the Mingus Flask application

## Installation

The VIN lookup service is already integrated into the Mingus Flask application. No additional installation is required.

## Usage

### Service Class Usage

```python
from backend.services.vin_lookup_service import VINLookupService, VINValidationError, VINAPIError

# Initialize the service
vin_service = VINLookupService()

# Lookup a VIN
try:
    vehicle_info = vin_service.lookup_vin("1HGBH41JXMN109186")
    
    print(f"Make: {vehicle_info.make}")
    print(f"Model: {vehicle_info.model}")
    print(f"Year: {vehicle_info.year}")
    print(f"Engine: {vehicle_info.engine}")
    print(f"Fuel Type: {vehicle_info.fuel_type}")
    
except VINValidationError as e:
    print(f"Invalid VIN: {e}")
except VINAPIError as e:
    print(f"API Error: {e}")
```

### API Endpoints

#### 1. VIN Lookup
**POST** `/api/vehicles/vin-lookup`

Lookup vehicle information by VIN.

**Request Body:**
```json
{
    "vin": "1HGBH41JXMN109186",
    "use_cache": true
}
```

**Response:**
```json
{
    "success": true,
    "vehicle_info": {
        "vin": "1HGBH41JXMN109186",
        "year": 2021,
        "make": "HONDA",
        "model": "CIVIC",
        "trim": "LX",
        "engine": "In-Line",
        "fuel_type": "Gasoline",
        "body_class": "Sedan/Saloon",
        "drive_type": "FWD",
        "transmission": "Manual",
        "doors": 4,
        "windows": 4,
        "series": "Civic",
        "plant_city": "GREENSBURG",
        "plant_state": "INDIANA",
        "plant_country": "UNITED STATES (USA)",
        "manufacturer": "AMERICAN HONDA MOTOR CO., INC.",
        "vehicle_type": "PASSENGER CAR",
        "source": "nhtsa",
        "lookup_timestamp": "2025-01-17T20:25:03.831578",
        "error_code": null,
        "error_text": null
    },
    "message": "VIN lookup completed successfully"
}
```

#### 2. VIN Validation
**POST** `/api/vehicles/vin-lookup/validate`

Validate VIN format.

**Request Body:**
```json
{
    "vin": "1HGBH41JXMN109186"
}
```

**Response:**
```json
{
    "success": true,
    "vin": "1HGBH41JXMN109186",
    "is_valid": true,
    "message": "VIN validation completed"
}
```

#### 3. Service Status
**GET** `/api/vehicles/vin-lookup/status`

Get VIN lookup service status and statistics.

**Response:**
```json
{
    "success": true,
    "service_status": {
        "status": "available",
        "error_count": 0,
        "last_error_time": null,
        "cache_size": 5,
        "cache_ttl": 3600,
        "timeout": 10,
        "max_retries": 3
    },
    "message": "VIN service status retrieved successfully"
}
```

#### 4. Health Check
**GET** `/api/vehicles/vin-lookup/health`

Perform health check on VIN lookup service.

**Response:**
```json
{
    "success": true,
    "health_check": {
        "status": "healthy",
        "service_available": true,
        "last_check": "2025-01-17T20:25:06.329704",
        "test_lookup_successful": true
    },
    "message": "VIN service health check completed"
}
```

#### 5. Clear Cache
**POST** `/api/vehicles/vin-lookup/cache/clear`

Clear VIN lookup cache.

**Response:**
```json
{
    "success": true,
    "message": "VIN lookup cache cleared successfully"
}
```

## Configuration

The VIN lookup service can be configured with the following parameters:

```python
vin_service = VINLookupService(
    timeout=10,        # Request timeout in seconds
    max_retries=3,     # Maximum number of retry attempts
    cache_ttl=3600     # Cache time-to-live in seconds
)
```

## Error Handling

The service provides comprehensive error handling:

### VINValidationError
Raised when the VIN format is invalid.

```python
try:
    vehicle_info = vin_service.lookup_vin("INVALID_VIN")
except VINValidationError as e:
    print(f"Invalid VIN: {e}")
```

### VINAPIError
Raised when there's an API-related error.

```python
try:
    vehicle_info = vin_service.lookup_vin("1HGBH41JXMN109186")
except VINAPIError as e:
    print(f"API Error: {e}")
```

### VINLookupError
Base exception for all VIN lookup errors.

## Fallback Mechanism

When the NHTSA API is unavailable, the service automatically falls back to providing basic vehicle information:

```python
vehicle_info = vin_service.lookup_vin("1HGBH41JXMN109186")
if vehicle_info.source == "fallback":
    print("Using fallback data - API unavailable")
    print(f"Error: {vehicle_info.error_text}")
```

## Caching

The service includes built-in caching to improve performance:

- **Cache TTL**: 1 hour by default (configurable)
- **Automatic Cache Management**: Expired entries are automatically removed
- **Cache Control**: Can be disabled per request or cleared entirely

```python
# Disable caching for a specific request
vehicle_info = vin_service.lookup_vin("1HGBH41JXMN109186", use_cache=False)

# Clear entire cache
vin_service.clear_cache()
```

## Logging

The service integrates with the Mingus logging system:

```python
import logging
logger = logging.getLogger(__name__)

# Service logs all operations
logger.info("VIN lookup successful")
logger.warning("API returned error")
logger.error("VIN service error")
```

## Testing

Run the test suite to verify functionality:

```bash
python test_vin_lookup.py
```

Run the example to see usage patterns:

```bash
python vin_lookup_example.py
```

## Service Management

### Service Status
Monitor the service status and performance:

```python
status = vin_service.get_service_status()
print(f"Service Status: {status['status']}")
print(f"Error Count: {status['error_count']}")
print(f"Cache Size: {status['cache_size']}")
```

### Health Check
Perform health checks:

```python
health = vin_service.health_check()
print(f"Service Healthy: {health['status'] == 'healthy'}")
print(f"API Available: {health['service_available']}")
```

## API Rate Limits

The NHTSA VIN decoder API is free but has rate limits:

- **No API Key Required**: Free to use
- **Rate Limits**: Reasonable usage limits apply
- **Retry Logic**: Built-in retry with exponential backoff
- **Error Handling**: Graceful handling of rate limit errors

## Supported Vehicle Information

The service returns standardized vehicle information including:

- **Basic Info**: Year, Make, Model, Trim
- **Technical Specs**: Engine, Fuel Type, Transmission, Drive Type
- **Body Details**: Body Class, Doors, Windows, Series
- **Manufacturing**: Plant City, State, Country, Manufacturer
- **Classification**: Vehicle Type, Model Year

## Integration with Mingus

The VIN lookup service is fully integrated with the Mingus Flask application:

1. **Service Class**: `backend/services/vin_lookup_service.py`
2. **API Endpoints**: `backend/api/vehicle_endpoints.py`
3. **Error Handling**: Follows Mingus error handling patterns
4. **Logging**: Uses Mingus logging configuration
5. **Database**: Can be extended to store VIN lookup history

## Example Integration

```python
# In your Flask route
from backend.services.vin_lookup_service import VINLookupService

@app.route('/lookup-vehicle', methods=['POST'])
def lookup_vehicle():
    data = request.get_json()
    vin = data.get('vin')
    
    try:
        vin_service = VINLookupService()
        vehicle_info = vin_service.lookup_vin(vin)
        
        return jsonify({
            'success': True,
            'vehicle': {
                'make': vehicle_info.make,
                'model': vehicle_info.model,
                'year': vehicle_info.year,
                'fuel_type': vehicle_info.fuel_type
            }
        })
    except VINValidationError as e:
        return jsonify({'error': f'Invalid VIN: {e}'}), 400
    except Exception as e:
        return jsonify({'error': 'Lookup failed'}), 500
```

## Troubleshooting

### Common Issues

1. **API Timeout**: Increase timeout value or check network connectivity
2. **Invalid VIN**: Ensure VIN is 17 characters and contains no invalid characters (I, O, Q)
3. **Service Unavailable**: Check service status and wait for recovery
4. **Cache Issues**: Clear cache if experiencing stale data

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('backend.services.vin_lookup_service').setLevel(logging.DEBUG)
```

## License

This VIN lookup service is part of the Mingus Personal Finance Application and follows the same licensing terms.

## Support

For issues or questions regarding the VIN lookup service, please refer to the Mingus application documentation or contact the development team.
