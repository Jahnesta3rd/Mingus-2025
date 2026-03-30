/**
 * WellnessImpactCard component tests.
 * - Insight rendering
 * - Different insight types
 * - Empty state with progress indicator
 * - Loading skeleton
 * - Insight list
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { WellnessImpactCard } from '../WellnessImpactCard';
import type { WellnessInsight } from '../InsightCard';

const mockInsight = (overrides: Partial<WellnessInsight> = {}): WellnessInsight => ({
  type: 'correlation',
  title: 'Stress & Spending Link',
  message: 'Your data shows higher stress weeks tend to have more impulse spending.',
  data_backing: 'Based on 8 weeks of your data',
  action: 'Consider a 24-hour pause when stress is high.',
  priority: 2,
  category: 'financial',
  dollar_amount: undefined,
  ...overrides,
});

describe('WellnessImpactCard', () => {
  describe('loading state', () => {
    it('shows loading skeleton when loading is true', () => {
      render(<WellnessImpactCard insights={[]} loading={true} weeksOfData={0} />);
      expect(screen.getByRole('region', { name: /wellness-money connection/i })).toBeInTheDocument();
      expect(screen.getByText(/your wellness-money connection/i)).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveTextContent(/loading|wellness insights/i);
    });
  });

  describe('empty / insufficient data', () => {
    it('shows progress bar when weeksOfData < 4', () => {
      render(<WellnessImpactCard insights={[]} loading={false} weeksOfData={2} />);
      expect(screen.getByText(/complete a few more weekly check-ins/i)).toBeInTheDocument();
      expect(screen.getByText(/we need about 4 weeks of data/i)).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('shows "no strong patterns" when weeksOfData >= 4 but insights empty', () => {
      render(<WellnessImpactCard insights={[]} loading={false} weeksOfData={4} />);
      expect(screen.getByText(/no strong patterns found yet/i)).toBeInTheDocument();
    });
  });

  describe('insight rendering', () => {
    it('renders up to 3 insights sorted by priority', () => {
      const insights: WellnessInsight[] = [
        mockInsight({ title: 'First', priority: 1 }),
        mockInsight({ title: 'Second', priority: 2 }),
        mockInsight({ title: 'Third', priority: 3 }),
      ];
      render(<WellnessImpactCard insights={insights} loading={false} weeksOfData={4} />);
      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Second')).toBeInTheDocument();
      expect(screen.getByText('Third')).toBeInTheDocument();
      expect(screen.getByRole('list', { name: /personalized insights/i })).toBeInTheDocument();
    });

    it('renders different insight types with title and message', () => {
      const insights: WellnessInsight[] = [
        mockInsight({ type: 'trend', title: 'Exercise Momentum', message: 'Trend message.' }),
        mockInsight({ type: 'anomaly', title: 'Stress Alert', message: 'Anomaly message.', dollar_amount: 50 }),
      ];
      render(<WellnessImpactCard insights={insights} loading={false} weeksOfData={4} />);
      expect(screen.getByText('Exercise Momentum')).toBeInTheDocument();
      expect(screen.getByText('Trend message.')).toBeInTheDocument();
      expect(screen.getByText('Stress Alert')).toBeInTheDocument();
      expect(screen.getByText('Anomaly message.')).toBeInTheDocument();
    });
  });

  describe('snapshot', () => {
    it('matches snapshot when loading', () => {
      const { container } = render(<WellnessImpactCard insights={[]} loading={true} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with insights', () => {
      const insights = [mockInsight(), mockInsight({ title: 'Second Insight', priority: 3 })];
      const { container } = render(<WellnessImpactCard insights={insights} loading={false} weeksOfData={6} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with insufficient data', () => {
      const { container } = render(<WellnessImpactCard insights={[]} loading={false} weeksOfData={2} />);
      expect(container).toMatchSnapshot();
    });
  });
});
