# Supabase Configuration Usage Guide

## Overview

This guide explains how to use the Supabase configuration and helper functions for the Ratchet Money marketing funnel. The configuration is located in `src/lib/supabase.js` and provides a complete set of functions for managing leads, assessments, and email communications.

## Quick Start

### 1. Import the Configuration

```javascript
import { 
  supabase,
  createLead, 
  confirmEmail,
  getAssessmentQuestions,
  submitAssessmentResponse,
  completeAssessment,
  getLeadByEmail,
  logEmailSent
} from '../lib/supabase.js'
```

### 2. Basic Usage Example

```javascript
// Create a new lead
const result = await createLead('user@example.com')
if (result.success) {
  console.log('Lead created:', result.data)
}

// Get assessment questions
const questions = await getAssessmentQuestions()
if (questions.success) {
  console.log('Questions loaded:', questions.data)
}
```

## Helper Functions Reference

### 1. Lead Management

#### `createLead(email)`
Creates a new lead in the database.

```javascript
const result = await createLead('user@example.com')
// Returns: { success: true, data: { id, email, created_at, ... } }
```

#### `confirmEmail(email)`
Confirms a lead's email subscription.

```javascript
const result = await confirmEmail('user@example.com')
// Returns: { success: true, data: { id, email, confirmed: true, ... } }
```

#### `getLeadByEmail(email)`
Retrieves lead information by email.

```javascript
const result = await getLeadByEmail('user@example.com')
// Returns: { success: true, data: { id, email, confirmed, segment, ... } }
```

### 2. Assessment Management

#### `getAssessmentQuestions()`
Fetches all active assessment questions.

```javascript
const result = await getAssessmentQuestions()
// Returns: { success: true, data: [question1, question2, ...] }
```

#### `startAssessment(email)`
Marks the start of an assessment for a lead.

```javascript
const result = await startAssessment('user@example.com')
// Returns: { success: true, data: { assessment_started_at: timestamp } }
```

#### `submitAssessmentResponse(leadId, questionId, responseValue, responsePoints)`
Submits an individual assessment response.

```javascript
const result = await submitAssessmentResponse(
  'lead-uuid',
  'question-uuid', 
  'option-value',
  5
)
// Returns: { success: true, data: { id, lead_id, question_id, ... } }
```

#### `completeAssessment(email, assessmentAnswers, totalScore)`
Completes the assessment and calculates results.

```javascript
const result = await completeAssessment(
  'user@example.com',
  { 'q1': { value: 'option1', points: 5 } },
  25
)
// Returns: { success: true, leadId: 'lead-uuid' }
```

### 3. Email Management

#### `logEmailSent(leadId, emailType, subject, body, status)`
Logs an email communication.

```javascript
const result = await logEmailSent(
  'lead-uuid',
  'welcome',
  'Welcome to Ratchet Money!',
  '<h1>Welcome!</h1>',
  'sent'
)
// Returns: { success: true, data: { id, lead_id, email_type, ... } }
```

## Complete Assessment Flow Example

Here's a complete example showing how to implement the assessment flow:

```javascript
import React, { useState, useEffect } from 'react'
import { 
  createLead, 
  getAssessmentQuestions, 
  submitAssessmentResponse, 
  completeAssessment,
  confirmEmail 
} from '../lib/supabase.js'

const AssessmentFlow = () => {
  const [email, setEmail] = useState('')
  const [questions, setQuestions] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [responses, setResponses] = useState({})
  const [step, setStep] = useState('email') // email, assessment, results

  // Load questions on mount
  useEffect(() => {
    loadQuestions()
  }, [])

  const loadQuestions = async () => {
    const result = await getAssessmentQuestions()
    if (result.success) {
      setQuestions(result.data)
    }
  }

  // Step 1: Email submission
  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    
    // Create lead
    const result = await createLead(email)
    if (result.success) {
      // Confirm email
      await confirmEmail(email)
      setStep('assessment')
    }
  }

  // Step 2: Question response
  const handleQuestionResponse = async (questionId, value, points) => {
    // Store locally
    setResponses(prev => ({
      ...prev,
      [questionId]: { value, points }
    }))

    // Save to database
    await submitAssessmentResponse(result.data.id, questionId, value, points)

    // Move to next question or complete
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1)
    } else {
      await handleAssessmentComplete()
    }
  }

  // Step 3: Complete assessment
  const handleAssessmentComplete = async () => {
    const score = Object.values(responses)
      .reduce((sum, response) => sum + response.points, 0)
    
    const result = await completeAssessment(email, responses, score)
    if (result.success) {
      setStep('results')
    }
  }

  // Render UI based on step...
}
```

## Using with the RatchetMoneyAPI Class

For more complex operations, you can use the `RatchetMoneyAPI` class:

```javascript
import { RatchetMoneyAPI } from '../api'

// Create lead with additional data
const result = await RatchetMoneyAPI.createLead({
  email: 'user@example.com',
  firstName: 'John',
  phoneNumber: '+1234567890',
  leadSource: 'website',
  utmData: {
    source: 'google',
    medium: 'cpc',
    campaign: 'spring2024'
  }
})

// Complete assessment with full submission
const assessmentResult = await RatchetMoneyAPI.completeAssessment({
  email: 'user@example.com',
  firstName: 'John',
  answers: { 'q1': 5, 'q2': 3, 'q3': 4 },
  leadSource: 'assessment',
  utmData: { source: 'facebook' }
})

// Send email
await RatchetMoneyAPI.sendEmail({
  to: 'user@example.com',
  subject: 'Your Results Are Ready!',
  body: '<h1>Results</h1>',
  leadId: 'lead-uuid',
  emailType: 'results'
})
```

## Error Handling

All helper functions return a consistent response format:

```javascript
// Success case
{ success: true, data: resultData }

// Error case
{ success: false, error: 'Error message' }
```

Example error handling:

```javascript
const result = await createLead('invalid-email')
if (!result.success) {
  console.error('Failed to create lead:', result.error)
  // Handle error appropriately
} else {
  console.log('Lead created successfully:', result.data)
}
```

## Environment Variables

Make sure your `.env` file contains:

```env
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
```

## Database Schema Requirements

The helper functions expect these tables to exist:

- `leads` - Lead information
- `assessment_questions` - Assessment questions
- `assessment_responses` - Individual responses
- `email_logs` - Email communication logs
- `email_templates` - Email templates

## Testing

You can test the configuration using:

```bash
# Test basic configuration
node scripts/test-supabase-config.js

# Test database access
node scripts/test-database-access.js
```

## Integration Tips

1. **Error Handling**: Always check the `success` property of returned objects
2. **Loading States**: Use the async nature of functions to show loading states
3. **Data Validation**: Validate data before sending to Supabase
4. **Rate Limiting**: Be mindful of Supabase rate limits in production
5. **RLS Policies**: Ensure Row Level Security policies are properly configured

## Next Steps

1. **Fix RLS Policies**: Run the SQL script in `scripts/fix-rls-policies.sql`
2. **Test Complete Flow**: Use the `AssessmentFlow` component as a reference
3. **Customize**: Adapt the helper functions to your specific needs
4. **Deploy**: Integrate into your main application

The Supabase configuration is now ready for production use! 