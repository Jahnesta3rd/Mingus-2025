import create from 'zustand';
import { 
  AICalculatorState, 
  AICalculatorFormData, 
  AICalculatorResults,
  AIRiskScore,
  AIRecommendation 
} from '../types/aiCalculator';

interface AICalculatorStore extends AICalculatorState {
  // Actions
  openModal: () => void;
  closeModal: () => void;
  setCurrentStep: (step: number) => void;
  updateFormData: (data: Partial<AICalculatorFormData>) => void;
  validateStep: (step: number) => Record<string, string>;
  submitForm: () => Promise<void>;
  resetForm: () => void;
  setResults: (results: AICalculatorResults) => void;
  setError: (error: string) => void;
  clearError: () => void;
}

const initialFormData: Partial<AICalculatorFormData> = {
  jobInfo: {
    title: '',
    industry: '',
    experience: 0
  },
  dailyTasks: {
    dataEntry: false,
    customerService: false,
    contentCreation: false,
    analysis: false,
    coding: false,
    design: false,
    management: false,
    research: false
  },
  workEnvironment: {
    remoteWork: 'none',
    aiUsage: 'none',
    teamSize: 'small'
  },
  skillsAndConcerns: {
    techSkills: [],
    aiConcerns: {
      jobLoss: false,
      skillGap: false,
      privacy: false,
      bias: false,
      overreliance: false
    }
  },
  contactInfo: {
    name: '',
    email: '',
    location: ''
  }
};

export const useAICalculatorStore = create<AICalculatorStore>((set, get) => ({
  // Initial state
  currentStep: 1,
  totalSteps: 5,
  formData: initialFormData,
  isSubmitting: false,
  isModalOpen: false,
  results: undefined,
  error: undefined,

  // Actions
  openModal: () => set({ isModalOpen: true, currentStep: 1, error: undefined }),
  
  closeModal: () => set({ 
    isModalOpen: false, 
    currentStep: 1, 
    error: undefined,
    results: undefined 
  }),

  setCurrentStep: (step: number) => {
    const { totalSteps } = get();
    if (step >= 1 && step <= totalSteps) {
      set({ currentStep: step, error: undefined });
    }
  },

  updateFormData: (data: Partial<AICalculatorFormData>) => {
    set((state) => ({
      formData: { ...state.formData, ...data }
    }));
  },

  validateStep: (step: number): Record<string, string> => {
    const { formData } = get();
    const errors: Record<string, string> = {};

    switch (step) {
      case 1: // Job Information
        if (!formData.jobInfo?.title?.trim()) {
          errors.jobTitle = 'Job title is required';
        }
        if (!formData.jobInfo?.industry?.trim()) {
          errors.industry = 'Industry is required';
        }
        if (!formData.jobInfo?.experience || formData.jobInfo.experience < 0) {
          errors.experience = 'Valid experience is required';
        }
        break;

      case 2: // Daily Tasks
        const hasTasks = Object.values(formData.dailyTasks || {}).some(Boolean);
        if (!hasTasks) {
          errors.dailyTasks = 'Please select at least one daily task';
        }
        break;

      case 3: // Work Environment
        if (!formData.workEnvironment?.remoteWork) {
          errors.remoteWork = 'Please select remote work preference';
        }
        if (!formData.workEnvironment?.aiUsage) {
          errors.aiUsage = 'Please select AI usage level';
        }
        if (!formData.workEnvironment?.teamSize) {
          errors.teamSize = 'Please select team size';
        }
        break;

      case 4: // Skills & Concerns
        if (!formData.skillsAndConcerns?.techSkills?.length) {
          errors.techSkills = 'Please select at least one tech skill';
        }
        break;

      case 5: // Contact Info
        if (!formData.contactInfo?.name?.trim()) {
          errors.name = 'Name is required';
        }
        if (!formData.contactInfo?.email?.trim()) {
          errors.email = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contactInfo.email)) {
          errors.email = 'Please enter a valid email address';
        }
        if (!formData.contactInfo?.location?.trim()) {
          errors.location = 'Location is required';
        }
        break;
    }

    return errors;
  },

  submitForm: async () => {
    const { formData, validateStep } = get();
    
    set({ isSubmitting: true, error: undefined });

    try {
      // Validate all steps
      for (let step = 1; step <= 5; step++) {
        const errors = validateStep(step);
        if (Object.keys(errors).length > 0) {
          throw new Error('Please complete all required fields');
        }
      }

      // Simulate API call to calculate AI impact
      const results = await calculateAIImpact(formData as AICalculatorFormData);
      
      set({ 
        results, 
        isSubmitting: false,
        currentStep: 6 // Show results
      });

    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'An error occurred',
        isSubmitting: false 
      });
    }
  },

  resetForm: () => {
    set({
      currentStep: 1,
      formData: initialFormData,
      results: undefined,
      error: undefined,
      isSubmitting: false
    });
  },

  setResults: (results: AICalculatorResults) => {
    set({ results });
  },

  setError: (error: string) => {
    set({ error });
  },

  clearError: () => {
    set({ error: undefined });
  }
}));

// Mock AI impact calculation function
async function calculateAIImpact(formData: AICalculatorFormData): Promise<AICalculatorResults> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Calculate risk scores based on form data
  const automationRisk = calculateAutomationRisk(formData);
  const augmentationPotential = calculateAugmentationPotential(formData);
  const overallRisk = Math.round((automationRisk + (100 - augmentationPotential)) / 2);

  const timeframe = getTimeframe(overallRisk);
  const confidence = Math.round(85 + Math.random() * 15); // 85-100%

  const riskScore: AIRiskScore = {
    overallRisk,
    automationRisk,
    augmentationPotential,
    timeframe,
    confidence
  };

  const recommendations: AIRecommendation[] = generateRecommendations(formData, riskScore);
  const insights = generateInsights(formData, riskScore);
  const nextSteps = generateNextSteps(formData, riskScore);

  return {
    riskScore,
    recommendations,
    insights,
    nextSteps
  };
}

function calculateAutomationRisk(formData: AICalculatorFormData): number {
  let risk = 0;
  
  // Job title analysis
  const highRiskTitles = ['data entry', 'administrative', 'receptionist', 'bookkeeper'];
  const mediumRiskTitles = ['analyst', 'researcher', 'writer', 'designer'];
  
  const title = formData.jobInfo.title.toLowerCase();
  if (highRiskTitles.some(t => title.includes(t))) risk += 30;
  else if (mediumRiskTitles.some(t => title.includes(t))) risk += 15;

  // Daily tasks analysis
  if (formData.dailyTasks.dataEntry) risk += 25;
  if (formData.dailyTasks.customerService) risk += 20;
  if (formData.dailyTasks.contentCreation) risk += 15;
  if (formData.dailyTasks.analysis) risk += 10;
  if (formData.dailyTasks.coding) risk += 5;
  if (formData.dailyTasks.management) risk -= 10;

  // AI usage analysis
  switch (formData.workEnvironment.aiUsage) {
    case 'extensive': risk += 15; break;
    case 'moderate': risk += 10; break;
    case 'minimal': risk += 5; break;
  }

  return Math.min(100, Math.max(0, risk));
}

function calculateAugmentationPotential(formData: AICalculatorFormData): number {
  let potential = 50; // Base potential
  
  // Skills analysis
  const techSkills = formData.skillsAndConcerns.techSkills.length;
  potential += techSkills * 5;

  // Experience analysis
  if (formData.jobInfo.experience > 5) potential += 15;
  else if (formData.jobInfo.experience > 2) potential += 10;

  // Team size analysis
  switch (formData.workEnvironment.teamSize) {
    case 'large': potential += 10; break;
    case 'medium': potential += 5; break;
    case 'solo': potential -= 5; break;
  }

  return Math.min(100, Math.max(0, potential));
}

function getTimeframe(risk: number): 'immediate' | 'short-term' | 'medium-term' | 'long-term' {
  if (risk >= 80) return 'immediate';
  if (risk >= 60) return 'short-term';
  if (risk >= 40) return 'medium-term';
  return 'long-term';
}

function generateRecommendations(formData: AICalculatorFormData, riskScore: AIRiskScore): AIRecommendation[] {
  const recommendations: AIRecommendation[] = [];

  if (riskScore.automationRisk > 70) {
    recommendations.push({
      id: 'upskill-critical',
      title: 'Upskill in AI-Resistant Skills',
      description: 'Focus on creative, strategic, and interpersonal skills that AI cannot easily replicate.',
      priority: 'high',
      category: 'skill',
      estimatedImpact: 85,
      timeframe: '3-6 months'
    });
  }

  if (formData.skillsAndConcerns.techSkills.length < 3) {
    recommendations.push({
      id: 'tech-literacy',
      title: 'Build Technical Literacy',
      description: 'Develop foundational understanding of AI tools and technologies relevant to your field.',
      priority: 'medium',
      category: 'skill',
      estimatedImpact: 70,
      timeframe: '2-4 months'
    });
  }

  if (riskScore.overallRisk > 50) {
    recommendations.push({
      id: 'career-pivot',
      title: 'Explore Career Pivot Opportunities',
      description: 'Research adjacent roles that leverage your experience while being less vulnerable to automation.',
      priority: 'high',
      category: 'career',
      estimatedImpact: 90,
      timeframe: '6-12 months'
    });
  }

  recommendations.push({
    id: 'mindset-shift',
    title: 'Adopt AI-Collaboration Mindset',
    description: 'Start viewing AI as a productivity tool rather than a threat to your job security.',
    priority: 'medium',
    category: 'mindset',
    estimatedImpact: 60,
    timeframe: '1-2 months'
  });

  return recommendations.slice(0, 4); // Return max 4 recommendations
}

function generateInsights(formData: AICalculatorFormData, riskScore: AIRiskScore): string[] {
  const insights: string[] = [];

  if (riskScore.automationRisk > 70) {
    insights.push('Your role has high automation potential due to repetitive tasks and structured workflows.');
  }

  if (formData.workEnvironment.aiUsage === 'extensive') {
    insights.push('Your organization is already heavily invested in AI, indicating rapid transformation ahead.');
  }

  if (formData.skillsAndConcerns.techSkills.length < 2) {
    insights.push('Limited technical skills may make it harder to adapt to AI-driven changes.');
  }

  if (riskScore.augmentationPotential > 70) {
    insights.push('Your role has strong potential for AI augmentation, which could increase your productivity significantly.');
  }

  return insights;
}

function generateNextSteps(formData: AICalculatorFormData, riskScore: AIRiskScore): string[] {
  const steps: string[] = [];

  steps.push('Complete a detailed skills assessment to identify specific gaps');
  steps.push('Research AI tools and technologies relevant to your industry');
  steps.push('Network with professionals who have successfully adapted to AI changes');
  steps.push('Consider enrolling in AI-related courses or certifications');

  return steps;
}
