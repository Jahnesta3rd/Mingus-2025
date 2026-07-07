import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

jest.mock('../hooks/useGoalAnalysis.js', () => ({
  __esModule: true,
  default: jest.fn(),
  mapEnrichmentToPaths: jest.fn(),
  clearGoalAnalysisCache: jest.fn(),
}));
jest.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@example.com' },
    getAccessToken: () => 'token',
  }),
}));
jest.mock('../utils/profileBuilder.js', () => ({
  __esModule: true,
  buildGoalAnalysisProfile: jest.fn().mockResolvedValue({
    id: 'user-1',
    income: 8000,
    savings: 25000,
    expenses: 5200,
    jobTitle: 'Engineer',
    industry: 'Technology',
    skills: ['JavaScript'],
    availableHours: 10,
  }),
}));

import GoalPlanningTab from './GoalPlanningTab';
import useGoalAnalysis from '../hooks/useGoalAnalysis.js';

const mockedUseGoalAnalysis = useGoalAnalysis as jest.MockedFunction<typeof useGoalAnalysis>;

const mockAnalyzeGoal = jest.fn();
const mockSelectPath = jest.fn();
const mockClear = jest.fn();

const idleHookState = {
  status: 'idle' as const,
  goalAnalysis: null,
  recommendations: { paths: [], selectedPath: null, source: null, generatedAt: null },
  jobSuggestions: { global: null, byPathId: {} },
  gigSuggestions: { global: null, byPathId: {} },
  expenseSuggestions: { global: null, byPathId: {} },
  error: null,
  progress: null,
  analyzeGoal: mockAnalyzeGoal,
  selectRecommendationPath: mockSelectPath,
  clearAnalysis: mockClear,
};

function renderTab() {
  return render(
    <MemoryRouter>
      <GoalPlanningTab />
    </MemoryRouter>,
  );
}

describe('GoalPlanningTab', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseGoalAnalysis.mockReturnValue(idleHookState);
  });

  it('renders GoalForm after profile loads', async () => {
    renderTab();
    expect(await screen.findByText(/what's your financial goal/i)).toBeInTheDocument();
  });

  it('shows recommendations when analysis completes', async () => {
    mockedUseGoalAnalysis.mockReturnValue({
      ...idleHookState,
      status: 'complete',
      goalAnalysis: {
        goalType: 'home_purchase',
        gaps: { monthlyToSave: 1000, savingsGap: 50000, incomeGap: 12000, feasible: false },
        summary: 'Buy a home in 5 years.',
      },
      recommendations: {
        paths: [
          {
            pathId: 'combined',
            title: 'Combined Strategy',
            mostRealistic: true,
            monthlyBoost: 2000,
            timeline: '6-12 months',
            feasibility: 'High',
            description: 'Mix strategies',
            pros: ['Balanced'],
            cons: ['Takes effort'],
            actionItems: [],
          },
        ],
        selectedPath: 'combined',
        source: 'fallback',
        generatedAt: null,
      },
    });

    renderTab();

    expect(await screen.findByRole('heading', { name: /your path to this goal/i })).toBeInTheDocument();
    expect(screen.getAllByText(/combined strategy/i).length).toBeGreaterThan(0);
  });

  it('calls analyzeGoal when form is submitted', async () => {
    const user = userEvent.setup();
    renderTab();

    await screen.findByText(/what's your financial goal/i);
    await user.selectOptions(screen.getByLabelText(/select goal type/i), 'home_purchase');
    await user.type(screen.getByLabelText(/target home price/i), '400000');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze my path/i })).not.toBeDisabled();
    });

    await user.click(screen.getByRole('button', { name: /analyze my path/i }));

    await waitFor(() => {
      expect(mockAnalyzeGoal).toHaveBeenCalled();
    });
  });
});
