# New User Workflow Testing Guide

## Test Plan for Landing Page Code Changes

This document outlines the testing steps for the new user workflow optimization changes.

---

## Prerequisites

1. **Backend Server Running**
   ```bash
   cd backend
   python app.py
   # Or use your preferred method
   ```

2. **Frontend Server Running**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Clear Browser Storage**
   - Open browser DevTools (F12)
   - Go to Application/Storage tab
   - Clear Local Storage
   - Clear Session Storage
   - Clear Cookies

---

## Test 1: Assessment → Signup Flow

### Steps:
1. Navigate to `http://localhost:3000` (or your frontend URL)
2. Click on any assessment button (e.g., "Determine Your Replacement Risk Due To AI")
3. Fill out the assessment form:
   - Email: `test@example.com`
   - First Name: `Test`
   - Complete all required questions
4. Submit the assessment

### Expected Results:
- ✅ Assessment submits successfully
- ✅ Success message appears
- ✅ After 1.5 seconds, modal closes and navigates to `/signup?from=assessment`
- ✅ Check localStorage: Should contain `mingus_assessment` key with JSON data

### Verification:
```javascript
// In browser console:
JSON.parse(localStorage.getItem('mingus_assessment'))
// Should return: { email: "test@example.com", firstName: "Test", assessmentType: "ai-risk", completedAt: "..." }
```

---

## Test 2: Signup Pre-fill

### Steps:
1. After completing Test 1, you should be on `/signup?from=assessment`
2. Check the signup form

### Expected Results:
- ✅ Email field is pre-filled with `test@example.com`
- ✅ First Name field is pre-filled with `Test`
- ✅ Welcome message appears: "Complete your registration to see your full AI Replacement Risk results!"
- ✅ Password and Confirm Password fields are empty

### Verification:
- Form fields should be populated automatically
- Welcome message should be visible above the form

---

## Test 3: Registration → Quick Setup

### Steps:
1. On the signup page (from Test 2)
2. Fill in password fields:
   - Password: `testpassword123`
   - Confirm Password: `testpassword123`
3. Click "Create Account"

### Expected Results:
- ✅ Account is created successfully
- ✅ Success message appears
- ✅ After 1.5 seconds, navigates to `/quick-setup`
- ✅ User is authenticated (check localStorage for `mingus_token`)

### Verification:
```javascript
// In browser console:
localStorage.getItem('mingus_token')
// Should return a JWT token string
```

---

## Test 4: Quick Setup Component

### Steps:
1. After registration, you should be on `/quick-setup`
2. Fill out the quick setup form:
   - Income Range: Select any option (e.g., "$50,000 - $75,000")
   - Location: Enter `Atlanta, GA`
   - Primary Goal: Select any option (e.g., "Build Emergency Fund")
3. Click "Go to Dashboard"

### Expected Results:
- ✅ Form validates all fields are filled
- ✅ Submit button is enabled when all fields are filled
- ✅ Loading state shows "Setting up..." during submission
- ✅ After successful submission, navigates to `/career-dashboard`
- ✅ Assessment data is cleared from localStorage

### Verification:
```javascript
// In browser console (after submission):
localStorage.getItem('mingus_assessment')
// Should return null (cleared after successful setup)
```

---

## Test 5: Quick Setup Skip Option

### Steps:
1. Navigate to `/quick-setup` (or complete registration again)
2. Click "Skip for now" button

### Expected Results:
- ✅ Immediately navigates to `/career-dashboard`
- ✅ No API call is made
- ✅ User can access dashboard without completing setup

---

## Test 6: Direct Signup (No Assessment)

### Steps:
1. Clear localStorage
2. Navigate directly to `/signup` (not from assessment)
3. Fill out the form manually:
   - Email: `direct@example.com`
   - First Name: `Direct`
   - Password: `testpassword123`
   - Confirm Password: `testpassword123`
4. Submit

### Expected Results:
- ✅ No pre-filled data
- ✅ No welcome message
- ✅ Registration works normally
- ✅ Redirects to `/quick-setup` after registration

---

## Test 7: Backend API Endpoint

### Steps:
1. Get authentication token (from Test 3)
2. Make API call to quick-setup endpoint:

```bash
curl -X POST http://localhost:5000/api/profile/quick-setup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "incomeRange": "50-75k",
    "location": "Atlanta, GA",
    "primaryGoal": "emergency-fund"
  }'
```

### Expected Results:
- ✅ Returns 200 status with `{ "success": true, "message": "Profile setup completed" }`
- ✅ Data is saved to `user_profiles.db` database
- ✅ Check database: `user_profiles` table should have new entry

### Verification:
```python
# In Python shell or script:
import sqlite3
conn = sqlite3.connect('user_profiles.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM user_profiles ORDER BY created_at DESC LIMIT 1')
print(cursor.fetchone())
```

---

## Test 8: Authentication Required

### Steps:
1. Clear authentication token from localStorage
2. Try to access `/quick-setup` directly

### Expected Results:
- ✅ Redirects to `/login` (ProtectedRoute should handle this)
- ✅ Cannot access quick-setup without authentication

---

## Test 9: Error Handling

### Test 9a: Invalid Token
1. Set invalid token in localStorage: `localStorage.setItem('mingus_token', 'invalid-token')`
2. Try to submit quick-setup form

### Expected Results:
- ✅ Returns 401 error
- ✅ Error message displayed: "Authentication required"

### Test 9b: Missing Fields
1. Fill out quick-setup form but leave one field empty
2. Try to submit

### Expected Results:
- ✅ Submit button is disabled
- ✅ Cannot submit until all fields are filled

### Test 9c: Network Error
1. Stop backend server
2. Try to submit quick-setup form

### Expected Results:
- ✅ Error message displayed
- ✅ Form remains accessible for retry

---

## Test 10: Database Verification

### Steps:
1. Complete full flow: Assessment → Signup → Quick Setup
2. Check database

### Expected Results:
- ✅ `user_profiles` table exists
- ✅ New row created with:
  - `user_id`: Matches registered user
  - `email`: Matches registered email
  - `income_range`: Selected value
  - `location`: Entered location
  - `primary_goal`: Selected goal
  - `setup_completed`: 1 (true)

---

## Browser Console Checks

Run these checks in browser console during testing:

```javascript
// Check assessment data storage
localStorage.getItem('mingus_assessment')

// Check authentication token
localStorage.getItem('mingus_token')

// Check if user is authenticated (from useAuth hook)
// This requires accessing React DevTools or checking network requests
```

---

## Network Tab Verification

Monitor these API calls in browser DevTools Network tab:

1. **Assessment Submission**
   - `POST /api/assessments`
   - Status: 200
   - Response: Success message

2. **Registration**
   - `POST /api/auth/register`
   - Status: 201
   - Response: `{ success: true, token: "...", user_id: "..." }`

3. **Quick Setup**
   - `POST /api/profile/quick-setup`
   - Headers: `Authorization: Bearer <token>`
   - Status: 200
   - Response: `{ success: true, message: "Profile setup completed" }`

---

## Common Issues & Solutions

### Issue: localStorage not saving
**Solution:** Check browser settings, ensure localStorage is enabled. Some browsers block localStorage in private/incognito mode.

### Issue: Token not found
**Solution:** Verify token is stored as `mingus_token` (not `token`). Check useAuth hook implementation.

### Issue: CORS errors
**Solution:** Ensure backend CORS is configured to allow frontend origin.

### Issue: 401 Unauthorized
**Solution:** Verify JWT_SECRET_KEY matches between frontend token generation and backend verification.

### Issue: Database not found
**Solution:** Ensure `user_profiles.db` is created in the correct location (backend directory).

---

## Success Criteria

All tests should pass with:
- ✅ No console errors
- ✅ No network errors (except intentional tests)
- ✅ Smooth user flow from assessment to dashboard
- ✅ Data persists correctly in database
- ✅ Authentication works properly
- ✅ Error handling works as expected

---

**Test Date:** [Current Date]
**Tester:** [Your Name]
**Environment:** Development (localhost)
