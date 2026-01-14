# Current New User Onboarding Steps

Based on the codebase and your experience, here are the existing steps for a new user:

---

## Current User Flow (As Implemented)

### Step 1: Landing Page
**URL:** `https://test.mingusapp.com/`  
**Action:** User arrives at the landing page
- Sees 4 assessment options:
  - Determine Your Replacement Risk Due To AI
  - Determine How Your Income Compares
  - Determine Your 'Cuffing Season' Score
  - Determine Your Layoff Risk

---

### Step 2: Assessment Completion (Optional)
**URL:** Modal overlay on landing page  
**Action:** User clicks an assessment button and completes it
- Enters email and first name
- Answers assessment questions (7-8 questions depending on type)
- Submits assessment
- **Result:** Assessment data saved to localStorage
- **Navigation:** Automatically redirects to `/signup?from=assessment` after 1.5 seconds

**Data Captured:**
- Email address
- First name
- Assessment type
- Assessment answers
- Completion timestamp

---

### Step 3: Registration / Sign Up
**URL:** `https://test.mingusapp.com/signup`  
**Action:** User creates an account

**If coming from assessment:**
- Email field is **pre-filled** from assessment
- First name field is **pre-filled** from assessment
- Welcome message appears: "Complete your registration to see your full [Assessment Type] results!"

**Required Fields:**
- Email address
- Password (minimum 8 characters)
- Confirm Password
- First Name

**Optional Fields:**
- Last Name

**After Submission:**
- Account created in database
- User authenticated (JWT token stored)
- **Navigation:** Redirects to `/quick-setup` after 1.5 seconds

---

### Step 4: Quick Setup (NEW - Simplified Profile)
**URL:** `https://test.mingusapp.com/quick-setup`  
**Action:** User completes 3 quick questions

**Questions:**
1. **What's your annual income range?**
   - Options: $30,000 - $50,000, $50,000 - $75,000, $75,000 - $100,000, $100,000+

2. **Where are you located?**
   - Free text input: City, State or ZIP code

3. **What's your top financial priority?**
   - Options:
     - Build Emergency Fund
     - Pay Off Debt
     - Start Investing
     - Save for Home
     - Plan for Retirement

**Options:**
- Submit: Saves data and goes to dashboard
- Skip: Goes directly to dashboard without saving

**After Submission:**
- Data saved to `user_profiles` database table
- Assessment data cleared from localStorage
- **Navigation:** Redirects to `/career-dashboard`

---

### Step 5: Career Dashboard
**URL:** `https://test.mingusapp.com/career-dashboard`  
**Action:** User accesses main dashboard
- Full access to career protection features
- Financial wellness tools
- Job matching recommendations
- Risk analytics
- And other features based on tier

---

## Alternative Flow (Direct Signup - No Assessment)

If user goes directly to signup without completing an assessment:

1. **Landing Page** → User clicks "Get Started" or navigates directly
2. **Sign Up** → No pre-filled data, no welcome message
3. **Quick Setup** → Same 3 questions
4. **Career Dashboard** → Full access

---

## Legacy Flow (6-Step Profile Setup)

**Note:** There's also a comprehensive 6-step profile setup system (`UserProfile` component) that includes:

1. **Personal Information**
   - Age, Location, Education, Employment

2. **Financial Information**
   - Annual Income, Monthly Take-home, Student Loans, Credit Card Debt, Current Savings

3. **Monthly Expenses**
   - Rent, Car Payment, Insurance, Groceries, Utilities, Student Loan Payment, Credit Card Minimum

4. **Important Dates**
   - Birthday, Planned Vacation, Car Inspection, Sister's Wedding

5. **Health & Wellness**
   - Physical Activity, Relationship Satisfaction, Meditation Minutes, Stress Spending

6. **Vehicle & Transportation**
   - Vehicle Expenses, Transportation Stress, Commute Satisfaction, Vehicle Decisions

7. **Goals**
   - Emergency Fund Goal, Debt Payoff Date, Monthly Savings Goal

**Current Status:** This comprehensive profile is available but not part of the default onboarding flow. Users can access it later from their profile settings.

---

## Data Flow Summary

```
Landing Page
    ↓
Assessment (Optional)
    ↓ [Saves to localStorage]
Sign Up Page
    ↓ [Pre-fills from localStorage]
Account Creation
    ↓ [Creates user, stores JWT token]
Quick Setup (3 questions)
    ↓ [Saves to database]
Career Dashboard
    ↓
Full Access to Features
```

---

## Key Differences: Old vs New Flow

### Old Flow (Before Optimization):
1. Landing Page
2. Assessment
3. Sign Up
4. **6-Step Comprehensive Profile Setup** (7 steps total)
5. Dashboard

### New Flow (Current - Optimized):
1. Landing Page
2. Assessment (Optional)
3. Sign Up (Pre-filled if from assessment)
4. **Quick Setup** (3 questions only)
5. Dashboard

**Improvements:**
- ✅ Reduced from 7 steps to 3-5 steps
- ✅ Pre-fills data from assessment
- ✅ Faster time to value (dashboard access)
- ✅ Optional comprehensive profile available later

---

## What Happens Behind the Scenes

### Assessment Completion:
- Data saved to: `localStorage.getItem('mingus_assessment')`
- Contains: `{ email, firstName, assessmentType, completedAt }`

### Registration:
- API Call: `POST /api/auth/register`
- Creates user in database
- Returns JWT token
- Token stored: `localStorage.getItem('mingus_token')`

### Quick Setup:
- API Call: `POST /api/profile/quick-setup`
- Requires: JWT authentication
- Saves to: `user_profiles` table in database
- Fields: `income_range`, `location`, `primary_goal`, `setup_completed`

### Dashboard Access:
- Protected route (requires authentication)
- Uses JWT token for API calls
- Displays personalized content based on user data

---

## Current Status Based on Your Experience

Since you mentioned you "entered your information and the page directed me to the career dashboard," it appears:

1. ✅ You completed registration
2. ✅ You were redirected to quick-setup (or skipped it)
3. ✅ You were taken to the career dashboard

**Possible scenarios:**
- You completed quick-setup → Data saved → Dashboard
- You clicked "Skip for now" → Dashboard (no data saved)
- Quick-setup had an error → Fallback to dashboard

---

## Next Steps for Users

After reaching the dashboard, users can:
- Complete the full 6-step profile later (from settings)
- Access all features based on their tier
- Update their quick-setup information
- Complete additional assessments
- Set up financial goals
- Explore job matching
- View risk analytics

---

**Last Updated:** January 2025  
**Based on:** Current codebase implementation
