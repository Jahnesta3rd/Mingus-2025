import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { RecommendationsWithFeatures } from './RecommendationsWithFeatures.jsx';

const basePath = {
  pathId: 'career_advancement',
  title: 'Career Advancement',
  description: 'Get promoted to Senior Engineer',
  monthlyBoost: 2500,
  timeline: '3-6 months',
  feasibility: 'Medium',
  pros: ['Higher base salary'],
  cons: ['Requires interview prep'],
  actionItems: ['Update resume'],
  projections: [{ year: 1, cumulativeSavings: 12000, goalReached: false }],
  mostRealistic: true,
};

const secondPath = {
  ...basePath,
  pathId: 'side_income',
  title: 'Side Income',
  description: 'Freelance on evenings',
  mostRealistic: false,
};

const defaultProps = {
  goal: { type: 'home_purchase', timeline: 5 },
  analysis: {
    summary: 'Buy a home in 5 years.',
    goalType: 'home_purchase',
    gaps: {
      monthlyToSave: 1200,
      savingsGap: 60000,
      incomeGap: 15000,
      feasible: false,
    },
  },
  recommendations: {
    paths: [basePath, secondPath],
    selectedPath: 'career_advancement',
  },
  jobSuggestions: {
    byPathId: {
      career_advancement: {
        jobs: [{ jobId: 'j1', title: 'Senior Engineer', expectedSalary: 140000, incomeIncrease: 20000 }],
      },
    },
    global: null,
  },
  gigSuggestions: { byPathId: {}, global: null },
  expenseSuggestions: {
    byPathId: {
      career_advancement: {
        suggestions: [
          { suggestionId: 'e1', categoryId: 'dining', title: 'Eat out less', monthlySavings: 150 },
          { suggestionId: 'e2', categoryId: 'housing', title: 'Refinance', monthlySavings: 300 },
        ],
      },
    },
    global: null,
  },
  selectedPathId: 'career_advancement',
  onSelectPath: jest.fn(),
  trackedExpenseCategories: ['dining'],
};

function renderRecommendations(overrides = {}) {
  return render(
    <MemoryRouter>
      <RecommendationsWithFeatures {...defaultProps} {...overrides} />
    </MemoryRouter>,
  );
}

describe('RecommendationsWithFeatures', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders goal summary and gap metrics', () => {
    renderRecommendations();

    expect(screen.getByText('Buy a home in 5 years.')).toBeInTheDocument();
    expect(screen.getByText('$1,200')).toBeInTheDocument();
    expect(screen.getByText('Needs a plan')).toBeInTheDocument();
  });

  it('renders recommendation path cards', () => {
    renderRecommendations();

    const pathList = screen.getByRole('list', { name: /recommendation paths/i });
    expect(within(pathList).getByText(/career advancement/i)).toBeInTheDocument();
    expect(within(pathList).getByText(/side income/i)).toBeInTheDocument();
    expect(screen.getAllByText(/recommended/i).length).toBeGreaterThan(0);
  });

  it('shows module links and filtered expense cuts for expanded path', () => {
    renderRecommendations();

    expect(screen.getByRole('link', { name: /job recommendations/i })).toHaveAttribute(
      'href',
      '/dashboard/tools?tab=discover',
    );
    expect(screen.getByText(/eat out less/i)).toBeInTheDocument();
    expect(screen.queryByText(/refinance/i)).not.toBeInTheDocument();
    expect(screen.getByText(/your tracked categories/i)).toBeInTheDocument();
  });

  it('calls onSelectPath when another path is expanded', async () => {
    const user = userEvent.setup();
    const onSelectPath = jest.fn();
    renderRecommendations({ onSelectPath });

    const pathList = screen.getByRole('list', { name: /recommendation paths/i });
    await user.click(within(pathList).getByRole('button', { name: /side income/i }));

    expect(onSelectPath).toHaveBeenCalledWith('side_income');
  });

  it('returns null when there are no paths', () => {
    const { container } = renderRecommendations({ recommendations: { paths: [] } });
    expect(container).toBeEmptyDOMElement();
  });
});
