/**
 * Mingus Personal Finance App - MemeSplashPage Component Tests
 * Comprehensive tests for the React meme splash page component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import MemeSplashPage from '../../../frontend/src/components/MemeSplashPage';

// Mock fetch globally
global.fetch = jest.fn();

// Mock console methods to avoid noise in tests
const originalConsoleError = console.error;
const originalConsoleLog = console.log;

beforeAll(() => {
  console.error = jest.fn();
  console.log = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
  console.log = originalConsoleLog;
});

describe('MemeSplashPage Component', () => {
  const mockOnContinue = jest.fn();
  const mockOnSkip = jest.fn();
  
  const defaultProps = {
    onContinue: mockOnContinue,
    onSkip: mockOnSkip,
    userId: 'user123',
    sessionId: 'session456',
    autoAdvanceDelay: 10000,
    className: 'test-class'
  };

  const mockMemeData = {
    id: 1,
    image_url: 'https://example.com/meme1.jpg',
    category: 'faith',
    caption: 'Sunday motivation: Trust the process',
    alt_text: 'Faith meme showing trust',
    is_active: true,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Component Rendering', () => {
    it('renders loading skeleton initially', () => {
      (fetch as jest.Mock).mockImplementation(() => new Promise(() => {})); // Never resolves
      
      render(<MemeSplashPage {...defaultProps} />);
      
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
      expect(screen.getByText('Loading your daily motivation...')).toBeInTheDocument();
    });

    it('renders meme content after successful fetch', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      expect(screen.getByAltText('Faith meme showing trust')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /skip this feature/i })).toBeInTheDocument();
    });

    it('applies custom className', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      render(<MemeSplashPage {...defaultProps} className="custom-class" />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
      expect(container).toHaveClass('custom-class');
    });

    it('renders with default props when optional props are not provided', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      render(<MemeSplashPage onContinue={mockOnContinue} onSkip={mockOnSkip} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      // Should use default autoAdvanceDelay of 10000ms
      expect(screen.getByText('10s')).toBeInTheDocument();
    });
  });

  describe('API Integration', () => {
    it('fetches meme data on component mount', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/user-meme', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': 'user123',
            'X-Session-ID': 'session456'
          },
          credentials: 'include'
        });
      });
    });

    it('sends analytics when meme is viewed', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMemeData
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      // Should send view analytics
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            meme_id: 1,
            action: 'view',
            user_id: 'user123',
            session_id: 'session456'
          })
        });
      });
    });

    it('handles API errors gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('handles non-ok API responses', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to fetch meme: 500 Internal Server Error')).toBeInTheDocument();
      });
    });

    it('tracks mood data when mood is selected', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMemeData
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, message: 'Mood tracked successfully' })
        });

      render(<MemeSplashPage {...defaultProps} enableMoodTracking={true} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      // Wait for mood selector to appear
      await waitFor(() => {
        expect(screen.getByText('How does this make you feel?')).toBeInTheDocument();
      });

      // Click on happy mood
      const happyMoodButton = screen.getByLabelText('Select happy mood: Positive, content');
      fireEvent.click(happyMoodButton);

      // Verify mood tracking API was called
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-mood', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: expect.stringContaining('"mood_label":"happy"')
        });
      });
    });

    it('does not show mood selector when mood tracking is disabled', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMemeData
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<MemeSplashPage {...defaultProps} enableMoodTracking={false} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      // Mood selector should not be present
      expect(screen.queryByText('How does this make you feel?')).not.toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });
    });

    it('calls onContinue when continue button is clicked', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      fireEvent.click(continueButton);

      expect(mockOnContinue).toHaveBeenCalledTimes(1);
    });

    it('calls onSkip when skip button is clicked', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const skipButton = screen.getByRole('button', { name: /skip this feature/i });
      fireEvent.click(skipButton);

      expect(mockOnSkip).toHaveBeenCalledTimes(1);
    });

    it('sends analytics when continue button is clicked', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      fireEvent.click(continueButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', expect.objectContaining({
          body: JSON.stringify({
            meme_id: 1,
            action: 'continue',
            user_id: 'user123',
            session_id: 'session456'
          })
        }));
      });
    });

    it('sends analytics when skip button is clicked', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const skipButton = screen.getByRole('button', { name: /skip this feature/i });
      fireEvent.click(skipButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', expect.objectContaining({
          body: JSON.stringify({
            meme_id: 1,
            action: 'skip',
            user_id: 'user123',
            session_id: 'session456'
          })
        }));
      });
    });
  });

  describe('Keyboard Navigation', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });
    });

    it('calls onContinue when Enter key is pressed', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
      fireEvent.keyDown(container!, { key: 'Enter' });

      expect(mockOnContinue).toHaveBeenCalledTimes(1);
    });

    it('calls onContinue when Space key is pressed', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
      fireEvent.keyDown(container!, { key: ' ' });

      expect(mockOnContinue).toHaveBeenCalledTimes(1);
    });

    it('calls onSkip when Escape key is pressed', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
      fireEvent.keyDown(container!, { key: 'Escape' });

      expect(mockOnSkip).toHaveBeenCalledTimes(1);
    });

    it('ignores other keys', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
      fireEvent.keyDown(container!, { key: 'a' });
      fireEvent.keyDown(container!, { key: 'Tab' });

      expect(mockOnContinue).not.toHaveBeenCalled();
      expect(mockOnSkip).not.toHaveBeenCalled();
    });
  });

  describe('Auto-advance Functionality', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });
    });

    it('shows countdown timer', async () => {
      render(<MemeSplashPage {...defaultProps} autoAdvanceDelay={5000} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      expect(screen.getByText('5s')).toBeInTheDocument();
    });

    it('decrements countdown timer', async () => {
      render(<MemeSplashPage {...defaultProps} autoAdvanceDelay={3000} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      expect(screen.getByText('3s')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText('2s')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText('1s')).toBeInTheDocument();
    });

    it('auto-advances after delay', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      render(<MemeSplashPage {...defaultProps} autoAdvanceDelay={2000} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(2000);
      });

      expect(mockOnContinue).toHaveBeenCalledTimes(1);
    });

    it('sends auto_advance analytics when auto-advancing', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      render(<MemeSplashPage {...defaultProps} autoAdvanceDelay={2000} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', expect.objectContaining({
          body: JSON.stringify({
            meme_id: 1,
            action: 'auto_advance',
            user_id: 'user123',
            session_id: 'session456'
          })
        }));
      });
    });

    it('stops auto-advance when user interacts', async () => {
      render(<MemeSplashPage {...defaultProps} autoAdvanceDelay={5000} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      // User clicks continue
      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      fireEvent.click(continueButton);

      // Advance time past the auto-advance delay
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      // onContinue should only be called once (from the button click)
      expect(mockOnContinue).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error Handling', () => {
    it('shows error message when fetch fails', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('retries when retry button is clicked', async () => {
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMemeData
        });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('handles image load errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const image = screen.getByAltText('Faith meme showing trust');
      fireEvent.error(image);

      expect(screen.getByText('Failed to load meme image')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });
    });

    it('has proper ARIA labels', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /skip this feature/i })).toBeInTheDocument();
    });

    it('has proper alt text for images', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByAltText('Faith meme showing trust')).toBeInTheDocument();
      });
    });

    it('is keyboard navigable', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
      expect(container).toHaveAttribute('tabIndex', '-1');
    });

    it('has proper focus management', async () => {
      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      expect(continueButton).toBeInTheDocument();
      
      // Button should be focusable
      continueButton.focus();
      expect(document.activeElement).toBe(continueButton);
    });
  });

  describe('Component Cleanup', () => {
    it('cleans up timers on unmount', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      const { unmount } = render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      unmount();

      // Advance timers to ensure they were cleared
      act(() => {
        jest.advanceTimersByTime(15000);
      });

      // Should not call onContinue after unmount
      expect(mockOnContinue).not.toHaveBeenCalled();
    });

    it('cleans up timers when user interacts', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      fireEvent.click(continueButton);

      // Advance timers to ensure they were cleared
      act(() => {
        jest.advanceTimersByTime(15000);
      });

      // onContinue should only be called once
      expect(mockOnContinue).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    it('handles missing meme data gracefully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => null
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
      });
    });

    it('handles malformed meme data', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1 }) // Missing required fields
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
      });
    });

    it('handles very long captions', async () => {
      const longCaptionMeme = {
        ...mockMemeData,
        caption: 'A'.repeat(1000)
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => longCaptionMeme
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('A'.repeat(1000))).toBeInTheDocument();
      });
    });

    it('handles special characters in caption', async () => {
      const specialCharMeme = {
        ...mockMemeData,
        caption: 'Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?'
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => specialCharMeme
      });

      render(<MemeSplashPage {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?')).toBeInTheDocument();
      });
    });
  });
});
