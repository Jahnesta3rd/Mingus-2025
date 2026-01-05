/**
 * Logger utility for development and production logging
 * 
 * Provides controlled logging that:
 * - Only logs in development mode
 * - Always logs errors (for debugging)
 * - Can be extended to send errors to error tracking services in production
 */

export const logger = {
  /**
   * Log informational messages (only in development)
   */
  log: (...args: any[]): void => {
    if (import.meta.env.DEV) {
      console.log(...args);
    }
  },

  /**
   * Log error messages (always logged, can be sent to error tracking in production)
   */
  error: (...args: any[]): void => {
    // Always log errors for debugging
    console.error(...args);
    
    // In production, send to error tracking service
    if (import.meta.env.PROD) {
      // TODO: Integrate with error tracking service (e.g., Sentry, LogRocket)
      // Example:
      // if (window.Sentry) {
      //   window.Sentry.captureException(args[0]);
      // }
    }
  },

  /**
   * Log warning messages (only in development)
   */
  warn: (...args: any[]): void => {
    if (import.meta.env.DEV) {
      console.warn(...args);
    }
  },

  /**
   * Log debug messages (only in development)
   */
  debug: (...args: any[]): void => {
    if (import.meta.env.DEV) {
      console.debug(...args);
    }
  },

  /**
   * Log info messages (only in development)
   */
  info: (...args: any[]): void => {
    if (import.meta.env.DEV) {
      console.info(...args);
    }
  }
};

