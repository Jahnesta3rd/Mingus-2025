import React, { useState, useEffect } from 'react';
import BasicInfoStep from './BasicInfoStep';
import DetailedProfileStep from './DetailedProfileStep';
import ReportGenerationStep from './ReportGenerationStep';
import ProgressIndicator from './ProgressIndicator';
import GamificationPanel from './GamificationPanel';
import { 
  BasicLeadInfo, 
  DetailedProfile, 
  LeadCaptureProgress, 
  GamificationBadge, 
  CareerMilestone,
  PersonalizedReport 
} from '../../types/leadCapture';

interface AdvancedLeadCaptureProps {
  onComplete?: (report: PersonalizedReport) => void;
  onStepChange?: (step: number) => void;
  className?: string;
}

const AdvancedLeadCapture: React.FC<AdvancedLeadCaptureProps> = ({
  onComplete,
  onStepChange,
  className = ''
}) => {
  const [basicInfo, setBasicInfo] = useState<Partial<BasicLeadInfo>>({});
  const [detailedProfile, setDetailedProfile] = useState<Partial<DetailedProfile>>({});
  const [currentStep, setCurrentStep] = useState(1);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [report, setReport] = useState<PersonalizedReport | null>(null);
  const [badges, setBadges] = useState<GamificationBadge[]>([]);
  const [milestones, setMilestones] = useState<CareerMilestone[]>([]);

  const totalSteps = 3;

  // Initialize gamification elements
  useEffect(() => {
    initializeGamification();
  }, []);

  const initializeGamification = () => {
    const initialBadges: GamificationBadge[] = [
      {
        id: 'first-step',
        name: 'Getting Started',
        description: 'Completed your first step',
        icon: '🚀',
        color: 'bg-blue-500',
        unlocked: false,
        criteria: 'Complete basic information'
      },
      {
        id: 'salary-insight',
        name: 'Salary Insight',
        description: 'Unlocked detailed salary analysis',
        icon: '💰',
        color: 'bg-green-500',
        unlocked: false,
        criteria: 'Complete detailed profile'
      },
      {
        id: 'career-planner',
        name: 'Career Planner',
        description: 'Generated personalized career plan',
        icon: '📈',
        color: 'bg-purple-500',
        unlocked: false,
        criteria: 'Generate personalized report'
      },
      {
        id: 'market-expert',
        name: 'Market Expert',
        description: 'Top 10% salary in your field',
        icon: '🏆',
        color: 'bg-yellow-500',
        unlocked: false,
        criteria: 'Achieve top 10% salary percentile'
      }
    ];

    const initialMilestones: CareerMilestone[] = [
      {
        id: 'profile-completion',
        name: 'Profile Completion',
        description: 'Complete your detailed profile',
        progress: 0,
        target: 100,
        unit: '%',
        icon: '📋',
        color: 'bg-blue-500',
        completed: false
      },
      {
        id: 'salary-goal',
        name: 'Salary Goal Setting',
        description: 'Set your target salary',
        progress: 0,
        target: 1,
        unit: 'goal',
        icon: '🎯',
        color: 'bg-green-500',
        completed: false
      },
      {
        id: 'skill-development',
        name: 'Skill Development',
        description: 'Identify key skills to develop',
        progress: 0,
        target: 5,
        unit: 'skills',
        icon: '🛠️',
        color: 'bg-purple-500',
        completed: false
      }
    ];

    setBadges(initialBadges);
    setMilestones(initialMilestones);
  };

  const updateProgress = (step: number) => {
    const progressPercentage = (step / totalSteps) * 100;
    
    // Update milestones based on progress
    setMilestones(prev => prev.map(milestone => {
      if (milestone.id === 'profile-completion') {
        const newProgress = Math.min(100, progressPercentage);
        return {
          ...milestone,
          progress: newProgress,
          completed: newProgress >= 100
        };
      }
      return milestone;
    }));

    // Check for badge unlocks
    checkBadgeUnlocks(step);
  };

  const checkBadgeUnlocks = (step: number) => {
    setBadges(prev => prev.map(badge => {
      let shouldUnlock = false;

      switch (badge.id) {
        case 'first-step':
          shouldUnlock = step >= 1 && !badge.unlocked;
          break;
        case 'salary-insight':
          shouldUnlock = step >= 2 && !badge.unlocked;
          break;
        case 'career-planner':
          shouldUnlock = step >= 3 && !badge.unlocked;
          break;
        case 'market-expert':
          // Check if user is in top 10% based on salary data
          shouldUnlock = basicInfo.currentSalary && basicInfo.currentSalary > 120000 && !badge.unlocked;
          break;
      }

      if (shouldUnlock) {
        return {
          ...badge,
          unlocked: true,
          unlockedAt: new Date()
        };
      }

      return badge;
    }));
  };

  const handleBasicInfoComplete = (info: BasicLeadInfo) => {
    setBasicInfo(info);
    setCurrentStep(2);
    updateProgress(2);
    onStepChange?.(2);
  };

  const handleDetailedProfileComplete = (profile: DetailedProfile) => {
    setDetailedProfile(profile);
    setCurrentStep(3);
    updateProgress(3);
    onStepChange?.(3);
  };

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    
    try {
      // Simulate report generation
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const generatedReport: PersonalizedReport = {
        id: `report-${Date.now()}`,
        generatedAt: new Date(),
        basicInfo: basicInfo as BasicLeadInfo,
        detailedProfile: detailedProfile as DetailedProfile,
        salaryProjections: generateSalaryProjections(detailedProfile as DetailedProfile),
        skillRecommendations: generateSkillRecommendations(detailedProfile as DetailedProfile),
        careerPathRecommendations: generateCareerPathRecommendations(detailedProfile as DetailedProfile),
        marketInsights: generateMarketInsights(detailedProfile as DetailedProfile),
        mingusPlatformPreview: generateMingusPreview()
      };

      setReport(generatedReport);
      onComplete?.(generatedReport);
      
      // Unlock final badge
      checkBadgeUnlocks(3);
      
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const generateSalaryProjections = (profile: DetailedProfile) => {
    const baseSalary = profile.targetSalary || 75000;
    const projections = [];
    
    for (let year = 1; year <= 5; year++) {
      const growthRate = 0.05 + (year * 0.02); // 5% base + 2% per year
      const projectedSalary = Math.round(baseSalary * Math.pow(1 + growthRate, year));
      
      projections.push({
        year,
        projectedSalary,
        growthRate: growthRate * 100,
        factors: ['Experience growth', 'Skill development', 'Market demand'],
        confidence: Math.max(0.7, 1 - (year * 0.05))
      });
    }
    
    return projections;
  };

  const generateSkillRecommendations = (profile: DetailedProfile) => {
    const skills = profile.skills || [];
    const recommendations = [
      {
        skill: 'Leadership',
        category: 'Management',
        priority: 'high' as const,
        impact: 15000,
        learningPath: 'Management training programs',
        estimatedTime: '6-12 months',
        cost: 5000
      },
      {
        skill: 'Data Analysis',
        category: 'Technical',
        priority: 'medium' as const,
        impact: 8000,
        learningPath: 'Online courses and certifications',
        estimatedTime: '3-6 months',
        cost: 2000
      },
      {
        skill: 'Strategic Planning',
        category: 'Business',
        priority: 'high' as const,
        impact: 12000,
        learningPath: 'MBA or executive education',
        estimatedTime: '12-24 months',
        cost: 45000
      }
    ];

    return recommendations.filter(rec => !skills.includes(rec.skill));
  };

  const generateCareerPathRecommendations = (profile: DetailedProfile) => {
    return [
      {
        title: 'Senior Leadership Track',
        description: 'Advance to executive positions with strategic leadership skills',
        timeline: 3,
        investment: 60000,
        projectedReturn: 150000,
        steps: [
          {
            order: 1,
            title: 'Complete MBA',
            description: 'Earn advanced business degree',
            duration: '2 years',
            cost: 45000,
            impact: 30000
          },
          {
            order: 2,
            title: 'Leadership Training',
            description: 'Develop executive leadership skills',
            duration: '6 months',
            cost: 15000,
            impact: 20000
          }
        ],
        risk: 'medium' as const
      }
    ];
  };

  const generateMarketInsights = (profile: DetailedProfile) => {
    return [
      {
        category: 'Industry Trends',
        title: 'Technology Sector Growth',
        description: 'Your industry is experiencing 15% annual growth',
        data: { growthRate: 15, demand: 'high' },
        source: 'Bureau of Labor Statistics',
        relevance: 0.9
      },
      {
        category: 'Salary Trends',
        title: 'Competitive Compensation',
        description: 'Top performers in your field earn 40% more than average',
        data: { premium: 40, percentile: 90 },
        source: 'Salary.com',
        relevance: 0.8
      }
    ];
  };

  const generateMingusPreview = () => {
    return {
      features: [
        'Advanced salary benchmarking',
        'Personalized career coaching',
        'Skill gap analysis',
        'Market trend insights',
        'Networking opportunities'
      ],
      benefits: [
        'Increase your salary by 25% on average',
        'Access to exclusive career resources',
        'Direct mentorship from industry leaders',
        'Real-time market data and insights'
      ],
      pricing: [
        {
          name: 'Basic',
          price: 29,
          period: 'month',
          features: ['Basic salary insights', 'Career path planning', 'Email support']
        },
        {
          name: 'Professional',
          price: 79,
          period: 'month',
          features: ['Advanced analytics', 'Personal coaching', 'Priority support'],
          popular: true
        },
        {
          name: 'Executive',
          price: 199,
          period: 'month',
          features: ['Executive coaching', 'Custom reports', 'Dedicated support']
        }
      ],
      testimonials: [
        {
          name: 'Sarah Johnson',
          role: 'Senior Manager',
          company: 'Tech Corp',
          content: 'Mingus helped me negotiate a 30% salary increase!',
          rating: 5
        }
      ],
      ctaText: 'Start Your Free Trial',
      ctaUrl: '/signup'
    };
  };

  const getProgressPercentage = () => {
    return (currentStep / totalSteps) * 100;
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Progress Indicator */}
      <ProgressIndicator 
        currentStep={currentStep}
        totalSteps={totalSteps}
        progressPercentage={getProgressPercentage()}
      />

      {/* Gamification Panel */}
      <div className="mb-6">
        <GamificationPanel 
          badges={badges}
          milestones={milestones}
          currentStep={currentStep}
        />
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        {currentStep === 1 && (
          <BasicInfoStep 
            onComplete={handleBasicInfoComplete}
            initialData={basicInfo}
          />
        )}

        {currentStep === 2 && (
          <DetailedProfileStep 
            onComplete={handleDetailedProfileComplete}
            onBack={() => {
              setCurrentStep(1);
              updateProgress(1);
              onStepChange?.(1);
            }}
            initialData={detailedProfile}
            basicInfo={basicInfo as BasicLeadInfo}
          />
        )}

        {currentStep === 3 && (
          <ReportGenerationStep 
            onGenerateReport={handleGenerateReport}
            onBack={() => {
              setCurrentStep(2);
              updateProgress(2);
              onStepChange?.(2);
            }}
            isGenerating={isGeneratingReport}
            report={report}
            basicInfo={basicInfo as BasicLeadInfo}
            detailedProfile={detailedProfile as DetailedProfile}
          />
        )}
      </div>
    </div>
  );
};

export default AdvancedLeadCapture; 