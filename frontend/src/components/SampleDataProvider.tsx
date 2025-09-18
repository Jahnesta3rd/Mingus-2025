import React, { createContext, useContext } from 'react';

// Sample data for dashboard preview
export const sampleDashboardData = {
  riskAssessment: {
    currentLevel: 'action_needed',
    score: 68,
    factors: [
      { name: 'Market Volatility', impact: 'high', trend: 'increasing' },
      { name: 'Skill Relevance', impact: 'medium', trend: 'stable' },
      { name: 'Industry Stability', impact: 'high', trend: 'decreasing' },
      { name: 'Competition Level', impact: 'medium', trend: 'increasing' }
    ],
    recommendations: [
      'Consider upskilling in AI and machine learning',
      'Network with professionals in emerging tech fields',
      'Update your resume with recent achievements',
      'Explore remote work opportunities'
    ]
  },
  
  jobRecommendations: {
    safeGrowth: [
      {
        id: 1,
        title: 'Senior Software Engineer',
        company: 'TechCorp Inc.',
        location: 'San Francisco, CA',
        salary: '$120,000 - $150,000',
        match: 92,
        description: 'Stable role with growth opportunities in established company',
        benefits: ['Health Insurance', '401k Match', 'Flexible Hours'],
        urgency: 'low'
      },
      {
        id: 2,
        title: 'Product Manager',
        company: 'InnovateLabs',
        location: 'Austin, TX',
        salary: '$110,000 - $135,000',
        match: 88,
        description: 'Product management role with clear career progression',
        benefits: ['Stock Options', 'Learning Budget', 'Remote Work'],
        urgency: 'low'
      }
    ],
    strategicAdvance: [
      {
        id: 3,
        title: 'AI Solutions Architect',
        company: 'FutureTech Systems',
        location: 'Seattle, WA',
        salary: '$140,000 - $180,000',
        match: 85,
        description: 'High-growth role in AI/ML space with excellent prospects',
        benefits: ['Equity', 'Conference Budget', 'Mentorship Program'],
        urgency: 'medium'
      },
      {
        id: 4,
        title: 'Technical Lead',
        company: 'ScaleUp Ventures',
        location: 'New York, NY',
        salary: '$130,000 - $160,000',
        match: 82,
        description: 'Leadership role with technical and management growth',
        benefits: ['Performance Bonus', 'Leadership Training', 'Team Building'],
        urgency: 'medium'
      }
    ],
    ambitiousLeap: [
      {
        id: 5,
        title: 'VP of Engineering',
        company: 'StartupX',
        location: 'San Francisco, CA',
        salary: '$180,000 - $250,000',
        match: 75,
        description: 'Executive role with significant equity and growth potential',
        benefits: ['Significant Equity', 'Executive Benefits', 'Board Access'],
        urgency: 'high'
      },
      {
        id: 6,
        title: 'CTO',
        company: 'NextGen AI',
        location: 'Remote',
        salary: '$200,000 - $300,000',
        match: 70,
        description: 'C-level position in cutting-edge AI company',
        benefits: ['Major Equity Stake', 'Full Benefits', 'Creative Freedom'],
        urgency: 'high'
      }
    ]
  },
  
  locationData: [
    {
      id: 1,
      name: 'San Francisco, CA',
      average_salary: 145000,
      job_count: 2847,
      growth_rate: 8.2,
      cost_of_living: 165.2,
      tech_hub_score: 95,
      remote_friendly: 85
    },
    {
      id: 2,
      name: 'Seattle, WA',
      average_salary: 132000,
      job_count: 1923,
      growth_rate: 6.8,
      cost_of_living: 142.1,
      tech_hub_score: 88,
      remote_friendly: 78
    },
    {
      id: 3,
      name: 'Austin, TX',
      average_salary: 118000,
      job_count: 1654,
      growth_rate: 12.4,
      cost_of_living: 98.7,
      tech_hub_score: 82,
      remote_friendly: 92
    },
    {
      id: 4,
      name: 'New York, NY',
      average_salary: 138000,
      job_count: 3241,
      growth_rate: 5.2,
      cost_of_living: 187.3,
      tech_hub_score: 90,
      remote_friendly: 65
    },
    {
      id: 5,
      name: 'Denver, CO',
      average_salary: 108000,
      job_count: 987,
      growth_rate: 15.6,
      cost_of_living: 112.4,
      tech_hub_score: 75,
      remote_friendly: 88
    }
  ],
  
  analytics: {
    careerTrajectory: [
      { month: 'Jan', score: 65 },
      { month: 'Feb', score: 68 },
      { month: 'Mar', score: 72 },
      { month: 'Apr', score: 70 },
      { month: 'May', score: 75 },
      { month: 'Jun', score: 78 }
    ],
    skillDemand: [
      { skill: 'JavaScript', demand: 95, growth: 12 },
      { skill: 'Python', demand: 88, growth: 18 },
      { skill: 'React', demand: 82, growth: 15 },
      { skill: 'Node.js', demand: 78, growth: 8 },
      { skill: 'AWS', demand: 85, growth: 22 },
      { skill: 'Machine Learning', demand: 92, growth: 25 }
    ],
    marketTrends: {
      remoteWork: 78,
      salaryGrowth: 6.2,
      jobOpenings: 12450,
      competitionLevel: 72
    }
  },
  
  recentActivity: [
    {
      id: 1,
      type: 'assessment',
      title: 'Career Risk Assessment Completed',
      description: 'Completed comprehensive career risk evaluation',
      timestamp: '2024-01-15T10:30:00Z',
      status: 'completed',
      metadata: { score: 68, level: 'action_needed' }
    },
    {
      id: 2,
      type: 'recommendation',
      title: 'New Job Recommendations Available',
      description: '6 new job matches found based on your profile',
      timestamp: '2024-01-15T09:15:00Z',
      status: 'completed',
      metadata: { count: 6, tier: 'strategic_advance' }
    },
    {
      id: 3,
      type: 'profile_update',
      title: 'Profile Updated',
      description: 'Added new skills and experience to your profile',
      timestamp: '2024-01-14T16:45:00Z',
      status: 'completed',
      metadata: { skills_added: 3 }
    },
    {
      id: 4,
      type: 'risk_change',
      title: 'Risk Level Updated',
      description: 'Career risk level changed from Watchful to Action Needed',
      timestamp: '2024-01-14T14:20:00Z',
      status: 'completed',
      metadata: { previous_level: 'watchful', new_level: 'action_needed' }
    },
    {
      id: 5,
      type: 'application',
      title: 'Job Application Submitted',
      description: 'Applied for Senior Software Engineer at TechCorp Inc.',
      timestamp: '2024-01-13T11:30:00Z',
      status: 'pending',
      metadata: { company: 'TechCorp Inc.', position: 'Senior Software Engineer' }
    }
  ]
};

const SampleDataContext = createContext(sampleDashboardData);

export const useSampleData = () => {
  const context = useContext(SampleDataContext);
  if (!context) {
    throw new Error('useSampleData must be used within SampleDataProvider');
  }
  return context;
};

export const SampleDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <SampleDataContext.Provider value={sampleDashboardData}>
      {children}
    </SampleDataContext.Provider>
  );
};

