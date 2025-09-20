import React, { useState } from 'react';
import NavigationBar from '../components/NavigationBar';

const SimpleJobMatchingPreview: React.FC = () => {
  const [activeTab, setActiveTab] = useState('demo');
  // User tier should be determined by actual subscription level, not user selection
  const userTier: 'Budget' | 'Mid-tier' | 'Professional' = 'Professional'; // This would come from user profile/subscription

  // Mock data for demonstration
  const mockResult = {
    problem_solution_summary: {
      confidence_score: 0.87,
      industry_context: "Technology",
      company_stage: "Growth Stage",
      problem_statement: {
        context: "A rapidly growing fintech startup",
        challenge: "scaling customer acquisition while maintaining service quality",
        impact: "customer churn and revenue loss",
        desired_outcome: "sustainable growth with high customer satisfaction",
        timeframe: "6 months",
        constraints: ["Limited budget", "Small team", "Regulatory compliance"]
      },
      top_solutions: {
        skills: [
          { name: "Customer Acquisition Strategy", score: 92 },
          { name: "Data Analytics", score: 88 },
          { name: "Growth Hacking", score: 85 },
          { name: "Customer Success Management", score: 82 },
          { name: "Marketing Automation", score: 78 }
        ],
        certifications: [
          { name: "Google Analytics Certified", score: 90 },
          { name: "HubSpot Growth Marketing", score: 85 },
          { name: "Salesforce Certified", score: 80 },
          { name: "PMP Certification", score: 75 },
          { name: "Agile Marketing", score: 70 }
        ],
        titles: [
          { name: "Growth Marketing Manager", score: 95 },
          { name: "Customer Acquisition Specialist", score: 88 },
          { name: "Marketing Operations Manager", score: 82 },
          { name: "Customer Success Manager", score: 78 },
          { name: "Digital Marketing Lead", score: 75 }
        ]
      }
    },
    career_positioning_plan: {
      problem_solving_focus: "Customer acquisition and retention optimization",
      solution_roadmap: [
        { skill: "Advanced Analytics", timeline: "30 days", cost: "$500", expected_impact: "High" },
        { skill: "Growth Marketing", timeline: "60 days", cost: "$1,200", expected_impact: "High" },
        { skill: "Customer Success", timeline: "90 days", cost: "$800", expected_impact: "Medium" }
      ],
      networking_strategy: [
        "Join Growth Marketing communities",
        "Attend fintech networking events",
        "Connect with customer success professionals"
      ],
      skill_development_plan: {
        immediate_actions: [
          { action: "Complete Google Analytics certification", timeline: "2 weeks" },
          { action: "Set up advanced tracking systems", timeline: "1 week" }
        ],
        short_term_goals: [
          { action: "Implement A/B testing framework", timeline: "1 month" },
          { action: "Develop customer segmentation strategy", timeline: "6 weeks" }
        ],
        medium_term_goals: [
          { action: "Launch automated marketing campaigns", timeline: "2 months" },
          { action: "Build customer success metrics dashboard", timeline: "10 weeks" }
        ],
        long_term_goals: [
          { action: "Lead growth marketing team", timeline: "6 months" },
          { action: "Develop company-wide growth strategy", timeline: "8 months" }
        ]
      }
    },
    job_matches: [
      {
        job_opportunity: {
          job_id: "job_001",
          title: "Growth Marketing Manager",
          company: "TechStart Inc",
          location: "San Francisco, CA",
          salary_min: 90000,
          salary_max: 120000,
          description: "Lead growth marketing initiatives for a fast-growing fintech startup..."
        },
        enhanced_score: 92,
        positioning_strategy: {
          problem_focus: "Customer acquisition scaling challenges",
          value_proposition: "Proven track record in growth marketing with data-driven approach",
          key_skills_to_highlight: ["Analytics", "Growth Hacking", "Customer Acquisition"]
        },
        application_insights: {
          application_strength: 88,
          skill_gaps: [
            { skill: "Advanced SQL", priority: "High" },
            { skill: "Marketing Automation Tools", priority: "Medium" }
          ],
          immediate_actions: [
            "Update resume with growth metrics",
            "Prepare case study examples",
            "Research company's growth challenges"
          ]
        }
      },
      {
        job_opportunity: {
          job_id: "job_002",
          title: "Senior Marketing Operations Manager",
          company: "ScaleUp Ventures",
          location: "Remote",
          salary_min: 110000,
          salary_max: 140000,
          description: "Oversee marketing operations and campaign optimization for a growing tech company..."
        },
        enhanced_score: 88,
        positioning_strategy: {
          problem_focus: "Marketing operations efficiency and campaign optimization",
          value_proposition: "Strong analytical background with experience in marketing automation and ROI optimization",
          key_skills_to_highlight: ["Marketing Operations", "Campaign Management", "ROI Optimization"]
        },
        application_insights: {
          application_strength: 85,
          skill_gaps: [
            { skill: "Marketing Automation Platforms", priority: "High" },
            { skill: "Advanced Excel/Google Sheets", priority: "Medium" }
          ],
          immediate_actions: [
            "Highlight operations experience",
            "Prepare campaign performance examples",
            "Research company's marketing stack"
          ]
        }
      },
      {
        job_opportunity: {
          job_id: "job_003",
          title: "Customer Acquisition Lead",
          company: "GrowthCo",
          location: "New York, NY",
          salary_min: 95000,
          salary_max: 125000,
          description: "Lead customer acquisition strategies and manage acquisition channels for a B2B SaaS company..."
        },
        enhanced_score: 85,
        positioning_strategy: {
          problem_focus: "B2B customer acquisition and lead generation optimization",
          value_proposition: "Data-driven approach to customer acquisition with proven results in B2B marketing",
          key_skills_to_highlight: ["B2B Marketing", "Lead Generation", "Customer Acquisition"]
        },
        application_insights: {
          application_strength: 82,
          skill_gaps: [
            { skill: "B2B Sales Funnel Knowledge", priority: "High" },
            { skill: "LinkedIn Advertising", priority: "Medium" }
          ],
          immediate_actions: [
            "Emphasize B2B experience",
            "Prepare acquisition case studies",
            "Research company's target market"
          ]
        }
      }
    ]
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'Budget': return 'bg-violet-600';
      case 'Mid-tier': return 'bg-purple-600';
      case 'Professional': return 'bg-violet-700';
      default: return 'bg-slate-600';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const formatSalary = (min: number, max: number) => {
    return `$${(min / 1000).toFixed(0)}k - $${(max / 1000).toFixed(0)}k`;
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header id="navigation" role="banner" aria-label="Site header">
        <NavigationBar />
      </header>

      {/* Hero Section with Gradient Background */}
      <section className="relative pt-16 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Large Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-violet-900 to-purple-900"></div>
        
        <div className="relative max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 sm:mb-6 leading-tight">
              Career Opportunities
              <br />
              <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                Built For Your Success
              </span>
            </h1>
            <p className="text-lg sm:text-xl md:text-2xl text-gray-300 mb-6 sm:mb-8 max-w-2xl mx-auto leading-relaxed">
              Discover your next career move with personalized recommendations tailored to your background and goals.
            </p>
          </div>
        </div>
      </section>

      {/* Main Content Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-800/50" role="region" aria-label="Career matching">
        <div className="max-w-7xl mx-auto">

        {activeTab === 'demo' ? (
          <div className="max-w-6xl mx-auto">
            {/* Demo Interface */}
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 text-white">
                Ready to Find Your Next Opportunity?
              </h2>
              <p className="text-xl text-gray-300 max-w-3xl mx-auto">
                Get personalized job recommendations based on your profile and career goals
              </p>
            </div>

            <div className="space-y-8">
              <div className="text-center">
                <button
                  onClick={() => setActiveTab('results')}
                  className="group bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-8 py-4 rounded-lg text-xl font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-violet-500/25 flex items-center justify-center hover:-translate-y-1 mx-auto"
                >
                  <span className="mr-3">🚀</span>
                  Analyze My Career Opportunities
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12">
                <div className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                  <div className="text-purple-400 mb-4 group-hover:text-purple-300 transition-all duration-300 transform group-hover:scale-110">
                    <span className="text-4xl">🧠</span>
                  </div>
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-purple-100 transition-colors duration-300">Smart Analysis</h3>
                  <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">
                    Advanced analysis of job opportunities tailored to your background and career trajectory
                  </p>
                </div>
                <div className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                  <div className="text-purple-400 mb-4 group-hover:text-purple-300 transition-all duration-300 transform group-hover:scale-110">
                    <span className="text-4xl">🎯</span>
                  </div>
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-purple-100 transition-colors duration-300">Perfect Matches</h3>
                  <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">
                    Find opportunities that align with your skills, values, and career aspirations
                  </p>
                </div>
                <div className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                  <div className="text-purple-400 mb-4 group-hover:text-purple-300 transition-all duration-300 transform group-hover:scale-110">
                    <span className="text-4xl">🚀</span>
                  </div>
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-purple-100 transition-colors duration-300">Career Growth</h3>
                  <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">
                    Strategic recommendations to advance your career and maximize your potential
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <button
                onClick={() => setActiveTab('demo')}
                className="group bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-300 border border-gray-700 hover:border-purple-500/50 hover:scale-105"
              >
                ← Back to Analysis
              </button>
            </div>

            {/* Results Display */}
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 text-white">
                Your Career Opportunities
              </h2>
              <div className="flex items-center justify-center space-x-4 bg-gray-800 rounded-xl px-6 py-3 border border-gray-700 max-w-md mx-auto">
                <span className="text-gray-300 text-lg">Analysis Confidence:</span>
                <span className="text-green-400 font-bold text-xl">
                  {Math.round(mockResult.problem_solution_summary.confidence_score * 100)}%
                </span>
              </div>
            </div>

            {/* Career Focus */}
            <div className="mb-16">
              <h3 className="text-2xl font-bold text-white mb-6">Your Career Focus</h3>
              <div className="bg-gray-800 p-8 rounded-xl border border-gray-700">
                <p className="text-gray-300 leading-relaxed text-lg">
                  Based on your background and career goals, we've identified opportunities in{' '}
                  <span className="font-bold text-white">{mockResult.problem_solution_summary.problem_statement.context}</span> where you can address{' '}
                  <span className="text-violet-400 font-semibold">{mockResult.problem_solution_summary.problem_statement.challenge}</span> and help achieve{' '}
                  <span className="text-green-400 font-semibold">{mockResult.problem_solution_summary.problem_statement.desired_outcome}</span>.
                </p>
              </div>
            </div>

            {/* Recommendations */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
              <div>
                <h4 className="text-xl font-semibold mb-4 text-white">Recommended Skills</h4>
                <div className="space-y-4">
                  {mockResult.problem_solution_summary.top_solutions.skills.slice(0, 3).map((skill, index) => (
                    <div key={index} className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-semibold text-white group-hover:text-purple-100 transition-colors duration-300">{skill.name}</span>
                        <span className={`font-bold ${getScoreColor(skill.score)}`}>
                          {skill.score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-600 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-yellow-400 to-yellow-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${skill.score}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xl font-semibold mb-4 text-white">Certifications to Consider</h4>
                <div className="space-y-4">
                  {mockResult.problem_solution_summary.top_solutions.certifications.slice(0, 3).map((cert, index) => (
                    <div key={index} className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-semibold text-white group-hover:text-purple-100 transition-colors duration-300">{cert.name}</span>
                        <span className={`font-bold ${getScoreColor(cert.score)}`}>
                          {cert.score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-600 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-blue-400 to-blue-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${cert.score}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xl font-semibold mb-4 text-white">Target Positions</h4>
                <div className="space-y-4">
                  {mockResult.problem_solution_summary.top_solutions.titles.slice(0, 3).map((title, index) => (
                    <div key={index} className="group bg-gray-800 p-6 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-semibold text-white group-hover:text-purple-100 transition-colors duration-300">{title.name}</span>
                        <span className={`font-bold ${getScoreColor(title.score)}`}>
                          {title.score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-600 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-green-400 to-green-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${title.score}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Job Matches */}
            <div>
              <h3 className="text-2xl font-bold text-white mb-8">Recommended Opportunities</h3>
              <div className="space-y-6">
                {mockResult.job_matches.map((match, index) => (
                  <div key={index} className="group bg-gray-800 p-8 rounded-xl hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 border border-gray-700 hover:border-purple-500/50">
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex-1">
                        <h4 className="text-2xl font-bold text-white mb-3 group-hover:text-purple-100 transition-colors duration-300">{match.job_opportunity.title}</h4>
                        <p className="text-gray-300 text-lg mb-4 group-hover:text-gray-200 transition-colors duration-300">{match.job_opportunity.company} • {match.job_opportunity.location}</p>
                        <div className="flex items-center space-x-8 text-lg">
                          <span className="text-gray-300">Salary: <span className="text-white font-semibold">{formatSalary(match.job_opportunity.salary_min, match.job_opportunity.salary_max)}</span></span>
                          <span className="text-gray-300">Match Score: <span className={`font-bold ${getScoreColor(match.enhanced_score)}`}>{Math.round(match.enhanced_score)}/100</span></span>
                        </div>
                      </div>
                      <button className="group bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-violet-500/25">
                        Apply Now
                      </button>
                    </div>
                    <div className="bg-gray-700 rounded-xl p-6 border border-gray-600">
                      <h5 className="font-bold text-white mb-4 text-lg">Why This Role Fits You</h5>
                      <p className="text-gray-300 mb-3">{match.positioning_strategy.problem_focus}</p>
                      <p className="text-gray-300">{match.positioning_strategy.value_proposition}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        </div>
      </section>

      {/* Footer */}
      <footer id="footer" className="bg-gray-900 border-t border-gray-800 py-12 px-4 sm:px-6 lg:px-8" role="contentinfo" aria-label="Site footer">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col items-center text-center">
            {/* Mingus Logo */}
            <div className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent mb-4">
              Mingus
            </div>
            
            {/* Copyright */}
            <p className="text-gray-400 text-sm">
              © 2024 Mingus. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default SimpleJobMatchingPreview;
