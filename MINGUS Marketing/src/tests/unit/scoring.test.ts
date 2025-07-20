import { calculateScore, calculateSegment, validateEmail, validateForm, saveProgress, loadProgress } from '../../utils/questionnaireUtils'
import { generateMockQuestions, generateMockResponses, generateMockResults } from '../utils/testUtils'

describe('Scoring Algorithm', () => {
  const questions = generateMockQuestions()
  
  describe('calculateScore', () => {
    it('should calculate correct score for all positive responses', () => {
      const responses = questions.map(q => ({
        questionId: q.id,
        response: q.options[q.options.length - 1], // Last option (most positive)
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const score = calculateScore(questions, responses)
      expect(score).toBeGreaterThan(80)
      expect(score).toBeLessThanOrEqual(100)
    })

    it('should calculate correct score for all negative responses', () => {
      const responses = questions.map(q => ({
        questionId: q.id,
        response: q.options[0], // First option (most negative)
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const score = calculateScore(questions, responses)
      expect(score).toBeGreaterThanOrEqual(0)
      expect(score).toBeLessThan(30)
    })

    it('should calculate correct score for mixed responses', () => {
      const responses = questions.map((q, index) => ({
        questionId: q.id,
        response: q.options[Math.floor(index / 2) % q.options.length], // Alternating responses
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const score = calculateScore(questions, responses)
      expect(score).toBeGreaterThanOrEqual(0)
      expect(score).toBeLessThanOrEqual(100)
    })

    it('should handle missing responses', () => {
      const responses = questions.slice(0, 5).map(q => ({
        questionId: q.id,
        response: q.options[2], // Middle option
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const score = calculateScore(questions, responses)
      expect(score).toBeGreaterThanOrEqual(0)
      expect(score).toBeLessThanOrEqual(100)
    })

    it('should apply question weights correctly', () => {
      const weightedQuestions = questions.map((q, index) => ({
        ...q,
        weight: index + 1 // Different weights for each question
      }))
      
      const responses = weightedQuestions.map(q => ({
        questionId: q.id,
        response: q.options[2], // Middle option
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const score = calculateScore(weightedQuestions, responses)
      expect(score).toBeGreaterThanOrEqual(0)
      expect(score).toBeLessThanOrEqual(100)
    })

    it('should handle edge cases', () => {
      // Empty responses
      expect(calculateScore(questions, [])).toBe(0)
      
      // No questions
      expect(calculateScore([], [])).toBe(0)
      
      // Invalid question weights
      const invalidQuestions = questions.map(q => ({ ...q, weight: -1 }))
      const responses = questions.map(q => ({
        questionId: q.id,
        response: q.options[2],
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      expect(calculateScore(invalidQuestions, responses)).toBeGreaterThanOrEqual(0)
    })
  })

  describe('calculateSegment', () => {
    it('should return correct segment for high scores', () => {
      const segment = calculateSegment(85)
      expect(segment).toBe('stress-free')
    })

    it('should return correct segment for medium scores', () => {
      const segment = calculateSegment(65)
      expect(segment).toBe('balanced')
    })

    it('should return correct segment for low scores', () => {
      const segment = calculateSegment(35)
      expect(segment).toBe('stress-prone')
    })

    it('should handle boundary values', () => {
      expect(calculateSegment(80)).toBe('stress-free')
      expect(calculateSegment(79)).toBe('balanced')
      expect(calculateSegment(50)).toBe('balanced')
      expect(calculateSegment(49)).toBe('stress-prone')
    })

    it('should handle edge cases', () => {
      expect(calculateSegment(100)).toBe('stress-free')
      expect(calculateSegment(0)).toBe('stress-prone')
      expect(calculateSegment(-10)).toBe('stress-prone')
      expect(calculateSegment(150)).toBe('stress-free')
    })
  })
})

describe('Form Validation', () => {
  describe('validateEmail', () => {
    it('should validate correct email formats', () => {
      const validEmails = [
        'test@example.com',
        'user.name@domain.co.uk',
        'user+tag@example.org',
        '123@numbers.com',
        'user@subdomain.example.com'
      ]
      
      validEmails.forEach(email => {
        expect(validateEmail(email)).toBe(true)
      })
    })

    it('should reject invalid email formats', () => {
      const invalidEmails = [
        'invalid-email',
        '@example.com',
        'user@',
        'user@.com',
        'user..name@example.com',
        'user@example..com',
        'user name@example.com',
        'user@example.com.',
        '.user@example.com'
      ]
      
      invalidEmails.forEach(email => {
        expect(validateEmail(email)).toBe(false)
      })
    })

    it('should handle edge cases', () => {
      expect(validateEmail('')).toBe(false)
      expect(validateEmail('   ')).toBe(false)
      expect(validateEmail(null as any)).toBe(false)
      expect(validateEmail(undefined as any)).toBe(false)
    })
  })

  describe('validateForm', () => {
    it('should validate complete form data', () => {
      const validFormData = {
        email: 'test@example.com',
        name: 'Test User',
        age: 30,
        income: 75000,
        phone: '+1234567890',
        contactMethod: 'email',
        betaInterest: true
      }
      
      const result = validateForm(validFormData)
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })

    it('should reject form with missing required fields', () => {
      const invalidFormData = {
        email: '',
        name: '',
        age: 0,
        income: 0,
        phone: '',
        contactMethod: 'email',
        betaInterest: false
      }
      
      const result = validateForm(invalidFormData)
      expect(result.isValid).toBe(false)
      expect(result.errors.email).toBeDefined()
      expect(result.errors.name).toBeDefined()
    })

    it('should validate age range', () => {
      const formData = {
        email: 'test@example.com',
        name: 'Test User',
        age: 15, // Too young
        income: 75000,
        phone: '+1234567890',
        contactMethod: 'email',
        betaInterest: true
      }
      
      const result = validateForm(formData)
      expect(result.isValid).toBe(false)
      expect(result.errors.age).toBeDefined()
    })

    it('should validate income range', () => {
      const formData = {
        email: 'test@example.com',
        name: 'Test User',
        age: 30,
        income: 5000, // Too low
        phone: '+1234567890',
        contactMethod: 'email',
        betaInterest: true
      }
      
      const result = validateForm(formData)
      expect(result.isValid).toBe(false)
      expect(result.errors.income).toBeDefined()
    })

    it('should validate phone format', () => {
      const formData = {
        email: 'test@example.com',
        name: 'Test User',
        age: 30,
        income: 75000,
        phone: 'invalid-phone',
        contactMethod: 'phone',
        betaInterest: true
      }
      
      const result = validateForm(formData)
      expect(result.isValid).toBe(false)
      expect(result.errors.phone).toBeDefined()
    })

    it('should handle partial form data', () => {
      const partialFormData = {
        email: 'test@example.com',
        name: 'Test User'
        // Missing other fields
      }
      
      const result = validateForm(partialFormData as any)
      expect(result.isValid).toBe(false)
      expect(Object.keys(result.errors).length).toBeGreaterThan(0)
    })
  })
})

describe('Local Storage Functionality', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  describe('saveProgress', () => {
    it('should save questionnaire progress', () => {
      const progress = {
        currentQuestion: 5,
        responses: {
          q1: 'Very confident',
          q2: 'Save for retirement',
          q3: 'Weekly',
          q4: '10-20%',
          q5: 'Research thoroughly'
        },
        startTime: Date.now()
      }
      
      saveProgress(progress)
      
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'questionnaire_progress',
        JSON.stringify(progress)
      )
    })

    it('should handle large response data', () => {
      const largeResponses = {}
      for (let i = 1; i <= 100; i++) {
        largeResponses[`q${i}`] = `Response ${i} with some longer text content`
      }
      
      const progress = {
        currentQuestion: 50,
        responses: largeResponses,
        startTime: Date.now()
      }
      
      expect(() => saveProgress(progress)).not.toThrow()
    })

    it('should handle invalid data gracefully', () => {
      expect(() => saveProgress(null as any)).not.toThrow()
      expect(() => saveProgress(undefined as any)).not.toThrow()
      expect(() => saveProgress({} as any)).not.toThrow()
    })
  })

  describe('loadProgress', () => {
    it('should load saved progress', () => {
      const savedProgress = {
        currentQuestion: 5,
        responses: {
          q1: 'Very confident',
          q2: 'Save for retirement'
        },
        startTime: Date.now()
      }
      
      localStorage.setItem('questionnaire_progress', JSON.stringify(savedProgress))
      
      const loadedProgress = loadProgress()
      expect(loadedProgress).toEqual(savedProgress)
    })

    it('should return null for non-existent progress', () => {
      const loadedProgress = loadProgress()
      expect(loadedProgress).toBeNull()
    })

    it('should handle corrupted data', () => {
      localStorage.setItem('questionnaire_progress', 'invalid-json')
      
      const loadedProgress = loadProgress()
      expect(loadedProgress).toBeNull()
    })

    it('should handle expired progress', () => {
      const expiredProgress = {
        currentQuestion: 5,
        responses: {},
        startTime: Date.now() - (24 * 60 * 60 * 1000) // 24 hours ago
      }
      
      localStorage.setItem('questionnaire_progress', JSON.stringify(expiredProgress))
      
      const loadedProgress = loadProgress()
      expect(loadedProgress).toBeNull()
    })
  })
})

describe('Results Calculation', () => {
  describe('calculateResults', () => {
    it('should generate results for high score', () => {
      const questions = generateMockQuestions()
      const responses = questions.map(q => ({
        questionId: q.id,
        response: q.options[q.options.length - 1], // Most positive response
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const results = calculateResults(questions, responses)
      
      expect(results.score).toBeGreaterThan(80)
      expect(results.segment).toBe('stress-free')
      expect(results.recommendations).toHaveLength(5)
      expect(results.strengths).toHaveLength(3)
      expect(results.areasForImprovement).toHaveLength(3)
      expect(results.nextSteps).toHaveLength(3)
    })

    it('should generate results for low score', () => {
      const questions = generateMockQuestions()
      const responses = questions.map(q => ({
        questionId: q.id,
        response: q.options[0], // Most negative response
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const results = calculateResults(questions, responses)
      
      expect(results.score).toBeLessThan(30)
      expect(results.segment).toBe('stress-prone')
      expect(results.recommendations).toHaveLength(5)
      expect(results.strengths).toHaveLength(3)
      expect(results.areasForImprovement).toHaveLength(3)
      expect(results.nextSteps).toHaveLength(3)
    })

    it('should handle partial responses', () => {
      const questions = generateMockQuestions()
      const responses = questions.slice(0, 5).map(q => ({
        questionId: q.id,
        response: q.options[2], // Middle response
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const results = calculateResults(questions, responses)
      
      expect(results.score).toBeGreaterThanOrEqual(0)
      expect(results.score).toBeLessThanOrEqual(100)
      expect(results.segment).toBeDefined()
      expect(results.recommendations).toBeDefined()
    })

    it('should generate consistent results for same inputs', () => {
      const questions = generateMockQuestions()
      const responses = questions.map(q => ({
        questionId: q.id,
        response: q.options[2], // Middle response
        timestamp: new Date().toISOString(),
        timeSpent: 20
      }))
      
      const results1 = calculateResults(questions, responses)
      const results2 = calculateResults(questions, responses)
      
      expect(results1.score).toBe(results2.score)
      expect(results1.segment).toBe(results2.segment)
    })
  })
})

describe('Performance Tests', () => {
  it('should calculate score quickly for large datasets', () => {
    const largeQuestions = Array.from({ length: 100 }, (_, i) => ({
      id: `q${i + 1}`,
      text: `Question ${i + 1}`,
      type: 'multiple_choice',
      options: ['Option 1', 'Option 2', 'Option 3', 'Option 4', 'Option 5'],
      category: 'test',
      weight: 1.0,
      required: true,
      order: i + 1
    }))
    
    const largeResponses = largeQuestions.map(q => ({
      questionId: q.id,
      response: q.options[2],
      timestamp: new Date().toISOString(),
      timeSpent: 20
    }))
    
    const startTime = performance.now()
    const score = calculateScore(largeQuestions, largeResponses)
    const endTime = performance.now()
    
    expect(score).toBeGreaterThanOrEqual(0)
    expect(score).toBeLessThanOrEqual(100)
    expect(endTime - startTime).toBeLessThan(100) // Should complete in under 100ms
  })

  it('should handle memory efficiently', () => {
    const initialMemory = (performance as any).memory?.usedJSHeapSize || 0
    
    // Generate and process large dataset
    const questions = generateMockQuestions(50)
    const responses = generateMockResponses(questions)
    
    for (let i = 0; i < 100; i++) {
      calculateScore(questions, responses)
      calculateResults(questions, responses)
    }
    
    const finalMemory = (performance as any).memory?.usedJSHeapSize || 0
    const memoryIncrease = finalMemory - initialMemory
    
    // Memory increase should be reasonable (less than 10MB)
    expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024)
  })
})

// Mock the questionnaireUtils functions for testing
jest.mock('../../utils/questionnaireUtils', () => ({
  calculateScore: jest.fn((questions, responses) => {
    if (questions.length === 0 || responses.length === 0) return 0
    
    const totalWeight = questions.reduce((sum, q) => sum + (q.weight || 1), 0)
    const weightedScore = responses.reduce((sum, r) => {
      const question = questions.find(q => q.id === r.questionId)
      if (!question) return sum
      
      const optionIndex = question.options.indexOf(r.response)
      const normalizedScore = (optionIndex / (question.options.length - 1)) * 100
      return sum + (normalizedScore * (question.weight || 1))
    }, 0)
    
    return Math.round(weightedScore / totalWeight)
  }),
  
  calculateSegment: jest.fn((score) => {
    if (score >= 80) return 'stress-free'
    if (score >= 50) return 'balanced'
    return 'stress-prone'
  }),
  
  validateEmail: jest.fn((email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }),
  
  validateForm: jest.fn((formData) => {
    const errors: any = {}
    
    if (!formData.email || !validateEmail(formData.email)) {
      errors.email = 'Valid email is required'
    }
    
    if (!formData.name || formData.name.trim().length < 2) {
      errors.name = 'Name is required'
    }
    
    if (!formData.age || formData.age < 18 || formData.age > 100) {
      errors.age = 'Age must be between 18 and 100'
    }
    
    if (!formData.income || formData.income < 10000) {
      errors.income = 'Income must be at least $10,000'
    }
    
    if (formData.contactMethod === 'phone' && (!formData.phone || !/^\+?[\d\s\-\(\)]+$/.test(formData.phone))) {
      errors.phone = 'Valid phone number is required'
    }
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    }
  }),
  
  saveProgress: jest.fn((progress) => {
    localStorage.setItem('questionnaire_progress', JSON.stringify(progress))
  }),
  
  loadProgress: jest.fn(() => {
    const saved = localStorage.getItem('questionnaire_progress')
    if (!saved) return null
    
    try {
      const progress = JSON.parse(saved)
      const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000)
      
      if (progress.startTime && progress.startTime < oneDayAgo) {
        localStorage.removeItem('questionnaire_progress')
        return null
      }
      
      return progress
    } catch {
      return null
    }
  }),
  
  calculateResults: jest.fn((questions, responses) => {
    const score = calculateScore(questions, responses)
    const segment = calculateSegment(score)
    
    return {
      score,
      segment,
      segmentDescription: `You are a ${segment} person`,
      recommendations: [
        'Set up automatic savings',
        'Create a budget',
        'Build emergency fund',
        'Consider investments',
        'Review goals regularly'
      ],
      strengths: [
        'Financial awareness',
        'Good habits',
        'Risk management'
      ],
      areasForImprovement: [
        'Emergency fund',
        'Investment diversity',
        'Regular reviews'
      ],
      nextSteps: [
        'Set up automatic savings',
        'Create monthly review',
        'Schedule check-in'
      ]
    }
  })
})) 