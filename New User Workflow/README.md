# New User Workflow Documentation

This folder contains all markdown files related to workflows and processes required to create a new user, including the initial assessment process.

## Files Included

### 1. MINGUS_USER_JOURNEY_TEST_PLAN.md
**Purpose:** Comprehensive test plan for the complete user journey from landing page to assessment completion.

**Key Sections:**
- Phase 1: Initial Landing & First Impressions
- Phase 2: Assessment Flow Testing (AI Risk, Income Comparison, Cuffing Season, Layoff Risk)
- Phase 3: Feature Exploration
- Phase 4: Pricing & FAQ Testing
- Phase 5: Call-to-Action & Conversion Testing
- Phase 6: Performance & Technical Testing

**Use Case:** Understanding the complete user journey and testing requirements for new user onboarding.

---

### 2. ASSESSMENT_SYSTEM_TEST_REPORT.md
**Purpose:** Documentation of the assessment modal system that captures user information and provides personalized assessments.

**Key Sections:**
- Assessment Types (AI Replacement Risk, Income Comparison, Cuffing Season Score, Layoff Risk)
- Email Capture Process
- Form Submission Flow
- Result Calculation
- User Experience Flow

**Use Case:** Understanding how assessments work as part of the initial user engagement and lead capture process.

---

### 3. PHASE3_PROFILE_SYSTEM_SUMMARY.md
**Purpose:** Complete documentation of the 6-step profile setup system that new users complete after registration.

**Key Sections:**
- Step 1: Personal Information Collection
- Step 2: Financial Information Entry
- Step 3: Monthly Expenses Tracking
- Step 4: Important Dates Planning
- Step 5: Health & Wellness Check-in
- Step 6: Goals Setting

**Use Case:** Understanding the comprehensive profile setup process that follows user registration.

---

### 4. DEPLOY_REGISTRATION_CHANGES.md
**Purpose:** Technical deployment guide for the user registration and sign-up functionality.

**Key Sections:**
- Registration Endpoint Details (`/api/auth/register`)
- SignUp Page Component
- Database Migration Requirements
- Deployment Steps
- Post-Deployment Testing

**Use Case:** Understanding the technical implementation of user account creation and registration process.

---

## Complete New User Workflow

Based on these documents, the complete new user workflow consists of:

1. **Landing Page** → User arrives and sees assessment options
2. **Assessment Completion** → User completes one or more assessments (AI Risk, Income Comparison, Cuffing Season, Layoff Risk)
3. **Email Capture** → User provides email and first name during assessment
4. **Registration** → User signs up with email, password, first name, last name
5. **Account Creation** → System creates user account with default tier ('budget')
6. **Profile Setup** → User completes 6-step profile setup:
   - Personal Information
   - Financial Information
   - Monthly Expenses
   - Important Dates
   - Health & Wellness
   - Goals
7. **Dashboard Access** → User is redirected to career dashboard

---

## Optimization Opportunities

These documents can be used to identify optimization opportunities in:
- Reducing steps in the registration process
- Streamlining assessment completion
- Simplifying profile setup
- Improving conversion rates at each stage
- Reducing user drop-off points
- Enhancing user experience flow

---

**Last Updated:** January 2025
**Purpose:** Centralized documentation for optimizing the new user workflow process
