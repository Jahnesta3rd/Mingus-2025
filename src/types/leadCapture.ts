export interface BasicLeadInfo {
  email: string;
  currentSalary: number;
  location: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
}

export interface DetailedProfile {
  industry: string;
  education: string;
  yearsOfExperience: number;
  careerGoals: string[];
  targetSalary: number;
  preferredLocation: string;
  skills: string[];
  companySize: string;
  role: string;
}

export interface LeadCaptureProgress {
  basicInfoCompleted: boolean;
  detailedProfileCompleted: boolean;
  reportGenerated: boolean;
  currentStep: 'basic' | 'detailed' | 'report';
  progressPercentage: number;
}

export interface GamificationBadge {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  unlocked: boolean;
  unlockedAt?: Date;
  criteria: string;
}

export interface CareerMilestone {
  id: string;
  name: string;
  description: string;
  progress: number;
  target: number;
  unit: string;
  icon: string;
  color: string;
  completed: boolean;
  completedAt?: Date;
}

export interface PersonalizedReport {
  id: string;
  generatedAt: Date;
  basicInfo: BasicLeadInfo;
  detailedProfile: DetailedProfile;
  salaryProjections: SalaryProjection[];
  skillRecommendations: SkillRecommendation[];
  careerPathRecommendations: CareerPathRecommendation[];
  marketInsights: MarketInsight[];
  mingusPlatformPreview: MingusPreview;
}

export interface SalaryProjection {
  year: number;
  projectedSalary: number;
  growthRate: number;
  factors: string[];
  confidence: number;
}

export interface SkillRecommendation {
  skill: string;
  category: string;
  priority: 'high' | 'medium' | 'low';
  impact: number;
  learningPath: string;
  estimatedTime: string;
  cost: number;
}

export interface CareerPathRecommendation {
  title: string;
  description: string;
  timeline: number;
  investment: number;
  projectedReturn: number;
  steps: CareerStep[];
  risk: 'low' | 'medium' | 'high';
}

export interface CareerStep {
  order: number;
  title: string;
  description: string;
  duration: string;
  cost: number;
  impact: number;
}

export interface MarketInsight {
  category: string;
  title: string;
  description: string;
  data: any;
  source: string;
  relevance: number;
}

export interface MingusPreview {
  features: string[];
  benefits: string[];
  pricing: PricingTier[];
  testimonials: Testimonial[];
  ctaText: string;
  ctaUrl: string;
}

export interface PricingTier {
  name: string;
  price: number;
  period: string;
  features: string[];
  popular?: boolean;
}

export interface Testimonial {
  name: string;
  role: string;
  company: string;
  content: string;
  avatar?: string;
  rating: number;
}

export interface LeadCaptureState {
  basicInfo: Partial<BasicLeadInfo>;
  detailedProfile: Partial<DetailedProfile>;
  progress: LeadCaptureProgress;
  badges: GamificationBadge[];
  milestones: CareerMilestone[];
  report?: PersonalizedReport;
  isGeneratingReport: boolean;
  currentStep: number;
  totalSteps: number;
} 