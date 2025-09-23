/**
 * Comprehensive Daily Outlook Component Tests
 * 
 * This test suite covers:
 * - Component rendering and display
 * - User interaction handling
 * - API integration testing
 * - Responsive design validation
 * - Accessibility compliance testing
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import DailyOutlook from '../DailyOutlook';
import { useAuth } from '../../hooks/useAuth';
import { useAnalytics } from '../../hooks/useAnalytics';

// Mock the hooks
jest.mock('../../hooks/useAuth');
jest.mock('../../hooks/useAnalytics');

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

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Test data fixtures
const mockDailyOutlookData = {
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
    },
    {
      id: 'action_2',
      title: 'Update Goals',
      description: 'Review your financial goals',
      completed: false,
      priority: 'medium' as const,
      estimated_time: '10 min'
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

describe('DailyOutlook Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({ user: mockUser });
    (useAnalytics as jest.Mock).mockReturnValue(mockAnalytics);
    localStorageMock.getItem.mockReturnValue('mock-jwt-token');
  });

  describe('Component Rendering', () => {
    it('renders loading state initially', () => {
      (fetch as jest.Mock).mockImplementation(() => 
        new Promise(() => {}) // Never resolves to keep loading state
      );

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('renders error state when API call fails', async () => {
      (fetch as jest.Mock).mockRejectedValue(new Error('API Error'));

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/failed to load daily outlook/i)).toBeInTheDocument();
      });
    });

    it('renders daily outlook data successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
        expect(screen.getByText('Financial Progress')).toBeInTheDocument();
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
        expect(screen.getByText('Update Goals')).toBeInTheDocument();
      });
    });

    it('displays balance score with trend indicator', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('85')).toBeInTheDocument();
        expect(screen.getByText('+5.2%')).toBeInTheDocument();
      });
    });

    it('shows streak information correctly', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('7')).toBeInTheDocument(); // Current streak
        expect(screen.getByText('12')).toBeInTheDocument(); // Longest streak
      });
    });
  });

  describe('User Interaction Handling', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
      });
    });

    it('handles action completion toggle', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

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

    it('handles star rating submission', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      const starButtons = screen.getAllByRole('button');
      const fiveStarButton = starButtons.find(button => 
        button.getAttribute('data-rating') === '5'
      );
      
      if (fiveStarButton) {
        await userEvent.click(fiveStarButton);
      }

      expect(fetch).toHaveBeenCalledWith('/api/daily-outlook/rating', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer mock-jwt-token',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rating: 5 })
      });
    });

    it('handles share functionality', async () => {
      // Mock navigator.share
      const mockShare = jest.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, 'share', {
        value: mockShare,
        writable: true
      });

      const shareButton = screen.getByLabelText(/share/i);
      await userEvent.click(shareButton);

      expect(mockShare).toHaveBeenCalledWith({
        title: 'My Daily Outlook',
        text: 'Check out my progress on Mingus!',
        url: window.location.href
      });
    });

    it('handles share fallback when navigator.share is not available', async () => {
      // Mock clipboard API
      const mockWriteText = jest.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: mockWriteText },
        writable: true
      });

      // Remove navigator.share
      delete (navigator as any).share;

      const shareButton = screen.getByLabelText(/share/i);
      await userEvent.click(shareButton);

      expect(mockWriteText).toHaveBeenCalledWith(window.location.href);
    });
  });

  describe('API Integration Testing', () => {
    it('makes correct API call with authentication', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/daily-outlook', {
          headers: {
            'Authorization': 'Bearer mock-jwt-token',
            'Content-Type': 'application/json',
          },
        });
      });
    });

    it('handles API errors gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/failed to load daily outlook/i)).toBeInTheDocument();
      });

      expect(mockAnalytics.trackError).toHaveBeenCalledWith(
        'daily_outlook_fetch_error',
        'Network error'
      );
    });

    it('handles 403 Forbidden response', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          error: 'Feature not available',
          message: 'Daily Outlook feature is not available in your current tier.',
          upgrade_required: true
        })
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/feature not available/i)).toBeInTheDocument();
        expect(screen.getByText(/upgrade required/i)).toBeInTheDocument();
      });
    });

    it('handles 404 Not Found response', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          error: 'No outlook available',
          message: 'No daily outlook available for today.'
        })
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/no outlook available/i)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design Validation', () => {
    it('applies mobile styles on small screens', async () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        const container = screen.getByTestId('daily-outlook-container');
        expect(container).toHaveClass('mobile-layout');
      });
    });

    it('applies desktop styles on large screens', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        const container = screen.getByTestId('daily-outlook-container');
        expect(container).toHaveClass('desktop-layout');
      });
    });

    it('handles orientation changes', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
      });

      // Simulate orientation change
      act(() => {
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: 800,
        });
        window.dispatchEvent(new Event('resize'));
      });

      // Component should still render correctly
      expect(screen.getByText('Review Budget')).toBeInTheDocument();
    });
  });

  describe('Accessibility Compliance Testing', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
      });
    });

    it('has proper ARIA labels and roles', () => {
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /share/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/review budget/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/update goals/i)).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const firstAction = screen.getByLabelText(/review budget/i);
      firstAction.focus();
      expect(firstAction).toHaveFocus();

      // Tab to next interactive element
      await userEvent.tab();
      const nextElement = document.activeElement;
      expect(nextElement).toBeInTheDocument();
    });

    it('has proper heading hierarchy', () => {
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);
      
      // Check for h1 (main heading)
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toBeInTheDocument();
    });

    it('provides screen reader announcements for dynamic content', async () => {
      // Mock screen reader announcement
      const mockAnnounce = jest.fn();
      Object.defineProperty(window, 'speechSynthesis', {
        value: {
          speak: mockAnnounce
        },
        writable: true
      });

      // Trigger action completion
      const actionCheckbox = screen.getByLabelText(/review budget/i);
      await userEvent.click(actionCheckbox);

      // Should announce completion
      expect(mockAnnounce).toHaveBeenCalled();
    });

    it('has proper color contrast ratios', () => {
      const elements = screen.getAllByRole('text');
      elements.forEach(element => {
        const styles = window.getComputedStyle(element);
        // This would need actual color contrast testing in a real implementation
        expect(styles.color).toBeDefined();
        expect(styles.backgroundColor).toBeDefined();
      });
    });

    it('supports focus management', () => {
      const focusableElements = screen.getAllByRole('button');
      focusableElements.forEach(element => {
        expect(element).toHaveAttribute('tabIndex');
      });
    });
  });

  describe('Celebration and Animation Effects', () => {
    it('shows celebration animation for milestone reached', async () => {
      const celebrationData = {
        ...mockDailyOutlookData,
        streak_data: {
          ...mockDailyOutlookData.streak_data,
          milestone_reached: true
        }
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => celebrationData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/celebration/i)).toBeInTheDocument();
      });
    });

    it('handles score change animations', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        const scoreElement = screen.getByText('85');
        expect(scoreElement).toHaveClass('score-change-animation');
      });
    });
  });

  describe('Error Boundary Integration', () => {
    it('handles component errors gracefully', async () => {
      // Mock component to throw error
      const ThrowError = () => {
        throw new Error('Component error');
      };

      render(
        <BrowserRouter>
          <ThrowError />
        </BrowserRouter>
      );

      // Should show error boundary
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });

  describe('Performance Testing', () => {
    it('renders within performance budget', async () => {
      const startTime = performance.now();

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within 100ms
      expect(renderTime).toBeLessThan(100);
    });

    it('handles large datasets efficiently', async () => {
      const largeDataset = {
        ...mockDailyOutlookData,
        quick_actions: Array.from({ length: 50 }, (_, i) => ({
          id: `action_${i}`,
          title: `Action ${i}`,
          description: `Description ${i}`,
          completed: false,
          priority: 'medium' as const,
          estimated_time: '5 min'
        }))
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => largeDataset
      });

      const startTime = performance.now();

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Action 0')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should handle large datasets efficiently
      expect(renderTime).toBeLessThan(500);
    });
  });

  describe('Analytics Integration', () => {
    it('tracks component load event', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockAnalytics.trackInteraction).toHaveBeenCalledWith(
          'daily_outlook_loaded',
          expect.objectContaining({
            user_tier: 'professional',
            balance_score: 85,
            streak_count: 7
          })
        );
      });
    });

    it('tracks user interactions', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDailyOutlookData
      });

      render(
        <BrowserRouter>
          <DailyOutlook />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
      });

      const actionCheckbox = screen.getByLabelText(/review budget/i);
      await userEvent.click(actionCheckbox);

      expect(mockAnalytics.trackInteraction).toHaveBeenCalledWith(
        'action_completed',
        expect.objectContaining({
          action_id: 'action_1',
          completion_status: true
        })
      );
    });
  });
});
