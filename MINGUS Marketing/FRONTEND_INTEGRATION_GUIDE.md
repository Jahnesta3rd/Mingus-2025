# MINGUS Frontend Integration Guide

## 🚀 Complete Frontend-Backend Integration

This guide covers the complete integration of your React frontend with the backend PDF generation and email services.

## 📁 File Structure

```
src/
├── components/
│   ├── IntegratedAssessmentFlow.jsx    # Complete assessment flow
│   ├── AssessmentResults.tsx           # Results display component
│   └── EmailConfirmation.jsx           # Email confirmation component
├── services/
│   ├── emailService.js                 # Email and PDF API calls
│   └── supabase.js                     # Database operations
├── lib/
│   └── supabase.js                     # Supabase client configuration
└── utils/
    └── assessmentUtils.js              # Helper functions
```

## 🔧 Environment Configuration

### Frontend Environment Variables

Create `.env.local` in your React app root:

```env
# Backend API URL
REACT_APP_API_URL=http://localhost:3001

# Supabase Configuration
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key

# Optional: Analytics
REACT_APP_GA_ID=your-google-analytics-id
```

## 🎯 Complete User Flow

### 1. Email Collection & Confirmation

```jsx
// User enters email → Confirmation email sent → User clicks link → Assessment starts
const handleEmailSubmit = async (email) => {
  // 1. Create lead in database
  const leadResult = await createLead(email)
  
  // 2. Send confirmation email
  const emailResult = await sendConfirmationEmail(email, leadResult.data.id)
  
  // 3. Show confirmation screen
  setStep('confirmation')
}
```

### 2. Assessment Completion

```jsx
// User answers questions → Score calculated → Segment determined → PDF generated
const handleAssessmentComplete = async () => {
  // 1. Calculate score and determine segment
  const score = calculateScore(responses)
  const segment = determineSegment(score)
  
  // 2. Complete assessment in database
  await completeAssessment(email, responses, score)
  
  // 3. Generate PDF report
  const pdfResult = await generateReport(leadId)
  
  // 4. Send results email with PDF
  await sendAssessmentResults(email, segment, score, firstName, leadId, pdfResult.downloadUrl)
  
  // 5. Show results with download link
  setStep('results')
}
```

## 📄 PDF Generation Integration

### Backend API Call

```javascript
// src/services/emailService.js
export const generateReport = async (leadId) => {
  const response = await fetch(`${API_BASE_URL}/api/generate-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ leadId })
  })
  
  const result = await response.json()
  return result.success ? 
    { success: true, downloadUrl: result.downloadUrl, filename: result.filename } :
    { success: false, error: result.error }
}
```

### Frontend Usage

```jsx
// In IntegratedAssessmentFlow.jsx
const handleAssessmentComplete = async () => {
  setGeneratingPDF(true)
  
  // Generate PDF
  const pdfResult = await generateReport(leadId)
  
  if (pdfResult.success) {
    setPdfDownloadUrl(pdfResult.downloadUrl)
    console.log('PDF ready:', pdfResult.downloadUrl)
  } else {
    console.error('PDF generation failed:', pdfResult.error)
  }
  
  setGeneratingPDF(false)
}
```

## 📧 Email Integration

### Confirmation Email

```javascript
// Send confirmation email with assessment link
export const sendConfirmationEmail = async (email, leadId) => {
  const response = await fetch(`${API_BASE_URL}/api/send-confirmation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, leadId })
  })
  
  return response.json()
}
```

### Results Email with PDF

```javascript
// Send results email with PDF download link
export const sendAssessmentResults = async (email, userSegment, score, firstName, leadId, pdfDownloadUrl) => {
  const response = await fetch(`${API_BASE_URL}/api/send-results`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      email, 
      userSegment, 
      score, 
      firstName, 
      leadId,
      pdfDownloadUrl 
    })
  })
  
  return response.json()
}
```

## 🎨 UI Components

### Email Collection Screen

```jsx
{step === 'email' && (
  <div>
    <h2>Money & Relationship Assessment</h2>
    <form onSubmit={handleEmailSubmit}>
      <input 
        type="email" 
        value={email} 
        onChange={(e) => setEmail(e.target.value)}
        placeholder="your@email.com"
        required 
      />
      <button type="submit">Start Free Assessment</button>
    </form>
    <p>Get a FREE personalized PDF action plan!</p>
  </div>
)}
```

### Email Confirmation Screen

```jsx
{step === 'confirmation' && (
  <div className="text-center">
    <h2>Check Your Email</h2>
    <p>We've sent a confirmation link to <strong>{email}</strong></p>
    <div className="bg-blue-50 p-4 rounded-lg">
      <ol>
        <li>Check your inbox (and spam folder)</li>
        <li>Click the confirmation link</li>
        <li>Complete your assessment</li>
        <li>Get your FREE personalized PDF report</li>
      </ol>
    </div>
  </div>
)}
```

### Assessment Questions

```jsx
{step === 'assessment' && (
  <div>
    <div className="progress-bar">
      <span>Question {currentQuestion + 1} of {questions.length}</span>
      <div className="progress-fill" style={{width: `${progress}%`}}></div>
    </div>
    
    <h3>{questions[currentQuestion]?.question_text}</h3>
    
    {questions[currentQuestion]?.question_type === 'radio' && (
      <div className="options">
        {options.map(option => (
          <button 
            key={option.value}
            onClick={() => handleQuestionResponse(questionId, option.value, option.points)}
          >
            {option.label}
          </button>
        ))}
      </div>
    )}
  </div>
)}
```

### PDF Generation Screen

```jsx
{step === 'generating' && (
  <div className="text-center">
    <div className="spinner"></div>
    <h2>Creating Your Personal Report</h2>
    <p>We're analyzing your responses and generating your custom action plan...</p>
    
    <div className="progress-steps">
      <div className="step completed">Assessment completed ✓</div>
      <div className="step active">Generating your PDF report...</div>
      <div className="step">Sending email with download link</div>
    </div>
  </div>
)}
```

### Results Screen with PDF Download

```jsx
{step === 'results' && (
  <div className="text-center">
    <h2>Assessment Complete!</h2>
    
    <div className="results-card">
      <h3>Your Results:</h3>
      <p className="segment">{getUserSegmentDisplay(userSegment)}</p>
      <p className="score">Score: {totalScore}/100</p>
      <p className="plan">Recommended Plan: {getProductTier(totalScore)}</p>
    </div>

    {/* PDF Download Section */}
    {pdfDownloadUrl && (
      <div className="pdf-download">
        <h4>Your Free Personal Action Plan</h4>
        <p>We've created a detailed 10-page report with your personalized strategies.</p>
        <button onClick={() => window.open(pdfDownloadUrl, '_blank')}>
          📥 Download Your Free Report
        </button>
      </div>
    )}

    <button className="cta-button">
      Get Your Personal Finance Plan
    </button>
  </div>
)}
```

## 🔄 State Management

### Component State

```jsx
const [step, setStep] = useState('email') // email, confirmation, assessment, generating, results
const [email, setEmail] = useState('')
const [firstName, setFirstName] = useState('')
const [leadId, setLeadId] = useState(null)
const [questions, setQuestions] = useState([])
const [currentQuestion, setCurrentQuestion] = useState(0)
const [responses, setResponses] = useState({})
const [totalScore, setTotalScore] = useState(0)
const [userSegment, setUserSegment] = useState('')
const [pdfDownloadUrl, setPdfDownloadUrl] = useState(null)
const [generatingPDF, setGeneratingPDF] = useState(false)
const [loading, setLoading] = useState(false)
```

### URL Parameter Handling

```jsx
useEffect(() => {
  // Check if user is coming back from email confirmation
  const urlParams = new URLSearchParams(window.location.search)
  const confirmToken = urlParams.get('confirm')
  const emailParam = urlParams.get('email')
  
  if (confirmToken && emailParam) {
    handleEmailConfirmation(emailParam)
  }
}, [])
```

## 🎨 Styling & UX

### Tailwind CSS Classes

```jsx
// Progress bar
<div className="w-full bg-gray-200 rounded-full h-2">
  <div 
    className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
    style={{ width: `${progress}%` }}
  ></div>
</div>

// Segment-specific colors
const getSegmentColor = (segment) => {
  const colors = {
    'stress-free': 'green',
    'relationship-spender': 'orange',
    'emotional-manager': 'purple',
    'crisis-mode': 'red'
  }
  return colors[segment] || 'blue'
}

// Loading states
{loading && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white p-6 rounded-lg">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p className="mt-2 text-center text-gray-600">Loading...</p>
    </div>
  </div>
)}
```

## 🔧 Error Handling

### API Error Handling

```javascript
// Generic error handler
const handleApiError = (error, fallbackMessage) => {
  console.error('API Error:', error)
  
  if (error.response?.status === 404) {
    return { success: false, error: 'Resource not found' }
  }
  
  if (error.response?.status === 500) {
    return { success: false, error: 'Server error - please try again' }
  }
  
  return { success: false, error: fallbackMessage || 'Something went wrong' }
}

// Usage in components
try {
  const result = await generateReport(leadId)
  if (!result.success) {
    console.error('PDF generation failed:', result.error)
    // Show user-friendly error message
    setError('PDF generation failed. Your results are still available.')
  }
} catch (error) {
  handleApiError(error, 'Failed to generate PDF')
}
```

### User-Friendly Error Messages

```jsx
// Error state in component
const [error, setError] = useState(null)

{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
    <p className="text-red-800 text-sm">{error}</p>
    <button 
      onClick={() => setError(null)}
      className="text-red-600 hover:text-red-800 text-xs mt-2"
    >
      Dismiss
    </button>
  </div>
)}
```

## 📊 Analytics Integration

### Google Analytics Events

```javascript
// Track assessment completion
const trackAssessmentComplete = (segment, score) => {
  if (window.gtag) {
    window.gtag('event', 'assessment_complete', {
      event_category: 'engagement',
      event_label: segment,
      value: score
    })
  }
}

// Track PDF download
const trackPDFDownload = (segment) => {
  if (window.gtag) {
    window.gtag('event', 'pdf_download', {
      event_category: 'conversion',
      event_label: segment
    })
  }
}

// Usage
const handleAssessmentComplete = async () => {
  // ... assessment logic ...
  
  trackAssessmentComplete(userSegment, totalScore)
  
  if (pdfResult.success) {
    trackPDFDownload(userSegment)
  }
}
```

## 🧪 Testing

### Component Testing

```javascript
// Test PDF generation flow
test('generates PDF and shows download link', async () => {
  const mockGenerateReport = jest.fn().mockResolvedValue({
    success: true,
    downloadUrl: 'http://localhost:3001/api/download/test.pdf',
    filename: 'test.pdf'
  })
  
  render(<IntegratedAssessmentFlow />)
  
  // Complete assessment
  fireEvent.click(screen.getByText('Complete Assessment'))
  
  // Wait for PDF generation
  await waitFor(() => {
    expect(mockGenerateReport).toHaveBeenCalled()
  })
  
  // Check for download link
  expect(screen.getByText('Download Your Free Report')).toBeInTheDocument()
})
```

### API Testing

```javascript
// Test email service
test('sends confirmation email successfully', async () => {
  const mockFetch = jest.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ success: true, emailId: 'test-123' })
  })
  
  global.fetch = mockFetch
  
  const result = await sendConfirmationEmail('test@example.com', 'lead-123')
  
  expect(result.success).toBe(true)
  expect(mockFetch).toHaveBeenCalledWith(
    'http://localhost:3001/api/send-confirmation',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ email: 'test@example.com', leadId: 'lead-123' })
    })
  )
})
```

## 🚀 Performance Optimization

### Lazy Loading

```jsx
// Lazy load heavy components
const PDFViewer = React.lazy(() => import('./PDFViewer'))
const Analytics = React.lazy(() => import('./Analytics'))

// Only load when needed
{showPDF && (
  <Suspense fallback={<div>Loading PDF...</div>}>
    <PDFViewer url={pdfDownloadUrl} />
  </Suspense>
)}
```

### Memoization

```jsx
// Memoize expensive calculations
const userSegment = useMemo(() => {
  return determineSegment(totalScore)
}, [totalScore])

const productTier = useMemo(() => {
  return getProductTier(totalScore)
}, [totalScore])
```

## 🔒 Security Considerations

### Input Validation

```javascript
// Validate email format
const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Sanitize user input
const sanitizeInput = (input) => {
  return input.trim().replace(/[<>]/g, '')
}
```

### API Security

```javascript
// Add CSRF protection
const addCSRFToken = (headers) => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content
  if (token) {
    headers['X-CSRF-Token'] = token
  }
  return headers
}

// Use in API calls
const response = await fetch(url, {
  method: 'POST',
  headers: addCSRFToken({
    'Content-Type': 'application/json'
  }),
  body: JSON.stringify(data)
})
```

## 📱 Mobile Responsiveness

### Responsive Design

```jsx
// Mobile-first approach
<div className="max-w-md mx-auto p-4 sm:p-6 bg-white rounded-lg shadow-lg">
  <h2 className="text-xl sm:text-2xl font-bold mb-4 text-center">
    Money & Relationship Assessment
  </h2>
  
  <div className="space-y-4 sm:space-y-6">
    {/* Content */}
  </div>
</div>
```

### Touch-Friendly Buttons

```jsx
// Large touch targets for mobile
<button className="w-full p-4 sm:p-3 text-left border border-gray-300 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 focus:ring-2 focus:ring-blue-500 min-h-[44px]">
  {option.label}
</button>
```

## 🎉 Success Metrics

### Conversion Tracking

```javascript
// Track key conversion points
const trackConversion = (step, data) => {
  if (window.gtag) {
    window.gtag('event', 'conversion', {
      send_to: 'AW-CONVERSION_ID/CONVERSION_LABEL',
      value: data.value,
      currency: 'USD',
      transaction_id: data.transactionId
    })
  }
}

// Usage
trackConversion('assessment_complete', {
  value: 10.00,
  transactionId: leadId
})
```

### User Journey Analytics

```javascript
// Track user progression through funnel
const trackStep = (stepName) => {
  if (window.gtag) {
    window.gtag('event', 'step_view', {
      event_category: 'funnel',
      event_label: stepName
    })
  }
}

// Track in component
useEffect(() => {
  trackStep(step)
}, [step])
```

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] API endpoints tested
- [ ] PDF generation working
- [ ] Email delivery verified
- [ ] Mobile responsiveness checked
- [ ] Analytics tracking implemented
- [ ] Error handling tested
- [ ] Performance optimized

### Post-Deployment

- [ ] Monitor PDF generation success rate
- [ ] Track email delivery rates
- [ ] Monitor user conversion funnel
- [ ] Check server performance
- [ ] Verify analytics data
- [ ] Test error scenarios

Your MINGUS frontend is now fully integrated with the backend PDF generation and email services! 🎉 