# Mingus Vehicle Management System

## Overview

The Mingus Vehicle Management System provides comprehensive SQLAlchemy models and API endpoints for tracking vehicles, maintenance predictions, commute scenarios, and gas prices by Metropolitan Statistical Area (MSA). This system integrates with the existing Mingus financial application to provide vehicle-related financial insights and cost tracking.

## Models

### 1. User Model (`backend/models/user_models.py`)

Based on the existing Mingus user structure with additional relationships to vehicles.

**Key Fields:**
- `id`: Primary key
- `user_id`: Unique user identifier
- `email`: User email address
- `first_name`, `last_name`: User personal information
- `referral_code`: Referral system integration
- `feature_unlocked`: Feature access control
- `created_at`, `updated_at`: Timestamps

**Relationships:**
- `vehicles`: One-to-many relationship with Vehicle model

### 2. Vehicle Model (`backend/models/vehicle_models.py`)

Tracks user vehicles with comprehensive details for financial analysis.

**Key Fields:**
- `id`: Primary key
- `user_id`: Foreign key to User model
- `vin`: Vehicle Identification Number (unique)
- `year`, `make`, `model`, `trim`: Vehicle specifications
- `current_mileage`: Current odometer reading
- `monthly_miles`: Estimated monthly mileage
- `user_zipcode`: User's zipcode for MSA mapping
- `assigned_msa`: Assigned Metropolitan Statistical Area
- `created_date`, `updated_date`: Timestamps

**Relationships:**
- `user`: Many-to-one relationship with User model
- `maintenance_predictions`: One-to-many relationship with MaintenancePrediction
- `commute_scenarios`: One-to-many relationship with CommuteScenario

**Indexes:**
- `idx_vehicle_user_year`: Composite index on user_id and year
- `idx_vehicle_make_model`: Composite index on make and model
- `idx_vehicle_msa_zipcode`: Composite index on assigned_msa and user_zipcode

### 3. MaintenancePrediction Model

Predicts future vehicle maintenance needs and costs.

**Key Fields:**
- `id`: Primary key
- `vehicle_id`: Foreign key to Vehicle model
- `service_type`: Type of maintenance service
- `description`: Detailed service description
- `predicted_date`: Predicted service date
- `predicted_mileage`: Predicted mileage at service time
- `estimated_cost`: Estimated service cost
- `probability`: Prediction confidence (0.0 to 1.0)
- `is_routine`: Whether this is routine maintenance
- `created_date`: Timestamp

**Constraints:**
- `check_probability_range`: Ensures probability is between 0.0 and 1.0
- `check_positive_cost`: Ensures estimated cost is non-negative

### 4. CommuteScenario Model

Tracks different job location scenarios and associated costs.

**Key Fields:**
- `id`: Primary key
- `vehicle_id`: Foreign key to Vehicle model
- `job_location`: Job location description
- `job_zipcode`: Job location zipcode
- `distance_miles`: Commute distance in miles
- `daily_cost`: Daily commute cost
- `monthly_cost`: Monthly commute cost
- `gas_price_per_gallon`: Gas price at time of calculation
- `vehicle_mpg`: Vehicle miles per gallon
- `from_msa`, `to_msa`: MSA information for route
- `created_date`: Timestamp

**Constraints:**
- Multiple positive value checks for distance, costs, gas price, and MPG

### 5. MSAGasPrice Model

Tracks current gas prices by Metropolitan Statistical Area.

**Key Fields:**
- `id`: Primary key
- `msa_name`: MSA name (including "National Average")
- `current_price`: Current gas price per gallon
- `last_updated`: Last update timestamp

**Constraints:**
- `check_positive_price`: Ensures gas price is non-negative

## API Endpoints

### Vehicle Management

- `GET /api/vehicles?user_id={user_id}` - Get all vehicles for a user
- `POST /api/vehicles` - Create a new vehicle
- `GET /api/vehicles/{vehicle_id}` - Get specific vehicle
- `PUT /api/vehicles/{vehicle_id}` - Update vehicle
- `DELETE /api/vehicles/{vehicle_id}` - Delete vehicle

### Maintenance Predictions

- `GET /api/vehicles/{vehicle_id}/maintenance-predictions` - Get maintenance predictions
- `POST /api/vehicles/{vehicle_id}/maintenance-predictions` - Create maintenance prediction

### Commute Scenarios

- `GET /api/vehicles/{vehicle_id}/commute-scenarios` - Get commute scenarios
- `POST /api/vehicles/{vehicle_id}/commute-scenarios` - Create commute scenario

### MSA Gas Prices

- `GET /api/msa-gas-prices` - Get all MSA gas prices
- `POST /api/msa-gas-prices` - Create or update MSA gas price

### Analytics

- `GET /api/vehicles/{vehicle_id}/analytics` - Get vehicle analytics

## Database Setup

### 1. Install Dependencies

```bash
pip install Flask-SQLAlchemy==3.0.5
```

### 2. Initialize Database

```python
from backend.models.database import init_database
from flask import Flask

app = Flask(__name__)
init_database(app)
```

### 3. Create Sample Data

```bash
# Set environment variable to create sample data
export CREATE_SAMPLE_DATA=true

# Run initialization script
python backend/models/init_vehicle_db.py
```

### 4. Test Models

```bash
python test_vehicle_models.py
```

## Integration with Existing Mingus App

The vehicle management system is fully integrated with the existing Mingus application:

1. **Database Integration**: Uses the same SQLite database with SQLAlchemy ORM
2. **User Model Compatibility**: Extends existing user model with vehicle relationships
3. **API Integration**: New endpoints registered with existing Flask app
4. **Security**: Inherits existing security middleware and validation
5. **CORS**: Compatible with existing CORS configuration

## Usage Examples

### Creating a Vehicle

```python
from backend.models.database import db
from backend.models.vehicle_models import Vehicle

# Create a new vehicle
vehicle = Vehicle(
    user_id=1,
    vin='1HGBH41JXMN109186',
    year=2020,
    make='Honda',
    model='Civic',
    trim='EX',
    current_mileage=45000,
    monthly_miles=1200,
    user_zipcode='90210',
    assigned_msa='Los Angeles-Long Beach-Anaheim, CA'
)

db.session.add(vehicle)
db.session.commit()
```

### Adding Maintenance Prediction

```python
from backend.models.vehicle_models import MaintenancePrediction
from datetime import date, timedelta
from decimal import Decimal

prediction = MaintenancePrediction(
    vehicle_id=vehicle.id,
    service_type='Oil Change',
    description='Regular oil change service',
    predicted_date=date.today() + timedelta(days=30),
    predicted_mileage=46200,
    estimated_cost=Decimal('45.00'),
    probability=0.95,
    is_routine=True
)

db.session.add(prediction)
db.session.commit()
```

### Creating Commute Scenario

```python
from backend.models.vehicle_models import CommuteScenario

scenario = CommuteScenario(
    vehicle_id=vehicle.id,
    job_location='Downtown Los Angeles',
    job_zipcode='90012',
    distance_miles=25.5,
    daily_cost=Decimal('8.50'),
    monthly_cost=Decimal('187.00'),
    gas_price_per_gallon=Decimal('4.25'),
    vehicle_mpg=32.0,
    from_msa='Los Angeles-Long Beach-Anaheim, CA',
    to_msa='Los Angeles-Long Beach-Anaheim, CA'
)

db.session.add(scenario)
db.session.commit()
```

## Database Schema

The system creates the following tables:

1. `users` - User information (extends existing)
2. `vehicles` - Vehicle details
3. `maintenance_predictions` - Maintenance predictions
4. `commute_scenarios` - Commute cost scenarios
5. `msa_gas_prices` - Gas prices by MSA

## Features

- **Comprehensive Vehicle Tracking**: Full vehicle details with VIN validation
- **Maintenance Prediction**: AI-ready structure for maintenance cost prediction
- **Commute Analysis**: Multiple job location scenario tracking
- **MSA Integration**: Metropolitan Statistical Area mapping for location-based pricing
- **Financial Analytics**: Cost tracking and analysis capabilities
- **RESTful API**: Complete CRUD operations for all models
- **Data Validation**: Comprehensive constraints and validation
- **JSON Serialization**: Built-in to_dict() methods for API responses

## Security

- Inherits existing Mingus security middleware
- Input validation through APIValidator
- SQL injection protection via SQLAlchemy ORM
- CORS protection for API endpoints
- Rate limiting on all endpoints

## Future Enhancements

- Integration with vehicle maintenance APIs
- Real-time gas price updates
- Machine learning for maintenance prediction
- Route optimization for commute scenarios
- Insurance cost tracking
- Depreciation calculations
