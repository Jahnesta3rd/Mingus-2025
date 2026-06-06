import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import RecommendationTiers from '../RecommendationTiers';

jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackInteraction: jest.fn(),
    trackError: jest.fn(),
    getSessionId: jest.fn(() => 'test-session'),
    getUserId: jest.fn(() => 'test-user'),
  }),
}));

const mockLogout = jest.fn();
const mockGetAccessToken = jest.fn(() => 'test-jwt-token');

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    userTier: null,
    loading: false,
    user: null,
    isAuthenticated: false,
    getAccessToken: mockGetAccessToken,
    logout: mockLogout,
  }),
}));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

const emptyRecommendations = {
  success: true,
  recommendations: { same_level: [], reach: [], conservative: [] },
};

beforeEach(() => {
  mockLogout.mockClear();
  mockGetAccessToken.mockReturnValue('test-jwt-token');
  global.fetch = jest.fn().mockImplementation((url: string) => {
    if (String(url).includes('/api/career/income-percentile')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ status: 'no_career_data' }),
      } as Response);
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => emptyRecommendations,
    } as Response);
  });
});

function renderTiers(props: React.ComponentProps<typeof RecommendationTiers>) {
  return render(
    <MemoryRouter>
      <RecommendationTiers {...props} />
    </MemoryRouter>
  );
}

describe('RecommendationTiers', () => {
  it('shows budget upsell when userTier is budget', async () => {
    renderTiers({ userTier: 'budget' });

    await waitFor(() => {
      expect(screen.getByText('Unlock Personalized Job Recommendations')).toBeInTheDocument();
    });
    expect(screen.getByText('Upgrade to Mid-Tier')).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalledWith(
      '/api/recommendations/process-resume',
      expect.anything()
    );
    expect(screen.queryByText('Healthcare Technology Solutions')).not.toBeInTheDocument();
  });

  it('shows profile prompt for mid tier without career profile', async () => {
    renderTiers({ userTier: 'mid_tier' });

    await waitFor(() => {
      expect(screen.getByText('Complete Your Career Profile')).toBeInTheDocument();
    });
    expect(screen.getByText('Complete Profile')).toBeInTheDocument();
  });

  it('shows holding state for professional tier with complete profile', async () => {
    renderTiers({
      userTier: 'professional',
      careerProfile: { current_role: 'Program Manager', industry: 'Government' },
    });

    await waitFor(() => {
      expect(screen.getByText('Sourcing Roles for You')).toBeInTheDocument();
    });
    expect(screen.getByText(/We are sourcing roles that match your profile/)).toBeInTheDocument();
    expect(screen.queryByText('Senior Marketing Coordinator')).not.toBeInTheDocument();
  });

  it('does not send Authorization when getAccessToken returns ok placeholder', async () => {
    mockGetAccessToken.mockReturnValue('ok');
    renderTiers({
      userTier: 'professional',
      careerProfile: { current_role: 'Engineer', industry: 'Technology' },
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    const init = (global.fetch as jest.Mock).mock.calls[0][1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
    expect(init.credentials).toBe('include');
  });

  it('renders tier job titles when API returns recommendations', async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes('/api/career/income-percentile')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ status: 'no_career_data' }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          recommendations: {
            conservative: [
              {
                job_id: '1',
                title: 'Staff Software Engineer',
                company: 'Acme Corp',
                seniority_level: 'senior',
                salary_min: 140000,
                salary_max: 180000,
                advancement_trajectory: 'Principal Engineer',
              },
            ],
            same_level: [],
            reach: [],
          },
        }),
      });
    });

    renderTiers({
      userTier: 'professional',
      careerProfile: { current_role: 'Engineer', industry: 'Technology' },
    });

    await waitFor(() => {
      expect(screen.getByText('Staff Software Engineer')).toBeInTheDocument();
    });
    expect(screen.getByText('Safe Moves')).toBeInTheDocument();
    expect(screen.getByText('Next step:')).toBeInTheDocument();
    expect(screen.getByText('Principal Engineer')).toBeInTheDocument();
  });

  it('shows income standing banner and upward percentile chip when percentile data is available', async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes('/api/career/income-percentile')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            status: 'ok',
            bls_career_field: 'Technology',
            current_salary: 85000,
            percentile_bracket: 25,
            percentile_label: '25th–50th percentile',
            percentiles: { p10: 52000, p25: 68000, p50: 104900, p75: 136000, p90: 174000 },
            zip_missing: true,
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          recommendations: {
            conservative: [
              {
                job_id: '1',
                title: 'Staff Software Engineer',
                company: 'Acme Corp',
                seniority_level: 'senior',
                salary_min: 140000,
                salary_max: 180000,
                salary_median: 150000,
                advancement_trajectory: 'Principal Engineer',
              },
            ],
            same_level: [],
            reach: [],
          },
        }),
      });
    });

    renderTiers({
      userTier: 'professional',
      careerProfile: { current_role: 'Engineer', industry: 'Technology' },
    });

    await waitFor(() => {
      expect(screen.getByText(/You're currently in the/)).toBeInTheDocument();
    });
    expect(screen.getByText('25th–50th percentile')).toBeInTheDocument();
    expect(screen.getByText('Add your zip for local data →')).toBeInTheDocument();
    expect(screen.getByText('↑ Moves you to 75th–90th percentile')).toBeInTheDocument();
  });
});
