import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import OptimalLocationRouter from '../OptimalLocationRouter';

// Mock the hooks
jest.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user',
      email: 'test@example.com',
      name: 'Test User',
      token: 'test-token',
      isAuthenticated: true
    },
    isAuthenticated: true,
    loading: false
  })
}));

jest.mock('../../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackPageView: jest.fn(),
    trackInteraction: jest.fn(),
    trackError: jest.fn(),
    getSessionId: jest.fn(() => 'test-session'),
    getUserId: jest.fn(() => 'test-user')
  })
}));

// Mock fetch
global.fetch = jest.fn();

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('OptimalLocationRouter', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tier: 'mid_tier' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ scenarios: [] })
      });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Authentication', () => {
    it('should redirect to login when not authenticated', async () => {
      // Mock unauthenticated state
      jest.doMock('../../../hooks/useAuth', () => ({
        useAuth: () => ({
          user: null,
          isAuthenticated: false,
          loading: false
        })
      }));

      const { useAuth } = require('../../../hooks/useAuth');
      useAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        loading: false
      });

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });

    it('should show loading state during authentication check', () => {
      jest.doMock('../../../hooks/useAuth', () => ({
        useAuth: () => ({
          user: null,
          isAuthenticated: false,
          loading: true
        })
      }));

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      expect(screen.getByText('Loading optimal location feature...')).toBeInTheDocument();
    });
  });

  describe('Component Rendering', () => {
    it('should render the main component structure', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Optimal Living Location')).toBeInTheDocument();
        expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
      });
    });

    it('should display user tier badge', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('MID TIER')).toBeInTheDocument();
      });
    });

    it('should render navigation tabs', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Housing Search')).toBeInTheDocument();
        expect(screen.getByText('Scenarios')).toBeInTheDocument();
        expect(screen.getByText('Results')).toBeInTheDocument();
        expect(screen.getByText('Preferences')).toBeInTheDocument();
      });
    });
  });

  describe('View Navigation', () => {
    it('should switch between views when tabs are clicked', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Housing Search')).toBeInTheDocument();
      });

      // Click on Scenarios tab
      fireEvent.click(screen.getByText('Scenarios'));

      await waitFor(() => {
        expect(screen.getByText('Location Scenarios')).toBeInTheDocument();
      });
    });

    it('should disable restricted features for budget tier', async () => {
      // Mock budget tier
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ tier: 'budget' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ scenarios: [] })
        });

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('BUDGET')).toBeInTheDocument();
      });

      // Check that scenario planning is disabled
      const scenariosTab = screen.getByText('Scenarios').closest('button');
      expect(scenariosTab).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('Housing Search', () => {
    it('should render housing search form', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Your Optimal Location')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter city, state, or ZIP code')).toBeInTheDocument();
        expect(screen.getByText('Search Locations')).toBeInTheDocument();
      });
    });

    it('should handle form submission', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ tier: 'mid_tier' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ scenarios: [] })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ results: [{ title: 'Test Property', price: 1500 }] })
        });

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Your Optimal Location')).toBeInTheDocument();
      });

      // Fill out form
      fireEvent.change(screen.getByPlaceholderText('Enter city, state, or ZIP code'), {
        target: { value: 'San Francisco, CA' }
      });

      fireEvent.change(screen.getByDisplayValue('0'), {
        target: { value: '1000' }
      });

      fireEvent.change(screen.getByDisplayValue('0'), {
        target: { value: '2000' }
      });

      // Submit form
      fireEvent.click(screen.getByText('Search Locations'));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/optimal-location/housing-search',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': 'Bearer test-token'
            })
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('API Error'));

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Unable to Load Feature')).toBeInTheDocument();
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('API Error'));

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        const nav = screen.getByRole('tablist');
        expect(nav).toBeInTheDocument();

        const tabs = screen.getAllByRole('tab');
        expect(tabs).toHaveLength(4);
      });
    });

    it('should support keyboard navigation', async () => {
      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        const firstTab = screen.getByText('Housing Search').closest('button');
        expect(firstTab).toHaveAttribute('tabIndex', '0');
      });
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should hide text on small screens', async () => {
      // Mock small screen
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        const backButton = screen.getByLabelText('Back to dashboard');
        expect(backButton).toBeInTheDocument();
      });
    });
  });

  describe('Tier-based Features', () => {
    it('should show upgrade prompt for restricted features', async () => {
      // Mock budget tier
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ tier: 'budget' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ scenarios: [] })
        });

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Housing search is available with Budget tier or higher.')).toBeInTheDocument();
      });
    });

    it('should show all features for professional tier', async () => {
      // Mock professional tier
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ tier: 'professional' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ scenarios: [] })
        });

      render(
        <TestWrapper>
          <OptimalLocationRouter />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('PROFESSIONAL')).toBeInTheDocument();
        
        // All tabs should be enabled
        const tabs = screen.getAllByRole('tab');
        tabs.forEach(tab => {
          expect(tab).not.toHaveAttribute('aria-disabled', 'true');
        });
      });
    });
  });
});
