/**
 * Optimized Daily Outlook Component Tests
 * 
 * Tests for the performance-optimized DailyOutlook component including:
 * - Performance optimizations
 * - Progressive loading
 * - Image optimization
 * - Lazy loading
 * - Offline mode
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import OptimizedDailyOutlook from '../OptimizedDailyOutlook';

// Mock fetch globally
global.fetch = jest.fn();

// Mock performance API
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  mark: jest.fn(),
  measure: jest.fn(),
  getEntriesByName: jest.fn(() => []),
  getEntriesByType: jest.fn(() => [])
};
Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true
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
const mockOptimizedData = {
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
  user_tier: 'professional' as const,
  cached: true,
  load_time: 45,
  performance_metrics: {
    cache_hit: true,
    load_time: 45,
    component_render_time: 12,
    image_load_time: 8
  }
};

describe('OptimizedDailyOutlook Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPerformance.now.mockReturnValue(Date.now());
  });

  describe('Performance Optimizations', () => {
    it('renders with performance monitoring', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      expect(mockPerformance.mark).toHaveBeenCalledWith('optimized-daily-outlook-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('optimized-daily-outlook-end');
      expect(mockPerformance.measure).toHaveBeenCalledWith(
        'optimized-daily-outlook-render',
        'optimized-daily-outlook-start',
        'optimized-daily-outlook-end'
      );
    });

    it('tracks performance metrics', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Check that performance metrics are displayed
      expect(screen.getByText(/load time: 45ms/i)).toBeInTheDocument();
      expect(screen.getByText(/cache hit/i)).toBeInTheDocument();
    });

    it('handles performance budget violations', async () => {
      const slowData = {
        ...mockOptimizedData,
        load_time: 5000, // 5 seconds - exceeds budget
        performance_metrics: {
          ...mockOptimizedData.performance_metrics,
          load_time: 5000
        }
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => slowData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/performance warning/i)).toBeInTheDocument();
      });
    });
  });

  describe('Progressive Loading', () => {
    it('loads components progressively', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableProgressiveLoading={true}
          />
        </BrowserRouter>
      );

      // Balance score should load first
      await waitFor(() => {
        expect(screen.getByText('85')).toBeInTheDocument();
      });

      // Quick actions should load after
      await waitFor(() => {
        expect(screen.getByText('Review Budget')).toBeInTheDocument();
      });
    });

    it('shows loading states for progressive components', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableProgressiveLoading={true}
          />
        </BrowserRouter>
      );

      // Should show loading for quick actions initially
      expect(screen.getByText(/loading quick actions/i)).toBeInTheDocument();
    });

    it('handles progressive loading errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableProgressiveLoading={true}
          />
        </BrowserRouter>
      );

      // Simulate error in progressive loading
      act(() => {
        // Trigger error in progressive loading
        const errorEvent = new ErrorEvent('error', {
          message: 'Progressive loading failed'
        });
        window.dispatchEvent(errorEvent);
      });

      await waitFor(() => {
        expect(screen.getByText(/progressive loading failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Image Optimization', () => {
    it('optimizes images when enabled', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableImageOptimization={true}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Check that images have optimization attributes
      const images = screen.getAllByRole('img');
      images.forEach(img => {
        expect(img).toHaveAttribute('loading', 'lazy');
        expect(img).toHaveAttribute('decoding', 'async');
      });
    });

    it('handles image loading errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableImageOptimization={true}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Simulate image loading error
      const images = screen.getAllByRole('img');
      if (images.length > 0) {
        act(() => {
          fireEvent.error(images[0]);
        });

        expect(screen.getByText(/image failed to load/i)).toBeInTheDocument();
      }
    });

    it('tracks image load performance', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableImageOptimization={true}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Check that image load time is tracked
      expect(screen.getByText(/image load time: 8ms/i)).toBeInTheDocument();
    });
  });

  describe('Lazy Loading', () => {
    it('implements lazy loading when enabled', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableLazyLoading={true}
          />
        </BrowserRouter>
      );

      // Check that IntersectionObserver is used
      expect(global.IntersectionObserver).toHaveBeenCalled();
    });

    it('loads content when it comes into view', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableLazyLoading={true}
          />
        </BrowserRouter>
      );

      // Simulate intersection observer callback
      const observerCallback = (global.IntersectionObserver as jest.Mock).mock.calls[0][0];
      observerCallback([{ isIntersecting: true, target: document.createElement('div') }]);

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });
    });

    it('handles lazy loading errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableLazyLoading={true}
          />
        </BrowserRouter>
      );

      // Simulate intersection observer error
      const observerCallback = (global.IntersectionObserver as jest.Mock).mock.calls[0][0];
      observerCallback([{ isIntersecting: true, target: null }]);

      await waitFor(() => {
        expect(screen.getByText(/lazy loading failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Offline Mode', () => {
    it('handles offline mode when enabled', async () => {
      // Mock offline state
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableOfflineMode={true}
          />
        </BrowserRouter>
      );

      expect(screen.getByText(/offline mode/i)).toBeInTheDocument();
      expect(screen.getByText(/cached data/i)).toBeInTheDocument();
    });

    it('switches to online mode when connection is restored', async () => {
      // Start offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableOfflineMode={true}
          />
        </BrowserRouter>
      );

      expect(screen.getByText(/offline mode/i)).toBeInTheDocument();

      // Simulate connection restoration
      act(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: true
        });
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(screen.getByText(/online mode/i)).toBeInTheDocument();
      });
    });

    it('caches data for offline use', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableOfflineMode={true}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Check that data is cached
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'daily_outlook_cache_1',
        expect.any(String)
      );
    });
  });

  describe('Performance Benchmarking', () => {
    it('benchmarks component render time', async () => {
      const startTime = performance.now();
      mockPerformance.now.mockReturnValueOnce(startTime);

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      const endTime = startTime + 25; // 25ms render time
      mockPerformance.now.mockReturnValueOnce(endTime);

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      expect(mockPerformance.measure).toHaveBeenCalledWith(
        'optimized-daily-outlook-render',
        'optimized-daily-outlook-start',
        'optimized-daily-outlook-end'
      );
    });

    it('tracks memory usage', async () => {
      const mockMemory = {
        usedJSHeapSize: 1000000,
        totalJSHeapSize: 2000000,
        jsHeapSizeLimit: 4000000
      };

      Object.defineProperty(performance, 'memory', {
        value: mockMemory,
        writable: true
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Check that memory usage is tracked
      expect(screen.getByText(/memory usage/i)).toBeInTheDocument();
    });

    it('handles performance budget violations', async () => {
      const slowData = {
        ...mockOptimizedData,
        load_time: 5000,
        performance_metrics: {
          ...mockOptimizedData.performance_metrics,
          load_time: 5000,
          component_render_time: 2000
        }
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => slowData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/performance budget exceeded/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });

    it('handles performance monitoring errors', async () => {
      mockPerformance.measure.mockImplementation(() => {
        throw new Error('Performance monitoring error');
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook userId={1} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      // Should still render despite performance monitoring error
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    it('handles offline mode errors', async () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      // Mock localStorage error
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            enableOfflineMode={true}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/offline mode error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Callback Handling', () => {
    it('calls onLoadComplete when data is loaded', async () => {
      const mockOnLoadComplete = jest.fn();

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptimizedData
      });

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            onLoadComplete={mockOnLoadComplete}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument();
      });

      expect(mockOnLoadComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          loadTime: 45,
          cached: true
        })
      );
    });

    it('calls onError when error occurs', async () => {
      const mockOnError = jest.fn();

      (fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

      render(
        <BrowserRouter>
          <OptimizedDailyOutlook 
            userId={1} 
            onError={mockOnError}
          />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });

      expect(mockOnError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'API Error'
        })
      );
    });
  });
});
