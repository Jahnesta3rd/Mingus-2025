import React from 'react';
import AdvancedLeadCapture from '../src/components/leadCapture/AdvancedLeadCapture';
import { PersonalizedReport } from '../src/types/leadCapture';

const LeadCaptureDemo: React.FC = () => {
  const handleComplete = (report: PersonalizedReport) => {
    console.log('Lead capture completed:', report);
    // Here you would typically send the data to your backend
    // and redirect to a thank you page or dashboard
  };

  const handleStepChange = (step: number) => {
    console.log('Step changed to:', step);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Advanced Lead Capture Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience our progressive disclosure lead capture system with gamification elements, 
            personalized reports, and Mingus platform integration.
          </p>
        </div>

        {/* Lead Capture Component */}
        <AdvancedLeadCapture
          onComplete={handleComplete}
          onStepChange={handleStepChange}
        />

        {/* Features Overview */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-3xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Progressive Disclosure</h3>
            <p className="text-gray-600">
              Collect information gradually to reduce form abandonment and increase completion rates.
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-3xl mb-4">🏆</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Gamification</h3>
            <p className="text-gray-600">
              Badges, milestones, and progress tracking to keep users engaged throughout the process.
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Personalized Reports</h3>
            <p className="text-gray-600">
              Generate detailed 5-year career projections and skill recommendations based on user data.
            </p>
          </div>
        </div>

        {/* Technical Details */}
        <div className="mt-16 bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Technical Implementation</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Progressive disclosure with 3-step process</li>
                <li>• Real-time form validation</li>
                <li>• Gamification badges and milestones</li>
                <li>• Progress tracking and visual indicators</li>
                <li>• Personalized report generation</li>
                <li>• Mingus platform integration</li>
                <li>• Mobile-responsive design</li>
                <li>• TypeScript type safety</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Components</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• AdvancedLeadCapture (main orchestrator)</li>
                <li>• BasicInfoStep (email, salary, location)</li>
                <li>• DetailedProfileStep (career goals, skills)</li>
                <li>• ReportGenerationStep (personalized insights)</li>
                <li>• ProgressIndicator (visual progress)</li>
                <li>• GamificationPanel (badges & milestones)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadCaptureDemo; 