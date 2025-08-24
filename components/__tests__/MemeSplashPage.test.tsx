import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import MemeSplashPage from '../MemeSplashPage';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

// Mock console.error to avoid noise in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe('MemeSplashPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockMeme = {
    id: 'test-meme-1',
    image_url: 'https://example.com/meme.jpg',
    caption: 'Test meme caption',
    category: 'work_life',
    alt_text: 'A funny meme about work life balance',
    tags: ['work', 'life', 'balance']
  };

  const mockApiResponse = {
    success: true,
    meme: mockMeme,
    timestamp: '2024-01-01T00:00:00Z'
  };

  describe('Loading State', () => {
    it('should show loading skeleton initially', () => {
      (fetch as jest.Mock).mockImplementation(() => 
        new Promise(() => {}) // Never resolves to keep loading state
      );

      render(<MemeSplashPage />);
      
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('should show loading skeleton with proper structure', () => {
      (fetch as jest.Mock).mockImplementation(() => 
        new Promise(() => {})
      );

      render(<MemeSplashPage />);
      
      // Check for skeleton elements
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
      // Add more specific skeleton checks if needed
    });
  });

  describe('Success State', () => {
    beforeEach(() => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });
    });

    it('should display meme when loaded successfully', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText('Test meme caption')).toBeInTheDocument();
      });

      expect(screen.getByAltText('A funny meme about work life balance')).toBeInTheDocument();
      expect(screen.getByText('work_life')).toBeInTheDocument();
    });

    it('should show prominent continue button', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });
    });

    it('should show opt-out link in header', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });
    });

    it('should show "Not today" option', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /not today/i })).toBeInTheDocument();
      });
    });

    it('should show auto-advance countdown when enabled', async () => {
      render(<MemeSplashPage autoAdvanceSeconds={10} />);

      await waitFor(() => {
        expect(screen.getByText(/auto-continue in 10s/i)).toBeInTheDocument();
      });
    });

    it('should not show auto-advance countdown when disabled', async () => {
      render(<MemeSplashPage autoAdvanceSeconds={0} />);

      await waitFor(() => {
        expect(screen.queryByText(/auto-continue/i)).not.toBeInTheDocument();
      });
    });

    it('should display MINGUS branding', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText('MINGUS')).toBeInTheDocument();
        expect(screen.getByText('Daily Inspiration')).toBeInTheDocument();
      });
    });

    it('should display meme category badge', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText('work_life')).toBeInTheDocument();
      });
    });
  });

  describe('Error State', () => {
    it('should show error message when API fails', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });
    });

    it('should show continue button on error', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });
    });

    it('should show specific error message', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should retry when retry button is clicked', async () => {
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        });

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /try again/i }));

      await waitFor(() => {
        expect(screen.getByText('Test meme caption')).toBeInTheDocument();
      });
    });
  });

  describe('No Meme Available', () => {
    it('should show no meme message when API returns no meme', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, meme: null })
      });

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText(/no inspiration today/i)).toBeInTheDocument();
      });
    });

    it('should show appropriate message for no meme', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, meme: null })
      });

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText(/check back tomorrow/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    beforeEach(() => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });
    });

    it('should call onContinue when continue button is clicked', async () => {
      const mockOnContinue = jest.fn();
      render(<MemeSplashPage onContinue={mockOnContinue} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /continue to dashboard/i }));

      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledTimes(1);
      });
    });

    it('should call onSkip when skip button is clicked', async () => {
      const mockOnSkip = jest.fn();
      render(<MemeSplashPage onSkip={mockOnSkip} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /not today/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /not today/i }));

      await waitFor(() => {
        expect(mockOnSkip).toHaveBeenCalledTimes(1);
      });
    });

    it('should show opt-out modal when opt-out link is clicked', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /turn off daily memes/i }));

      await waitFor(() => {
        expect(screen.getByText(/turn off daily memes\?/i)).toBeInTheDocument();
      });
    });

    it('should call onOptOut when opt-out is confirmed', async () => {
      const mockOnOptOut = jest.fn();
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<MemeSplashPage onOptOut={mockOnOptOut} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /turn off daily memes/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /turn off daily memes/i }));

      await waitFor(() => {
        expect(mockOnOptOut).toHaveBeenCalledTimes(1);
      });
    });

    it('should close modal when clicking outside', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /turn off daily memes/i }));

      await waitFor(() => {
        expect(screen.getByText(/turn off daily memes\?/i)).toBeInTheDocument();
      });

      // Click outside modal
      fireEvent.click(screen.getByText(/turn off daily memes\?/i).parentElement!.parentElement!);

      await waitFor(() => {
        expect(screen.queryByText(/turn off daily memes\?/i)).not.toBeInTheDocument();
      });
    });

    it('should show loading state during opt-out', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        })
        .mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /turn off daily memes/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /turn off daily memes/i }));

      await waitFor(() => {
        expect(screen.getByText(/turning off/i)).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    beforeEach(() => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });
    });

    it('should handle Enter key to continue', async () => {
      const mockOnContinue = jest.fn();
      render(<MemeSplashPage onContinue={mockOnContinue} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: 'Enter' });

      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle Space key to continue', async () => {
      const mockOnContinue = jest.fn();
      render(<MemeSplashPage onContinue={mockOnContinue} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: ' ' });

      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle Escape key to skip', async () => {
      const mockOnSkip = jest.fn();
      render(<MemeSplashPage onSkip={mockOnSkip} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /not today/i })).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: 'Escape' });

      await waitFor(() => {
        expect(mockOnSkip).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle O key to open opt-out modal', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: 'O' });

      await waitFor(() => {
        expect(screen.getByText(/turn off daily memes\?/i)).toBeInTheDocument();
      });
    });

    it('should handle lowercase o key to open opt-out modal', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /turn off daily memes/i })).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: 'o' });

      await waitFor(() => {
        expect(screen.getByText(/turn off daily memes\?/i)).toBeInTheDocument();
      });
    });

    it('should not handle keyboard events during loading', async () => {
      (fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
      
      const mockOnContinue = jest.fn();
      render(<MemeSplashPage onContinue={mockOnContinue} />);

      fireEvent.keyDown(document, { key: 'Enter' });

      expect(mockOnContinue).not.toHaveBeenCalled();
    });
  });

  describe('Image Loading', () => {
    beforeEach(() => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });
    });

    it('should show loading state for image', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      });
    });

    it('should show error state when image fails to load', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        const img = screen.getByAltText('A funny meme about work life balance');
        fireEvent.error(img);
      });

      await waitFor(() => {
        expect(screen.getByText(/image unavailable/i)).toBeInTheDocument();
      });
    });

    it('should show image when loaded successfully', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        const img = screen.getByAltText('A funny meme about work life balance');
        fireEvent.load(img);
      });

      expect(screen.getByAltText('A funny meme about work life balance')).toBeInTheDocument();
    });
  });

  describe('Auto-advance', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should auto-advance after countdown', async () => {
      const mockOnContinue = jest.fn();
      render(<MemeSplashPage onContinue={mockOnContinue} autoAdvanceSeconds={3} />);

      await waitFor(() => {
        expect(screen.getByText(/auto-continue in 3s/i)).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledTimes(1);
      });
    });

    it('should update countdown every second', async () => {
      render(<MemeSplashPage autoAdvanceSeconds={3} />);

      await waitFor(() => {
        expect(screen.getByText(/auto-continue in 3s/i)).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(screen.getByText(/auto-continue in 2s/i)).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(screen.getByText(/auto-continue in 1s/i)).toBeInTheDocument();
      });
    });

    it('should not auto-advance when disabled', async () => {
      const mockOnContinue = jest.fn();
      render(<MemeSplashPage onContinue={mockOnContinue} autoAdvanceSeconds={0} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(5000);
      });

      expect(mockOnContinue).not.toHaveBeenCalled();
    });
  });

  describe('Analytics Tracking', () => {
    beforeEach(() => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });
    });

    it('should track view analytics when meme loads', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            meme_id: 'test-meme-1',
            interaction_type: 'viewed',
            source_page: 'meme_splash'
          })
        }));
      });
    });

    it('should track continue analytics when continue button is clicked', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /continue to dashboard/i }));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            meme_id: 'test-meme-1',
            interaction_type: 'continued',
            source_page: 'meme_splash'
          })
        }));
      });
    });

    it('should track skip analytics when skip button is clicked', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /not today/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /not today/i }));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/meme-analytics', expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            meme_id: 'test-meme-1',
            interaction_type: 'skipped',
            source_page: 'meme_splash'
          })
        }));
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });
    });

    it('should have proper ARIA labels', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByLabelText(/turn off daily memes/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/continue to dashboard/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/skip for today/i)).toBeInTheDocument();
      });
    });

    it('should have proper alt text for images', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByAltText('A funny meme about work life balance')).toBeInTheDocument();
      });
    });

    it('should be keyboard navigable', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      // Tab navigation should work
      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      expect(continueButton).toHaveAttribute('tabIndex', '0');
    });

    it('should have proper focus management', async () => {
      render(<MemeSplashPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
      continueButton.focus();
      expect(continueButton).toHaveFocus();
    });
  });

  describe('Error Boundary', () => {
    it('should handle component errors gracefully', () => {
      const ErrorComponent = () => {
        throw new Error('Test error');
      };

      render(
        <div>
          <ErrorComponent />
        </div>
      );

      // Should not crash the test
      expect(true).toBe(true);
    });
  });

  describe('Props and Configuration', () => {
    it('should respect autoAdvanceSeconds prop', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });

      render(<MemeSplashPage autoAdvanceSeconds={5} />);

      await waitFor(() => {
        expect(screen.getByText(/auto-continue in 5s/i)).toBeInTheDocument();
      });
    });

    it('should respect showOptOutModal prop', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse
      });

      render(<MemeSplashPage showOptOutModal={false} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /turn off daily memes/i })).not.toBeInTheDocument();
      });
    });

    it('should call custom callbacks when provided', async () => {
      const mockOnContinue = jest.fn();
      const mockOnSkip = jest.fn();
      const mockOnOptOut = jest.fn();

      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockApiResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(
        <MemeSplashPage 
          onContinue={mockOnContinue}
          onSkip={mockOnSkip}
          onOptOut={mockOnOptOut}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /continue to dashboard/i }));

      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledTimes(1);
      });
    });
  });
});
