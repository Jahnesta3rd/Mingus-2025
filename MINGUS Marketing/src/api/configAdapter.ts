/**
 * Config Adapter for Marketing Funnel
 * 
 * This adapter allows the marketing funnel to work with different config file structures
 * instead of environment variables.
 */

// Default config structure - modify this to match your existing config
interface MarketingFunnelConfig {
  supabase: {
    url: string
    anonKey: string
    serviceRoleKey?: string
  }
  email: {
    provider: 'mock' | 'sendgrid' | 'mailchimp' | 'convertkit'
    appUrl: string
  }
  analytics?: {
    googleAnalyticsId?: string
  }
}

// Fallback configuration - replace with your actual values
const fallbackConfig: MarketingFunnelConfig = {
  supabase: {
    url: 'https://your-project.supabase.co',
    anonKey: 'your-anon-key',
    serviceRoleKey: 'your-service-role-key'
  },
  email: {
    provider: 'mock',
    appUrl: 'http://localhost:3000'
  },
  analytics: {
    googleAnalyticsId: 'your-ga-id'
  }
}

// Try to import your existing config - modify the import path as needed
let config: MarketingFunnelConfig | null = null

// Function to load config dynamically
const loadConfig = async (): Promise<MarketingFunnelConfig> => {
  if (config) return config

  try {
    // Try different common config import patterns
    const configModule = await import('../config')
    
    if (configModule.config?.marketingFunnel) {
      // Option A: config.js/ts with marketingFunnel section
      config = configModule.config.marketingFunnel
    } else if (configModule.default?.marketingFunnel) {
      // Option B: default export with marketingFunnel section
      config = configModule.default.marketingFunnel
    } else if (configModule.appConfig?.marketingFunnel) {
      // Option C: appConfig with marketingFunnel section
      config = configModule.appConfig.marketingFunnel
    } else if (configModule.developmentConfig?.marketingFunnel) {
      // Option D: environment-specific config
      const env = process.env.NODE_ENV || 'development'
      const envConfig = env === 'production' 
        ? configModule.productionConfig 
        : configModule.developmentConfig
      config = envConfig.marketingFunnel
    }
  } catch (error) {
    console.warn('Could not import config file, using fallback configuration')
  }

  return config || fallbackConfig
}

// Initialize config synchronously for immediate use
const initializeConfig = (): MarketingFunnelConfig => {
  // For immediate use, return fallback config
  // The actual config will be loaded when needed
  return fallbackConfig
}

// Export the resolved config
export const marketingFunnelConfig: MarketingFunnelConfig = initializeConfig()

// Helper functions to access config values
export const getSupabaseUrl = (): string => {
  return config?.supabase.url || fallbackConfig.supabase.url
}

export const getSupabaseAnonKey = (): string => {
  return config?.supabase.anonKey || fallbackConfig.supabase.anonKey
}

export const getSupabaseServiceRoleKey = (): string | undefined => {
  return config?.supabase.serviceRoleKey || fallbackConfig.supabase.serviceRoleKey
}

export const getEmailProvider = (): 'mock' | 'sendgrid' | 'mailchimp' | 'convertkit' => {
  return config?.email.provider || fallbackConfig.email.provider
}

export const getAppUrl = (): string => {
  return config?.email.appUrl || fallbackConfig.email.appUrl
}

export const getGoogleAnalyticsId = (): string | undefined => {
  return config?.analytics?.googleAnalyticsId || fallbackConfig.analytics?.googleAnalyticsId
}

// Configuration validation
export const validateConfig = (): boolean => {
  const required = [
    getSupabaseUrl(),
    getSupabaseAnonKey(),
    getEmailProvider(),
    getAppUrl()
  ]
  
  const missing = required.filter(value => !value)
  
  if (missing.length > 0) {
    console.error('Missing required marketing funnel configuration:', missing)
    return false
  }
  
  return true
}

// Load config asynchronously
export const loadConfigAsync = async (): Promise<void> => {
  config = await loadConfig()
  
  // Log configuration status (development only)
  if (process.env.NODE_ENV === 'development') {
    console.log('Marketing Funnel Config:', {
      supabaseUrl: getSupabaseUrl(),
      emailProvider: getEmailProvider(),
      appUrl: getAppUrl(),
      configSource: config ? 'imported' : 'fallback'
    })
  }
}

// Initialize config loading
if (typeof window !== 'undefined') {
  // In browser environment, load config after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      loadConfigAsync()
    })
  } else {
    loadConfigAsync()
  }
} 