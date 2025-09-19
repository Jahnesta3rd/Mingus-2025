import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import ScenarioComparison from '../ScenarioComparison';

// Mock the tier restrictions hook with realistic behavior
const mockUseTierRestrictions = jest.fn();
jest.mock('../../../hooks/useTierRestrictions', () => ({
  useTierRestrictions: () => mockUseTierRestrictions(),
  TierGate: ({ children, feature }: { children: React.ReactNode; feature: string }) => {
    const { hasFeatureAccess } = mockUseTierRestrictions();
    return hasFeatureAccess(feature) ? <>{children}</> : null;
  }
}));

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  ComposedChart: ({ children }: { children: React.ReactNode }) => <div data-testid="composed-chart">{children}</div>,
  ScatterChart: ({ children }: { children: React.ReactNode }) => <div data-testid="scatter-chart">{children}</div>,
  Scatter: () => <div data-testid="scatter" />
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

const mockCurrentSituation = {
  rent: 1400,
  commute_cost: 0,
  total_monthly_cost: 1400,
  affordability_score: 75,
  location: 'Current Location',
  commute_time: 0
};

const mockScenarios = [
  {
    id: 1,
    scenario_name: 'Downtown Apartment',
    housing_data: {
      address: '123 Main St, Downtown',
      rent: 1245,
      bedrooms: 2,
      bathrooms: 2,
      square_feet: 1200,
      housing_type: 'apartment',
      amenities: ['parking', 'laundry', 'gym'],
      neighborhood: 'Downtown',
      zip_code: '12345',
      latitude: 40.7128,
      longitude: -74.0060
    },
    commute_data: {
      distance_miles: 8.5,
      drive_time_minutes: 25,
      public_transit_time_minutes: 35,
      walking_time_minutes: 15,
      gas_cost_daily: 4.50,
      public_transit_cost_daily: 5.00,
      parking_cost_daily: 12.00,
      total_daily_cost: 16.50,
      total_monthly_cost: 65
    },
    financial_impact: {
      affordability_score: 85,
      rent_to_income_ratio: 0.28,
      total_housing_cost: 1310,
      monthly_savings: 90,
      annual_savings: 1080,
      cost_of_living_index: 1.2,
      property_tax_estimate: 0,
      insurance_estimate: 50
    },
    career_data: {
      job_opportunities_count: 150,
      average_salary: 75000,
      salary_range_min: 55000,
      salary_range_max: 95000,
      industry_concentration: ['tech', 'finance', 'healthcare'],
      remote_work_friendly: true,
      commute_impact_score: 75
    },
    is_favorite: false,
    created_at: '2024-01-01T00:00:00Z'
  }
];

describe('ScenarioComparison Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Budget Tier Integration', () => {
    beforeEach(() => {
      mockUseTierRestrictions.mockReturnValue({
        hasFeatureAccess: jest.fn((feature: string) => {
          // Budget tier has limited access
          if (feature === 'career_integration') return false;
          if (feature === 'export_functionality') return false;
          return true;
        }),
        canPerformAction: jest.fn(() => true)
      });
    });

    it('hides career integration tab for budget users', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="budget"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.queryByRole('tab', { name: /career integration/i })).not.toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /financial impact/i })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /comparison table/i })).toBeInTheDocument();
      });
    });

    it('shows upgrade prompt for export functionality', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="budget"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      // Select a scenario to enable action buttons
      const downtownCard = screen.getByText('Downtown Apartment').closest('[role="button"]');
      fireEvent.click(downtownCard!);

      await waitFor(() => {
        const exportButton = screen.getByText('Export Analysis');
        expect(exportButton).toBeDisabled();
        expect(exportButton.closest('span')).toHaveAttribute('title', 'Export functionality available in Professional tier');
      });
    });
  });

  describe('Mid-tier Integration', () => {
    beforeEach(() => {
      mockUseTierRestrictions.mockReturnValue({
        hasFeatureAccess: jest.fn((feature: string) => {
          // Mid-tier has career integration but no export
          if (feature === 'career_integration') return true;
          if (feature === 'export_functionality') return false;
          return true;
        }),
        canPerformAction: jest.fn(() => true)
      });
    });

    it('shows career integration tab for mid-tier users', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="mid_tier"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /career integration/i })).toBeInTheDocument();
      });

      // Click on career integration tab
      const careerTab = screen.getByRole('tab', { name: /career integration/i });
      fireEvent.click(careerTab);

      await waitFor(() => {
        expect(screen.getByText('Career Opportunities - Downtown Apartment')).toBeInTheDocument();
        expect(screen.getByText('150 opportunities within 30 miles')).toBeInTheDocument();
      });
    });

    it('shows upgrade prompt for export functionality', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="mid_tier"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      // Select a scenario to enable action buttons
      const downtownCard = screen.getByText('Downtown Apartment').closest('[role="button"]');
      fireEvent.click(downtownCard!);

      await waitFor(() => {
        const exportButton = screen.getByText('Export Analysis');
        expect(exportButton).toBeDisabled();
      });
    });
  });

  describe('Professional Tier Integration', () => {
    beforeEach(() => {
      mockUseTierRestrictions.mockReturnValue({
        hasFeatureAccess: jest.fn(() => true), // Professional has all features
        canPerformAction: jest.fn(() => true)
      });
    });

    it('shows all features for professional users', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="professional"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /career integration/i })).toBeInTheDocument();
      });

      // Select a scenario to enable action buttons
      const downtownCard = screen.getByText('Downtown Apartment').closest('[role="button"]');
      fireEvent.click(downtownCard!);

      await waitFor(() => {
        const exportButton = screen.getByText('Export Analysis');
        expect(exportButton).not.toBeDisabled();
      });
    });

    it('allows export functionality for professional users', async () => {
      const mockOnExportAnalysis = jest.fn();
      
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="professional"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
            onExportAnalysis={mockOnExportAnalysis}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      // Select a scenario
      const downtownCard = screen.getByText('Downtown Apartment').closest('[role="button"]');
      fireEvent.click(downtownCard!);

      await waitFor(() => {
        const exportButton = screen.getByText('Export Analysis');
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Export Analysis')).toBeInTheDocument();
        expect(screen.getByText('Select export format for your scenario comparison:')).toBeInTheDocument();
      });

      // Click export button in dialog
      const exportConfirmButton = screen.getByText('Export');
      fireEvent.click(exportConfirmButton);

      expect(mockOnExportAnalysis).toHaveBeenCalledWith(1);
    });
  });

  describe('Component Interaction Flow', () => {
    beforeEach(() => {
      mockUseTierRestrictions.mockReturnValue({
        hasFeatureAccess: jest.fn(() => true),
        canPerformAction: jest.fn(() => true)
      });
    });

    it('handles complete user interaction flow', async () => {
      const mockOnMakePrimary = jest.fn();
      const mockOnToggleFavorite = jest.fn();
      const mockOnShareScenario = jest.fn();
      const mockOnDeleteScenario = jest.fn();

      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="professional"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
            onMakePrimary={mockOnMakePrimary}
            onToggleFavorite={mockOnToggleFavorite}
            onShareScenario={mockOnShareScenario}
            onDeleteScenario={mockOnDeleteScenario}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      // 1. Select a scenario
      const downtownCard = screen.getByText('Downtown Apartment').closest('[role="button"]');
      fireEvent.click(downtownCard!);

      await waitFor(() => {
        expect(screen.getByText('Selected for Comparison')).toBeInTheDocument();
      });

      // 2. Toggle favorite
      const starButton = screen.getAllByRole('button').find(button => 
        button.querySelector('[data-testid="StarBorderIcon"]') || 
        button.querySelector('[data-testid="StarIcon"]')
      );
      if (starButton) {
        fireEvent.click(starButton);
        expect(mockOnToggleFavorite).toHaveBeenCalledWith(1);
      }

      // 3. Make primary choice
      const makePrimaryButton = screen.getByText('Make Primary Choice');
      fireEvent.click(makePrimaryButton);
      expect(mockOnMakePrimary).toHaveBeenCalledWith(1);

      // 4. Share scenario
      const shareButton = screen.getByText('Share Scenario');
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(screen.getByText('Share Scenario')).toBeInTheDocument();
      });

      const shareConfirmButton = screen.getByText('Share');
      fireEvent.click(shareConfirmButton);
      expect(mockOnShareScenario).toHaveBeenCalledWith(1);

      // 5. Delete scenario
      const deleteButton = screen.getByText('Delete Scenario');
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Delete Scenario')).toBeInTheDocument();
      });

      const deleteConfirmButton = screen.getByText('Delete');
      fireEvent.click(deleteConfirmButton);
      expect(mockOnDeleteScenario).toHaveBeenCalledWith(1);
    });

    it('navigates between tabs correctly', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="professional"
            scenarios={mockScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      // Start on Financial Impact tab
      expect(screen.getByText('Monthly Cash Flow Comparison')).toBeInTheDocument();

      // Switch to Comparison Table
      const comparisonTab = screen.getByRole('tab', { name: /comparison table/i });
      fireEvent.click(comparisonTab);

      await waitFor(() => {
        expect(screen.getByText('Detailed Comparison')).toBeInTheDocument();
        expect(screen.getByText('Rent')).toBeInTheDocument();
      });

      // Switch to Career Integration
      const careerTab = screen.getByRole('tab', { name: /career integration/i });
      fireEvent.click(careerTab);

      await waitFor(() => {
        expect(screen.getByText('Career Opportunities - Downtown Apartment')).toBeInTheDocument();
      });

      // Switch back to Financial Impact
      const financialTab = screen.getByRole('tab', { name: /financial impact/i });
      fireEvent.click(financialTab);

      await waitFor(() => {
        expect(screen.getByText('Monthly Cash Flow Comparison')).toBeInTheDocument();
      });
    });
  });

  describe('Data Validation and Error Handling', () => {
    beforeEach(() => {
      mockUseTierRestrictions.mockReturnValue({
        hasFeatureAccess: jest.fn(() => true),
        canPerformAction: jest.fn(() => true)
      });
    });

    it('handles empty scenarios array', async () => {
      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="professional"
            scenarios={[]}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.getByText('Current Situation')).toBeInTheDocument();
        // Should not crash with empty scenarios
      });
    });

    it('handles malformed scenario data gracefully', async () => {
      const malformedScenarios = [
        {
          id: 1,
          scenario_name: 'Test Scenario',
          housing_data: null, // Malformed data
          commute_data: {},
          financial_impact: {},
          career_data: {},
          is_favorite: false,
          created_at: '2024-01-01T00:00:00Z'
        }
      ];

      render(
        <TestWrapper>
          <ScenarioComparison
            userTier="professional"
            scenarios={malformedScenarios}
            currentSituation={mockCurrentSituation}
          />
        </TestWrapper>
      );

      jest.advanceTimersByTime(1000);

      await waitFor(() => {
        // Should not crash, but may show error states
        expect(screen.getByText('Test Scenario')).toBeInTheDocument();
      });
    });
  });
});
