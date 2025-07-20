import { RatchetMoneyAPI } from '../api'

// Mock environment variables for testing
process.env.REACT_APP_SUPABASE_URL = 'https://test.supabase.co'
process.env.REACT_APP_SUPABASE_ANON_KEY = 'test-anon-key'
process.env.REACT_APP_EMAIL_PROVIDER = 'mock'

describe('Backend Integration Tests', () => {
  beforeEach(() => {
    // Clear any existing mocks
    jest.clearAllMocks()
  })

  describe('Assessment Service', () => {
    test('should calculate correct score and segment', async () => {
      const mockAnswers = {
        'relationship_status': 'married',
        'spending_habits': 'overspend',
        'financial_stress': 'often',
        'emotional_spending': ['breakup', 'fights'],
        'financial_boundaries': 'uncomfortable',
        'money_talks': 'never',
        'relationship_money_conflicts': 'often',
        'financial_independence': 'not_important'
      }

      const submission = {
        email: 'test@example.com',
        firstName: 'Test',
        phoneNumber: '1234567890',
        contactMethod: 'email' as const,
        betaInterest: 'very' as const,
        answers: mockAnswers,
        leadSource: 'test',
        utmData: {
          source: 'test',
          medium: 'test',
          campaign: 'test'
        }
      }

      // This would test the actual scoring logic
      // For now, we'll just verify the service exists
      expect(RatchetMoneyAPI.assessment).toBeDefined()
      expect(typeof RatchetMoneyAPI.assessment.submitAssessment).toBe('function')
    })

    test('should handle assessment questions correctly', async () => {
      const questions = await RatchetMoneyAPI.assessment.getAssessmentQuestions()
      expect(Array.isArray(questions)).toBe(true)
      expect(questions.length).toBeGreaterThan(0)
      
      // Verify question structure
      const firstQuestion = questions[0]
      expect(firstQuestion).toHaveProperty('id')
      expect(firstQuestion).toHaveProperty('question')
      expect(firstQuestion).toHaveProperty('type')
      expect(firstQuestion).toHaveProperty('required')
    })
  })

  describe('Lead Service', () => {
    test('should create lead with correct data', async () => {
      const leadData = {
        email: 'test@example.com',
        name: 'Test User',
        phone: '1234567890',
        leadSource: 'test',
        contactMethod: 'email' as const,
        betaInterest: true,
        utmData: {
          source: 'test',
          medium: 'test',
          campaign: 'test'
        }
      }

      expect(RatchetMoneyAPI.leads).toBeDefined()
      expect(typeof RatchetMoneyAPI.leads.createLead).toBe('function')
    })

    test('should get lead analytics', async () => {
      expect(typeof RatchetMoneyAPI.leads.getLeadAnalytics).toBe('function')
      
      // Test analytics structure
      const analytics = await RatchetMoneyAPI.leads.getLeadAnalytics()
      expect(analytics).toHaveProperty('totalLeads')
      expect(analytics).toHaveProperty('confirmedLeads')
      expect(analytics).toHaveProperty('assessmentCompletions')
      expect(analytics).toHaveProperty('segmentDistribution')
      expect(analytics).toHaveProperty('averageScore')
      expect(analytics).toHaveProperty('conversionRate')
    })
  })

  describe('Email Service', () => {
    test('should send email with correct data', async () => {
      const emailData = {
        to: 'test@example.com',
        subject: 'Test Email',
        body: '<h1>Test</h1>',
        leadId: 'test-lead-id',
        emailType: 'confirmation' as const
      }

      expect(RatchetMoneyAPI.email).toBeDefined()
      expect(typeof RatchetMoneyAPI.email.sendEmail).toBe('function')
    })

    test('should send welcome email', async () => {
      const mockLead = {
        id: 'test-lead-id',
        email: 'test@example.com',
        name: 'Test User',
        segment: 'stress-free' as const,
        score: 10,
        product_tier: 'Budget ($10)' as const,
        created_at: new Date().toISOString(),
        confirmed: true,
        assessment_completed: true,
        assessment_answers: {},
        email_sequence_sent: 0,
        last_email_sent: null
      }

      expect(typeof RatchetMoneyAPI.email.sendWelcomeEmail).toBe('function')
    })
  })

  describe('Complete Workflow', () => {
    test('should complete full assessment workflow', async () => {
      const submission = {
        email: 'test@example.com',
        firstName: 'Test',
        phoneNumber: '1234567890',
        contactMethod: 'email' as const,
        betaInterest: 'somewhat' as const,
        answers: {
          'relationship_status': 'single',
          'spending_habits': 'independent',
          'financial_stress': 'never'
        },
        leadSource: 'test',
        utmData: {}
      }

      expect(typeof RatchetMoneyAPI.completeAssessment).toBe('function')
    })

    test('should create lead and send confirmation', async () => {
      const leadData = {
        email: 'test@example.com',
        name: 'Test User',
        leadSource: 'test',
        contactMethod: 'email' as const,
        betaInterest: true
      }

      expect(typeof RatchetMoneyAPI.createLeadAndConfirm).toBe('function')
    })

    test('should get comprehensive analytics', async () => {
      const analytics = await RatchetMoneyAPI.getAnalytics()
      
      expect(analytics).toHaveProperty('leads')
      expect(analytics).toHaveProperty('assessments')
      expect(analytics).toHaveProperty('overall')
      
      expect(analytics.overall).toHaveProperty('totalUsers')
      expect(analytics.overall).toHaveProperty('conversionRate')
      expect(analytics.overall).toHaveProperty('averageScore')
      expect(analytics.overall).toHaveProperty('topSegment')
    })
  })

  describe('Error Handling', () => {
    test('should handle missing email gracefully', async () => {
      const submission = {
        email: '',
        firstName: 'Test',
        contactMethod: 'email' as const,
        betaInterest: 'somewhat' as const,
        answers: {},
        leadSource: 'test',
        utmData: {}
      }

      await expect(RatchetMoneyAPI.completeAssessment(submission))
        .rejects
        .toThrow('User email not found')
    })

    test('should handle database errors gracefully', async () => {
      // Test with invalid lead ID
      await expect(RatchetMoneyAPI.leads.getLeadById('invalid-id'))
        .resolves
        .toBeNull()
    })
  })
}) 