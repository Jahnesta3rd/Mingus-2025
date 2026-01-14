# Mingus Landing Page & Registration Code Changes

## Overview

This document contains specific code changes to implement the optimization recommendations for the new user registration process.

---

## 1. Pass Assessment Data to Registration

### File: `frontend/src/components/LandingPage.tsx`

**Location:** Inside `handleAssessmentSubmit` function, after line ~357 (after successful submission)

**Add this code:**

```typescript
// After: logger.log('Assessment submitted successfully:', {...});
// Add: Store assessment data for registration pre-fill
try {
  localStorage.setItem('mingus_assessment', JSON.stringify({
    email: sanitizedData.email,
    firstName: sanitizedData.firstName,
    assessmentType: sanitizedData.assessmentType,
    completedAt: new Date().toISOString()
  }));
} catch (e) {
  // localStorage might be unavailable in some contexts
  console.warn('Could not save assessment data to localStorage');
}

// Navigate to signup instead of just closing modal
setTimeout(() => {
  setActiveAssessment(null);
  navigate('/signup?from=assessment');
}, 1500);
```

---

## 2. Pre-fill Registration Form

### File: `frontend/src/pages/SignUpPage.tsx`

**Add this useEffect hook near the top of the component:**

```typescript
import { useSearchParams } from 'react-router-dom';

// Inside the component:
const [searchParams] = useSearchParams();

useEffect(() => {
  // Check if user came from assessment
  const fromAssessment = searchParams.get('from') === 'assessment';
  
  const savedData = localStorage.getItem('mingus_assessment');
  if (savedData) {
    try {
      const { email, firstName, assessmentType } = JSON.parse(savedData);
      setFormData(prev => ({
        ...prev,
        email: email || prev.email,
        firstName: firstName || prev.firstName
      }));
      
      // Show a personalized message if from assessment
      if (fromAssessment && assessmentType) {
        setWelcomeMessage(`Complete your registration to see your full ${formatAssessmentType(assessmentType)} results!`);
      }
    } catch (e) {
      console.warn('Could not parse assessment data');
    }
  }
}, [searchParams]);

// Helper function
const formatAssessmentType = (type: string): string => {
  const names: Record<string, string> = {
    'ai-risk': 'AI Replacement Risk',
    'income-comparison': 'Income Comparison',
    'cuffing-season': 'Cuffing Season Score',
    'layoff-risk': 'Layoff Risk'
  };
  return names[type] || 'Assessment';
};
```

---

## 3. Simplified Quick Setup Profile Component

### Create New File: `frontend/src/components/QuickSetup.tsx`

```tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, MapPin, Target, ArrowRight } from 'lucide-react';

interface QuickSetupData {
  incomeRange: string;
  location: string;
  primaryGoal: string;
}

const QuickSetup: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<QuickSetupData>({
    incomeRange: '',
    location: '',
    primaryGoal: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const incomeRanges = [
    { value: '30-50k', label: '$30,000 - $50,000' },
    { value: '50-75k', label: '$50,000 - $75,000' },
    { value: '75-100k', label: '$75,000 - $100,000' },
    { value: '100k+', label: '$100,000+' }
  ];

  const financialGoals = [
    { value: 'emergency-fund', label: 'Build Emergency Fund' },
    { value: 'debt-payoff', label: 'Pay Off Debt' },
    { value: 'investing', label: 'Start Investing' },
    { value: 'home-purchase', label: 'Save for Home' },
    { value: 'retirement', label: 'Plan for Retirement' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/profile/quick-setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Setup error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isValid = formData.incomeRange && formData.location && formData.primaryGoal;

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Let's personalize your experience
          </h1>
          <p className="text-gray-400">
            Just 3 quick questions to get you started
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Income Range */}
          <div>
            <label className="flex items-center gap-2 text-white font-medium mb-3">
              <DollarSign className="h-5 w-5 text-violet-400" />
              What's your annual income range?
            </label>
            <div className="grid grid-cols-2 gap-3">
              {incomeRanges.map(range => (
                <button
                  key={range.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, incomeRange: range.value }))}
                  className={`p-3 rounded-lg border text-sm transition-all ${
                    formData.incomeRange === range.value
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-violet-500'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Location */}
          <div>
            <label className="flex items-center gap-2 text-white font-medium mb-3">
              <MapPin className="h-5 w-5 text-violet-400" />
              Where are you located?
            </label>
            <input
              type="text"
              placeholder="City, State or ZIP code"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-violet-500 focus:outline-none"
            />
          </div>
          
          {/* Primary Goal */}
          <div>
            <label className="flex items-center gap-2 text-white font-medium mb-3">
              <Target className="h-5 w-5 text-violet-400" />
              What's your top financial priority?
            </label>
            <div className="space-y-2">
              {financialGoals.map(goal => (
                <button
                  key={goal.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, primaryGoal: goal.value }))}
                  className={`w-full p-3 rounded-lg border text-left transition-all ${
                    formData.primaryGoal === goal.value
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-violet-500'
                  }`}
                >
                  {goal.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Submit */}
          <button
            type="submit"
            disabled={!isValid || isSubmitting}
            className={`w-full py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
              isValid && !isSubmitting
                ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? 'Setting up...' : (
              <>
                Go to Dashboard
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>
          
          {/* Skip Option */}
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="w-full py-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            Skip for now
          </button>
        </form>
      </div>
    </div>
  );
};

export default QuickSetup;
```

---

## 4. Update App Router

### File: `frontend/src/App.tsx`

**Replace the UserProfile route with QuickSetup:**

```tsx
// Import
import QuickSetup from './components/QuickSetup';

// In routes, replace:
// <Route path="/profile-setup" element={<UserProfile />} />
// With:
<Route path="/quick-setup" element={<QuickSetup />} />
```

**Update the redirect after registration in SignUpPage.tsx:**

```tsx
// Change:
navigate('/profile-setup');
// To:
navigate('/quick-setup');
```

---

## 5. Backend Quick Setup Endpoint

### Create New File: `backend/api/quick_setup_endpoints.py`

```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import sqlite3
from datetime import datetime

quick_setup_api = Blueprint('quick_setup_api', __name__)

@quick_setup_api.route('/api/profile/quick-setup', methods=['POST'])
@login_required
def quick_setup():
    """Handle quick profile setup with minimal required fields"""
    try:
        data = request.get_json()
        
        income_range = data.get('incomeRange', '')
        location = data.get('location', '')
        primary_goal = data.get('primaryGoal', '')
        
        # Validate required fields
        if not all([income_range, location, primary_goal]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Save to database
        conn = sqlite3.connect('user_profiles.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (user_id, email, income_range, location, primary_goal, setup_completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id,
            current_user.email,
            income_range,
            location,
            primary_goal,
            True,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile setup completed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Summary of Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `LandingPage.tsx` | Modify | Add localStorage save after assessment |
| `SignUpPage.tsx` | Modify | Add useEffect to pre-fill from assessment |
| `QuickSetup.tsx` | **New** | Simplified 1-screen profile setup |
| `App.tsx` | Modify | Update routes for QuickSetup |
| `quick_setup_endpoints.py` | **New** | Backend endpoint for quick setup |

---

## Testing Checklist

After implementing these changes, verify:

- [ ] Assessment completion saves data to localStorage
- [ ] SignUp page pre-fills email and firstName from assessment
- [ ] Navigation from assessment to signup works
- [ ] QuickSetup component accepts input and submits
- [ ] User can skip QuickSetup and go directly to dashboard
- [ ] All existing functionality still works

---

*Document prepared: January 2025*
*For: Mingus Personal Finance Application*
