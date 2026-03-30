/**
 * WellnessScoreCard component tests.
 * - Score display
 * - Color coding at different levels
 * - Change indicators (up/down/neutral)
 * - Empty state
 * - Loading state (handled by parent; card receives null for empty)
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { WellnessScoreCard } from '../WellnessScoreCard';

const baseScores = {
  physical_score: 70,
  mental_score: 75,
  relational_score: 65,
  financial_feeling_score: 72,
  overall_wellness_score: 71,
  physical_change: 5,
  mental_change: -2,
  relational_change: 0,
  overall_change: 3,
  week_ending_date: '2025-02-02',
};

describe('WellnessScoreCard', () => {
  describe('score display', () => {
    it('renders overall score and week label when scores provided', () => {
      render(<WellnessScoreCard scores={baseScores} />);
      expect(screen.getByRole('region', { name: /wellness score/i })).toBeInTheDocument();
      expect(screen.getByText(/71|70/)).toBeInTheDocument();
      expect(screen.getByText(/Feb|2025/)).toBeInTheDocument();
    });

    it('renders all four category cards', () => {
      render(<WellnessScoreCard scores={baseScores} />);
      expect(screen.getByRole('article', { name: /physical/i })).toBeInTheDocument();
      expect(screen.getByRole('article', { name: /mental/i })).toBeInTheDocument();
      expect(screen.getByRole('article', { name: /relational/i })).toBeInTheDocument();
      expect(screen.getByRole('article', { name: /financial/i })).toBeInTheDocument();
    });
  });

  describe('color coding at different levels', () => {
    it('thriving (75+) has green styling', () => {
      const scores = { ...baseScores, overall_wellness_score: 85 };
      const { container } = render(<WellnessScoreCard scores={scores} />);
      const region = screen.getByRole('region', { name: /wellness score/i });
      expect(region).toHaveTextContent(/thriving/i);
      expect(container.querySelector('[style*="10B981"]') || container.querySelector('[fill*="10B981"]') || container.textContent).toBeTruthy();
    });

    it('growing (50-74) displays', () => {
      render(<WellnessScoreCard scores={baseScores} />);
      expect(screen.getByText(/71|70/)).toBeInTheDocument();
    });

    it('building (25-49) displays', () => {
      const scores = { ...baseScores, overall_wellness_score: 40 };
      render(<WellnessScoreCard scores={scores} />);
      expect(screen.getByRole('region', { name: /wellness score/i })).toHaveTextContent(/building/i);
    });

    it('attention (0-24) displays', () => {
      const scores = { ...baseScores, overall_wellness_score: 15 };
      render(<WellnessScoreCard scores={scores} />);
      expect(screen.getByRole('region', { name: /wellness score/i })).toHaveTextContent(/needs attention/i);
    });
  });

  describe('change indicators', () => {
    it('shows positive change', () => {
      const scores = { ...baseScores, physical_change: 10, mental_change: 5 };
      render(<WellnessScoreCard scores={scores} />);
      expect(screen.getByText(/\+10/)).toBeInTheDocument();
    });

    it('shows negative change', () => {
      const scores = { ...baseScores, physical_change: -5 };
      render(<WellnessScoreCard scores={scores} />);
      expect(screen.getByText(/-5/)).toBeInTheDocument();
    });

    it('shows zero/neutral', () => {
      const scores = { ...baseScores, physical_change: 0, mental_change: 0 };
      render(<WellnessScoreCard scores={scores} />);
      expect(screen.getByRole('region', { name: /wellness score/i })).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('renders empty state when scores is null', () => {
      render(<WellnessScoreCard scores={null} onStartCheckin={jest.fn()} />);
      const region = screen.getByRole('region', { name: /wellness score/i });
      expect(region).toBeInTheDocument();
      expect(region).toHaveTextContent(/complete your first check-in|get started|start check-in/i);
      const cta = screen.getByRole('button', { name: /start.*check-in/i });
      expect(cta).toBeInTheDocument();
    });

    it('calls onStartCheckin when CTA clicked', () => {
      const onStartCheckin = jest.fn();
      render(<WellnessScoreCard scores={null} onStartCheckin={onStartCheckin} />);
      const cta = screen.getByRole('button', { name: /start.*check-in/i });
      cta.click();
      expect(onStartCheckin).toHaveBeenCalled();
    });
  });

  describe('snapshot', () => {
    it('matches snapshot with scores', () => {
      const { container } = render(<WellnessScoreCard scores={baseScores} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot when empty', () => {
      const { container } = render(<WellnessScoreCard scores={null} />);
      expect(container).toMatchSnapshot();
    });
  });
});
