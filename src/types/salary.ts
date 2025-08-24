export interface SalaryData {
  userSalary: number;
  peerAverage: number;
  peerMedian: number;
  peer75thPercentile: number;
  peer25thPercentile: number;
  confidenceInterval: {
    lower: number;
    upper: number;
  };
  sampleSize: number;
  msa: string;
  industry: string;
  experienceLevel: string;
  educationLevel: string;
}

export interface CareerPath {
  currentSalary: number;
  targetSalary: number;
  yearsToTarget: number;
  steps: CareerStep[];
  totalInvestment: number;
  roi: number;
}

export interface CareerStep {
  id: string;
  title: string;
  description: string;
  cost: number;
  duration: number; // in months
  salaryIncrease: number;
  type: 'education' | 'certification' | 'skill' | 'relocation' | 'networking';
  priority: 'high' | 'medium' | 'low';
}

export interface CulturalContext {
  representationPremium: number;
  salaryGap: number;
  systemicBarriers: string[];
  diverseLeadershipBonus: number;
  communityWealthBuilding: {
    mentorshipOpportunities: number;
    networkingGroups: number;
    investmentOpportunities: number;
  };
}

export interface SalaryBenchmarkFilters {
  msa: string;
  industry: string;
  experienceLevel: string;
  educationLevel: string;
  companySize: string;
  role: string;
}

export interface CareerSimulatorParams {
  currentEducation: string;
  targetEducation: string;
  currentSkills: string[];
  targetSkills: string[];
  currentLocation: string;
  targetLocation: string;
  yearsOfExperience: number;
  targetYearsOfExperience: number;
  networkingScore: number;
  targetNetworkingScore: number;
} 