import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimelineProjection from './TimelineProjection.jsx';

jest.mock('recharts', () => {
  const OriginalResponsiveContainer = jest.requireActual('recharts').ResponsiveContainer;

  return {
    ...jest.requireActual('recharts'),
    ResponsiveContainer: ({ children, width, height }) => (
      <OriginalResponsiveContainer width={width ?? '100%'} height={height ?? 400}>
        {children}
      </OriginalResponsiveContainer>
    ),
  };
});

const goal = { timeline: 5, totalNeeded: 97000 };
const analysis = {
  futureState: { savingsTarget: 97000, timelineYears: 5 },
  presentState: { savings: 25000 },
};

const paths = [
  {
    pathId: 'career_advancement',
    title: 'Career Advancement',
    monthlyBoost: 1500,
    feasibility: 'Medium',
    projections: [
      { year: 1, cumulativeSavings: 43000, goalReached: false },
      { year: 2, cumulativeSavings: 61000, goalReached: false },
      { year: 3, cumulativeSavings: 79000, goalReached: false },
      { year: 4, cumulativeSavings: 97000, goalReached: true },
    ],
  },
  {
    pathId: 'side_income',
    title: 'Side Income',
    monthlyBoost: 1000,
    feasibility: 'High',
    projections: [
      { year: 1, cumulativeSavings: 37000, goalReached: false },
      { year: 2, cumulativeSavings: 49000, goalReached: false },
    ],
  },
  {
    pathId: 'combined',
    title: 'Combined Strategy',
    monthlyBoost: 2200,
    feasibility: 'Very High',
    mostRealistic: true,
    projections: [
      { year: 1, cumulativeSavings: 51400, goalReached: false },
      { year: 2, cumulativeSavings: 77800, goalReached: false },
      { year: 3, cumulativeSavings: 104200, goalReached: true },
    ],
  },
];

describe('TimelineProjection', () => {
  it('renders chart and metrics for three paths', () => {
    render(
      <TimelineProjection
        goal={goal}
        paths={paths}
        analysis={analysis}
        currentSavings={25000}
      />,
    );

    expect(screen.getByRole('heading', { name: /savings timeline/i })).toBeInTheDocument();
    expect(screen.getByTestId('timeline-chart-wrap')).toBeInTheDocument();
    expect(screen.getAllByText(/career advancement/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/side income/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/combined strategy/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/recommended/i).length).toBeGreaterThan(0);
  });

  it('calls onSelectPath when a metric card is clicked', async () => {
    const user = userEvent.setup();
    const onSelectPath = jest.fn();

    render(
      <TimelineProjection
        goal={goal}
        paths={paths}
        analysis={analysis}
        currentSavings={25000}
        selectedPathId="career_advancement"
        onSelectPath={onSelectPath}
      />,
    );

    await user.click(screen.getAllByRole('button', { name: /side income/i })[0]);
    expect(onSelectPath).toHaveBeenCalledWith('side_income');
  });

  it('toggles legend visibility and keeps selected path highlight', async () => {
    const user = userEvent.setup();
    const onSelectPath = jest.fn();

    render(
      <TimelineProjection
        goal={goal}
        paths={paths}
        analysis={analysis}
        currentSavings={25000}
        selectedPathId="combined"
        onSelectPath={onSelectPath}
      />,
    );

    const legend = screen.getByRole('list', { name: /path legend/i });
    const legendButton = within(legend).getByRole('listitem', { name: /career advancement/i });
    await user.click(legendButton);
    expect(onSelectPath).toHaveBeenCalledWith('career_advancement');
    expect(legendButton.className).toMatch(/legendItemHidden/);
  });

  it('renders empty state when no paths are provided', () => {
    render(<TimelineProjection goal={goal} paths={[]} analysis={analysis} />);
    expect(screen.getByText(/projection data will appear/i)).toBeInTheDocument();
  });

  it('supports different goal timelines in summary copy', () => {
    render(
      <TimelineProjection
        goal={{ timeline: 8 }}
        paths={paths}
        analysis={{ ...analysis, futureState: { savingsTarget: 97000, timelineYears: 8 } }}
        currentSavings={25000}
      />,
    );

    expect(screen.getByText(/8 years/i)).toBeInTheDocument();
  });

  it('uses responsive chart container dimensions', () => {
    render(
      <TimelineProjection
        goal={goal}
        paths={paths}
        analysis={analysis}
        currentSavings={25000}
      />,
    );

    const wrap = screen.getByTestId('timeline-chart-wrap');
    expect(wrap).toHaveClass('chartWrap');
  });
});
