# Simple Flask Integration Setup

This is a simplified approach to integrate UserService and OnboardingService with Flask. The comprehensive factory pattern files are preserved for later use.

## Quick Start

### 1. Environment Setup

Copy the simple environment file:
```bash
cp simple_env.example .env
```

Edit `.env` with your database credentials:
```bash
DATABASE_URL=postgresql://username:password@localhost/mingus_db
SECRET_KEY=your-secret-key
FLASK_DEBUG=true
PORT=5002
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

### 3. Run the Application

```bash
python simple_app.py
```

The app will start on `http://localhost:5002`

## Available Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user  
- `POST /api/logout` - Logout user
- `GET /api/check-auth` - Check authentication status

### Profile Management
- `GET /api/profile` - Get user profile (requires auth)
- `PUT /api/profile` - Update user profile (requires auth)

### Onboarding
- `POST /api/onboarding/start` - Start onboarding (requires auth)
- `POST /api/onboarding/step/<step_name>` - Update onboarding step (requires auth)
- `GET /api/onboarding/progress` - Get onboarding progress (requires auth)

## Example Usage

### Register a User
```bash
curl -X POST http://localhost:5002/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123!",
    "full_name": "Test User",
    "phone_number": "+1234567890"
  }'
```

### Login
```bash
curl -X POST http://localhost:5002/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123!"
  }'
```

### Update Profile
```bash
curl -X PUT http://localhost:5002/api/profile \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{
    "monthly_income": 5000,
    "age_range": "26-35",
    "location_state": "CA"
  }'
```

## Key Features

- **Simple Setup**: Single file application
- **Service Integration**: UserService and OnboardingService available
- **Session Authentication**: Simple session-based auth
- **Database Integration**: Automatic table creation
- **CORS Support**: Configured for frontend development
- **Error Handling**: Basic error responses

## Services Available

- `app.user_service` - UserService instance
- `app.onboarding_service` - OnboardingService instance

## Differences from Factory Pattern

This simple approach:
- ✅ Single file setup
- ✅ Direct service initialization  
- ✅ Simple authentication
- ✅ Basic error handling
- ❌ No configuration classes
- ❌ No blueprints
- ❌ No middleware
- ❌ Limited scalability

## When to Use

**Use Simple Approach:**
- Quick prototyping
- Small applications
- Learning/testing
- Minimal setup needed

**Use Factory Pattern (preserved files):**
- Production applications
- Large codebases
- Multiple environments
- Team development
- Scalable architecture

## Files Preserved for Later Use

The comprehensive factory pattern implementation is preserved in:
- `backend/app_factory.py` - Application factory
- `config/` - Configuration classes
- `backend/routes/` - Blueprint routes
- `app.py` - Factory-based entry point
- `env.example` - Full environment example
- `docs/FLASK_INTEGRATION_GUIDE.md` - Complete documentation

You can switch to the factory pattern later by running `python app.py` instead of `python simple_app.py`. 