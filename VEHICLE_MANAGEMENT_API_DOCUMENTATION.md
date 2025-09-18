# Vehicle Management API Documentation

## Overview

The Vehicle Management API provides comprehensive RESTful endpoints for managing vehicles, maintenance predictions, commute analysis, and cash flow forecasting in the Mingus application. All endpoints require JWT authentication and include proper validation, error handling, and CSRF protection.

## Authentication

All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

For state-changing operations (POST, PUT, DELETE), include the CSRF token:
```
X-CSRF-Token: <csrf_token>
```

## Base URL
```
/api/vehicle
```

## Endpoints

### 1. Create Vehicle
**POST** `/api/vehicle`

Create a new vehicle with optional VIN lookup.

#### Request Body
```json
{
  "vin": "string (optional)",
  "year": "integer",
  "make": "string",
  "model": "string",
  "trim": "string (optional)",
  "current_mileage": "integer (optional, default: 0)",
  "monthly_miles": "integer (optional, default: 0)",
  "user_zipcode": "string",
  "use_vin_lookup": "boolean (optional, default: false)"
}
```

#### Response
```json
{
  "success": true,
  "vehicle": {
    "id": 1,
    "user_id": 123,
    "vin": "1HGBH41JXMN109186",
    "year": 2021,
    "make": "Honda",
    "model": "Civic",
    "trim": "LX",
    "current_mileage": 25000,
    "monthly_miles": 1000,
    "user_zipcode": "30309",
    "assigned_msa": "Atlanta, GA",
    "created_date": "2024-01-15T10:30:00Z",
    "updated_date": "2024-01-15T10:30:00Z"
  },
  "message": "Vehicle created successfully"
}
```

#### Status Codes
- `201` - Vehicle created successfully
- `400` - Invalid request data
- `401` - Authentication required
- `403` - CSRF token required
- `409` - Vehicle with VIN already exists
- `500` - Internal server error

### 2. Get User Vehicles
**GET** `/api/vehicle`

Get all vehicles for the authenticated user.

#### Query Parameters
- `limit` (optional): Maximum number of vehicles to return
- `offset` (optional): Number of vehicles to skip

#### Response
```json
{
  "success": true,
  "vehicles": [
    {
      "id": 1,
      "user_id": 123,
      "vin": "1HGBH41JXMN109186",
      "year": 2021,
      "make": "Honda",
      "model": "Civic",
      "trim": "LX",
      "current_mileage": 25000,
      "monthly_miles": 1000,
      "user_zipcode": "30309",
      "assigned_msa": "Atlanta, GA",
      "created_date": "2024-01-15T10:30:00Z",
      "updated_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1,
  "limit": null,
  "offset": 0
}
```

#### Status Codes
- `200` - Success
- `401` - Authentication required
- `500` - Internal server error

### 3. Get Vehicle
**GET** `/api/vehicle/{id}`

Get a specific vehicle by ID.

#### Response
```json
{
  "success": true,
  "vehicle": {
    "id": 1,
    "user_id": 123,
    "vin": "1HGBH41JXMN109186",
    "year": 2021,
    "make": "Honda",
    "model": "Civic",
    "trim": "LX",
    "current_mileage": 25000,
    "monthly_miles": 1000,
    "user_zipcode": "30309",
    "assigned_msa": "Atlanta, GA",
    "created_date": "2024-01-15T10:30:00Z",
    "updated_date": "2024-01-15T10:30:00Z"
  }
}
```

#### Status Codes
- `200` - Success
- `401` - Authentication required
- `404` - Vehicle not found
- `500` - Internal server error

### 4. Update Vehicle
**PUT** `/api/vehicle/{id}`

Update vehicle information.

#### Request Body
```json
{
  "year": "integer (optional)",
  "make": "string (optional)",
  "model": "string (optional)",
  "trim": "string (optional)",
  "current_mileage": "integer (optional)",
  "monthly_miles": "integer (optional)",
  "user_zipcode": "string (optional)",
  "assigned_msa": "string (optional)"
}
```

#### Response
```json
{
  "success": true,
  "vehicle": {
    "id": 1,
    "user_id": 123,
    "vin": "1HGBH41JXMN109186",
    "year": 2021,
    "make": "Honda",
    "model": "Civic",
    "trim": "LX",
    "current_mileage": 30000,
    "monthly_miles": 1200,
    "user_zipcode": "30309",
    "assigned_msa": "Atlanta, GA",
    "created_date": "2024-01-15T10:30:00Z",
    "updated_date": "2024-01-15T11:45:00Z"
  },
  "message": "Vehicle updated successfully"
}
```

#### Status Codes
- `200` - Vehicle updated successfully
- `400` - Invalid request data
- `401` - Authentication required
- `403` - CSRF token required
- `404` - Vehicle not found
- `500` - Internal server error

### 5. Delete Vehicle
**DELETE** `/api/vehicle/{id}`

Delete a vehicle and all associated data.

#### Response
```json
{
  "success": true,
  "message": "Vehicle deleted successfully"
}
```

#### Status Codes
- `200` - Vehicle deleted successfully
- `401` - Authentication required
- `403` - CSRF token required
- `404` - Vehicle not found
- `500` - Internal server error

### 6. Get Maintenance Predictions
**GET** `/api/vehicle/{id}/maintenance-predictions`

Get maintenance predictions for a vehicle.

#### Query Parameters
- `months` (optional): Number of months to look ahead (default: 12)
- `include_past` (optional): Include past predictions (default: false)

#### Response
```json
{
  "success": true,
  "vehicle_id": 1,
  "predictions": [
    {
      "service_type": "Oil Change",
      "description": "Regular oil change service",
      "predicted_date": "2024-02-15",
      "predicted_mileage": 30000,
      "estimated_cost": 45.00,
      "probability": 0.95,
      "is_routine": true,
      "maintenance_type": "routine",
      "priority": "high",
      "msa_name": "Atlanta, GA",
      "pricing_multiplier": 0.95,
      "base_cost": 40.00,
      "regional_adjustment": 5.00
    }
  ],
  "summary": {
    "total_predictions": 1,
    "routine_predictions": 1,
    "non_routine_predictions": 0,
    "total_estimated_cost": 45.00,
    "routine_cost": 45.00,
    "non_routine_cost": 0.00
  },
  "filters": {
    "months_ahead": 12,
    "include_past": false
  }
}
```

#### Status Codes
- `200` - Success
- `401` - Authentication required
- `404` - Vehicle not found
- `500` - Internal server error

### 7. Calculate Commute Analysis
**POST** `/api/vehicle/{id}/commute-analysis`

Calculate commute costs for job locations.

#### Request Body
```json
{
  "job_locations": [
    {
      "name": "Tech Company Inc",
      "address": "123 Business St",
      "zipcode": "30309",
      "distance_miles": 15.5
    }
  ],
  "vehicle_mpg": 25,
  "work_days_per_month": 22
}
```

#### Response
```json
{
  "success": true,
  "vehicle_id": 1,
  "analysis_results": [
    {
      "job_location": "Tech Company Inc",
      "address": "123 Business St",
      "zipcode": "30309",
      "distance_miles": 15.5,
      "gas_price_per_gallon": 3.20,
      "vehicle_mpg": 25,
      "daily_cost": 1.98,
      "monthly_cost": 43.56,
      "annual_cost": 522.72,
      "msa_name": "Atlanta, GA",
      "work_days_per_month": 22
    }
  ],
  "summary": {
    "total_job_locations": 1,
    "total_monthly_cost": 43.56,
    "total_annual_cost": 522.72,
    "work_days_per_month": 22,
    "vehicle_mpg": 25
  },
  "message": "Commute analysis completed successfully"
}
```

#### Status Codes
- `200` - Analysis completed successfully
- `400` - Invalid request data
- `401` - Authentication required
- `403` - CSRF token required
- `404` - Vehicle not found
- `500` - Internal server error

### 8. Get Forecast Impact
**GET** `/api/vehicle/{id}/forecast-impact`

Get vehicle expenses impact on cash flow.

#### Query Parameters
- `months` (optional): Number of months to forecast (default: 12)
- `include_commute` (optional): Include commute costs (default: true)
- `include_maintenance` (optional): Include maintenance costs (default: true)

#### Response
```json
{
  "success": true,
  "forecast": {
    "vehicle_id": 1,
    "vehicle_info": {
      "id": 1,
      "user_id": 123,
      "vin": "1HGBH41JXMN109186",
      "year": 2021,
      "make": "Honda",
      "model": "Civic",
      "trim": "LX",
      "current_mileage": 25000,
      "monthly_miles": 1000,
      "user_zipcode": "30309",
      "assigned_msa": "Atlanta, GA",
      "created_date": "2024-01-15T10:30:00Z",
      "updated_date": "2024-01-15T10:30:00Z"
    },
    "forecast_period_months": 12,
    "total_monthly_impact": 88.56,
    "total_annual_impact": 1062.72,
    "breakdown": {
      "maintenance": {
        "monthly_cost": 45.00,
        "annual_cost": 540.00,
        "predictions_count": 3
      },
      "commute": {
        "monthly_cost": 43.56,
        "annual_cost": 522.72,
        "scenarios_count": 1
      }
    },
    "monthly_breakdown": [
      {
        "month": 1,
        "maintenance_cost": 45.00,
        "commute_cost": 43.56,
        "total_cost": 88.56
      }
    ]
  },
  "message": "Cash flow forecast generated successfully"
}
```

#### Status Codes
- `200` - Success
- `400` - Invalid request parameters
- `401` - Authentication required
- `404` - Vehicle not found
- `500` - Internal server error

### 9. VIN Lookup
**POST** `/api/vehicle/vin-lookup`

Lookup vehicle information by VIN.

#### Request Body
```json
{
  "vin": "1HGBH41JXMN109186",
  "use_cache": true
}
```

#### Response
```json
{
  "success": true,
  "vehicle_info": {
    "vin": "1HGBH41JXMN109186",
    "year": 2021,
    "make": "Honda",
    "model": "Civic",
    "trim": "LX",
    "engine": "1.5L 4-Cylinder",
    "fuel_type": "Gasoline",
    "body_class": "Sedan",
    "drive_type": "FWD",
    "transmission": "CVT",
    "doors": "4",
    "windows": "4",
    "series": "Civic",
    "plant_city": "Greensburg",
    "plant_state": "IN",
    "plant_country": "United States",
    "manufacturer": "Honda",
    "model_year": 2021,
    "vehicle_type": "PASSENGER CAR",
    "source": "nhtsa",
    "lookup_timestamp": "2024-01-15T10:30:00Z",
    "error_code": null,
    "error_text": null
  },
  "message": "VIN lookup completed successfully"
}
```

#### Status Codes
- `200` - VIN lookup successful
- `400` - Invalid VIN format
- `401` - Authentication required
- `403` - CSRF token required
- `503` - VIN lookup service unavailable
- `500` - Internal server error

### 10. Health Check
**GET** `/api/vehicle/health`

Health check endpoint for vehicle management API.

#### Response
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "vin_lookup": "operational",
    "maintenance_prediction": "operational"
  },
  "message": "Vehicle management API is healthy"
}
```

#### Status Codes
- `200` - API is healthy
- `500` - API is unhealthy

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "status_code": 400
}
```

## Rate Limiting

All endpoints are subject to rate limiting:
- Default: 100 requests per minute per IP address
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Security Features

- **JWT Authentication**: All endpoints require valid JWT tokens
- **CSRF Protection**: State-changing operations require CSRF tokens
- **Input Validation**: All input data is validated and sanitized
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **SQL Injection Protection**: All database queries use parameterized statements
- **XSS Protection**: Input data is sanitized to prevent cross-site scripting

## Examples

### Creating a Vehicle with VIN Lookup
```bash
curl -X POST http://localhost:5000/api/vehicle \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-CSRF-Token: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "vin": "1HGBH41JXMN109186",
    "use_vin_lookup": true,
    "current_mileage": 25000,
    "monthly_miles": 1000,
    "user_zipcode": "30309"
  }'
```

### Getting Maintenance Predictions
```bash
curl -X GET "http://localhost:5000/api/vehicle/1/maintenance-predictions?months=12&include_past=false" \
  -H "Authorization: Bearer your_jwt_token"
```

### Calculating Commute Analysis
```bash
curl -X POST http://localhost:5000/api/vehicle/1/commute-analysis \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-CSRF-Token: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "job_locations": [
      {
        "name": "Tech Company Inc",
        "address": "123 Business St",
        "zipcode": "30309",
        "distance_miles": 15.5
      }
    ],
    "vehicle_mpg": 25,
    "work_days_per_month": 22
  }'
```

## Integration with Existing Services

The Vehicle Management API integrates with several existing Mingus services:

- **VIN Lookup Service**: For vehicle information retrieval
- **Maintenance Prediction Engine**: For maintenance forecasting
- **Gas Price Service**: For location-based fuel pricing
- **MSA Mapping Service**: For geographic cost adjustments
- **User Management**: For authentication and authorization

This integration ensures consistent data flow and leverages existing infrastructure for optimal performance and reliability.
