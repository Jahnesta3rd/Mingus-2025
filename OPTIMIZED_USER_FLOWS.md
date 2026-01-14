# Optimized User Flows for Mingus

## Flow 1: Assessment Completion Path

**User Journey:** Landing Page → Assessment → Sign Up → Quick Setup → Dashboard

### Step-by-Step Flow:

1. **Landing Page** (`/`)
   - User sees 4 assessment options
   - Clicks one (e.g., "Determine Your Replacement Risk Due To AI")

2. **Assessment Modal**
   - User enters email and first name
   - Completes 7-8 questions
   - Submits assessment
   - **Data Saved:** `localStorage.setItem('mingus_assessment', {...})`
   - **Navigation:** Auto-redirects to `/signup?from=assessment&type=ai-risk` after 1.5s

3. **Sign Up Page** (`/signup?from=assessment&type=ai-risk`)
   - **Pre-filled:** Email and First Name from assessment
   - **Welcome Message:** "Complete your registration to see your full AI Replacement Risk results!"
   - User enters password and confirms
   - **Navigation:** Redirects to `/quick-setup?from=assessment` after registration

4. **Quick Setup** (`/quick-setup?from=assessment`)
   - **Enhanced Message:** "Let's personalize your experience based on your assessment"
   - Shows assessment type badge
   - 3 quick questions (same as before)
   - **Navigation:** Redirects to `/career-dashboard` after completion

5. **Career Dashboard** (`/career-dashboard`)
   - Full access with personalized content
   - Assessment results available
   - Onboarding complete

---

## Flow 2: "Get Started" Button Path

**User Journey:** Landing Page → Sign Up → Quick Setup → Dashboard

### Step-by-Step Flow:

1. **Landing Page** (`/`)
   - User clicks "Get Started" button (from hero, CTA, pricing, or nav)
   - **Navigation:** Goes directly to `/signup?source=cta`

2. **Sign Up Page** (`/signup?source=cta`)
   - **No pre-filled data**
   - **Welcome Message:** "Welcome to Mingus! Let's get you started on your financial wellness journey."
   - Standard registration form
   - User enters: email, password, first name, last name (optional)
   - **Navigation:** Redirects to `/quick-setup?source=cta` after registration

3. **Quick Setup** (`/quick-setup?source=cta`)
   - **Standard Message:** "Let's personalize your experience"
   - No assessment badge
   - 3 quick questions
   - **Navigation:** Redirects to `/career-dashboard` after completion

4. **Career Dashboard** (`/career-dashboard`)
   - Full access
   - Standard onboarding
   - Can complete assessments later

---

## Key Differences Between Flows

| Feature | Assessment Path | Get Started Path |
|---------|----------------|------------------|
| **Entry Point** | Assessment modal | "Get Started" button |
| **Signup Pre-fill** | ✅ Email & First Name | ❌ None |
| **Welcome Message** | Assessment-specific | Generic welcome |
| **Query Params** | `?from=assessment&type=X` | `?source=cta` |
| **Quick Setup Message** | Assessment-enhanced | Standard |
| **Assessment Badge** | ✅ Shows in quick-setup | ❌ None |
| **Time to Value** | Faster (pre-filled) | Standard |

---

## Implementation Plan

### Changes Needed:

1. **LandingPage.tsx**
   - Update assessment redirect to include assessment type: `/signup?from=assessment&type=${assessmentType}`
   - Ensure "Get Started" buttons use: `/signup?source=cta`

2. **SignUpPage.tsx**
   - Detect `source=cta` vs `from=assessment`
   - Show different welcome messages
   - Pre-fill only if `from=assessment`

3. **QuickSetup.tsx**
   - Detect query params
   - Show assessment badge if `from=assessment`
   - Adjust messaging based on entry point

4. **Analytics Tracking**
   - Track conversion paths separately
   - Measure which flow converts better

---

## Benefits of This Approach

✅ **Personalized Experience:** Assessment users get tailored messaging  
✅ **Clear Differentiation:** Two distinct paths with appropriate messaging  
✅ **Better Analytics:** Can track conversion rates for each path  
✅ **Flexible:** Easy to A/B test different messages  
✅ **User-Friendly:** Reduces friction for both entry points
