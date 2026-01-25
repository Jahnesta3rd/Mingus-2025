# Buttons Displayed After Assessment Completion

This document lists all buttons that appear after a user completes an assessment in the Mingus application.

---

## Overview

After completing an assessment, users see the **AssessmentResults** component which displays:
- Assessment score and results
- Personalized recommendations
- Multiple call-to-action (CTA) buttons
- Action buttons for sharing and retaking
- Bottom action buttons for additional features

---

## Button Categories

### 1. Primary CTA Buttons (Assessment-Specific)

These buttons vary based on the assessment type completed. Each assessment has **2 primary CTA buttons**:

#### AI Replacement Risk Assessment (`ai-risk`)
1. **"Start Learning"** (Primary - Violet gradient)
   - Title: "Get AI-Ready Skills Training"
   - Description: "Learn the skills that will keep you ahead of AI"
   - Action: Navigates to `/signup?from=assessment&type=ai-risk`
   - Icon: BookOpen
   - Style: White text on violet gradient background

2. **"Join Network"** (Secondary - Gray)
   - Title: "Join AI Professionals Network"
   - Description: "Connect with others navigating AI in their careers"
   - Action: Navigates to `/signup?from=assessment&type=ai-risk`
   - Icon: Users
   - Style: White text on gray background

#### Income Comparison Assessment (`income-comparison`)
1. **"Get Negotiation Guide"** (Primary - Violet gradient)
   - Title: "Negotiate Your Salary"
   - Description: "Get expert guidance on salary negotiation"
   - Action: Navigates to `/signup?from=assessment&type=income-comparison`
   - Icon: DollarSign
   - Style: White text on violet gradient background

2. **"Create Plan"** (Secondary - Gray)
   - Title: "Career Advancement Plan"
   - Description: "Create a roadmap to increase your earning potential"
   - Action: Navigates to `/signup?from=assessment&type=income-comparison`
   - Icon: TrendingUp
   - Style: White text on gray background

#### Cuffing Season Score (`cuffing-season`)
1. **"Join Workshop"** (Primary - Violet gradient)
   - Title: "Dating Success Workshop"
   - Description: "Learn proven strategies for meaningful connections"
   - Action: Navigates to `/signup?from=assessment&type=cuffing-season`
   - Icon: Users
   - Style: White text on violet gradient background

2. **"Start Course"** (Secondary - Gray)
   - Title: "Confidence Building Course"
   - Description: "Build the confidence to attract the right partner"
   - Action: Navigates to `/signup?from=assessment&type=cuffing-season`
   - Icon: Target
   - Style: White text on gray background

#### Layoff Risk Assessment (`layoff-risk`)
1. **"Get Action Plan"** (Primary - Violet gradient)
   - Title: "Job Security Action Plan"
   - Description: "Protect your career with strategic moves"
   - Action: Navigates to `/signup?from=assessment&type=layoff-risk`
   - Icon: Shield
   - Style: White text on violet gradient background

2. **"Start Program"** (Secondary - Gray)
   - Title: "Skills Development Program"
   - Description: "Build in-demand skills to future-proof your career"
   - Action: Navigates to `/signup?from=assessment&type=layoff-risk`
   - Icon: BookOpen
   - Style: White text on gray background

#### Vehicle Financial Health Assessment (`vehicle-financial-health`)
1. **"Get Planning Guide"** (Primary - Violet gradient)
   - Title: "Vehicle Financial Planning Guide"
   - Description: "Get expert strategies for vehicle cost management"
   - Action: Navigates to `/signup?from=assessment&type=vehicle-financial-health`
   - Icon: Car
   - Style: White text on violet gradient background

2. **"Calculate Fund"** (Secondary - Gray)
   - Title: "Vehicle Emergency Fund Calculator"
   - Description: "Calculate the right emergency fund for your vehicle"
   - Action: Navigates to `/signup?from=assessment&type=vehicle-financial-health`
   - Icon: Calculator
   - Style: White text on gray background

#### Default (Other Assessment Types)
1. **"Get Guidance"** (Primary - Violet gradient)
   - Title: "Get Personalized Guidance"
   - Description: "Receive expert advice tailored to your results"
   - Action: Navigates to `/signup?from=assessment&type={type}`
   - Icon: Target
   - Style: White text on violet gradient background

2. **"Join Community"** (Secondary - Gray)
   - Title: "Join Our Community"
   - Description: "Connect with others on similar journeys"
   - Action: Navigates to `/signup?from=assessment&type={type}`
   - Icon: Users
   - Style: White text on gray background

---

### 2. Main Action Buttons

These buttons appear below the CTA sections:

#### **"Sign Up to Access Full Features"** (Primary Action)
- **Location:** Full-width button at bottom of CTA section
- **Style:** Violet to purple gradient background, white text
- **Icon:** UserPlus
- **Action:** 
  - Closes the assessment modal
  - Navigates to `/signup?from=assessment&type={assessmentType}`
- **Hover Effect:** Scale up slightly (105%)

#### **"Retake Assessment"** (Secondary Action - Left)
- **Location:** Bottom left of action buttons section
- **Style:** Gray background, white text
- **Icon:** Target
- **Action:** 
  - Resets assessment to step 0
  - Clears all answers
  - Allows user to retake the same assessment

#### **"Share Results"** (Secondary Action - Right)
- **Location:** Bottom right of action buttons section
- **Style:** Gray background, white text
- **Icon:** Share2
- **Action:** 
  - Uses native share API if available
  - Falls back to copying to clipboard
  - Shares: "I just completed the [Assessment Title] and scored [score]/100! Check it out: [URL]"

---

### 3. Bottom Action Buttons (Footer Section)

These buttons appear in the footer section at the very bottom of the results:

#### **"Download PDF"**
- **Location:** Bottom left of footer
- **Style:** Gray text that turns white on hover
- **Icon:** Download
- **Action:** Currently displays but functionality may not be fully implemented
- **Status:** Button visible, functionality TBD

#### **"Resend Email"**
- **Location:** Center of footer
- **Style:** Gray text that turns white on hover
- **Icon:** Mail
- **Action:** Currently displays but functionality may not be fully implemented
- **Status:** Button visible, functionality TBD

#### **"Schedule Follow-up"**
- **Location:** Bottom right of footer
- **Style:** Gray text that turns white on hover
- **Icon:** Calendar
- **Action:** Currently displays but functionality may not be fully implemented
- **Status:** Button visible, functionality TBD

---

### 4. Close Button

#### **Close (X) Button**
- **Location:** Top right corner of the results modal
- **Style:** Violet-200 text that turns white on hover
- **Icon:** X (close icon)
- **Action:** Closes the assessment results modal
- **Accessibility:** Has `aria-label="Close results"`

---

## Complete Button List Summary

### By Section:

1. **Header Section:**
   - Close (X) button

2. **CTA Section (Assessment-Specific):**
   - Primary CTA button (varies by assessment type)
   - Secondary CTA button (varies by assessment type)

3. **Main Action Buttons:**
   - "Sign Up to Access Full Features" (full-width, primary)
   - "Retake Assessment" (left, secondary)
   - "Share Results" (right, secondary)

4. **Footer Section:**
   - "Download PDF"
   - "Resend Email"
   - "Schedule Follow-up"

---

## Navigation Behavior

### All CTA Buttons Navigate to Signup:
- **Primary CTA buttons:** Navigate to `/signup?from=assessment&type={type}`
- **Secondary CTA buttons:** Navigate to `/signup?from=assessment&type={type}`
- **"Sign Up to Access Full Features" button:** Navigates to `/signup?from=assessment&type={type}`

### All Navigation Actions:
1. Close the modal first (`onClose()`)
2. Wait 100ms (`setTimeout`)
3. Navigate to signup page with assessment context

This ensures:
- Modal closes smoothly before navigation
- Assessment data is preserved in localStorage
- Signup page can pre-fill email and first name
- User sees personalized welcome message

---

## Button Styling Details

### Primary CTA Buttons:
- **Background:** Gradient from `violet-600` to `purple-600`
- **Text:** White
- **Hover:** Background changes to `violet-700` to `purple-700`
- **Icon:** Colored icon on left side
- **Layout:** Full-width within card, with icon and text

### Secondary CTA Buttons:
- **Background:** `gray-800` with `gray-700` border
- **Text:** White
- **Hover:** Background changes to `gray-600`
- **Icon:** Gray icon on left side
- **Layout:** Full-width within card, with icon and text

### Main "Sign Up" Button:
- **Background:** Gradient from `violet-600` to `purple-600`
- **Text:** White
- **Hover:** 
  - Background: `violet-700` to `purple-700`
  - Scale: 105% (slight zoom effect)
- **Icon:** UserPlus icon
- **Layout:** Full-width, centered

### Secondary Action Buttons (Retake/Share):
- **Background:** `gray-700`
- **Text:** White
- **Hover:** Background changes to `gray-600`
- **Icons:** Target (Retake), Share2 (Share)
- **Layout:** Side-by-side, equal width

### Footer Action Buttons:
- **Text:** `gray-400` (default), `white` (on hover)
- **Icons:** Download, Mail, Calendar
- **Layout:** Horizontal row with spacing
- **No background:** Text-only buttons

---

## Component Location

**File:** `frontend/src/components/AssessmentResults.tsx`

**Key Functions:**
- `CTASection`: Renders the primary and secondary CTA buttons
- `AssessmentResults`: Main component that renders all buttons
- Button actions are passed as props: `onSignUp`, `onRetake`, `onShare`, `onClose`

---

## User Flow After Button Click

### Sign Up Flow (All CTA buttons + "Sign Up to Access Full Features"):
1. User clicks any signup-related button
2. Modal closes (`onClose()`)
3. 100ms delay
4. Navigate to `/signup?from=assessment&type={type}`
5. Signup page loads with:
   - Pre-filled email (from assessment)
   - Pre-filled first name (from assessment)
   - Welcome message: "Complete your registration to see your full [Assessment Type] results!"
6. User completes registration
7. Redirects to Quick Setup
8. Then to Career Dashboard

### Retake Flow:
1. User clicks "Retake Assessment"
2. Assessment resets to step 0
3. All answers cleared
4. User can start assessment over

### Share Flow:
1. User clicks "Share Results"
2. If native share API available:
   - Opens device share dialog
   - User can share via email, social media, etc.
3. If native share not available:
   - Copies text to clipboard
   - Text: "I just completed the [Title] and scored [score]/100! Check it out: [URL]"

---

## Summary

**Total Buttons Displayed:** 8-9 buttons (depending on assessment type)

1. Close button (X) - Header
2. Primary CTA button (assessment-specific) - CTA Section
3. Secondary CTA button (assessment-specific) - CTA Section
4. "Sign Up to Access Full Features" - Main Action
5. "Retake Assessment" - Main Action
6. "Share Results" - Main Action
7. "Download PDF" - Footer
8. "Resend Email" - Footer
9. "Schedule Follow-up" - Footer

**All signup-related buttons (1-4) navigate to the same signup page** with assessment context preserved.

---

**Last Updated:** January 2025  
**Based on:** `frontend/src/components/AssessmentResults.tsx`
