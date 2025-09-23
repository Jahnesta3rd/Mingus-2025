/**
 * Mingus Application - Optimized Daily Outlook Component
 * High-performance Daily Outlook component with comprehensive optimization
 */

import React, { useState, useEffect, useCallback, useMemo, Suspense, lazy } from 'react';
import { performanceOptimizer, ServiceWorkerManager, ProgressiveLoadingManager, ImageOptimizationManager, LazyLoadingManager } from '../services/performanceOptimizer';

// Lazy load heavy components
const BalanceScoreChart = lazy(() => import('./BalanceScoreChart'));
const QuickActionsPanel = lazy(() => import('./QuickActionsPanel'));
const PeerComparisonWidget = lazy(() => import('./PeerComparisonWidget'));
const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));

interface DailyOutlookData {
  id: number;
  user_id: number;
  date: string;
  balance_score: number;
  financial_weight: number;
  wellness_weight: number;
  relationship_weight: number;
  career_weight: number;
  primary_insight: string;
  quick_actions: Array<{
    id: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    estimated_time: string;
  }>;
  encouragement_message: string;
  surprise_element: string;
  streak_count: number;
  viewed_at?: string;
  actions_completed?: string[];
  user_rating?: number;
  created_at: string;
}

interface OptimizedDailyOutlookProps {
  userId: number;
  date?: string;
  enableOfflineMode?: boolean;
  enableProgressiveLoading?: boolean;
  enableImageOptimization?: boolean;
  enableLazyLoading?: boolean;
  onLoadComplete?: (loadTime: number) => void;
  onError?: (error: Error) => void;
}

const OptimizedDailyOutlook: React.FC<OptimizedDailyOutlookProps> = ({
  userId,
  date = new Date().toISOString().split('T')[0],
  enableOfflineMode = true,
  enableProgressiveLoading = true,
  enableImageOptimization = true,
  enableLazyLoading = true,
  onLoadComplete,
  onError
}) => {
  // State management
  const [dailyOutlook, setDailyOutlook] = useState<DailyOutlookData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadTime, setLoadTime] = useState<number>(0);
  const [progressiveLoading, setProgressiveLoading] = useState({
    balanceScore: false,
    quickActions: false,
    peerComparison: false,
    analytics: false
  });

  // Performance monitoring
  const [performanceMetrics, setPerformanceMetrics] = useState({
    cacheHit: false,
    loadTime: 0,
    componentRenderTime: 0,
    imageLoadTime: 0
  });

  // Initialize performance optimization
  useEffect(() => {
    const initializeOptimization = async () => {
      try {
        // Initialize service worker for offline support
        if (enableOfflineMode) {
          const swManager = ServiceWorkerManager.getInstance();
          await swManager.register();
        }

        // Initialize progressive loading
        if (enableProgressiveLoading) {
          const progressiveManager = ProgressiveLoadingManager.getInstance();
          // Progressive loading will be handled in loadDailyOutlook
        }

        // Initialize image optimization
        if (enableImageOptimization) {
          const imageManager = ImageOptimizationManager.getInstance();
          imageManager.setupLazyLoading();
        }

        // Initialize performance monitoring
        const startTime = performance.now();
        setPerformanceMetrics(prev => ({
          ...prev,
          componentRenderTime: startTime
        }));

      } catch (err) {
        console.error('Error initializing performance optimization:', err);
        onError?.(err as Error);
      }
    };

    initializeOptimization();
  }, [enableOfflineMode, enableProgressiveLoading, enableImageOptimization, onError]);

  // Load daily outlook data with optimization
  const loadDailyOutlook = useCallback(async () => {
    const startTime = performance.now();
    setLoading(true);
    setError(null);

    try {
      // Check cache first
      const cacheKey = `daily_outlook_${userId}_${date}`;
      const cachedData = localStorage.getItem(cacheKey);
      
      if (cachedData) {
        const parsedData = JSON.parse(cachedData);
        const cacheTime = new Date(parsedData.cached_at).getTime();
        const now = Date.now();
        const cacheAge = now - cacheTime;
        
        // Use cache if less than 1 hour old
        if (cacheAge < 3600000) {
          setDailyOutlook(parsedData);
          setPerformanceMetrics(prev => ({
            ...prev,
            cacheHit: true,
            loadTime: performance.now() - startTime
          }));
          setLoadTime(performance.now() - startTime);
          setLoading(false);
          onLoadComplete?.(performance.now() - startTime);
          return;
        }
      }

      // Progressive loading strategy
      if (enableProgressiveLoading) {
        const progressiveManager = ProgressiveLoadingManager.getInstance();
        
        // Load balance score first (most important)
        progressiveManager.addToQueue(async () => {
          try {
            const balanceScoreResponse = await fetch(`/api/v2/daily-outlook/${userId}/balance-score?date=${date}`);
            const balanceScoreData = await balanceScoreResponse.json();
            
            if (balanceScoreData.success) {
              setProgressiveLoading(prev => ({ ...prev, balanceScore: true }));
            }
          } catch (err) {
            console.error('Error loading balance score:', err);
          }
        });

        // Load quick actions second
        progressiveManager.addToQueue(async () => {
          try {
            const quickActionsResponse = await fetch(`/api/v2/daily-outlook/${userId}/quick-actions?date=${date}`);
            const quickActionsData = await quickActionsResponse.json();
            
            if (quickActionsData.success) {
              setProgressiveLoading(prev => ({ ...prev, quickActions: true }));
            }
          } catch (err) {
            console.error('Error loading quick actions:', err);
          }
        });

        // Load peer comparison data last
        progressiveManager.addToQueue(async () => {
          try {
            const peerComparisonResponse = await fetch(`/api/v2/daily-outlook/${userId}/peer-comparison?date=${date}`);
            const peerComparisonData = await peerComparisonResponse.json();
            
            if (peerComparisonData.success) {
              setProgressiveLoading(prev => ({ ...prev, peerComparison: true }));
            }
          } catch (err) {
            console.error('Error loading peer comparison:', err);
          }
        });
      }

      // Load main daily outlook data
      const response = await fetch(`/api/v2/daily-outlook/${userId}?date=${date}`, {
        headers: {
          'Accept': 'application/json',
          'Accept-Encoding': 'gzip, deflate, br'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setDailyOutlook(data.data);
        
        // Cache the response
        const cacheData = {
          ...data.data,
          cached_at: new Date().toISOString()
        };
        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
        
        setPerformanceMetrics(prev => ({
          ...prev,
          cacheHit: false,
          loadTime: performance.now() - startTime
        }));
      } else {
        throw new Error(data.error || 'Failed to load daily outlook');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      onError?.(err as Error);
    } finally {
      const totalLoadTime = performance.now() - startTime;
      setLoadTime(totalLoadTime);
      setLoading(false);
      onLoadComplete?.(totalLoadTime);
    }
  }, [userId, date, enableProgressiveLoading, onLoadComplete, onError]);

  // Load data on mount and when dependencies change
  useEffect(() => {
    loadDailyOutlook();
  }, [loadDailyOutlook]);

  // Optimized image URLs
  const optimizedImages = useMemo(() => {
    if (!enableImageOptimization) return {};
    
    const imageManager = ImageOptimizationManager.getInstance();
    
    return {
      backgroundImage: imageManager.optimizeImage('/static/images/daily-outlook-bg.webp', {
        width: 800,
        height: 600,
        quality: 85,
        format: 'webp'
      }),
      balanceChart: imageManager.optimizeImage('/static/images/balance-score-chart.webp', {
        width: 400,
        height: 300,
        quality: 90,
        format: 'webp'
      }),
      actionIcons: imageManager.optimizeImage('/static/images/quick-actions-icons.webp', {
        width: 200,
        height: 200,
        quality: 80,
        format: 'webp'
      })
    };
  }, [enableImageOptimization]);

  // Memoized components for performance
  const BalanceScoreSection = useMemo(() => {
    if (!dailyOutlook || !progressiveLoading.balanceScore) return null;
    
    return (
      <Suspense fallback={<div className="animate-pulse bg-gray-200 h-32 rounded"></div>}>
        <BalanceScoreChart
          score={dailyOutlook.balance_score}
          weights={{
            financial: dailyOutlook.financial_weight,
            wellness: dailyOutlook.wellness_weight,
            relationship: dailyOutlook.relationship_weight,
            career: dailyOutlook.career_weight
          }}
          optimizedImage={optimizedImages.balanceChart}
        />
      </Suspense>
    );
  }, [dailyOutlook, progressiveLoading.balanceScore, optimizedImages.balanceChart]);

  const QuickActionsSection = useMemo(() => {
    if (!dailyOutlook || !progressiveLoading.quickActions) return null;
    
    return (
      <Suspense fallback={<div className="animate-pulse bg-gray-200 h-24 rounded"></div>}>
        <QuickActionsPanel
          actions={dailyOutlook.quick_actions}
          onActionComplete={(actionId) => {
            // Handle action completion
            console.log('Action completed:', actionId);
          }}
          optimizedImages={optimizedImages.actionIcons}
        />
      </Suspense>
    );
  }, [dailyOutlook, progressiveLoading.quickActions, optimizedImages.actionIcons]);

  const PeerComparisonSection = useMemo(() => {
    if (!dailyOutlook || !progressiveLoading.peerComparison) return null;
    
    return (
      <Suspense fallback={<div className="animate-pulse bg-gray-200 h-20 rounded"></div>}>
        <PeerComparisonWidget
          userScore={dailyOutlook.balance_score}
          date={date}
        />
      </Suspense>
    );
  }, [dailyOutlook, progressiveLoading.peerComparison, date]);

  // Loading skeleton
  const LoadingSkeleton = () => (
    <div className="space-y-4">
      <div className="animate-pulse bg-gray-200 h-8 rounded"></div>
      <div className="animate-pulse bg-gray-200 h-32 rounded"></div>
      <div className="animate-pulse bg-gray-200 h-24 rounded"></div>
      <div className="animate-pulse bg-gray-200 h-20 rounded"></div>
    </div>
  );

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error loading daily outlook
            </h3>
            <div className="mt-2 text-sm text-red-700">
              {error}
            </div>
            <div className="mt-4">
              <button
                onClick={loadDailyOutlook}
                className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-2 rounded-md text-sm font-medium"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main component render
  return (
    <div className="optimized-daily-outlook">
      {/* Performance metrics (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mb-4 p-2 bg-gray-100 rounded text-xs">
          <div>Load Time: {loadTime.toFixed(2)}ms</div>
          <div>Cache Hit: {performanceMetrics.cacheHit ? 'Yes' : 'No'}</div>
          <div>Progressive Loading: {Object.values(progressiveLoading).filter(Boolean).length}/4</div>
        </div>
      )}

      {/* Background image with optimization */}
      {enableImageOptimization && (
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-10"
          style={{
            backgroundImage: `url(${optimizedImages.backgroundImage})`
          }}
        />
      )}

      {/* Main content */}
      <div className="relative z-10">
        {loading ? (
          <LoadingSkeleton />
        ) : dailyOutlook ? (
          <div className="space-y-6">
            {/* Header */}
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900">
                Daily Outlook
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                {new Date(dailyOutlook.date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>

            {/* Primary insight */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                Today's Insight
              </h2>
              <p className="text-gray-700 leading-relaxed">
                {dailyOutlook.primary_insight}
              </p>
            </div>

            {/* Balance score section */}
            {BalanceScoreSection}

            {/* Quick actions section */}
            {QuickActionsSection}

            {/* Encouragement message */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Keep Going! 💪
              </h3>
              <p className="text-gray-700">
                {dailyOutlook.encouragement_message}
              </p>
            </div>

            {/* Surprise element */}
            {dailyOutlook.surprise_element && (
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Today's Surprise 🎉
                </h3>
                <p className="text-gray-700">
                  {dailyOutlook.surprise_element}
                </p>
              </div>
            )}

            {/* Peer comparison section */}
            {PeerComparisonSection}

            {/* Streak counter */}
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center justify-center">
                <span className="text-2xl mr-2">🔥</span>
                <span className="text-lg font-semibold text-gray-900">
                  {dailyOutlook.streak_count} day streak!
                </span>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default OptimizedDailyOutlook;
