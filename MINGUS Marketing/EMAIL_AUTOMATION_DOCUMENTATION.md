# Email Capture and Automation Integration System

## Overview

This comprehensive email automation system for Ratchet Money provides complete email capture, segmentation, automated sequences, and conversion tracking capabilities. The system integrates with popular email service providers (Mailchimp, ConvertKit, SendGrid) and includes advanced features like A/B testing, engagement tracking, and personalized content delivery.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Email Service Integration](#email-service-integration)
5. [Security Features](#security-features)
6. [Email Templates](#email-templates)
7. [A/B Testing](#ab-testing)
8. [Setup Instructions](#setup-instructions)
9. [Usage Examples](#usage-examples)
10. [Troubleshooting](#troubleshooting)

## System Architecture

### Components

- **Frontend**: React + TypeScript components for email capture and assessment
- **Backend**: Supabase database with PostgreSQL
- **Email Services**: Mailchimp, ConvertKit, or SendGrid integration
- **Security**: Rate limiting, input validation, CORS protection
- **Analytics**: Engagement tracking and conversion monitoring

### Data Flow

1. User completes assessment → Lead data stored in Supabase
2. Lead automatically added to email service with segment tags
3. Welcome sequence triggered based on segment
4. Engagement tracked and stored
5. A/B testing applied to optimize performance

## Database Schema

### Core Tables

#### `leads`
Stores all lead information with email automation fields:

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    segment VARCHAR(100) NOT NULL,
    score INTEGER NOT NULL,
    product_tier VARCHAR(100) NOT NULL,
    email_preferences JSONB,
    engagement_metrics JSONB,
    ab_test_group VARCHAR(100),
    -- ... additional fields
);
```

#### `email_logs`
Tracks all email communications:

```sql
CREATE TABLE email_logs (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    email_type VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'sent',
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    -- ... additional fields
);
```

#### `email_templates`
Stores email templates with variables:

```sql
CREATE TABLE email_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    template_type VARCHAR(100) NOT NULL,
    segment VARCHAR(100),
    variables TEXT[],
    -- ... additional fields
);
```

### Additional Tables

- `assessment_questions` - Assessment question bank
- `assessment_responses` - Individual user responses
- `email_campaigns` - Campaign management
- `ab_tests` - A/B testing configuration
- `email_events` - Detailed event tracking
- `conversions` - Conversion attribution
- `lead_tags` - Advanced segmentation

## API Endpoints

### 1. Questionnaire Submission

```typescript
POST /api/questionnaire/submit
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "responses": {
    "question_1": "answer_1",
    "question_2": "answer_2"
  },
  "score": 75,
  "contactMethod": "email",
  "betaInterest": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "segment": "emotional-manager",
    "product_tier": "Mid-tier ($20)",
    "score": 75
  },
  "message": "Questionnaire submitted successfully"
}
```

### 2. Email List Subscription

```typescript
POST /api/email/subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "preferences": {
    "marketing": true,
    "transactional": true,
    "frequency": "weekly"
  }
}
```

### 3. Results Delivery

```typescript
POST /api/results/deliver
Content-Type: application/json

{
  "leadId": "uuid"
}
```

### 4. Segment Tagging

```typescript
PUT /api/leads/{leadId}/segment
Content-Type: application/json

{
  "segment": "stress-free"
}
```

## Email Service Integration

### Supported Providers

1. **Mailchimp**
   - Full API integration
   - Segment-based campaigns
   - Tag management
   - Merge fields support

2. **ConvertKit**
   - Form and sequence integration
   - Tag-based segmentation
   - Broadcast campaigns

3. **SendGrid**
   - Transactional email support
   - Marketing campaigns
   - Contact management

### Configuration

Set environment variables for your chosen provider:

```bash
# Mailchimp
REACT_APP_EMAIL_PROVIDER=mailchimp
REACT_APP_MAILCHIMP_API_KEY=your_api_key
REACT_APP_MAILCHIMP_LIST_ID=your_list_id
REACT_APP_MAILCHIMP_SERVER_PREFIX=us1

# ConvertKit
REACT_APP_EMAIL_PROVIDER=convertkit
REACT_APP_CONVERTKIT_API_KEY=your_api_key
REACT_APP_CONVERTKIT_FORM_ID=your_form_id
REACT_APP_CONVERTKIT_SEQUENCE_ID=your_sequence_id

# SendGrid
REACT_APP_EMAIL_PROVIDER=sendgrid
REACT_APP_SENDGRID_API_KEY=your_api_key
REACT_APP_SENDGRID_FROM_EMAIL=noreply@yourdomain.com
REACT_APP_SENDGRID_FROM_NAME=Ratchet Money
```

### Usage Example

```typescript
import { EmailAutomationService } from '../services/emailService'

const emailService = new EmailAutomationService()

// Process a new lead
const result = await emailService.processLead(lead)

// Send segment-specific email
await emailService.sendSegmentSpecificEmail(
  'stress-free',
  'Your Stress-Free Financial Strategy',
  emailBody
)
```

## Security Features

### Rate Limiting

- Configurable rate limits per endpoint
- IP-based and user-based limiting
- Automatic blocking of abusive requests

### Input Validation

- Email format validation
- Phone number validation
- XSS prevention
- SQL injection protection

### Authentication

- JWT-based authentication
- API key validation
- Session management

### CORS Protection

- Configurable allowed origins
- Method restrictions
- Header validation

### Data Encryption

- Sensitive data encryption
- Secure transmission
- Audit logging

## Email Templates

### Template Types

1. **Welcome Sequence** (5 emails)
   - Welcome email
   - 5-minute money audit
   - Personality reveal
   - Success stories
   - Action plan

2. **Assessment Results**
   - Immediate results delivery
   - Personalized recommendations
   - Next steps

3. **Segment-Specific**
   - Stress-free strategies
   - Relationship spender guidance
   - Emotional manager support
   - Crisis mode intervention

4. **Product Launch**
   - New product announcements
   - Exclusive access
   - Limited-time offers

### Template Variables

```typescript
{
  "name": "User's first name",
  "segment": "stress-free",
  "score": 75,
  "product_tier": "Mid-tier ($20)",
  "getSegmentDescription": "Personalized description",
  "getTimeline": "Expected timeline",
  "getCtaLink": "Call-to-action URL"
}
```

### Template Usage

```typescript
import { EMAIL_TEMPLATES, getSegmentDescription } from '../templates/emailTemplates'

const template = EMAIL_TEMPLATES.find(t => t.id === 'results-immediate')
const body = template.body
  .replace('{{name}}', lead.name || 'there')
  .replace('{{segment}}', lead.segment)
  .replace('{{score}}', lead.score.toString())
```

## A/B Testing

### Test Types

1. **Email Subject Lines**
2. **Email Content**
3. **Landing Page Elements**
4. **Call-to-Action Buttons**

### Configuration

```typescript
const abTest = {
  name: "Welcome Email Subject Test",
  test_type: "email_subject",
  variants: [
    { name: "Control", subject: "Welcome to Ratchet Money!" },
    { name: "Variant A", subject: "🚀 Transform Your Financial Life" },
    { name: "Variant B", subject: "Your Financial Freedom Starts Here" }
  ],
  traffic_split: { "Control": 33, "Variant A": 33, "Variant B": 34 },
  primary_metric: "open_rate"
}
```

### Statistical Analysis

- Confidence level calculation
- Sample size requirements
- Winner determination
- Statistical significance testing

## Setup Instructions

### 1. Environment Configuration

Copy `env.example` to `.env` and configure:

```bash
# Supabase
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_anon_key
REACT_APP_SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Email Service
REACT_APP_EMAIL_PROVIDER=mailchimp
REACT_APP_EMAIL_API_KEY=your_api_key
REACT_APP_EMAIL_LIST_ID=your_list_id

# Security
REACT_APP_RATE_LIMIT_ENABLED=true
REACT_APP_RATE_LIMIT_MAX_REQUESTS=100
REACT_APP_JWT_SECRET=your_jwt_secret
```

### 2. Database Setup

Run the database schema:

```bash
# Connect to your Supabase database
psql -h your-supabase-host -U postgres -d postgres -f supabase-email-automation-schema.sql
```

### 3. Email Service Setup

#### Mailchimp Setup

1. Create a Mailchimp account
2. Create an audience/list
3. Generate API key
4. Note your server prefix (e.g., us1)
5. Configure merge fields for segmentation

#### ConvertKit Setup

1. Create a ConvertKit account
2. Create a form for lead capture
3. Generate API key
4. Create a sequence for welcome emails
5. Set up tags for segmentation

#### SendGrid Setup

1. Create a SendGrid account
2. Verify your sender domain
3. Generate API key
4. Create a contact list
5. Set up custom fields

### 4. Template Configuration

1. Import email templates to your database
2. Customize templates for your brand
3. Set up merge fields in your email service
4. Test template rendering

### 5. Integration Testing

```typescript
// Test questionnaire submission
const testLead = {
  email: 'test@example.com',
  name: 'Test User',
  responses: { question_1: 'answer_1' },
  score: 50
}

const result = await submitQuestionnaire(testLead)
console.log('Submission result:', result)
```

## Usage Examples

### Basic Email Capture

```typescript
import { subscribeToEmailList } from '../api/emailAutomation'

const subscription = await subscribeToEmailList({
  email: 'user@example.com',
  name: 'John Doe',
  preferences: {
    marketing: true,
    transactional: true,
    frequency: 'weekly'
  }
})
```

### Assessment with Email Automation

```typescript
import { submitQuestionnaire } from '../api/emailAutomation'

const submission = await submitQuestionnaire({
  email: 'user@example.com',
  name: 'John Doe',
  responses: assessmentResponses,
  score: calculatedScore,
  contactMethod: 'email',
  betaInterest: true
})

// Lead is automatically:
// 1. Stored in database
// 2. Added to email service
// 3. Tagged with segment
// 4. Triggered welcome sequence
```

### Segment-Specific Campaigns

```typescript
import { EmailAutomationService } from '../services/emailService'

const emailService = new EmailAutomationService()

// Send campaign to specific segment
await emailService.sendSegmentSpecificEmail(
  'stress-free',
  'Your Stress-Free Financial Strategy',
  stressFreeTemplate
)
```

### A/B Testing

```typescript
import { createABTest, getABTestVariant } from '../utils/abTesting'

// Create A/B test
const testId = await createABTest({
  name: 'Welcome Email Test',
  test_type: 'email_subject',
  variants: [
    { name: 'Control', content: 'Welcome to Ratchet Money!' },
    { name: 'Variant A', content: '🚀 Transform Your Financial Life' }
  ],
  traffic_split: { 'Control': 50, 'Variant A': 50 }
})

// Get variant for user
const variant = await getABTestVariant(testId, userId)
```

## Troubleshooting

### Common Issues

#### 1. Email Service Connection Errors

**Problem**: Cannot connect to email service
**Solution**: 
- Verify API keys are correct
- Check network connectivity
- Ensure email service account is active

#### 2. Template Rendering Issues

**Problem**: Email templates not rendering correctly
**Solution**:
- Check template syntax
- Verify merge fields exist in email service
- Test template variables

#### 3. Rate Limiting Errors

**Problem**: Too many requests errors
**Solution**:
- Implement proper rate limiting
- Add request queuing
- Monitor API usage

#### 4. Database Connection Issues

**Problem**: Cannot connect to Supabase
**Solution**:
- Verify environment variables
- Check Supabase project status
- Ensure proper permissions

### Debug Mode

Enable debug logging:

```bash
REACT_APP_ENABLE_DEBUG_LOGGING=true
REACT_APP_LOG_LEVEL=debug
```

### Monitoring

Monitor system health:

```typescript
// Check email service status
const status = await emailService.getStatus()

// Monitor engagement metrics
const metrics = await getEngagementMetrics()

// Track conversion rates
const conversions = await getConversionRates()
```

### Performance Optimization

1. **Database Indexing**: Ensure proper indexes on frequently queried fields
2. **Caching**: Implement Redis caching for frequently accessed data
3. **Batch Processing**: Process emails in batches for better performance
4. **CDN**: Use CDN for static assets and email templates

## Security Best Practices

### API Security

1. **Rate Limiting**: Implement per-user and per-IP rate limits
2. **Input Validation**: Validate all user inputs
3. **Authentication**: Use JWT tokens for API access
4. **CORS**: Configure proper CORS policies

### Data Protection

1. **Encryption**: Encrypt sensitive data at rest and in transit
2. **Access Control**: Implement role-based access control
3. **Audit Logging**: Log all security events
4. **Data Retention**: Implement proper data retention policies

### Email Security

1. **Authentication**: Use SPF, DKIM, and DMARC
2. **List Hygiene**: Regular list cleaning and validation
3. **Unsubscribe**: Easy unsubscribe process
4. **Compliance**: Follow CAN-SPAM and GDPR requirements

## Compliance and Legal

### GDPR Compliance

- Data minimization
- User consent management
- Right to be forgotten
- Data portability
- Privacy by design

### CAN-SPAM Compliance

- Clear sender identification
- Accurate subject lines
- Physical address inclusion
- Unsubscribe mechanism
- Honor unsubscribe requests

### Email Best Practices

- Permission-based marketing
- Clear value proposition
- Mobile-friendly design
- A/B testing
- Regular list cleaning

## Support and Maintenance

### Regular Maintenance

1. **Database Maintenance**: Regular backups and optimization
2. **Email Service**: Monitor deliverability and engagement
3. **Security Updates**: Keep dependencies updated
4. **Performance Monitoring**: Monitor system performance

### Support Resources

- Documentation: This guide
- Code Repository: GitHub repository
- Issue Tracking: GitHub Issues
- Community: Developer forums

### Contact Information

- Technical Support: support@ratchetmoney.com
- Security Issues: security@ratchetmoney.com
- Feature Requests: product@ratchetmoney.com

---

This email automation system provides a complete solution for lead capture, segmentation, and automated email marketing. Follow the setup instructions carefully and test thoroughly before deploying to production. 