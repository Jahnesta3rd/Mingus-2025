# User Registration Workflows - Complete Documentation

This document displays all existing workflows for registering a new user in the Mingus application.

---

## Overview

The Mingus application supports **two main registration workflows**:

1. **Assessment → Registration → Quick Setup → Dashboard** (with pre-filled data)
2. **Direct Registration → Quick Setup → Dashboard** (without assessment)

Both workflows converge at the Quick Setup step and lead to the Career Dashboard.

---

## Workflow 1: Assessment-Based Registration

### Flow Diagram
```
Landing Page (/)
    ↓
Assessment Modal (on landing page)
    ↓ [Saves to localStorage]
Sign Up Page (/signup?from=assessment)
    ↓ [Pre-fills email & first name]
Account Creation (POST /api/auth/register)
    ↓ [Creates user, stores JWT token]
Quick Setup (/quick-setup?from=assessment)
    ↓ [Saves profile data]
Career Dashboard (/career-dashboard)
```

### Step-by-Step Process

#### Step 1: Landing Page
- **URL:** `/`
- **User Action:** Arrives at landing page
- **Options Available:**
  - Determine Your Replacement Risk Due To AI
  - Determine How Your Income Compares
  - Determine Your 'Cuffing Season' Score
  - Determine Your Layoff Risk

#### Step 2: Assessment Completion (Optional Entry Point)
- **Location:** Modal overlay on landing page
- **User Actions:**
  1. Clicks an assessment button
  2. Enters email and first name
  3. Answers 7-8 assessment questions (varies by type)
  4. Submits assessment

- **Data Captured:**
  ```json
  {
    "email": "user@example.com",
    "firstName": "John",
    "assessmentType": "ai-risk",
    "answers": [...],
    "completedAt": "2025-01-XX..."
  }
  ```

- **Storage:** Data saved to `localStorage.setItem('mingus_assessment', JSON.stringify(data))`
- **Navigation:** Auto-redirects to `/signup?from=assessment&type=ai-risk` after 1.5 seconds

#### Step 3: Registration / Sign Up
- **URL:** `/signup?from=assessment&type=ai-risk`
- **Component:** `SignUpPage.tsx`
- **Pre-filled Data:**
  - ✅ Email address (from assessment)
  - ✅ First name (from assessment)
  
- **Welcome Message:** 
  - "Complete your registration to see your full [Assessment Type] results!"

- **Form Fields:**
  - **Required:**
    - Email address (pre-filled)
    - Password (minimum 8 characters)
    - Confirm Password
    - First Name (pre-filled)
  - **Optional:**
    - Last Name

- **Client-Side Validation:**
  - Email format check (must contain '@')
  - Password length (minimum 8 characters)
  - Password confirmation match
  - First name required

- **Registration Process:**
  1. Form validation
  2. API call: `POST /api/auth/register`
  3. Request body:
     ```json
     {
       "email": "user@example.com",
       "password": "password123",
       "first_name": "John",
       "last_name": "Doe"
     }
     ```

- **Backend Processing** (`backend/api/auth_endpoints.py`):
  1. Rate limiting check (IP-based)
  2. Validate required fields (email, password, first_name)
  3. Validate email format
  4. Validate password length (≥ 8 characters)
  5. Check if user already exists (409 Conflict if exists)
  6. Generate unique `user_id` (UUID v4)
  7. Hash password using `hash_password()` function
  8. Create user record:
     - `user_id`: UUID
     - `email`: Lowercase, trimmed
     - `first_name`: Trimmed
     - `last_name`: Optional, trimmed
     - `password_hash`: Hashed password
     - `tier`: 'budget' (default)
     - `created_at`: Current UTC timestamp
     - `updated_at`: Current UTC timestamp
  9. Commit to database
  10. Generate JWT token using `generate_jwt_token(user_id, email)`
  11. Return response:
      ```json
      {
        "success": true,
        "user_id": "uuid-here",
        "email": "user@example.com",
        "name": "John",
        "token": "jwt-token-here",
        "message": "Registration successful"
      }
      ```

- **Frontend Response Handling** (`frontend/src/hooks/useAuth.tsx`):
  1. Store JWT token: `localStorage.setItem('mingus_token', token)`
  2. Update auth context with user data
  3. Set success state
  4. Navigate to `/quick-setup?from=assessment` after 1.5 seconds

#### Step 4: Quick Setup
- **URL:** `/quick-setup?from=assessment`
- **Component:** `QuickSetup.tsx`
- **Special Features:**
  - Shows assessment completion badge
  - Personalized message: "Let's personalize your experience based on your assessment"

- **Questions (3 total):**
  1. **What's your annual income range?**
     - Options:
       - $30,000 - $50,000 (`30-50k`)
       - $50,000 - $75,000 (`50-75k`)
       - $75,000 - $100,000 (`75-100k`)
       - $100,000+ (`100k+`)
  
  2. **Where are you located?**
     - Free text input: City, State or ZIP code
  
  3. **What's your top financial priority?**
     - Options:
       - Build Emergency Fund (`emergency-fund`)
       - Pay Off Debt (`debt-payoff`)
       - Start Investing (`investing`)
       - Save for Home (`home-purchase`)
       - Plan for Retirement (`retirement`)

- **User Options:**
  - **Submit:** Saves data and navigates to dashboard
  - **Skip:** Goes directly to dashboard without saving

- **Submission Process:**
  1. Validates all 3 fields are filled
  2. API call: `POST /api/profile/quick-setup`
  3. Headers:
     ```
     Authorization: Bearer <jwt-token>
     Content-Type: application/json
     ```
  4. Request body:
     ```json
     {
       "incomeRange": "75-100k",
       "location": "San Francisco, CA",
       "primaryGoal": "emergency-fund"
     }
     ```
  5. On success:
     - Clears assessment data: `localStorage.removeItem('mingus_assessment')`
     - Navigates to `/career-dashboard`

#### Step 5: Career Dashboard
- **URL:** `/career-dashboard`
- **Access:** Protected route (requires authentication)
- **Features Available:**
  - Full access to career protection features
  - Financial wellness tools
  - Job matching recommendations
  - Risk analytics
  - Assessment results (if completed)
  - Features based on user tier

---

## Workflow 2: Direct Registration (No Assessment)

### Flow Diagram
```
Landing Page (/)
    ↓ [User clicks "Get Started" or navigates directly]
Sign Up Page (/signup or /signup?source=cta)
    ↓ [No pre-filled data]
Account Creation (POST /api/auth/register)
    ↓ [Creates user, stores JWT token]
Quick Setup (/quick-setup)
    ↓ [Saves profile data]
Career Dashboard (/career-dashboard)
```

### Step-by-Step Process

#### Step 1: Landing Page
- **URL:** `/`
- **User Action:** Clicks "Get Started" button or navigates directly to signup
- **Navigation:** Goes to `/signup` or `/signup?source=cta`

#### Step 2: Registration / Sign Up
- **URL:** `/signup` or `/signup?source=cta`
- **Component:** `SignUpPage.tsx`
- **Pre-filled Data:**
  - ❌ No pre-filled data (all fields empty)
  
- **Welcome Message (if from CTA):**
  - "Welcome to Mingus! Let's get you started on your financial wellness journey."

- **Form Fields:** Same as Workflow 1
  - **Required:**
    - Email address
    - Password (minimum 8 characters)
    - Confirm Password
    - First Name
  - **Optional:**
    - Last Name

- **Registration Process:** Identical to Workflow 1, Step 3
- **Navigation:** Redirects to `/quick-setup` (or `/quick-setup?source=cta`) after 1.5 seconds

#### Step 3: Quick Setup
- **URL:** `/quick-setup` or `/quick-setup?source=cta`
- **Component:** `QuickSetup.tsx`
- **Standard Message:** "Let's personalize your experience"
- **Questions:** Same 3 questions as Workflow 1, Step 4
- **Submission Process:** Identical to Workflow 1, Step 4

#### Step 4: Career Dashboard
- **URL:** `/career-dashboard`
- **Access:** Same as Workflow 1, Step 5

---

## Technical Implementation Details

### Frontend Components

#### SignUpPage Component
- **File:** `frontend/src/pages/SignUpPage.tsx`
- **Key Features:**
  - Pre-fills data from `localStorage.getItem('mingus_assessment')`
  - Validates form before submission
  - Handles entry source tracking (`assessment`, `cta`, or `null`)
  - Shows personalized welcome messages
  - Redirects authenticated users to dashboard
  - Uses `useAuth` hook for registration

#### QuickSetup Component
- **File:** `frontend/src/components/QuickSetup.tsx`
- **Key Features:**
  - Detects assessment completion from URL params
  - Shows assessment badge if applicable
  - Validates all fields before submission
  - Provides skip option
  - Clears assessment data after successful submission

#### useAuth Hook
- **File:** `frontend/src/hooks/useAuth.tsx`
- **Registration Function:**
  ```typescript
  register(email: string, password: string, firstName: string, lastName?: string): Promise<void>
  ```
- **Process:**
  1. Makes POST request to `/api/auth/register`
  2. Handles errors and network issues
  3. Stores JWT token in localStorage
  4. Updates auth context
  5. Throws errors for frontend handling

### Backend Endpoints

#### Registration Endpoint
- **Route:** `POST /api/auth/register`
- **File:** `backend/api/auth_endpoints.py`
- **Security Features:**
  - Rate limiting (IP-based)
  - Password hashing
  - Email validation
  - Duplicate user check
  - JWT token generation

- **Request Format:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```

- **Response Format (Success - 201):**
  ```json
  {
    "success": true,
    "user_id": "uuid-here",
    "email": "user@example.com",
    "name": "John",
    "token": "jwt-token-here",
    "message": "Registration successful"
  }
  ```

- **Response Format (Error - 400/409/429/500):**
  ```json
  {
    "success": false,
    "error": "Error message here"
  }
  ```

#### Quick Setup Endpoint
- **Route:** `POST /api/profile/quick-setup`
- **File:** `backend/api/profile_endpoints.py`
- **Authentication:** Required (JWT Bearer token)
- **Request Format:**
  ```json
  {
    "incomeRange": "75-100k",
    "location": "San Francisco, CA",
    "primaryGoal": "emergency-fund"
  }
  ```

### Data Storage

#### localStorage Keys
- `mingus_assessment`: Stores assessment data
  ```json
  {
    "email": "user@example.com",
    "firstName": "John",
    "assessmentType": "ai-risk",
    "completedAt": "2025-01-XX..."
  }
  ```
- `mingus_token`: Stores JWT authentication token

#### Database Tables
- **users**: Stores user account information
  - `user_id` (UUID, Primary Key)
  - `email` (Unique)
  - `first_name`
  - `last_name` (Nullable)
  - `password_hash`
  - `tier` (Default: 'budget')
  - `created_at`
  - `updated_at`

- **user_profiles**: Stores quick setup data
  - `user_id` (Foreign Key)
  - `income_range`
  - `location`
  - `primary_goal`
  - `setup_completed` (Boolean)

---

## Error Handling

### Registration Errors

| Error Code | Scenario | User Message |
|------------|----------|--------------|
| 400 | Missing required fields | "Email is required" / "Password is required" / "First name is required" |
| 400 | Invalid email format | "Invalid email format" |
| 400 | Password too short | "Password must be at least 8 characters long" |
| 409 | User already exists | "User with this email already exists" |
| 429 | Rate limit exceeded | "Rate limit exceeded" |
| 500 | Server error | "Registration failed. Please try again." (production) or detailed error (development) |

### Quick Setup Errors

| Error Code | Scenario | User Message |
|------------|----------|--------------|
| 401 | Missing/invalid token | "Authentication required. Please log in again." |
| 400 | Missing fields | "Failed to save profile setup" |
| 500 | Server error | "Setup error occurred" |

---

## Validation Rules

### Email
- Must contain '@' symbol
- Must have '.' after '@'
- Converted to lowercase
- Trimmed of whitespace

### Password
- Minimum 8 characters
- No maximum length enforced
- Hashed using secure hashing algorithm

### First Name
- Required
- Trimmed of whitespace

### Last Name
- Optional
- Trimmed of whitespace if provided

### Quick Setup Fields
- All 3 fields required for submission
- Income range: Must be one of the predefined options
- Location: Free text (no validation)
- Primary goal: Must be one of the predefined options

---

## Security Features

1. **Rate Limiting:** IP-based rate limiting on registration endpoint
2. **Password Hashing:** Passwords are hashed before storage (never stored in plain text)
3. **JWT Authentication:** Secure token-based authentication
4. **Input Validation:** Both client-side and server-side validation
5. **SQL Injection Prevention:** Using ORM (SQLAlchemy) with parameterized queries
6. **XSS Prevention:** React automatically escapes user input

---

## Alternative Flows

### Legacy 6-Step Profile Setup
- **Status:** Available but not part of default onboarding
- **Access:** From profile settings after registration
- **Steps:**
  1. Personal Information
  2. Financial Information
  3. Monthly Expenses
  4. Important Dates
  5. Health & Wellness
  6. Goals

### Skip Quick Setup
- Users can click "Skip for now" on Quick Setup page
- Navigates directly to dashboard
- No profile data saved
- Can complete later from settings

---

## Summary

### Current Optimized Flow
1. Landing Page
2. Assessment (Optional) → Saves to localStorage
3. Sign Up → Pre-fills if from assessment
4. Quick Setup (3 questions) → Can skip
5. Career Dashboard

### Key Improvements Over Legacy Flow
- ✅ Reduced from 7 steps to 3-5 steps
- ✅ Pre-fills data from assessment
- ✅ Faster time to value (dashboard access)
- ✅ Optional comprehensive profile available later
- ✅ Skip option for quick setup

---

**Last Updated:** January 2025  
**Based on:** Current codebase implementation in `frontend/src/pages/SignUpPage.tsx`, `backend/api/auth_endpoints.py`, and `frontend/src/components/QuickSetup.tsx`
