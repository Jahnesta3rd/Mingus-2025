# OnboardingService Documentation

## Overview

The OnboardingService is a comprehensive service class designed to manage user onboarding for the Mingus personal finance application. It handles user profile creation, onboarding progress tracking, and provides a structured approach to collecting user financial and demographic information.

## Features

- **User Profile Management**: Create and manage detailed user profiles with financial and demographic data
- **Onboarding Progress Tracking**: Track user progress through onboarding steps
- **Step-by-Step Completion**: Manage completion status for individual onboarding steps
- **Response Storage**: Store user responses during the onboarding process
- **Database Integration**: Full SQLAlchemy ORM integration with PostgreSQL
- **Error Handling**: Comprehensive error handling and logging
- **Validation**: Input validation and data integrity checks

## Database Models

### UserProfile Model

The `UserProfile` model stores comprehensive user financial and demographic information:

```python
class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    # Core fields
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), unique=True)
    
    # Financial Information
    monthly_income = Column(Float)
    income_frequency = Column(String(50))
    primary_income_source = Column(String(100))
    secondary_income_source = Column(String(100))
    expense_categories = Column(Text)  # JSON string
    
    # Financial Goals
    primary_goal = Column(String(100))
    goal_amount = Column(Float)
    goal_timeline_months = Column(Integer)
    
    # Demographics
    age_range = Column(String(50))
    location_state = Column(String(50))
    location_city = Column(String(100))
    household_size = Column(Integer)
    employment_status = Column(String(50))
    
    # Financial Situation
    current_savings = Column(Float)
    current_debt = Column(Float)
    credit_score_range = Column(String(50))
    
    # Preferences
    risk_tolerance = Column(String(50))
    investment_experience = Column(String(50))
    
    # Metadata
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    is_complete = Column(Boolean, default=False)
```

### OnboardingProgress Model

The `OnboardingProgress` model tracks user progress through the onboarding process:

```python
class OnboardingProgress(Base):
    __tablename__ = 'onboarding_progress'
    
    # Core fields
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), unique=True)
    
    # Step tracking
    current_step = Column(String(100), default='welcome')
    total_steps = Column(Integer, default=5)
    completed_steps = Column(Integer, default=0)
    step_status = Column(Text)  # JSON string
    
    # Progress details
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    
    # Completion status
    is_complete = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)
    onboarding_responses = Column(Text)  # JSON string
```

## Service Methods

### Core Methods

#### 1. `create_user_profile(profile_data)`

Creates a new user profile with financial and demographic data.

**Parameters:**
- `profile_data` (Dict[str, Any]): Dictionary containing profile information

**Required fields:**
- `user_id`: User's ID

**Optional fields:**
- `monthly_income`: Monthly income amount
- `income_frequency`: Income frequency (monthly, bi-weekly, etc.)
- `primary_income_source`: Primary source of income
- `expense_categories`: Dictionary of expense categories
- `primary_goal`: Primary financial goal
- `goal_amount`: Goal amount
- `goal_timeline_months`: Timeline in months
- `age_range`: Age range category
- `location_state`: State location
- `location_city`: City location
- `household_size`: Number of people in household
- `employment_status`: Employment status
- `current_savings`: Current savings amount
- `current_debt`: Current debt amount
- `credit_score_range`: Credit score range
- `risk_tolerance`: Risk tolerance level
- `investment_experience`: Investment experience level

**Returns:**
- `Dict[str, Any]`: Created profile data or None if creation fails

**Example:**
```python
profile_data = {
    'user_id': 'user-123',
    'monthly_income': 5000.0,
    'income_frequency': 'monthly',
    'primary_income_source': 'salary',
    'age_range': '26-35',
    'location_state': 'CA',
    'location_city': 'San Francisco',
    'household_size': 2,
    'employment_status': 'employed',
    'current_savings': 10000.0,
    'current_debt': 5000.0,
    'credit_score_range': 'good'
}

profile = onboarding_service.create_user_profile(profile_data)
```

#### 2. `create_onboarding_record(onboarding_data)`

Creates a new onboarding progress tracking record.

**Parameters:**
- `onboarding_data` (Dict[str, Any]): Dictionary containing onboarding information

**Required fields:**
- `user_id`: User's ID

**Optional fields:**
- `current_step`: Current onboarding step (default: 'welcome')
- `total_steps`: Total number of steps (default: 5)
- `step_status`: Dictionary of step completion status
- `onboarding_responses`: Dictionary of user responses

**Returns:**
- `Dict[str, Any]`: Created onboarding record or None if creation fails

**Example:**
```python
onboarding_data = {
    'user_id': 'user-123',
    'current_step': 'welcome',
    'total_steps': 5
}

record = onboarding_service.create_onboarding_record(onboarding_data)
```

### Additional Methods

#### 3. `update_onboarding_progress(user_id, step_name, is_completed, responses)`

Updates onboarding progress for a specific step.

**Parameters:**
- `user_id` (str): User's ID
- `step_name` (str): Name of the step to update
- `is_completed` (bool): Whether the step is completed (default: True)
- `responses` (Dict[str, Any]): Additional responses for this step (optional)

**Returns:**
- `Dict[str, Any]`: Updated onboarding record or None if update fails

**Example:**
```python
# Mark profile step as completed
onboarding_service.update_onboarding_progress(
    user_id='user-123',
    step_name='profile',
    is_completed=True,
    responses={'income': 5000, 'location': 'CA'}
)
```

#### 4. `get_user_profile(user_id)`

Retrieves user profile by user ID.

**Parameters:**
- `user_id` (str): User's ID

**Returns:**
- `Dict[str, Any]`: User profile data or None if not found

#### 5. `get_onboarding_progress(user_id)`

Retrieves onboarding progress by user ID.

**Parameters:**
- `user_id` (str): User's ID

**Returns:**
- `Dict[str, Any]`: Onboarding progress data or None if not found

#### 6. `update_user_profile(user_id, update_data)`

Updates user profile information.

**Parameters:**
- `user_id` (str): User's ID
- `update_data` (Dict[str, Any]): Dictionary containing fields to update

**Returns:**
- `Dict[str, Any]`: Updated profile data or None if update fails

## Default Structures

### Default Profile Structure

The service provides a default profile structure for new users:

```python
{
    'monthly_income': None,
    'income_frequency': None,
    'primary_income_source': None,
    'secondary_income_source': None,
    'expense_categories': {
        'housing': 0,
        'transportation': 0,
        'food': 0,
        'utilities': 0,
        'healthcare': 0,
        'entertainment': 0,
        'shopping': 0,
        'debt_payments': 0,
        'savings': 0,
        'other': 0
    },
    'primary_goal': None,
    'goal_amount': None,
    'goal_timeline_months': None,
    'age_range': None,
    'location_state': None,
    'location_city': None,
    'household_size': None,
    'employment_status': None,
    'current_savings': None,
    'current_debt': None,
    'credit_score_range': None,
    'risk_tolerance': None,
    'investment_experience': None,
    'is_complete': False
}
```

### Default Onboarding Structure

The service provides a default onboarding structure:

```python
{
    'current_step': 'welcome',
    'total_steps': 5,
    'completed_steps': 0,
    'step_status': {
        'welcome': {'completed': False, 'completed_at': None},
        'profile': {'completed': False, 'completed_at': None},
        'goals': {'completed': False, 'completed_at': None},
        'preferences': {'completed': False, 'completed_at': None},
        'complete': {'completed': False, 'completed_at': None}
    },
    'is_complete': False,
    'completion_percentage': 0,
    'onboarding_responses': {}
}
```

## Onboarding Steps

The service supports a 5-step onboarding process:

1. **Welcome**: Initial welcome and introduction
2. **Profile**: Basic demographic and financial information
3. **Goals**: Financial goals and objectives
4. **Preferences**: Risk tolerance and investment preferences
5. **Complete**: Onboarding completion

## Integration with Flask

### Basic Setup

```python
from flask import Flask
from backend.services.onboarding_service import OnboardingService

app = Flask(__name__)

# Initialize service
DATABASE_URL = 'postgresql://username:password@localhost/mingus_db'
onboarding_service = OnboardingService(None, DATABASE_URL)
```

### Example Routes

```python
@app.route('/api/onboarding/start', methods=['POST'])
def start_onboarding():
    data = request.get_json()
    user_id = data.get('user_id')
    
    # Create onboarding record
    onboarding_record = onboarding_service.create_onboarding_record({
        'user_id': user_id,
        'current_step': 'welcome'
    })
    
    return jsonify({'success': True, 'onboarding_record': onboarding_record})

@app.route('/api/onboarding/profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    user_id = data.get('user_id')
    
    # Create user profile
    profile = onboarding_service.create_user_profile({
        'user_id': user_id,
        'monthly_income': data.get('monthly_income'),
        'age_range': data.get('age_range'),
        # ... other fields
    })
    
    # Update progress
    onboarding_service.update_onboarding_progress(
        user_id=user_id,
        step_name='profile',
        is_completed=True,
        responses=data
    )
    
    return jsonify({'success': True, 'profile': profile})
```

## Error Handling

The service includes comprehensive error handling:

- **Database Errors**: Handles SQLAlchemy errors gracefully
- **Validation Errors**: Validates required fields and data types
- **Duplicate Records**: Prevents creation of duplicate profiles/records
- **Logging**: Detailed logging for debugging and monitoring

## Database Migrations

Run the following SQL scripts to create the required tables:

1. `migrations/20250618_create_users_table.sql`
2. `migrations/20250618_create_user_profiles_table.sql`
3. `migrations/20250618_create_onboarding_progress_table.sql`

## Best Practices

1. **Always validate user input** before passing to service methods
2. **Handle service method returns** - they may return None on failure
3. **Use transactions** for operations that modify multiple records
4. **Log errors** for debugging and monitoring
5. **Validate user existence** before creating profiles/records
6. **Use appropriate HTTP status codes** in API responses

## Testing

The service can be tested using the provided example integration file:

```bash
python examples/onboarding_service_integration.py
```

This will start a Flask development server with all the onboarding endpoints available for testing. 