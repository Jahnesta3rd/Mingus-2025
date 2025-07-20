import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { BrowserRouter } from 'react-router-dom'

// Test wrapper with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Mock data generators
export const generateMockUser = (overrides = {}) => ({
  id: 'test-user-123',
  email: 'test@example.com',
  name: 'Test User',
  age: 30,
  income: 75000,
  phone: '+1234567890',
  contactMethod: 'email',
  betaInterest: true,
  createdAt: new Date().toISOString(),
  ...overrides
})

export const generateMockQuestion = (overrides = {}) => ({
  id: 'q1',
  text: 'How do you typically feel about your financial situation?',
  type: 'multiple_choice',
  options: ['Very stressed', 'Somewhat stressed', 'Neutral', 'Confident', 'Very confident'],
  category: 'financial_attitude',
  weight: 1.0,
  required: true,
  order: 1,
  ...overrides
})

export const generateMockQuestions = (count = 10) => {
  const questions = [
    {
      id: 'q1',
      text: 'How do you typically feel about your financial situation?',
      type: 'multiple_choice',
      options: ['Very stressed', 'Somewhat stressed', 'Neutral', 'Confident', 'Very confident'],
      category: 'financial_attitude',
      weight: 1.0
    },
    {
      id: 'q2',
      text: 'What is your primary financial goal?',
      type: 'multiple_choice',
      options: ['Save for retirement', 'Pay off debt', 'Build emergency fund', 'Invest for growth', 'Buy a home'],
      category: 'financial_goals',
      weight: 1.2
    },
    {
      id: 'q3',
      text: 'How often do you check your bank account?',
      type: 'multiple_choice',
      options: ['Daily', 'Weekly', 'Monthly', 'Rarely', 'Never'],
      category: 'financial_behavior',
      weight: 0.8
    },
    {
      id: 'q4',
      text: 'How much do you save each month?',
      type: 'multiple_choice',
      options: ['Nothing', 'Less than 10%', '10-20%', '20-30%', 'More than 30%'],
      category: 'savings_behavior',
      weight: 1.5
    },
    {
      id: 'q5',
      text: 'How do you make investment decisions?',
      type: 'multiple_choice',
      options: ['Research thoroughly', 'Follow advice', 'Gut feeling', 'Avoid investing', 'Not sure'],
      category: 'investment_approach',
      weight: 1.3
    },
    {
      id: 'q6',
      text: 'How do you handle unexpected expenses?',
      type: 'multiple_choice',
      options: ['Use emergency fund', 'Credit card', 'Borrow money', 'Cut other expenses', 'Panic'],
      category: 'emergency_handling',
      weight: 1.1
    },
    {
      id: 'q7',
      text: 'How do you track your spending?',
      type: 'multiple_choice',
      options: ['Budget app', 'Spreadsheet', 'Mental notes', 'Don\'t track', 'Not sure'],
      category: 'spending_tracking',
      weight: 0.9
    },
    {
      id: 'q8',
      text: 'How do you feel about taking financial risks?',
      type: 'multiple_choice',
      options: ['Very comfortable', 'Somewhat comfortable', 'Neutral', 'Uncomfortable', 'Very uncomfortable'],
      category: 'risk_tolerance',
      weight: 1.4
    },
    {
      id: 'q9',
      text: 'How do you plan for major purchases?',
      type: 'multiple_choice',
      options: ['Save in advance', 'Use credit', 'Wait for sales', 'Impulse buy', 'Avoid large purchases'],
      category: 'purchase_planning',
      weight: 1.0
    },
    {
      id: 'q10',
      text: 'How do you view your financial future?',
      type: 'multiple_choice',
      options: ['Very optimistic', 'Somewhat optimistic', 'Neutral', 'Concerned', 'Very worried'],
      category: 'financial_outlook',
      weight: 1.2
    }
  ]

  return questions.slice(0, count).map((q, index) => ({
    ...q,
    order: index + 1
  }))
}

export const generateMockResponses = (questions = generateMockQuestions()) => {
  return questions.map(question => ({
    questionId: question.id,
    response: question.options[Math.floor(Math.random() * question.options.length)],
    timestamp: new Date().toISOString(),
    timeSpent: Math.floor(Math.random() * 30) + 10 // 10-40 seconds
  }))
}

export const generateMockResults = (overrides = {}) => ({
  score: 75,
  segment: 'stress-free',
  segmentDescription: 'You have a balanced approach to money management',
  recommendations: [
    'Set up automatic savings transfers',
    'Create a simple budget system',
    'Build an emergency fund',
    'Consider low-risk investments',
    'Review your financial goals regularly'
  ],
  strengths: [
    'Good financial awareness',
    'Consistent saving habits',
    'Risk-appropriate decisions'
  ],
  areasForImprovement: [
    'Emergency fund could be larger',
    'Consider diversifying investments',
    'Regular financial reviews needed'
  ],
  nextSteps: [
    'Set up automatic savings',
    'Create monthly budget review',
    'Schedule quarterly financial check-in'
  ],
  ...overrides
})

// Mock analytics
export const mockAnalytics = {
  trackEvent: jest.fn(),
  trackPageView: jest.fn(),
  trackQuestionnaireStart: jest.fn(),
  trackQuestionCompleted: jest.fn(),
  trackEmailSubmitted: jest.fn(),
  trackResultsViewed: jest.fn(),
  trackCTAClick: jest.fn(),
  trackAbandonment: jest.fn(),
  trackFunnelStage: jest.fn(),
  trackUserBehavior: jest.fn(),
  trackPerformance: jest.fn(),
  setConsent: jest.fn(),
  initializeSession: jest.fn()
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
}

// Mock sessionStorage
export const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
}

// Mock fetch
export const mockFetch = jest.fn()

// Mock IntersectionObserver
export const mockIntersectionObserver = {
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}

// Mock ResizeObserver
export const mockResizeObserver = {
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}

// Mock Performance API
export const mockPerformance = {
  now: jest.fn(() => Date.now()),
  getEntriesByType: jest.fn(() => []),
  getEntriesByName: jest.fn(() => []),
  mark: jest.fn(),
  measure: jest.fn(),
  clearMarks: jest.fn(),
  clearMeasures: jest.fn(),
  timeOrigin: Date.now()
}

// Mock navigator
export const mockNavigator = {
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

// Mock window
export const mockWindow = {
  innerWidth: 1920,
  innerHeight: 1080,
  screen: {
    width: 1920,
    height: 1080,
    availWidth: 1920,
    availHeight: 1040
  },
  location: {
    href: 'https://ratchetmoney.com',
    origin: 'https://ratchetmoney.com',
    pathname: '/',
    search: '',
    hash: ''
  },
  history: {
    pushState: jest.fn(),
    replaceState: jest.fn(),
    go: jest.fn(),
    back: jest.fn(),
    forward: jest.fn()
  },
  scrollTo: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn()
}

// Test setup utilities
export const setupTestEnvironment = () => {
  // Mock global objects
  global.fetch = mockFetch
  global.localStorage = mockLocalStorage
  global.sessionStorage = mockSessionStorage
  global.navigator = mockNavigator as any
  global.window = mockWindow as any
  global.IntersectionObserver = jest.fn(() => mockIntersectionObserver)
  global.ResizeObserver = jest.fn(() => mockResizeObserver)
  global.performance = mockPerformance as any

  // Mock console methods in tests
  global.console = {
    ...console,
    log: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    debug: jest.fn()
  }

  // Mock requestAnimationFrame
  global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16))
  global.cancelAnimationFrame = jest.fn()

  // Mock matchMedia
  global.matchMedia = jest.fn(() => ({
    matches: false,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
}

export const cleanupTestEnvironment = () => {
  jest.clearAllMocks()
  jest.clearAllTimers()
}

// Test data helpers
export const createTestQuestionnaireState = (overrides = {}) => ({
  currentQuestion: 1,
  totalQuestions: 10,
  responses: {},
  progress: 0,
  startTime: Date.now(),
  isComplete: false,
  ...overrides
})

export const createTestValidationState = (overrides = {}) => ({
  errors: {},
  touched: {},
  isValid: true,
  isSubmitting: false,
  ...overrides
})

// Accessibility testing helpers
export const accessibilityTestHelpers = {
  // Check for proper heading structure
  checkHeadingStructure: (container: HTMLElement) => {
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
    const headingLevels = Array.from(headings).map(h => parseInt(h.tagName.charAt(1)))
    
    // Check for skipped heading levels
    for (let i = 1; i < headingLevels.length; i++) {
      if (headingLevels[i] - headingLevels[i - 1] > 1) {
        throw new Error(`Skipped heading level: ${headingLevels[i - 1]} to ${headingLevels[i]}`)
      }
    }
  },

  // Check for proper form labels
  checkFormLabels: (container: HTMLElement) => {
    const inputs = container.querySelectorAll('input, select, textarea')
    inputs.forEach(input => {
      const id = input.getAttribute('id')
      if (id) {
        const label = container.querySelector(`label[for="${id}"]`)
        if (!label) {
          throw new Error(`Input with id "${id}" missing associated label`)
        }
      }
    })
  },

  // Check for proper ARIA attributes
  checkAriaAttributes: (container: HTMLElement) => {
    const elementsWithAria = container.querySelectorAll('[aria-*]')
    elementsWithAria.forEach(element => {
      const ariaAttributes = Array.from(element.attributes)
        .filter(attr => attr.name.startsWith('aria-'))
      
      ariaAttributes.forEach(attr => {
        if (attr.value === '') {
          throw new Error(`Empty ARIA attribute: ${attr.name}`)
        }
      })
    })
  },

  // Check for proper color contrast (basic check)
  checkColorContrast: (container: HTMLElement) => {
    const elements = container.querySelectorAll('*')
    elements.forEach(element => {
      const style = window.getComputedStyle(element)
      const backgroundColor = style.backgroundColor
      const color = style.color
      
      // Basic check - in real testing, use a proper contrast checker
      if (backgroundColor === 'transparent' && color === 'transparent') {
        console.warn('Potential contrast issue detected')
      }
    })
  }
}

// Performance testing helpers
export const performanceTestHelpers = {
  // Measure render time
  measureRenderTime: async (component: ReactElement) => {
    const start = performance.now()
    const { unmount } = customRender(component)
    const end = performance.now()
    unmount()
    return end - start
  },

  // Measure memory usage
  measureMemoryUsage: () => {
    if ('memory' in performance) {
      return (performance as any).memory
    }
    return null
  },

  // Simulate slow network
  simulateSlowNetwork: (delay = 1000) => {
    return new Promise(resolve => setTimeout(resolve, delay))
  },

  // Check bundle size (mock)
  checkBundleSize: () => {
    // In real testing, this would check actual bundle size
    return {
      total: 250000, // 250KB
      gzipped: 75000, // 75KB
      chunks: 3
    }
  }
}

// A/B testing helpers
export const abTestHelpers = {
  // Generate test variants
  generateTestVariants: (testId: string, variants: string[]) => {
    return variants.map(variant => ({
      testId,
      variant,
      impressions: 0,
      conversions: 0,
      conversionRate: 0
    }))
  },

  // Calculate statistical significance
  calculateSignificance: (control: number, variant: number, controlN: number, variantN: number) => {
    // Simplified chi-square test
    const controlRate = control / controlN
    const variantRate = variant / variantN
    const pooledRate = (control + variant) / (controlN + variantN)
    
    const chiSquare = Math.pow(controlRate - variantRate, 2) / 
      (pooledRate * (1 - pooledRate) * (1/controlN + 1/variantN))
    
    return chiSquare > 3.84 // 95% confidence level
  },

  // Simulate A/B test results
  simulateABTestResults: (testId: string, days = 30) => {
    const results = []
    for (let day = 0; day < days; day++) {
      results.push({
        date: new Date(Date.now() - (days - day) * 24 * 60 * 60 * 1000).toISOString(),
        control: {
          impressions: Math.floor(Math.random() * 100) + 50,
          conversions: Math.floor(Math.random() * 20) + 5
        },
        variant: {
          impressions: Math.floor(Math.random() * 100) + 50,
          conversions: Math.floor(Math.random() * 25) + 8
        }
      })
    }
    return results
  }
}

// Export everything
export * from '@testing-library/react'
export { customRender as render } 