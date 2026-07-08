import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import SideIncomeAccelerator from '../SideIncomeAccelerator';
import * as integrationAPI from '../../api/integrationAPI';
import * as sideIncomeAPI from '../../api/sideIncomeAPI';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    getAccessToken: () => 'test-token',
    isAuthenticated: true,
    user: { id: 'user-1', email: 'test@example.com' },
    loading: false,
  }),
}));

jest.mock('../../api/sideIncomeAPI');
jest.mock('../../api/integrationAPI');

const mockResponse: sideIncomeAPI.SideIncomeResponse = {
  matches: [
    {
      title: 'Freelance Design',
      type: 'freelance',
      hourly_range: '$50-80/hr',
      hours_per_week: 10,
      monthly_income: 1200,
      schedule_fit: 'Remote, flexible',
      why_it_fits: 'Leverages design skills',
      first_step: 'Create portfolio',
      startup_cost: '$0-500',
      icc_impact: {
        closes_monthly_gap: true,
        gap_coverage_pct: 120,
        timeline_acceleration_months: 7,
      },
      interim_housing_combo: {
        new_gap_with_roommate: 0,
        months_to_startup_with_roommate: 4,
      },
    },
    {
      title: 'Retail Shift',
      type: 'part_time',
      hourly_range: '$18-22/hr',
      hours_per_week: 15,
      monthly_income: 900,
      schedule_fit: 'Evenings',
      why_it_fits: 'Fast to start',
      first_step: 'Apply locally',
      startup_cost: '$0',
      icc_impact: {
        closes_monthly_gap: false,
        gap_coverage_pct: 90,
        timeline_acceleration_months: 9,
      },
      interim_housing_combo: {
        new_gap_with_roommate: 0,
        months_to_startup_with_roommate: 5,
      },
    },
    {
      title: 'Weekend Tutor',
      type: 'gig',
      hourly_range: '$30-45/hr',
      hours_per_week: 10,
      monthly_income: 600,
      schedule_fit: 'Weekends',
      why_it_fits: 'Uses teaching skills',
      first_step: 'Sign up online',
      startup_cost: '$0-100',
      icc_impact: {
        closes_monthly_gap: false,
        gap_coverage_pct: 60,
        timeline_acceleration_months: 11,
      },
      interim_housing_combo: {
        new_gap_with_roommate: 100,
        months_to_startup_with_roommate: 8,
      },
    },
  ],
  recommendation: {
    title: 'Freelance Design',
    type: 'freelance',
    hourly_range: '$50-80/hr',
    hours_per_week: 10,
    monthly_income: 1200,
    schedule_fit: 'Remote, flexible',
    why_it_fits: 'Leverages design skills',
    first_step: 'Create portfolio',
    startup_cost: '$0-500',
    icc_impact: {
      closes_monthly_gap: true,
      gap_coverage_pct: 120,
      timeline_acceleration_months: 7,
    },
    interim_housing_combo: {
      new_gap_with_roommate: 0,
      months_to_startup_with_roommate: 4,
    },
  },
  context: {
    relationship_exit_urgency: 'medium',
    timeline_pressure: '12_months',
    total_monthly_gap: 1000,
    startup_cost: 6000,
  },
};

function renderAccelerator(onJobSelected = jest.fn()) {
  return render(
    <MemoryRouter>
      <SideIncomeAccelerator
        monthlyGap={1000}
        startupCostNeeded={6000}
        timelineMonths={12}
        iccAssessmentId="11111111-1111-1111-1111-111111111111"
        partnerId="22222222-2222-2222-2222-222222222222"
        onJobSelected={onJobSelected}
      />
    </MemoryRouter>,
  );
}

describe('SideIncomeAccelerator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (sideIncomeAPI.getSideIncomeRecommendations as jest.Mock).mockResolvedValue(mockResponse);
    (integrationAPI.createIccToDf1Handoff as jest.Mock).mockResolvedValue({
      success: true,
      commitment_id: '33333333-3333-3333-3333-333333333333',
      handoff_url: '/dashboard/tools?tab=debt&subTab=second-job',
      message: 'Great! You selected Freelance Design.',
    });
  });

  it('shows intake form on mount', () => {
    renderAccelerator();
    expect(screen.getByText(/how much time can you spare/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /see side income options/i })).toBeInTheDocument();
  });

  it('fetches recommendations after intake submit', async () => {
    renderAccelerator();
    await userEvent.click(screen.getByRole('button', { name: /see side income options/i }));

    await waitFor(() => {
      expect(sideIncomeAPI.getSideIncomeRecommendations).toHaveBeenCalled();
    });

    expect(await screen.findByText(/freelance design/i)).toBeInTheDocument();
  });

  it('calls handoff API and navigates when Get Started is clicked', async () => {
    const onJobSelected = jest.fn();
    renderAccelerator(onJobSelected);
    await userEvent.click(screen.getByRole('button', { name: /see side income options/i }));
    const buttons = await screen.findAllByRole('button', { name: /get started/i });
    await userEvent.click(buttons[0]);

    await waitFor(() => {
      expect(integrationAPI.createIccToDf1Handoff).toHaveBeenCalledWith(
        expect.objectContaining({
          selectedJob: 'Freelance Design',
          targetMonthlyIncome: 1200,
          gapCoveragePct: 120,
        }),
        expect.any(Object),
      );
    });
    expect(onJobSelected).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/tools?tab=debt&subTab=second-job');
  });

  it('shows error on handoff failure without navigating', async () => {
    (integrationAPI.createIccToDf1Handoff as jest.Mock).mockRejectedValue(
      new Error('handoff failed'),
    );
    renderAccelerator();
    await userEvent.click(screen.getByRole('button', { name: /see side income options/i }));
    const buttons = await screen.findAllByRole('button', { name: /get started/i });
    await userEvent.click(buttons[0]);
    expect(await screen.findByRole('alert')).toHaveTextContent(/handoff failed/i);
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
