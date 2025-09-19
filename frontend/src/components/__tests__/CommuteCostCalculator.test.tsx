import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import CommuteCostCalculator from '../CommuteCostCalculator';

// Mock the analytics hook
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackInteraction: jest.fn(),
    trackError: jest.fn()
  })
}));

// Mock fetch
global.fetch = jest.fn();

// Mock data
const mockVehicles = [
  {
    id: 'vehicle_1',
    make: 'Honda',
    model: 'Civic',
    year: 2020,
    mpg: 32,
    fuelType: 'gasoline' as const,
    currentMileage: 25000,
    monthlyMiles: 1200
  },
  {
    id: 'vehicle_2',
    make: 'Toyota',
    model: 'Prius',
    year: 2019,
    mpg: 50,
    fuelType: 'hybrid' as const,
    currentMileage: 30000,
    monthlyMiles: 1000
  }
];

const mockJobOffer = {
  id: 'job_1',
  title: 'Software Engineer',
  company: 'Tech Corp',
  location: 'San Francisco, CA',
  salary: {
    min: 120000,
    max: 150000,
    median: 135000
  },
  benefits: ['Health Insurance', '401k', 'Remote Work'],
  remoteFriendly: true
};

describe('CommuteCostCalculator', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('renders the commute cost calculator', () => {
    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Commute Cost Calculator')).toBeInTheDocument();
    expect(screen.getByText('Calculate true compensation including transportation costs')).toBeInTheDocument();
  });

  it('displays job offer information when provided', () => {
    render(
      <CommuteCostCalculator
        jobOffer={mockJobOffer}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    expect(screen.getByText('Tech Corp • San Francisco, CA')).toBeInTheDocument();
    expect(screen.getByText('$135,000')).toBeInTheDocument();
  });

  it('renders vehicle selection options', () => {
    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    expect(screen.getByText('2020 Honda Civic')).toBeInTheDocument();
    expect(screen.getByText('2019 Toyota Prius')).toBeInTheDocument();
  });

  it('handles job location input', async () => {
    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    const jobLocationInput = screen.getByPlaceholderText('Enter job address');
    fireEvent.change(jobLocationInput, { target: { value: '123 Tech Street' } });

    expect(jobLocationInput).toHaveValue('123 Tech Street');
  });

  it('handles home location input', async () => {
    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    const homeLocationInput = screen.getByPlaceholderText('Enter home address');
    fireEvent.change(homeLocationInput, { target: { value: '456 Home Avenue' } });

    expect(homeLocationInput).toHaveValue('456 Home Avenue');
  });

  it('handles vehicle selection', () => {
    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    const hondaButton = screen.getByText('2020 Honda Civic').closest('button');
    fireEvent.click(hondaButton!);

    expect(hondaButton).toHaveClass('border-violet-500');
  });

  it('shows address autocomplete suggestions', async () => {
    // Mock autocomplete response
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        suggestions: [
          {
            description: '123 Tech Street, San Francisco, CA',
            place_id: 'test_place_1',
            formatted_address: '123 Tech Street, San Francisco, CA'
          }
        ]
      })
    });

    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    const jobLocationInput = screen.getByPlaceholderText('Enter job address');
    fireEvent.change(jobLocationInput, { target: { value: '123 Tech' } });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/geocoding/autocomplete', expect.any(Object));
    });
  });

  it('calculates commute costs when all inputs are provided', async () => {
    // Mock geocoding responses
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.7749, lng: -122.4194 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.8044, lng: -122.2712 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          distance: 15.5
        })
      });

    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in locations
    const jobLocationInput = screen.getByPlaceholderText('Enter job address');
    const homeLocationInput = screen.getByPlaceholderText('Enter home address');
    
    fireEvent.change(jobLocationInput, { target: { value: '123 Tech Street' } });
    fireEvent.change(homeLocationInput, { target: { value: '456 Home Avenue' } });

    // Select vehicle
    const hondaButton = screen.getByText('2020 Honda Civic').closest('button');
    fireEvent.click(hondaButton!);

    await waitFor(() => {
      expect(screen.getByText('Weekly Commute Costs')).toBeInTheDocument();
    });
  });

  it('displays cost breakdown when calculation is complete', async () => {
    // Mock successful calculation
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.7749, lng: -122.4194 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.8044, lng: -122.2712 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          distance: 15.5
        })
      });

    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in all required fields
    fireEvent.change(screen.getByPlaceholderText('Enter job address'), { 
      target: { value: '123 Tech Street' } 
    });
    fireEvent.change(screen.getByPlaceholderText('Enter home address'), { 
      target: { value: '456 Home Avenue' } 
    });
    fireEvent.click(screen.getByText('2020 Honda Civic').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Fuel')).toBeInTheDocument();
      expect(screen.getByText('Maintenance')).toBeInTheDocument();
      expect(screen.getByText('Depreciation')).toBeInTheDocument();
    });
  });

  it('shows true compensation when job offer is provided', async () => {
    // Mock successful calculation
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.7749, lng: -122.4194 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.8044, lng: -122.2712 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          distance: 15.5
        })
      });

    render(
      <CommuteCostCalculator
        jobOffer={mockJobOffer}
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in all required fields
    fireEvent.change(screen.getByPlaceholderText('Enter job address'), { 
      target: { value: '123 Tech Street' } 
    });
    fireEvent.change(screen.getByPlaceholderText('Enter home address'), { 
      target: { value: '456 Home Avenue' } 
    });
    fireEvent.click(screen.getByText('2020 Honda Civic').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('True Monthly Compensation')).toBeInTheDocument();
    });
  });

  it('handles vehicle comparison when multiple vehicles are available', async () => {
    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in locations and select vehicle
    fireEvent.change(screen.getByPlaceholderText('Enter job address'), { 
      target: { value: '123 Tech Street' } 
    });
    fireEvent.change(screen.getByPlaceholderText('Enter home address'), { 
      target: { value: '456 Home Avenue' } 
    });
    fireEvent.click(screen.getByText('2020 Honda Civic').closest('button')!);

    // Mock successful calculation
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.7749, lng: -122.4194 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.8044, lng: -122.2712 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          distance: 15.5
        })
      });

    await waitFor(() => {
      expect(screen.getByText('Show Comparison')).toBeInTheDocument();
    });

    // Click comparison button
    fireEvent.click(screen.getByText('Show Comparison'));

    await waitFor(() => {
      expect(screen.getByText('Vehicle Comparison')).toBeInTheDocument();
    });
  });

  it('handles save scenario functionality', async () => {
    const mockOnSaveScenario = jest.fn();
    
    // Mock successful calculation
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.7749, lng: -122.4194 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          coordinates: { lat: 37.8044, lng: -122.2712 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          distance: 15.5
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Scenario saved successfully'
        })
      });

    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={mockOnSaveScenario}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in all required fields
    fireEvent.change(screen.getByPlaceholderText('Enter job address'), { 
      target: { value: '123 Tech Street' } 
    });
    fireEvent.change(screen.getByPlaceholderText('Enter home address'), { 
      target: { value: '456 Home Avenue' } 
    });
    fireEvent.click(screen.getByText('2020 Honda Civic').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Save Scenario')).toBeInTheDocument();
    });

    // Click save scenario button
    fireEvent.click(screen.getByText('Save Scenario'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/commute/scenarios', expect.any(Object));
    });
  });

  it('displays error messages when API calls fail', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in locations
    fireEvent.change(screen.getByPlaceholderText('Enter job address'), { 
      target: { value: '123 Tech Street' } 
    });
    fireEvent.change(screen.getByPlaceholderText('Enter home address'), { 
      target: { value: '456 Home Avenue' } 
    });
    fireEvent.click(screen.getByText('2020 Honda Civic').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText(/Failed to calculate commute/)).toBeInTheDocument();
    });
  });

  it('shows loading state during calculations', async () => {
    // Mock slow API response
    (fetch as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ success: true, coordinates: { lat: 37.7749, lng: -122.4194 } })
      }), 100))
    );

    render(
      <CommuteCostCalculator
        vehicles={mockVehicles}
        onSaveScenario={jest.fn()}
        onLoadScenario={jest.fn()}
      />
    );

    // Fill in locations
    fireEvent.change(screen.getByPlaceholderText('Enter job address'), { 
      target: { value: '123 Tech Street' } 
    });
    fireEvent.change(screen.getByPlaceholderText('Enter home address'), { 
      target: { value: '456 Home Avenue' } 
    });
    fireEvent.click(screen.getByText('2020 Honda Civic').closest('button')!);

    // Should show loading state
    expect(screen.getByText('Calculating commute costs...')).toBeInTheDocument();
  });
});
