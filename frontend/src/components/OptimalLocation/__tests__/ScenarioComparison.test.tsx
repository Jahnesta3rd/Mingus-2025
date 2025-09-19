import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import ScenarioComparison from '../ScenarioComparison';

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

describe('ScenarioComparison', () => {
  const mockScenarios = [
    {
      id: 1,
      scenario_name: 'Downtown Apartment',
      housing_data: {
        address: '123 Main St',
        city: 'New York',
        state: 'NY',
        zip_code: '10001',
        rent: 3000,
        bedrooms: 2,
        bathrooms: 1,
        property_type: 'apartment'
      },
      financial_impact: {
        monthly_rent: 3000,
        affordability_score: 85,
        total_monthly_housing_cost: 3200,
        rent_to_income_ratio: 0.25
      },
      commute_data: {
        estimated_commute_time: 20,
        estimated_distance: 8.5,
        commute_cost_per_month: 200
      },
      career_data: {
        nearby_job_opportunities: 25,
        average_salary_in_area: 85000,
        career_growth_potential: 'High'
      },
      is_favorite: false,
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: 2,
      scenario_name: 'Suburban House',
      housing_data: {
        address: '456 Oak Ave',
        city: 'Brooklyn',
        state: 'NY',
        zip_code: '11201',
        rent: 2200,
        bedrooms: 3,
        bathrooms: 2,
        property_type: 'house'
      },
      financial_impact: {
        monthly_rent: 2200,
        affordability_score: 75,
        total_monthly_housing_cost: 2400,
        rent_to_income_ratio: 0.18
      },
      commute_data: {
        estimated_commute_time: 35,
        estimated_distance: 15.2,
        commute_cost_per_month: 300
      },
      career_data: {
        nearby_job_opportunities: 15,
        average_salary_in_area: 75000,
        career_growth_potential: 'Medium'
      },
      is_favorite: true,
      created_at: '2024-01-14T15:45:00Z'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true,
          scenarios: mockScenarios
        })
      });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the scenario comparison interface', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      expect(screen.getByText('Location Scenarios')).toBeInTheDocument();
      expect(screen.getByText('Compare Scenarios')).toBeInTheDocument();
      expect(screen.getByText('Downtown Apartment')).toBeInTheDocument();
      expect(screen.getByText('Suburban House')).toBeInTheDocument();
    });

    it('should render scenario cards with all required information', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Check first scenario card
      expect(screen.getByText('Downtown Apartment')).toBeInTheDocument();
      expect(screen.getByText('123 Main St, New York, NY 10001')).toBeInTheDocument();
      expect(screen.getByText('$3,000/month')).toBeInTheDocument();
      expect(screen.getByText('2 bed • 1 bath')).toBeInTheDocument();
      expect(screen.getByText('85% Affordability Score')).toBeInTheDocument();

      // Check second scenario card
      expect(screen.getByText('Suburban House')).toBeInTheDocument();
      expect(screen.getByText('456 Oak Ave, Brooklyn, NY 11201')).toBeInTheDocument();
      expect(screen.getByText('$2,200/month')).toBeInTheDocument();
      expect(screen.getByText('3 bed • 2 bath')).toBeInTheDocument();
      expect(screen.getByText('75% Affordability Score')).toBeInTheDocument();
    });

    it('should render comparison table when scenarios are selected', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios for comparison
      const scenario1Checkbox = screen.getByLabelText('Select Downtown Apartment for comparison');
      const scenario2Checkbox = screen.getByLabelText('Select Suburban House for comparison');
      
      await user.click(scenario1Checkbox);
      await user.click(scenario2Checkbox);

      // Click compare button
      await user.click(screen.getByText('Compare Selected'));

      await waitFor(() => {
        expect(screen.getByText('Scenario Comparison')).toBeInTheDocument();
        expect(screen.getByText('Downtown Apartment')).toBeInTheDocument();
        expect(screen.getByText('Suburban House')).toBeInTheDocument();
      });
    });

    it('should show empty state when no scenarios are provided', () => {
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={[]} />
        </TestWrapper>
      );

      expect(screen.getByText('No scenarios saved yet')).toBeInTheDocument();
      expect(screen.getByText('Create your first housing scenario to get started')).toBeInTheDocument();
      expect(screen.getByText('Create Scenario')).toBeInTheDocument();
    });
  });

  describe('Scenario Selection', () => {
    it('should allow selecting multiple scenarios for comparison', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      const scenario1Checkbox = screen.getByLabelText('Select Downtown Apartment for comparison');
      const scenario2Checkbox = screen.getByLabelText('Select Suburban House for comparison');
      
      // Select first scenario
      await user.click(scenario1Checkbox);
      expect(scenario1Checkbox).toBeChecked();
      expect(screen.getByText('1 scenario selected')).toBeInTheDocument();

      // Select second scenario
      await user.click(scenario2Checkbox);
      expect(scenario2Checkbox).toBeChecked();
      expect(screen.getByText('2 scenarios selected')).toBeInTheDocument();
    });

    it('should limit selection to maximum number of scenarios', async () => {
      const user = userEvent.setup();
      
      // Create more scenarios than the limit
      const manyScenarios = Array.from({ length: 6 }, (_, i) => ({
        ...mockScenarios[0],
        id: i + 1,
        scenario_name: `Scenario ${i + 1}`
      }));

      render(
        <TestWrapper>
          <ScenarioComparison scenarios={manyScenarios} maxSelection={3} />
        </TestWrapper>
      );

      // Select first 3 scenarios
      for (let i = 0; i < 3; i++) {
        const checkbox = screen.getByLabelText(`Select Scenario ${i + 1} for comparison`);
        await user.click(checkbox);
      }

      // Try to select 4th scenario
      const fourthCheckbox = screen.getByLabelText('Select Scenario 4 for comparison');
      await user.click(fourthCheckbox);

      expect(fourthCheckbox).not.toBeChecked();
      expect(screen.getByText('Maximum 3 scenarios can be compared')).toBeInTheDocument();
    });

    it('should clear all selections when clear button is clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios
      const scenario1Checkbox = screen.getByLabelText('Select Downtown Apartment for comparison');
      const scenario2Checkbox = screen.getByLabelText('Select Suburban House for comparison');
      
      await user.click(scenario1Checkbox);
      await user.click(scenario2Checkbox);

      // Clear selections
      await user.click(screen.getByText('Clear Selection'));

      expect(scenario1Checkbox).not.toBeChecked();
      expect(scenario2Checkbox).not.toBeChecked();
      expect(screen.queryByText('scenarios selected')).not.toBeInTheDocument();
    });
  });

  describe('Comparison Features', () => {
    it('should display detailed comparison table', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios and compare
      await user.click(screen.getByLabelText('Select Downtown Apartment for comparison'));
      await user.click(screen.getByLabelText('Select Suburban House for comparison'));
      await user.click(screen.getByText('Compare Selected'));

      await waitFor(() => {
        // Check comparison table headers
        expect(screen.getByText('Criteria')).toBeInTheDocument();
        expect(screen.getByText('Downtown Apartment')).toBeInTheDocument();
        expect(screen.getByText('Suburban House')).toBeInTheDocument();

        // Check comparison data
        expect(screen.getByText('Monthly Rent')).toBeInTheDocument();
        expect(screen.getByText('$3,000')).toBeInTheDocument();
        expect(screen.getByText('$2,200')).toBeInTheDocument();

        expect(screen.getByText('Affordability Score')).toBeInTheDocument();
        expect(screen.getByText('85%')).toBeInTheDocument();
        expect(screen.getByText('75%')).toBeInTheDocument();

        expect(screen.getByText('Commute Time')).toBeInTheDocument();
        expect(screen.getByText('20 min')).toBeInTheDocument();
        expect(screen.getByText('35 min')).toBeInTheDocument();
      });
    });

    it('should highlight best values in comparison', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios and compare
      await user.click(screen.getByLabelText('Select Downtown Apartment for comparison'));
      await user.click(screen.getByLabelText('Select Suburban House for comparison'));
      await user.click(screen.getByText('Compare Selected'));

      await waitFor(() => {
        // Best affordability score should be highlighted
        const bestAffordability = screen.getByText('85%').closest('td');
        expect(bestAffordability).toHaveClass('best-value');

        // Best commute time should be highlighted
        const bestCommute = screen.getByText('20 min').closest('td');
        expect(bestCommute).toHaveClass('best-value');
      });
    });

    it('should allow switching between different comparison views', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios and compare
      await user.click(screen.getByLabelText('Select Downtown Apartment for comparison'));
      await user.click(screen.getByLabelText('Select Suburban House for comparison'));
      await user.click(screen.getByText('Compare Selected'));

      await waitFor(() => {
        expect(screen.getByText('Scenario Comparison')).toBeInTheDocument();
      });

      // Switch to financial comparison
      await user.click(screen.getByText('Financial'));
      
      expect(screen.getByText('Financial Comparison')).toBeInTheDocument();
      expect(screen.getByText('Monthly Rent')).toBeInTheDocument();
      expect(screen.getByText('Total Monthly Cost')).toBeInTheDocument();

      // Switch to location comparison
      await user.click(screen.getByText('Location'));
      
      expect(screen.getByText('Location Comparison')).toBeInTheDocument();
      expect(screen.getByText('Address')).toBeInTheDocument();
      expect(screen.getByText('Neighborhood')).toBeInTheDocument();
    });
  });

  describe('Scenario Management', () => {
    it('should allow favoriting scenarios', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // First scenario is not favorited
      const favoriteButton1 = screen.getByLabelText('Add Downtown Apartment to favorites');
      expect(favoriteButton1).toBeInTheDocument();

      // Second scenario is already favorited
      const favoriteButton2 = screen.getByLabelText('Remove Suburban House from favorites');
      expect(favoriteButton2).toBeInTheDocument();

      // Toggle favorite status
      await user.click(favoriteButton1);
      expect(screen.getByLabelText('Remove Downtown Apartment from favorites')).toBeInTheDocument();
    });

    it('should allow deleting scenarios', async () => {
      const user = userEvent.setup();
      const mockOnDelete = jest.fn();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} onDelete={mockOnDelete} />
        </TestWrapper>
      );

      // Click delete button for first scenario
      const deleteButton = screen.getByLabelText('Delete Downtown Apartment scenario');
      await user.click(deleteButton);

      // Confirm deletion
      await user.click(screen.getByText('Delete Scenario'));

      expect(mockOnDelete).toHaveBeenCalledWith(1);
    });

    it('should show confirmation dialog before deleting', async () => {
      const user = userEvent.setup();
      const mockOnDelete = jest.fn();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} onDelete={mockOnDelete} />
        </TestWrapper>
      );

      // Click delete button
      const deleteButton = screen.getByLabelText('Delete Downtown Apartment scenario');
      await user.click(deleteButton);

      // Should show confirmation dialog
      expect(screen.getByText('Delete Scenario?')).toBeInTheDocument();
      expect(screen.getByText('Are you sure you want to delete this scenario?')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Delete Scenario')).toBeInTheDocument();

      // Cancel deletion
      await user.click(screen.getByText('Cancel'));
      expect(mockOnDelete).not.toHaveBeenCalled();
    });

    it('should allow editing scenario names', async () => {
      const user = userEvent.setup();
      const mockOnUpdate = jest.fn();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} onUpdate={mockOnUpdate} />
        </TestWrapper>
      );

      // Click edit button
      const editButton = screen.getByLabelText('Edit Downtown Apartment scenario name');
      await user.click(editButton);

      // Should show edit input
      const editInput = screen.getByDisplayValue('Downtown Apartment');
      expect(editInput).toBeInTheDocument();

      // Update name
      await user.clear(editInput);
      await user.type(editInput, 'Updated Apartment Name');

      // Save changes
      await user.click(screen.getByText('Save'));

      expect(mockOnUpdate).toHaveBeenCalledWith(1, { scenario_name: 'Updated Apartment Name' });
    });
  });

  describe('Sorting and Filtering', () => {
    it('should allow sorting scenarios by different criteria', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Sort by rent (ascending)
      await user.click(screen.getByText('Sort by'));
      await user.click(screen.getByText('Monthly Rent'));

      // Check order (should be Suburban House first, then Downtown Apartment)
      const scenarioCards = screen.getAllByTestId('scenario-card');
      expect(scenarioCards[0]).toHaveTextContent('Suburban House');
      expect(scenarioCards[1]).toHaveTextContent('Downtown Apartment');

      // Sort by affordability score (descending)
      await user.click(screen.getByText('Sort by'));
      await user.click(screen.getByText('Affordability Score'));

      // Check order (should be Downtown Apartment first, then Suburban House)
      const updatedScenarioCards = screen.getAllByTestId('scenario-card');
      expect(updatedScenarioCards[0]).toHaveTextContent('Downtown Apartment');
      expect(updatedScenarioCards[1]).toHaveTextContent('Suburban House');
    });

    it('should allow filtering scenarios by criteria', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Filter by affordability score
      await user.click(screen.getByText('Filter'));
      await user.click(screen.getByText('High Affordability'));

      // Should only show scenarios with high affordability
      expect(screen.getByText('Downtown Apartment')).toBeInTheDocument();
      expect(screen.queryByText('Suburban House')).not.toBeInTheDocument();
    });

    it('should show filter count and clear filters', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Apply filter
      await user.click(screen.getByText('Filter'));
      await user.click(screen.getByText('High Affordability'));

      // Should show filter count
      expect(screen.getByText('1 of 2 scenarios')).toBeInTheDocument();

      // Clear filters
      await user.click(screen.getByText('Clear Filters'));

      // Should show all scenarios
      expect(screen.getByText('Downtown Apartment')).toBeInTheDocument();
      expect(screen.getByText('Suburban House')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Check main container has proper role
      const mainContainer = screen.getByRole('main');
      expect(mainContainer).toBeInTheDocument();

      // Check scenario cards have proper structure
      const scenarioCards = screen.getAllByTestId('scenario-card');
      scenarioCards.forEach(card => {
        expect(card).toHaveAttribute('role', 'article');
      });

      // Check comparison table has proper structure
      const compareButton = screen.getByRole('button', { name: /compare selected/i });
      expect(compareButton).toBeInTheDocument();
    });

    it('should support keyboard navigation for scenario selection', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Tab to first checkbox
      await user.tab();
      const firstCheckbox = screen.getByLabelText('Select Downtown Apartment for comparison');
      expect(firstCheckbox).toHaveFocus();

      // Tab to second checkbox
      await user.tab();
      const secondCheckbox = screen.getByLabelText('Select Suburban House for comparison');
      expect(secondCheckbox).toHaveFocus();
    });

    it('should announce comparison results to screen readers', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios and compare
      await user.click(screen.getByLabelText('Select Downtown Apartment for comparison'));
      await user.click(screen.getByLabelText('Select Suburban House for comparison'));
      await user.click(screen.getByText('Compare Selected'));

      await waitFor(() => {
        const comparisonTable = screen.getByRole('table');
        expect(comparisonTable).toHaveAttribute('aria-label', 'Scenario comparison table');
      });
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should stack scenario cards vertically on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      const scenarioCards = screen.getAllByTestId('scenario-card');
      scenarioCards.forEach(card => {
        expect(card).toHaveClass('mobile-stack');
      });
    });

    it('should show mobile-optimized comparison view', async () => {
      const user = userEvent.setup();
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      // Select scenarios and compare
      await user.click(screen.getByLabelText('Select Downtown Apartment for comparison'));
      await user.click(screen.getByLabelText('Select Suburban House for comparison'));
      await user.click(screen.getByText('Compare Selected'));

      await waitFor(() => {
        const comparisonTable = screen.getByRole('table');
        expect(comparisonTable).toHaveClass('mobile-comparison');
      });
    });
  });

  describe('Performance', () => {
    it('should not re-render unnecessarily when props change', () => {
      const { rerender } = render(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      const initialRenderCount = screen.getByRole('main').getAttribute('data-render-count');
      
      // Rerender with same props
      rerender(
        <TestWrapper>
          <ScenarioComparison scenarios={mockScenarios} />
        </TestWrapper>
      );

      const afterRerenderCount = screen.getByRole('main').getAttribute('data-render-count');
      expect(afterRerenderCount).toBe(initialRenderCount);
    });

    it('should handle large numbers of scenarios efficiently', () => {
      const manyScenarios = Array.from({ length: 100 }, (_, i) => ({
        ...mockScenarios[0],
        id: i + 1,
        scenario_name: `Scenario ${i + 1}`
      }));

      const startTime = performance.now();
      
      render(
        <TestWrapper>
          <ScenarioComparison scenarios={manyScenarios} />
        </TestWrapper>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (less than 1 second)
      expect(renderTime).toBeLessThan(1000);
    });
  });
});
