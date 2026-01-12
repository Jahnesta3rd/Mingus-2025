import React, { useState, useCallback, useEffect, useRef } from 'react';
import { X, ArrowLeft, ArrowRight, Check, Mail, User } from 'lucide-react';
import { AssessmentType } from '../types/assessments';
import { InputValidator } from '../utils/validation';
import { Sanitizer } from '../utils/sanitize';
import AssessmentResults from './AssessmentResults';

// Types
export interface AssessmentData {
  email: string;
  firstName?: string;
  phone?: string;
  answers: Record<string, any>;
  assessmentType: string;
  completedAt?: string;
}

export interface AssessmentQuestion {
  id: string;
  question: string;
  type: 'single' | 'multiple' | 'scale' | 'text' | 'email';
  options?: string[];
  required: boolean;
  placeholder?: string;
}

export interface AssessmentConfig {
  id: string;
  title: string;
  description: string;
  questions: AssessmentQuestion[];
  estimatedTime: string;
  icon: React.ReactNode;
}

interface AssessmentModalProps {
  isOpen: boolean;
  assessmentType: AssessmentType | null;
  onClose: () => void;
  onSubmit: (data: AssessmentData) => void;
  isSubmitting?: boolean;
  className?: string;
}

// Assessment Configurations
const assessmentConfigs: Record<AssessmentType, AssessmentConfig> = {
  'ai-risk': {
    id: 'ai-risk',
    title: 'AI Replacement Risk Assessment',
    description: 'Determine your job security in the age of artificial intelligence',
    estimatedTime: '3-5 minutes',
    icon: <User className="w-8 h-8" />,
    questions: [
      {
        id: 'email',
        question: 'What\'s your email address?',
        type: 'email',
        required: true,
        placeholder: 'your.email@example.com'
      },
      {
        id: 'firstName',
        question: 'What\'s your first name?',
        type: 'text',
        required: true,
        placeholder: 'Your first name'
      },
      {
        id: 'jobTitle',
        question: 'What\'s your current job title?',
        type: 'text',
        required: true,
        placeholder: 'e.g., Software Engineer, Marketing Manager'
      },
      {
        id: 'industry',
        question: 'What industry do you work in?',
        type: 'single',
        required: true,
        options: [
          'Technology/Software',
          'Healthcare',
          'Finance/Banking',
          'Education',
          'Manufacturing',
          'Retail/E-commerce',
          'Marketing/Advertising',
          'Consulting',
          'Government',
          'Other'
        ]
      },
      {
        id: 'automationLevel',
        question: 'How much of your daily work involves repetitive, rule-based tasks?',
        type: 'scale',
        required: true,
        options: ['Very Little', 'Some', 'Moderate', 'A Lot', 'Almost Everything']
      },
      {
        id: 'aiTools',
        question: 'Do you currently use AI tools in your work?',
        type: 'single',
        required: true,
        options: ['Never', 'Rarely', 'Sometimes', 'Often', 'Constantly']
      },
      {
        id: 'skills',
        question: 'Which skills best describe your expertise? (Select all that apply)',
        type: 'multiple',
        required: true,
        options: [
          'Data Analysis',
          'Creative Writing',
          'Customer Service',
          'Project Management',
          'Coding/Programming',
          'Sales',
          'Research',
          'Design',
          'Strategy',
          'Teaching/Training'
        ]
      }
    ]
  },
  'income-comparison': {
    id: 'income-comparison',
    title: 'Income Comparison Assessment',
    description: 'See how your income compares to others in your field and location',
    estimatedTime: '2-3 minutes',
    icon: <User className="w-8 h-8" />,
    questions: [
      {
        id: 'email',
        question: 'What\'s your email address?',
        type: 'email',
        required: true,
        placeholder: 'your.email@example.com'
      },
      {
        id: 'firstName',
        question: 'What\'s your first name?',
        type: 'text',
        required: true,
        placeholder: 'Your first name'
      },
      {
        id: 'currentSalary',
        question: 'What\'s your current annual salary?',
        type: 'single',
        required: true,
        options: [
          'Under $30,000',
          '$30,000 - $50,000',
          '$50,000 - $75,000',
          '$75,000 - $100,000',
          '$100,000 - $150,000',
          '$150,000 - $200,000',
          'Over $200,000'
        ]
      },
      {
        id: 'jobTitle',
        question: 'What\'s your job title?',
        type: 'text',
        required: true,
        placeholder: 'e.g., Software Engineer, Marketing Manager'
      },
      {
        id: 'experience',
        question: 'How many years of experience do you have?',
        type: 'single',
        required: true,
        options: [
          'Less than 1 year',
          '1-2 years',
          '3-5 years',
          '6-10 years',
          '11-15 years',
          '16-20 years',
          'Over 20 years'
        ]
      },
      {
        id: 'location',
        question: 'What\'s your work location?',
        type: 'single',
        required: true,
        options: [
          'New York, NY',
          'San Francisco, CA',
          'Los Angeles, CA',
          'Chicago, IL',
          'Austin, TX',
          'Seattle, WA',
          'Boston, MA',
          'Remote',
          'Other'
        ]
      },
      {
        id: 'education',
        question: 'What\'s your highest level of education?',
        type: 'single',
        required: true,
        options: [
          'High School',
          'Associate Degree',
          'Bachelor\'s Degree',
          'Master\'s Degree',
          'PhD/Professional Degree'
        ]
      }
    ]
  },
  'cuffing-season': {
    id: 'cuffing-season',
    title: 'Cuffing Season Score Assessment',
    description: 'Discover your relationship patterns and dating readiness',
    estimatedTime: '3-4 minutes',
    icon: <User className="w-8 h-8" />,
    questions: [
      {
        id: 'email',
        question: 'What\'s your email address?',
        type: 'email',
        required: true,
        placeholder: 'your.email@example.com'
      },
      {
        id: 'firstName',
        question: 'What\'s your first name?',
        type: 'text',
        required: true,
        placeholder: 'Your first name'
      },
      {
        id: 'age',
        question: 'What\'s your age range?',
        type: 'single',
        required: true,
        options: [
          '18-24',
          '25-29',
          '30-34',
          '35-39',
          '40-44',
          '45-49',
          '50+'
        ]
      },
      {
        id: 'relationshipStatus',
        question: 'What\'s your current relationship status?',
        type: 'single',
        required: true,
        options: [
          'Single and dating',
          'Single and not dating',
          'In a relationship',
          'Married',
          'Divorced',
          'Widowed'
        ]
      },
      {
        id: 'datingFrequency',
        question: 'How often do you go on dates?',
        type: 'single',
        required: true,
        options: [
          'Multiple times per week',
          'Once a week',
          '2-3 times per month',
          'Once a month',
          'Rarely',
          'Never'
        ]
      },
      {
        id: 'winterDating',
        question: 'Do you find yourself more interested in dating during winter months?',
        type: 'single',
        required: true,
        options: [
          'Much more interested',
          'Somewhat more interested',
          'No change',
          'Less interested',
          'Much less interested'
        ]
      },
      {
        id: 'relationshipGoals',
        question: 'What are you looking for in a relationship? (Select all that apply)',
        type: 'multiple',
        required: true,
        options: [
          'Casual dating',
          'Serious relationship',
          'Marriage',
          'Friendship',
          'Just having fun',
          'Not sure'
        ]
      }
    ]
  },
  'layoff-risk': {
    id: 'layoff-risk',
    title: 'Layoff Risk Assessment',
    description: 'Evaluate your job security and career stability',
    estimatedTime: '4-5 minutes',
    icon: <User className="w-8 h-8" />,
    questions: [
      {
        id: 'email',
        question: 'What\'s your email address?',
        type: 'email',
        required: true,
        placeholder: 'your.email@example.com'
      },
      {
        id: 'firstName',
        question: 'What\'s your first name?',
        type: 'text',
        required: true,
        placeholder: 'Your first name'
      },
      {
        id: 'companySize',
        question: 'How many employees does your company have?',
        type: 'single',
        required: true,
        options: [
          '1-10 employees',
          '11-50 employees',
          '51-200 employees',
          '201-1000 employees',
          '1000+ employees'
        ]
      },
      {
        id: 'tenure',
        question: 'How long have you been with your current company?',
        type: 'single',
        required: true,
        options: [
          'Less than 6 months',
          '6 months - 1 year',
          '1-2 years',
          '3-5 years',
          '6-10 years',
          'Over 10 years'
        ]
      },
      {
        id: 'performance',
        question: 'How would you rate your recent job performance?',
        type: 'single',
        required: true,
        options: [
          'Exceeds expectations',
          'Meets expectations',
          'Below expectations',
          'Unsure'
        ]
      },
      {
        id: 'companyHealth',
        question: 'How would you describe your company\'s financial health?',
        type: 'single',
        required: true,
        options: [
          'Very strong',
          'Strong',
          'Stable',
          'Some concerns',
          'Major concerns'
        ]
      },
      {
        id: 'recentLayoffs',
        question: 'Has your company had recent layoffs?',
        type: 'single',
        required: true,
        options: [
          'Yes, major layoffs',
          'Yes, minor layoffs',
          'No layoffs',
          'Not sure'
        ]
      },
      {
        id: 'skillsRelevance',
        question: 'How relevant are your skills to current market demands?',
        type: 'single',
        required: true,
        options: [
          'Very relevant',
          'Somewhat relevant',
          'Neutral',
          'Somewhat outdated',
          'Very outdated'
        ]
      }
    ]
  },
  'vehicle-financial-health': {
    id: 'vehicle-financial-health',
    title: 'Vehicle Financial Health Assessment',
    description: 'Evaluate your vehicle-related financial wellness and planning',
    estimatedTime: '4-5 minutes',
    icon: <User className="w-8 h-8" />,
    questions: [
      {
        id: 'email',
        question: 'What\'s your email address?',
        type: 'email',
        required: true,
        placeholder: 'your.email@example.com'
      },
      {
        id: 'firstName',
        question: 'What\'s your first name?',
        type: 'text',
        required: true,
        placeholder: 'Your first name'
      },
      {
        id: 'vehicleAge',
        question: 'How old is your current vehicle?',
        type: 'single',
        required: true,
        options: [
          'Less than 2 years',
          '2-5 years',
          '6-10 years',
          '11-15 years',
          '16-20 years',
          'Over 20 years',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'vehicleMileage',
        question: 'What is your vehicle\'s current mileage?',
        type: 'single',
        required: true,
        options: [
          'Under 50,000 miles',
          '50,000 - 75,000 miles',
          '75,000 - 100,000 miles',
          '100,000 - 150,000 miles',
          '150,000 - 200,000 miles',
          'Over 200,000 miles',
          'I don\'t know'
        ]
      },
      {
        id: 'maintenanceHistory',
        question: 'How would you describe your recent maintenance history?',
        type: 'single',
        required: true,
        options: [
          'Regular maintenance, no major issues',
          'Some minor repairs, mostly routine maintenance',
          'Several unexpected repairs in the past year',
          'Major repairs needed recently',
          'I don\'t keep track of maintenance',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'monthlyTransportationCosts',
        question: 'How aware are you of your monthly transportation costs?',
        type: 'single',
        required: true,
        options: [
          'Very aware - I track every expense',
          'Somewhat aware - I know the major costs',
          'Generally aware - I have a rough idea',
          'Not very aware - I don\'t track these costs',
          'Not aware at all - I don\'t know my costs'
        ]
      },
      {
        id: 'emergencyFund',
        question: 'Do you have an emergency fund specifically for vehicle repairs?',
        type: 'single',
        required: true,
        options: [
          'Yes, I have a dedicated vehicle emergency fund',
          'Yes, I have a general emergency fund that could cover vehicle repairs',
          'No, but I have some savings that could help',
          'No, I don\'t have any emergency savings',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'vehicleFinancialStress',
        question: 'How much financial stress do your vehicle costs cause you?',
        type: 'single',
        required: true,
        options: [
          'No stress at all',
          'Minimal stress',
          'Moderate stress',
          'Significant stress',
          'Extreme stress',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'commuteDistance',
        question: 'What is your typical daily commute distance?',
        type: 'single',
        required: true,
        options: [
          'Less than 10 miles round trip',
          '10-25 miles round trip',
          '25-50 miles round trip',
          '50-75 miles round trip',
          'Over 75 miles round trip',
          'I work from home',
          'I don\'t have a regular commute'
        ]
      },
      {
        id: 'vehicleInsurance',
        question: 'How would you describe your vehicle insurance and financing situation?',
        type: 'single',
        required: true,
        options: [
          'Fully paid off, comprehensive insurance',
          'Making payments, comprehensive insurance',
          'Fully paid off, basic insurance',
          'Making payments, basic insurance',
          'Leasing with insurance included',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'futureVehiclePlanning',
        question: 'How are you planning for your next vehicle purchase?',
        type: 'single',
        required: true,
        options: [
          'I have a detailed savings plan and timeline',
          'I have a general savings plan',
          'I\'m saving some money but no specific plan',
          'I\'ll figure it out when the time comes',
          'I plan to finance it when needed',
          'I don\'t plan to buy another vehicle'
        ]
      }
    ]
  }
};

// Loading Skeleton Component
const LoadingSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="h-8 bg-gray-700 rounded w-3/4 mb-4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-700 rounded w-full"></div>
      <div className="h-4 bg-gray-700 rounded w-5/6"></div>
      <div className="h-4 bg-gray-700 rounded w-4/6"></div>
    </div>
  </div>
);

// Main AssessmentModal Component
const AssessmentModal: React.FC<AssessmentModalProps> = ({
  isOpen,
  assessmentType,
  onClose,
  onSubmit,
  isSubmitting = false,
  className = ''
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<any>(null);
  
  const modalRef = useRef<HTMLDivElement>(null);

  const config = assessmentType ? assessmentConfigs[assessmentType] : null;
  const totalSteps = config ? config.questions.length : 0;
  const currentQuestion = config ? config.questions[currentStep] : null;

  // Handle modal visibility
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      setCurrentStep(0);
      setAnswers({});
      setError(null);
      setShowResults(false);
      setAssessmentResult(null);
    } else {
      setIsVisible(false);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  // Handle answer change with validation
  const handleAnswerChange = useCallback((questionId: string, value: any) => {
    // Sanitize input based on question type
    let sanitizedValue = value;
    
    if (typeof value === 'string') {
      sanitizedValue = Sanitizer.sanitizeString(value);
    } else if (Array.isArray(value)) {
      sanitizedValue = value.map(item => 
        typeof item === 'string' ? Sanitizer.sanitizeString(item) : item
      );
    }
    
    setAnswers(prev => ({
      ...prev,
      [questionId]: sanitizedValue
    }));
  }, []);

  // Handle next step
  const handleNext = useCallback(() => {
    if (currentQuestion && currentQuestion.required && !answers[currentQuestion.id]) {
      setError('This question is required');
      return;
    }

    if (currentStep < totalSteps - 1) {
      setCurrentStep(prev => prev + 1);
      setError(null);
    } else {
      handleSubmit();
    }
  }, [currentStep, totalSteps, currentQuestion, answers]);

  // Handle previous step
  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      setError(null);
    }
  }, [currentStep]);

  // Handle form submission with validation
  const handleSubmit = useCallback(async () => {
    if (!config || !answers.email) {
      setError('Email is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Validate email
      const emailValidation = InputValidator.validateEmail(answers.email);
      if (!emailValidation.isValid) {
        setError(`Email: ${emailValidation.errors.join(', ')}`);
        setLoading(false);
        return;
      }

      // Validate first name if provided
      if (answers.firstName) {
        const nameValidation = InputValidator.validateName(answers.firstName);
        if (!nameValidation.isValid) {
          setError(`Name: ${nameValidation.errors.join(', ')}`);
          setLoading(false);
          return;
        }
      }

      // Validate phone if provided
      if (answers.phone) {
        const phoneValidation = InputValidator.validatePhone(answers.phone);
        if (!phoneValidation.isValid) {
          setError(`Phone: ${phoneValidation.errors.join(', ')}`);
          setLoading(false);
          return;
        }
      }

      // Validate and sanitize answers
      const answersValidation = InputValidator.validateAssessmentAnswers(answers);
      if (!answersValidation.isValid) {
        setError(`Answers: ${answersValidation.errors.join(', ')}`);
        setLoading(false);
        return;
      }

      const assessmentData: AssessmentData = {
        email: emailValidation.sanitizedValue!,
        firstName: answers.firstName ? InputValidator.validateName(answers.firstName).sanitizedValue : undefined,
        phone: answers.phone ? InputValidator.validatePhone(answers.phone).sanitizedValue : undefined,
        answers: answersValidation.sanitizedValue as Record<string, any>,
        assessmentType: config.id,
        completedAt: new Date().toISOString()
      };

      // Simulate API call and get results
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Generate mock results based on assessment type
      const mockResult = generateMockResults(assessmentData.assessmentType, assessmentData.answers);
      setAssessmentResult(mockResult);
      setShowResults(true);
      
      // Still call onSubmit for data collection
      onSubmit(assessmentData);
      
      // Show email confirmation
      console.log('📧 Results email sent to:', assessmentData.email);
    } catch (err) {
      setError('Failed to submit assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [config, answers, onSubmit, onClose]);

  // Generate mock results for demonstration
  const generateMockResults = (assessmentType: string, _answers: Record<string, any>) => {
    const baseScore = Math.floor(Math.random() * 40) + 30; // Score between 30-70
    // const riskLevels = ['Low', 'Medium', 'High'];
    const riskLevel = baseScore > 60 ? 'High' : baseScore > 40 ? 'Medium' : 'Low';
    
    const recommendations: Record<AssessmentType, string[]> = {
      'ai-risk': [
        'Develop skills in areas where human judgment is irreplaceable',
        'Learn to work alongside AI tools rather than compete with them',
        'Focus on creative problem-solving and emotional intelligence',
        'Stay updated with AI trends in your industry'
      ],
      'income-comparison': [
        'Research salary benchmarks for your role and location',
        'Document your achievements and value to the company',
        'Practice your negotiation skills and timing',
        'Consider additional certifications or training'
      ],
      'cuffing-season': [
        'Be authentic and genuine in your interactions',
        'Focus on building meaningful connections',
        'Work on your communication skills',
        'Take care of your physical and mental health'
      ],
      'layoff-risk': [
        'Build strong relationships with key stakeholders',
        'Develop skills that are in high demand',
        'Create a personal brand and online presence',
        'Have a backup plan and emergency fund'
      ],
      'vehicle-financial-health': [
        'Create a dedicated vehicle emergency fund',
        'Track all vehicle-related expenses monthly',
        'Research and compare insurance options regularly',
        'Plan ahead for your next vehicle purchase'
      ]
    };

    return {
      score: baseScore,
      risk_level: riskLevel,
      recommendations: assessmentType && assessmentType in recommendations 
        ? recommendations[assessmentType as AssessmentType] 
        : recommendations['ai-risk'],
      assessment_type: assessmentType,
      completed_at: new Date().toISOString(),
      percentile: Math.floor(Math.random() * 40) + 30,
      benchmark: {
        average: baseScore - 10,
        high: baseScore + 20,
        low: baseScore - 25
      }
    };
  };

  // Handle retaking assessment
  const handleRetake = useCallback(() => {
    setShowResults(false);
    setCurrentStep(0);
    setAnswers({});
    setError(null);
  }, []);

  // Handle sharing results
  const handleShare = useCallback(() => {
    if (navigator.share) {
      navigator.share({
        title: `${config?.title} Results`,
        text: `I just completed the ${config?.title} and scored ${assessmentResult?.score}/100!`,
        url: window.location.href
      });
    } else {
      // Fallback to copying to clipboard
      navigator.clipboard.writeText(`I just completed the ${config?.title} and scored ${assessmentResult?.score}/100! Check it out: ${window.location.href}`);
    }
  }, [config, assessmentResult]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleNext();
    }
  }, [handleNext]);

  if (!isOpen || !config) return null;

  // Show results if available
  if (showResults && assessmentResult) {
    return (
      <div 
        className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 transition-all duration-300 ${
          isVisible ? 'opacity-100' : 'opacity-0'
        } ${className}`}
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <AssessmentResults
          result={assessmentResult}
          onClose={onClose}
          onRetake={handleRetake}
          onShare={handleShare}
        />
      </div>
    );
  }

  return (
    <div 
      className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 transition-all duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      } ${className}`}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        ref={modalRef}
        className={`bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden transition-all duration-300 ${
          isVisible ? 'scale-100' : 'scale-95'
        }`}
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="text-violet-200">
                {config.icon}
              </div>
              <div>
                <h2 className="text-xl font-bold">{config.title}</h2>
                <p className="text-violet-100 text-sm">{config.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-violet-200 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-violet-600 rounded p-1"
              aria-label="Close assessment"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Enhanced Progress Bar */}
          <div className="w-full bg-violet-400 bg-opacity-30 rounded-full h-3 mb-2">
            <div 
              className="bg-white h-3 rounded-full transition-all duration-500 ease-out shadow-lg"
              style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-violet-100 text-sm font-medium">
              Question {currentStep + 1} of {totalSteps}
            </p>
            <p className="text-violet-200 text-xs">
              {config.estimatedTime}
            </p>
          </div>
          <div className="mt-1 text-xs text-violet-200">
            {Math.round(((currentStep + 1) / totalSteps) * 100)}% Complete
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {(loading || isSubmitting) ? (
            <LoadingSkeleton />
          ) : currentQuestion ? (
            <div className="space-y-6">
              {/* Question Progress Indicator */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-violet-300">
                    Question {currentStep + 1} of {totalSteps}
                  </span>
                  <span className="text-xs text-gray-400">
                    {Math.round(((currentStep + 1) / totalSteps) * 100)}% Complete
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div 
                    className="bg-gradient-to-r from-violet-500 to-purple-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {currentQuestion.question}
                </h3>
                {currentQuestion.required && (
                  <p className="text-gray-400 text-sm">* Required</p>
                )}
              </div>

              {/* Question Input */}
              <div className="space-y-4">
                {currentQuestion.type === 'email' && (
                  <div>
                    <label htmlFor={`${currentQuestion.id}-input`} className="block text-sm font-medium text-white mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <input
                        id={`${currentQuestion.id}-input`}
                        type="email"
                        value={answers[currentQuestion.id] || ''}
                        onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                        placeholder={currentQuestion.placeholder}
                        disabled={isSubmitting}
                        className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                        required={currentQuestion.required}
                        aria-describedby={`${currentQuestion.id}-help`}
                      />
                    </div>
                    <p id={`${currentQuestion.id}-help`} className="text-sm text-gray-400 mt-1">
                      Enter your email address to receive your assessment results
                    </p>
                  </div>
                )}

                {currentQuestion.type === 'text' && (
                  <div>
                    <label htmlFor={`${currentQuestion.id}-input`} className="block text-sm font-medium text-white mb-2">
                      {currentQuestion.id === 'firstName' ? 'First Name' : 
                       currentQuestion.id === 'jobTitle' ? 'Job Title' : 
                       currentQuestion.id === 'phone' ? 'Phone Number' : 
                       'Text Input'}
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <input
                        id={`${currentQuestion.id}-input`}
                        type="text"
                        value={answers[currentQuestion.id] || ''}
                        onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                        placeholder={currentQuestion.placeholder}
                        disabled={isSubmitting}
                        className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                        required={currentQuestion.required}
                        aria-describedby={`${currentQuestion.id}-help`}
                      />
                    </div>
                    <p id={`${currentQuestion.id}-help`} className="text-sm text-gray-400 mt-1">
                      {currentQuestion.id === 'firstName' ? 'Enter your first name' : 
                       currentQuestion.id === 'jobTitle' ? 'Enter your current job title or position' : 
                       currentQuestion.id === 'phone' ? 'Enter your phone number (optional)' : 
                       'Enter your response'}
                    </p>
                  </div>
                )}

                {currentQuestion.type === 'single' && currentQuestion.options && (
                  <fieldset>
                    <legend className="text-sm font-medium text-white mb-3">
                      {currentQuestion.id === 'industry' ? 'Select your industry' :
                       currentQuestion.id === 'automationLevel' ? 'How much of your work is repetitive?' :
                       currentQuestion.id === 'aiTools' ? 'How often do you use AI tools?' :
                       currentQuestion.id === 'currentSalary' ? 'Select your salary range' :
                       currentQuestion.id === 'experience' ? 'Select your experience level' :
                       currentQuestion.id === 'location' ? 'Select your location' :
                       currentQuestion.id === 'mood' ? 'How are you feeling today?' :
                       'Select an option'}
                    </legend>
                    <div className="space-y-2">
                      {currentQuestion.options.map((option, index) => (
                        <label
                          key={index}
                          className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all duration-200 focus-within:outline-none focus-within:ring-2 focus-within:ring-violet-500 focus-within:ring-offset-2 focus-within:ring-offset-gray-900 ${
                            answers[currentQuestion.id] === option
                              ? 'border-violet-500 bg-violet-500 bg-opacity-10'
                              : 'border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <input
                            type="radio"
                            name={currentQuestion.id}
                            value={option}
                            checked={answers[currentQuestion.id] === option}
                            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                            className="sr-only focus:not-sr-only focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2"
                            aria-describedby={`${currentQuestion.id}-help`}
                          />
                          <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
                            answers[currentQuestion.id] === option
                              ? 'border-violet-500 bg-violet-500'
                              : 'border-gray-400'
                          }`}>
                            {answers[currentQuestion.id] === option && (
                              <div className="w-2 h-2 bg-white rounded-full" />
                            )}
                          </div>
                          <span className="text-white">{option}</span>
                        </label>
                      ))}
                    </div>
                    <p id={`${currentQuestion.id}-help`} className="text-sm text-gray-400 mt-2">
                      {currentQuestion.id === 'industry' ? 'Choose the industry that best describes your work' :
                       currentQuestion.id === 'automationLevel' ? 'Consider how much of your daily tasks follow predictable patterns' :
                       currentQuestion.id === 'aiTools' ? 'Think about how frequently you use AI-powered tools in your work' :
                       currentQuestion.id === 'currentSalary' ? 'Select the range that includes your annual salary' :
                       currentQuestion.id === 'experience' ? 'Consider your total years of professional experience' :
                       currentQuestion.id === 'location' ? 'Select your primary work location' :
                       currentQuestion.id === 'mood' ? 'Choose the option that best describes your current mood' :
                       'Select the option that best applies to you'}
                    </p>
                  </fieldset>
                )}

                {currentQuestion.type === 'multiple' && currentQuestion.options && (
                  <fieldset>
                    <legend className="text-sm font-medium text-white mb-3">
                      {currentQuestion.id === 'skills' ? 'Select your skills (choose all that apply)' :
                       currentQuestion.id === 'interests' ? 'Select your interests (choose all that apply)' :
                       'Select all options that apply'}
                    </legend>
                    <div className="space-y-2">
                      {currentQuestion.options.map((option, index) => (
                        <label
                          key={index}
                          className={`flex items-center p-3 rounded-lg border transition-all duration-200 ${
                            isSubmitting 
                              ? 'cursor-not-allowed opacity-50' 
                              : 'cursor-pointer'
                          } ${
                            answers[currentQuestion.id]?.includes(option)
                              ? 'border-violet-500 bg-violet-500 bg-opacity-10'
                              : 'border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={answers[currentQuestion.id]?.includes(option) || false}
                            onChange={(e) => {
                              const currentValues = answers[currentQuestion.id] || [];
                              const newValues = e.target.checked
                                ? [...currentValues, option]
                                : currentValues.filter((v: string) => v !== option);
                              handleAnswerChange(currentQuestion.id, newValues);
                            }}
                            disabled={isSubmitting}
                            className="sr-only focus:not-sr-only focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 disabled:opacity-50"
                            aria-describedby={`${currentQuestion.id}-help`}
                          />
                          <div className={`w-4 h-4 rounded border-2 mr-3 flex items-center justify-center ${
                            answers[currentQuestion.id]?.includes(option)
                              ? 'border-violet-500 bg-violet-500'
                              : 'border-gray-400'
                          }`}>
                            {answers[currentQuestion.id]?.includes(option) && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                          <span className="text-white">{option}</span>
                        </label>
                      ))}
                    </div>
                    <p id={`${currentQuestion.id}-help`} className="text-sm text-gray-400 mt-2">
                      {currentQuestion.id === 'skills' ? 'Select all skills that you have experience with or are interested in developing' :
                       currentQuestion.id === 'interests' ? 'Select all areas that interest you or are relevant to your goals' :
                       'You can select multiple options that apply to you'}
                    </p>
                  </fieldset>
                )}

                {currentQuestion.type === 'scale' && currentQuestion.options && (
                  <fieldset>
                    <legend className="text-sm font-medium text-white mb-3">
                      {currentQuestion.id === 'automationLevel' ? 'Rate your automation level' :
                       currentQuestion.id === 'satisfaction' ? 'Rate your satisfaction level' :
                       currentQuestion.id === 'confidence' ? 'Rate your confidence level' :
                       'Select your rating'}
                    </legend>
                    <div className="space-y-2">
                      {currentQuestion.options.map((option, index) => (
                        <label
                          key={index}
                          className={`flex items-center p-3 rounded-lg border transition-all duration-200 focus-within:outline-none focus-within:ring-2 focus-within:ring-violet-500 focus-within:ring-offset-2 focus-within:ring-offset-gray-900 ${
                            isSubmitting 
                              ? 'cursor-not-allowed opacity-50' 
                              : 'cursor-pointer'
                          } ${
                            answers[currentQuestion.id] === option
                              ? 'border-violet-500 bg-violet-500 bg-opacity-10'
                              : 'border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <input
                            type="radio"
                            name={currentQuestion.id}
                            value={option}
                            checked={answers[currentQuestion.id] === option}
                            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                            disabled={isSubmitting}
                            className="sr-only focus:not-sr-only focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 disabled:opacity-50"
                            aria-describedby={`${currentQuestion.id}-help`}
                          />
                          <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
                            answers[currentQuestion.id] === option
                              ? 'border-violet-500 bg-violet-500'
                              : 'border-gray-400'
                          }`}>
                            {answers[currentQuestion.id] === option && (
                              <div className="w-2 h-2 bg-white rounded-full" />
                            )}
                          </div>
                          <span className="text-white">{option}</span>
                        </label>
                      ))}
                    </div>
                    <p id={`${currentQuestion.id}-help`} className="text-sm text-gray-400 mt-2">
                      {currentQuestion.id === 'automationLevel' ? 'Consider how much of your daily work involves repetitive, rule-based tasks that could potentially be automated' :
                       currentQuestion.id === 'satisfaction' ? 'Rate your overall satisfaction with the current situation' :
                       currentQuestion.id === 'confidence' ? 'Rate your confidence level in this area' :
                       'Select the option that best represents your rating on this scale'}
                    </p>
                  </fieldset>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-300 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="bg-gray-800 px-6 py-4 flex items-center justify-between">
          <button
            onClick={currentStep > 0 ? handlePrevious : onClose}
            disabled={isSubmitting}
            className="flex items-center space-x-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800 rounded px-2 py-1"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{currentStep > 0 ? 'Previous' : 'Cancel'}</span>
          </button>

          <button
            onClick={handleNext}
            disabled={loading || isSubmitting || (currentQuestion?.required && !answers[currentQuestion.id])}
            className="flex items-center space-x-2 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 disabled:from-gray-600 disabled:to-gray-600 text-white px-6 py-2 rounded-lg font-semibold transition-all duration-200 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800"
          >
            {(loading || isSubmitting) ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                <span>Submitting...</span>
              </>
            ) : currentStep === totalSteps - 1 ? (
              <>
                <span>Complete Assessment</span>
                <Check className="w-4 h-4" />
              </>
            ) : (
              <>
                <span>Next Question</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssessmentModal;
