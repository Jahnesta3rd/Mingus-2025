import '@testing-library/jest-dom'
import 'jest-axe/extend-expect'
import { setupTestEnvironment, cleanupTestEnvironment } from './utils/testUtils'

// Extend expect matchers
import 'jest-extended'

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}))

// Mock ResizeObserver
global.ResizeObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}))

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
})

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(callback => setTimeout(callback, 16))
global.cancelAnimationFrame = jest.fn()

// Mock performance API
Object.defineProperty(window, 'performance', {
  writable: true,
  value: {
    now: jest.fn(() => Date.now()),
    getEntriesByType: jest.fn(() => []),
    getEntriesByName: jest.fn(() => []),
    mark: jest.fn(),
    measure: jest.fn(),
    clearMarks: jest.fn(),
    clearMeasures: jest.fn(),
    timeOrigin: Date.now(),
    memory: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000
    }
  }
})

// Mock navigator
Object.defineProperty(window, 'navigator', {
  writable: true,
  value: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    language: 'en-US',
    languages: ['en-US', 'en'],
    onLine: true,
    doNotTrack: null,
    cookieEnabled: true,
    maxTouchPoints: 0,
    hardwareConcurrency: 8,
    deviceMemory: 8,
    connection: {
      effectiveType: '4g',
      downlink: 10,
      rtt: 50,
      saveData: false
    }
  }
})

// Mock window methods
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn()
})

Object.defineProperty(window, 'addEventListener', {
  writable: true,
  value: jest.fn()
})

Object.defineProperty(window, 'removeEventListener', {
  writable: true,
  value: jest.fn()
})

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
}
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
}
global.sessionStorage = sessionStorageMock

// Mock fetch
global.fetch = jest.fn()

// Mock console methods in tests
const originalConsole = { ...console }
beforeEach(() => {
  console.log = jest.fn()
  console.warn = jest.fn()
  console.error = jest.fn()
  console.info = jest.fn()
  console.debug = jest.fn()
})

afterEach(() => {
  console.log = originalConsole.log
  console.warn = originalConsole.warn
  console.error = originalConsole.error
  console.info = originalConsole.info
  console.debug = originalConsole.debug
})

// Global test setup
beforeEach(() => {
  setupTestEnvironment()
})

// Global test cleanup
afterEach(() => {
  cleanupTestEnvironment()
})

// Mock environment variables
process.env.REACT_APP_SUPABASE_URL = 'https://test.supabase.co'
process.env.REACT_APP_SUPABASE_ANON_KEY = 'test-anon-key'
process.env.REACT_APP_GA_MEASUREMENT_ID = 'GA-TEST-ID'
process.env.REACT_APP_MAILCHIMP_API_KEY = 'test-mailchimp-key'
process.env.REACT_APP_MAILCHIMP_LIST_ID = 'test-list-id'
process.env.REACT_APP_CONVERTKIT_API_KEY = 'test-convertkit-key'
process.env.REACT_APP_CONVERTKIT_FORM_ID = 'test-form-id'
process.env.REACT_APP_SENDGRID_API_KEY = 'test-sendgrid-key'

// Mock crypto for secure random values
Object.defineProperty(window, 'crypto', {
  writable: true,
  value: {
    getRandomValues: jest.fn((array) => {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256)
      }
      return array
    }),
    randomUUID: jest.fn(() => 'test-uuid-1234-5678-9012')
  }
})

// Mock URL API
global.URL = {
  createObjectURL: jest.fn(() => 'blob:test-url'),
  revokeObjectURL: jest.fn()
} as any

// Mock File API
global.File = class MockFile {
  name: string
  size: number
  type: string
  
  constructor(bits: any[], name: string, options?: any) {
    this.name = name
    this.size = bits.length
    this.type = options?.type || 'text/plain'
  }
} as any

// Mock FileReader
global.FileReader = class MockFileReader {
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  result: string | ArrayBuffer | null = null
  
  readAsText(blob: Blob) {
    setTimeout(() => {
      this.result = 'test file content'
      this.onload?.(new ProgressEvent('load'))
    }, 0)
  }
  
  readAsDataURL(blob: Blob) {
    setTimeout(() => {
      this.result = 'data:text/plain;base64,dGVzdCBmaWxlIGNvbnRlbnQ='
      this.onload?.(new ProgressEvent('load'))
    }, 0)
  }
} as any

// Mock FormData
global.FormData = class MockFormData {
  private data = new Map()
  
  append(name: string, value: any) {
    this.data.set(name, value)
  }
  
  get(name: string) {
    return this.data.get(name)
  }
  
  has(name: string) {
    return this.data.has(name)
  }
  
  delete(name: string) {
    this.data.delete(name)
  }
  
  entries() {
    return this.data.entries()
  }
  
  keys() {
    return this.data.keys()
  }
  
  values() {
    return this.data.values()
  }
  
  forEach(callback: (value: any, key: string) => void) {
    this.data.forEach(callback)
  }
} as any

// Mock Headers
global.Headers = class MockHeaders {
  private headers = new Map()
  
  constructor(init?: any) {
    if (init) {
      Object.entries(init).forEach(([key, value]) => {
        this.headers.set(key.toLowerCase(), value)
      })
    }
  }
  
  append(name: string, value: string) {
    this.headers.set(name.toLowerCase(), value)
  }
  
  get(name: string) {
    return this.headers.get(name.toLowerCase()) || null
  }
  
  has(name: string) {
    return this.headers.has(name.toLowerCase())
  }
  
  set(name: string, value: string) {
    this.headers.set(name.toLowerCase(), value)
  }
  
  delete(name: string) {
    this.headers.delete(name.toLowerCase())
  }
  
  forEach(callback: (value: string, key: string) => void) {
    this.headers.forEach(callback)
  }
} as any

// Mock Response
global.Response = class MockResponse {
  ok: boolean
  status: number
  statusText: string
  headers: Headers
  body: any
  
  constructor(body?: any, init?: any) {
    this.body = body
    this.ok = init?.status < 400 || true
    this.status = init?.status || 200
    this.statusText = init?.statusText || 'OK'
    this.headers = new Headers(init?.headers)
  }
  
  json() {
    return Promise.resolve(this.body)
  }
  
  text() {
    return Promise.resolve(JSON.stringify(this.body))
  }
  
  blob() {
    return Promise.resolve(new Blob([JSON.stringify(this.body)]))
  }
} as any

// Mock Request
global.Request = class MockRequest {
  url: string
  method: string
  headers: Headers
  body: any
  
  constructor(input: string | Request, init?: any) {
    this.url = typeof input === 'string' ? input : input.url
    this.method = init?.method || 'GET'
    this.headers = new Headers(init?.headers)
    this.body = init?.body
  }
} as any

// Custom matchers for testing
expect.extend({
  toBeValidEmail(received) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const pass = emailRegex.test(received)
    
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid email`,
        pass: true
      }
    } else {
      return {
        message: () => `expected ${received} to be a valid email`,
        pass: false
      }
    }
  },
  
  toBeValidPhone(received) {
    const phoneRegex = /^\+?[\d\s\-\(\)]+$/
    const pass = phoneRegex.test(received)
    
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid phone number`,
        pass: true
      }
    } else {
      return {
        message: () => `expected ${received} to be a valid phone number`,
        pass: false
      }
    }
  },
  
  toBeInRange(received, min, max) {
    const pass = received >= min && received <= max
    
    if (pass) {
      return {
        message: () => `expected ${received} not to be between ${min} and ${max}`,
        pass: true
      }
    } else {
      return {
        message: () => `expected ${received} to be between ${min} and ${max}`,
        pass: false
      }
    }
  }
})

// Global test utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidEmail(): R
      toBeValidPhone(): R
      toBeInRange(min: number, max: number): R
    }
  }
}

// Export test utilities for use in tests
export { setupTestEnvironment, cleanupTestEnvironment } 