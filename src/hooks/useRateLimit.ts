import { useState, useEffect, useCallback } from 'react';

interface RateLimitConfig {
  maxAttempts: number;
  windowMs: number;
  key: string;
}

interface RateLimitState {
  attempts: number;
  remainingAttempts: number;
  resetTime: number;
  isBlocked: boolean;
  timeUntilReset: number;
}

export function useRateLimit(config: RateLimitConfig) {
  const [state, setState] = useState<RateLimitState>(() => {
    const stored = localStorage.getItem(`rate_limit_${config.key}`);
    if (stored) {
      const data = JSON.parse(stored);
      const now = Date.now();
      
      // Check if window has expired
      if (now > data.resetTime) {
        localStorage.removeItem(`rate_limit_${config.key}`);
        return {
          attempts: 0,
          remainingAttempts: config.maxAttempts,
          resetTime: now + config.windowMs,
          isBlocked: false,
          timeUntilReset: 0
        };
      }
      
      return {
        attempts: data.attempts,
        remainingAttempts: Math.max(0, config.maxAttempts - data.attempts),
        resetTime: data.resetTime,
        isBlocked: data.attempts >= config.maxAttempts,
        timeUntilReset: Math.max(0, data.resetTime - now)
      };
    }
    
    return {
      attempts: 0,
      remainingAttempts: config.maxAttempts,
      resetTime: Date.now() + config.windowMs,
      isBlocked: false,
      timeUntilReset: 0
    };
  });

  // Update time until reset
  useEffect(() => {
    if (state.isBlocked) {
      const interval = setInterval(() => {
        const now = Date.now();
        const timeUntilReset = Math.max(0, state.resetTime - now);
        
        if (timeUntilReset === 0) {
          // Reset rate limit
          localStorage.removeItem(`rate_limit_${config.key}`);
          setState({
            attempts: 0,
            remainingAttempts: config.maxAttempts,
            resetTime: now + config.windowMs,
            isBlocked: false,
            timeUntilReset: 0
          });
        } else {
          setState(prev => ({
            ...prev,
            timeUntilReset
          }));
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [state.isBlocked, state.resetTime, config.key, config.maxAttempts, config.windowMs]);

  const attempt = useCallback(() => {
    const now = Date.now();
    
    // Check if window has expired
    if (now > state.resetTime) {
      // Reset rate limit
      const newState = {
        attempts: 1,
        remainingAttempts: config.maxAttempts - 1,
        resetTime: now + config.windowMs,
        isBlocked: false,
        timeUntilReset: 0
      };
      
      setState(newState);
      localStorage.setItem(`rate_limit_${config.key}`, JSON.stringify({
        attempts: newState.attempts,
        resetTime: newState.resetTime
      }));
      
      return true;
    }
    
    // Check if already blocked
    if (state.isBlocked) {
      return false;
    }
    
    // Increment attempts
    const newAttempts = state.attempts + 1;
    const newState = {
      attempts: newAttempts,
      remainingAttempts: Math.max(0, config.maxAttempts - newAttempts),
      resetTime: state.resetTime,
      isBlocked: newAttempts >= config.maxAttempts,
      timeUntilReset: state.timeUntilReset
    };
    
    setState(newState);
    localStorage.setItem(`rate_limit_${config.key}`, JSON.stringify({
      attempts: newState.attempts,
      resetTime: newState.resetTime
    }));
    
    return true;
  }, [state, config]);

  const reset = useCallback(() => {
    localStorage.removeItem(`rate_limit_${config.key}`);
    setState({
      attempts: 0,
      remainingAttempts: config.maxAttempts,
      resetTime: Date.now() + config.windowMs,
      isBlocked: false,
      timeUntilReset: 0
    });
  }, [config]);

  const formatTimeUntilReset = useCallback(() => {
    if (state.timeUntilReset === 0) return '';
    
    const minutes = Math.floor(state.timeUntilReset / 60000);
    const seconds = Math.floor((state.timeUntilReset % 60000) / 1000);
    
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }, [state.timeUntilReset]);

  return {
    ...state,
    attempt,
    reset,
    formatTimeUntilReset
  };
} 