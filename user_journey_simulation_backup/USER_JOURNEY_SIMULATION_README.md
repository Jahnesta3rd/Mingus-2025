# MINGUS User Journey Simulation

## Overview

This comprehensive user journey simulation tests the complete MINGUS application experience from initial discovery through monthly reporting. The simulation validates all major user flows, subscription tiers, feature access controls, and integration points.

## 🎯 User Journey Steps

The simulation covers 8 complete user journey steps:

### 1. **App Discovery**
- Landing page accessibility
- Assessment landing page
- Available assessments listing
- Initial user engagement

### 2. **Budget Tier Signup ($10)**
- User registration
- Budget tier subscription creation
- Tier access verification
- Basic feature availability

### 3. **Profile Setup with Income/Expenses**
- Complete profile creation
- Income and expense data entry
- Financial questionnaire completion
- Onboarding completion
- Profile data validation

### 4. **First Weekly Check-in**
- Health check-in form access
- Weekly health data submission
- Check-in history verification
- Health status tracking
- Health statistics generation

### 5. **Financial Forecast Review**
- Cash flow forecast generation
- Financial analysis access
- Spending patterns analysis
- Budget variance calculation
- Financial insights (Budget tier limited)

### 6. **Mid-Tier Upgrade ($20)**
- Upgrade options display
- Subscription upgrade process
- New tier access verification
- Enhanced features availability
- Career risk management access

### 7. **Career Recommendations**
- Job recommendations generation
- Salary analysis
- Career advancement strategy
- Skill gap analysis
- Career risk management (Mid-tier feature)

### 8. **Monthly Report Review**
- Monthly report generation
- Report retrieval and display
- Report analytics
- Report insights
- Report recommendations
- Report download functionality

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **MINGUS application** running (default: http://localhost:5001)
3. **Dependencies** installed

### Installation

```bash
# Install dependencies
pip install -r requirements-user-journey-simulation.txt

# Make scripts executable
chmod +x user_journey_simulation.py
chmod +x run_user_journey_tests.py
```

### Running the Simulation

#### Complete Journey Test
```bash
# Run all 8 steps
python user_journey_simulation.py

# With custom URL
python user_journey_simulation.py --url http://localhost:5002

# Save results to file
python user_journey_simulation.py --output results.json
```

#### Individual Step Testing
```bash
# Run specific steps
python run_user_journey_tests.py --step 1,2,3

# Run single step
python run_user_journey_tests.py --step 4

# Run all steps
python run_user_journey_tests.py --step all
```

## 📊 Test Coverage

### Authentication & User Management
- ✅ User registration
- ✅ Session management
- ✅ Profile creation and updates
- ✅ Data validation

### Subscription System
- ✅ Budget tier ($10) signup
- ✅ Mid-tier ($20) upgrade
- ✅ Tier access verification
- ✅ Feature gating

### Onboarding Flow
- ✅ Profile setup
- ✅ Income/expense entry
- ✅ Financial questionnaire
- ✅ Onboarding completion

### Health & Wellness
- ✅ Weekly check-in form
- ✅ Health data submission
- ✅ Health statistics
- ✅ Health-finance correlations

### Financial Features
- ✅ Cash flow forecasting
- ✅ Financial analysis
- ✅ Spending patterns
- ✅ Budget variance
- ✅ Financial insights

### Career Features
- ✅ Job recommendations
- ✅ Salary analysis
- ✅ Career strategy
- ✅ Skill gap analysis
- ✅ Risk management (Mid-tier)

### Reporting System
- ✅ Monthly report generation
- ✅ Report analytics
- ✅ Report insights
- ✅ Report recommendations
- ✅ Report download

## 🔧 Configuration

### Environment Variables
```bash
# Application URL
MINGUS_BASE_URL=http://localhost:5001

# Test user credentials
TEST_USER_EMAIL=testuser@example.com
TEST_USER_PASSWORD=TestPassword123!
```

### Custom Test Data
Modify the test data in `user_journey_simulation.py`:

```python
self.test_user = {
    "email": "your-test-email@example.com",
    "password": "YourTestPassword123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "555-123-4567"
}

self.profile_data = {
    "monthly_income": 75000,
    "income_frequency": "monthly",
    # ... other profile fields
}
```

## 📈 Expected Results

### Successful Journey
When all steps pass, you should see:
```
============================================================
SIMULATION SUMMARY
============================================================
Overall Status: PASS
Test User: testuser_1234567890@example.com

Step Results:
  Step 1: App Discovery: PASS
  Step 2: Budget Tier Signup: PASS
  Step 3: Profile Setup: PASS
  Step 4: Weekly Check-in: PASS
  Step 5: Financial Forecast: PASS
  Step 6: Mid-Tier Upgrade: PASS
  Step 7: Career Recommendations: PASS
  Step 8: Monthly Report: PASS
```

### Common Issues & Solutions

#### Connection Errors
```
Error: Application health check failed
```
**Solution**: Ensure the MINGUS application is running on the specified URL.

#### Authentication Errors
```
Status code: 401, Response: Unauthorized
```
**Solution**: Check authentication endpoints and session management.

#### Missing Endpoints
```
Status code: 404, Response: Not Found
```
**Solution**: Verify API endpoints are implemented and accessible.

#### Subscription Errors
```
Status code: 400, Response: Invalid subscription data
```
**Solution**: Check subscription tier configuration and Stripe integration.

## 🧪 Testing Scenarios

### Scenario 1: New User Journey
```bash
python run_user_journey_tests.py --step 1,2,3
```
Tests the complete onboarding experience for new users.

### Scenario 2: Feature Access Testing
```bash
python run_user_journey_tests.py --step 2,6,7
```
Tests subscription upgrades and feature access controls.

### Scenario 3: Health & Finance Integration
```bash
python run_user_journey_tests.py --step 4,5
```
Tests the unique health-finance correlation features.

### Scenario 4: Reporting & Analytics
```bash
python run_user_journey_tests.py --step 8
```
Tests the comprehensive reporting system.

## 📝 Logging

The simulation generates detailed logs:

- **Console Output**: Real-time test progress
- **Log File**: `user_journey_simulation.log`
- **JSON Results**: Detailed test results (if --output specified)

### Log Levels
- **INFO**: Test progress and results
- **ERROR**: Test failures and exceptions
- **DEBUG**: Detailed API interactions (with --verbose)

## 🔍 Debugging

### Enable Verbose Logging
```bash
python run_user_journey_tests.py --verbose
```

### Test Individual Components
```bash
# Test only authentication
python run_user_journey_tests.py --step 2

# Test only health features
python run_user_journey_tests.py --step 4

# Test only financial features
python run_user_journey_tests.py --step 5
```

### API Endpoint Testing
The simulation tests these key endpoints:

```
GET  /health                           # Health check
GET  /                                 # Landing page
GET  /assessments                      # Assessment landing
GET  /api/assessments/available        # Available assessments
POST /api/auth/signup                  # User registration
POST /api/subscriptions/create         # Subscription creation
GET  /api/subscriptions/tier-access    # Tier access verification
POST /api/onboarding/profile           # Profile creation
POST /api/onboarding/expenses          # Expenses setup
POST /api/onboarding/financial-questionnaire  # Financial questionnaire
POST /api/onboarding/complete          # Onboarding completion
GET  /api/user/profile                 # Profile retrieval
GET  /api/health/checkin               # Health check-in form
POST /api/health/checkin               # Health check-in submission
GET  /api/health/checkin/history       # Check-in history
GET  /api/health/status                # Health status
GET  /api/health/stats                 # Health statistics
POST /forecast                         # Cash flow forecast
GET  /api/financial/analysis           # Financial analysis
GET  /api/financial/spending-patterns  # Spending patterns
GET  /api/financial/budget-variance    # Budget variance
GET  /api/financial/insights           # Financial insights
GET  /api/subscriptions/upgrade-options # Upgrade options
POST /api/subscriptions/upgrade        # Subscription upgrade
GET  /api/features/available           # Available features
POST /api/career/job-recommendations   # Job recommendations
GET  /api/career/salary-analysis       # Salary analysis
POST /api/career/advancement-strategy  # Career strategy
GET  /api/career/skill-gaps            # Skill gap analysis
GET  /api/career/risk-management       # Career risk management
POST /api/reports/generate             # Report generation
GET  /api/reports/{id}                 # Report retrieval
GET  /api/reports/{id}/analytics       # Report analytics
GET  /api/reports/{id}/insights        # Report insights
GET  /api/reports/{id}/recommendations # Report recommendations
GET  /api/reports/{id}/download        # Report download
```

## 📊 Performance Metrics

The simulation tracks:
- **Response Times**: API endpoint performance
- **Success Rates**: Test step completion rates
- **Error Patterns**: Common failure points
- **Feature Coverage**: Endpoint accessibility

## 🤝 Contributing

To add new test scenarios:

1. **Add new test methods** to `MingusUserJourneySimulator`
2. **Update step mapping** in `run_user_journey_tests.py`
3. **Add test data** for new scenarios
4. **Update documentation** with new test cases

## 📄 License

This simulation is part of the MINGUS application testing suite.

## 🆘 Support

For issues with the simulation:
1. Check the application is running
2. Verify API endpoints are accessible
3. Review log files for detailed error information
4. Test individual steps to isolate issues
