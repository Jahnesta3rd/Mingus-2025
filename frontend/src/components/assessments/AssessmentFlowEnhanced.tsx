import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import LoadingSpinner from '../shared/LoadingSpinner';
import AssessmentQuestion from './AssessmentQuestion';
import { useAssessmentTracking, useConversionTracking } from '../analytics/AssessmentAnalytics';

// Types
interface Question {
  id: string;
  type: 'text' | 'select' | 'multi_select' | 'radio' | 'number' | 'email';
  text: string;
  required: boolean;
  options?: Array<{
    value: string;
    label: string;
  }>;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  skip_logic?: {
    condition: string;
    value: string;
    skip_to: string;
  };
}

interface AssessmentData {
  id: string;
  type: string;
  title: string;
  description: string;
  questions: Question[];
  estimated_duration_minutes: number;
  version: string;
}

interface FormData {
  [key: string]: string | string[] | number;
}

interface ValidationErrors {
  [key: string]: string;
}

const AssessmentFlowEnhanced: React.FC = () => {
  const { assessmentType } = useParams<{ assessmentType: string }>();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<FormData>({});
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState<Date | null>(null);
  const [progress, setProgress] = useState(0);
  const [timeSpent, setTimeSpent] = useState(0);
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  // Analytics tracking
  const { startAssessment, answerQuestion, completeAssessment } = useAssessmentTracking(
    assessmentType || 'unknown',
    assessment?.id
  );
  const { captureEmail, openConversionModal } = useConversionTracking();

  // Load assessment data
  const loadAssessment = useCallback(async () => {
    if (!assessmentType) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/assessments/${assessmentType}/questions`, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setAssessment(data);
      setStartTime(new Date());
      setQuestionStartTime(new Date());
      
      // Start analytics tracking
      startAssessment();
      
      // Load saved progress from localStorage
      const savedProgress = localStorage.getItem(`assessment_${assessmentType}_progress`);
      if (savedProgress) {
        const { formData: savedData, currentStep: savedStep } = JSON.parse(savedProgress);
        setFormData(savedData || {});
        setCurrentStep(savedStep || 0);
        setProgress(((savedStep || 0) / data.questions.length) * 100);
      } else {
        setProgress((1 / data.questions.length) * 100);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assessment');
    } finally {
      setLoading(false);
    }
  }, [assessmentType, startAssessment]);

  useEffect(() => {
    loadAssessment();
  }, [loadAssessment]);

  // Update time spent
  useEffect(() => {
    const interval = setInterval(() => {
      if (startTime) {
        setTimeSpent(Math.floor((Date.now() - startTime.getTime()) / 1000));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // Auto-save progress
  const saveProgress = useCallback(() => {
    if (assessmentType && assessment) {
      const progressData = {
        formData,
        currentStep,
        timestamp: new Date().toISOString(),
        timeSpent
      };
      localStorage.setItem(`assessment_${assessmentType}_progress`, JSON.stringify(progressData));
    }
  }, [assessmentType, assessment, formData, currentStep, timeSpent]);

  // Auto-save every 30 seconds
  useEffect(() => {
    autoSaveRef.current = setInterval(saveProgress, 30000);
    return () => {
      if (autoSaveRef.current) {
        clearInterval(autoSaveRef.current);
      }
    };
  }, [saveProgress]);

  // Handle question navigation
  const handleNext = useCallback(() => {
    if (!assessment) return;

    const currentQuestion = assessment.questions[currentStep];
    
    // Validate current question
    if (currentQuestion.required && !formData[currentQuestion.id]) {
      setErrors({ [currentQuestion.id]: 'This question is required' });
      return;
    }

    // Track question answered
    const timeSpentOnQuestion = questionStartTime 
      ? Math.floor((Date.now() - questionStartTime.getTime()) / 1000)
      : 0;
    
    answerQuestion(currentQuestion.id, currentStep + 1, timeSpentOnQuestion);

    // Clear errors
    setErrors({});

    // Move to next question
    const nextStep = currentStep + 1;
    if (nextStep < assessment.questions.length) {
      setCurrentStep(nextStep);
      setQuestionStartTime(new Date());
      setProgress(((nextStep + 1) / assessment.questions.length) * 100);
    } else {
      // Assessment completed
      handleSubmit();
    }
  }, [assessment, currentStep, formData, errors, answerQuestion, questionStartTime]);

  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      const prevStep = currentStep - 1;
      setCurrentStep(prevStep);
      setQuestionStartTime(new Date());
      setProgress(((prevStep + 1) / (assessment?.questions.length || 1)) * 100);
      setErrors({});
    }
  }, [currentStep, assessment]);

  // Handle form data changes
  const handleInputChange = useCallback((questionId: string, value: string | string[] | number) => {
    setFormData(prev => ({
      ...prev,
      [questionId]: value
    }));

    // Clear error for this field
    if (errors[questionId]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[questionId];
        return newErrors;
      });
    }
  }, [errors]);

  // Handle assessment submission
  const handleSubmit = useCallback(async () => {
    if (!assessment) return;

    try {
      setSubmitting(true);

      // Calculate final metrics
      const finalTimeSpent = startTime 
        ? Math.floor((Date.now() - startTime.getTime()) / 1000)
        : timeSpent;
      
      const questionsAnswered = Object.keys(formData).length;
      const completionRate = (questionsAnswered / assessment.questions.length) * 100;

      // Submit assessment
      const response = await fetch(`/api/assessments/${assessmentType}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          responses: formData,
          time_spent: finalTimeSpent,
          questions_answered: questionsAnswered
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // Track assessment completion
      completeAssessment(
        result.score,
        result.risk_level,
        finalTimeSpent
      );

      // Clear saved progress
      localStorage.removeItem(`assessment_${assessmentType}_progress`);

      // Navigate to results
      navigate(`/assessment/${assessmentType}/results`, {
        state: {
          result,
          timeSpent: finalTimeSpent,
          questionsAnswered,
          completionRate
        }
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit assessment');
      setSubmitting(false);
    }
  }, [assessment, assessmentType, formData, startTime, timeSpent, completeAssessment, navigate]);

  // Handle email capture (if this is an email question)
  const handleEmailCapture = useCallback((email: string) => {
    captureEmail(email, 'assessment');
  }, [captureEmail]);

  // Handle conversion modal trigger
  const handleConversionTrigger = useCallback(() => {
    openConversionModal('assessment_completion', 'assessment_results');
  }, [openConversionModal]);

  // Format time display
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Get current question
  const currentQuestion = assessment?.questions[currentStep];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error Loading Assessment</div>
          <div className="text-gray-600 mb-4">{error}</div>
          <button
            onClick={loadAssessment}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!assessment || !currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 text-xl">Assessment not found</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {assessment.title}
              </h1>
              <p className="text-sm text-gray-600">
                Question {currentStep + 1} of {assessment.questions.length}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                ⏱ {formatTime(timeSpent)}
              </div>
              <div className="text-sm text-gray-600">
                📊 {Math.round(progress)}% complete
              </div>
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {/* Question */}
          <div className="p-8">
            <AssessmentQuestion
              question={currentQuestion}
              value={formData[currentQuestion.id]}
              error={errors[currentQuestion.id]}
              onChange={(value) => handleInputChange(currentQuestion.id, value)}
              onEmailCapture={handleEmailCapture}
            />
          </div>

          {/* Navigation */}
          <div className="px-8 py-6 bg-gray-50 border-t border-gray-200 rounded-b-lg">
            <div className="flex items-center justify-between">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  currentStep === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-600 text-white hover:bg-gray-700'
                }`}
              >
                Previous
              </button>

              <div className="flex items-center space-x-4">
                <button
                  onClick={saveProgress}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Save Progress
                </button>
                
                <button
                  onClick={handleNext}
                  disabled={submitting}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    submitting
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {submitting ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Submitting...
                    </div>
                  ) : currentStep === assessment.questions.length - 1 ? (
                    'Complete Assessment'
                  ) : (
                    'Next Question'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Assessment Info */}
        <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {currentStep + 1}
              </div>
              <div className="text-sm text-gray-600">Current Question</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Object.keys(formData).length}
              </div>
              <div className="text-sm text-gray-600">Questions Answered</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {formatTime(timeSpent)}
              </div>
              <div className="text-sm text-gray-600">Time Spent</div>
            </div>
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-6 bg-blue-50 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Need Help?
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  Your progress is automatically saved every 30 seconds. You can leave and return anytime.
                  If you need assistance, contact our support team.
                </p>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => handleConversionTrigger()}
                  className="text-sm font-medium text-blue-800 hover:text-blue-600"
                >
                  Get Support →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentFlowEnhanced;
