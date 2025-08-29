import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import LoadingSpinner from '../shared/LoadingSpinner';
import AssessmentQuestion from './AssessmentQuestion';

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

const AssessmentFlow: React.FC = () => {
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
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

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
      
      // Load saved progress from localStorage
      const savedProgress = localStorage.getItem(`assessment_${assessmentType}_progress`);
      if (savedProgress) {
        const { formData: savedData, currentStep: savedStep } = JSON.parse(savedProgress);
        setFormData(savedData || {});
        setCurrentStep(savedStep || 0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assessment');
    } finally {
      setLoading(false);
    }
  }, [assessmentType]);

  useEffect(() => {
    loadAssessment();
  }, [loadAssessment]);

  // Auto-save progress
  const saveProgress = useCallback(() => {
    if (!assessmentType) return;

    const progressData = {
      formData,
      currentStep,
      timestamp: new Date().toISOString(),
    };

    localStorage.setItem(`assessment_${assessmentType}_progress`, JSON.stringify(progressData));
  }, [assessmentType, formData, currentStep]);

  // Auto-save on form data change
  useEffect(() => {
    if (autoSaveRef.current) {
      clearTimeout(autoSaveRef.current);
    }

    autoSaveRef.current = setTimeout(() => {
      saveProgress();
    }, 2000); // Save after 2 seconds of inactivity

    return () => {
      if (autoSaveRef.current) {
        clearTimeout(autoSaveRef.current);
      }
    };
  }, [formData, currentStep, saveProgress]);

  // Validate current question
  const validateQuestion = useCallback((question: Question, value: any): string | null => {
    if (question.required && (!value || (Array.isArray(value) && value.length === 0))) {
      return 'This field is required';
    }

    if (!value) return null;

    // Type-specific validation
    switch (question.type) {
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value as string)) {
          return 'Please enter a valid email address';
        }
        break;
      case 'number':
        const numValue = Number(value);
        if (isNaN(numValue)) {
          return 'Please enter a valid number';
        }
        if (question.validation?.min && numValue < question.validation.min) {
          return `Value must be at least ${question.validation.min}`;
        }
        if (question.validation?.max && numValue > question.validation.max) {
          return `Value must be no more than ${question.validation.max}`;
        }
        break;
      case 'text':
        if (question.validation?.pattern) {
          const regex = new RegExp(question.validation.pattern);
          if (!regex.test(value as string)) {
            return question.validation.message || 'Invalid format';
          }
        }
        break;
    }

    return null;
  }, []);

  // Handle question answer
  const handleAnswer = useCallback((questionId: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [questionId]: value,
    }));

    // Clear error for this question
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[questionId];
      return newErrors;
    });
  }, []);

  // Navigate to next question
  const handleNext = useCallback(() => {
    if (!assessment) return;

    const currentQuestion = assessment.questions[currentStep];
    const currentValue = formData[currentQuestion.id];
    
    // Validate current question
    const validationError = validateQuestion(currentQuestion, currentValue);
    if (validationError) {
      setErrors(prev => ({
        ...prev,
        [currentQuestion.id]: validationError,
      }));
      return;
    }

    // Check skip logic
    if (currentQuestion.skip_logic) {
      const { condition, value: skipValue, skip_to } = currentQuestion.skip_logic;
      if (currentValue === skipValue) {
        const skipIndex = assessment.questions.findIndex(q => q.id === skip_to);
        if (skipIndex !== -1) {
          setCurrentStep(skipIndex);
          return;
        }
      }
    }

    // Move to next question
    if (currentStep < assessment.questions.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  }, [assessment, currentStep, formData, validateQuestion]);

  // Navigate to previous question
  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep]);

  // Submit assessment
  const handleSubmit = useCallback(async () => {
    if (!assessment || !assessmentType) return;

    // Validate all questions
    const newErrors: ValidationErrors = {};
    assessment.questions.forEach(question => {
      const value = formData[question.id];
      const error = validateQuestion(question, value);
      if (error) {
        newErrors[question.id] = error;
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setSubmitting(true);
      
      const endTime = new Date();
      const timeSpentSeconds = startTime ? Math.floor((endTime.getTime() - startTime.getTime()) / 1000) : 0;

      const response = await fetch(`/api/assessments/${assessmentType}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          responses: formData,
          time_spent_seconds: timeSpentSeconds,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Clear saved progress
      localStorage.removeItem(`assessment_${assessmentType}_progress`);
      
      // Navigate to results
      navigate(`/assessments/${assessmentType}/results/${result.assessment_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit assessment');
    } finally {
      setSubmitting(false);
    }
  }, [assessment, assessmentType, formData, startTime, validateQuestion, navigate]);

  // Calculate progress percentage
  const progressPercentage = assessment ? ((currentStep + 1) / assessment.questions.length) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="xl" className="mx-auto mb-4" />
          <p className="text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Unable to Load Assessment</h1>
          <p className="text-gray-600 mb-6">{error || 'Assessment not found'}</p>
          <button
            onClick={() => navigate('/assessments')}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = assessment.questions[currentStep];
  const isLastQuestion = currentStep === assessment.questions.length - 1;
  const hasErrors = Object.keys(errors).length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{assessment.title}</h1>
              <p className="text-gray-600">{assessment.description}</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">
                Question {currentStep + 1} of {assessment.questions.length}
              </div>
              <div className="text-sm text-gray-500">
                Est. {assessment.estimated_duration_minutes} min
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{Math.round(progressPercentage)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-lg p-8">
          {/* Question */}
          <AssessmentQuestion
            question={currentQuestion}
            value={formData[currentQuestion.id]}
            error={errors[currentQuestion.id]}
            onChange={(value) => handleAnswer(currentQuestion.id, value)}
          />

          {/* Navigation */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              ← Previous
            </button>

            <div className="flex items-center space-x-4">
              {/* Save Progress Indicator */}
              <div className="text-sm text-gray-500">
                Progress saved automatically
              </div>

              {/* Next/Submit Button */}
              {isLastQuestion ? (
                <button
                  onClick={handleSubmit}
                  disabled={submitting || hasErrors}
                  className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                >
                  {submitting ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Assessment'
                  )}
                </button>
              ) : (
                <button
                  onClick={handleNext}
                  disabled={hasErrors}
                  className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next →
                </button>
              )}
            </div>
          </div>

          {/* Error Summary */}
          {hasErrors && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="text-sm font-semibold text-red-800 mb-2">
                Please fix the following errors:
              </h3>
              <ul className="text-sm text-red-700 space-y-1">
                {Object.entries(errors).map(([questionId, error]) => (
                  <li key={questionId}>• {error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Help Text */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Your progress is automatically saved. You can close this page and return later.</p>
        </div>
      </div>
    </div>
  );
};

export default AssessmentFlow;
