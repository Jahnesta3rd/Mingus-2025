import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import HousingSearch from '../HousingSearch';

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

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('HousingSearch', () => {
  const mockOnSearch = jest.fn();
  const mockOnResults = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true,
          listings: [
            {
              id: 'listing1',
              address: '123 Main St',
              city: 'New York',
              state: 'NY',
              zip_code: '10001',
              rent: 2500,
              bedrooms: 2,
              bathrooms: 1,
              property_type: 'apartment',
              affordability_score: 85
            }
          ],
          total_results: 1
        })
      });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the housing search form', () => {
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      expect(screen.getByText('Find Your Optimal Location')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter city, state, or ZIP code')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Rent')).toBeInTheDocument();
      expect(screen.getByLabelText('Bedrooms')).toBeInTheDocument();
      expect(screen.getByLabelText('Bathrooms')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Commute Time (minutes)')).toBeInTheDocument();
      expect(screen.getByText('Search Locations')).toBeInTheDocument();
    });

    it('should render all form fields with proper labels', () => {
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Check all form fields are present
      expect(screen.getByLabelText('Location')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Rent')).toBeInTheDocument();
      expect(screen.getByLabelText('Min Rent')).toBeInTheDocument();
      expect(screen.getByLabelText('Bedrooms')).toBeInTheDocument();
      expect(screen.getByLabelText('Bathrooms')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Commute Time (minutes)')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Distance from Work (miles)')).toBeInTheDocument();
      expect(screen.getByLabelText('Housing Type')).toBeInTheDocument();
    });

    it('should render advanced options toggle', () => {
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      expect(screen.getByText('Advanced Options')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /advanced options/i })).toBeInTheDocument();
    });
  });

  describe('Form Interactions', () => {
    it('should update form values when user types', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const locationInput = screen.getByPlaceholderText('Enter city, state, or ZIP code');
      const maxRentInput = screen.getByLabelText('Max Rent');
      const bedroomsInput = screen.getByLabelText('Bedrooms');

      await user.type(locationInput, 'San Francisco, CA');
      await user.type(maxRentInput, '3000');
      await user.type(bedroomsInput, '2');

      expect(locationInput).toHaveValue('San Francisco, CA');
      expect(maxRentInput).toHaveValue(3000);
      expect(bedroomsInput).toHaveValue(2);
    });

    it('should toggle advanced options visibility', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const advancedToggle = screen.getByRole('button', { name: /advanced options/i });
      
      // Initially advanced options should be hidden
      expect(screen.queryByLabelText('Must Have Features')).not.toBeInTheDocument();
      
      // Click to show advanced options
      await user.click(advancedToggle);
      
      expect(screen.getByLabelText('Must Have Features')).toBeInTheDocument();
      expect(screen.getByLabelText('Nice to Have Features')).toBeInTheDocument();
      expect(screen.getByLabelText('Preferred Areas')).toBeInTheDocument();
    });

    it('should validate required fields before submission', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const searchButton = screen.getByText('Search Locations');
      
      // Try to submit without filling required fields
      await user.click(searchButton);
      
      // Should show validation errors
      expect(screen.getByText('Please enter a location')).toBeInTheDocument();
      expect(screen.getByText('Please enter maximum rent')).toBeInTheDocument();
    });

    it('should clear form when clear button is clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const locationInput = screen.getByPlaceholderText('Enter city, state, or ZIP code');
      const maxRentInput = screen.getByLabelText('Max Rent');
      
      // Fill form
      await user.type(locationInput, 'New York, NY');
      await user.type(maxRentInput, '2500');
      
      // Clear form
      const clearButton = screen.getByText('Clear Form');
      await user.click(clearButton);
      
      expect(locationInput).toHaveValue('');
      expect(maxRentInput).toHaveValue(0);
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Fill required fields
      await user.type(screen.getByPlaceholderText('Enter city, state, or ZIP code'), 'New York, NY');
      await user.type(screen.getByLabelText('Max Rent'), '3000');
      await user.type(screen.getByLabelText('Bedrooms'), '2');
      await user.type(screen.getByLabelText('Bathrooms'), '1');
      await user.type(screen.getByLabelText('Max Commute Time (minutes)'), '30');

      // Submit form
      const searchButton = screen.getByText('Search Locations');
      await user.click(searchButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/housing/search',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': 'Bearer test-token',
              'Content-Type': 'application/json',
              'X-CSRF-Token': expect.any(String)
            }),
            body: expect.stringContaining('"zip_code":"New York, NY"')
          })
        );
      });
    });

    it('should show loading state during search', async () => {
      const user = userEvent.setup();
      
      // Mock delayed response
      (global.fetch as jest.Mock).mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ success: true, listings: [] })
          }), 100)
        )
      );

      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Fill and submit form
      await user.type(screen.getByPlaceholderText('Enter city, state, or ZIP code'), 'New York, NY');
      await user.type(screen.getByLabelText('Max Rent'), '3000');
      await user.type(screen.getByLabelText('Bedrooms'), '2');
      await user.type(screen.getByLabelText('Bathrooms'), '1');
      await user.type(screen.getByLabelText('Max Commute Time (minutes)'), '30');
      
      await user.click(screen.getByText('Search Locations'));

      // Should show loading state
      expect(screen.getByText('Searching...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /search locations/i })).toBeDisabled();
    });

    it('should handle search success and display results', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Fill and submit form
      await user.type(screen.getByPlaceholderText('Enter city, state, or ZIP code'), 'New York, NY');
      await user.type(screen.getByLabelText('Max Rent'), '3000');
      await user.type(screen.getByLabelText('Bedrooms'), '2');
      await user.type(screen.getByLabelText('Bathrooms'), '1');
      await user.type(screen.getByLabelText('Max Commute Time (minutes)'), '30');
      
      await user.click(screen.getByText('Search Locations'));

      await waitFor(() => {
        expect(mockOnSearch).toHaveBeenCalledWith(expect.objectContaining({
          zip_code: 'New York, NY',
          max_rent: 3000,
          bedrooms: 2,
          bathrooms: 1,
          commute_time: 30
        }));
      });

      await waitFor(() => {
        expect(mockOnResults).toHaveBeenCalledWith(expect.objectContaining({
          success: true,
          listings: expect.arrayContaining([
            expect.objectContaining({
              id: 'listing1',
              address: '123 Main St',
              city: 'New York',
              state: 'NY',
              rent: 2500,
              affordability_score: 85
            })
          ])
        }));
      });
    });

    it('should handle search error and display error message', async () => {
      const user = userEvent.setup();
      
      // Mock API error
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal server error' })
      });

      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Fill and submit form
      await user.type(screen.getByPlaceholderText('Enter city, state, or ZIP code'), 'New York, NY');
      await user.type(screen.getByLabelText('Max Rent'), '3000');
      await user.type(screen.getByLabelText('Bedrooms'), '2');
      await user.type(screen.getByLabelText('Bathrooms'), '1');
      await user.type(screen.getByLabelText('Max Commute Time (minutes)'), '30');
      
      await user.click(screen.getByText('Search Locations'));

      await waitFor(() => {
        expect(screen.getByText('Search failed. Please try again.')).toBeInTheDocument();
      });
    });
  });

  describe('Tier Restrictions', () => {
    it('should show upgrade prompt for budget tier users', () => {
      render(
        <TestWrapper>
          <HousingSearch 
            onSearch={mockOnSearch} 
            onResults={mockOnResults}
            userTier="budget"
            tierFeatures={{ housing_searches_per_month: 3 }}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Housing search is available with Budget tier or higher.')).toBeInTheDocument();
      expect(screen.getByText('Upgrade to Mid-tier for unlimited searches')).toBeInTheDocument();
    });

    it('should show search limit for mid-tier users', () => {
      render(
        <TestWrapper>
          <HousingSearch 
            onSearch={mockOnSearch} 
            onResults={mockOnResults}
            userTier="mid_tier"
            tierFeatures={{ housing_searches_per_month: 10 }}
          />
        </TestWrapper>
      );

      expect(screen.getByText('10 searches remaining this month')).toBeInTheDocument();
    });

    it('should show unlimited searches for professional tier', () => {
      render(
        <TestWrapper>
          <HousingSearch 
            onSearch={mockOnSearch} 
            onResults={mockOnResults}
            userTier="professional"
            tierFeatures={{ housing_searches_per_month: -1 }}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Unlimited searches')).toBeInTheDocument();
    });
  });

  describe('Advanced Features', () => {
    it('should allow setting must-have features', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Show advanced options
      await user.click(screen.getByRole('button', { name: /advanced options/i }));

      const mustHaveInput = screen.getByLabelText('Must Have Features');
      await user.type(mustHaveInput, 'parking, laundry, gym');

      expect(mustHaveInput).toHaveValue('parking, laundry, gym');
    });

    it('should allow setting nice-to-have features', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Show advanced options
      await user.click(screen.getByRole('button', { name: /advanced options/i }));

      const niceToHaveInput = screen.getByLabelText('Nice to Have Features');
      await user.type(niceToHaveInput, 'pool, balcony, pet-friendly');

      expect(niceToHaveInput).toHaveValue('pool, balcony, pet-friendly');
    });

    it('should allow setting preferred areas', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Show advanced options
      await user.click(screen.getByRole('button', { name: /advanced options/i }));

      const preferredAreasInput = screen.getByLabelText('Preferred Areas');
      await user.type(preferredAreasInput, 'downtown, midtown, upper east side');

      expect(preferredAreasInput).toHaveValue('downtown, midtown, upper east side');
    });
  });

  describe('Accessibility', () => {
    it('should have proper form labels and ARIA attributes', () => {
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Check form has proper role
      const form = screen.getByRole('form');
      expect(form).toBeInTheDocument();

      // Check all inputs have proper labels
      const locationInput = screen.getByLabelText('Location');
      expect(locationInput).toHaveAttribute('aria-required', 'true');

      const maxRentInput = screen.getByLabelText('Max Rent');
      expect(maxRentInput).toHaveAttribute('type', 'number');
      expect(maxRentInput).toHaveAttribute('min', '0');

      const bedroomsInput = screen.getByLabelText('Bedrooms');
      expect(bedroomsInput).toHaveAttribute('type', 'number');
      expect(bedroomsInput).toHaveAttribute('min', '0');
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const locationInput = screen.getByPlaceholderText('Enter city, state, or ZIP code');
      const maxRentInput = screen.getByLabelText('Max Rent');
      const bedroomsInput = screen.getByLabelText('Bedrooms');

      // Tab through form fields
      await user.tab();
      expect(locationInput).toHaveFocus();

      await user.tab();
      expect(maxRentInput).toHaveFocus();

      await user.tab();
      expect(bedroomsInput).toHaveFocus();
    });

    it('should announce validation errors to screen readers', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      // Try to submit without required fields
      await user.click(screen.getByText('Search Locations'));

      const errorMessages = screen.getAllByRole('alert');
      expect(errorMessages.length).toBeGreaterThan(0);
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should stack form fields vertically on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const form = screen.getByRole('form');
      expect(form).toHaveClass('mobile-stack');
    });

    it('should show mobile-optimized button layout', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const searchButton = screen.getByText('Search Locations');
      expect(searchButton).toHaveClass('mobile-full-width');
    });
  });

  describe('Performance', () => {
    it('should debounce location input to avoid excessive API calls', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const locationInput = screen.getByPlaceholderText('Enter city, state, or ZIP code');
      
      // Type quickly
      await user.type(locationInput, 'New York');
      
      // Wait for debounce
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('should not re-render unnecessarily when props change', () => {
      const { rerender } = render(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const initialRenderCount = screen.getByRole('form').getAttribute('data-render-count');
      
      // Rerender with same props
      rerender(
        <TestWrapper>
          <HousingSearch onSearch={mockOnSearch} onResults={mockOnResults} />
        </TestWrapper>
      );

      const afterRerenderCount = screen.getByRole('form').getAttribute('data-render-count');
      expect(afterRerenderCount).toBe(initialRenderCount);
    });
  });
});
