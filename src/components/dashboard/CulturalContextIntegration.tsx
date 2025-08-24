import React, { useState, useEffect } from 'react';
import { CulturalContext } from '../../types/salary';

interface CulturalContextIntegrationProps {
  userSalary?: number;
  industry?: string;
  className?: string;
}

const CulturalContextIntegration: React.FC<CulturalContextIntegrationProps> = ({
  userSalary = 75000,
  industry = 'Technology',
  className = ''
}) => {
  const [culturalData, setCulturalData] = useState<CulturalContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'gaps' | 'premium' | 'community'>('gaps');

  // Mock data - replace with actual API call
  useEffect(() => {
    const fetchCulturalData = async () => {
      setIsLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockData: CulturalContext = {
        representationPremium: 8500,
        salaryGap: 12000,
        systemicBarriers: [
          'Unconscious bias in hiring and promotion processes',
          'Limited access to high-profile projects and mentorship',
          'Network gaps in executive circles',
          'Stereotype threat affecting performance reviews',
          'Lack of representation in leadership positions'
        ],
        diverseLeadershipBonus: 15000,
        communityWealthBuilding: {
          mentorshipOpportunities: 85,
          networkingGroups: 23,
          investmentOpportunities: 12
        }
      };

      setCulturalData(mockData);
      setIsLoading(false);
    };

    fetchCulturalData();
  }, [industry]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Cultural Context & Equity Insights
        </h3>
        <p className="text-sm text-gray-600">
          Understanding systemic factors and opportunities for African American professionals
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('gaps')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'gaps'
              ? 'border-red-500 text-red-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Salary Gaps
        </button>
        <button
          onClick={() => setActiveTab('premium')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'premium'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Representation Premium
        </button>
        <button
          onClick={() => setActiveTab('community')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'community'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Community Wealth
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'gaps' && culturalData && (
        <div className="space-y-6">
          {/* Salary Gap Overview */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-red-900">Average Salary Gap</h4>
              <div className="text-2xl font-bold text-red-600">
                -{formatCurrency(culturalData.salaryGap)}
              </div>
            </div>
            <p className="text-sm text-red-700">
              African American professionals in {industry} earn on average{' '}
              {formatCurrency(culturalData.salaryGap)} less than their white counterparts
              with similar qualifications and experience.
            </p>
          </div>

          {/* Systemic Barriers */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Systemic Barriers to Address</h4>
            <div className="space-y-3">
              {culturalData.systemicBarriers.map((barrier, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <p className="text-sm text-gray-700">{barrier}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Action Items */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-3">What You Can Do</h5>
            <div className="space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                <span>Document your achievements and contributions</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                <span>Seek out mentors and sponsors in your field</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                <span>Join professional organizations and networks</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                <span>Advocate for transparent salary structures</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'premium' && culturalData && (
        <div className="space-y-6">
          {/* Representation Premium */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-green-900">Representation Premium</h4>
              <div className="text-2xl font-bold text-green-600">
                +{formatCurrency(culturalData.representationPremium)}
              </div>
            </div>
            <p className="text-sm text-green-700">
              Companies with diverse leadership teams offer on average{' '}
              {formatCurrency(culturalData.representationPremium)} more in compensation
              to African American professionals.
            </p>
          </div>

          {/* Diverse Leadership Bonus */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-blue-900">Diverse Leadership Bonus</h4>
              <div className="text-2xl font-bold text-blue-600">
                +{formatCurrency(culturalData.diverseLeadershipBonus)}
              </div>
            </div>
            <p className="text-sm text-blue-700">
              Additional compensation potential when working for companies with
              African American representation in leadership positions.
            </p>
          </div>

          {/* Company Recommendations */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Companies with Strong Representation</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: 'Microsoft', diversity: '32%', bonus: '+$12,000' },
                { name: 'Salesforce', diversity: '28%', bonus: '+$10,500' },
                { name: 'Netflix', diversity: '25%', bonus: '+$9,800' },
                { name: 'Adobe', diversity: '30%', bonus: '+$11,200' }
              ].map((company, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-2">
                    <h5 className="font-medium text-gray-900">{company.name}</h5>
                    <span className="text-sm text-green-600 font-medium">{company.bonus}</span>
                  </div>
                  <p className="text-xs text-gray-600">
                    {company.diversity} African American leadership representation
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Research Insights */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h5 className="font-medium text-yellow-900 mb-2">Research Insights</h5>
            <p className="text-sm text-yellow-800">
              Studies show that companies with diverse leadership teams are 35% more likely
              to have above-average financial returns and offer more equitable compensation
              structures for all employees.
            </p>
          </div>
        </div>
      )}

      {activeTab === 'community' && culturalData && (
        <div className="space-y-6">
          {/* Community Wealth Building Overview */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-semibold text-purple-900 mb-3">Community Wealth Building</h4>
            <p className="text-sm text-purple-700">
              Leverage community networks and resources to accelerate your career growth
              and build generational wealth.
            </p>
          </div>

          {/* Community Resources */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border border-gray-200 rounded-lg">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {culturalData.communityWealthBuilding.mentorshipOpportunities}
              </div>
              <div className="text-sm text-gray-600">Mentorship Programs</div>
              <div className="text-xs text-gray-500 mt-1">Available in your area</div>
            </div>
            <div className="text-center p-4 border border-gray-200 rounded-lg">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {culturalData.communityWealthBuilding.networkingGroups}
              </div>
              <div className="text-sm text-gray-600">Professional Networks</div>
              <div className="text-xs text-gray-500 mt-1">Active groups nearby</div>
            </div>
            <div className="text-center p-4 border border-gray-200 rounded-lg">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {culturalData.communityWealthBuilding.investmentOpportunities}
              </div>
              <div className="text-sm text-gray-600">Investment Groups</div>
              <div className="text-xs text-gray-500 mt-1">Wealth building focused</div>
            </div>
          </div>

          {/* Featured Organizations */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Featured Organizations</h4>
            <div className="space-y-3">
              {[
                {
                  name: 'National Black MBA Association',
                  focus: 'Professional Development & Networking',
                  members: '12,000+',
                  benefits: 'Mentorship, Job Board, Conferences'
                },
                {
                  name: 'Black Enterprise',
                  focus: 'Business & Investment Education',
                  members: '6.2M+',
                  benefits: 'Financial Literacy, Investment Opportunities'
                },
                {
                  name: 'National Society of Black Engineers',
                  focus: 'STEM Career Advancement',
                  members: '24,000+',
                  benefits: 'Technical Training, Leadership Development'
                }
              ].map((org, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h5 className="font-medium text-gray-900">{org.name}</h5>
                      <p className="text-sm text-gray-600">{org.focus}</p>
                    </div>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {org.members}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{org.benefits}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Wealth Building Tips */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-3">Wealth Building Strategies</h5>
            <div className="space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span>Join investment clubs focused on African American communities</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span>Participate in mentorship programs as both mentor and mentee</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span>Support Black-owned businesses and professional services</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span>Engage in community financial literacy programs</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 mt-6">
        <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
          Join Community
        </button>
        <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors">
          Get Resources
        </button>
      </div>
    </div>
  );
};

export default CulturalContextIntegration; 