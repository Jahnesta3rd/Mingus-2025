import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { useAnalytics } from './useAnalytics';

// ========================================
// TYPESCRIPT INTERFACES
// ========================================

interface DailyOutlookData {
  user_name: string;
  current_time: string;
  balance_score: {
    value: number;
    trend: 'up' | 'down' | 'stable';
    change_percentage: number;
    previous_value: number;
  };
  primary_insight: {
    title: string;
    message: string;
    type: 'positive' | 'neutral' | 'warning' | 'celebration';
    icon: string;
  };
  quick_actions: Array<{
    id: string;
    title: string;
    description: string;
    completed: boolean;
    priority: 'high' | 'medium' | 'low';
    estimated_time: string;
  }>;
  encouragement_message: {
    text: string;
    type: 'motivational' | 'achievement' | 'reminder' | 'celebration';
    emoji: string;
  };
  streak_data: {
    current_streak: number;
    longest_streak: number;
    milestone_reached: boolean;
    next_milestone: number;
    progress_percentage: number;
  };
  tomorrow_teaser: {
    title: string;
    description: string;
    excitement_level: number;
  };
  user_tier: 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';
}

interface CacheEntry {
  data: DailyOutlookData;
  timestamp: number;
  expiresAt: number;
}

interface UseDailyOutlookCacheReturn {
  data: DailyOutlookData | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  isStale: boolean;
  lastUpdated: Date | null;
}

// ========================================
// CACHE CONFIGURATION
// ========================================

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const STALE_THRESHOLD = 2 * 60 * 1000; // 2 minutes
const PRELOAD_THRESHOLD = 4 * 60 * 1000; // 4 minutes

// ========================================
// CACHE STORAGE
// ========================================

class DailyOutlookCache {
  private cache = new Map<string, CacheEntry>();
  private preloadPromises = new Map<string, Promise<DailyOutlookData>>();

  set(key: string, data: DailyOutlookData, duration: number = CACHE_DURATION): void {
    const now = Date.now();
    this.cache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + duration
    });
  }

  get(key: string): DailyOutlookData | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  isStale(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return true;

    const now = Date.now();
    return (now - entry.timestamp) > STALE_THRESHOLD;
  }

  shouldPreload(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return true;

    const now = Date.now();
    return (now - entry.timestamp) > PRELOAD_THRESHOLD;
  }

  clear(): void {
    this.cache.clear();
    this.preloadPromises.clear();
  }

  setPreloadPromise(key: string, promise: Promise<DailyOutlookData>): void {
    this.preloadPromises.set(key, promise);
  }

  getPreloadPromise(key: string): Promise<DailyOutlookData> | null {
    return this.preloadPromises.get(key) || null;
  }

  clearPreloadPromise(key: string): void {
    this.preloadPromises.delete(key);
  }
}

// Global cache instance
const cache = new DailyOutlookCache();

// ========================================
// HOOK IMPLEMENTATION
// ========================================

export const useDailyOutlookCache = (): UseDailyOutlookCacheReturn => {
  const { user } = useAuth();
  const { trackInteraction, trackError } = useAnalytics();
  
  const [data, setData] = useState<DailyOutlookData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  const cacheKey = `daily-outlook-${user?.id || 'anonymous'}`;
  const abortControllerRef = useRef<AbortController | null>(null);

  // ========================================
  // FETCH FUNCTION
  // ========================================

  const fetchDailyOutlook = useCallback(async (forceRefresh: boolean = false): Promise<DailyOutlookData> => {
    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/daily-outlook', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch daily outlook: ${response.status}`);
      }

      const data = await response.json();
      
      // Update cache
      cache.set(cacheKey, data);
      
      await trackInteraction('daily_outlook_fetched', {
        user_tier: data.user_tier,
        balance_score: data.balance_score.value,
        cached: !forceRefresh
      });

      return data;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        throw err; // Re-throw abort errors
      }
      
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch daily outlook';
      await trackError('daily_outlook_fetch_error', errorMessage);
      throw new Error(errorMessage);
    }
  }, [cacheKey, trackInteraction, trackError]);

  // ========================================
  // REFETCH FUNCTION
  // ========================================

  const refetch = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchDailyOutlook(true);
      setData(data);
      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refetch data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchDailyOutlook]);

  // ========================================
  // INITIAL LOAD
  // ========================================

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Check cache first
        const cachedData = cache.get(cacheKey);
        if (cachedData && !cache.isStale(cacheKey)) {
          setData(cachedData);
          setLastUpdated(new Date(cache.cache.get(cacheKey)?.timestamp || Date.now()));
          setLoading(false);
          
          // Preload if needed
          if (cache.shouldPreload(cacheKey)) {
            const preloadPromise = fetchDailyOutlook(true);
            cache.setPreloadPromise(cacheKey, preloadPromise);
            
            preloadPromise
              .then((newData) => {
                setData(newData);
                setLastUpdated(new Date());
                cache.clearPreloadPromise(cacheKey);
              })
              .catch(() => {
                // Ignore preload errors
                cache.clearPreloadPromise(cacheKey);
              });
          }
          return;
        }

        // Check if there's already a preload in progress
        const existingPreload = cache.getPreloadPromise(cacheKey);
        if (existingPreload) {
          try {
            const preloadedData = await existingPreload;
            setData(preloadedData);
            setLastUpdated(new Date());
            cache.clearPreloadPromise(cacheKey);
            return;
          } catch {
            // If preload failed, continue with fresh fetch
            cache.clearPreloadPromise(cacheKey);
          }
        }

        // Fetch fresh data
        const freshData = await fetchDailyOutlook(true);
        setData(freshData);
        setLastUpdated(new Date());
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load daily outlook';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    if (user?.id) {
      loadData();
    }

    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [user?.id, fetchDailyOutlook]);

  // ========================================
  // PERIODIC REFRESH
  // ========================================

  useEffect(() => {
    if (!data) return;

    const interval = setInterval(() => {
      if (cache.isStale(cacheKey)) {
        // Silently refresh in background
        fetchDailyOutlook(true)
          .then((newData) => {
            setData(newData);
            setLastUpdated(new Date());
          })
          .catch(() => {
            // Ignore background refresh errors
          });
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [data, cacheKey, fetchDailyOutlook]);

  // ========================================
  // CLEANUP ON USER CHANGE
  // ========================================

  useEffect(() => {
    return () => {
      // Clear cache when user changes
      cache.clear();
    };
  }, [user?.id]);

  return {
    data,
    loading,
    error,
    refetch,
    isStale: data ? cache.isStale(cacheKey) : false,
    lastUpdated
  };
};

// ========================================
// EXPORT CACHE UTILITIES
// ========================================

export const clearDailyOutlookCache = (): void => {
  cache.clear();
};

export const preloadTomorrowsOutlook = async (userId: string): Promise<void> => {
  try {
    const token = localStorage.getItem('mingus_token');
    const response = await fetch('/api/daily-outlook/tomorrow', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      cache.set(`tomorrow-outlook-${userId}`, data, 24 * 60 * 60 * 1000); // 24 hours
    }
  } catch (err) {
    // Silently fail preloading
    console.warn('Failed to preload tomorrow\'s outlook:', err);
  }
};
