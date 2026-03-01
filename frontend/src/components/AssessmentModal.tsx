import React, { useState, useCallback, useEffect, useRef } from 'react';
import { X, ArrowLeft, ArrowRight, Check, Mail, User } from 'lucide-react';
import { AssessmentType } from '../types/assessments';
import { InputValidator } from '../utils/validation';
import { Sanitizer } from '../utils/sanitize';
import { calculateAssessmentScore } from '../utils/assessmentScoring';
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
    estimatedTime: '5-7 minutes',
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
        id: 'automateFirst',
        question: 'If your employer could automate 50% of your tasks tomorrow at no cost, which 50% would go first?',
        type: 'single',
        required: true,
        options: [
          'Administrative/scheduling',
          'Data entry or reporting',
          'Research and summarizing',
          'Customer communications',
          'Decision-making',
          'I genuinely don\'t know'
        ]
      },
      {
        id: 'replacedByProcess',
        question: 'Have you ever been replaced by a process, software, or system – even partially?',
        type: 'single',
        required: true,
        options: [
          'Yes, significantly',
          'Yes, in a minor way',
          'No, I don\'t think so',
          'I\'m not sure'
        ]
      },
      {
        id: 'productivityDrop',
        question: 'If your role didn\'t exist tomorrow, how long would it take your team to notice a productivity drop?',
        type: 'single',
        required: true,
        options: [
          'Immediately',
          'Within a few days',
          'Within a week or two',
          'A month or more',
          'Probably not for a while'
        ]
      },
      {
        id: 'proactiveLearning',
        question: 'How often do you proactively learn new tools or skills without being told to?',
        type: 'scale',
        required: true,
        options: ['Never', 'Rarely', 'Sometimes', 'Often', 'Constantly']
      },
      {
        id: 'newTechReaction',
        question: 'When new technology is introduced at your job, which best describes your reaction?',
        type: 'single',
        required: true,
        options: [
          'I resist it and stick to what works',
          'I wait to see what others do',
          'I adopt it when required',
          'I try to learn it early',
          'I help others adopt it'
        ]
      },
      {
        id: 'salaryDecidersUnderstand',
        question: 'Do the people who decide your salary fully understand what you do day to day?',
        type: 'single',
        required: true,
        options: [
          'Yes, completely',
          'Mostly',
          'Somewhat',
          'Not really',
          'No, not at all'
        ]
      },
      {
        id: 'valueInHeadVsDocumented',
        question: 'How much of the unique value you bring to your job lives in your head versus in documented systems?',
        type: 'scale',
        required: true,
        options: [
          'Almost all in my head',
          'Mostly in my head',
          'Split roughly evenly',
          'Mostly documented',
          'Almost entirely documented'
        ]
      },
      {
        id: 'toolTookOverTask',
        question: 'In the past year, has a tool or system taken over any task that used to require your direct involvement?',
        type: 'single',
        required: true,
        options: [
          'Yes, several tasks',
          'Yes, one or two things',
          'Not yet but I can see it coming',
          'No',
          'Not that I\'m aware of'
        ]
      },
      {
        id: 'reasonNotLearningAI',
        question: 'What\'s your honest reason for not learning AI tools more deeply?',
        type: 'single',
        required: true,
        options: [
          'No time',
          'No access or resources',
          'Don\'t see the relevance',
          'Worried it will replace me',
          'Already using them actively',
          'No particular reason'
        ]
      },
      {
        id: 'jobExistsFiveYears',
        question: 'If you had to bet on your job existing in its current form five years from now, what odds would you give yourself?',
        type: 'single',
        required: true,
        options: [
          'Less than 25% chance it survives unchanged',
          '25-50%',
          '50-75%',
          '75-90%',
          'Greater than 90%'
        ]
      }
    ]
  },
  'income-comparison': {
    id: 'income-comparison',
    title: 'Income Comparison Assessment',
    description: 'See how your income compares to others in your field and location',
    estimatedTime: '4-6 minutes',
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
        id: 'lastSalaryResearch',
        question: 'When did you last research what someone in your exact role earns at another company?',
        type: 'single',
        required: true,
        options: [
          'Within the last 3 months',
          '6-12 months ago',
          '1-2 years ago',
          'More than 2 years ago',
          'Never'
        ]
      },
      {
        id: 'lastRaiseNegotiate',
        question: 'When you last received a raise or offer, did you negotiate?',
        type: 'single',
        required: true,
        options: [
          'Yes, and I got more than the initial offer',
          'Yes, but I accepted the first counter',
          'No, I accepted without negotiating',
          'I didn\'t think I could negotiate',
          'I don\'t remember'
        ]
      },
      {
        id: 'colleagueEarnedMore',
        question: 'If a colleague doing the same job as you earned 30% more, what would you do?',
        type: 'single',
        required: true,
        options: [
          'Ask my manager immediately',
          'Research whether it\'s true first',
          'Feel upset but probably do nothing',
          'Update my resume',
          'Leave as soon as possible'
        ]
      },
      {
        id: 'benchmarkSalaryFrequency',
        question: 'How often do you benchmark your salary against market data?',
        type: 'scale',
        required: true,
        options: ['Never', 'Rarely', 'Once a year', 'Every few months', 'Continuously']
      },
      {
        id: 'reasonNotEarnedMore',
        question: 'What is the single biggest reason you haven\'t earned more money in the past 2 years?',
        type: 'single',
        required: true,
        options: [
          'Didn\'t ask for a raise',
          'Limited opportunities at my company',
          'My skills aren\'t in high demand',
          'Personal circumstances limited my ability to move',
          'I have been earning more',
          'I don\'t know'
        ]
      },
      {
        id: 'incomeGrowthInitiative',
        question: 'How much of your income growth over your career has come from proactive moves you made vs. things that just happened?',
        type: 'scale',
        required: true,
        options: [
          'Almost all just happened',
          'Mostly happened to me',
          'Roughly equal',
          'Mostly my initiative',
          'Almost entirely my own doing'
        ]
      },
      {
        id: 'incomeSameFiveYears',
        question: 'If your income stayed exactly the same for the next 5 years, how significantly would it affect your quality of life?',
        type: 'scale',
        required: true,
        options: [
          'No impact at all',
          'Minor inconvenience',
          'Moderate concern',
          'Serious problem',
          'It would be devastating'
        ]
      },
      {
        id: 'turnedDownHigherPay',
        question: 'Have you ever turned down a higher-paying opportunity to stay in your current role?',
        type: 'single',
        required: true,
        options: [
          'Yes, multiple times',
          'Yes, once',
          'No, I\'ve always pursued better pay',
          'Not applicable'
        ]
      },
      {
        id: 'understandTotalComp',
        question: 'How well do you understand the total value of your compensation, including benefits, equity, and perks?',
        type: 'scale',
        required: true,
        options: ['Not at all', 'Vaguely', 'Somewhat', 'Pretty well', 'Completely']
      }
    ]
  },
  'cuffing-season': {
    id: 'cuffing-season',
    title: 'Cuffing Season Score Assessment',
    description: 'Discover your relationship patterns and dating readiness',
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
        id: 'lastRelationshipEnded',
        question: 'Looking back at your last significant relationship, what ended it or what\'s keeping you from one now?',
        type: 'single',
        required: true,
        options: [
          'Compatibility issues',
          'Timing or life circumstances',
          'Financial stress',
          'Emotional unavailability (mine)',
          'Emotional unavailability (theirs)',
          'I\'m currently in a relationship',
          'I\'m not sure'
        ]
      },
      {
        id: 'whatWouldGetInWay',
        question: 'If the right person came along tomorrow, what would realistically get in the way?',
        type: 'multiple',
        required: true,
        options: [
          'Work schedule or career demands',
          'Financial stress',
          'Where I live',
          'My own emotional state',
          'Past relationship baggage',
          'Nothing - I\'m ready',
          'I don\'t know'
        ]
      },
      {
        id: 'datingHabitsAligned',
        question: 'How aligned are your dating habits with what you say you actually want?',
        type: 'scale',
        required: true,
        options: ['Completely misaligned', 'Somewhat misaligned', 'Neutral', 'Mostly aligned', 'Completely aligned']
      },
      {
        id: 'overlookRedFlags',
        question: 'When you\'re attracted to someone, do you tend to overlook red flags early on?',
        type: 'scale',
        required: true,
        options: ['Almost always', 'Often', 'Sometimes', 'Rarely', 'Never']
      },
      {
        id: 'financialConfidenceDating',
        question: 'How much does your financial situation affect the confidence you bring to dating?',
        type: 'scale',
        required: true,
        options: ['Not at all', 'Slightly', 'Moderately', 'Quite a bit', 'Significantly']
      },
      {
        id: 'financialIncompatibilityTension',
        question: 'Have you been in a relationship where financial incompatibility was a source of tension?',
        type: 'single',
        required: true,
        options: [
          'Yes, it was a major issue',
          'Yes, a minor issue',
          'No, not at all',
          'I haven\'t been in a serious relationship'
        ]
      },
      {
        id: 'commitmentConcerns',
        question: 'When you think about committing to a partner, what concerns you most?',
        type: 'single',
        required: true,
        options: [
          'Losing my independence',
          'Financial entanglement',
          'Getting hurt again',
          'Making the wrong choice',
          'Nothing - I\'m ready to commit',
          'Not applicable'
        ]
      },
      {
        id: 'friendsInfluenceDating',
        question: 'How much of your dating behavior is influenced by what your friends or social circle are doing?',
        type: 'scale',
        required: true,
        options: ['Barely at all', 'Slightly', 'Somewhat', 'A fair amount', 'Significantly']
      },
      {
        id: 'honestAboutFinances',
        question: 'How honest are you with new partners about your financial situation and goals early in a relationship?',
        type: 'scale',
        required: true,
        options: ['Not at all honest', 'Somewhat guarded', 'Neutral', 'Fairly open', 'Completely open']
      }
    ]
  },
  'layoff-risk': {
    id: 'layoff-risk',
    title: 'Layoff Risk Assessment',
    description: 'Evaluate your job security and career stability',
    estimatedTime: '5-6 minutes',
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
        id: 'confidentSurviveCut',
        question: 'If your company had to cut 20% of its workforce tomorrow, how confident are you that you\'d be in the surviving 80%?',
        type: 'scale',
        required: true,
        options: ['Not confident at all', 'Slightly confident', 'Somewhat confident', 'Fairly confident', 'Very confident']
      },
      {
        id: 'replaceableInstitutionalKnowledge',
        question: 'How replaceable is your institutional knowledge – the things only you know about your company or role?',
        type: 'scale',
        required: true,
        options: [
          'Anyone could do my job quickly',
          'It would take some ramp-up',
          'I\'d be hard to replace in the short term',
          'I\'m very difficult to replace',
          'Irreplaceable in my current context'
        ]
      },
      {
        id: 'trustedColleagueJobSecurityConcerns',
        question: 'Has a trusted colleague, manager, or mentor ever raised concerns about your job security – even gently?',
        type: 'single',
        required: true,
        options: [
          'Yes, explicitly',
          'Yes, subtly or indirectly',
          'No, I\'ve only received positive signals',
          'I don\'t have those kinds of conversations',
          'I\'m not sure'
        ]
      },
      {
        id: 'relationshipWithDecisionMakers',
        question: 'How would you describe your relationship with the decision-makers who would determine layoffs at your company?',
        type: 'single',
        required: true,
        options: [
          'Strong, I\'m well-known and valued',
          'Good, they know who I am',
          'Neutral, they know my name',
          'Weak, I\'m mostly invisible to leadership',
          'I don\'t know'
        ]
      },
      {
        id: 'stepsToReduceLayoffRisk',
        question: 'Have you taken any concrete steps in the past 6 months to reduce your layoff risk?',
        type: 'multiple',
        required: true,
        options: [
          'Updated my resume',
          'Expanded my professional network',
          'Learned a new in-demand skill',
          'Had a direct conversation with my manager',
          'Built visibility with leadership',
          'No, I haven\'t done any of these'
        ]
      },
      {
        id: 'incomeExpensesThreeMonths',
        question: 'How would your income and expenses hold up if you went 3 months without a paycheck?',
        type: 'single',
        required: true,
        options: [
          'I\'d be fine - I have savings',
          'I\'d manage but it would be tight',
          'I\'d struggle significantly',
          'I\'d be in serious financial trouble within weeks',
          'I haven\'t thought about it'
        ]
      },
      {
        id: 'leadershipCommunicateFinancialPressure',
        question: 'When your company faces financial pressure, does leadership communicate clearly with employees?',
        type: 'single',
        required: true,
        options: [
          'Yes, very transparently',
          'Generally yes',
          'It\'s inconsistent',
          'Rarely',
          'Never - we\'re usually the last to know'
        ]
      },
      {
        id: 'roleMentionedInRestructuring',
        question: 'How often has your role, budget, or headcount been mentioned in restructuring conversations?',
        type: 'single',
        required: true,
        options: [
          'Frequently',
          'A few times',
          'Once',
          'Never that I know of',
          'I wouldn\'t be told'
        ]
      },
      {
        id: 'jobSearchDurationIfLaidOff',
        question: 'If you were laid off today, how long would your job search realistically take - not how long you hope it would take?',
        type: 'single',
        required: true,
        options: [
          'Less than a month',
          '1-3 months',
          '3-6 months',
          '6-12 months',
          'More than a year'
        ]
      }
    ]
  },
  'vehicle-financial-health': {
    id: 'vehicle-financial-health',
    title: 'Vehicle Financial Health Assessment',
    description: 'Evaluate your vehicle-related financial wellness and planning',
    estimatedTime: '5-6 minutes',
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
        id: 'researchTotalCostOfOwnership',
        question: 'When you bought or leased your current vehicle, did you research total cost of ownership (insurance, gas, maintenance) before deciding?',
        type: 'single',
        required: true,
        options: [
          'Yes, thoroughly',
          'Yes, but only partially',
          'I mainly focused on the monthly payment',
          'No, I didn\'t think about it that way',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'twoThousandRepairTomorrow',
        question: 'If your vehicle needed a $2,000 repair tomorrow, what would you do?',
        type: 'single',
        required: true,
        options: [
          'Pay cash from savings',
          'Put it on a credit card',
          'Finance it somehow',
          'I\'d have to delay the repair',
          'I\'m not sure',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'unexpectedRepairsPastYear',
        question: 'How much has your vehicle cost you in unexpected repairs over the past 12 months?',
        type: 'single',
        required: true,
        options: [
          'Nothing',
          'Under $500',
          '$500-$1,500',
          '$1,500-$3,000',
          'Over $3,000',
          'I don\'t track this',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'expenseMostUnderestimate',
        question: 'Which vehicle expense do you most frequently underestimate or forget to account for?',
        type: 'single',
        required: true,
        options: [
          'Insurance',
          'Fuel',
          'Routine maintenance',
          'Unexpected repairs',
          'Depreciation',
          'Registration and taxes',
          'I account for all of them',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'vehicleFinancialOrLifestyle',
        question: 'Be honest: is your current vehicle a financial decision, a lifestyle/status decision, or both?',
        type: 'single',
        required: true,
        options: [
          'Purely financial - it gets me where I need to go',
          'Mostly financial with some preference',
          'An equal mix of both',
          'Mostly about image or lifestyle',
          'Primarily about image or lifestyle',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'stayedLongerThanShouldHave',
        question: 'Have you ever stayed in a vehicle longer than you should have because repairs felt cheaper than a new payment - only to spend more in the end?',
        type: 'single',
        required: true,
        options: [
          'Yes, that\'s happened to me',
          'Possibly, I\'m not sure',
          'No, I\'ve always made good calls',
          'Not applicable',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'breakdownAffectIncome',
        question: 'If your vehicle broke down permanently tomorrow, how would it affect your ability to earn income?',
        type: 'single',
        required: true,
        options: [
          'I\'d lose my job or income immediately',
          'It would significantly disrupt my work',
          'Moderate disruption',
          'Minimal impact',
          'No impact - I work remotely or have other options',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'marketValueAndUnderwater',
        question: 'Do you know the current market value of your vehicle and whether you owe more than it\'s worth?',
        type: 'single',
        required: true,
        options: [
          'Yes, I know both and I\'m in good shape',
          'Yes, and I owe more than it\'s worth (underwater)',
          'I have a general idea',
          'No, I haven\'t looked',
          'I don\'t own a vehicle'
        ]
      },
      {
        id: 'betterVehicleDecisionNextTime',
        question: 'What would it take for you to make a fundamentally better vehicle financial decision next time?',
        type: 'single',
        required: true,
        options: [
          'A clear budget before I shop',
          'Knowledge of total cost, not just payments',
          'Less pressure from salespeople or circumstances',
          'More emergency savings going in',
          'A plan for my current vehicle before buying',
          'I\'m already making good decisions',
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

      const calculatedResults = calculateAssessmentScore(config.id as import('../utils/assessmentScoring').AssessmentType, assessmentData.answers);

      const response = await fetch('/api/assessments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          ...assessmentData,
          calculatedResults: {
            score: calculatedResults.score,
            risk_level: calculatedResults.risk_level,
            recommendations: calculatedResults.recommendations,
            subscores: calculatedResults.subscores
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to submit assessment: ${response.statusText}`);
      }

      const apiResponse = await response.json();
      
      // Get assessment_id from response
      const assessmentId = apiResponse.assessment_id || parseInt(response.headers.get('X-Assessment-ID') || '0');
      
      const scored = calculatedResults;
      const results = apiResponse.results || {
        ...scored,
        assessment_type: assessmentData.assessmentType,
        completed_at: assessmentData.completedAt,
        subscores: scored.subscores,
        percentile: Math.min(95, Math.max(5, scored.score + Math.floor(Math.random() * 20) - 10)),
        benchmark: {
          average: Math.max(0, scored.score - 12),
          high: Math.min(100, scored.score + 18),
          low: Math.max(0, scored.score - 28)
        }
      };
      
      // Add assessment_id to results
      const resultWithId = {
        ...results,
        assessment_id: assessmentId,
        assessment_type: assessmentData.assessmentType,
        completed_at: assessmentData.completedAt
      };
      
      setAssessmentResult(resultWithId);
      setShowResults(true);
      
      // Still call onSubmit for data collection (parent component may need it)
      onSubmit(assessmentData);
      
      // Show email confirmation
      if (apiResponse.email_sent) {
        console.log('📧 Results email sent to:', assessmentData.email);
      }
    } catch (err) {
      setError('Failed to submit assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [config, answers, onSubmit, onClose]);

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
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      } ${className}`}
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        ref={modalRef}
        className={`bg-gray-800 rounded-lg w-full max-w-lg h-[85vh] sm:h-auto sm:max-h-[90vh] flex flex-col shadow-2xl transition-all duration-300 ${
          isVisible ? 'scale-100' : 'scale-95'
        }`}
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        {/* Header - fixed at top */}
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-4 sm:p-6 text-white flex-shrink-0 border-b border-violet-500">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="text-violet-200">
                {config.icon}
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-bold">{config.title}</h2>
                <p className="text-violet-100 text-xs sm:text-sm">{config.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-violet-200 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-violet-600 rounded p-1"
              aria-label="Close assessment"
            >
              <X className="w-5 h-5 sm:w-6 sm:h-6" />
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
            <p className="text-violet-100 text-xs sm:text-sm font-medium">
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

        {/* Scrollable content area */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-1">
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

        {/* Footer with buttons - ALWAYS visible */}
        <div className="p-4 sm:px-6 sm:py-4 border-t border-gray-700 flex-shrink-0 bg-gray-800 flex items-center justify-between">
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
