import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Shield, 
  Target, 
  MapPin, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  DollarSign,
  Briefcase,
  Star,
  ArrowRight,
  ExternalLink
} from 'lucide-react';

const ComprehensiveDashboardPreview: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'recommendations' | 'location' | 'analytics'>('overview');
  const [riskLevel, setRiskLevel] = useState<'secure' | 'watchful' | 'action_needed' | 'urgent'>('action_needed');

  const sampleData = {
    riskAssessment: {
      level: 'action_needed',
      score: 68,
      factors: [
        { name: 'Market Volatility', impact: 'high', trend: 'increasing', value: 85 },
        { name: 'Skill Relevance', impact: 'medium', trend: 'stable', value: 72 },
        { name: 'Industry Stability', impact: 'high', trend: 'decreasing', value: 45 },
        { name: 'Competition Level', impact: 'medium', trend: 'increasing', value: 78 }
      ]
    },
    recommendations: {
      safeGrowth: [
        {
          title: 'Senior Software Engineer',
          company: 'TechCorp Inc.',
          location: 'San Francisco, CA',
          salary: '$120,000 - $150,000',
          match: 92,
          description: 'Stable role with growth opportunities in established company',
          benefits: ['Health Insurance', '401k Match', 'Flexible Hours']
        },
        {
          title: 'Product Manager',
          company: 'InnovateLabs',
          location: 'Austin, TX',
          salary: '$110,000 - $135,000',
          match: 88,
          description: 'Product management role with clear career progression',
          benefits: ['Stock Options', 'Learning Budget', 'Remote Work']
        }
      ],
      strategicAdvance: [
        {
          title: 'AI Solutions Architect',
          company: 'FutureTech Systems',
          location: 'Seattle, WA',
          salary: '$140,000 - $180,000',
          match: 85,
          description: 'High-growth role in AI/ML space with excellent prospects',
          benefits: ['Equity', 'Conference Budget', 'Mentorship Program']
        }
      ],
      ambitiousLeap: [
        {
          title: 'VP of Engineering',
          company: 'StartupX',
          location: 'San Francisco, CA',
          salary: '$180,000 - $250,000',
          match: 75,
          description: 'Executive role with significant equity and growth potential',
          benefits: ['Significant Equity', 'Executive Benefits', 'Board Access']
        }
      ]
    },
    locations: [
      { name: 'San Francisco, CA', salary: 145000, jobs: 2847, growth: 8.2, cost: 165.2 },
      { name: 'Seattle, WA', salary: 132000, jobs: 1923, growth: 6.8, cost: 142.1 },
      { name: 'Austin, TX', salary: 118000, jobs: 1654, growth: 12.4, cost: 98.7 },
      { name: 'New York, NY', salary: 138000, jobs: 3241, growth: 5.2, cost: 187.3 }
    ],
    activity: [
      { type: 'assessment', title: 'Career Risk Assessment Completed', time: '2 hours ago', status: 'completed' },
      { type: 'recommendation', title: 'New Job Recommendations Available', time: '4 hours ago', status: 'completed' },
      { type: 'profile', title: 'Profile Updated', time: '1 day ago', status: 'completed' },
      { type: 'application', title: 'Job Application Submitted', time: '2 days ago', status: 'pending' }
    ]
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'secure': return 'text-green-600 bg-green-100';
      case 'watchful': return 'text-yellow-600 bg-yellow-100';
      case 'action_needed': return 'text-orange-600 bg-orange-100';
      case 'urgent': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'secure': return <Shield className="h-5 w-5" />;
      case 'watchful': return <AlertTriangle className="h-5 w-5" />;
      case 'action_needed': return <Target className="h-5 w-5" />;
      case 'urgent': return <AlertTriangle className="h-5 w-5" />;
      default: return <Shield className="h-5 w-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-slate-900/90 backdrop-blur-sm border-b border-slate-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-violet-700 rounded-lg flex items-center justify-center shadow-lg hover:shadow-violet-500/25 transition-all duration-300">
                    <span className="text-white font-bold text-xl">M</span>
                  </div>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Career Protection Dashboard</h1>
                  <div className="bg-violet-100 text-violet-800 text-xs px-2 py-1 rounded-full font-medium">
                    PREVIEW WITH SAMPLE DATA
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="text-sm text-violet-400 hover:text-violet-300 font-medium px-3 py-1 rounded hover:bg-slate-800/50 transition-colors"
              >
                ← Back to Home
              </button>
              
              <div className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${getRiskColor(riskLevel)}`}>
                {riskLevel.replace('_', ' ')}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Risk Status Hero */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-violet-600 to-purple-600 p-8 shadow-xl hover:shadow-violet-500/25 transition-all duration-300">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" />
            
            <div className="relative z-10 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-white/20 rounded-lg">
                    {getRiskIcon(riskLevel)}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">Action Needed</h2>
                    <p className="text-violet-100">Your career requires immediate attention</p>
                  </div>
                </div>
                
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium">Risk Score: 68/100</span>
                    <span className="text-violet-200 text-sm">High Risk</span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-3">
                    <div className="bg-white h-3 rounded-full" style={{ width: '68%' }} />
                  </div>
                </div>
                
                <p className="text-white/90 mb-4">
                  Market volatility and industry changes indicate your current position may be at risk. 
                  Consider exploring new opportunities and upskilling.
                </p>
                
                <button className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-violet-500/25 hover:-translate-y-0.5">
                  View Protection Plan
                </button>
              </div>
              
              <div className="flex-shrink-0 ml-6">
                <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-12 w-12 text-white" />
                </div>
              </div>
            </div>
          </div>
          
          {/* Tab Navigation */}
          <div className="border-b border-slate-800/50">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'recommendations', label: 'Job Recommendations', icon: '🎯' },
                { id: 'location', label: 'Location Intelligence', icon: '🗺️' },
                { id: 'analytics', label: 'Career Analytics', icon: '📈' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-violet-500 text-violet-400'
                      : 'border-transparent text-gray-300 hover:text-violet-400 hover:border-violet-400'
                  }`}
                >
                  <span>{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="min-h-[600px]">
            
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="grid gap-8 lg:grid-cols-2">
                {/* Quick Actions */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
                  <div className="space-y-4">
                    <div className="bg-gradient-to-r from-violet-600/20 to-purple-600/20 border border-violet-500/30 rounded-lg p-4 backdrop-blur-sm">
                      <div className="flex items-start gap-3">
                        <Target className="h-5 w-5 text-violet-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <h4 className="font-semibold text-white">Protection Plan</h4>
                          <p className="text-violet-200 text-sm mt-1">
                            Immediate action recommended for your career security
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <button 
                        onClick={() => setActiveTab('recommendations')}
                        className="w-full flex items-center gap-3 p-4 bg-slate-800/50 text-violet-300 hover:bg-slate-700/50 border border-slate-700/50 rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/10 cursor-pointer"
                      >
                        <div className="p-2 bg-violet-600/20 rounded-lg">
                          <Target className="h-5 w-5 text-violet-400" />
                        </div>
                        <div className="flex-1 text-left">
                          <h5 className="font-medium text-white">View Job Recommendations</h5>
                          <p className="text-sm text-violet-200">Explore personalized job opportunities</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-violet-400" />
                      </button>
                      
                      <button 
                        onClick={() => setActiveTab('location')}
                        className="w-full flex items-center gap-3 p-4 bg-slate-800/50 text-purple-300 hover:bg-slate-700/50 border border-slate-700/50 rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10 cursor-pointer"
                      >
                        <div className="p-2 bg-purple-600/20 rounded-lg">
                          <MapPin className="h-5 w-5 text-purple-400" />
                        </div>
                        <div className="flex-1 text-left">
                          <h5 className="font-medium text-white">Location Intelligence</h5>
                          <p className="text-sm text-purple-200">Analyze job markets by location</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-purple-400" />
                      </button>
                      
                      <button 
                        onClick={() => setActiveTab('analytics')}
                        className="w-full flex items-center gap-3 p-4 bg-slate-800/50 text-green-300 hover:bg-slate-700/50 border border-slate-700/50 rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-green-500/10 cursor-pointer"
                      >
                        <div className="p-2 bg-green-600/20 rounded-lg">
                          <TrendingUp className="h-5 w-5 text-green-400" />
                        </div>
                        <div className="flex-1 text-left">
                          <h5 className="font-medium text-white">Career Analytics</h5>
                          <p className="text-sm text-green-200">View detailed career insights</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-green-400" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Recent Activity */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    {sampleData.activity.map((item, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:bg-slate-700/50 transition-colors">
                        <div className={`p-2 rounded-lg ${
                          item.status === 'completed' ? 'bg-green-600/20 text-green-400' : 'bg-yellow-600/20 text-yellow-400'
                        }`}>
                          {item.type === 'assessment' && <Target className="h-4 w-4" />}
                          {item.type === 'recommendation' && <TrendingUp className="h-4 w-4" />}
                          {item.type === 'profile' && <Users className="h-4 w-4" />}
                          {item.type === 'application' && <Briefcase className="h-4 w-4" />}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white text-sm">{item.title}</h4>
                          <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                            <Clock className="h-3 w-3" />
                            <span>{item.time}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              item.status === 'completed' ? 'bg-green-600/20 text-green-400' : 'bg-yellow-600/20 text-yellow-400'
                            }`}>
                              {item.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <div className="space-y-8">
                {/* Safe Growth Tier */}
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                      <Shield className="h-5 w-5 text-green-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900">Safe Growth</h3>
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
                      Low Risk
                    </span>
                  </div>
                  
                  <div className="grid gap-4 md:grid-cols-2">
                    {sampleData.recommendations.safeGrowth.map((job, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-semibold text-gray-900">{job.title}</h4>
                            <p className="text-gray-600">{job.company}</p>
                            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-semibold text-gray-900">{job.salary}</div>
                            <div className="text-sm text-green-600 font-medium">{job.match}% match</div>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 text-sm mb-4">{job.description}</p>
                        
                        <div className="flex flex-wrap gap-2 mb-4">
                          {job.benefits.map((benefit, i) => (
                            <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                              {benefit}
                            </span>
                          ))}
                        </div>
                        
                        <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                          Apply Now
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Strategic Advance Tier */}
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                      <Target className="h-5 w-5 text-yellow-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900">Strategic Advance</h3>
                    <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full font-medium">
                      Medium Risk
                    </span>
                  </div>
                  
                  <div className="grid gap-4 md:grid-cols-2">
                    {sampleData.recommendations.strategicAdvance.map((job, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-semibold text-gray-900">{job.title}</h4>
                            <p className="text-gray-600">{job.company}</p>
                            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-semibold text-gray-900">{job.salary}</div>
                            <div className="text-sm text-yellow-600 font-medium">{job.match}% match</div>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 text-sm mb-4">{job.description}</p>
                        
                        <div className="flex flex-wrap gap-2 mb-4">
                          {job.benefits.map((benefit, i) => (
                            <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                              {benefit}
                            </span>
                          ))}
                        </div>
                        
                        <button className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                          Apply Now
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Ambitious Leap Tier */}
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900">Ambitious Leap</h3>
                    <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full font-medium">
                      High Risk
                    </span>
                  </div>
                  
                  <div className="grid gap-4 md:grid-cols-2">
                    {sampleData.recommendations.ambitiousLeap.map((job, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-semibold text-gray-900">{job.title}</h4>
                            <p className="text-gray-600">{job.company}</p>
                            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                              <MapPin className="h-3 w-3" />
                              {job.location}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-semibold text-gray-900">{job.salary}</div>
                            <div className="text-sm text-red-600 font-medium">{job.match}% match</div>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 text-sm mb-4">{job.description}</p>
                        
                        <div className="flex flex-wrap gap-2 mb-4">
                          {job.benefits.map((benefit, i) => (
                            <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                              {benefit}
                            </span>
                          ))}
                        </div>
                        
                        <button className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                          Apply Now
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Location Tab */}
            {activeTab === 'location' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Location Intelligence</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">Radius:</span>
                    <select className="border border-gray-300 rounded px-2 py-1 text-sm">
                      <option>25 miles</option>
                      <option>50 miles</option>
                      <option>100 miles</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {sampleData.locations.map((location, index) => (
                    <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-4">
                        <h4 className="font-semibold text-gray-900">{location.name}</h4>
                        <div className="text-right">
                          <div className="text-lg font-semibold text-gray-900">${(location.salary / 1000).toFixed(0)}k</div>
                          <div className="text-sm text-gray-500">avg salary</div>
                        </div>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Job Openings:</span>
                          <span className="font-medium">{location.jobs.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Growth Rate:</span>
                          <span className="font-medium text-green-600">+{location.growth}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Cost of Living:</span>
                          <span className="font-medium">{location.cost}</span>
                        </div>
                      </div>
                      
                      <button className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                        View Details
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
              <div className="space-y-8">
                <h3 className="text-lg font-semibold text-gray-900">Career Analytics</h3>
                
                {/* Career Trajectory Chart */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Career Trajectory</h4>
                  <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-500">Career trajectory chart would be displayed here</p>
                      <p className="text-sm text-gray-400">Showing 6-month trend with risk score progression</p>
                    </div>
                  </div>
                </div>
                
                {/* Skill Demand Analysis */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Skill Demand Analysis</h4>
                  <div className="space-y-4">
                    {[
                      { skill: 'JavaScript', demand: 95, growth: 12 },
                      { skill: 'Python', demand: 88, growth: 18 },
                      { skill: 'React', demand: 82, growth: 15 },
                      { skill: 'Node.js', demand: 78, growth: 8 },
                      { skill: 'AWS', demand: 85, growth: 22 }
                    ].map((skill, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-gray-900">{skill.skill}</span>
                            <span className="text-sm text-gray-500">{skill.demand}% demand</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${skill.demand}%` }}
                            />
                          </div>
                          <div className="text-xs text-green-600 mt-1">+{skill.growth}% growth</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Market Trends */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600 mb-1">78%</div>
                    <div className="text-sm text-gray-600">Remote Work</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-green-600 mb-1">6.2%</div>
                    <div className="text-sm text-gray-600">Salary Growth</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600 mb-1">12.4k</div>
                    <div className="text-sm text-gray-600">Job Openings</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-orange-600 mb-1">72%</div>
                    <div className="text-sm text-gray-600">Competition</div>
                  </div>
                </div>
              </div>
            )}
            
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveDashboardPreview;

