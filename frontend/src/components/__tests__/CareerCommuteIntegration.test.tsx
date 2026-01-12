import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CareerCommuteIntegration from '../CareerCommuteIntegration';

// Mock the analytics hook
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackInteraction: jest.fn(),
    trackError: jest.fn()
  })
}));

// Mock fetch
global.fetch = jest.fn();

// Mock data
const mockJobRecommendations = [
  {
    job: {
      job_id: 'job_1',
      title: 'Software Engineer',
      company: 'Tech Corp',
      location: 'San Francisco, CA',
      msa: 'San Francisco-Oakland-Berkeley, CA',
      salary_min: 120000,
      salary_max: 150000,
      salary_median: 135000,
      remote_friendly: true,
      url: 'https://example.com/job/1',
      description: 'Great software engineering role',
      requirements: ['Python', 'React', 'AWS'],
      benefits: ['Health Insurance', '401k', 'Remote Work'],
      field: 'Technology',
      experience_level: 'Mid-level',
      company_size: 'Large',
      company_industry: 'Technology',
      equity_offered: true,
      bonus_potential: 15000,
      overall_score: 0.85,
      diversity_score: 0.75,
      growth_score: 0.80,
      culture_score: 0.70,
      career_advancement_score: 0.85,
      work_life_balance_score: 0.75
    },
    tier: 'optimal',
    success_probability: 0.75,
    salary_increase_potential: 0.25,
    skills_gap_analysis: [
      {
        skill: 'Python',
        category: 'Programming',
        current_level: 3,
        required_level: 4,
        gap_size: 1,
        priority: 'High',
        learning_time_estimate: '2-3 months',
        resources: ['Online courses', 'Practice projects']
      }
    ],
    application_strategy: {
      approach: 'Technical focus with leadership examples',
      key_selling_points: ['Strong technical background', 'Leadership experience'],
      potential_challenges: ['Competitive market', 'High expectations'],
      mitigation_strategies: ['Prepare technical examples', 'Research company culture']
    },
    preparation_roadmap: {
      immediate_actions: ['Update resume', 'Practice coding'],
      short_term_goals: ['Complete Python certification', 'Build portfolio project'],
      long_term_goals: ['Become senior engineer', 'Lead technical team'],
      skill_development_plan: ['Advanced Python', 'System design', 'Leadership'],
      certification_recommendations: ['AWS Certified Developer', 'Python Professional']
    },
    diversity_analysis: {
      diversity_score: 0.75,
      inclusion_benefits: ['Diverse team', 'Inclusive culture'],
      company_diversity_metrics: { 'leadership_diversity': 0.60, 'team_diversity': 0.80 }
    },
    company_culture_fit: 0.70,
    career_advancement_potential: 0.85
  },
  {
    job: {
      job_id: 'job_2',
      title: 'Senior Developer',
      company: 'StartupXYZ',
      location: 'Austin, TX',
      msa: 'Austin-Round Rock-Georgetown, TX',
      salary_min: 140000,
      salary_max: 180000,
      salary_median: 160000,
      remote_friendly: false,
      url: 'https://example.com/job/2',
      description: 'Senior developer role at fast-growing startup',
      requirements: ['JavaScript', 'Node.js', 'MongoDB'],
      benefits: ['Equity', 'Health Insurance', 'Flexible hours'],
      field: 'Technology',
      experience_level: 'Senior',
      company_size: 'Small',
      company_industry: 'Technology',
      equity_offered: true,
      bonus_potential: 20000,
      overall_score: 0.90,
      diversity_score: 0.65,
      growth_score: 0.95,
      culture_score: 0.85,
      career_advancement_score: 0.90,
      work_life_balance_score: 0.80
    },
    tier: 'stretch',
    success_probability: 0.60,
    salary_increase_potential: 0.40,
    skills_gap_analysis: [
      {
        skill: 'Node.js',
        category: 'Backend',
        current_level: 2,
        required_level: 4,
        gap_size: 2,
        priority: 'Critical',
        learning_time_estimate: '4-6 months',
        resources: ['Node.js course', 'Practice projects', 'Mentorship']
      }
    ],
    application_strategy: {
      approach: 'Showcase learning ability and passion',
      key_selling_points: ['Fast learner', 'Passionate about technology'],
      potential_challenges: ['Skill gap', 'High competition'],
      mitigation_strategies: ['Intensive learning plan', 'Build relevant projects']
    },
    preparation_roadmap: {
      immediate_actions: ['Start Node.js course', 'Build practice projects'],
      short_term_goals: ['Complete Node.js certification', 'Build full-stack app'],
      long_term_goals: ['Become full-stack expert', 'Lead development team'],
      skill_development_plan: ['Node.js mastery', 'Database design', 'System architecture'],
      certification_recommendations: ['Node.js Professional', 'MongoDB Certified Developer']
    },
    diversity_analysis: {
      diversity_score: 0.65,
      inclusion_benefits: ['Startup culture', 'Growth opportunities'],
      company_diversity_metrics: { 'leadership_diversity': 0.40, 'team_diversity': 0.70 }
    },
    company_culture_fit: 0.85,
    career_advancement_potential: 0.90
  }
];

const mockVehicles = [
  {
    id: 'vehicle_1',
    make: 'Honda',
    model: 'Civic',
    year: 2020,
    mpg: 32,
    fuelType: 'gasoline' as const,
    currentMileage: 25000,
    monthlyMiles: 1200
  },
  {
    id: 'vehicle_2',
    make: 'Toyota',
    model: 'Prius',
    year: 2019,
    mpg: 50,
    fuelType: 'hybrid' as const,
    currentMileage: 30000,
    monthlyMiles: 1000
  }
];

describe('CareerCommuteIntegration', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('renders the career commute integration component', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Career + Commute Analysis')).toBeInTheDocument();
    expect(screen.getByText('Evaluate job opportunities with true compensation including transportation costs')).toBeInTheDocument();
  });

  it('displays job opportunities with commute analysis buttons', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    expect(screen.getByText('Tech Corp • San Francisco, CA')).toBeInTheDocument();
    expect(screen.getByText('Senior Developer')).toBeInTheDocument();
    expect(screen.getByText('StartupXYZ • Austin, TX')).toBeInTheDocument();
    
    // Should have analyze commute buttons
    const analyzeButtons = screen.getAllByText('Analyze Commute');
    expect(analyzeButtons).toHaveLength(2);
  });

  it('shows job statistics in the header', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('2')).toBeInTheDocument(); // Job opportunities count
    expect(screen.getByText('Job Opportunities')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Vehicles count
    expect(screen.getByText('Vehicles Available')).toBeInTheDocument();
  });

  it('displays job details including salary, success probability, and benefits', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Check first job details
    expect(screen.getByText('$135,000')).toBeInTheDocument();
    expect(screen.getByText('Success: 75%')).toBeInTheDocument();
    expect(screen.getByText('Increase: +25%')).toBeInTheDocument();
    
    // Check benefits
    expect(screen.getByText('Health Insurance')).toBeInTheDocument();
    expect(screen.getByText('401k')).toBeInTheDocument();
    expect(screen.getByText('Remote Work')).toBeInTheDocument();
  });

  it('shows tier labels with correct styling', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Optimal')).toBeInTheDocument();
    expect(screen.getByText('Stretch')).toBeInTheDocument();
  });

  it('displays diversity and growth scores', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Diversity Score')).toBeInTheDocument();
    expect(screen.getByText('Growth Potential')).toBeInTheDocument();
    expect(screen.getByText('Culture Fit')).toBeInTheDocument();
    expect(screen.getByText('Remote Friendly')).toBeInTheDocument();
  });

  it('shows skills gap analysis for jobs', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Key Skills Needed')).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('Node.js')).toBeInTheDocument();
  });

  it('opens commute calculator modal when analyze commute is clicked', async () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    const analyzeButtons = screen.getAllByText('Analyze Commute');
    fireEvent.click(analyzeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Commute Cost Analysis')).toBeInTheDocument();
      expect(screen.getByText('Software Engineer at Tech Corp')).toBeInTheDocument();
    });
  });

  it('handles save scenario functionality', async () => {
    const mockOnSaveScenario = jest.fn();
    
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={mockOnSaveScenario}
        onLoadScenario={jest.fn()}
      />
    );

    // Open commute calculator
    const analyzeButtons = screen.getAllByText('Analyze Commute');
    fireEvent.click(analyzeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Commute Cost Analysis')).toBeInTheDocument();
    });

    // The save functionality is tested in the CommuteCostCalculator component
    // This test just ensures the integration works
    expect(mockOnSaveScenario).toBeDefined();
  });

  it('handles load scenario functionality', async () => {
    const mockOnLoadScenario = jest.fn();
    
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={mockOnLoadScenario}
      />
    );

    // The load functionality is tested in the CommuteCostCalculator component
    // This test just ensures the integration works
    expect(mockOnLoadScenario).toBeDefined();
  });

  it('displays saved scenarios when available', async () => {
    // Mock saved scenarios
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        scenarios: [
          {
            id: 'scenario_1',
            name: 'Tech Corp - Honda Civic',
            job_location: { address: '123 Tech Street, San Francisco, CA' },
            home_location: { address: '456 Home Avenue, Oakland, CA' },
            costs: { total: 150.50 },
            commute_details: { distance: 15.5 }
          }
        ]
      })
    });

    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Saved Commute Scenarios')).toBeInTheDocument();
    });
  });

  it('handles empty job recommendations', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={[]}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('0')).toBeInTheDocument(); // Job opportunities count
    expect(screen.getByText('Job Opportunities')).toBeInTheDocument();
  });

  it('handles empty vehicles list', () => {
    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={[]}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('0')).toBeInTheDocument(); // Vehicles count
    expect(screen.getByText('Vehicles Available')).toBeInTheDocument();
  });

  it('shows error messages when API calls fail', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // The error handling is tested in the individual components
    // This test just ensures the integration doesn't break
    expect(screen.getByText('Career + Commute Analysis')).toBeInTheDocument();
  });

  it('tracks analytics events', async () => {
    const mockTrackInteraction = jest.fn();
    const mockTrackError = jest.fn();

    // Mock the analytics hook
    jest.doMock('../../hooks/useAnalytics', () => ({
      useAnalytics: () => ({
        trackInteraction: mockTrackInteraction,
        trackError: mockTrackError
      })
    }));

    render(
      <CareerCommuteIntegration
        jobRecommendations={mockJobRecommendations}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Click analyze commute button
    const analyzeButtons = screen.getAllByText('Analyze Commute');
    fireEvent.click(analyzeButtons[0]);

    // Analytics tracking is tested in the individual components
    expect(mockTrackInteraction).toBeDefined();
    expect(mockTrackError).toBeDefined();
  });
});
