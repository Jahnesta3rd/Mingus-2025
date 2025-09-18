import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RecommendationTiers from '../components/RecommendationTiers';

// Mock the useAnalytics hook
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackInteraction: jest.fn(),
    trackError: jest.fn(),
    getSessionId: jest.fn(() => 'test-session'),
    getUserId: jest.fn(() => 'test-user')
  })
}));

// Mock fetch
global.fetch = jest.fn();

describe('RecommendationTiers Component', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('renders loading state initially', () => {
    render(<RecommendationTiers />);
    expect(screen.getByText('Career Recommendations')).toBeInTheDocument();
  });

  it('renders error state when API fails', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));
    
    render(<RecommendationTiers />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load recommendations')).toBeInTheDocument();
    });
  });

  it('renders tier cards when data is loaded', async () => {
    const mockData = {
      success: true,
      recommendations: {
        conservative: [],
        optimal: [],
        stretch: [],
        total_count: 0
      }
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    render(<RecommendationTiers />);
    
    await waitFor(() => {
      expect(screen.getByText('Safe Growth')).toBeInTheDocument();
      expect(screen.getByText('Strategic Advance')).toBeInTheDocument();
      expect(screen.getByText('Ambitious Leap')).toBeInTheDocument();
    });
  });

  it('handles tier expansion correctly', async () => {
    const mockData = {
      success: true,
      recommendations: {
        conservative: [],
        optimal: [],
        stretch: [],
        total_count: 0
      }
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    render(<RecommendationTiers />);
    
    await waitFor(() => {
      const expandButton = screen.getByText('View All 0 Opportunities');
      fireEvent.click(expandButton);
    });
  });

  it('handles radius change correctly', async () => {
    const mockData = {
      success: true,
      recommendations: {
        conservative: [],
        optimal: [],
        stretch: [],
        total_count: 0
      }
    };

    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockData
    });

    render(<RecommendationTiers />);
    
    await waitFor(() => {
      const radiusSelect = screen.getByLabelText('Select search radius');
      fireEvent.change(radiusSelect, { target: { value: '30' } });
    });
  });

  it('handles comparison mode toggle correctly', async () => {
    const mockData = {
      success: true,
      recommendations: {
        conservative: [],
        optimal: [],
        stretch: [],
        total_count: 0
      }
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    render(<RecommendationTiers />);
    
    await waitFor(() => {
      const compareButton = screen.getByText('Compare Tiers');
      fireEvent.click(compareButton);
      expect(screen.getByText('Exit Compare')).toBeInTheDocument();
    });
  });
});
