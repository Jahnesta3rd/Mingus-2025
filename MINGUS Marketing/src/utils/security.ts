import { supabase } from '../lib/supabase'

// Security configuration
interface SecurityConfig {
  rateLimit: {
    enabled: boolean
    windowMs: number
    maxRequests: number
  }
  cors: {
    origins: string[]
    methods: string[]
    headers: string[]
  }
  validation: {
    emailRegex: RegExp
    phoneRegex: RegExp
    maxInputLength: number
  }
}

// Rate limiting storage (in production, use Redis)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>()

// Security configuration
export const securityConfig: SecurityConfig = {
  rateLimit: {
    enabled: process.env.REACT_APP_RATE_LIMIT_ENABLED === 'true',
    windowMs: parseInt(process.env.REACT_APP_RATE_LIMIT_WINDOW_MS || '900000'),
    maxRequests: parseInt(process.env.REACT_APP_RATE_LIMIT_MAX_REQUESTS || '100')
  },
  cors: {
    origins: process.env.REACT_APP_CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
    methods: process.env.REACT_APP_CORS_METHODS?.split(',') || ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    headers: process.env.REACT_APP_CORS_HEADERS?.split(',') || ['Content-Type', 'Authorization']
  },
  validation: {
    emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    phoneRegex: /^\+?[\d\s\-\(\)]{10,}$/,
    maxInputLength: 1000
  }
}

// Rate limiting middleware
export function rateLimit(identifier: string): { allowed: boolean; remaining: number; resetTime: number } {
  if (!securityConfig.rateLimit.enabled) {
    return { allowed: true, remaining: -1, resetTime: 0 }
  }

  const now = Date.now()
  const windowMs = securityConfig.rateLimit.windowMs
  const maxRequests = securityConfig.rateLimit.maxRequests

  const record = rateLimitStore.get(identifier)
  
  if (!record || now > record.resetTime) {
    // New window or expired
    rateLimitStore.set(identifier, {
      count: 1,
      resetTime: now + windowMs
    })
    return { allowed: true, remaining: maxRequests - 1, resetTime: now + windowMs }
  }

  if (record.count >= maxRequests) {
    return { allowed: false, remaining: 0, resetTime: record.resetTime }
  }

  record.count++
  return { allowed: true, remaining: maxRequests - record.count, resetTime: record.resetTime }
}

// Input validation utilities
export function validateEmail(email: string): { valid: boolean; error?: string } {
  if (!email || typeof email !== 'string') {
    return { valid: false, error: 'Email is required' }
  }

  if (email.length > 255) {
    return { valid: false, error: 'Email is too long' }
  }

  if (!securityConfig.validation.emailRegex.test(email)) {
    return { valid: false, error: 'Invalid email format' }
  }

  return { valid: true }
}

export function validatePhone(phone: string): { valid: boolean; error?: string } {
  if (!phone) {
    return { valid: true } // Phone is optional
  }

  if (typeof phone !== 'string') {
    return { valid: false, error: 'Phone must be a string' }
  }

  if (!securityConfig.validation.phoneRegex.test(phone)) {
    return { valid: false, error: 'Invalid phone format' }
  }

  return { valid: true }
}

export function validateInput(input: any, maxLength?: number): { valid: boolean; error?: string } {
  if (input === null || input === undefined) {
    return { valid: false, error: 'Input is required' }
  }

  const length = maxLength || securityConfig.validation.maxInputLength

  if (typeof input === 'string' && input.length > length) {
    return { valid: false, error: `Input exceeds maximum length of ${length} characters` }
  }

  if (typeof input === 'object' && JSON.stringify(input).length > length) {
    return { valid: false, error: `Input exceeds maximum length of ${length} characters` }
  }

  return { valid: true }
}

// XSS prevention
export function sanitizeInput(input: string): string {
  if (typeof input !== 'string') {
    return input
  }

  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
}

// SQL injection prevention (basic)
export function sanitizeSQL(input: string): string {
  if (typeof input !== 'string') {
    return input
  }

  // Remove common SQL injection patterns
  const sqlPatterns = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/gi,
    /(\b(OR|AND)\b\s+\d+\s*=\s*\d+)/gi,
    /(\b(OR|AND)\b\s+['"]\w+['"]\s*=\s*['"]\w+['"])/gi,
    /(--|\/\*|\*\/|;)/g
  ]

  let sanitized = input
  sqlPatterns.forEach(pattern => {
    sanitized = sanitized.replace(pattern, '')
  })

  return sanitized.trim()
}

// Authentication utilities
export async function verifyUserSession(): Promise<{ valid: boolean; user?: any; error?: string }> {
  try {
    const { data: { user }, error } = await supabase.auth.getUser()
    
    if (error || !user) {
      return { valid: false, error: 'Invalid or expired session' }
    }

    return { valid: true, user }
  } catch (error) {
    return { valid: false, error: 'Authentication error' }
  }
}

export async function verifyApiKey(apiKey: string): Promise<{ valid: boolean; error?: string }> {
  const validApiKey = process.env.REACT_APP_EMAIL_API_KEY
  
  if (!validApiKey) {
    return { valid: false, error: 'API key not configured' }
  }

  if (apiKey !== validApiKey) {
    return { valid: false, error: 'Invalid API key' }
  }

  return { valid: true }
}

// CORS utilities
export function validateCORS(origin: string): boolean {
  return securityConfig.cors.origins.includes(origin) || 
         securityConfig.cors.origins.includes('*')
}

export function getCORSHeaders(origin: string): Record<string, string> {
  if (!validateCORS(origin)) {
    return {}
  }

  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': securityConfig.cors.methods.join(', '),
    'Access-Control-Allow-Headers': securityConfig.cors.headers.join(', '),
    'Access-Control-Max-Age': '86400'
  }
}

// Encryption utilities (basic)
export function encryptSensitiveData(data: string): string {
  // In production, use a proper encryption library like crypto-js
  // This is a basic example - replace with proper encryption
  return btoa(encodeURIComponent(data))
}

export function decryptSensitiveData(encryptedData: string): string {
  // In production, use a proper encryption library like crypto-js
  // This is a basic example - replace with proper decryption
  try {
    return decodeURIComponent(atob(encryptedData))
  } catch {
    throw new Error('Invalid encrypted data')
  }
}

// Request validation middleware
export function validateRequest(data: any, schema: Record<string, any>): { valid: boolean; errors: string[] } {
  const errors: string[] = []

  for (const [field, rules] of Object.entries(schema)) {
    const value = data[field]

    // Required field validation
    if (rules.required && (value === undefined || value === null || value === '')) {
      errors.push(`${field} is required`)
      continue
    }

    // Skip further validation if field is not required and empty
    if (!rules.required && (value === undefined || value === null || value === '')) {
      continue
    }

    // Type validation
    if (rules.type && typeof value !== rules.type) {
      errors.push(`${field} must be of type ${rules.type}`)
    }

    // Length validation
    if (rules.minLength && value.length < rules.minLength) {
      errors.push(`${field} must be at least ${rules.minLength} characters`)
    }

    if (rules.maxLength && value.length > rules.maxLength) {
      errors.push(`${field} must be no more than ${rules.maxLength} characters`)
    }

    // Pattern validation
    if (rules.pattern && !rules.pattern.test(value)) {
      errors.push(`${field} format is invalid`)
    }

    // Custom validation
    if (rules.custom) {
      const customResult = rules.custom(value)
      if (customResult !== true) {
        errors.push(customResult || `${field} validation failed`)
      }
    }
  }

  return { valid: errors.length === 0, errors }
}

// Common validation schemas
export const validationSchemas = {
  emailSubscription: {
    email: {
      required: true,
      type: 'string',
      pattern: securityConfig.validation.emailRegex,
      maxLength: 255
    },
    name: {
      required: false,
      type: 'string',
      maxLength: 255
    },
    preferences: {
      required: false,
      type: 'object'
    }
  },
  questionnaireSubmission: {
    email: {
      required: true,
      type: 'string',
      pattern: securityConfig.validation.emailRegex,
      maxLength: 255
    },
    name: {
      required: false,
      type: 'string',
      maxLength: 255
    },
    phone: {
      required: false,
      type: 'string',
      pattern: securityConfig.validation.phoneRegex
    },
    responses: {
      required: true,
      type: 'object'
    },
    score: {
      required: true,
      type: 'number',
      custom: (value: number) => {
        if (value < 0 || value > 100) {
          return 'Score must be between 0 and 100'
        }
        return true
      }
    }
  }
}

// Security headers
export function getSecurityHeaders(): Record<string, string> {
  return {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': process.env.REACT_APP_CSP_POLICY || "default-src 'self'",
    'Strict-Transport-Security': `max-age=${process.env.REACT_APP_HSTS_MAX_AGE || '31536000'}; includeSubDomains; preload`
  }
}

// Audit logging
export function logSecurityEvent(event: string, details: any, userId?: string): void {
  const logEntry = {
    timestamp: new Date().toISOString(),
    event,
    details,
    userId,
    ipAddress: 'client-ip', // In production, get from request
    userAgent: 'client-user-agent' // In production, get from request
  }

  // In production, send to logging service
  console.log('Security Event:', logEntry)
}

// Request sanitization
export function sanitizeRequest(data: any): any {
  if (typeof data === 'string') {
    return sanitizeInput(data)
  }

  if (typeof data === 'object' && data !== null) {
    const sanitized: any = Array.isArray(data) ? [] : {}
    
    for (const [key, value] of Object.entries(data)) {
      sanitized[key] = sanitizeRequest(value)
    }
    
    return sanitized
  }

  return data
}

// API response wrapper with security headers
export function createSecureResponse(data: any, status: number = 200): Response {
  const headers = {
    'Content-Type': 'application/json',
    ...getSecurityHeaders()
  }

  return new Response(JSON.stringify(data), {
    status,
    headers
  })
}

// Error response wrapper
export function createErrorResponse(error: string, status: number = 400): Response {
  return createSecureResponse({
    success: false,
    error,
    timestamp: new Date().toISOString()
  }, status)
}

// Success response wrapper
export function createSuccessResponse(data: any, message?: string): Response {
  return createSecureResponse({
    success: true,
    data,
    message,
    timestamp: new Date().toISOString()
  })
} 