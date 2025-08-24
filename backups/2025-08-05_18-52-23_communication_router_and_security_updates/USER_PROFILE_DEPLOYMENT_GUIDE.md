# User Profile Features Deployment Guide

## Overview
This guide covers the deployment of user profile features for the Mingus application.

## Prerequisites
- Flask application running
- Database configured and accessible
- Frontend build system ready

## Database Setup

### 1. Apply Migrations
```bash
# Apply user profile migrations
python apply_user_profile_migrations.py

# Or manually apply migrations
psql -d your_database -f migrations/003_add_missing_profile_fields.sql
psql -d your_database -f migrations/012_add_comprehensive_user_fields.sql
```

### 2. Verify Database Schema
```sql
-- Check if user_profiles table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'user_profiles'
);

-- Check if key columns exist in users table
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('first_name', 'last_name', 'zip_code', 'dependents_count');
```

## Backend Setup

### 1. Verify Routes
The following routes should be available:
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/onboarding/status` - Get onboarding status
- `POST /api/onboarding/step/<step>` - Complete onboarding step
- `POST /api/onboarding/complete` - Complete onboarding

### 2. Verify Services
The following services should be available:
- `UserProfileService` - Manages user profiles
- `OnboardingService` - Manages onboarding flow

## Frontend Setup

### 1. Verify Components
The following components should be available:
- `pages/onboarding.tsx` - Onboarding page
- `components/onboarding/OnboardingFlow.tsx` - Onboarding flow component
- `store/userStore.ts` - User state management

### 2. Test User Flow
1. Navigate to `/onboarding`
2. Complete profile information
3. Verify data persistence
4. Check profile completion percentage

## Testing

### 1. Run Integration Test
```bash
python test_user_profile_integration.py
```

### 2. Manual Testing
1. Start the Flask application
2. Open browser to onboarding page
3. Complete the onboarding flow
4. Verify data is saved correctly

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify DATABASE_URL is set correctly
   - Check database server is running
   - Verify user permissions

2. **Migration Errors**
   - Check if migrations were applied successfully
   - Verify database schema matches expectations
   - Check migration logs

3. **API Endpoint Errors**
   - Verify blueprints are registered
   - Check route definitions
   - Verify service implementations

4. **Frontend Errors**
   - Check component imports
   - Verify store configuration
   - Check API endpoint URLs

## Success Criteria

✅ Database migrations applied successfully
✅ Backend API endpoints responding correctly
✅ Frontend components loading without errors
✅ User profile data persisting correctly
✅ Onboarding flow completing successfully
✅ Profile completion percentage calculating correctly

## Next Steps

After successful deployment:
1. Monitor user onboarding completion rates
2. Track profile completion percentages
3. Gather user feedback on onboarding experience
4. Optimize flow based on user behavior
