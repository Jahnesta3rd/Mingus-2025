import { RatchetMoneyAPI } from '../../api'

// Simple test to verify backend integration
describe('Backend Integration - Simple Test', () => {
  test('should have all required services', () => {
    expect(RatchetMoneyAPI.assessment).toBeDefined()
    expect(RatchetMoneyAPI.email).toBeDefined()
    expect(RatchetMoneyAPI.leads).toBeDefined()
  })

  test('should have assessment service methods', () => {
    expect(typeof RatchetMoneyAPI.assessment.submitAssessment).toBe('function')
    expect(typeof RatchetMoneyAPI.assessment.getAssessmentQuestions).toBe('function')
    expect(typeof RatchetMoneyAPI.assessment.getLeadByEmail).toBe('function')
  })

  test('should have email service methods', () => {
    expect(typeof RatchetMoneyAPI.email.sendEmail).toBe('function')
    expect(typeof RatchetMoneyAPI.email.sendWelcomeEmail).toBe('function')
    expect(typeof RatchetMoneyAPI.email.sendFollowUpEmail).toBe('function')
  })

  test('should have lead service methods', () => {
    expect(typeof RatchetMoneyAPI.leads.createLead).toBe('function')
    expect(typeof RatchetMoneyAPI.leads.getLeadByEmail).toBe('function')
    expect(typeof RatchetMoneyAPI.leads.getLeadAnalytics).toBe('function')
  })

  test('should have main API methods', () => {
    expect(typeof RatchetMoneyAPI.completeAssessment).toBe('function')
    expect(typeof RatchetMoneyAPI.createLeadAndConfirm).toBe('function')
    expect(typeof RatchetMoneyAPI.getAnalytics).toBe('function')
  })
}) 