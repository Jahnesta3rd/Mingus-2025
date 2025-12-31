# Landing Page Troubleshooting Guide

**Date:** January 2025  
**Component:** `frontend/src/components/LandingPage.tsx`

## 🔧 Step-by-Step Fix Instructions

### Issue 1: Remove ResponsiveTestComponent from Production

**Problem:** Development component included in production build

**Steps:**
1. Open `frontend/src/components/LandingPage.tsx`
2. Find line 335: `<ResponsiveTestComponent />`
3. Replace with:
   ```tsx
   {process.env.NODE_ENV === 'development' && <ResponsiveTestComponent />}
   ```
4. Save file
5. Test: Run `npm run build` and verify component is not in production bundle

**Verification:**
```bash
# Check production build
npm run build
grep -r "ResponsiveTestComponent" dist/
# Should return no results
```

---

### Issue 2: Remove Console Statements

**Problem:** Console.log/error statements in production code

**Steps:**
1. Open `frontend/src/components/LandingPage.tsx`
2. Create utility file `frontend/src/utils/logger.ts`:
   ```tsx
   export const logger = {
     log: (...args: any[]) => {
       if (process.env.NODE_ENV === 'development') {
         console.log(...args);
       }
     },
     error: (...args: any[]) => {
       console.error(...args); // Always log errors
       // In production, send to error tracking service
       if (process.env.NODE_ENV === 'production') {
         // Send to Sentry, LogRocket, etc.
       }
     },
     warn: (...args: any[]) => {
       if (process.env.NODE_ENV === 'development') {
         console.warn(...args);
       }
     }
   };
   ```
3. Import logger: `import { logger } from '../utils/logger';`
4. Replace all console statements:
   - Line 236: `logger.log(\`Button clicked: ${action}\`)`
   - Line 257: `logger.error('Email validation failed:', emailValidation.errors)`
   - Line 292: `logger.log('Assessment submitted successfully:', {...})`
   - Line 303: `logger.error('Error submitting assessment:', error)`
   - Line 307: `logger.error('Full error details:', error)`
5. Save and test

**Verification:**
```bash
# Build production and check for console statements
npm run build
# Open browser console in production build
# Should see no console.log statements
```

---

### Issue 3: Replace window.location with React Router

**Problem:** Using window.location causes full page reloads

**Steps:**
1. Open `frontend/src/components/LandingPage.tsx`
2. Add import at top: `import { useNavigate } from 'react-router-dom';`
3. Add hook in component:
   ```tsx
   const LandingPage: React.FC = () => {
     const navigate = useNavigate();
     // ... rest of component
   ```
4. Find line 574:
   ```tsx
   // Before:
   onClick={() => window.location.href = '/career-dashboard'}
   
   // After:
   onClick={() => navigate('/career-dashboard')}
   ```
5. Find line 766 and make same change
6. Save and test navigation

**Verification:**
- Click "View Dashboard" buttons
- Verify no full page reload occurs
- Check browser Network tab - should see no full page requests

---

### Issue 4: Add Error Handling with User Feedback

**Problem:** API errors not shown to users

**Steps:**
1. Add error state:
   ```tsx
   const [error, setError] = useState<string | null>(null);
   const [success, setSuccess] = useState<string | null>(null);
   ```
2. Update `handleAssessmentSubmit`:
   ```tsx
   const handleAssessmentSubmit = async (data: AssessmentData) => {
     setError(null);
     setSuccess(null);
     setIsSubmitting(true);
     
     try {
       // ... existing validation code ...
       
       const response = await fetch('/api/assessments', {
         // ... existing fetch code ...
       });

       if (!response.ok) {
         const errorData = await response.json().catch(() => ({}));
         throw new Error(errorData.message || `HTTP ${response.status}: Failed to submit assessment`);
       }

       setSuccess('Assessment submitted successfully!');
       setActiveAssessment(null);
       
       // Clear success message after 5 seconds
       setTimeout(() => setSuccess(null), 5000);
       
     } catch (error) {
       setError(error instanceof Error ? error.message : 'Failed to submit assessment. Please try again.');
       logger.error('Error submitting assessment:', error);
     } finally {
       setIsSubmitting(false);
     }
   };
   ```
3. Add error/success display in JSX (before closing main tag):
   ```tsx
   {/* Error/Success Messages */}
   {error && (
     <div className="fixed top-4 right-4 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md">
       <div className="flex items-center justify-between">
         <span>{error}</span>
         <button 
           onClick={() => setError(null)}
           className="ml-4 text-white hover:text-gray-200"
           aria-label="Close error message"
         >
           ×
         </button>
       </div>
     </div>
   )}
   
   {success && (
     <div className="fixed top-4 right-4 bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md">
       <div className="flex items-center justify-between">
         <span>{success}</span>
         <button 
           onClick={() => setSuccess(null)}
           className="ml-4 text-white hover:text-gray-200"
           aria-label="Close success message"
         >
           ×
         </button>
       </div>
     </div>
   )}
   ```
4. Save and test error scenarios

**Verification:**
- Test with network offline
- Test with invalid email
- Verify error message appears
- Verify success message appears on success

---

### Issue 5: Add Loading State for Assessment Submission

**Problem:** No loading indicator during submission

**Steps:**
1. Add loading state:
   ```tsx
   const [isSubmitting, setIsSubmitting] = useState(false);
   ```
2. Update `handleAssessmentSubmit`:
   ```tsx
   const handleAssessmentSubmit = async (data: AssessmentData) => {
     setIsSubmitting(true);
     // ... existing code ...
     finally {
       setIsSubmitting(false);
     }
   };
   ```
3. Pass to AssessmentModal:
   ```tsx
   <AssessmentModal
     isOpen={activeAssessment !== null}
     assessmentType={activeAssessment}
     onClose={handleAssessmentClose}
     onSubmit={handleAssessmentSubmit}
     isSubmitting={isSubmitting}
   />
   ```
4. Update AssessmentModal component to show loading state (if not already)
5. Disable form inputs during submission

**Verification:**
- Submit assessment form
- Verify loading spinner appears
- Verify form is disabled during submission
- Verify loading disappears after completion

---

### Issue 6: Fix Memory Leak in useEffect

**Problem:** Potential memory leak from test function

**Steps:**
1. Check `runComprehensiveTest()` implementation
2. If it creates timers/listeners, ensure cleanup
3. Update useEffect:
   ```tsx
   useEffect(() => {
     if (process.env.NODE_ENV === 'development') {
       const timer = setTimeout(() => {
         runComprehensiveTest();
       }, 2000);
       
       return () => {
         clearTimeout(timer);
         // Add any cleanup from runComprehensiveTest if needed
       };
     }
   }, []);
   ```
4. Test component mount/unmount

**Verification:**
- Use React DevTools Profiler
- Mount and unmount component multiple times
- Check for memory leaks
- Verify no console warnings

---

### Issue 7: Add Error Boundary for Modal

**Problem:** Modal errors can crash entire page

**Steps:**
1. Create modal error fallback component:
   ```tsx
   // frontend/src/components/ModalErrorFallback.tsx
   const ModalErrorFallback = () => (
     <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
       <div className="bg-white rounded-lg p-6 max-w-md">
         <h2 className="text-xl font-bold mb-4">Something went wrong</h2>
         <p className="mb-4">The assessment modal encountered an error.</p>
         <button 
           onClick={() => window.location.reload()}
           className="bg-violet-600 text-white px-4 py-2 rounded"
         >
           Reload Page
         </button>
       </div>
     </div>
   );
   ```
2. Wrap AssessmentModal:
   ```tsx
   <ErrorBoundary fallback={<ModalErrorFallback />}>
     <AssessmentModal
       isOpen={activeAssessment !== null}
       assessmentType={activeAssessment}
       onClose={handleAssessmentClose}
       onSubmit={handleAssessmentSubmit}
     />
   </ErrorBoundary>
   ```

**Verification:**
- Intentionally break AssessmentModal
- Verify error boundary catches error
- Verify fallback UI displays

---

### Issue 8: Improve Accessibility

**Problem:** Missing ARIA labels on some elements

**Steps:**
1. Audit all buttons for ARIA labels
2. Add missing labels:
   ```tsx
   // Example for pricing tier buttons
   <button
     aria-label={`Subscribe to ${tier.name} plan for ${tier.price} per month`}
     aria-describedby={`${tier.name}-description`}
   >
   ```
3. Add descriptions:
   ```tsx
   <div id={`${tier.name}-description`} className="sr-only">
     {tier.description}. Features include: {tier.features.join(', ')}
   </div>
   ```
4. Test with screen reader

**Verification:**
- Run Lighthouse accessibility audit
- Test with NVDA/JAWS/VoiceOver
- Verify all interactive elements are accessible
- Check for ARIA label warnings

---

### Issue 9: Split Large Component

**Problem:** Component is too large (1054 lines)

**Steps:**
1. Create component files:
   - `HeroSection.tsx`
   - `AssessmentSection.tsx`
   - `FeaturesSection.tsx`
   - `PricingSection.tsx`
   - `FAQSection.tsx`
   - `CTASection.tsx`
2. Extract each section to its own component
3. Update LandingPage to import and use components:
   ```tsx
   import HeroSection from './sections/HeroSection';
   import AssessmentSection from './sections/AssessmentSection';
   // ... etc
   
   return (
     <ErrorBoundary>
       <div className="min-h-screen bg-gray-900 text-white">
         <NavigationBar />
         <main>
           <HeroSection 
             onAssessmentClick={handleAssessmentClick}
             isLoading={isLoading}
           />
           <AssessmentSection 
             onAssessmentClick={handleAssessmentClick}
             isLoading={isLoading}
           />
           {/* ... other sections ... */}
         </main>
       </div>
     </ErrorBoundary>
   );
   ```

**Verification:**
- Verify page renders correctly
- Test all functionality still works
- Check bundle size reduction
- Verify no performance regression

---

### Issue 10: Extract Assessment Type

**Problem:** Assessment type union repeated

**Steps:**
1. Create `frontend/src/types/assessments.ts`:
   ```tsx
   export type AssessmentType = 
     | 'ai-risk' 
     | 'income-comparison' 
     | 'cuffing-season' 
     | 'layoff-risk' 
     | 'vehicle-financial-health';
   ```
2. Import in LandingPage:
   ```tsx
   import { AssessmentType } from '../types/assessments';
   ```
3. Replace all occurrences:
   ```tsx
   const [activeAssessment, setActiveAssessment] = useState<AssessmentType | null>(null);
   
   const handleAssessmentClick = (assessmentType: AssessmentType) => {
     // ...
   };
   ```

**Verification:**
- TypeScript should compile without errors
- All type references should work
- No type mismatches

---

### Issue 11: Dynamic Copyright Year

**Problem:** Hardcoded copyright year

**Steps:**
1. Find line 1036
2. Replace:
   ```tsx
   // Before:
   © 2024 Mingus. All rights reserved.
   
   // After:
   © {new Date().getFullYear()} Mingus. All rights reserved.
   ```

**Verification:**
- Check footer displays current year
- Test in different years (if possible)

---

### Issue 12: Add Analytics Tracking

**Problem:** No user interaction tracking

**Steps:**
1. Install analytics library (e.g., `react-ga4` or `@analytics/google-analytics`)
2. Create analytics utility:
   ```tsx
   // frontend/src/utils/analytics.ts
   export const trackEvent = (eventName: string, properties?: Record<string, any>) => {
     if (typeof window !== 'undefined' && window.gtag) {
       window.gtag('event', eventName, properties);
     }
   };
   ```
3. Add tracking to key events:
   ```tsx
   const handleButtonClick = (action: string) => {
     trackEvent('button_click', { button_name: action, page: 'landing' });
     // ... existing code ...
   };
   
   const handleAssessmentClick = (assessmentType: AssessmentType) => {
     trackEvent('assessment_started', { assessment_type: aassessmentType });
     // ... existing code ...
   };
   ```

**Verification:**
- Check analytics dashboard for events
- Verify events fire correctly
- Test in production environment

---

## 🧪 Testing After Fixes

### Manual Testing Checklist
- [ ] Page loads without errors
- [ ] All buttons work correctly
- [ ] Navigation works (no page reloads)
- [ ] Assessment modal opens/closes
- [ ] Form submission works
- [ ] Error messages display
- [ ] Success messages display
- [ ] Loading states work
- [ ] No console errors
- [ ] No console.log in production

### Automated Testing
```bash
# Run linter
npm run lint

# Run type check
npm run type-check

# Run tests
npm run test

# Build production
npm run build

# Test production build
npm run preview
```

### Performance Testing
```bash
# Run Lighthouse
npx lighthouse http://localhost:5173 --view

# Check bundle size
npm run build
ls -lh dist/assets/
```

---

## 📊 Verification Checklist

After applying all fixes:

- [ ] No console statements in production build
- [ ] ResponsiveTestComponent not in production
- [ ] All navigation uses React Router
- [ ] Error handling with user feedback works
- [ ] Loading states for all async operations
- [ ] No memory leaks detected
- [ ] Error boundaries catch errors
- [ ] Accessibility audit passes (>90)
- [ ] Performance score > 90 (Lighthouse)
- [ ] TypeScript compiles without errors
- [ ] ESLint passes
- [ ] All tests pass
- [ ] Production build successful

---

## 🚨 Common Issues & Solutions

### Issue: TypeScript errors after changes
**Solution:** Run `npm run type-check` and fix type errors

### Issue: Build fails
**Solution:** Check for syntax errors, missing imports, or type mismatches

### Issue: Navigation doesn't work
**Solution:** Ensure Router is set up correctly in App.tsx

### Issue: Error messages don't appear
**Solution:** Check z-index, positioning, and state management

### Issue: Analytics not tracking
**Solution:** Verify analytics script is loaded, check browser console for errors

---

**Last Updated:** January 2025  
**Status:** Ready for Implementation

