export interface JobInformation {
  title: string;
  industry: string;
  experience: number;
}

export interface DailyTasks {
  dataEntry: boolean;
  customerService: boolean;
  contentCreation: boolean;
  analysis: boolean;
  coding: boolean;
  design: boolean;
  management: boolean;
  research: boolean;
}

export interface WorkEnvironment {
  remoteWork: 'full' | 'hybrid' | 'none';
  aiUsage: 'extensive' | 'moderate' | 'minimal' | 'none';
  teamSize: 'solo' | 'small' | 'medium' | 'large';
}

export interface SkillsAndConcerns {
  techSkills: string[];
  aiConcerns: {
    jobLoss: boolean;
    skillGap: boolean;
    privacy: boolean;
    bias: boolean;
    overreliance: boolean;
  };
}

export interface ContactInfo {
  name: string;
  email: string;
  location: string;
}

export interface AICalculatorFormData {
  jobInfo: JobInformation;
  dailyTasks: DailyTasks;
  workEnvironment: WorkEnvironment;
  skillsAndConcerns: SkillsAndConcerns;
  contactInfo: ContactInfo;
}

export interface AIRiskScore {
  overallRisk: number; // 0-100
  automationRisk: number; // 0-100
  augmentationPotential: number; // 0-100
  timeframe: 'immediate' | 'short-term' | 'medium-term' | 'long-term';
  confidence: number; // 0-100
}

export interface AIRecommendation {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  category: 'skill' | 'career' | 'mindset' | 'action';
  estimatedImpact: number; // 0-100
  timeframe: string;
  cost?: number;
}

export interface AICalculatorResults {
  riskScore: AIRiskScore;
  recommendations: AIRecommendation[];
  insights: string[];
  nextSteps: string[];
}

export interface AICalculatorState {
  currentStep: number;
  totalSteps: number;
  formData: Partial<AICalculatorFormData>;
  isSubmitting: boolean;
  results?: AICalculatorResults;
  error?: string;
  isModalOpen: boolean;
}

export interface AICalculatorTriggerProps {
  variant?: 'primary' | 'secondary' | 'floating';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children?: React.ReactNode;
  onClick?: () => void;
}

export interface AICalculatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (results: AICalculatorResults) => void;
}

export interface AIResultsDisplayProps {
  results: AICalculatorResults;
  onUpgrade?: () => void;
  onShare?: () => void;
  countdownMinutes?: number;
}

export interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
  className?: string;
}

export interface FormStepProps {
  formData: Partial<AICalculatorFormData>;
  onUpdate: (data: Partial<AICalculatorFormData>) => void;
  onNext: () => void;
  onBack: () => void;
  currentStep: number;
  totalSteps: number;
  errors?: Record<string, string>;
}
