import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Questionnaire } from '../../components/Questionnaire'
import { AssessmentResults } from '../../components/AssessmentResults'
import { OptimizedLandingPage } from '../../components/OptimizedLandingPage'
import { mockAnalytics, setupTestEnvironment, cleanupTestEnvironment, generateMockQuestions, generateMockResponses } from '../utils/testUtils'

// Mock the analytics service
jest.mock('../../services/analytics', () => ({
  analytics: mockAnalytics
}))

// Mock the Supabase client
jest.mock('../../lib/supabase', () => ({
  supabase: {
    from: jest.fn(() => ({
      insert: jest.fn(() => Promise.resolve({ data: null, error: null })),
      select: jest.fn(() => Promise.resolve({ data: [], error: null })),
      update: jest.fn(() => Promise.resolve({ data: null, error: null }))
    })),
    auth: {
      signUp: jest.fn(() => Promise.resolve({ data: null, error: null })),
      signIn: jest.fn(() => Promise.resolve({ data: null, error: null }))
    }
  }
}))

// Mock the email service
jest.mock('../../services/emailService', () => ({
  subscribeToEmailList: jest.fn(() => Promise.resolve({ success: true })),
  sendWelcomeEmail: jest.fn(() => Promise.resolve({ success: true })),
  sendResultsEmail: jest.fn(() => Promise.resolve({ success: true }))
}))

describe('Complete Questionnaire Flow', () => {
  beforeEach(() => {
    setupTestEnvironment()
    jest.clearAllMocks()
  })

  afterEach(() => {
    cleanupTestEnvironment()
  })

  describe('Landing Page to Questionnaire Flow', () => {
    it('should navigate from landing page to questionnaire', async () => {
      render(<OptimizedLandingPage />)
      
      // Check landing page elements
      expect(screen.getByText(/Transform Your Financial Future/i)).toBeInTheDocument()
      expect(screen.getByText(/Start Your Free Assessment/i)).toBeInTheDocument()
      
      // Click start button
      const startButton = screen.getByText(/Start Your Free Assessment/i)
      await userEvent.click(startButton)
      
      // Should show questionnaire
      await waitFor(() => {
        expect(screen.getByText(/Question 1 of 10/i)).toBeInTheDocument()
      })
      
      // Analytics should be tracked
      expect(mockAnalytics.trackQuestionnaireStart).toHaveBeenCalled()
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('questionnaire_start')
    })

    it('should track landing page view analytics', () => {
      render(<OptimizedLandingPage />)
      
      expect(mockAnalytics.trackPageView).toHaveBeenCalledWith('Landing Page', '/')
      expect(mockAnalytics.trackLandingPageView).toHaveBeenCalled()
    })
  })

  describe('Questionnaire Completion Flow', () => {
    it('should complete full questionnaire with all questions', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Answer all questions
      for (let i = 0; i < questions.length; i++) {
        const question = questions[i]
        const questionText = screen.getByText(question.text)
        expect(questionText).toBeInTheDocument()
        
        // Select an answer
        const answerOption = screen.getByText(question.options[2]) // Middle option
        await userEvent.click(answerOption)
        
        // Wait for next question or completion
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
        
        // Analytics should be tracked
        expect(mockAnalytics.trackQuestionCompleted).toHaveBeenCalledWith(
          i + 1,
          question.text,
          question.options[2],
          expect.any(Number)
        )
      }
      
      // Should show email collection form
      await waitFor(() => {
        expect(screen.getByText(/Get Your Results/i)).toBeInTheDocument()
      })
    })

    it('should handle questionnaire abandonment', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Answer first few questions
      for (let i = 0; i < 3; i++) {
        const question = questions[i]
        const answerOption = screen.getByText(question.options[2])
        await userEvent.click(answerOption)
        
        if (i < 2) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Simulate page unload (abandonment)
      fireEvent.beforeunload(window)
      
      // Analytics should track abandonment
      expect(mockAnalytics.trackQuestionnaireAbandoned).toHaveBeenCalledWith(4, 'page_unload')
    })

    it('should save and restore progress', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      // Mock saved progress
      const savedProgress = {
        currentQuestion: 3,
        responses: {
          q1: 'Very confident',
          q2: 'Save for retirement'
        },
        startTime: Date.now()
      }
      
      localStorage.setItem('questionnaire_progress', JSON.stringify(savedProgress))
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Should show resume dialog
      await waitFor(() => {
        expect(screen.getByText(/Resume where you left off/i)).toBeInTheDocument()
      })
      
      // Click resume
      const resumeButton = screen.getByText(/Resume/i)
      await userEvent.click(resumeButton)
      
      // Should be on question 3
      await waitFor(() => {
        expect(screen.getByText(`Question 3 of ${questions.length}`)).toBeInTheDocument()
      })
    })
  })

  describe('Email Submission Flow', () => {
    it('should submit email and show results', async () => {
      const questions = generateMockQuestions()
      const responses = generateMockResponses(questions)
      const onComplete = jest.fn()
      
      // Mock completed questionnaire
      const mockResults = {
        score: 75,
        segment: 'stress-free',
        segmentDescription: 'You have a balanced approach to money management',
        recommendations: [
          'Set up automatic savings transfers',
          'Create a simple budget system',
          'Build an emergency fund'
        ],
        strengths: ['Good financial awareness', 'Consistent saving habits'],
        areasForImprovement: ['Emergency fund could be larger'],
        nextSteps: ['Set up automatic savings', 'Create monthly budget review']
      }
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete questionnaire (simplified)
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[2])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Fill email form
      await waitFor(() => {
        expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
      })
      
      const emailInput = screen.getByLabelText(/Email/i)
      const nameInput = screen.getByLabelText(/Name/i)
      const submitButton = screen.getByText(/Get Your Results/i)
      
      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.type(nameInput, 'Test User')
      await userEvent.click(submitButton)
      
      // Should show results
      await waitFor(() => {
        expect(screen.getByText(/Your Results/i)).toBeInTheDocument()
      })
      
      // Analytics should be tracked
      expect(mockAnalytics.trackEmailSubmitted).toHaveBeenCalledWith(
        'test@example.com',
        'stress-free',
        75
      )
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('email_submitted')
    })

    it('should validate email form', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete questionnaire quickly
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[2])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Try to submit without email
      await waitFor(() => {
        expect(screen.getByText(/Get Your Results/i)).toBeInTheDocument()
      })
      
      const submitButton = screen.getByText(/Get Your Results/i)
      await userEvent.click(submitButton)
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/Email is required/i)).toBeInTheDocument()
      })
      
      // Try invalid email
      const emailInput = screen.getByLabelText(/Email/i)
      await userEvent.type(emailInput, 'invalid-email')
      await userEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/Please enter a valid email/i)).toBeInTheDocument()
      })
    })
  })

  describe('Results Display Flow', () => {
    it('should display results correctly', async () => {
      const results = {
        score: 85,
        segment: 'stress-free',
        segmentDescription: 'You have excellent financial habits',
        recommendations: [
          'Continue your current savings strategy',
          'Consider increasing your investment portfolio',
          'Plan for long-term financial goals'
        ],
        strengths: [
          'Strong financial discipline',
          'Excellent saving habits',
          'Good risk management'
        ],
        areasForImprovement: [
          'Consider diversifying investments',
          'Plan for retirement more aggressively'
        ],
        nextSteps: [
          'Set up automatic investment contributions',
          'Schedule annual financial review',
          'Consider working with a financial advisor'
        ]
      }
      
      const onRestart = jest.fn()
      
      render(<AssessmentResults results={results} onRestart={onRestart} />)
      
      // Check results display
      expect(screen.getByText(/Your Results/i)).toBeInTheDocument()
      expect(screen.getByText(/85/i)).toBeInTheDocument() // Score
      expect(screen.getByText(/stress-free/i)).toBeInTheDocument()
      expect(screen.getByText(/You have excellent financial habits/i)).toBeInTheDocument()
      
      // Check recommendations
      results.recommendations.forEach(rec => {
        expect(screen.getByText(rec)).toBeInTheDocument()
      })
      
      // Check strengths
      results.strengths.forEach(strength => {
        expect(screen.getByText(strength)).toBeInTheDocument()
      })
      
      // Analytics should be tracked
      expect(mockAnalytics.trackResultsViewed).toHaveBeenCalledWith('stress-free', 85)
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('results_viewed')
    })

    it('should handle CTA clicks', async () => {
      const results = {
        score: 75,
        segment: 'balanced',
        segmentDescription: 'You have a balanced approach',
        recommendations: ['Test recommendation'],
        strengths: ['Test strength'],
        areasForImprovement: ['Test improvement'],
        nextSteps: ['Test next step']
      }
      
      const onRestart = jest.fn()
      
      render(<AssessmentResults results={results} onRestart={onRestart} />)
      
      // Click CTA button
      const ctaButton = screen.getByText(/Get Your Personalized Plan/i)
      await userEvent.click(ctaButton)
      
      // Analytics should be tracked
      expect(mockAnalytics.trackCTAClick).toHaveBeenCalledWith(
        'primary',
        'Get Your Personalized Plan',
        '/checkout'
      )
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('cta_clicked')
    })

    it('should handle restart functionality', async () => {
      const results = {
        score: 60,
        segment: 'balanced',
        segmentDescription: 'You have a balanced approach',
        recommendations: ['Test recommendation'],
        strengths: ['Test strength'],
        areasForImprovement: ['Test improvement'],
        nextSteps: ['Test next step']
      }
      
      const onRestart = jest.fn()
      
      render(<AssessmentResults results={results} onRestart={onRestart} />)
      
      // Click restart button
      const restartButton = screen.getByText(/Take Assessment Again/i)
      await userEvent.click(restartButton)
      
      expect(onRestart).toHaveBeenCalled()
    })
  })

  describe('Analytics Integration', () => {
    it('should track all funnel stages', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Track questionnaire start
      expect(mockAnalytics.trackQuestionnaireStart).toHaveBeenCalled()
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('questionnaire_start')
      
      // Answer questions
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[2])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Submit email
      await waitFor(() => {
        expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
      })
      
      const emailInput = screen.getByLabelText(/Email/i)
      const nameInput = screen.getByLabelText(/Name/i)
      const submitButton = screen.getByText(/Get Your Results/i)
      
      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.type(nameInput, 'Test User')
      await userEvent.click(submitButton)
      
      // Track email submission
      expect(mockAnalytics.trackEmailSubmitted).toHaveBeenCalled()
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('email_submitted')
      
      // Track results view
      await waitFor(() => {
        expect(screen.getByText(/Your Results/i)).toBeInTheDocument()
      })
      
      expect(mockAnalytics.trackResultsViewed).toHaveBeenCalled()
      expect(mockAnalytics.trackFunnelStage).toHaveBeenCalledWith('results_viewed')
    })

    it('should track user behavior', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Simulate user interactions
      const questionText = screen.getByText(questions[0].text)
      await userEvent.hover(questionText)
      
      // Wait for behavior tracking
      await waitFor(() => {
        expect(mockAnalytics.trackUserBehavior).toHaveBeenCalled()
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // Mock network error
      global.fetch = jest.fn(() => Promise.reject(new Error('Network error')))
      
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete questionnaire
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[2])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Submit email
      await waitFor(() => {
        expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
      })
      
      const emailInput = screen.getByLabelText(/Email/i)
      const nameInput = screen.getByLabelText(/Name/i)
      const submitButton = screen.getByText(/Get Your Results/i)
      
      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.type(nameInput, 'Test User')
      await userEvent.click(submitButton)
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument()
      })
    })

    it('should handle validation errors', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete questionnaire
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[2])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Try to submit with invalid data
      await waitFor(() => {
        expect(screen.getByText(/Get Your Results/i)).toBeInTheDocument()
      })
      
      const submitButton = screen.getByText(/Get Your Results/i)
      await userEvent.click(submitButton)
      
      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/Email is required/i)).toBeInTheDocument()
        expect(screen.getByText(/Name is required/i)).toBeInTheDocument()
      })
    })
  })

  describe('Performance Testing', () => {
    it('should render questionnaire quickly', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      const startTime = performance.now()
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      const endTime = performance.now()
      
      expect(endTime - startTime).toBeLessThan(100) // Should render in under 100ms
    })

    it('should handle large question sets efficiently', async () => {
      const largeQuestions = generateMockQuestions(50)
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={largeQuestions} />)
      
      // Should render without performance issues
      expect(screen.getByText(largeQuestions[0].text)).toBeInTheDocument()
    })
  })
}) 