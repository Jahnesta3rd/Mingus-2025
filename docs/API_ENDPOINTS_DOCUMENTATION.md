# API Endpoints Documentation

## Overview

This document describes the API endpoints for the MINGUS user profile and onboarding system. All endpoints follow RESTful conventions and return JSON responses.

## Base URL

```
https://api.mingus.com/v1
```

## Authentication

All endpoints require authentication via one of the following methods:

- **Bearer Token**: `Authorization: Bearer <token>`
- **Session Cookie**: `sessionToken` cookie

## Common Response Format

All endpoints return responses in the following format:

```json
{
  "success": boolean,
  "message": string,
  "data"?: any,
  "errors"?: Array<{
    "field": string,
    "message": string,
    "code": string
  }>
}
```

## User Profile Endpoints

### GET /api/user/profile

Retrieves the current user's profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Profile retrieved successfully",
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1990-01-01",
    "zipCode": "12345",
    "phoneNumber": "+1234567890",
    "monthlyIncome": 5000,
    "incomeFrequency": "monthly",
    "profileCompletionPercentage": 75,
    "onboardingStep": 5,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  },
  "analytics": {
    "completionPercentage": 75,
    "completedFields": 19,
    "totalFields": 25,
    "missingFields": ["wellnessGoals", "stressLevelBaseline", "healthCheckinFrequency"],
    "categoryCompletions": {
      "personal": 100,
      "financial": 80,
      "demographics": 60,
      "goals": 100,
      "wellness": 0
    }
  }
}
```

### PATCH /api/user/profile

Updates the user's profile information.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": {
    "firstName": "John",
    "lastName": "Doe",
    "monthlyIncome": 5500,
    "riskToleranceLevel": "moderate"
  },
  "onboardingStep": 6,
  "profileCompletionPercentage": 80
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": "user-123",
    "firstName": "John",
    "lastName": "Doe",
    "monthlyIncome": 5500,
    "riskToleranceLevel": "moderate",
    "onboardingStep": 6,
    "profileCompletionPercentage": 80,
    "updatedAt": "2024-01-15T10:35:00Z"
  },
  "analytics": {
    "completionPercentage": 80,
    "completedFields": 20,
    "totalFields": 25,
    "missingFields": ["wellnessGoals", "stressLevelBaseline", "healthCheckinFrequency"],
    "categoryCompletions": {
      "personal": 100,
      "financial": 100,
      "demographics": 60,
      "goals": 100,
      "wellness": 0
    }
  }
}
```

### POST /api/user/profile

Creates a new user profile.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": {
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane@example.com",
    "dateOfBirth": "1985-05-15",
    "zipCode": "54321",
    "monthlyIncome": 6000,
    "incomeFrequency": "monthly"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile created successfully",
  "user": {
    "id": "user-456",
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane@example.com",
    "dateOfBirth": "1985-05-15",
    "zipCode": "54321",
    "monthlyIncome": 6000,
    "incomeFrequency": "monthly",
    "profileCompletionPercentage": 0,
    "onboardingStep": 1,
    "createdAt": "2024-01-15T10:40:00Z",
    "updatedAt": "2024-01-15T10:40:00Z"
  },
  "analytics": {
    "completionPercentage": 24,
    "completedFields": 6,
    "totalFields": 25,
    "missingFields": ["phoneNumber", "primaryIncomeSource", "currentSavingsBalance"],
    "categoryCompletions": {
      "personal": 60,
      "financial": 40,
      "demographics": 0,
      "goals": 0,
      "wellness": 0
    }
  }
}
```

## Onboarding Progress Endpoints

### GET /api/user/onboarding-progress

Retrieves the user's onboarding progress.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Progress retrieved successfully",
  "progress": {
    "currentStep": 3,
    "completedSteps": [1, 2],
    "totalSteps": 10,
    "completionPercentage": 20
  },
  "analytics": {
    "completionPercentage": 45,
    "completedFields": 11,
    "totalFields": 25,
    "missingFields": ["wellnessGoals", "stressLevelBaseline"],
    "categoryCompletions": {
      "personal": 100,
      "financial": 80,
      "demographics": 40,
      "goals": 0,
      "wellness": 0
    },
    "nextRecommendedFields": ["primaryFinancialGoal", "riskToleranceLevel", "financialKnowledgeLevel"]
  }
}
```

### POST /api/user/onboarding-progress

Saves the user's onboarding progress.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "currentStep": 4,
  "completedSteps": [1, 2, 3],
  "userData": {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "monthlyIncome": 5000,
    "incomeFrequency": "monthly",
    "primaryIncomeSource": "full-time-employment",
    "currentSavingsBalance": 10000
  },
  "profileCompletionPercentage": 50
}
```

**Response:**
```json
{
  "success": true,
  "message": "Progress saved successfully",
  "progress": {
    "currentStep": 4,
    "completedSteps": [1, 2, 3],
    "totalSteps": 10,
    "completionPercentage": 30
  },
  "analytics": {
    "completionPercentage": 50,
    "completedFields": 12,
    "totalFields": 25,
    "missingFields": ["wellnessGoals", "stressLevelBaseline"],
    "categoryCompletions": {
      "personal": 100,
      "financial": 80,
      "demographics": 40,
      "goals": 0,
      "wellness": 0
    },
    "nextRecommendedFields": ["primaryFinancialGoal", "riskToleranceLevel", "financialKnowledgeLevel"]
  }
}
```

### DELETE /api/user/onboarding-progress

Clears the user's onboarding progress.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Progress cleared successfully"
}
```

## Error Responses

### Validation Error (400)
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format",
      "code": "VALIDATION_ERROR"
    },
    {
      "field": "monthlyIncome",
      "message": "Monthly income must be between $0 and $999,999",
      "code": "OUT_OF_RANGE"
    }
  ]
}
```

### Unauthorized (401)
```json
{
  "success": false,
  "message": "Unauthorized"
}
```

### Not Found (404)
```json
{
  "success": false,
  "message": "Profile not found"
}
```

### Conflict (409)
```json
{
  "success": false,
  "message": "Profile already exists",
  "errors": [
    {
      "field": "email",
      "message": "A profile with this email already exists",
      "code": "DUPLICATE_EMAIL"
    }
  ]
}
```

### Internal Server Error (500)
```json
{
  "success": false,
  "message": "Internal server error"
}
```

## Data Models

### UserProfile
```typescript
interface UserProfile {
  // Authentication & Profile
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  dateOfBirth?: Date;
  zipCode?: string;
  phoneNumber?: string;
  emailVerificationStatus: boolean;

  // Financial Data
  monthlyIncome?: number;
  incomeFrequency?: 'weekly' | 'bi-weekly' | 'semi-monthly' | 'monthly' | 'annually';
  primaryIncomeSource?: string;
  currentSavingsBalance?: number;
  totalDebtAmount?: number;
  creditScoreRange?: 'excellent' | 'good' | 'fair' | 'poor' | 'very_poor' | 'unknown';
  employmentStatus?: string;

  // Demographics
  ageRange?: '18-24' | '25-34' | '35-44' | '45-54' | '55-64' | '65+';
  maritalStatus?: 'single' | 'married' | 'partnership' | 'divorced' | 'widowed' | 'prefer_not_to_say';
  dependentsCount?: number;
  householdSize?: number;
  educationLevel?: string;
  occupation?: string;
  industry?: string;
  yearsOfExperience?: 'less_than_1' | '1-3' | '4-7' | '8-12' | '13-20' | '20+';

  // Goals & Preferences
  primaryFinancialGoal?: string;
  riskToleranceLevel?: 'conservative' | 'moderate' | 'aggressive' | 'unsure';
  financialKnowledgeLevel?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  preferredContactMethod?: string;
  notificationPreferences?: NotificationPreferences;

  // Health & Wellness
  healthCheckinFrequency?: 'daily' | 'weekly' | 'monthly' | 'on_demand' | 'never';
  stressLevelBaseline?: number;
  wellnessGoals?: string[];

  // Meta
  profileCompletionPercentage: number;
  onboardingStep: number;
  gdprConsentStatus: boolean;
  dataSharingPreferences?: string;
  createdAt: Date;
  updatedAt: Date;
}
```

### NotificationPreferences
```typescript
interface NotificationPreferences {
  weeklyInsights: boolean;
  monthlySpendingSummaries: boolean;
  goalProgressUpdates: boolean;
  billPaymentReminders: boolean;
  marketUpdates: boolean;
  educationalContent: boolean;
  productUpdates: boolean;
}
```

## Rate Limiting

- **Profile endpoints**: 100 requests per minute per user
- **Progress endpoints**: 200 requests per minute per user

## Analytics Events

The API automatically tracks the following events:

- `profile_created` - When a new profile is created
- `profile_updated` - When a profile is updated
- `progress_saved` - When onboarding progress is saved
- `progress_cleared` - When onboarding progress is cleared

## Implementation Notes

### Database Integration

Replace the mock database functions in the API endpoints with your actual database operations:

```typescript
// Replace mock functions with real database calls
async function getUserProfile(userId: string): Promise<Partial<UserProfile> | null> {
  return await db.users.findUnique({ where: { id: userId } });
}

async function updateUserProfile(userId: string, data: Partial<UserProfileUpdate>): Promise<Partial<UserProfile>> {
  return await db.users.update({ 
    where: { id: userId }, 
    data: { ...data, updatedAt: new Date() } 
  });
}
```

### Authentication Integration

Replace the mock authentication with your actual auth system:

```typescript
// Replace with your actual JWT verification
async function verifyToken(token: string): Promise<UserSession | null> {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!);
    return decoded as UserSession;
  } catch (error) {
    return null;
  }
}
```

### Analytics Integration

Replace the mock analytics logging with your actual analytics system:

```typescript
// Replace with your actual analytics tracking
async function logProfileUpdate(userId: string, data: any) {
  await analytics.track('profile_updated', { 
    userId, 
    ...data,
    timestamp: new Date().toISOString()
  });
}
```

## Testing

Use the provided test endpoints to verify your implementation:

```bash
# Test profile retrieval
curl -H "Authorization: Bearer <token>" \
  https://api.mingus.com/v1/api/user/profile

# Test profile update
curl -X PATCH \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"data":{"firstName":"John","lastName":"Doe"}}' \
  https://api.mingus.com/v1/api/user/profile

# Test progress save
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"currentStep":2,"completedSteps":[1],"userData":{"firstName":"John"}}' \
  https://api.mingus.com/v1/api/user/onboarding-progress
``` 