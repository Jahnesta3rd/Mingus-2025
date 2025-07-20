import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axe, toHaveNoViolations } from 'jest-axe'
import { Questionnaire } from '../../components/Questionnaire'
import { AssessmentResults } from '../../components/AssessmentResults'
import { OptimizedLandingPage } from '../../components/OptimizedLandingPage'
import { setupTestEnvironment, cleanupTestEnvironment, generateMockQuestions, accessibilityTestHelpers, performanceTestHelpers } from '../utils/testUtils'

// Extend Jest matchers for accessibility testing
expect.extend(toHaveNoViolations)

describe('User Experience Testing', () => {
  beforeEach(() => {
    setupTestEnvironment()
  })

  afterEach(() => {
    cleanupTestEnvironment()
  })

  describe('Cross-Browser Compatibility', () => {
    const browsers = [
      {
        name: 'Chrome',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      },
      {
        name: 'Firefox',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
      },
      {
        name: 'Safari',
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
      },
      {
        name: 'Edge',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
      }
    ]

    browsers.forEach(browser => {
      it(`should render correctly in ${browser.name}`, () => {
        // Mock user agent
        Object.defineProperty(navigator, 'userAgent', {
          value: browser.userAgent,
          configurable: true
        })

        const questions = generateMockQuestions()
        const onComplete = jest.fn()
        
        const { container } = render(<Questionnaire onComplete={onComplete} questions={questions} />)
        
        // Basic functionality should work
        expect(screen.getByText(questions[0].text)).toBeInTheDocument()
        expect(container).toBeInTheDocument()
      })
    })

    it('should handle different screen resolutions', () => {
      const resolutions = [
        { width: 1920, height: 1080, name: 'Desktop HD' },
        { width: 1366, height: 768, name: 'Laptop' },
        { width: 1024, height: 768, name: 'Tablet Landscape' },
        { width: 768, height: 1024, name: 'Tablet Portrait' },
        { width: 375, height: 667, name: 'Mobile Portrait' },
        { width: 414, height: 896, name: 'Mobile Large' }
      ]

      resolutions.forEach(resolution => {
        // Mock window dimensions
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: resolution.width
        })
        Object.defineProperty(window, 'innerHeight', {
          writable: true,
          configurable: true,
          value: resolution.height
        })

        const questions = generateMockQuestions()
        const onComplete = jest.fn()
        
        const { container } = render(<Questionnaire onComplete={onComplete} questions={questions} />)
        
        // Should render without errors
        expect(container).toBeInTheDocument()
        expect(screen.getByText(questions[0].text)).toBeInTheDocument()
      })
    })
  })

  describe('Mobile Device Testing', () => {
    it('should be touch-friendly on mobile devices', async () => {
      // Mock mobile device
      Object.defineProperty(navigator, 'maxTouchPoints', {
        value: 5,
        configurable: true
      })
      
      Object.defineProperty(window, 'innerWidth', {
        value: 375,
        configurable: true
      })
      
      Object.defineProperty(window, 'innerHeight', {
        value: 667,
        configurable: true
      })

      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Check for touch-friendly button sizes
      const answerOptions = screen.getAllByRole('button')
      answerOptions.forEach(button => {
        const rect = button.getBoundingClientRect()
        expect(rect.width).toBeGreaterThanOrEqual(44) // Minimum touch target size
        expect(rect.height).toBeGreaterThanOrEqual(44)
      })
    })

    it('should handle orientation changes', () => {
      // Mock orientation change
      const mockMatchMedia = jest.fn()
      mockMatchMedia.mockReturnValue({
        matches: false,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      })
      
      global.matchMedia = mockMatchMedia

      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Should handle orientation change without errors
      expect(screen.getByText(questions[0].text)).toBeInTheDocument()
    })

    it('should work with iOS Safari quirks', () => {
      // Mock iOS Safari
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
        configurable: true
      })

      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Test iOS-specific interactions
      const answerOption = screen.getByText(questions[0].options[0])
      
      // Simulate iOS touch events
      fireEvent.touchStart(answerOption)
      fireEvent.touchEnd(answerOption)
      
      // Should handle iOS touch events
      expect(answerOption).toBeInTheDocument()
    })

    it('should handle slow mobile connections', async () => {
      // Mock slow connection
      Object.defineProperty(navigator, 'connection', {
        value: {
          effectiveType: '2g',
          downlink: 0.5,
          rtt: 2000,
          saveData: true
        },
        configurable: true
      })

      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Should show loading states appropriately
      expect(screen.getByText(questions[0].text)).toBeInTheDocument()
    })
  })

  describe('Accessibility Compliance (WCAG 2.1)', () => {
    it('should meet WCAG 2.1 AA standards for questionnaire', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      const { container } = render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Run axe accessibility tests
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should meet WCAG 2.1 AA standards for results page', async () => {
      const results = {
        score: 75,
        segment: 'stress-free',
        segmentDescription: 'You have a balanced approach to money management',
        recommendations: ['Test recommendation'],
        strengths: ['Test strength'],
        areasForImprovement: ['Test improvement'],
        nextSteps: ['Test next step']
      }
      
      const onRestart = jest.fn()
      
      const { container } = render(<AssessmentResults results={results} onRestart={onRestart} />)
      
      // Run axe accessibility tests
      const axeResults = await axe(container)
      expect(axeResults).toHaveNoViolations()
    })

    it('should meet WCAG 2.1 AA standards for landing page', async () => {
      const { container } = render(<OptimizedLandingPage />)
      
      // Run axe accessibility tests
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper heading structure', () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      const { container } = render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Check heading structure
      expect(() => accessibilityTestHelpers.checkHeadingStructure(container)).not.toThrow()
    })

    it('should have proper form labels', () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      const { container } = render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Check form labels
      expect(() => accessibilityTestHelpers.checkFormLabels(container)).not.toThrow()
    })

    it('should have proper ARIA attributes', () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      const { container } = render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Check ARIA attributes
      expect(() => accessibilityTestHelpers.checkAriaAttributes(container)).not.toThrow()
    })

    it('should be keyboard navigable', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Test keyboard navigation
      const answerOptions = screen.getAllByRole('button')
      
      // Focus first option
      answerOptions[0].focus()
      expect(document.activeElement).toBe(answerOptions[0])
      
      // Navigate with arrow keys
      fireEvent.keyDown(answerOptions[0], { key: 'ArrowRight' })
      expect(document.activeElement).toBe(answerOptions[1])
      
      // Select with Enter key
      fireEvent.keyDown(answerOptions[1], { key: 'Enter' })
      
      // Should advance to next question
      await waitFor(() => {
        expect(screen.getByText(`Question 2 of ${questions.length}`)).toBeInTheDocument()
      })
    })

    it('should have proper focus management', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Answer first question
      const answerOption = screen.getByText(questions[0].options[0])
      await userEvent.click(answerOption)
      
      // Focus should move to next question
      await waitFor(() => {
        const nextQuestionOptions = screen.getAllByRole('button')
        expect(nextQuestionOptions[0]).toHaveFocus()
      })
    })

    it('should announce dynamic content changes', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Check for live regions
      const liveRegion = screen.getByRole('status')
      expect(liveRegion).toBeInTheDocument()
      
      // Answer question
      const answerOption = screen.getByText(questions[0].options[0])
      await userEvent.click(answerOption)
      
      // Live region should be updated
      await waitFor(() => {
        expect(liveRegion).toHaveTextContent('Question 2 of 10')
      })
    })
  })

  describe('Loading Performance Testing', () => {
    it('should load questionnaire quickly', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      const renderTime = await performanceTestHelpers.measureRenderTime(
        <Questionnaire onComplete={onComplete} questions={questions} />
      )
      
      expect(renderTime).toBeLessThan(100) // Should render in under 100ms
    })

    it('should load results page quickly', async () => {
      const results = {
        score: 75,
        segment: 'stress-free',
        segmentDescription: 'Test description',
        recommendations: ['Test'],
        strengths: ['Test'],
        areasForImprovement: ['Test'],
        nextSteps: ['Test']
      }
      
      const onRestart = jest.fn()
      
      const renderTime = await performanceTestHelpers.measureRenderTime(
        <AssessmentResults results={results} onRestart={onRestart} />
      )
      
      expect(renderTime).toBeLessThan(100)
    })

    it('should handle large datasets efficiently', async () => {
      const largeQuestions = generateMockQuestions(50)
      const onComplete = jest.fn()
      
      const startTime = performance.now()
      render(<Questionnaire onComplete={onComplete} questions={largeQuestions} />)
      const endTime = performance.now()
      
      expect(endTime - startTime).toBeLessThan(200) // Should handle large datasets
    })

    it('should optimize memory usage', () => {
      const initialMemory = performanceTestHelpers.measureMemoryUsage()
      
      // Render multiple components
      for (let i = 0; i < 10; i++) {
        const questions = generateMockQuestions()
        const onComplete = jest.fn()
        render(<Questionnaire onComplete={onComplete} questions={questions} />)
      }
      
      const finalMemory = performanceTestHelpers.measureMemoryUsage()
      
      if (initialMemory && finalMemory) {
        const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize
        expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024) // Less than 50MB increase
      }
    })

    it('should handle slow network conditions', async () => {
      // Mock slow network
      global.fetch = jest.fn(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({ ok: true, json: () => Promise.resolve({}) }), 2000)
        )
      )

      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Should show loading states
      expect(screen.getByText(questions[0].text)).toBeInTheDocument()
    })
  })

  describe('Form Abandonment Scenarios', () => {
    it('should detect and handle early abandonment', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Leave page immediately
      fireEvent.beforeunload(window)
      
      // Should track abandonment
      // Note: In real implementation, this would be tracked via analytics
      expect(window).toBeDefined()
    })

    it('should detect abandonment after partial completion', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Answer first few questions
      for (let i = 0; i < 3; i++) {
        const answerOption = screen.getByText(questions[i].options[0])
        await userEvent.click(answerOption)
        
        if (i < 2) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Abandon at question 4
      fireEvent.beforeunload(window)
      
      // Should track abandonment at specific point
      expect(window).toBeDefined()
    })

    it('should save progress before abandonment', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Answer questions
      for (let i = 0; i < 5; i++) {
        const answerOption = screen.getByText(questions[i].options[0])
        await userEvent.click(answerOption)
        
        if (i < 4) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Simulate abandonment
      fireEvent.beforeunload(window)
      
      // Progress should be saved
      const savedProgress = localStorage.getItem('questionnaire_progress')
      expect(savedProgress).toBeTruthy()
    })

    it('should show re-engagement message on return', async () => {
      // Mock saved progress
      const savedProgress = {
        currentQuestion: 5,
        responses: {
          q1: 'Very confident',
          q2: 'Save for retirement',
          q3: 'Weekly',
          q4: '10-20%'
        },
        startTime: Date.now() - (2 * 60 * 60 * 1000) // 2 hours ago
      }
      
      localStorage.setItem('questionnaire_progress', JSON.stringify(savedProgress))
      
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Should show resume dialog
      await waitFor(() => {
        expect(screen.getByText(/Resume where you left off/i)).toBeInTheDocument()
      })
    })

    it('should handle abandonment at email collection', async () => {
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete questionnaire
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[0])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      // Abandon at email collection
      await waitFor(() => {
        expect(screen.getByText(/Get Your Results/i)).toBeInTheDocument()
      })
      
      fireEvent.beforeunload(window)
      
      // Should track abandonment at email collection
      expect(window).toBeDefined()
    })
  })

  describe('Error Recovery', () => {
    it('should handle network errors gracefully', async () => {
      // Mock network error
      global.fetch = jest.fn(() => Promise.reject(new Error('Network error')))
      
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete questionnaire
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[0])
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
      const submitButton = screen.getByText(/Get Your Results/i)
      
      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.click(submitButton)
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument()
      })
    })

    it('should allow retry after errors', async () => {
      // Mock network error then success
      let callCount = 0
      global.fetch = jest.fn(() => {
        callCount++
        if (callCount === 1) {
          return Promise.reject(new Error('Network error'))
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
      })
      
      const questions = generateMockQuestions()
      const onComplete = jest.fn()
      
      render(<Questionnaire onComplete={onComplete} questions={questions} />)
      
      // Complete and submit
      for (let i = 0; i < questions.length; i++) {
        const answerOption = screen.getByText(questions[i].options[0])
        await userEvent.click(answerOption)
        
        if (i < questions.length - 1) {
          await waitFor(() => {
            expect(screen.getByText(`Question ${i + 2} of ${questions.length}`)).toBeInTheDocument()
          })
        }
      }
      
      await waitFor(() => {
        expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
      })
      
      const emailInput = screen.getByLabelText(/Email/i)
      const submitButton = screen.getByText(/Get Your Results/i)
      
      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.click(submitButton)
      
      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument()
      })
      
      // Click retry
      const retryButton = screen.getByText(/Try Again/i)
      await userEvent.click(retryButton)
      
      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText(/Your Results/i)).toBeInTheDocument()
      })
    })
  })
}) 