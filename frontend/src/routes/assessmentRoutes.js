import React from 'react';
import { Routes, Route } from 'react-router-dom';

// Assessment Components
import AssessmentLanding from '../components/assessments/AssessmentLanding';
import AssessmentFlow from '../components/assessments/AssessmentFlow';
import AssessmentResults from '../components/assessments/AssessmentResults';

// Error Boundary
import ErrorBoundary from '../components/shared/ErrorBoundary';

const AssessmentRoutes = () => {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Assessment Landing Page */}
        <Route 
          path="/" 
          element={<AssessmentLanding />} 
        />
        
        {/* Assessment Flow */}
        <Route 
          path="/:assessmentType" 
          element={<AssessmentFlow />} 
        />
        
        {/* Assessment Results */}
        <Route 
          path="/:assessmentType/results/:assessmentId" 
          element={<AssessmentResults />} 
        />
        
        {/* Fallback - redirect to landing */}
        <Route 
          path="*" 
          element={<AssessmentLanding />} 
        />
      </Routes>
    </ErrorBoundary>
  );
};

export default AssessmentRoutes;
