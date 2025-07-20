/**
 * Example Configuration Files for Marketing Funnel Integration
 * 
 * Choose the example that matches your existing config structure
 */

// ============================================================================
// EXAMPLE 1: Simple Config Object
// ============================================================================
export const simpleConfig = {
  // Your existing app config
  api: {
    baseUrl: 'https://your-api.com',
    timeout: 5000
  },
  
  // Add marketing funnel config
  marketingFunnel: {
    supabase: {
      url: 'https://your-existing-project.supabase.co',
      anonKey: 'your-existing-anon-key',
      serviceRoleKey: 'your-existing-service-role-key'
    },
    email: {
      provider: 'mock', // or 'sendgrid', 'mailchimp', 'convertkit'
      appUrl: 'http://localhost:3000'
    },
    analytics: {
      googleAnalyticsId: 'your-existing-ga-id' // optional
    }
  }
}

// ============================================================================
// EXAMPLE 2: Environment-Specific Config
// ============================================================================
export const developmentConfig = {
  // Your existing development config
  api: {
    baseUrl: 'http://localhost:3001',
    timeout: 10000
  },
  
  marketingFunnel: {
    supabase: {
      url: 'https://your-dev-project.supabase.co',
      anonKey: 'your-dev-anon-key',
      serviceRoleKey: 'your-dev-service-role-key'
    },
    email: {
      provider: 'mock',
      appUrl: 'http://localhost:3000'
    }
  }
}

export const productionConfig = {
  // Your existing production config
  api: {
    baseUrl: 'https://your-production-api.com',
    timeout: 5000
  },
  
  marketingFunnel: {
    supabase: {
      url: 'https://your-prod-project.supabase.co',
      anonKey: 'your-prod-anon-key',
      serviceRoleKey: 'your-prod-service-role-key'
    },
    email: {
      provider: 'sendgrid', // or your preferred email provider
      appUrl: 'https://yourdomain.com'
    },
    analytics: {
      googleAnalyticsId: 'GA_MEASUREMENT_ID'
    }
  }
}

// ============================================================================
// EXAMPLE 3: Nested Config Structure
// ============================================================================
export const nestedConfig = {
  app: {
    name: 'Your App',
    version: '1.0.0'
  },
  
  services: {
    api: {
      baseUrl: 'https://your-api.com'
    },
    
    database: {
      // Your existing database config
      type: 'postgres',
      host: 'localhost'
    },
    
    marketingFunnel: {
      supabase: {
        url: 'https://your-existing-project.supabase.co',
        anonKey: 'your-existing-anon-key',
        serviceRoleKey: 'your-existing-service-role-key'
      },
      email: {
        provider: 'mock',
        appUrl: 'http://localhost:3000'
      }
    }
  }
}

// ============================================================================
// EXAMPLE 4: Function-Based Config
// ============================================================================
export const createConfig = (environment = 'development') => {
  const baseConfig = {
    api: {
      baseUrl: environment === 'production' 
        ? 'https://your-production-api.com' 
        : 'http://localhost:3001'
    }
  }
  
  const marketingFunnelConfig = {
    supabase: {
      url: environment === 'production'
        ? 'https://your-prod-project.supabase.co'
        : 'https://your-dev-project.supabase.co',
      anonKey: environment === 'production'
        ? 'your-prod-anon-key'
        : 'your-dev-anon-key',
      serviceRoleKey: environment === 'production'
        ? 'your-prod-service-role-key'
        : 'your-dev-service-role-key'
    },
    email: {
      provider: environment === 'production' ? 'sendgrid' : 'mock',
      appUrl: environment === 'production'
        ? 'https://yourdomain.com'
        : 'http://localhost:3000'
    }
  }
  
  return {
    ...baseConfig,
    marketingFunnel: marketingFunnelConfig
  }
}

// ============================================================================
// EXAMPLE 5: Config with Validation
// ============================================================================
export const validatedConfig = {
  // Your existing config
  api: {
    baseUrl: 'https://your-api.com'
  },
  
  marketingFunnel: {
    supabase: {
      url: 'https://your-existing-project.supabase.co',
      anonKey: 'your-existing-anon-key',
      serviceRoleKey: 'your-existing-service-role-key'
    },
    email: {
      provider: 'mock',
      appUrl: 'http://localhost:3000'
    }
  }
}

// Validation function
export const validateMarketingFunnelConfig = (config) => {
  const required = [
    config.marketingFunnel?.supabase?.url,
    config.marketingFunnel?.supabase?.anonKey,
    config.marketingFunnel?.email?.provider,
    config.marketingFunnel?.email?.appUrl
  ]
  
  const missing = required.filter(value => !value)
  
  if (missing.length > 0) {
    throw new Error(`Missing required marketing funnel configuration: ${missing.join(', ')}`)
  }
  
  return true
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

// Example 1: Using simple config
// import { simpleConfig } from './config-examples'
// export default simpleConfig

// Example 2: Using environment-specific config
// const env = process.env.NODE_ENV || 'development'
// const config = env === 'production' ? productionConfig : developmentConfig
// export default config

// Example 3: Using nested config
// import { nestedConfig } from './config-examples'
// export default nestedConfig

// Example 4: Using function-based config
// const config = createConfig(process.env.NODE_ENV)
// export default config

// Example 5: Using validated config
// import { validatedConfig, validateMarketingFunnelConfig } from './config-examples'
// validateMarketingFunnelConfig(validatedConfig)
// export default validatedConfig 