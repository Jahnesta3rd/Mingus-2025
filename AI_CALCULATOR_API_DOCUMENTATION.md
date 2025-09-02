# 🤖 AI Job Impact Calculator API Documentation

## 📋 Overview

The AI Job Impact Calculator API provides comprehensive endpoints for assessing AI's impact on jobs, searching job data, and tracking conversions. Built with Flask, SQLAlchemy, and integrated with Resend email service and Stripe payments.

## 🔗 Base URL

```
https://api.mingusapp.com/api/ai-calculator
```

## 🔐 Authentication

Currently, the API uses rate limiting and CSRF protection. No authentication is required for public endpoints.

## 📊 Rate Limiting

- **Assessment Submission**: 5 requests per minute
- **Job Search**: 10 requests per minute  
- **Conversion Tracking**: 10 requests per minute

## 🚀 API Endpoints

---

### **1. POST /assess**

**Description**: Submit a 5-step AI job impact assessment and receive personalized analysis

**URL**: `/api/ai-calculator/assess`

**Method**: `POST`

**Content-Type**: `application/json`

#### **Request Body**

```json
{
  "job_title": "Software Engineer",
  "industry": "technology",
  "experience_level": "senior",
  "tasks_array": ["coding", "analysis", "project_management"],
  "remote_work_frequency": "often",
  "ai_usage_frequency": "sometimes",
  "team_size": "11-25",
  "tech_skills_level": "advanced",
  "concerns_array": ["job_loss", "skill_gap"],
  "first_name": "John",
  "email": "john@example.com",
  "location": "San Francisco, CA",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "ai_calculator",
  "utm_term": "ai job impact",
  "utm_content": "banner_ad"
}
```

#### **Field Descriptions**

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `job_title` | string | ✅ | User's job title | Any string |
| `industry` | string | ✅ | Industry sector | `technology`, `healthcare`, `finance`, `manufacturing`, `retail`, `marketing`, `education`, `legal`, `consulting`, `other` |
| `experience_level` | string | ✅ | Years of experience | `entry`, `mid`, `senior`, `executive` |
| `tasks_array` | array | ✅ | Daily tasks performed | `coding`, `writing`, `analysis`, `data_entry`, `customer_service`, `project_management`, `creative_design`, `sales`, `reporting`, `content_creation` |
| `remote_work_frequency` | string | ✅ | Remote work frequency | `never`, `rarely`, `sometimes`, `often`, `always` |
| `ai_usage_frequency` | string | ✅ | AI tool usage frequency | `never`, `rarely`, `sometimes`, `often`, `always` |
| `team_size` | string | ✅ | Team size | `1-5`, `6-10`, `11-25`, `26-50`, `50+` |
| `tech_skills_level` | string | ✅ | Technical skill level | `basic`, `intermediate`, `advanced`, `expert` |
| `concerns_array` | array | ✅ | AI-related concerns | `job_loss`, `skill_gap`, `automation`, `competition`, `ethical`, `none` |
| `first_name` | string | ✅ | User's first name | Any string |
| `email` | string | ✅ | User's email address | Valid email format |
| `location` | string | ❌ | User's location | Any string |
| `utm_*` | string | ❌ | UTM tracking parameters | Any string |

#### **Response**

**Success (200 OK)**

```json
{
  "success": true,
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "automation_score": 25,
  "augmentation_score": 75,
  "risk_level": "low",
  "recommendations": [
    "Continue developing your technical and analytical skills",
    "Explore ways to leverage AI to increase your productivity",
    "Consider mentoring others in AI adoption",
    "Focus on leadership and innovation skills",
    "Stay ahead of the curve by learning emerging technologies"
  ],
  "email_sent": true,
  "message": "Assessment completed successfully"
}
```

**Error (400 Bad Request)**

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid data provided",
  "details": [
    "experience_level must be one of: entry, mid, senior, executive"
  ]
}
```

#### **Scoring Algorithm**

The API uses a sophisticated scoring algorithm:

1. **Base Score**: Job title fuzzy matching against reference data
2. **Industry Modifiers**: Industry-specific adjustments
3. **Task Modifiers**: Daily task automation potential
4. **Experience Modifiers**: Experience level impact
5. **AI Usage Modifiers**: Current AI tool usage
6. **Tech Skills Modifiers**: Technical expertise level

**Score Bounds**:
- Automation Score: 5-80
- Augmentation Score: 10-85

**Risk Levels**:
- **Low**: Total impact < 30
- **Medium**: Total impact 30-49
- **High**: Total impact ≥ 50

---

### **2. GET /job-search**

**Description**: Fuzzy search for job titles in the risk data database

**URL**: `/api/ai-calculator/job-search`

**Method**: `GET`

#### **Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_title` | string | ✅ | Job title to search for |

#### **Request Example**

```
GET /api/ai-calculator/job-search?job_title=software engineer
```

#### **Response**

**Success (200 OK)**

```json
{
  "success": true,
  "query": "software engineer",
  "results": [
    {
      "job_keyword": "software_engineer",
      "automation_base_score": 20,
      "augmentation_base_score": 80,
      "risk_category": "low",
      "similarity_score": 0.95
    },
    {
      "job_keyword": "data_engineer",
      "automation_base_score": 25,
      "augmentation_base_score": 75,
      "risk_category": "low",
      "similarity_score": 0.65
    }
  ],
  "total_results": 2
}
```

**Error (400 Bad Request)**

```json
{
  "success": false,
  "error": "missing_job_title",
  "message": "job_title parameter is required"
}
```

#### **Search Algorithm**

- Uses Python's `SequenceMatcher` for fuzzy string matching
- Minimum similarity threshold: 0.3
- Returns top 10 most relevant matches
- Sorted by similarity score (descending)

---

### **3. POST /convert**

**Description**: Track conversion events and trigger Stripe checkout for paid conversions

**URL**: `/api/ai-calculator/convert`

**Method**: `POST`

**Content-Type**: `application/json`

#### **Request Body**

```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversion_type": "paid_upgrade",
  "conversion_value": 99.00,
  "conversion_source": "email",
  "conversion_medium": "email",
  "conversion_campaign": "ai_calculator_followup"
}
```

#### **Field Descriptions**

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `assessment_id` | string | ✅ | UUID of the assessment | Valid UUID |
| `conversion_type` | string | ✅ | Type of conversion | `email_signup`, `paid_upgrade`, `consultation_booking`, `course_enrollment` |
| `conversion_value` | float | ✅ | Monetary value of conversion | Positive number |
| `conversion_source` | string | ❌ | Source of conversion | Any string |
| `conversion_medium` | string | ❌ | Medium of conversion | Any string |
| `conversion_campaign` | string | ❌ | Campaign name | Any string |

#### **Response**

**Success (200 OK)**

```json
{
  "success": true,
  "conversion_id": "660e8400-e29b-41d4-a716-446655440000",
  "conversion_type": "paid_upgrade",
  "conversion_value": 99.00,
  "stripe_session_id": "cs_test_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6"
}
```

**Error (404 Not Found)**

```json
{
  "success": false,
  "error": "assessment_not_found",
  "message": "Assessment not found"
}
```

#### **Stripe Integration**

For paid conversions (`paid_upgrade`, `consultation_booking`, `course_enrollment`), the API automatically creates a Stripe checkout session with:

- **Product Names**:
  - `paid_upgrade`: "MINGUS Premium Subscription"
  - `consultation_booking`: "AI Career Consultation"
  - `course_enrollment`: "AI Career Mastery Course"

- **Success URL**: `{frontend_url}/success?session_id={CHECKOUT_SESSION_ID}`
- **Cancel URL**: `{frontend_url}/cancel`

---

## 🔧 Configuration

### **Environment Variables**

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/mingus

# Email Service
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=ai-insights@mingusapp.com
RESEND_FROM_NAME=MINGUS AI Career Insights

# Payment Processing
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Frontend
FRONTEND_URL=https://mingusapp.com

# Flask
FLASK_ENV=production
FLASK_DEBUG=false
```

### **Database Tables**

The API uses three main tables:

1. **`ai_job_assessments`**: Stores assessment data and results
2. **`ai_job_risk_data`**: Reference data for job risk calculations
3. **`ai_calculator_conversions`**: Tracks conversion events

---

## 🛡️ Security Features

### **Input Validation**
- Comprehensive field validation
- Email format verification
- Enum value validation
- SQL injection protection

### **Rate Limiting**
- Configurable rate limits per endpoint
- IP-based limiting
- Graceful error responses

### **CSRF Protection**
- CSRF tokens for form submissions
- Secure cookie handling
- Cross-origin request protection

### **Data Protection**
- Input sanitization
- XSS protection
- Secure database queries
- Error message sanitization

---

## 📊 Analytics & Tracking

### **Conversion Events**
- Assessment completions
- Email signups
- Paid conversions
- Job searches

### **Funnel Tracking**
- Awareness → Interest → Consideration → Intent → Purchase
- Touchpoint tracking
- Days to conversion
- Revenue attribution

### **Performance Metrics**
- Response times
- Error rates
- Success rates
- User engagement

---

## 🚨 Error Handling

### **HTTP Status Codes**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (validation errors) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

### **Error Response Format**

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": ["Additional error details"]
}
```

### **Common Error Codes**

| Error Code | Description |
|------------|-------------|
| `no_data` | No request body provided |
| `missing_field` | Required field missing |
| `invalid_email` | Invalid email format |
| `validation_error` | Data validation failed |
| `assessment_not_found` | Assessment ID not found |
| `invalid_conversion_type` | Invalid conversion type |
| `assessment_failed` | Assessment processing failed |
| `search_failed` | Job search failed |
| `conversion_failed` | Conversion tracking failed |

---

## 🔄 Webhooks

### **Stripe Webhooks**

The API supports Stripe webhooks for payment processing:

- **Payment Success**: Update conversion status
- **Payment Failure**: Handle failed payments
- **Refund Processing**: Handle refunds

### **Email Webhooks**

Resend webhooks for email delivery tracking:

- **Email Delivered**: Track delivery success
- **Email Opened**: Track engagement
- **Email Clicked**: Track click-through rates
- **Email Bounced**: Handle delivery failures

---

## 📈 Monitoring & Logging

### **Logging Levels**
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors
- **DEBUG**: Detailed debugging (development only)

### **Log Format**
```
2024-01-15 10:30:45,123 - ai_calculator_api - INFO - Assessment completed for john@example.com: low risk
```

### **Health Checks**
- Database connectivity
- Email service status
- Stripe API status
- Rate limiting status

---

## 🧪 Testing

### **Test Endpoints**

```bash
# Test assessment submission
curl -X POST https://api.mingusapp.com/api/ai-calculator/assess \
  -H "Content-Type: application/json" \
  -d @test_assessment.json

# Test job search
curl "https://api.mingusapp.com/api/ai-calculator/job-search?job_title=engineer"

# Test conversion tracking
curl -X POST https://api.mingusapp.com/api/ai-calculator/convert \
  -H "Content-Type: application/json" \
  -d @test_conversion.json
```

### **Test Data**

**test_assessment.json**:
```json
{
  "job_title": "Software Engineer",
  "industry": "technology",
  "experience_level": "senior",
  "tasks_array": ["coding", "analysis"],
  "remote_work_frequency": "often",
  "ai_usage_frequency": "sometimes",
  "team_size": "11-25",
  "tech_skills_level": "advanced",
  "concerns_array": ["skill_gap"],
  "first_name": "Test",
  "email": "test@example.com"
}
```

**test_conversion.json**:
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversion_type": "email_signup",
  "conversion_value": 25.00
}
```

---

## 🔗 Integration Examples

### **Frontend Integration (JavaScript)**

```javascript
// Submit assessment
async function submitAssessment(data) {
  try {
    const response = await fetch('/api/ai-calculator/assess', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (result.success) {
      displayResults(result);
    } else {
      handleError(result);
    }
  } catch (error) {
    console.error('Assessment submission failed:', error);
  }
}

// Search jobs
async function searchJobs(jobTitle) {
  try {
    const response = await fetch(`/api/ai-calculator/job-search?job_title=${encodeURIComponent(jobTitle)}`);
    const result = await response.json();
    
    if (result.success) {
      displaySearchResults(result.results);
    }
  } catch (error) {
    console.error('Job search failed:', error);
  }
}

// Track conversion
async function trackConversion(assessmentId, conversionType, value) {
  try {
    const response = await fetch('/api/ai-calculator/convert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assessment_id: assessmentId,
        conversion_type: conversionType,
        conversion_value: value
      })
    });
    
    const result = await response.json();
    
    if (result.success && result.stripe_session_id) {
      // Redirect to Stripe checkout
      window.location.href = `/checkout?session_id=${result.stripe_session_id}`;
    }
  } catch (error) {
    console.error('Conversion tracking failed:', error);
  }
}
```

### **Python Integration**

```python
import requests
import json

class AICalculatorAPI:
    def __init__(self, base_url="https://api.mingusapp.com"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def submit_assessment(self, data):
        """Submit AI job impact assessment"""
        url = f"{self.base_url}/api/ai-calculator/assess"
        response = self.session.post(url, json=data)
        return response.json()
    
    def search_jobs(self, job_title):
        """Search for job titles"""
        url = f"{self.base_url}/api/ai-calculator/job-search"
        params = {"job_title": job_title}
        response = self.session.get(url, params=params)
        return response.json()
    
    def track_conversion(self, assessment_id, conversion_type, value):
        """Track conversion event"""
        url = f"{self.base_url}/api/ai-calculator/convert"
        data = {
            "assessment_id": assessment_id,
            "conversion_type": conversion_type,
            "conversion_value": value
        }
        response = self.session.post(url, json=data)
        return response.json()

# Usage example
api = AICalculatorAPI()

# Submit assessment
assessment_data = {
    "job_title": "Data Scientist",
    "industry": "technology",
    "experience_level": "mid",
    "tasks_array": ["analysis", "coding"],
    "remote_work_frequency": "sometimes",
    "ai_usage_frequency": "often",
    "team_size": "6-10",
    "tech_skills_level": "advanced",
    "concerns_array": ["skill_gap"],
    "first_name": "Alice",
    "email": "alice@example.com"
}

result = api.submit_assessment(assessment_data)
print(f"Assessment ID: {result['assessment_id']}")
print(f"Risk Level: {result['risk_level']}")
```

---

## 📞 Support

### **Contact Information**
- **Email**: api-support@mingusapp.com
- **Documentation**: https://docs.mingusapp.com/ai-calculator-api
- **Status Page**: https://status.mingusapp.com

### **Rate Limits & Quotas**
- **Free Tier**: 100 requests/day
- **Pro Tier**: 10,000 requests/day
- **Enterprise**: Custom limits

### **Response Times**
- **Assessment Submission**: < 2 seconds
- **Job Search**: < 500ms
- **Conversion Tracking**: < 1 second

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Production Ready
