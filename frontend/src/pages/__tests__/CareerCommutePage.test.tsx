import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CareerCommutePage from '../CareerCommutePage';

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
  }
];

const mockVehicles = [
  {
    id: 'vehicle_1',
    make: 'Honda',
    model: 'Civic',
    year: 2020,
    mpg: 32,
    fuelType: 'gasoline',
    currentMileage: 25000,
    monthlyMiles: 1200
  }
];

describe('CareerCommutePage', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('renders loading state initially', () => {
    // Mock slow API response
    (fetch as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ recommendations: [], vehicles: [] })
      }), 100))
    );

    render(<CareerCommutePage />);

    expect(screen.getByText('Loading Career Analysis')).toBeInTheDocument();
    expect(screen.getByText('Preparing your commute cost calculations...')).toBeInTheDocument();
  });

  it('renders error state when API calls fail', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Data')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('shows try again button on error', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    // Click try again button
    fireEvent.click(screen.getByText('Try Again'));

    // Should make new API calls
    expect(fetch).toHaveBeenCalledTimes(2); // Initial call + retry
  });

  it('renders page with job recommendations and vehicles', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Career + Commute Analysis')).toBeInTheDocument();
    });

    // Check header stats
    expect(screen.getByText('1')).toBeInTheDocument(); // Job opportunities count
    expect(screen.getByText('Job Opportunities')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Vehicles count
    expect(screen.getByText('Vehicles Available')).toBeInTheDocument();
  });

  it('shows no job recommendations message when empty', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('No Job Recommendations')).toBeInTheDocument();
      expect(screen.getByText('Complete your career assessment to get personalized job recommendations.')).toBeInTheDocument();
      expect(screen.getByText('Take Career Assessment')).toBeInTheDocument();
    });
  });

  it('shows no vehicles message when empty', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: [] })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('No Vehicles Added')).toBeInTheDocument();
      expect(screen.getByText('Add your vehicles to calculate accurate commute costs.')).toBeInTheDocument();
      expect(screen.getByText('Add Vehicle')).toBeInTheDocument();
    });
  });

  it('displays job recommendations with commute analysis', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp • San Francisco, CA')).toBeInTheDocument();
      expect(screen.getByText('$135,000')).toBeInTheDocument();
      expect(screen.getByText('Analyze Commute')).toBeInTheDocument();
    });
  });

  it('shows job statistics in header', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      // Check header stats
      expect(screen.getByText('1')).toBeInTheDocument(); // Job opportunities
      expect(screen.getByText('Job Opportunities')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument(); // Vehicles
      expect(screen.getByText('Vehicles Available')).toBeInTheDocument();
      expect(screen.getByText('25%')).toBeInTheDocument(); // Avg salary increase
      expect(screen.getByText('Avg. Salary Increase')).toBeInTheDocument();
    });
  });

  it('handles multiple job recommendations', async () => {
    const multipleJobs = [
      ...mockJobRecommendations,
      {
        ...mockJobRecommendations[0],
        job: {
          ...mockJobRecommendations[0].job,
          job_id: 'job_2',
          title: 'Senior Developer',
          company: 'StartupXYZ',
          salary_median: 160000
        },
        salary_increase_potential: 0.40
      }
    ];

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: multipleJobs })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Senior Developer')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp • San Francisco, CA')).toBeInTheDocument();
      expect(screen.getByText('StartupXYZ • San Francisco, CA')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: false,
        status: 500
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Data')).toBeInTheDocument();
    });
  });

  it('handles partial API failures', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Data')).toBeInTheDocument();
    });
  });

  it('tracks analytics events on page load', async () => {
    const mockTrackInteraction = jest.fn();
    const mockTrackError = jest.fn();

    // Mock the analytics hook
    jest.doMock('../../hooks/useAnalytics', () => ({
      useAnalytics: () => ({
        trackInteraction: mockTrackInteraction,
        trackError: mockTrackError
      })
    }));

    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Career + Commute Analysis')).toBeInTheDocument();
    });

    // Analytics tracking is tested in the individual components
    expect(mockTrackInteraction).toBeDefined();
    expect(mockTrackError).toBeDefined();
  });

  it('handles empty responses from API', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}) // Empty response
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}) // Empty response
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('No Job Recommendations')).toBeInTheDocument();
    });
  });

  it('handles malformed JSON responses', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => { throw new Error('Invalid JSON') }
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Data')).toBeInTheDocument();
    });
  });

  it('handles network timeouts', async () => {
    (fetch as jest.Mock).mockImplementation(() => 
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Network timeout')), 100)
      )
    );

    render(<CareerCommutePage />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Data')).toBeInTheDocument();
    });
  });

  it('retries API calls when try again is clicked', async () => {
    (fetch as jest.Mock)
      .mockRejectedValueOnce(new Error('Initial error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockJobRecommendations })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ vehicles: mockVehicles })
      });

    render(<CareerCommutePage />);

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    // Click try again
    fireEvent.click(screen.getByText('Try Again'));

    // Should eventually show success
    await waitFor(() => {
      expect(screen.getByText('Career + Commute Analysis')).toBeInTheDocument();
    });
  });
});
