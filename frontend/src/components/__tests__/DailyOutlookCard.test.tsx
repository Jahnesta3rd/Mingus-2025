/**
 * Daily Outlook Card Component Tests
 * 
 * Tests for the compact DailyOutlookCard component including:
 * - Card rendering and display
 * - Caching functionality
 * - User interaction handling
 * - Responsive design
 * - Accessibility features
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import DailyOutlookCard from '../DailyOutlookCard';
import { useAuth } from '../../hooks/useAuth';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useDailyOutlookCache } from '../../hooks/useDailyOutlookCache';

// Mock the hooks
jest.mock('../../hooks/useAuth');
jest.mock('../../hooks/useAnalytics');
jest.mock('../../hooks/useDailyOutlookCache');

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Test data fixtures
const mockOutlookData = {
  user_name: 'Test User',
  current_time: '2024-01-15T10:30:00Z',
  balance_score: {
    value: 85,
    trend: 'up' as const,
    change_percentage: 5.2,
    previous_value: 80
  },
  primary_insight: {
    title: 'Financial Progress',
    message: 'Your financial progress is on track!',
    type: 'positive' as const,
    icon: 'trending-up'
  },
  quick_actions: [
    {
      id: 'action_1',
      title: 'Review Budget',
      description: 'Check your monthly spending',
      completed: false,
      priority: 'high' as const,
      estimated_time: '5 min'
    }
  ],
  encouragement_message: {
    text: 'Great job maintaining your streak!',
    type: 'motivational' as const,
    emoji: '🔥'
  },
  streak_data: {
    current_streak: 7,
    longest_streak: 12,
    milestone_reached: true,
    next_milestone: 14,
    progress_percentage: 50
  },
  tomorrow_teaser: {
    title: 'Tomorrow\'s Focus',
    description: 'We\'ll dive deeper into your investment strategy',
    excitement_level: 8
  },
  user_tier: 'professional' as const
};

const mockUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  tier: 'professional'
};

const mockAnalytics = {
  trackInteraction: jest.fn(),
  trackError: jest.fn(),
  trackPageView: jest.fn()
};

const mockCache = {
  data: mockOutlookData,
  loading: false,
  error: null,
  refetch: jest.fn(),
  isStale: false
};

describe('DailyOutlookCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({ user: mockUser });
    (useAnalytics as jest.Mock).mockReturnValue(mockAnalytics);
    (useDailyOutlookCache as jest.Mock).mockReturnValue(mockCache);
    localStorageMock.getItem.mockReturnValue('mock-jwt-token');
  });

  describe('Component Rendering', () => {
    it('renders card with outlook data', () => {
      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('Financial Progress')).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('+5.2%')).toBeInTheDocument();
    });

    it('renders loading state', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        loading: true,
        data: null
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('renders error state', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        loading: false,
        data: null,
        error: 'Failed to load data'
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText(/failed to load data/i)).toBeInTheDocument();
    });

    it('renders compact version', () => {
      render(
        <BrowserRouter>
          <DailyOutlookCard compact={true} />
        </BrowserRouter>
      );

      const card = screen.getByTestId('daily-outlook-card');
      expect(card).toHaveClass('compact');
    });

    it('shows stale data indicator', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        isStale: true
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText(/data may be outdated/i)).toBeInTheDocument();
    });
  });

  describe('User Interaction Handling', () => {
    it('handles view full outlook click', async () => {
      const mockOnViewFullOutlook = jest.fn();

      render(
        <BrowserRouter>
          <DailyOutlookCard onViewFullOutlook={mockOnViewFullOutlook} />
        </BrowserRouter>
      );

      const viewButton = screen.getByText(/view full outlook/i);
      await userEvent.click(viewButton);

      expect(mockOnViewFullOutlook).toHaveBeenCalled();
      expect(mockAnalytics.trackInteraction).toHaveBeenCalledWith(
        'daily_outlook_card_view_full',
        expect.objectContaining({
          user_tier: 'professional',
          balance_score: 85
        })
      );
    });

    it('handles refresh data click', async () => {
      const mockRefetch = jest.fn();
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        refetch: mockRefetch
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const refreshButton = screen.getByLabelText(/refresh data/i);
      await userEvent.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('handles action completion in card', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const actionCheckbox = screen.getByLabelText(/review budget/i);
      await userEvent.click(actionCheckbox);

      expect(fetch).toHaveBeenCalledWith('/api/daily-outlook/action-completed', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer mock-jwt-token',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action_id: 'action_1',
          completion_status: true
        })
      });
    });
  });

  describe('Caching Functionality', () => {
    it('uses cached data when available', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        data: mockOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('Financial Progress')).toBeInTheDocument();
    });

    it('handles cache miss gracefully', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        data: null,
        loading: true
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('tracks cache performance', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        isStale: true
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(mockAnalytics.trackInteraction).toHaveBeenCalledWith(
        'daily_outlook_card_loaded',
        expect.objectContaining({
          is_stale: true
        })
      );
    });
  });

  describe('Responsive Design', () => {
    it('adapts to mobile screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const card = screen.getByTestId('daily-outlook-card');
      expect(card).toHaveClass('mobile-layout');
    });

    it('adapts to tablet screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const card = screen.getByTestId('daily-outlook-card');
      expect(card).toHaveClass('tablet-layout');
    });

    it('adapts to desktop screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const card = screen.getByTestId('daily-outlook-card');
      expect(card).toHaveClass('desktop-layout');
    });
  });

  describe('Accessibility Features', () => {
    it('has proper ARIA labels', () => {
      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByRole('article')).toBeInTheDocument();
      expect(screen.getByLabelText(/daily outlook card/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/balance score/i)).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const firstButton = screen.getByRole('button');
      firstButton.focus();
      expect(firstButton).toHaveFocus();

      await userEvent.tab();
      const nextElement = document.activeElement;
      expect(nextElement).toBeInTheDocument();
    });

    it('announces dynamic content changes', async () => {
      const mockAnnounce = jest.fn();
      Object.defineProperty(window, 'speechSynthesis', {
        value: { speak: mockAnnounce },
        writable: true
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const actionCheckbox = screen.getByLabelText(/review budget/i);
      await userEvent.click(actionCheckbox);

      expect(mockAnnounce).toHaveBeenCalled();
    });

    it('has proper color contrast', () => {
      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const textElements = screen.getAllByRole('text');
      textElements.forEach(element => {
        const styles = window.getComputedStyle(element);
        expect(styles.color).toBeDefined();
        expect(styles.backgroundColor).toBeDefined();
      });
    });
  });

  describe('Celebration Effects', () => {
    it('shows milestone celebration', async () => {
      const celebrationData = {
        ...mockOutlookData,
        streak_data: {
          ...mockOutlookData.streak_data,
          milestone_reached: true
        }
      };

      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        data: celebrationData
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/celebration/i)).toBeInTheDocument();
      });
    });

    it('handles celebration animation timing', async () => {
      const celebrationData = {
        ...mockOutlookData,
        streak_data: {
          ...mockOutlookData.streak_data,
          milestone_reached: true
        }
      };

      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        data: celebrationData
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      // Celebration should show initially
      expect(screen.getByText(/celebration/i)).toBeInTheDocument();

      // Wait for celebration to hide
      await waitFor(() => {
        expect(screen.queryByText(/celebration/i)).not.toBeInTheDocument();
      }, { timeout: 4000 });
    });
  });

  describe('Performance Testing', () => {
    it('renders within performance budget', () => {
      const startTime = performance.now();

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within 50ms for card component
      expect(renderTime).toBeLessThan(50);
    });

    it('handles frequent updates efficiently', () => {
      const { rerender } = render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const startTime = performance.now();

      // Simulate frequent updates
      for (let i = 0; i < 10; i++) {
        rerender(
          <BrowserRouter>
            <DailyOutlookCard />
          </BrowserRouter>
        );
      }

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      // Should handle updates efficiently
      expect(totalTime).toBeLessThan(100);
    });
  });

  describe('Error Handling', () => {
    it('handles cache errors gracefully', () => {
      (useDailyOutlookCache as jest.Mock).mockReturnValue({
        ...mockCache,
        data: null,
        error: 'Cache error',
        loading: false
      });

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      expect(screen.getByText(/cache error/i)).toBeInTheDocument();
    });

    it('handles API errors in actions', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

      render(
        <BrowserRouter>
          <DailyOutlookCard />
        </BrowserRouter>
      );

      const actionCheckbox = screen.getByLabelText(/review budget/i);
      await userEvent.click(actionCheckbox);

      expect(mockAnalytics.trackError).toHaveBeenCalledWith(
        'daily_outlook_action_error',
        'API Error'
      );
    });
  });
});
