# Flask Integration Guide

## Overview

This guide explains how to integrate the UserService and OnboardingService with your Flask application using the application factory pattern. The services are made available as `current_app.user_service` and `current_app.onboarding_service` throughout your application.

## Architecture

### Application Factory Pattern

The application uses the factory pattern to create and configure the Flask application:

```
app.py (entry point)
├── backend/app_factory.py (factory function)
├── config/ (configuration classes)
├── backend/routes/ (blueprint routes)
└── backend/services/ (service classes)
```

### Service Integration

Services are initialized during app creation and attached to the Flask app context:

- `current_app.user_service` - UserService instance
- `current_app.onboarding_service` - OnboardingService instance
- `current_app.config['DATABASE_SESSION']` - Database session factory

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file based on `env.example`:

```bash
# Copy example environment file
cp env.example .env

# Edit with your actual values
nano .env
```

Key configuration variables:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost/mingus_db
CREATE_TABLES=true

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Features
ENABLE_ONBOARDING=true
ENABLE_USER_PROFILES=true
BYPASS_AUTH=true
```

### 2. Database Setup

Run the database migrations:

```sql
-- Create users table
\i migrations/20250618_create_users_table.sql

-- Create user profiles table
\i migrations/20250618_create_user_profiles_table.sql

-- Create onboarding progress table
\i migrations/20250618_create_onboarding_progress_table.sql
```

### 3. Application Startup

The main application entry point is `app.py`:

```python
from backend.app_factory import create_app

app = create_app()  # Creates and configures the Flask app
```

## Service Usage

### Accessing Services in Routes

Services are available in route handlers via `current_app`:

```python
from flask import Blueprint, current_app, jsonify, request

@bp.route('/users', methods=['GET'])
def get_users():
    # Access UserService
    user_service = current_app.user_service
    
    # Access OnboardingService
    onboarding_service = current_app.onboarding_service
    
    # Use services
    users = user_service.get_all_users()
    return jsonify(users)
```

### Service Helper Functions

Use helper functions to get services outside of request context:

```python
from backend.app_factory import get_user_service, get_onboarding_service

def some_function():
    user_service = get_user_service()
    onboarding_service = get_onboarding_service()
    
    if user_service and onboarding_service:
        # Use services
        pass
```

## Route Blueprints

### Authentication Routes (`/api/auth`)

```python
# Registration
POST /api/auth/register
{
    "email": "user@example.com",
    "password": "securepassword123!",
    "full_name": "John Doe",
    "phone_number": "+1234567890"
}

# Login
POST /api/auth/login
{
    "email": "user@example.com",
    "password": "securepassword123!"
}

# Logout
POST /api/auth/logout

# Get Profile
GET /api/auth/profile

# Update Profile
PUT /api/auth/profile
{
    "full_name": "John Smith",
    "phone_number": "+1234567890"
}

# Check Authentication
GET /api/auth/check-auth
```

### Onboarding Routes (`/api/onboarding`)

```python
# Start Onboarding
POST /api/onboarding/start

# Create Profile
POST /api/onboarding/profile
{
    "monthly_income": 5000,
    "income_frequency": "monthly",
    "primary_income_source": "salary",
    "age_range": "26-35",
    "location_state": "CA",
    "location_city": "San Francisco",
    "household_size": 2,
    "employment_status": "employed",
    "current_savings": 10000,
    "current_debt": 5000,
    "credit_score_range": "good"
}

# Set Goals
POST /api/onboarding/goals
{
    "primary_goal": "save",
    "goal_amount": 50000,
    "goal_timeline_months": 24
}

# Set Preferences
POST /api/onboarding/preferences
{
    "risk_tolerance": "moderate",
    "investment_experience": "beginner"
}

# Set Expenses
POST /api/onboarding/expenses
{
    "expense_categories": {
        "housing": 2000,
        "transportation": 500,
        "food": 800,
        "utilities": 300,
        "healthcare": 200,
        "entertainment": 300,
        "shopping": 400,
        "debt_payments": 500,
        "savings": 1000,
        "other": 200
    }
}

# Complete Onboarding
POST /api/onboarding/complete

# Get Progress
GET /api/onboarding/progress

# Update Step
POST /api/onboarding/step/profile
{
    "completed": true,
    "responses": {
        "income": 5000,
        "location": "CA"
    }
}
```

### User Routes (`/api/user`)

```python
# Get Current User
GET /api/user/me

# Update Current User
PUT /api/user/me
{
    "full_name": "John Smith",
    "phone_number": "+1234567890"
}

# Get User Profile
GET /api/user/profile

# Update User Profile
PUT /api/user/profile
{
    "monthly_income": 6000,
    "current_savings": 15000
}

# Get Onboarding Progress
GET /api/user/onboarding

# Get Dashboard Data
GET /api/user/dashboard

# Deactivate Account
POST /api/user/deactivate
```

## Configuration Classes

### Base Configuration (`config/base.py`)

Contains common configuration for all environments:

```python
class Config:
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    CREATE_TABLES = os.environ.get('CREATE_TABLES', 'true').lower() == 'true'
    
    # Feature flags
    ENABLE_ONBOARDING = os.environ.get('ENABLE_ONBOARDING', 'true').lower() == 'true'
    ENABLE_USER_PROFILES = os.environ.get('ENABLE_USER_PROFILES', 'true').lower() == 'true'
    BYPASS_AUTH = os.environ.get('BYPASS_AUTH', 'false').lower() == 'true'
```

### Development Configuration (`config/development.py`)

Development-specific settings:

```python
class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = 'postgresql://mingus_user:mingus_password@localhost/mingus_dev'
    CREATE_TABLES = True
    BYPASS_AUTH = True
    LOG_LEVEL = 'DEBUG'
```

### Production Configuration (`config/production.py`)

Production-specific settings:

```python
class ProductionConfig(Config):
    DEBUG = False
    CREATE_TABLES = False
    BYPASS_AUTH = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'INFO'
```

## Database Integration

### Connection Pooling

The application uses SQLAlchemy connection pooling:

```python
engine = create_engine(
    database_url,
    pool_size=app.config.get('DB_POOL_SIZE', 10),
    max_overflow=app.config.get('DB_MAX_OVERFLOW', 20),
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Session Management

Database sessions are managed through the app context:

```python
# Get session factory
SessionLocal = current_app.config.get('DATABASE_SESSION')

# Use session
session = SessionLocal()
try:
    # Database operations
    pass
finally:
    session.close()
```

### Table Creation

Tables are automatically created in development:

```python
if app.config.get('CREATE_TABLES', True):
    UserBase.metadata.create_all(bind=engine)
    ProfileBase.metadata.create_all(bind=engine)
    ProgressBase.metadata.create_all(bind=engine)
```

## Error Handling

### Global Error Handlers

The application includes global error handlers:

```python
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Resource not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return {'error': 'Internal server error'}, 500
```

### Service Error Handling

Services include comprehensive error handling:

```python
try:
    # Service operation
    result = service.method()
    return result
except SQLAlchemyError as e:
    logger.error(f"Database error: {str(e)}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    return None
```

## Logging

### Configuration

Logging is configured in `app.py`:

```python
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
```

### Usage in Services

Services use structured logging:

```python
logger.info(f"User created successfully: {email}")
logger.warning(f"User already exists: {email}")
logger.error(f"Database error creating user: {str(e)}")
```

## Testing

### Running the Application

```bash
# Development
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost/mingus_dev
python app.py

# Production
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost/mingus_prod
python app.py
```

### Testing API Endpoints

```bash
# Register user
curl -X POST http://localhost:5002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123!",
    "full_name": "Test User",
    "phone_number": "+1234567890"
  }'

# Login
curl -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123!"
  }'

# Get profile
curl -X GET http://localhost:5002/api/auth/profile \
  -H "Cookie: session=your-session-cookie"
```

## Best Practices

### 1. Service Access

Always access services through `current_app` in route handlers:

```python
# Good
user_service = current_app.user_service

# Bad (don't import directly)
from backend.services.user_service import UserService
user_service = UserService()
```

### 2. Error Handling

Always handle service method returns:

```python
user = current_app.user_service.create_user(user_data)
if user:
    return jsonify({'success': True, 'user': user}), 201
else:
    return jsonify({'error': 'Failed to create user'}), 500
```

### 3. Session Management

Use sessions for authentication:

```python
# Store user in session
session['user_id'] = user['id']
session['user_email'] = user['email']

# Check authentication
user_id = session.get('user_id')
if not user_id:
    return jsonify({'error': 'Not authenticated'}), 401
```

### 4. Configuration

Use environment variables for configuration:

```python
# Good
DATABASE_URL = os.environ.get('DATABASE_URL')

# Bad (hardcoded)
DATABASE_URL = 'postgresql://user:pass@localhost/db'
```

### 5. Logging

Use appropriate log levels:

```python
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check `DATABASE_URL` environment variable
   - Ensure database is running
   - Verify user permissions

2. **Service Not Available**
   - Check if services are initialized in `app_factory.py`
   - Verify database connection
   - Check application logs

3. **Authentication Issues**
   - Verify `SECRET_KEY` is set
   - Check session configuration
   - Ensure `BYPASS_AUTH` is set correctly for development

4. **CORS Errors**
   - Check `CORS_ORIGINS` configuration
   - Verify frontend URL is included in origins
   - Check browser console for CORS errors

### Debug Mode

Enable debug mode for detailed error messages:

```bash
export FLASK_DEBUG=true
export LOG_LEVEL=DEBUG
python app.py
```

### Logs

Check application logs for errors:

```bash
tail -f logs/app.log
```

## Next Steps

1. **Add Authentication Middleware**: Implement proper authentication middleware
2. **Add Rate Limiting**: Implement rate limiting for API endpoints
3. **Add Caching**: Implement caching for frequently accessed data
4. **Add Admin Routes**: Create admin routes for user management
5. **Add Email Verification**: Implement email verification for new users
6. **Add Password Reset**: Implement password reset functionality
7. **Add API Documentation**: Generate API documentation using Swagger/OpenAPI 