# User Processes Documentation for Optimization

**Purpose:** Complete documentation of new user and returning user processes to identify optimization opportunities using Claude.

**Last Updated:** January 2025

---

## Table of Contents

1. [New User Process](#new-user-process)
2. [Returning User Process](#returning-user-process)
3. [Technical Implementation Details](#technical-implementation-details)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Optimization Opportunities](#optimization-opportunities)
6. [Key Metrics to Track](#key-metrics-to-track)

---

## New User Process

### Overview

The new user journey has been optimized from a 7-step process to a 3-5 step process, reducing friction and improving time-to-value.

### Complete Flow Diagram

```
┌─────────────────┐
│  Landing Page   │
│      (/)        │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    [Assessment]    [Direct Signup]
    (Optional)      (Get Started)
         │                 │
         ↓                 ↓
┌─────────────────────────────┐
│   Assessment Modal           │
│   (Captures: email, name)    │
└────────┬─────────────────────┘
         │
         │ [Saves to localStorage]
         │
         ↓
┌─────────────────────────────┐
│   Sign Up Page              │
│   (/signup?from=assessment) │
│   [Pre-filled if from assess]│
└────────┬─────────────────────┘
         │
         │ [POST /api/auth/register]
         │ [Creates user, JWT token]
         │
         ↓
┌─────────────────────────────┐
│   Quick Setup                │
│   (/quick-setup)             │
│   [3 questions]              │
└────────┬─────────────────────┘
         │
         │ [POST /api/profile/quick-setup]
         │ [Saves profile data]
         │
         ↓
┌─────────────────────────────┐
│   Career Dashboard           │
│   (/career-dashboard)        │
│   [Full access to features]  │
└─────────────────────────────┘
```

### Step-by-Step Breakdown

#### Step 1: Landing Page (`/`)

**User Actions:**
- Arrives at landing page
- Sees 4 assessment options:
  1. Determine Your Replacement Risk Due To AI
  2. Determine How Your Income Compares
  3. Determine Your 'Cuffing Season' Score
  4. Determine Your Layoff Risk
- Can click "Get Started" button (direct signup path)

**Technical Details:**
- Component: `LandingPage.tsx`
- No authentication required
- Analytics tracking enabled

**Optimization Notes:**
- Assessment completion is optional but encouraged
- Direct signup path available for users who want to skip assessment

---

#### Step 2: Assessment Completion (Optional)

**User Actions:**
1. Clicks an assessment button
2. Modal opens (`AssessmentModal.tsx`)
3. Enters:
   - Email address (required)
   - First name (optional)
   - Phone (optional)
4. Answers 7-8 questions (varies by assessment type)
5. Submits assessment
6. Sees results immediately in modal
7. Can download PDF (if implemented)
8. Clicks "Sign Up to Access Full Features"

**Data Captured:**
```json
{
  "email": "user@example.com",
  "firstName": "John",
  "phone": "1234567890",
  "assessmentType": "ai-risk",
  "answers": {
    "question1": "option1",
    "question2": "option2",
    ...
  },
  "completedAt": "2025-01-24T20:00:00Z"
}
```

**Storage:**
- Saved to `localStorage.setItem('mingus_assessment', JSON.stringify(data))`
- Also saved to database via `POST /api/assessments`

**API Calls:**
- `POST /api/assessments` - Submits assessment data
- Response includes: `assessment_id`, `results`, `email_sent`

**Navigation:**
- User clicks "Sign Up" button in results modal
- Navigates to: `/signup?from=assessment&type={assessmentType}`
- Modal closes before navigation

**Technical Details:**
- Component: `AssessmentModal.tsx`
- Results Component: `AssessmentResults.tsx`
- Email sent automatically via `EmailService`
- PDF download available (if assessment_id is present)

**Optimization Notes:**
- Results shown immediately (no wait for email)
- Assessment data pre-fills signup form
- Email confirmation shown in UI

---

#### Step 3: Registration / Sign Up (`/signup`)

**User Actions:**
1. Arrives at signup page
2. If from assessment:
   - Email field is **pre-filled**
   - First name field is **pre-filled**
   - Welcome message: "Complete your registration to see your full [Assessment Type] results!"
3. Fills in required fields:
   - Email address
   - Password (minimum 8 characters)
   - Confirm Password
   - First Name
4. Optionally fills:
   - Last Name
5. Submits form

**Form Validation:**
- Email format validation
- Password length (min 8 characters)
- Password confirmation match
- Required field checks

**API Call:**
```
POST /api/auth/register
Headers:
  Content-Type: application/json
Body:
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe" (optional)
}
```

**Response:**
```json
{
  "success": true,
  "user_id": 123,
  "email": "user@example.com",
  "name": "John",
  "token": "jwt_token_here",
  "message": "Registration successful"
}
```

**Storage:**
- JWT token saved to: `localStorage.setItem('mingus_token', token)`
- User data stored in context via `useAuth` hook
- Assessment data cleared from localStorage after successful registration

**Navigation:**
- Redirects to `/quick-setup` after 1.5 seconds
- If already authenticated, redirects to `/career-dashboard`

**Technical Details:**
- Component: `SignUpPage.tsx`
- Uses `useAuth` hook for registration
- Pre-fills from `localStorage.getItem('mingus_assessment')`
- Handles query params: `?from=assessment&type={type}`

**Optimization Notes:**
- Pre-filling reduces friction
- Welcome message personalizes experience
- Auto-redirect after registration

---

#### Step 4: Quick Setup (`/quick-setup`)

**User Actions:**
1. Arrives at quick setup page
2. Answers 3 questions:
   - **Question 1:** What's your annual income range?
     - Options: $30,000 - $50,000, $50,000 - $75,000, $75,000 - $100,000, $100,000+
   - **Question 2:** Where are you located?
     - Free text input: City, State or ZIP code
   - **Question 3:** What's your top financial priority?
     - Options:
       - Build Emergency Fund
       - Pay Off Debt
       - Start Investing
       - Save for Home
       - Plan for Retirement
3. Either:
   - Submits form → Saves data and goes to dashboard
   - Clicks "Skip for now" → Goes to dashboard without saving

**API Call:**
```
POST /api/profile/quick-setup
Headers:
  Content-Type: application/json
  Authorization: Bearer {jwt_token}
Body:
{
  "income_range": "$50,000 - $75,000",
  "location": "Atlanta, GA",
  "primary_goal": "Build Emergency Fund"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "setup_completed": true
}
```

**Storage:**
- Saved to `user_profiles` table in database
- Fields: `income_range`, `location`, `primary_goal`, `setup_completed`
- Assessment data cleared from localStorage

**Navigation:**
- Redirects to `/career-dashboard` after submission or skip

**Technical Details:**
- Component: `QuickSetup.tsx` (if exists) or handled in profile endpoints
- Requires authentication (JWT token)
- Skip option available

**Optimization Notes:**
- Only 3 questions (reduced from 6-step comprehensive profile)
- Skip option reduces friction
- Data can be updated later

---

#### Step 5: Career Dashboard (`/career-dashboard`)

**User Actions:**
- Accesses main dashboard
- Sees personalized content based on:
  - Assessment results (if completed)
  - Quick setup data (if completed)
  - User tier (default: 'budget')

**Features Available:**
- Career protection tools
- Financial wellness features
- Job matching recommendations
- Risk analytics
- Assessment results
- Profile management

**Technical Details:**
- Protected route (requires authentication)
- Uses JWT token for API calls
- Displays personalized content

**Optimization Notes:**
- Immediate value after quick setup
- Can complete full profile later from settings

---

### Alternative Flow: Direct Signup (No Assessment)

**Path:**
1. Landing Page → User clicks "Get Started"
2. Sign Up → No pre-filled data, no welcome message
3. Quick Setup → Same 3 questions
4. Career Dashboard → Full access

**Differences:**
- No assessment data in localStorage
- No pre-filled fields
- No personalized welcome message
- Same quick setup and dashboard access

---

### Legacy Flow: 6-Step Comprehensive Profile

**Note:** Available but not part of default onboarding. Users can access from profile settings.

**Steps:**
1. Personal Information (Age, Location, Education, Employment)
2. Financial Information (Income, Debt, Savings)
3. Monthly Expenses (Rent, Car, Insurance, etc.)
4. Important Dates (Birthday, Vacations, etc.)
5. Health & Wellness (Activity, Relationships, Stress)
6. Vehicle & Transportation (Vehicle expenses, Commute)
7. Goals (Emergency Fund, Debt Payoff, Savings)

**Current Status:** Optional, can be completed later

---

## Returning User Process

### Overview

Returning users have a streamlined login process that authenticates them and provides immediate access to their dashboard.

### Complete Flow Diagram

```
┌─────────────────┐
│  Landing Page   │
│      (/)        │
└────────┬────────┘
         │
         │ [Clicks "Sign In"]
         │
         ↓
┌─────────────────┐
│   Login Page    │
│     (/login)    │
└────────┬────────┘
         │
         │ [Enters email & password]
         │
         ↓
┌─────────────────────────────┐
│   POST /api/auth/login      │
│   [Validates credentials]   │
└────────┬─────────────────────┘
         │
         │ [Returns JWT token]
         │
         ↓
┌─────────────────────────────┐
│   Career Dashboard           │
│   (/career-dashboard)        │
│   [Full access to features]  │
└─────────────────────────────┘
```

### Step-by-Step Breakdown

#### Step 1: Access Login Page

**User Actions:**
- Clicks "Sign In" button on landing page
- Or navigates directly to `/login`
- Or tries to access protected route (auto-redirects to login)

**Technical Details:**
- Component: `LoginPage.tsx` (in `App.tsx`)
- No authentication required to view
- Protected routes redirect here if not authenticated

---

#### Step 2: Login Form Submission

**User Actions:**
1. Enters email address
2. Enters password
3. Clicks "Sign In" button
4. Sees loading state
5. Either:
   - Success → Redirected to dashboard
   - Error → Error message displayed

**Form Validation:**
- Email format validation
- Password required
- Client-side validation before API call

**API Call:**
```
POST /api/auth/login
Headers:
  Content-Type: application/json
Body:
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Success Response:**
```json
{
  "success": true,
  "user_id": 123,
  "email": "user@example.com",
  "name": "John",
  "token": "jwt_token_here",
  "message": "Login successful"
}
```

**Error Responses:**
- `401`: Invalid email or password
- `429`: Rate limit exceeded
- `500`: Server error

**Storage:**
- JWT token saved to: `localStorage.setItem('mingus_token', token)`
- User data stored in context via `useAuth` hook
- Last activity updated in database

**Navigation:**
- Redirects to `/career-dashboard` on success
- Stays on login page on error

**Technical Details:**
- Component: `LoginPage.tsx`
- Uses `useAuth` hook for login
- Rate limiting applied (IP-based)
- Password hashing verified server-side
- Last activity timestamp updated

**Optimization Notes:**
- Simple 2-field form
- Clear error messages
- Loading state during authentication
- Auto-redirect on success

---

#### Step 3: Career Dashboard Access

**User Actions:**
- Immediately redirected to dashboard
- Sees personalized content
- Full access to all features based on tier

**Features Available:**
- All features from new user dashboard
- Historical data (assessments, profile, etc.)
- Saved preferences
- Previous assessments and results

**Technical Details:**
- Protected route (requires authentication)
- JWT token used for all API calls
- User context loaded from token

**Optimization Notes:**
- Immediate access (no additional setup)
- Personalized experience
- Seamless transition from login

---

### Token Verification

**Process:**
- On app load, token is verified via `GET /api/auth/verify`
- If valid, user is authenticated
- If invalid/expired, user is logged out

**API Call:**
```
GET /api/auth/verify
Headers:
  Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "user_id": 123,
  "email": "user@example.com",
  "name": "John"
}
```

---

## Technical Implementation Details

### Authentication System

**Technology:** JWT (JSON Web Tokens)

**Token Storage:**
- `localStorage.getItem('mingus_token')`
- Sent in `Authorization: Bearer {token}` header

**Token Generation:**
- Backend: `backend/utils/jwt_utils.py`
- Expiration: Configurable (default: 7 days)

**Token Verification:**
- Middleware: `@require_auth` decorator
- Endpoint: `GET /api/auth/verify`

---

### Database Schema

**Users Table:**
```sql
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  tier TEXT DEFAULT 'budget',
  created_at TIMESTAMP,
  last_activity TIMESTAMP
);
```

**User Profiles Table:**
```sql
CREATE TABLE user_profiles (
  user_id INTEGER PRIMARY KEY,
  income_range TEXT,
  location TEXT,
  primary_goal TEXT,
  setup_completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Assessments Table:**
```sql
CREATE TABLE assessments (
  id INTEGER PRIMARY KEY,
  email TEXT,  -- Hashed
  first_name TEXT,
  assessment_type TEXT,
  answers TEXT,  -- JSON
  completed_at TIMESTAMP
);
```

---

### API Endpoints

#### Authentication Endpoints

**Register:**
- `POST /api/auth/register`
- Body: `{ email, password, firstName, lastName? }`
- Returns: `{ success, user_id, email, name, token }`

**Login:**
- `POST /api/auth/login`
- Body: `{ email, password }`
- Returns: `{ success, user_id, email, name, token }`

**Verify:**
- `GET /api/auth/verify`
- Headers: `Authorization: Bearer {token}`
- Returns: `{ success, user_id, email, name }`

#### Assessment Endpoints

**Submit Assessment:**
- `POST /api/assessments`
- Body: `{ email, firstName?, phone?, answers, assessmentType, completedAt }`
- Returns: `{ success, assessment_id, results, email_sent }`

**Get Results:**
- `GET /api/assessments/<id>/results`
- Returns: `{ success, assessment: {...} }`

**Download PDF:**
- `GET /api/assessments/<id>/download`
- Returns: PDF file

#### Profile Endpoints

**Quick Setup:**
- `POST /api/profile/quick-setup`
- Headers: `Authorization: Bearer {token}`
- Body: `{ income_range, location, primary_goal }`
- Returns: `{ success, message, setup_completed }`

---

### Frontend Components

**Key Components:**
- `LandingPage.tsx` - Landing page with assessments
- `AssessmentModal.tsx` - Assessment completion modal
- `AssessmentResults.tsx` - Results display
- `SignUpPage.tsx` - Registration form
- `LoginPage.tsx` - Login form (in App.tsx)
- `QuickSetup.tsx` - Quick setup form (if exists)

**Hooks:**
- `useAuth.tsx` - Authentication context and methods
- `useAnalytics.tsx` - Analytics tracking

**Routing:**
- React Router for navigation
- Protected routes with authentication check

---

## Data Flow Diagrams

### New User Data Flow

```
User Input
    ↓
localStorage (Assessment Data)
    ↓
API: POST /api/auth/register
    ↓
Database: users table
    ↓
JWT Token → localStorage
    ↓
API: POST /api/profile/quick-setup
    ↓
Database: user_profiles table
    ↓
Dashboard (Personalized Content)
```

### Returning User Data Flow

```
User Input (Email/Password)
    ↓
API: POST /api/auth/login
    ↓
Database: Verify credentials
    ↓
JWT Token → localStorage
    ↓
API: GET /api/auth/verify
    ↓
Dashboard (Personalized Content)
```

---

## Optimization Opportunities

### New User Process Optimizations

#### 1. Assessment Flow
**Current Issues:**
- Assessment is optional but encouraged
- Results shown in modal, then user must click to sign up
- Assessment data stored in localStorage (can be lost)

**Optimization Ideas:**
- Make assessment more prominent/required
- Auto-navigate to signup after assessment (with option to skip)
- Store assessment data server-side immediately
- Show assessment results on signup page as motivation
- Add progress indicators during assessment

#### 2. Registration Flow
**Current Issues:**
- Requires password confirmation (extra field)
- No password strength indicator
- No email verification
- Auto-redirect after 1.5 seconds (may be too fast/slow)

**Optimization Ideas:**
- Remove password confirmation (use show/hide toggle)
- Add password strength meter
- Implement email verification (optional)
- Make redirect timing configurable or user-controlled
- Add social login options (Google, Apple)
- Pre-validate email format before submission

#### 3. Quick Setup Flow
**Current Issues:**
- 3 questions may still feel like friction
- Skip option may reduce data quality
- No progress indicator
- Location input is free text (no validation)

**Optimization Ideas:**
- Reduce to 2 questions (income + goal)
- Make location optional or use ZIP code lookup
- Add progress bar (1 of 3, 2 of 3, etc.)
- Show value proposition for each question
- Pre-fill location from IP geolocation
- Make skip more prominent or remove it

#### 4. Onboarding Completion
**Current Issues:**
- No welcome tour/tutorial
- No feature highlights
- No onboarding checklist
- Users may not know what to do next

**Optimization Ideas:**
- Add interactive product tour
- Highlight key features on first visit
- Show onboarding checklist
- Provide "Getting Started" guide
- Send welcome email with next steps

---

### Returning User Process Optimizations

#### 1. Login Flow
**Current Issues:**
- Only email/password login
- No "Remember Me" option
- No password reset on login page
- No social login

**Optimization Ideas:**
- Add "Remember Me" checkbox
- Add "Forgot Password" link
- Add social login options
- Add biometric login (if supported)
- Show last login time/device
- Add 2FA option

#### 2. Session Management
**Current Issues:**
- Token stored in localStorage (XSS risk)
- No token refresh mechanism
- No session timeout warning

**Optimization Ideas:**
- Use httpOnly cookies for tokens
- Implement token refresh
- Add session timeout warning
- Show active sessions
- Allow session management

#### 3. Dashboard Experience
**Current Issues:**
- No personalized welcome back message
- No "What's New" section
- No activity summary

**Optimization Ideas:**
- Show personalized welcome message
- Highlight new features since last visit
- Show activity summary
- Suggest next actions
- Show incomplete tasks

---

### Cross-Process Optimizations

#### 1. Data Pre-filling
**Current:**
- Assessment → Signup (email, first name)
- No other pre-filling

**Optimization Ideas:**
- Pre-fill location from IP
- Pre-fill income from assessment answers
- Pre-fill goal from assessment type
- Use browser autofill more effectively

#### 2. Error Handling
**Current:**
- Basic error messages
- No retry mechanisms
- No offline support

**Optimization Ideas:**
- More descriptive error messages
- Add retry buttons
- Show offline mode
- Better network error handling

#### 3. Analytics & Tracking
**Current:**
- Basic analytics
- No conversion funnel tracking
- No drop-off analysis

**Optimization Ideas:**
- Track conversion funnel
- Identify drop-off points
- A/B test different flows
- Track time to complete each step
- Measure completion rates

---

## Key Metrics to Track

### New User Metrics

1. **Landing Page:**
   - Bounce rate
   - Assessment click-through rate
   - Direct signup click rate

2. **Assessment:**
   - Completion rate
   - Average time to complete
   - Drop-off by question
   - Email capture rate

3. **Registration:**
   - Signup conversion rate
   - Form completion time
   - Validation error rate
   - Pre-fill usage rate

4. **Quick Setup:**
   - Completion rate
   - Skip rate
   - Average time to complete
   - Question-level drop-off

5. **Overall:**
   - Time from landing to dashboard
   - Overall conversion rate
   - Drop-off points
   - Completion rate by entry point

### Returning User Metrics

1. **Login:**
   - Login success rate
   - Login failure rate
   - Average login time
   - Password reset rate

2. **Session:**
   - Session duration
   - Return frequency
   - Feature usage
   - Engagement score

---

## Questions for Claude Optimization

### New User Process

1. How can we reduce the number of steps from landing to dashboard?
2. What's the optimal number of questions in quick setup?
3. Should assessment be required or optional?
4. How can we improve conversion at each step?
5. What's the best way to handle pre-filling data?
6. Should we add email verification?
7. How can we reduce form abandonment?
8. What's the optimal redirect timing?

### Returning User Process

1. How can we improve login success rate?
2. Should we add social login?
3. How can we improve session management?
4. What's the best welcome-back experience?
5. How can we increase engagement after login?

### General

1. What A/B tests should we run?
2. How can we improve error handling?
3. What analytics should we prioritize?
4. How can we reduce technical friction?
5. What's the optimal user experience flow?

---

## Related Documentation

- `CURRENT_NEW_USER_STEPS.md` - Detailed new user steps
- `REGISTRATION_WORKFLOWS.md` - Registration workflows
- `New User Workflow/README.md` - New user workflow docs
- `ASSESSMENT_COMPLETION_BUTTONS.md` - Assessment button details
- `FIXES_APPLIED.md` - Recent fixes and improvements

---

**End of Document**
