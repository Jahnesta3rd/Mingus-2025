import React, { useState } from 'react';
import EnhancedJobMatchingDemo from '../components/EnhancedJobMatchingDemo';
import EnhancedJobMatchingResults from '../components/EnhancedJobMatchingResults';

const JobMatchingPreview: React.FC = () => {
  const [showResults, setShowResults] = useState(false);
  const [userTier, setUserTier] = useState<'Budget' | 'Mid-tier' | 'Professional'>('Budget');

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
          title: "Customer Success Manager",
          company: "FinTech Solutions",
          location: "New York, NY",
          salary_min: 75000,
          salary_max: 95000,
          description: "Manage customer relationships and drive retention for enterprise clients..."
        },
        enhanced_score: 85,
        positioning_strategy: {
          problem_focus: "Customer retention and satisfaction",
          value_proposition: "Strong background in customer relationship management",
          key_skills_to_highlight: ["Customer Success", "Retention", "Analytics"]
        },
        application_insights: {
          application_strength: 82,
          skill_gaps: [
            { skill: "Enterprise Software", priority: "Medium" },
            { skill: "Customer Success Tools", priority: "Low" }
          ],
          immediate_actions: [
            "Highlight customer retention metrics",
            "Prepare success stories",
            "Research company's customer base"
          ]
        }
      }
    ]
  };

  const handleRunAnalysis = () => {
    setShowResults(true);
  };

  const handleJobSelect = (job: any) => {
    console.log('Job selected:', job);
    // In a real app, this would navigate to job details or application
  };

  const handleUpgradePrompt = () => {
    console.log('Upgrade prompt triggered');
    // In a real app, this would show upgrade modal
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            Enhanced Job Matching Preview
          </h1>
          <p className="text-gray-300 text-lg">
            Experience the revolutionary problem-solution analysis approach
          </p>
        </div>

        {!showResults ? (
          <div className="max-w-4xl mx-auto">
            <EnhancedJobMatchingDemo 
              onRunAnalysis={handleRunAnalysis}
              userTier={userTier}
              onTierChange={setUserTier}
            />
          </div>
        ) : (
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <button
                onClick={() => setShowResults(false)}
                className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded-lg font-semibold transition-colors mb-4"
              >
                ← Back to Demo
              </button>
            </div>
            <EnhancedJobMatchingResults
              result={mockResult}
              userTier={userTier}
              onJobSelect={handleJobSelect}
              onUpgradePrompt={handleUpgradePrompt}
            />
          </div>
        )}

        <div className="mt-12 bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Key Features Demonstrated</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-700 border border-slate-600 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">Problem Analysis</h3>
              <p className="text-gray-300 text-sm">
                AI-powered extraction of business problems from job descriptions using linguistic analysis
              </p>
            </div>
            <div className="bg-slate-700 border border-slate-600 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">Solution Mapping</h3>
              <p className="text-gray-300 text-sm">
                Intelligent mapping of skills, certifications, and titles to solve identified problems
              </p>
            </div>
            <div className="bg-slate-700 border border-slate-600 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">Strategic Positioning</h3>
              <p className="text-gray-300 text-sm">
                Career positioning strategy with actionable development plans and networking guidance
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobMatchingPreview;
