# Mingus Application - Complete API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [API Endpoints](#api-endpoints)
   - [System & Health](#system--health)
   - [Assessments](#assessments)
   - [Memes](#memes)
   - [User Preferences](#user-preferences)
   - [Profiles](#profiles)
   - [Resume Parsing](#resume-parsing)
   - [Job Matching](#job-matching)
   - [Three-Tier Recommendations](#three-tier-recommendations)
   - [Recommendation Engine](#recommendation-engine)
   - [Referral-Gated Features](#referral-gated-features)
   - [Risk Analytics](#risk-analytics)
   - [Vehicle Management](#vehicle-management)
   - [Weekly Check-in](#weekly-check-in)
   - [Career-Vehicle Optimization](#career-vehicle-optimization)
   - [Housing](#housing)
   - [Daily Outlook](#daily-outlook)
   - [Professional Tier](#professional-tier)
   - [Tax Adjacent Features](#tax-adjacent-features)
   - [Business Integrations](#business-integrations)
   - [Subscription Management](#subscription-management)
   - [External APIs](#external-apis)
   - [Dashboard & Monitoring](#dashboard--monitoring)
   - [Gamification](#gamification)
   - [Notifications](#notifications)
   - [Analytics](#analytics)

---

## Overview

The Mingus Application API provides a comprehensive RESTful interface for personal finance management, career advancement, vehicle management, and wellness tracking. All endpoints return JSON responses and follow standard HTTP status codes.

**API Version:** 1.0.0  
**Last Updated:** 2024

---

## Base URL

```
Development: http://localhost:5001
Production: https://mingusapp.com
```

---

## Authentication

Most endpoints require authentication. Include authentication credentials in request headers:

```
X-User-ID: <user_id>
X-CSRF-Token: <csrf_token>
Authorization: Bearer <token>
```

Some endpoints may use session-based authentication or API keys depending on the feature tier.

---

## Rate Limiting

Rate limiting is enforced per IP address:
- **Default:** 100 requests per minute
- **Strict endpoints:** 20 requests per minute
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

When rate limit is exceeded, a `429 Too Many Requests` response is returned.

---

## Error Handling

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Error message",
  "status_code": 400
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## API Endpoints

### System & Health

#### GET /health
Health check endpoint (public, no auth required)

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis_sessions": "active",
    "query_cache": "active"
  }
}
```

#### GET /api/status
API status and endpoint listing (public)

**Response:**
```json
{
  "status": "operational",
  "endpoints": {
    "assessments": {...},
    "memes": {...},
    "vehicle_management": {...}
  }
}
```

---

### Assessments

#### POST /api/assessments
Submit a completed assessment

**Request Body:**
```json
{
  "email": "user@example.com",
  "firstName": "John",
  "phone": "555-1234",
  "assessmentType": "ai-risk",
  "answers": {
    "industry": "Technology",
    "automationLevel": "Moderate"
  },
  "completedAt": "2024-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "assessment_id": 123,
  "results": {
    "score": 45,
    "risk_level": "Medium",
    "recommendations": [...]
  }
}
```

#### GET /api/assessments/<id>/results
Get assessment results by ID

**Response:**
```json
{
  "success": true,
  "assessment": {
    "id": 123,
    "email": "user@example.com",
    "assessment_type": "ai-risk",
    "score": 45,
    "risk_level": "Medium"
  }
}
```

#### POST /api/assessments/analytics
Track assessment analytics events

**Request Body:**
```json
{
  "assessment_id": 123,
  "action": "question_answered",
  "question_id": "q1",
  "answer_value": "Technology"
}
```

---

### Memes

#### GET /api/user-meme
Get a random meme for the user

**Headers:**
- `X-User-ID`: User identifier
- `X-Session-ID`: Session identifier

**Response:**
```json
{
  "id": 1,
  "caption": "Funny meme caption",
  "image_url": "https://...",
  "category": "work_life"
}
```

#### POST /api/meme-analytics
Track meme interactions

**Request Body:**
```json
{
  "meme_id": 1,
  "action": "view",
  "user_id": "user123",
  "session_id": "session456"
}
```

#### GET /api/meme-stats
Get meme usage statistics (admin)

**Response:**
```json
{
  "total_memes": 50,
  "analytics_last_7_days": [...],
  "popular_memes": [...]
}
```

---

### User Preferences

#### GET /api/user-meme-preferences/<user_id>
Get meme preferences for a user

**Response:**
```json
{
  "success": true,
  "preferences": {
    "enabled": true,
    "categories": {
      "faith": true,
      "work_life": true
    },
    "frequency": "once_per_day"
  }
}
```

#### PUT /api/user-meme-preferences/<user_id>
Update meme preferences

**Request Body:**
```json
{
  "preferences": {
    "enabled": true,
    "categories": {...},
    "frequency": "weekly"
  }
}
```

#### DELETE /api/user-meme-preferences/<user_id>
Delete/reset preferences to defaults

---

### Profiles

#### POST /profile
Save user profile data

**Request Body:**
```json
{
  "email": "user@example.com",
  "personalInfo": {...},
  "financialInfo": {
    "annualIncome": 75000,
    "monthlyTakehome": 5000
  },
  "monthlyExpenses": {...}
}
```

#### GET /profile/<email>
Get user profile by email

#### GET /profile/<email>/summary
Get profile summary with calculated insights

**Response:**
```json
{
  "success": true,
  "summary": {
    "financial_insights": {
      "monthly_income": 5000,
      "total_monthly_expenses": 3500,
      "disposable_income": 1500,
      "debt_to_income_ratio": 25.5
    },
    "recommendations": [...]
  }
}
```

---

### Resume Parsing

#### POST /api/resume/parse
Parse resume content and extract structured data

**Request Body:**
```json
{
  "content": "Resume text content...",
  "file_name": "resume.pdf",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "resume_id": 456,
  "parsed_data": {
    "personal_info": {
      "full_name": "John Doe",
      "location": "New York, NY"
    },
    "experience": [...],
    "education": [...],
    "skills": [...]
  },
  "metadata": {
    "confidence_score": 85.5,
    "processing_time": 2.3
  }
}
```

#### GET /api/resume/<resume_id>
Get parsed resume result by ID

#### GET /api/resume/analytics
Get resume parsing analytics

---

### Job Matching

#### POST /api/job-matching/search
Search for income-focused job opportunities

**Request Body:**
```json
{
  "current_salary": 75000,
  "target_salary_increase": 0.25,
  "career_field": "technology",
  "experience_level": "mid",
  "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"],
  "remote_ok": true,
  "max_commute_time": 30
}
```

**Response:**
```json
{
  "success": true,
  "jobs": [...],
  "total_count": 25
}
```

#### GET /api/job-matching/company/<company_name>
Get company profile with diversity and growth metrics

#### POST /api/job-matching/msa-targeting
Apply MSA targeting to job results

#### POST /api/job-matching/remote-detection
Detect remote-friendly positions

---

### Three-Tier Recommendations

#### POST /api/three-tier/recommendations
Get job recommendations across all three tiers

**Request Body:**
```json
{
  "current_salary": 75000,
  "career_field": "technology",
  "experience_level": "mid",
  "max_recommendations_per_tier": 5
}
```

**Response:**
```json
{
  "success": true,
  "recommendations": {
    "conservative": [...],
    "optimal": [...],
    "stretch": [...]
  },
  "tier_summary": {...}
}
```

#### GET /api/three-tier/tier/<tier_name>
Get recommendations for a specific tier (conservative, optimal, stretch)

#### GET /api/three-tier/tiers/summary
Get summary information about all three tiers

#### POST /api/three-tier/skills/gap-analysis
Analyze skills gap for a specific job

---

### Recommendation Engine

#### POST /api/recommendations/process-resume
Process resume and generate complete job recommendations

**Request Body:**
```json
{
  "resume_content": "Resume text...",
  "user_id": "user123",
  "location": "New York",
  "preferences": {
    "remote_ok": true,
    "max_commute_time": 30
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "user123_abc123_20240101_120000",
  "recommendations": {
    "conservative": [...],
    "optimal": [...],
    "stretch": [...]
  },
  "processing_time": 6.5
}
```

#### GET /api/recommendations/status/<session_id>
Get processing status for a session

#### POST /api/recommendations/analytics
Track user analytics for recommendations

#### GET /api/recommendations/performance
Get system performance metrics

#### GET /api/recommendations/health
Health check endpoint

---

### Referral-Gated Features

#### GET /career-preview
Preview of job recommendation feature (public)

#### POST /refer-friend
Send referral invitations

**Request Body:**
```json
{
  "user_id": "user123",
  "friend_email": "friend@example.com",
  "friend_name": "Friend Name",
  "personal_message": "Check out this app!"
}
```

#### GET /referral-status/<referral_code>
Track individual referral success

#### GET /api/feature-access/job-recommendations
Check if user has unlocked feature

**Response:**
```json
{
  "success": true,
  "unlocked": true,
  "referral_count": 3,
  "referrals_needed": 3
}
```

#### POST /upload-resume
Secure resume upload (REFERRAL-GATED)

**Request:** Multipart form data with file

#### POST /set-location-preferences
Location preferences (REFERRAL-GATED)

#### POST /process-recommendations
Trigger recommendation engine (REFERRAL-GATED)

---

### Risk Analytics

#### POST /api/risk/assess-and-track
Comprehensive risk assessment with analytics tracking

**Request Body:**
```json
{
  "user_profile": {...}
}
```

**Response:**
```json
{
  "success": true,
  "risk_analysis": {
    "overall_risk": 0.65,
    "risk_breakdown": {...}
  },
  "recommendations_triggered": true
}
```

#### GET /api/risk/dashboard/<user_id>
Comprehensive risk dashboard with analytics

#### POST /api/risk/trigger-recommendations
Trigger risk-based recommendations with tracking

#### GET /api/risk/analytics/effectiveness
Get career protection effectiveness metrics

#### POST /api/risk/outcome/track
Track outcomes from risk-based interventions

#### GET /api/risk/monitor/status
Real-time risk system health monitoring

#### POST /api/risk/alert/trigger
Trigger risk alerts with analytics tracking

#### GET /api/risk/trends/live
Live risk trend data for dashboard

#### GET /api/risk/predictions/active
Active risk predictions requiring attention

#### GET /api/risk/experiments/active
Active risk-related A/B tests

#### POST /api/risk/experiments/assign
Assign user to risk experiment variant

#### GET /api/risk/health
Health check endpoint

---

### Vehicle Management

#### POST /api/vehicle
Create a new vehicle with optional VIN lookup

**Request Body:**
```json
{
  "vin": "1HGBH41JXMN109186",
  "year": 2020,
  "make": "Honda",
  "model": "Civic",
  "trim": "EX",
  "current_mileage": 30000,
  "monthly_miles": 1000,
  "user_zipcode": "30309",
  "use_vin_lookup": true
}
```

**Response:**
```json
{
  "success": true,
  "vehicle": {
    "id": 1,
    "vin": "1HGBH41JXMN109186",
    "year": 2020,
    "make": "Honda",
    "model": "Civic"
  }
}
```

#### GET /api/vehicle
Get all vehicles for authenticated user

**Query Parameters:**
- `limit`: Maximum number of vehicles (optional)
- `offset`: Number to skip (optional)

#### GET /api/vehicle/<vehicle_id>
Get a specific vehicle by ID

#### PUT /api/vehicle/<vehicle_id>
Update vehicle information

#### DELETE /api/vehicle/<vehicle_id>
Delete a vehicle and all associated data

#### GET /api/vehicle/<vehicle_id>/maintenance-predictions
Get maintenance predictions for a vehicle

**Query Parameters:**
- `months`: Number of months to look ahead (default: 12)
- `include_past`: Include past predictions (default: false)

**Response:**
```json
{
  "success": true,
  "predictions": [...],
  "summary": {
    "total_predictions": 8,
    "total_estimated_cost": 2500.00
  }
}
```

#### POST /api/vehicle/<vehicle_id>/commute-analysis
Calculate commute costs for job locations

**Request Body:**
```json
{
  "job_locations": [
    {
      "name": "Downtown Office",
      "address": "123 Main St, Atlanta, GA 30309",
      "zipcode": "30309"
    }
  ],
  "work_days_per_month": 22
}
```

#### GET /api/vehicle/<vehicle_id>/forecast-impact
Get vehicle expenses impact on cash flow

**Query Parameters:**
- `months`: Number of months to forecast (default: 12)
- `include_commute`: Include commute costs (default: true)
- `include_maintenance`: Include maintenance costs (default: true)

#### POST /api/vehicle/vin-lookup
Lookup vehicle information by VIN

**Request Body:**
```json
{
  "vin": "1HGBH41JXMN109186",
  "use_cache": true
}
```

#### GET /api/vehicle/health
Health check endpoint

---

### Weekly Check-in

#### POST /api/weekly-checkin
Submit weekly check-in data

**Request Body:**
```json
{
  "check_in_date": "2024-01-01",
  "healthWellness": {
    "physicalActivity": 15,
    "relationshipSatisfaction": 8,
    "meditationMinutes": 30,
    "stressSpending": 50.00
  },
  "vehicleWellness": {
    "vehicleExpenses": 200.00,
    "transportationStress": 2,
    "commuteSatisfaction": 4
  }
}
```

#### GET /api/weekly-checkin/latest
Get the latest weekly check-in for the user

#### GET /api/weekly-checkin/history
Get check-in history

**Query Parameters:**
- `limit`: Number of records (default: 10)
- `offset`: Number to skip (default: 0)

#### GET /api/weekly-checkin/analytics
Get check-in analytics

---

### Career-Vehicle Optimization

#### POST /api/career-vehicle/job-cost-analysis
Calculate true cost of job opportunities (ADD-ON REQUIRED)

**Request Body:**
```json
{
  "job_offers": [
    {
      "title": "Software Engineer",
      "company": "Tech Corp",
      "location": "123 Main St, San Francisco, CA 94105",
      "salary": 120000
    }
  ],
  "home_address": "456 Oak Ave, Oakland, CA 94601",
  "vehicle_id": 1,
  "work_days_per_month": 22
}
```

#### POST /api/career-vehicle/commute-impact-analysis
Analyze annual transportation cost projections

#### POST /api/career-vehicle/career-move-planning
Plan career moves with vehicle costs

#### POST /api/career-vehicle/budget-optimization
Optimize budget around job/commute decisions

#### GET /api/career-vehicle/feature-access
Check if user has add-on access

---

### Housing

#### POST /api/housing/analyze-career-scenarios
Analyze career scenarios for housing decisions (MID-TIER+)

**Request Body:**
```json
{
  "scenario_id": 123,
  "career_goals": ["remote_work", "promotion"],
  "time_horizon": 12
}
```

#### POST /api/housing/search-locations
Search for housing locations (RATE LIMITED)

**Request Body:**
```json
{
  "max_rent": 2000,
  "bedrooms": 2,
  "commute_time": 30,
  "zip_code": "30309",
  "housing_type": "apartment"
}
```

#### GET /api/housing/scenarios
Get user's housing scenarios

#### GET /api/housing/tier-info
Get tier information and feature access

---

### Daily Outlook

#### GET /api/daily-outlook
Get today's outlook for current user

**Response:**
```json
{
  "success": true,
  "outlook": {
    "date": "2024-01-01",
    "actions": [...],
    "insights": [...],
    "streak_count": 5
  }
}
```

#### GET /api/daily-outlook/history
Get outlook history with pagination

**Query Parameters:**
- `start_date`: Start date (optional)
- `end_date`: End date (optional)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

#### POST /api/daily-outlook/action-completed
Mark action as completed

**Request Body:**
```json
{
  "action_id": "action123",
  "completion_status": true,
  "completion_notes": "Completed successfully"
}
```

#### POST /api/daily-outlook/rating
Submit user rating

**Request Body:**
```json
{
  "rating": 5,
  "feedback": "Great insights!"
}
```

#### GET /api/daily-outlook/streak
Get current streak information

#### POST /api/relationship-status
Update relationship status

---

### Professional Tier

#### POST /api/professional/fleet
Create fleet vehicle (PROFESSIONAL TIER)

**Request Body:**
```json
{
  "vin": "1HGBH41JXMN109186",
  "year": 2020,
  "make": "Honda",
  "model": "Civic",
  "business_use_percentage": 80
}
```

#### GET /api/professional/fleet
Get all fleet vehicles

#### GET /api/professional/fleet/<vehicle_id>
Get specific fleet vehicle

#### POST /api/professional/mileage
Log business mileage

**Request Body:**
```json
{
  "vehicle_id": 1,
  "date": "2024-01-01",
  "miles": 150,
  "business_purpose": "Client meeting",
  "start_location": "Office",
  "end_location": "Client site"
}
```

#### POST /api/professional/tax/calculator
Calculate tax deductions

#### POST /api/professional/tax/report
Generate tax report

#### GET /api/professional/analytics/fleet
Get fleet analytics

#### POST /api/professional/roi-analysis
ROI analysis for fleet

#### GET /api/professional/health
Health check

---

### Tax Adjacent Features

#### POST /api/professional/expenses
Track business expenses

**Request Body:**
```json
{
  "date": "2024-01-01",
  "amount": 150.00,
  "category": "fuel",
  "description": "Gas for business trip",
  "receipt_url": "https://..."
}
```

#### GET /api/professional/expenses
Get expense records

#### POST /api/professional/mileage
Log mileage (see Professional Tier section)

#### GET /api/professional/mileage
Get mileage records

#### POST /api/professional/maintenance
Record maintenance with cost allocation

#### GET /api/professional/education
Get educational content

#### POST /api/professional/reports/expense
Generate expense reports

---

### Business Integrations

#### POST /api/professional/integrations/quickbooks/connect
Connect QuickBooks account

#### POST /api/professional/integrations/quickbooks/sync
Sync QuickBooks data

#### POST /api/professional/integrations/credit-card/connect
Connect credit card account

#### POST /api/professional/integrations/credit-card/categorize
Categorize credit card transactions

#### POST /api/professional/integrations/hr/connect
Connect HR system

#### GET /api/professional/integrations/hr/employee-vehicles
Get employee vehicles from HR system

#### POST /api/professional/integrations/insurance/connect
Connect insurance provider

#### GET /api/professional/integrations/insurance/policies
Get insurance policies

#### GET /api/professional/integrations/status
Get integration status

#### GET /api/professional/integrations/health
Health check

---

### Subscription Management

#### GET /api/subscription/plans
Get available subscription plans

**Response:**
```json
{
  "success": true,
  "plans": [
    {
      "tier": "budget",
      "price": 0.00,
      "features": [...]
    },
    {
      "tier": "mid_tier",
      "price": 9.99,
      "features": [...]
    }
  ]
}
```

#### GET /api/subscription/current
Get current subscription

#### POST /api/subscription/upgrade
Upgrade subscription

**Request Body:**
```json
{
  "target_tier": "mid_tier",
  "payment_method_id": "pm_123"
}
```

#### POST /api/subscription/cancel
Cancel subscription

#### GET /api/subscription/feature-access
Get feature access for current subscription

#### GET /api/subscription/usage
Get usage statistics

#### GET /api/subscription/billing-history
Get billing history

#### GET /api/subscription/health
Health check

---

### External APIs

#### GET /api/external/rentals/<zip_code>
Get rental listings for zip code

**Query Parameters:**
- `max_rent`: Maximum rent (optional)
- `bedrooms`: Number of bedrooms (optional)

#### GET /api/external/homes/<zip_code>
Get home listings for zip code

#### POST /api/external/route/distance
Calculate route distance

**Request Body:**
```json
{
  "origin": "123 Main St, Atlanta, GA",
  "destination": "456 Oak Ave, Atlanta, GA"
}
```

#### GET /api/external/route/cached
Get cached route data

#### GET /api/external/status
Get service status

#### POST /api/external/cache/clear
Clear external API cache

#### GET /api/external/cache/stats
Get cache statistics

---

### Dashboard & Monitoring

#### GET /api/dashboard/overview
Get dashboard overview data

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "system": {...},
  "application": {...},
  "errors": {...},
  "health": {...}
}
```

#### GET /api/dashboard/system
Get system resource metrics

#### GET /api/dashboard/application
Get application metrics

#### GET /api/dashboard/errors
Get error metrics

**Query Parameters:**
- `hours`: Hours to look back (default: 24)

#### GET /api/dashboard/history
Get metrics history for charts

**Query Parameters:**
- `hours`: Hours of history (default: 1)
- `type`: Metric type - 'system', 'application', 'all' (default: 'all')

#### GET /api/dashboard/alerts
Get active alerts

#### GET /api/dashboard/recommendations
Get performance recommendations

#### GET /api/metrics
Get detailed system and application metrics

#### GET /api/metrics/health
Get system health status

#### GET /api/metrics/recommendations
Get performance recommendations

#### GET /api/errors/stats
Get error statistics

**Query Parameters:**
- `hours`: Hours to look back (default: 24)

#### GET /api/errors
Get error list with optional filtering

**Query Parameters:**
- `severity`: Filter by severity (optional)
- `category`: Filter by category (optional)
- `limit`: Maximum number of errors (default: 100)

#### GET /api/errors/health
Get error monitoring health status

---

### Gamification

#### GET /api/gamification/streak
Get user streak information

#### GET /api/gamification/achievements
Get user achievements

#### GET /api/gamification/milestones
Get milestones

#### GET /api/gamification/challenges
Get available challenges

#### GET /api/gamification/leaderboard
Get leaderboard

**Query Parameters:**
- `type`: Leaderboard type (optional)
- `limit`: Number of entries (default: 10)

#### POST /api/gamification/recovery
Recover from streak loss

#### POST /api/gamification/challenges/join
Join a challenge

#### POST /api/gamification/achievements/claim
Claim an achievement

#### GET /api/gamification/analytics
Get gamification analytics

#### GET /api/gamification/tier-rewards
Get tier-specific rewards

---

### Notifications

#### POST /api/notifications/subscribe
Subscribe to notifications

**Request Body:**
```json
{
  "user_id": "user123",
  "notification_types": ["email", "push"],
  "preferences": {...}
}
```

#### POST /api/notifications/unsubscribe
Unsubscribe from notifications

#### GET /api/notifications/preferences
Get notification preferences

#### PUT /api/notifications/preferences
Update notification preferences

#### POST /api/notifications/test
Send test notification

#### POST /api/notifications/track
Track notification events

#### GET /api/notifications/history
Get notification history

#### GET /api/notifications/stats
Get notification statistics

#### POST /api/notifications/schedule
Schedule a notification

#### GET /api/notifications/templates
Get notification templates

#### POST /api/notifications/templates
Create notification template

---

### Analytics

#### POST /api/analytics/user-behavior/start-session
Start user session

#### POST /api/analytics/user-behavior/end-session
End user session

#### POST /api/analytics/user-behavior/track-interaction
Track user interaction

#### GET /api/analytics/user-behavior/metrics/<user_id>
Get user metrics

#### POST /api/analytics/recommendations/track
Track recommendation

#### POST /api/analytics/recommendations/track-engagement
Track engagement

#### POST /api/analytics/recommendations/track-application
Track application

#### GET /api/analytics/recommendations/effectiveness
Get effectiveness metrics

#### POST /api/analytics/performance/track-api
Track API performance

#### POST /api/analytics/performance/log-error
Log system error

#### GET /api/analytics/performance/summary
Get performance summary

#### GET /api/analytics/performance/real-time
Get real-time metrics

#### POST /api/analytics/success/track-income
Track income change

#### POST /api/analytics/success/track-advancement
Track career advancement

#### GET /api/analytics/success/metrics/<user_id>
Get user success metrics

#### GET /api/analytics/success/system-metrics
Get system success metrics

#### POST /api/analytics/ab-tests/create
Create A/B test

#### POST /api/analytics/ab-tests/<test_id>/add-variant
Add test variant

#### POST /api/analytics/ab-tests/<test_id>/start
Start A/B test

#### GET /api/analytics/ab-tests/<test_id>/results
Get test results

#### GET /api/analytics/dashboard/overview
Get dashboard overview

#### GET /api/analytics/dashboard/success-stories
Get success stories

---

## Additional Notes

### Feature Tiers

The application uses a tiered feature system:

- **Budget Tier**: Free tier with basic features
- **Budget + Career-Vehicle Add-on**: $7/month add-on for career-vehicle optimization
- **Mid-Tier**: $9.99/month with enhanced features
- **Professional Tier**: $29.99/month with business features

### CORS

CORS is configured for the following origins:
- Development: `http://localhost:3000`, `http://localhost:5173`
- Production: Configured via environment variables

### Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: ...`

### Data Validation

All input data is validated and sanitized using the `APIValidator` utility class. Invalid data returns `400 Bad Request` with detailed error messages.

### Pagination

List endpoints support pagination via query parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `limit`: Alternative to per_page
- `offset`: Number of items to skip

### Filtering & Sorting

Many list endpoints support filtering and sorting:
- Filter parameters vary by endpoint
- Sorting via `sort` and `order` query parameters
- Example: `?sort=created_at&order=desc`

---

## Support

For API support, please contact:
- Email: api-support@mingusapp.com
- Documentation: https://docs.mingusapp.com
- Status Page: https://status.mingusapp.com

---

**Last Updated:** 2024-01-01  
**API Version:** 1.0.0
