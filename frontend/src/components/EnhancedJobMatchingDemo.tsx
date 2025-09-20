import React, { useState } from 'react';
import EnhancedJobMatchingResults from './EnhancedJobMatchingResults';

// Mock data for demonstration
const mockEnhancedResult = {
  job_matches: [
    {
      job_opportunity: {
        job_id: "job_001",
        title: "Senior Marketing Specialist",
        company: "HealthTech Solutions",
        location: "Atlanta, GA",
        salary_min: 55000,
        salary_max: 70000,
        salary_median: 62500,
        url: "https://example.com/job/001",
        description: "Lead digital marketing initiatives for healthcare technology company...",
        overall_score: 85
      },
      enhanced_score: 92,
      problem_solution_alignment: 88,
      positioning_strategy: {
        problem_focus: "Low patient engagement rates on digital platforms (currently 15% vs industry 25%)",
        solution_approach: [
          "Leverage Google Analytics expertise to improve patient engagement tracking",
          "Apply HubSpot automation skills to streamline patient communication",
          "Use social media strategy experience to increase digital presence"
        ],
        key_skills_to_highlight: ["Google Analytics", "HubSpot", "Social Media Strategy", "Content Creation", "Email Marketing"],
        value_proposition: "As a Marketing Coordinator with expertise in Google Analytics and HubSpot, I can help HealthTech Solutions solve patient engagement challenges to achieve improved digital presence and competitive advantage.",
        interview_talking_points: [
          {
            problem: "Low patient engagement rates on digital platforms",
            solution: "Based on my experience with Google Analytics and social media strategy, I would approach this by implementing comprehensive tracking and A/B testing...",
            impact: "This would help achieve 25%+ patient engagement rates within 6 months"
          }
        ],
        resume_keywords: ["Google Analytics", "HubSpot", "Social Media Strategy", "Patient Engagement", "Healthcare Marketing"]
      },
      application_insights: {
        application_strength: 85,
        skill_gaps: [
          {
            skill: "Healthcare Industry Knowledge",
            priority: "High",
            time_to_learn: "2-4 weeks",
            cost: "$200-500 (courses + research)"
          },
          {
            skill: "Advanced Data Analysis",
            priority: "Medium",
            time_to_learn: "1-2 months",
            cost: "$300-800 (certification)"
          }
        ],
        immediate_actions: [
          "Update resume to highlight healthcare marketing experience",
          "Research HealthTech Solutions' current digital strategy",
          "Prepare examples of patient engagement improvements"
        ],
        salary_negotiation_points: [
          "Problem-solving expertise in patient engagement challenges",
          "Industry experience in healthcare marketing",
          "Track record of improving digital engagement by 45%"
        ],
        company_research_focus: [
          "How they currently handle patient engagement on digital platforms",
          "Their approach to healthcare marketing compliance",
          "Recent initiatives in digital health technology"
        ],
        cover_letter_angles: [
          "Addressing patient engagement challenges with Google Analytics expertise",
          "Helping achieve 25%+ patient engagement rates",
          "Bringing healthcare marketing experience to solve their digital challenges"
        ]
      }
    },
    {
      job_opportunity: {
        job_id: "job_002",
        title: "Marketing Data Analyst",
        company: "MedTech Innovations",
        location: "Atlanta, GA",
        salary_min: 50000,
        salary_max: 65000,
        salary_median: 57500,
        url: "https://example.com/job/002",
        description: "Analyze marketing data to improve patient acquisition and engagement...",
        overall_score: 78
      },
      enhanced_score: 85,
      problem_solution_alignment: 82,
      positioning_strategy: {
        problem_focus: "Difficulty measuring marketing ROI and patient acquisition costs",
        solution_approach: [
          "Leverage Google Analytics expertise to improve ROI tracking",
          "Apply data analysis skills to optimize patient acquisition costs"
        ],
        key_skills_to_highlight: ["Google Analytics", "Data Analysis", "ROI Tracking", "Patient Acquisition"],
        value_proposition: "As a Marketing Coordinator with expertise in Google Analytics and data analysis, I can help MedTech Innovations solve ROI measurement challenges to achieve better marketing efficiency.",
        interview_talking_points: [
          {
            problem: "Difficulty measuring marketing ROI",
            solution: "Based on my experience with Google Analytics and campaign tracking, I would implement comprehensive attribution modeling...",
            impact: "This would help achieve accurate ROI measurement and 20% cost reduction"
          }
        ],
        resume_keywords: ["Google Analytics", "Data Analysis", "ROI Tracking", "Marketing Analytics"]
      },
      application_insights: {
        application_strength: 78,
        skill_gaps: [
          {
            skill: "Advanced Excel/Spreadsheet Analysis",
            priority: "Medium",
            time_to_learn: "2-4 weeks",
            cost: "$100-300 (courses)"
          }
        ],
        immediate_actions: [
          "Highlight data analysis experience in resume",
          "Prepare examples of ROI improvement campaigns",
          "Research MedTech Innovations' current analytics setup"
        ],
        salary_negotiation_points: [
          "Data analysis expertise for ROI measurement",
          "Experience in healthcare marketing analytics",
          "Track record of improving campaign efficiency"
        ],
        company_research_focus: [
          "How they currently measure marketing ROI",
          "Their analytics tools and data infrastructure",
          "Recent data-driven marketing initiatives"
        ],
        cover_letter_angles: [
          "Addressing ROI measurement challenges with data analysis expertise",
          "Helping achieve better marketing efficiency through analytics",
          "Bringing healthcare marketing data experience to solve their measurement challenges"
        ]
      }
    }
  ],
  problem_solution_summary: {
    problem_statement: {
      context: "HealthTech Solutions is a healthcare technology startup",
      challenge: "facing low patient engagement rates on digital platforms and inconsistent brand messaging",
      impact: "reduced patient acquisition and brand recognition",
      desired_outcome: "improved patient engagement and consistent brand presence",
      timeframe: "3-6 months",
      constraints: ["limited marketing budget", "small team", "healthcare compliance requirements"]
    },
    industry_context: "healthcare",
    company_stage: "startup",
    confidence_score: 0.92,
    top_solutions: {
      skills: [
        { name: "Google Analytics", score: 95 },
        { name: "HubSpot Marketing", score: 88 },
        { name: "Social Media Strategy", score: 85 },
        { name: "Content Creation", score: 82 },
        { name: "Email Marketing", score: 80 }
      ],
      certifications: [
        { name: "Google Analytics Certified", score: 92 },
        { name: "HubSpot Content Marketing", score: 88 },
        { name: "Facebook Blueprint", score: 85 }
      ],
      titles: [
        { name: "Marketing Specialist", score: 95 },
        { name: "Digital Marketing Coordinator", score: 88 },
        { name: "Healthcare Marketing Analyst", score: 85 }
      ]
    }
  },
  career_positioning_plan: {
    problem_solving_focus: "Low patient engagement rates on digital platforms",
    solution_roadmap: [
      {
        skill: "Google Analytics",
        timeline: "2-4 weeks",
        cost: "$200-500",
        expected_impact: "+$5,000-10,000"
      },
      {
        skill: "HubSpot Marketing",
        timeline: "1-2 months",
        cost: "$300-800",
        expected_impact: "+$3,000-8,000"
      },
      {
        skill: "Healthcare Industry Knowledge",
        timeline: "2-4 weeks",
        cost: "$200-500",
        expected_impact: "+$2,000-5,000"
      }
    ],
    skill_development_plan: {
      immediate_actions: [
        {
          action: "Update resume to highlight healthcare marketing experience",
          timeline: "1 week",
          cost: "$0",
          priority: "High"
        },
        {
          action: "Research healthcare marketing best practices",
          timeline: "2 weeks",
          cost: "$100-200",
          priority: "High"
        }
      ],
      short_term_goals: [
        {
          action: "Complete Google Analytics certification",
          timeline: "1 month",
          cost: "$200-500",
          priority: "High"
        },
        {
          action: "Develop healthcare marketing portfolio",
          timeline: "6 weeks",
          cost: "$300-600",
          priority: "Medium"
        }
      ],
      medium_term_goals: [
        {
          action: "Master HubSpot marketing automation",
          timeline: "2 months",
          cost: "$400-800",
          priority: "Medium"
        }
      ],
      long_term_goals: [
        {
          action: "Become healthcare marketing expert",
          timeline: "6 months",
          cost: "$1000-2000",
          priority: "Low"
        }
      ]
    },
    networking_strategy: [
      "Join Healthcare Marketing Association",
      "Attend healthcare technology conferences",
      "Connect with healthcare marketers on LinkedIn",
      "Participate in healthcare marketing online communities"
    ],
    portfolio_projects: [
      "Build a healthcare patient engagement campaign case study",
      "Create a healthcare marketing ROI analysis project",
      "Develop a healthcare social media strategy demonstration"
    ],
    interview_preparation: [
      "Prepare STAR stories about solving patient engagement challenges",
      "Research HealthTech Solutions' current marketing approach",
      "Practice explaining Google Analytics solutions for healthcare"
    ]
  },
  success_probability: 0.87,
  generated_at: "2025-09-19T10:30:00Z"
};

const EnhancedJobMatchingDemo: React.FC = () => {
  const [selectedTier, setSelectedTier] = useState<'Budget' | 'Mid-tier' | 'Professional'>('Mid-tier');
  const [isLoading, setIsLoading] = useState(false);

  const handleJobSelect = (job: any) => {
    console.log('Job selected:', job);
    // Handle job selection logic
  };

  const handleUpgradePrompt = () => {
    console.log('Upgrade prompted');
    // Handle upgrade prompt logic
  };

  const simulateAnalysis = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Enhanced Job Matching Demo
              </h1>
              <p className="text-gray-300">
                Job Description to Problem Statement Analysis Methodology
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-300">User Tier:</span>
                <select
                  value={selectedTier}
                  onChange={(e) => setSelectedTier(e.target.value as any)}
                  className="px-3 py-1 border border-slate-600 bg-slate-700 text-white rounded-lg text-sm focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
                >
                  <option value="Budget">Budget ($15/month)</option>
                  <option value="Mid-tier">Mid-tier ($35/month)</option>
                  <option value="Professional">Professional ($100/month)</option>
                </select>
              </div>
              <button
                onClick={simulateAnalysis}
                disabled={isLoading}
                className="bg-violet-600 hover:bg-violet-700 disabled:bg-gray-600 text-white px-6 py-2 rounded-lg font-semibold transition-colors focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-slate-900"
              >
                {isLoading ? 'Analyzing...' : 'Run Analysis'}
              </button>
            </div>
          </div>
        </div>

        {/* Demo Content */}
        {isLoading ? (
          <div className="bg-slate-800 rounded-xl shadow-sm border border-slate-700 p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-white mb-2">Analyzing Job Description</h3>
            <p className="text-gray-300">
              Extracting problems, mapping solutions, and generating strategic positioning...
            </p>
          </div>
        ) : (
          <EnhancedJobMatchingResults
            result={mockEnhancedResult}
            userTier={selectedTier}
            onJobSelect={handleJobSelect}
            onUpgradePrompt={handleUpgradePrompt}
          />
        )}

        {/* Feature Explanation */}
        <div className="mt-8 bg-slate-800 rounded-xl shadow-sm border border-slate-700 p-6">
          <h2 className="text-xl font-bold text-white mb-4">How Enhanced Job Matching Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-violet-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="font-semibold text-white mb-2">Problem Extraction</h3>
              <p className="text-sm text-gray-300">
                Analyzes job descriptions to identify business problems and challenges that need solving.
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">💡</span>
              </div>
              <h3 className="font-semibold text-white mb-2">Solution Mapping</h3>
              <p className="text-sm text-gray-300">
                Maps problems to specific skills, certifications, and titles that position you as the solution.
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🚀</span>
              </div>
              <h3 className="font-semibold text-white mb-2">Strategic Positioning</h3>
              <p className="text-sm text-gray-300">
                Provides complete application strategy with positioning, talking points, and action plans.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedJobMatchingDemo;
