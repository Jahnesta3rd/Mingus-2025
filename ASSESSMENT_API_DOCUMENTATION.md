# Mingus Assessment System API Documentation

## Overview

The Mingus Assessment System provides comprehensive API endpoints for managing assessments, calculating scores using exact seeded logic, and handling user conversions from free assessments to paid subscriptions. The system supports both authenticated and anonymous users with proper rate limiting and security measures.

## Base URL

```
https://api.mingus.com/api/assessments
```

## Authentication

The assessment system supports two authentication modes:

1. **Authenticated Users**: Use existing session-based authentication
2. **Anonymous Users**: No authentication required, but rate limited

### Headers

```http
Content-Type: application/json
Authorization: Bearer <token>  # For authenticated users
```

## API Endpoints

### 1. Get Available Assessments

**Endpoint:** `GET /api/assessments/available`

**Description:** Returns list of active assessments with metadata, completion statistics, and user-specific data.

**Authentication:** Optional (different data for authenticated vs anonymous users)

**Rate Limiting:** 20 requests/hour for anonymous users

**Response:**

```json
{
  "success": true,
  "assessments": [
    {
      "id": "uuid",
      "type": "ai_job_risk",
      "title": "AI Job Risk Assessment",
      "description": "Assess your job's vulnerability to AI automation",
      "estimated_duration_minutes": 10,
      "version": "1.0",
      "requires_authentication": false,
      "allow_anonymous": true,
      "max_attempts_per_user": 3,
      "stats": {
        "total_attempts": 150,
        "completed_attempts": 120,
        "completion_rate": 80.0,
        "average_score": 65.5,
        "average_time_minutes": 8.2
      },
      "user_completed": false,
      "attempts_remaining": 3
    }
  ],
  "user_authenticated": true,
  "total_assessments": 4
}
```

### 2. Submit Assessment

**Endpoint:** `POST /api/assessments/{assessment_type}/submit`

**Description:** Accept assessment responses, calculate scores using exact seeded logic, and store results.

**Authentication:** Optional (anonymous or authenticated users)

**Rate Limiting:** 5 requests/hour for anonymous users

**Request Body:**

```json
{
  "responses": {
    "relationship_status": "married",
    "spending_habits": "joint_accounts",
    "financial_stress": "sometimes",
    "emotional_triggers": ["after_arguments", "social_pressure"]
  },
  "time_spent_seconds": 480,
  "session_id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "location": "New York, NY",
  "job_title": "Software Engineer",
  "industry": "Technology"
}
```

**Response:**

```json
{
  "success": true,
  "assessment_id": "uuid",
  "score": 75,
  "risk_level": "medium",
  "segment": "relationship-spender",
  "product_tier": "Mid-tier ($20)",
  "insights": [
    "Your relationship status indicates moderate financial interdependence",
    "Joint accounts suggest shared financial responsibility",
    "Occasional financial stress may impact relationship harmony"
  ],
  "recommendations": [
    "Consider establishing clear financial boundaries",
    "Develop a shared budget strategy",
    "Explore stress management techniques for financial discussions"
  ],
  "processing_time_ms": 45,
  "user_authenticated": false,
  "conversion_offer": {
    "lead_id": "uuid",
    "lead_score": 85,
    "offer_type": "assessment_conversion",
    "discount_percentage": 20,
    "trial_days": 7,
    "message": "Based on your Relationship Impact Assessment results, we're offering you a special trial to get personalized guidance."
  },
  "upgrade_message": "Get full access to all insights, detailed recommendations, and personalized guidance."
}
```

### 3. Get Assessment Results

**Endpoint:** `GET /api/assessments/{user_assessment_id}/results`

**Description:** Return detailed assessment results with tier-based access control.

**Authentication:** Required (users can only see their own results)

**Response:**

```json
{
  "success": true,
  "assessment": {
    "id": "uuid",
    "type": "ai_job_risk",
    "title": "AI Job Risk Assessment",
    "version": "1.0",
    "completed_at": "2025-01-15T10:30:00Z",
    "time_spent_minutes": 8.5
  },
  "results": {
    "score": 75,
    "risk_level": "medium",
    "segment": "relationship-spender",
    "product_tier": "Mid-tier ($20)"
  },
  "insights": [
    "Your job has moderate automation risk",
    "AI augmentation opportunities exist in your role",
    "Consider upskilling in AI-resistant skills"
  ],
  "recommendations": [
    "Develop human-centric skills",
    "Learn AI collaboration tools",
    "Focus on creative problem-solving"
  ],
  "subscription_tier": "free",
  "upgrade_message": "Upgrade to see all insights and detailed recommendations",
  "ai_analysis": {
    "automation_score": 65,
    "augmentation_score": 80,
    "risk_factors": [
      "Routine task automation",
      "Data processing automation"
    ],
    "mitigation_strategies": [
      "Develop strategic thinking skills",
      "Focus on human-AI collaboration"
    ]
  }
}
```

### 4. Convert Assessment to Subscription

**Endpoint:** `POST /api/assessments/convert/{user_assessment_id}`

**Description:** Handle conversion from free assessment to paid subscription with Stripe integration.

**Authentication:** Optional (anonymous or authenticated users)

**Request Body:**

```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "payment_method_id": "pm_1234567890"
}
```

**Response:**

```json
{
  "success": true,
  "subscription_id": "sub_1234567890",
  "customer_id": "cus_1234567890",
  "trial_days": 7,
  "tier": "Mid-tier ($20)",
  "segment": "relationship-spender",
  "next_steps": [
    "Complete your profile setup",
    "Explore premium features",
    "Schedule your first consultation"
  ],
  "payment_method_attached": true
}
```

### 5. Get Assessment Statistics

**Endpoint:** `GET /api/assessments/stats`

**Description:** Return real-time statistics for social proof and analytics.

**Authentication:** Not required (anonymous aggregated data only)

**Rate Limiting:** 30 requests/hour for anonymous users

**Response:**

```json
{
  "success": true,
  "today": {
    "total_assessments": 45,
    "completed_assessments": 38,
    "completion_rate": 84.4,
    "average_score": 67.2
  },
  "this_week": {
    "total_assessments": 320,
    "completed_assessments": 275,
    "completion_rate": 85.9,
    "average_score": 65.8
  },
  "by_assessment_type": {
    "ai_job_risk": {
      "total_attempts": 150,
      "average_score": 68.5
    },
    "relationship_impact": {
      "total_attempts": 120,
      "average_score": 62.3
    },
    "tax_impact": {
      "total_attempts": 80,
      "average_score": 71.2
    },
    "income_comparison": {
      "total_attempts": 95,
      "average_score": 64.8
    }
  },
  "risk_distribution": {
    "low": 45,
    "medium": 120,
    "high": 85,
    "critical": 25
  },
  "total_users_helped": 275
}
```

## Assessment Types

### 1. AI Job Risk Assessment (`ai_job_risk`)

**Purpose:** Assess job vulnerability to AI automation and identify augmentation opportunities.

**Key Metrics:**
- Automation Score (0-100)
- Augmentation Score (0-100)
- Risk Factors
- Mitigation Strategies

**Scoring Logic:** Higher scores indicate higher automation risk.

### 2. Relationship Impact Assessment (`relationship_impact`)

**Purpose:** Evaluate how financial decisions impact relationships and identify stress points.

**Key Metrics:**
- Relationship Stress Score (0-100)
- Financial Harmony Score (0-100)
- Cost Projections
- Risk Factors

**Scoring Logic:** Higher scores indicate better financial harmony.

### 3. Tax Impact Assessment (`tax_impact`)

**Purpose:** Analyze tax efficiency and identify optimization opportunities.

**Key Metrics:**
- Tax Efficiency Score (0-100)
- Potential Savings (decimal)
- Optimization Opportunities

**Scoring Logic:** Higher scores indicate better tax efficiency.

### 4. Income Comparison Assessment (`income_comparison`)

**Purpose:** Compare income to market standards and identify negotiation opportunities.

**Key Metrics:**
- Market Position Score (0-100)
- Salary Benchmark Data
- Negotiation Leverage Points

**Scoring Logic:** Higher scores indicate better market position.

## Error Responses

### 400 Bad Request

```json
{
  "success": false,
  "error": "Missing responses"
}
```

### 401 Unauthorized

```json
{
  "success": false,
  "error": "Authentication required",
  "message": "Authentication required"
}
```

### 403 Forbidden

```json
{
  "success": false,
  "error": "Unauthorized access to assessment results",
  "message": "Access denied"
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": "Assessment not found",
  "message": "Resource not found"
}
```

### 429 Rate Limited

```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "Maximum 5 requests per 1 hour(s) for anonymous users",
  "retry_after": 3600
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "Failed to submit assessment",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

- **Anonymous Users:** 5 assessment submissions per hour, 20 assessment list requests per hour, 30 stats requests per hour
- **Authenticated Users:** No rate limiting on assessment submissions

## Security Features

1. **Input Validation:** All assessment responses are validated against schema
2. **Authorization:** Users can only access their own assessment results
3. **Rate Limiting:** Prevents abuse from anonymous users
4. **Session Management:** Secure session handling for authenticated users
5. **Data Sanitization:** All inputs are sanitized and validated

## Integration with Existing Services

### Calculator Integration Service

The assessment system integrates with the existing `CalculatorIntegrationService` to use the exact seeded scoring logic from Prompts 0A-0C.

### Payment Processing

Assessment conversions integrate with the existing Stripe payment processing system through the `PaymentProcessor` service.

### Database Integration

The system uses the existing database session management and integrates with:
- User management system
- Subscription tier system
- Audit logging system
- Email sequence management

## Lead Scoring System

Anonymous users are automatically scored based on:
- Assessment score (0-30 points)
- Risk level (0-25 points)
- User segment (0-20 points)
- Assessment type (0-10 points)

Total lead score is capped at 100 points for sales prioritization.

## Email Sequences

The system automatically triggers email sequences based on:
- Assessment type
- User segment
- Risk level
- Score range

Email sequences are configurable and support delayed sending with engagement tracking.

## Testing

### Example Assessment Submission

```bash
curl -X POST https://api.mingus.com/api/assessments/relationship_impact/submit \
  -H "Content-Type: application/json" \
  -d '{
    "responses": {
      "relationship_status": "married",
      "spending_habits": "joint_accounts",
      "financial_stress": "sometimes",
      "emotional_triggers": ["after_arguments"]
    },
    "time_spent_seconds": 480,
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Example Results Retrieval

```bash
curl -X GET https://api.mingus.com/api/assessments/{assessment_id}/results \
  -H "Authorization: Bearer {token}"
```

## Performance Considerations

- Assessment scoring targets <100ms calculation time
- Database queries are optimized with proper indexing
- Rate limiting prevents system overload
- Caching is implemented for frequently accessed data

## Monitoring and Analytics

The system provides comprehensive analytics:
- Assessment completion rates
- Average scores by type
- Risk level distribution
- User engagement metrics
- Conversion tracking

All metrics are available through the `/api/assessments/stats` endpoint for social proof and internal monitoring.
