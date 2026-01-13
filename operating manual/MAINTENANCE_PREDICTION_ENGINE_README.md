# Maintenance Prediction Engine for Mingus Flask Application

A comprehensive maintenance prediction engine that forecasts vehicle maintenance costs based on mileage intervals, age-based repairs, and regional pricing adjustments.

## Features

- **Routine Maintenance Prediction**: Based on realistic mileage intervals (oil changes every 5,000 miles, brakes every 30,000 miles, etc.)
- **Age-Based Repair Predictions**: With probability estimates based on vehicle age
- **ZIP Code to MSA Mapping**: Maps user zipcodes to appropriate MSAs within a 75-mile radius
- **Regional Pricing Adjustments**: Adjusts maintenance costs based on MSA regional pricing multipliers
- **Fallback Pricing**: For zipcodes outside the 75-mile radius of target MSAs
- **Cash Flow Integration**: Generates maintenance cost forecasts for financial planning
- **Mileage Update Methods**: Updates predictions when vehicle mileage changes
- **MaintenancePrediction Model Compatibility**: Stores predictions in the existing database model

## Target MSA Centers (75-mile radius)

The engine covers the following major metropolitan areas:

1. **Atlanta, GA (30309)** - Pricing Multiplier: 0.95
2. **Houston, TX (77002)** - Pricing Multiplier: 0.90
3. **Washington, DC (20001)** - Pricing Multiplier: 1.15
4. **Dallas, TX (75201)** - Pricing Multiplier: 0.92
5. **New York, NY (10001)** - Pricing Multiplier: 1.25
6. **Philadelphia, PA (19102)** - Pricing Multiplier: 1.05
7. **Chicago, IL (60601)** - Pricing Multiplier: 1.10
8. **Charlotte, NC (28202)** - Pricing Multiplier: 0.88
9. **Miami, FL (33101)** - Pricing Multiplier: 1.08
10. **Baltimore, MD (21201)** - Pricing Multiplier: 1.02

## Maintenance Schedules

### Routine Maintenance (Mileage-Based)
- **Oil Change**: Every 5,000 miles - $45.00
- **Tire Rotation**: Every 7,500 miles - $25.00
- **Air Filter**: Every 15,000 miles - $35.00
- **Cabin Filter**: Every 20,000 miles - $40.00
- **Brake Inspection**: Every 25,000 miles - $75.00
- **Brake Pad Replacement**: Every 30,000 miles - $200.00
- **Transmission Service**: Every 60,000 miles - $150.00
- **Timing Belt**: Every 90,000 miles - $800.00
- **Spark Plugs**: Every 100,000 miles - $120.00
- **Battery Replacement**: Every 120,000 miles - $150.00

### Age-Based Maintenance
- **Suspension Check**: Every 36 months - $100.00
- **Exhaust System**: Every 48 months - $300.00
- **AC System Service**: Every 24 months - $150.00
- **Power Steering**: Every 60 months - $80.00
- **Coolant System**: Every 36 months - $120.00
- **Fuel System**: Every 48 months - $200.00
- **Electrical System**: Every 42 months - $150.00
- **Body & Paint**: Every 72 months - $500.00
- **Interior Maintenance**: Every 30 months - $200.00
- **Safety Systems**: Every 24 months - $100.00

## Usage

### Service Class Usage

```python
from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine

# Initialize the engine
engine = MaintenancePredictionEngine()

# Generate maintenance predictions
predictions = engine.predict_maintenance(
    vehicle_id=1,
    year=2020,
    make="Honda",
    model="Civic",
    current_mileage=35000,
    zipcode="10001",
    prediction_horizon_months=12
)

# Get cash flow forecast
forecast = engine.get_cash_flow_forecast(vehicle_id=1, months=12)

# Update predictions when mileage changes
updated_predictions = engine.update_predictions_for_mileage_change(
    vehicle_id=1, new_mileage=40000
)
```

### API Endpoints

#### 1. Generate Maintenance Predictions
**POST** `/api/vehicles/{vehicle_id}/maintenance-predictions/generate`

Generate maintenance predictions for a vehicle.

**Request Body:**
```json
{
    "prediction_horizon_months": 24
}
```

**Response:**
```json
{
    "success": true,
    "vehicle_id": 1,
    "predictions": [
        {
            "service_type": "Oil Change",
            "description": "Regular oil and filter change",
            "predicted_date": "2025-02-15",
            "predicted_mileage": 40000,
            "estimated_cost": 56.25,
            "probability": 0.95,
            "is_routine": true,
            "maintenance_type": "routine",
            "priority": "medium",
            "msa_name": "New York, NY",
            "pricing_multiplier": 1.25,
            "base_cost": 45.00,
            "regional_adjustment": 11.25
        }
    ],
    "prediction_horizon_months": 24,
    "total_predictions": 15,
    "message": "Maintenance predictions generated successfully"
}
```

#### 2. Get Maintenance Predictions
**GET** `/api/vehicles/{vehicle_id}/maintenance-predictions`

Get existing maintenance predictions for a vehicle.

#### 3. Update Mileage
**PUT** `/api/vehicles/{vehicle_id}/maintenance-predictions/update-mileage`

Update maintenance predictions when vehicle mileage changes.

**Request Body:**
```json
{
    "new_mileage": 40000
}
```

#### 4. Get Cash Flow Forecast
**GET** `/api/vehicles/{vehicle_id}/maintenance-predictions/cash-flow?months=12`

Get cash flow forecast for maintenance costs.

**Response:**
```json
{
    "success": true,
    "vehicle_id": 1,
    "forecast": {
        "vehicle_id": 1,
        "forecast_period_months": 12,
        "total_estimated_cost": 2881.25,
        "routine_maintenance_cost": 1668.75,
        "age_based_maintenance_cost": 1212.50,
        "monthly_breakdown": {
            "2025-01": {
                "total_cost": 2737.50,
                "routine_cost": 1668.75,
                "age_based_cost": 1068.75,
                "predictions": [...]
            }
        },
        "average_monthly_cost": 240.10,
        "generated_date": "2025-01-17"
    },
    "message": "Cash flow forecast generated successfully"
}
```

#### 5. Map ZIP Code to MSA
**POST** `/api/vehicles/maintenance-predictions/msa-mapping`

Map ZIP code to MSA for regional pricing.

**Request Body:**
```json
{
    "zipcode": "10001"
}
```

**Response:**
```json
{
    "success": true,
    "zipcode": "10001",
    "msa_name": "New York, NY",
    "pricing_multiplier": 1.25,
    "message": "ZIP code mapped to MSA successfully"
}
```

#### 6. Get Service Status
**GET** `/api/vehicles/maintenance-predictions/status`

Get maintenance prediction service status and statistics.

## Configuration

The maintenance prediction engine can be configured with various parameters:

```python
engine = MaintenancePredictionEngine(
    db_path="backend/mingus_vehicles.db"  # Database path
)
```

### MSA Centers
MSA centers are defined with their coordinates and pricing multipliers:

```python
msa_centers = [
    MSACenter("Atlanta, GA", "30309", 33.7890, -84.3880, 0.95),
    MSACenter("Houston, TX", "77002", 29.7604, -95.3698, 0.90),
    # ... more centers
]
```

### Maintenance Schedules
Maintenance schedules define service intervals and costs:

```python
maintenance_schedules = [
    MaintenanceSchedule(
        service_type="Oil Change",
        description="Regular oil and filter change",
        mileage_interval=5000,
        age_interval_months=6,
        base_cost=45.00,
        priority=ServicePriority.MEDIUM,
        is_routine=True,
        probability_base=0.95
    ),
    # ... more schedules
]
```

## Probability Calculations

### Mileage-Based Probability
Probability increases as the vehicle approaches the target mileage:

- **0-80% of interval**: Low probability (30% of base)
- **80-95% of interval**: Medium probability (70% of base)
- **95-100% of interval**: High probability (100% of base)

### Age-Based Probability
Probability increases with vehicle age:

```python
age_factor = min(vehicle_age_months / service.age_interval_months, 2.0)
probability = service.probability_base * age_factor * condition_factor
```

## Regional Pricing

### MSA Pricing Multipliers
- **New York, NY**: 1.25 (25% above base)
- **Washington, DC**: 1.15 (15% above base)
- **Chicago, IL**: 1.10 (10% above base)
- **Philadelphia, PA**: 1.05 (5% above base)
- **Miami, FL**: 1.08 (8% above base)
- **Baltimore, MD**: 1.02 (2% above base)
- **Atlanta, GA**: 0.95 (5% below base)
- **Dallas, TX**: 0.92 (8% below base)
- **Houston, TX**: 0.90 (10% below base)
- **Charlotte, NC**: 0.88 (12% below base)

### Fallback Pricing
For ZIP codes outside the 75-mile radius of target MSAs, a fallback pricing multiplier of 1.0 (base pricing) is used.

## Distance Calculation

The engine uses the Haversine formula to calculate distances between ZIP codes and MSA centers:

```python
def _calculate_distance(self, lat1, lon1, lat2, lon2):
    R = 3959  # Earth's radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
```

## Database Integration

The engine integrates with the existing `MaintenancePrediction` model:

```python
class MaintenancePrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    service_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    predicted_date = db.Column(db.Date)
    predicted_mileage = db.Column(db.Integer)
    estimated_cost = db.Column(db.Numeric(10, 2))
    probability = db.Column(db.Float)
    is_routine = db.Column(db.Boolean)
    # ... additional fields
```

## Testing

Run the test suite to verify functionality:

```bash
python test_maintenance_prediction.py
```

Run the example to see usage patterns:

```bash
python maintenance_prediction_example.py
```

## Integration with Cash Flow Forecasting

The maintenance prediction engine integrates with the Mingus cash flow forecasting system:

1. **Monthly Cost Projections**: Provides monthly maintenance cost estimates
2. **Budget Planning**: Helps users plan for upcoming maintenance expenses
3. **Financial Impact**: Shows regional cost variations for different locations
4. **Priority Scheduling**: Identifies high-cost, high-probability maintenance needs

## Error Handling

The engine includes comprehensive error handling:

- **Invalid ZIP Codes**: Falls back to base pricing
- **Database Errors**: Graceful degradation with logging
- **Missing Vehicle Data**: Clear error messages
- **API Failures**: Fallback mechanisms for external services

## Performance

- **Caching**: Predictions are cached to avoid recalculation
- **Batch Processing**: Multiple predictions generated efficiently
- **Database Optimization**: Indexed queries for fast retrieval
- **Memory Management**: Efficient data structures for large datasets

## Future Enhancements

Potential future improvements:

1. **Machine Learning**: Use historical data to improve prediction accuracy
2. **Weather Integration**: Factor in climate conditions for maintenance needs
3. **Driving Pattern Analysis**: Consider driving habits in predictions
4. **Real-time Pricing**: Integrate with live service pricing APIs
5. **Maintenance History**: Learn from past maintenance records
6. **Vehicle-Specific Adjustments**: Customize schedules based on make/model

## License

This maintenance prediction engine is part of the Mingus Personal Finance Application and follows the same licensing terms.

## Support

For issues or questions regarding the maintenance prediction engine, please refer to the Mingus application documentation or contact the development team.
