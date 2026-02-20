import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SpendingMilestonesWidget from '../SpendingMilestonesWidget';

const mockFetch = jest.fn();

function mockMilestonesResponse(overrides: Partial<{
  current_streak: number;
  next_milestone: number;
  milestones: { days: number; achieved: boolean; achieved_date: string | null }[];
  achievements: string[];
}> = {}) {
  const defaults = {
    current_streak: 5,
    next_milestone: 7,
    milestones: [
      { days: 3, achieved: true, achieved_date: '2024-01-03' },
      { days: 7, achieved: false, achieved_date: null },
      { days: 14, achieved: false, achieved_date: null },
      { days: 30, achieved: false, achieved_date: null },
      { days: 60, achieved: false, achieved_date: null },
      { days: 100, achieved: false, achieved_date: null },
    ],
    achievements: [],
  };
  return { ...defaults, ...overrides };
}

beforeEach(() => {
  mockFetch.mockReset();
  global.fetch = mockFetch;
  Object.defineProperty(window, 'localStorage', {
    value: { getItem: jest.fn(() => 'mock-token') },
    writable: true,
  });
});

describe('SpendingMilestonesWidget', () => {
  describe('1. Renders without TypeScript errors', () => {
    it('renders the component without throwing', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMilestonesResponse(),
      });
      const { container } = render(<SpendingMilestonesWidget userId="user-1" />);
      await waitFor(() => {
        expect(screen.getByText(/day streak/i)).toBeInTheDocument();
      });
      expect(container).toBeTruthy();
    });
  });

  describe('2. Circular SVG ring updates when streak changes', () => {
    it('shows streak number and ring reflects fetched data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMilestonesResponse({ current_streak: 4, next_milestone: 7 }),
      });
      render(<SpendingMilestonesWidget userId="user-1" />);
      await waitFor(() => {
        expect(screen.getByText('4')).toBeInTheDocument();
        expect(screen.getByText('Next milestone: 7 days')).toBeInTheDocument();
      });
      const svg = document.querySelector('svg');
      expect(svg).toBeInTheDocument();
      const progressCircle = svg?.querySelector('circle[stroke="#5B2D8E"]');
      expect(progressCircle).toBeInTheDocument();
    });

    it('ring progress circle uses strokeDashoffset derived from streak and next_milestone', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMilestonesResponse({ current_streak: 5, next_milestone: 7 }),
      });
      render(<SpendingMilestonesWidget userId="user-1" />);
      await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument());
      const purpleCircle = document.querySelector('circle[stroke="#5B2D8E"]');
      expect(purpleCircle).toHaveAttribute('stroke-dashoffset');
      expect(Number((purpleCircle as SVGElement).getAttribute('stroke-dashoffset'))).toBeLessThan(
        Number((purpleCircle as SVGElement).getAttribute('stroke-dasharray'))
      );
    });
  });

  describe('3. Badge tooltips on hover for achieved milestones', () => {
    it('shows tooltip with achieved_date when hovering an achieved badge', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockMilestonesResponse({
            milestones: [
              { days: 3, achieved: true, achieved_date: '2024-06-15' },
              { days: 7, achieved: false, achieved_date: null },
              { days: 14, achieved: false, achieved_date: null },
              { days: 30, achieved: false, achieved_date: null },
              { days: 60, achieved: false, achieved_date: null },
              { days: 100, achieved: false, achieved_date: null },
            ],
          }),
      });
      render(<SpendingMilestonesWidget userId="user-1" />);
      await waitFor(() => expect(screen.getByText(/day streak/i)).toBeInTheDocument());
      const achievedBadge = screen.getByRole('button', { name: /milestone 3 days, achieved/i });
      expect(achievedBadge).toBeInTheDocument();
      fireEvent.mouseEnter(achievedBadge);
      await waitFor(() => {
        const tooltip = document.querySelector('[role="tooltip"]');
        expect(tooltip).toBeInTheDocument();
        expect(tooltip?.textContent).toMatch(/Jun|6\/15\/2024|15\/06\/2024/);
      });
    });
  });

  describe('4. Empty state links to /daily-outlook', () => {
    it('shows empty state with link to /daily-outlook when current_streak is 0', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockMilestonesResponse({
            current_streak: 0,
            next_milestone: 3,
            milestones: [
              { days: 3, achieved: false, achieved_date: null },
              { days: 7, achieved: false, achieved_date: null },
              { days: 14, achieved: false, achieved_date: null },
              { days: 30, achieved: false, achieved_date: null },
              { days: 60, achieved: false, achieved_date: null },
              { days: 100, achieved: false, achieved_date: null },
            ],
          }),
      });
      render(<SpendingMilestonesWidget userId="user-1" />);
      await waitFor(() => {
        expect(screen.getByText(/complete your first check-in to start your streak/i)).toBeInTheDocument();
      });
      const link = screen.getByRole('link', { name: /go to daily outlook/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/daily-outlook');
    });
  });

  describe('5. 375px layout stacks vertically', () => {
    it('main content container has flex-col so layout stacks on small screens (< 640px)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMilestonesResponse(),
      });
      render(<SpendingMilestonesWidget userId="user-1" />);
      await waitFor(() => expect(screen.getByText(/day streak/i)).toBeInTheDocument());
      const region = document.querySelector('[aria-label="Spending milestones"]');
      expect(region).toBeInTheDocument();
      const inner = region?.querySelector('[class*="flex-col"]') ?? region?.firstElementChild;
      const className = (inner as HTMLElement)?.className ?? (region as HTMLElement)?.className ?? '';
      expect(className).toMatch(/flex-col/);
    });
  });
});
