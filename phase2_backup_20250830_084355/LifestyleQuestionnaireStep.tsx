import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import QuestionnaireFlow from '../questionnaires/QuestionnaireFlow';

const LifestyleQuestionnaireStep: React.FC = () => {
  const [isCompleted, setIsCompleted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if questionnaire is already completed
    const checkCompletion = async () => {
      try {
        const response = await fetch('/api/onboarding/progress/steps');
        const data = await response.json();
        if (data.success && data.step_status?.lifestyle_questionnaire?.completed) {
          setIsCompleted(true);
        }
      } catch (error) {
        console.error('Failed to check completion status:', error);
      }
    };
    checkCompletion();
  }, []);

  const handleQuestionnaireComplete = async (results: any) => {
    setIsSubmitting(true);
    try {
      // Save questionnaire results
      const response = await fetch('/api/lifestyle/questionnaire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(results),
      });

      if (response.ok) {
        // Update onboarding progress
        await fetch('/api/onboarding/step/lifestyle_questionnaire', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ completed: true }),
        });

        setIsCompleted(true);
        navigate('/onboarding/complete');
      }
    } catch (error) {
      console.error('Failed to save questionnaire results:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = async () => {
    setIsSubmitting(true);
    try {
      await fetch('/api/onboarding/step/lifestyle_questionnaire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed: true, skipped: true }),
      });
      navigate('/onboarding/complete');
    } catch (error) {
      console.error('Failed to skip questionnaire:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isCompleted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-100 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Lifestyle Assessment Complete!
          </h1>
          <p className="text-gray-600 mb-6">
            Excellent! Your lifestyle assessment has been completed successfully.
          </p>
          <button
            onClick={() => navigate('/onboarding/complete')}
            className="bg-gradient-to-r from-pink-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-pink-700 hover:to-purple-700 transition-colors"
          >
            Complete Onboarding
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-100">
      {/* Progress Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-semibold text-gray-900">Lifestyle Assessment</h1>
            <span className="text-base leading-relaxed text-gray-500">Step 6 of 7</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-pink-500 to-purple-600 h-2 rounded-full" style={{ width: '86%' }}></div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-sm p-8 mb-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Lifestyle & Preferences Assessment
            </h2>
            <p className="text-gray-600 mb-6">
              Help us understand your lifestyle, values, and preferences to provide more personalized financial advice.
            </p>
            <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
              <h3 className="font-semibold text-pink-800 mb-2">This assessment covers:</h3>
              <ul className="text-base leading-relaxed text-pink-700 space-y-1">
                <li>• Your daily lifestyle and routines</li>
                <li>• Values and priorities in life</li>
                <li>• Spending habits and preferences</li>
                <li>• Future aspirations and dreams</li>
                <li>• Cultural and community connections</li>
              </ul>
            </div>
          </div>

          {/* Questionnaire Component */}
          <QuestionnaireFlow
            questionnaireType="lifestyle"
            onComplete={handleQuestionnaireComplete}
            onSkip={handleSkip}
            isSubmitting={isSubmitting}
          />
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => navigate('/onboarding/financial-questionnaire')}
            className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleSkip}
            disabled={isSubmitting}
            className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
};

export default LifestyleQuestionnaireStep; 