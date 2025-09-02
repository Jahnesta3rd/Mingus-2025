import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import QuestionnaireFlow from '../questionnaires/QuestionnaireFlow';

const FinancialQuestionnaireStep: React.FC = () => {
  const [isCompleted, setIsCompleted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if questionnaire is already completed
    const checkCompletion = async () => {
      try {
        const response = await fetch('/api/onboarding/progress/steps');
        const data = await response.json();
        if (data.success && data.step_status?.financial_questionnaire?.completed) {
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
      const response = await fetch('/api/financial/questionnaire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(results),
      });

      if (response.ok) {
        // Update onboarding progress
        await fetch('/api/onboarding/step/financial_questionnaire', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ completed: true }),
        });

        setIsCompleted(true);
        // Navigate to next step based on user's choice
        const choiceResponse = await fetch('/api/onboarding/choice');
        if (choiceResponse.ok) {
          const choiceData = await choiceResponse.json();
          if (choiceData.choice === 'deep') {
            navigate('/onboarding/lifestyle-questionnaire');
          } else {
            navigate('/onboarding/complete');
          }
        } else {
          navigate('/onboarding/lifestyle-questionnaire');
        }
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
      await fetch('/api/onboarding/step/financial_questionnaire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed: true, skipped: true }),
      });
      navigate('/onboarding/lifestyle-questionnaire');
    } catch (error) {
      console.error('Failed to skip questionnaire:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isCompleted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Financial Assessment Complete!
          </h1>
          <p className="text-gray-600 mb-6">
            Great job! Your financial assessment has been completed successfully.
          </p>
          <button
            onClick={() => navigate('/onboarding/lifestyle-questionnaire')}
            className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-green-700 hover:to-blue-700 transition-colors"
          >
            Continue to Next Step
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      {/* Progress Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-semibold text-gray-900">Financial Assessment</h1>
            <span className="text-base leading-relaxed text-gray-500">Step 5 of 7</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 h-2 rounded-full" style={{ width: '71%' }}></div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-sm p-8 mb-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Financial Wellness Assessment
            </h2>
            <p className="text-gray-600 mb-6">
              This quick assessment helps us understand your financial situation and provide personalized recommendations.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-2">What to expect:</h3>
              <ul className="text-base leading-relaxed text-blue-700 space-y-1">
                <li>• 10-15 questions about your financial situation</li>
                <li>• Takes about 3-5 minutes to complete</li>
                <li>• Your answers help us provide better insights</li>
                <li>• All information is kept secure and private</li>
              </ul>
            </div>
          </div>

          {/* Questionnaire Component */}
          <QuestionnaireFlow
            questionnaireType="financial"
            onComplete={handleQuestionnaireComplete}
            onSkip={handleSkip}
            isSubmitting={isSubmitting}
          />
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => navigate('/onboarding/preferences')}
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

export default FinancialQuestionnaireStep; 