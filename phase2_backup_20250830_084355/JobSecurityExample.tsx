import React, { useState } from 'react';
import JobSecurityAnalysis from './JobSecurityAnalysis';
import JobSecurityDrillDown from './JobSecurityDrillDown';

// Sample data for demonstration
const sampleJobSecurityData = {
  overall_score: 72,
  user_perception_score: 75,
  external_data_score: 68,
  confidence_level: 85,
  risk_factors: [
    {
      category: 'Local Layoffs',
      severity: 'medium' as const,
      description: 'Recent layoffs in your industry within 25 miles',
      impact_score: 15
    },
    {
      category: 'Company Financials',
      severity: 'low' as const,
      description: 'Declining revenue trend in recent quarters',
      impact_score: 8
    },
    {
      category: 'Industry Volatility',
      severity: 'medium' as const,
      description: 'Technology sector showing increased volatility',
      impact_score: 12
    }
  ],
  positive_indicators: [
    'Strong company cash position',
    'Growing industry demand',
    'Your role is critical to operations',
    'Recent positive performance reviews'
  ],
  recommendations: [
    {
      priority: 'medium' as const,
      category: 'Career Development',
      title: 'Enhance Your Market Position',
      description: 'Strengthen your skills and network to improve job security',
      action_items: [
        'Update your professional certifications',
        'Expand your professional network',
        'Document your key achievements and contributions'
      ]
    },
    {
      priority: 'low' as const,
      category: 'Financial Planning',
      title: 'Build Emergency Savings',
      description: 'Ensure you have adequate savings for unexpected job changes',
      action_items: [
        'Aim for 6-12 months of expenses in emergency fund',
        'Review and update your budget',
        'Consider additional income streams'
      ]
    }
  ],
  trend_data: [
    { date: '2024-01-15', score: 68, change: 2 },
    { date: '2024-01-22', score: 70, change: 2 },
    { date: '2024-01-29', score: 72, change: 2 },
    { date: '2024-02-05', score: 71, change: -1 },
    { date: '2024-02-12', score: 72, change: 1 }
  ],
  last_updated: '2024-02-12T10:30:00Z',
  employer_name: 'TechCorp Solutions',
  industry_sector: 'Technology',
  location: 'Atlanta, GA'
};

// Sample drill-down data
const sampleDrillDownData = {
  user_perception: {
    component: 'user_perception' as const,
    details: {
      factors: [
        {
          name: 'Job Security Feeling',
          value: 8,
          weight: 40,
          trend: 'up' as const,
          description: 'Your confidence in job stability has increased'
        },
        {
          name: 'Workplace Stress',
          value: 6,
          weight: 30,
          trend: 'stable' as const,
          description: 'Stress levels remain manageable'
        },
        {
          name: 'Management Support',
          value: 7,
          weight: 20,
          trend: 'up' as const,
          description: 'Positive relationship with management'
        },
        {
          name: 'Career Growth',
          value: 8,
          weight: 10,
          trend: 'up' as const,
          description: 'Clear advancement opportunities available'
        }
      ],
      trends: [
        { period: 'This Week', value: 75, change: 2, significance: 'low' as const },
        { period: 'Last Week', value: 73, change: 1, significance: 'low' as const },
        { period: '2 Weeks Ago', value: 72, change: -1, significance: 'low' as const }
      ],
      insights: [
        'Your job security perception has improved by 15% over the past month',
        'Management relationship is a key positive factor',
        'Stress levels are well-managed and not impacting security'
      ],
      recommendations: [
        'Continue building relationships with key decision makers',
        'Document your contributions and achievements regularly',
        'Stay engaged with professional development opportunities'
      ]
    }
  },
  external_data: {
    component: 'external_data' as const,
    details: {
      factors: [
        {
          name: 'Local Unemployment',
          value: 3.2,
          weight: 25,
          trend: 'down' as const,
          description: 'Local unemployment rate is below national average'
        },
        {
          name: 'Industry Growth',
          value: 4.8,
          weight: 30,
          trend: 'up' as const,
          description: 'Technology sector showing strong growth'
        },
        {
          name: 'Company Financial Health',
          value: 65,
          weight: 35,
          trend: 'stable' as const,
          description: 'Company maintains solid financial position'
        },
        {
          name: 'Local Layoff Activity',
          value: 12,
          weight: 10,
          trend: 'up' as const,
          description: 'Recent layoffs in similar companies'
        }
      ],
      trends: [
        { period: 'This Week', value: 68, change: 1, significance: 'low' as const },
        { period: 'Last Week', value: 67, change: -2, significance: 'medium' as const },
        { period: '2 Weeks Ago', value: 69, change: 3, significance: 'low' as const }
      ],
      insights: [
        'Local market conditions are favorable for job security',
        'Industry growth provides stability despite some layoffs',
        'Company financials support continued employment'
      ],
      recommendations: [
        'Monitor local job market trends regularly',
        'Stay informed about industry developments',
        'Build relationships within your professional network'
      ]
    }
  }
};

const JobSecurityExample: React.FC = () => {
  const [showDrillDown, setShowDrillDown] = useState(false);
  const [drillDownData, setDrillDownData] = useState<any>(null);

  const handleDrillDown = (component: string) => {
    setDrillDownData(sampleDrillDownData[component as keyof typeof sampleDrillDownData]);
    setShowDrillDown(true);
  };

  const handleCloseDrillDown = () => {
    setShowDrillDown(false);
    setDrillDownData(null);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2" className="text-4xl font-bold text-gray-900 mb-6">Job Security Analysis</h1>
        <p className="text-gray-600">
          Comprehensive analysis of your job security based on personal perceptions and external market data.
        </p>
      </div>

      <JobSecurityAnalysis
        data={sampleJobSecurityData}
        onDrillDown={handleDrillDown}
        className="mb-8"
      />

      {showDrillDown && drillDownData && (
        <JobSecurityDrillDown
          data={drillDownData}
          onClose={handleCloseDrillDown}
        />
      )}

      {/* Integration Notes */}
      <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-3" className="text-xl font-semibold text-gray-800 mb-3">Integration Notes</h3>
        <div className="space-y-2 text-base leading-relaxed text-blue-800">
          <p>• This component integrates seamlessly with your existing health dashboard</p>
          <p>• Uses the same design patterns and color schemes as other Mingus components</p>
          <p>• Mobile-responsive and accessible</p>
          <p>• Supports real-time data updates from your job security scoring system</p>
          <p>• Includes drill-down functionality for detailed analysis</p>
        </div>
      </div>
    </div>
  );
};

export default JobSecurityExample; 