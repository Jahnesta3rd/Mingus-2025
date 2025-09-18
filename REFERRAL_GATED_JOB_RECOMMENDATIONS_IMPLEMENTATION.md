# Referral-Gated Job Recommendation System Implementation

## Overview

This implementation extends the existing Mingus Flask application with a comprehensive job recommendation system that uses referral-based access control. Users must complete 3 successful referrals to unlock premium job recommendation features.

## Features Implemented

### 🔐 Referral-Gated Access Control
- **Referral System**: Complete referral tracking with 3-referral unlock requirement
- **Feature Access Control**: Secure access checking before allowing job recommendations
- **Progress Tracking**: Real-time progress updates (0/3, 1/3, 2/3, 3/3)
- **Alternative Unlock**: Premium upgrade and trial options for non-referral users

### 🎯 Job Recommendation Engine
- **AI-Powered Matching**: Advanced job matching based on resume analysis
- **Salary Insights**: Discover opportunities for 20-50% salary increases
- **Location Intelligence**: ZIP code validation and commute analysis
- **Company Insights**: Culture, benefits, and growth opportunity analysis

### 📍 Location Services
- **ZIP Code Validation**: US ZIP code format validation and geocoding
- **Location Preferences**: Search radius and commute preference settings
- **Cost of Living Integration**: Location-based salary adjustments
- **Commute Analysis**: Distance and time estimation between locations

### 🔒 Security Features
- **Fraud Prevention**: Referral fraud detection and prevention
- **Rate Limiting**: API rate limiting for all endpoints
- **File Upload Security**: Secure resume upload with validation
- **Access Control**: Comprehensive access control for premium features

### 🎨 User Experience
- **Teaser Pages**: Compelling preview of locked features
- **Progress Visualization**: Beautiful progress bars and unlock tracking
- **Mobile Responsive**: Fully responsive design for all devices
- **Success Stories**: Social proof and motivation for referrals

## File Structure

```
backend/
├── models/
│   └── referral_models.py              # Referral system database models
├── forms/
│   └── referral_forms.py               # Enhanced form classes
├── api/
│   └── referral_gated_endpoints.py     # Main API endpoints
├── utils/
│   └── location_utils.py               # Location validation and geocoding
├── security/
│   └── referral_security.py            # Security and fraud prevention
└── integration/
    └── mingus_integration.py           # Integration with existing features

templates/
├── career_advancement_teaser.html      # Feature teaser page
└── job_recommendations.html            # Job recommendations interface

app.py                                  # Updated main application
```

## API Endpoints

### Public Access Routes
- `GET /career-preview` - Compelling preview of job recommendation feature
- `POST /refer-friend` - Send referral invitations
- `GET /referral-status/<referral_code>` - Track individual referral success

### Referral-Gated Routes
- `GET /career-advancement` - Feature teaser page with unlock requirements
- `GET /api/feature-access/job-recommendations` - Check if user has unlocked feature
- `POST /upload-resume` - Secure resume upload (REFERRAL-GATED)
- `POST /set-location-preferences` - Location preferences (REFERRAL-GATED)
- `POST /process-recommendations` - Trigger recommendation engine (REFERRAL-GATED)
- `GET /referral-progress` - Show user's progress toward unlock

### Utility Routes
- `POST /validate-zipcode` - Validate ZIP code and return location data
- `POST /location-recommendations` - Get location-based job recommendations

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referral_code TEXT UNIQUE,
    referred_by TEXT,
    referral_count INTEGER DEFAULT 0,
    successful_referrals INTEGER DEFAULT 0,
    feature_unlocked BOOLEAN DEFAULT FALSE,
    unlock_date TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Referrals Table
```sql
CREATE TABLE referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_user_id TEXT NOT NULL,
    referred_email TEXT NOT NULL,
    referral_code TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    validated_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (referrer_user_id) REFERENCES users (user_id)
);
```

### Feature Access Table
```sql
CREATE TABLE feature_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    unlocked BOOLEAN DEFAULT FALSE,
    unlock_method TEXT,
    unlock_date TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE(user_id, feature_name)
);
```

## Security Features

### Referral Fraud Prevention
- **Duplicate IP Detection**: Prevents multiple referrals from same IP
- **Rapid Referral Detection**: Flags suspicious rapid referral patterns
- **Email Pattern Analysis**: Detects suspicious email addresses
- **Self-Referral Prevention**: Blocks attempts to refer oneself

### File Upload Security
- **File Type Validation**: Only allows PDF, DOC, DOCX files
- **File Size Limits**: Maximum 10MB file size
- **Content Scanning**: Basic executable file detection
- **Secure Storage**: Files stored in protected directory

### Access Control
- **Feature Gating**: All premium features require referral unlock
- **Rate Limiting**: API rate limiting on all endpoints
- **IP Blocking**: Ability to block suspicious IP addresses
- **User Blocking**: Account suspension capabilities

## Integration with Existing Mingus Features

### Financial Planning Integration
- **Salary Impact Analysis**: Calculate potential financial impact of job changes
- **Budget Forecasting**: Update budget projections with new salary
- **Debt Payoff Acceleration**: Calculate faster debt payoff with salary increase
- **Savings Goal Updates**: Adjust savings goals based on new income

### Goal Setting Integration
- **Career Goal Alignment**: Match job recommendations with user goals
- **Progress Tracking**: Track progress toward career goals
- **Goal-Based Recommendations**: Generate recommendations based on goals
- **Milestone Celebration**: Celebrate goal achievements

### Analytics Integration
- **Unlock Tracking**: Track feature unlock events and methods
- **Engagement Metrics**: Monitor user engagement with new features
- **Referral Analytics**: Analyze referral program effectiveness
- **Feature Usage**: Track usage of unlocked features

## Usage Examples

### Creating a User with Referral
```python
from backend.models.referral_models import ReferralSystem

referral_system = ReferralSystem()

# Create user with referral
result = referral_system.create_user(
    user_id="user123",
    email="user@example.com",
    first_name="John",
    last_name="Doe",
    referred_by="referrer456"
)
```

### Checking Feature Access
```python
# Check if user has unlocked job recommendations
access_check = referral_system.check_feature_access("user123", "job_recommendations")

if access_check['unlocked']:
    # User has access, proceed with job recommendations
    pass
else:
    # Redirect to teaser page
    referrals_needed = access_check['referrals_needed']
    print(f"Need {referrals_needed} more referrals")
```

### Processing Job Recommendations
```python
from backend.api.referral_gated_endpoints import process_recommendations

# This endpoint is protected by @require_referral_unlock decorator
response = requests.post('/process-recommendations', 
    headers={'X-User-ID': 'user123', 'X-CSRF-Token': 'test-token'},
    json={
        'current_salary': 75000,
        'target_salary_increase': 0.25,
        'career_field': 'technology',
        'experience_level': 'mid'
    }
)
```

## Configuration

### Environment Variables
```bash
# Required for production
SECRET_KEY=your-secret-key
CSRF_SECRET_KEY=your-csrf-secret-key
ENCRYPTION_KEY=your-encryption-key

# Optional
RATE_LIMIT_PER_MINUTE=100
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_ENV=development
```

### Database Configuration
The system uses SQLite databases by default:
- `referral_system.db` - Referral system data
- `user_profiles.db` - User profile data (existing)
- `app.db` - Application data (existing)

## Deployment

### Prerequisites
- Python 3.8+
- Flask
- SQLite3
- Required Python packages (see requirements.txt)

### Installation
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export SECRET_KEY="your-secret-key"
export CSRF_SECRET_KEY="your-csrf-secret-key"
```

3. Run the application:
```bash
python app.py
```

### Production Considerations
- Use PostgreSQL instead of SQLite for production
- Implement proper JWT authentication
- Use Redis for rate limiting
- Set up proper logging and monitoring
- Configure HTTPS and security headers
- Implement proper file storage (AWS S3, etc.)

## Testing

### Unit Tests
```bash
# Run referral system tests
python -m pytest tests/test_referral_system.py

# Run location utility tests
python -m pytest tests/test_location_utils.py

# Run security tests
python -m pytest tests/test_referral_security.py
```

### Integration Tests
```bash
# Run full integration tests
python -m pytest tests/test_integration.py
```

## Monitoring and Analytics

### Key Metrics to Track
- **Referral Conversion Rate**: Percentage of referrals that complete signup
- **Feature Unlock Rate**: Percentage of users who unlock features
- **Job Application Rate**: Percentage of users who apply to recommended jobs
- **User Engagement**: Time spent in job recommendation features
- **Fraud Detection**: Number of blocked fraudulent referrals

### Logging
All security events and user actions are logged for monitoring:
- Referral attempts and completions
- Feature unlock events
- Security violations
- API usage patterns

## Future Enhancements

### Planned Features
- **Advanced AI Matching**: Machine learning-based job matching
- **Company Reviews Integration**: Glassdoor/Indeed review integration
- **Application Tracking**: Track job application progress
- **Interview Preparation**: AI-powered interview prep tools
- **Salary Negotiation**: Negotiation tips and tools

### Scalability Improvements
- **Microservices Architecture**: Split into separate services
- **Caching Layer**: Redis for improved performance
- **CDN Integration**: For static assets and file uploads
- **Load Balancing**: For high-traffic scenarios

## Support and Maintenance

### Regular Maintenance Tasks
- Monitor fraud detection metrics
- Update job recommendation algorithms
- Review and update security measures
- Analyze user engagement data
- Optimize database performance

### Troubleshooting
Common issues and solutions are documented in the troubleshooting guide:
- Database connection issues
- File upload problems
- Referral validation errors
- Security false positives

## Conclusion

This implementation provides a comprehensive referral-gated job recommendation system that integrates seamlessly with the existing Mingus application. The system includes robust security features, user-friendly interfaces, and comprehensive analytics to ensure a successful user experience while maintaining the integrity of the referral program.

The modular design allows for easy extension and customization, while the security features protect against fraud and abuse. The integration with existing Mingus features provides a cohesive user experience that encourages both referral participation and feature usage.
