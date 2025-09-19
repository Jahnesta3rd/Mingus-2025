# Housing Location Feature Database Schema

## Overview

This document describes the database schema for the Optimal Living Location feature in MINGUS. The feature helps users find the best housing locations based on their commute, financial situation, and career opportunities.

## Database Tables

### 1. `housing_searches` Table

Tracks user housing searches and their criteria.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `search_criteria` (JSON) - Search filters like max_rent, bedrooms, commute_time
- `msa_area` (VARCHAR(100)) - Metropolitan Statistical Area
- `lease_end_date` (DATE, NULLABLE) - When current lease ends
- `results_count` (INTEGER, DEFAULT 0) - Number of results found
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

**Constraints:**
- `check_positive_results_count`: results_count >= 0

**Indexes:**
- `idx_housing_searches_user_id`: user_id
- `idx_housing_searches_msa_area`: msa_area
- `idx_housing_searches_user_msa`: (user_id, msa_area)
- `idx_housing_searches_created_at`: created_at
- `idx_housing_searches_lease_end`: lease_end_date

### 2. `housing_scenarios` Table

Stores specific housing options with comprehensive analysis.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `scenario_name` (VARCHAR(255)) - User-defined name for the scenario
- `housing_data` (JSON) - Address, rent, location details
- `commute_data` (JSON) - Distance, time, costs
- `financial_impact` (JSON) - Affordability scores, cash flow impact
- `career_data` (JSON) - Job opportunities, salary projections
- `is_favorite` (BOOLEAN, DEFAULT FALSE) - User favorite flag
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_housing_scenarios_user_id`: user_id
- `idx_housing_scenarios_is_favorite`: is_favorite
- `idx_housing_scenarios_user_favorite`: (user_id, is_favorite)
- `idx_housing_scenarios_created_at`: created_at
- `idx_housing_scenarios_name`: scenario_name

### 3. `user_housing_preferences` Table

Stores user's housing preferences and criteria (one-to-one with users).

**Columns:**
- `user_id` (INTEGER, PRIMARY KEY, FOREIGN KEY → users.id)
- `max_commute_time` (INTEGER, NULLABLE) - Maximum commute time in minutes
- `preferred_housing_type` (ENUM, NULLABLE) - apartment, house, condo
- `min_bedrooms` (INTEGER, NULLABLE) - Minimum number of bedrooms
- `max_bedrooms` (INTEGER, NULLABLE) - Maximum number of bedrooms
- `max_rent_percentage` (NUMERIC(5,2), NULLABLE) - Max rent as percentage of income
- `preferred_neighborhoods` (ARRAY[STRING], NULLABLE) - Preferred neighborhood names
- `updated_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

**Constraints:**
- `check_positive_commute_time`: max_commute_time >= 0
- `check_positive_min_bedrooms`: min_bedrooms >= 0
- `check_positive_max_bedrooms`: max_bedrooms >= 0
- `check_bedroom_range`: min_bedrooms <= max_bedrooms
- `check_rent_percentage_range`: max_rent_percentage >= 0 AND max_rent_percentage <= 100

**Indexes:**
- `idx_housing_prefs_commute_time`: max_commute_time
- `idx_housing_prefs_housing_type`: preferred_housing_type
- `idx_housing_prefs_rent_percentage`: max_rent_percentage
- `idx_housing_prefs_updated_at`: updated_at

### 4. `commute_route_cache` Table

Caches Google Maps API route data to reduce API calls.

**Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `origin_zip` (VARCHAR(10)) - Origin zip code
- `destination_zip` (VARCHAR(10)) - Destination zip code
- `distance_miles` (NUMERIC(8,2)) - Route distance in miles
- `drive_time_minutes` (INTEGER) - Drive time in minutes
- `traffic_factor` (NUMERIC(3,2), DEFAULT 1.0) - Traffic multiplier
- `last_updated` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

**Constraints:**
- `check_positive_distance`: distance_miles >= 0
- `check_positive_drive_time`: drive_time_minutes >= 0
- `check_traffic_factor_range`: traffic_factor >= 0.1 AND traffic_factor <= 3.0

**Indexes:**
- `idx_commute_cache_origin_zip`: origin_zip
- `idx_commute_cache_destination_zip`: destination_zip
- `idx_commute_cache_route`: (origin_zip, destination_zip)
- `idx_commute_cache_last_updated`: last_updated
- `idx_commute_cache_distance`: distance_miles

## JSON Field Schemas

### `search_criteria` (housing_searches)
```json
{
  "max_rent": 2500,
  "min_bedrooms": 2,
  "max_bedrooms": 3,
  "max_commute_time": 30,
  "housing_types": ["apartment", "condo"],
  "amenities": ["parking", "laundry", "gym"],
  "pet_friendly": true,
  "furnished": false
}
```

### `housing_data` (housing_scenarios)
```json
{
  "address": "123 Main St, City, State 12345",
  "rent": 2200,
  "bedrooms": 2,
  "bathrooms": 2,
  "square_feet": 1200,
  "housing_type": "apartment",
  "amenities": ["parking", "laundry", "gym"],
  "neighborhood": "Downtown",
  "zip_code": "12345",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

### `commute_data` (housing_scenarios)
```json
{
  "distance_miles": 8.5,
  "drive_time_minutes": 25,
  "public_transit_time_minutes": 35,
  "walking_time_minutes": 15,
  "gas_cost_daily": 4.50,
  "public_transit_cost_daily": 5.00,
  "parking_cost_daily": 12.00,
  "total_daily_cost": 16.50,
  "total_monthly_cost": 495.00
}
```

### `financial_impact` (housing_scenarios)
```json
{
  "affordability_score": 85,
  "rent_to_income_ratio": 0.28,
  "total_housing_cost": 2695,
  "monthly_savings": 500,
  "annual_savings": 6000,
  "cost_of_living_index": 1.2,
  "property_tax_estimate": 0,
  "insurance_estimate": 50
}
```

### `career_data` (housing_scenarios)
```json
{
  "job_opportunities_count": 150,
  "average_salary": 75000,
  "salary_range_min": 55000,
  "salary_range_max": 95000,
  "industry_concentration": ["tech", "finance", "healthcare"],
  "remote_work_friendly": true,
  "commute_impact_score": 75
}
```

## Database Schema Diagram

```
users (existing)
  │
  ├── housing_searches (1:many)
  │
  ├── housing_scenarios (1:many)
  │
  └── user_housing_preferences (1:1)

commute_route_cache (standalone)
```

## Migration Details

### Migration ID
- **Revision ID**: `005_add_housing_location_tables`
- **Previous Revision**: `004_add_vehicle_management_tables`
- **File**: `migrations/versions/005_add_housing_location_tables.py`

### Running the Migration

```bash
# Navigate to migrations directory
cd migrations

# Run the migration
alembic upgrade 005_add_housing_location_tables

# Or upgrade to latest
alembic upgrade head
```

### Rollback

```bash
# Rollback to previous migration
alembic downgrade 004_add_vehicle_management_tables
```

## Performance Considerations

### Indexes Added
- **Primary Keys**: All tables have integer primary keys
- **Foreign Keys**: Indexed for join performance
- **Search Fields**: MSA, zip codes, user preferences
- **Composite Indexes**: Multi-column indexes for common query patterns
- **Date Indexes**: For time-based queries and cache expiration

### Query Optimization
- Foreign key constraints ensure data integrity
- Check constraints prevent invalid data
- JSON fields allow flexible data storage
- Proper data types for efficient storage
- Indexes optimized for common query patterns

## Integration with Existing System

### Compatibility
- **SQLite Compatible**: Uses SQLite-specific features appropriately
- **Existing Schema**: Extends existing users table
- **Migration History**: Follows existing migration numbering
- **Rollback Safe**: Complete downgrade functionality

### API Integration
- Tables are ready for SQLAlchemy ORM
- Compatible with existing Flask app structure
- Follows MINGUS naming conventions
- Supports existing validation patterns

## Usage Examples

### Creating a Housing Search
```python
from backend.models import HousingSearch, User

# Create a new housing search
search = HousingSearch(
    user_id=user.id,
    search_criteria={
        "max_rent": 2500,
        "min_bedrooms": 2,
        "max_commute_time": 30,
        "housing_types": ["apartment", "condo"]
    },
    msa_area="San Francisco-Oakland-Berkeley, CA",
    lease_end_date=date(2024, 6, 30),
    results_count=0
)
db.session.add(search)
db.session.commit()
```

### Creating a Housing Scenario
```python
from backend.models import HousingScenario

# Create a housing scenario
scenario = HousingScenario(
    user_id=user.id,
    scenario_name="Downtown Apartment",
    housing_data={
        "address": "123 Market St, San Francisco, CA 94105",
        "rent": 3200,
        "bedrooms": 2,
        "bathrooms": 2,
        "square_feet": 1200
    },
    commute_data={
        "distance_miles": 3.2,
        "drive_time_minutes": 15,
        "total_daily_cost": 8.50
    },
    financial_impact={
        "affordability_score": 78,
        "rent_to_income_ratio": 0.32
    },
    career_data={
        "job_opportunities_count": 200,
        "average_salary": 85000
    },
    is_favorite=False
)
db.session.add(scenario)
db.session.commit()
```

### Setting User Preferences
```python
from backend.models import UserHousingPreferences, HousingType

# Set user housing preferences
preferences = UserHousingPreferences(
    user_id=user.id,
    max_commute_time=30,
    preferred_housing_type=HousingType.APARTMENT,
    min_bedrooms=2,
    max_bedrooms=3,
    max_rent_percentage=30.0,
    preferred_neighborhoods=["Downtown", "Mission District", "SOMA"]
)
db.session.add(preferences)
db.session.commit()
```

## Troubleshooting

### Common Issues

1. **Migration Fails**
   ```bash
   # Check current migration status
   alembic current
   
   # Check migration history
   alembic history
   ```

2. **JSON Field Issues**
   - Ensure JSON data is properly formatted
   - Use `db.JSON` for flexible schema storage
   - Validate JSON structure in application code

3. **Enum Type Issues**
   - HousingType enum is created automatically
   - Ensure enum values match exactly
   - Check for case sensitivity

4. **Foreign Key Constraints**
   - Ensure users table exists before running migration
   - Check user_id references are valid
   - Use CASCADE delete for data cleanup
