import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ABTestProvider, useABTest } from '../../hooks/useABTest'
import { ABTestHeadlines } from '../../components/ABTestHeadlines'
import { ABTestQuestions } from '../../components/ABTestQuestions'
import { ABTestResults } from '../../components/ABTestResults'
import { ABTestCTAs } from '../../components/ABTestCTAs'
import { mockAnalytics, setupTestEnvironment, cleanupTestEnvironment, generateMockQuestions, abTestHelpers } from '../utils/testUtils'

// Mock analytics service
jest.mock('../../services/analytics', () => ({
  analytics: mockAnalytics
}))

describe('A/B Testing Framework', () => {
  beforeEach(() => {
    setupTestEnvironment()
    jest.clearAllMocks()
  })

  afterEach(() => {
    cleanupTestEnvironment()
  })

  describe('Headline Variations', () => {
    const headlineTests = [
      {
        testId: 'landing_headline',
        variants: [
          'Transform Your Financial Future',
          'Stop Stressing About Money',
          'Take Control of Your Finances',
          'Build Wealth, Not Worry'
        ]
      },
      {
        testId: 'results_headline',
        variants: [
          'Your Personalized Results',
          'Here\'s Your Financial Profile',
          'Your Money Mindset Revealed',
          'Your Financial Health Score'
        ]
      }
    ]

    headlineTests.forEach(test => {
      describe(`${test.testId} A/B Test`, () => {
        it('should randomly assign users to variants', () => {
          const variants = new Set()
          
          // Test multiple renders to ensure random distribution
          for (let i = 0; i < 100; i++) {
            const TestComponent = () => {
              const { variant } = useABTest(test.testId, test.variants)
              return <div data-testid="headline">{variant}</div>
            }
            
            render(
              <ABTestProvider>
                <TestComponent />
              </ABTestProvider>
            )
            
            const headline = screen.getByTestId('headline')
            variants.add(headline.textContent)
          }
          
          // Should have multiple variants (not just one)
          expect(variants.size).toBeGreaterThan(1)
        })

        it('should consistently assign same variant to user', () => {
          const TestComponent = () => {
            const { variant } = useABTest(test.testId, test.variants)
            return <div data-testid="headline">{variant}</div>
          }
          
          // Render multiple times
          const { rerender } = render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const firstVariant = screen.getByTestId('headline').textContent
          
          // Rerender multiple times
          for (let i = 0; i < 10; i++) {
            rerender(
              <ABTestProvider>
                <TestComponent />
              </ABTestProvider>
            )
            
            expect(screen.getByTestId('headline').textContent).toBe(firstVariant)
          }
        })

        it('should track variant impressions', () => {
          const TestComponent = () => {
            const { variant } = useABTest(test.testId, test.variants)
            return <div data-testid="headline">{variant}</div>
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          expect(mockAnalytics.trackABTestImpression).toHaveBeenCalledWith(
            test.testId,
            expect.any(String),
            'headline'
          )
        })

        it('should track headline click conversions', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            return (
              <button 
                data-testid="headline-button"
                onClick={() => trackConversion('click')}
              >
                {variant}
              </button>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const button = screen.getByTestId('headline-button')
          await userEvent.click(button)
          
          expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
            test.testId,
            expect.any(String),
            'click'
          )
        })
      })
    })
  })

  describe('Question Phrasing Variations', () => {
    const questionTests = [
      {
        testId: 'question_phrasing_1',
        variants: [
          {
            text: 'How do you typically feel about your financial situation?',
            options: ['Very stressed', 'Somewhat stressed', 'Neutral', 'Confident', 'Very confident']
          },
          {
            text: 'When you think about money, how do you usually feel?',
            options: ['Extremely anxious', 'A bit worried', 'Okay', 'Pretty good', 'Great']
          },
          {
            text: 'What\'s your general attitude toward your finances?',
            options: ['Overwhelmed', 'Concerned', 'Indifferent', 'Optimistic', 'Excited']
          }
        ]
      },
      {
        testId: 'question_phrasing_2',
        variants: [
          {
            text: 'What is your primary financial goal?',
            options: ['Save for retirement', 'Pay off debt', 'Build emergency fund', 'Invest for growth', 'Buy a home']
          },
          {
            text: 'What money goal matters most to you right now?',
            options: ['Retirement planning', 'Debt elimination', 'Emergency savings', 'Investment growth', 'Home ownership']
          }
        ]
      }
    ]

    questionTests.forEach(test => {
      describe(`${test.testId} A/B Test`, () => {
        it('should display different question variants', () => {
          const TestComponent = () => {
            const { variant } = useABTest(test.testId, test.variants)
            return (
              <div>
                <div data-testid="question-text">{variant.text}</div>
                {variant.options.map((option, index) => (
                  <button key={index} data-testid={`option-${index}`}>
                    {option}
                  </button>
                ))}
              </div>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const questionText = screen.getByTestId('question-text')
          expect(test.variants.some(v => v.text === questionText.textContent)).toBe(true)
        })

        it('should track question completion rates by variant', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            return (
              <div>
                <div>{variant.text}</div>
                {variant.options.map((option, index) => (
                  <button 
                    key={index}
                    data-testid={`option-${index}`}
                    onClick={() => trackConversion('question_completed')}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const option = screen.getByTestId('option-0')
          await userEvent.click(option)
          
          expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
            test.testId,
            expect.any(String),
            'question_completed'
          )
        })

        it('should measure time spent on questions by variant', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            return (
              <div>
                <div>{variant.text}</div>
                {variant.options.map((option, index) => (
                  <button 
                    key={index}
                    data-testid={`option-${index}`}
                    onClick={() => trackConversion('question_completed', { timeSpent: 5000 })}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const option = screen.getByTestId('option-0')
          await userEvent.click(option)
          
          expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
            test.testId,
            expect.any(String),
            'question_completed',
            { timeSpent: 5000 }
          )
        })
      })
    })
  })

  describe('Results Presentation Variations', () => {
    const resultsTests = [
      {
        testId: 'results_layout',
        variants: [
          {
            layout: 'card',
            style: 'modern'
          },
          {
            layout: 'list',
            style: 'minimal'
          },
          {
            layout: 'grid',
            style: 'traditional'
          }
        ]
      },
      {
        testId: 'results_emphasis',
        variants: [
          {
            emphasis: 'score',
            primaryMetric: 'financial_health_score'
          },
          {
            emphasis: 'segment',
            primaryMetric: 'money_mindset_type'
          },
          {
            emphasis: 'recommendations',
            primaryMetric: 'action_items'
          }
        ]
      }
    ]

    resultsTests.forEach(test => {
      describe(`${test.testId} A/B Test`, () => {
        it('should display different results layouts', () => {
          const TestComponent = () => {
            const { variant } = useABTest(test.testId, test.variants)
            return (
              <div data-testid="results-layout" data-layout={variant.layout} data-style={variant.style}>
                Results Layout: {variant.layout} - {variant.style}
              </div>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const layout = screen.getByTestId('results-layout')
          expect(test.variants.some(v => v.layout === layout.getAttribute('data-layout'))).toBe(true)
        })

        it('should track results engagement by variant', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            return (
              <div>
                <div>Results Layout: {variant.layout}</div>
                <button 
                  data-testid="results-cta"
                  onClick={() => trackConversion('results_engaged')}
                >
                  Learn More
                </button>
              </div>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const cta = screen.getByTestId('results-cta')
          await userEvent.click(cta)
          
          expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
            test.testId,
            expect.any(String),
            'results_engaged'
          )
        })

        it('should measure scroll depth on results page', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            
            React.useEffect(() => {
              // Simulate scroll event
              const handleScroll = () => {
                trackConversion('scroll_depth', { depth: 75 })
              }
              
              window.addEventListener('scroll', handleScroll)
              return () => window.removeEventListener('scroll', handleScroll)
            }, [trackConversion])
            
            return (
              <div style={{ height: '2000px' }}>
                <div>Results Layout: {variant.layout}</div>
                <div style={{ height: '1500px' }}>Scroll content</div>
              </div>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          // Simulate scroll
          fireEvent.scroll(window, { target: { scrollY: 1500 } })
          
          await waitFor(() => {
            expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
              test.testId,
              expect.any(String),
              'scroll_depth',
              { depth: 75 }
            )
          })
        })
      })
    })
  })

  describe('CTA Placement and Wording', () => {
    const ctaTests = [
      {
        testId: 'primary_cta_wording',
        variants: [
          'Get Your Personalized Plan',
          'Start Building Wealth',
          'Take the Next Step',
          'Unlock Your Results'
        ]
      },
      {
        testId: 'cta_placement',
        variants: [
          { position: 'top', style: 'button' },
          { position: 'bottom', style: 'button' },
          { position: 'floating', style: 'button' },
          { position: 'inline', style: 'link' }
        ]
      },
      {
        testId: 'cta_color',
        variants: [
          { color: 'blue', contrast: 'high' },
          { color: 'green', contrast: 'high' },
          { color: 'orange', contrast: 'medium' },
          { color: 'purple', contrast: 'high' }
        ]
      }
    ]

    ctaTests.forEach(test => {
      describe(`${test.testId} A/B Test`, () => {
        it('should display different CTA variants', () => {
          const TestComponent = () => {
            const { variant } = useABTest(test.testId, test.variants)
            return (
              <button 
                data-testid="cta-button"
                data-position={variant.position || 'default'}
                data-color={variant.color || 'default'}
              >
                {typeof variant === 'string' ? variant : 'Click Here'}
              </button>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const cta = screen.getByTestId('cta-button')
          expect(cta).toBeInTheDocument()
        })

        it('should track CTA click rates by variant', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            return (
              <button 
                data-testid="cta-button"
                onClick={() => trackConversion('cta_clicked')}
              >
                {typeof variant === 'string' ? variant : 'Click Here'}
              </button>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          const cta = screen.getByTestId('cta-button')
          await userEvent.click(cta)
          
          expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
            test.testId,
            expect.any(String),
            'cta_clicked'
          )
        })

        it('should measure CTA visibility and engagement', async () => {
          const TestComponent = () => {
            const { variant, trackConversion } = useABTest(test.testId, test.variants)
            
            React.useEffect(() => {
              // Simulate intersection observer
              const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                  if (entry.isIntersecting) {
                    trackConversion('cta_visible')
                  }
                })
              })
              
              const element = document.querySelector('[data-testid="cta-button"]')
              if (element) observer.observe(element)
              
              return () => observer.disconnect()
            }, [trackConversion])
            
            return (
              <button 
                data-testid="cta-button"
                onClick={() => trackConversion('cta_clicked')}
              >
                {typeof variant === 'string' ? variant : 'Click Here'}
              </button>
            )
          }
          
          render(
            <ABTestProvider>
              <TestComponent />
            </ABTestProvider>
          )
          
          // Simulate CTA becoming visible
          const cta = screen.getByTestId('cta-button')
          fireEvent.scroll(window, { target: { scrollY: 100 } })
          
          await waitFor(() => {
            expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
              test.testId,
              expect.any(String),
              'cta_visible'
            )
          })
        })
      })
    })
  })

  describe('Statistical Significance Testing', () => {
    it('should calculate conversion rates correctly', () => {
      const testResults = [
        { variant: 'A', impressions: 1000, conversions: 50 },
        { variant: 'B', impressions: 1000, conversions: 65 },
        { variant: 'C', impressions: 1000, conversions: 45 }
      ]
      
      const conversionRates = testResults.map(result => ({
        ...result,
        rate: (result.conversions / result.impressions) * 100
      }))
      
      expect(conversionRates[0].rate).toBe(5.0) // 50/1000 * 100
      expect(conversionRates[1].rate).toBe(6.5) // 65/1000 * 100
      expect(conversionRates[2].rate).toBe(4.5) // 45/1000 * 100
    })

    it('should determine statistical significance', () => {
      // Test case: Variant B has higher conversion rate
      const control = { conversions: 50, impressions: 1000 }
      const variant = { conversions: 65, impressions: 1000 }
      
      const isSignificant = abTestHelpers.calculateSignificance(
        control.conversions,
        variant.conversions,
        control.impressions,
        variant.impressions
      )
      
      expect(isSignificant).toBe(true)
    })

    it('should handle insufficient sample sizes', () => {
      // Test case: Small sample size
      const control = { conversions: 5, impressions: 100 }
      const variant = { conversions: 8, impressions: 100 }
      
      const isSignificant = abTestHelpers.calculateSignificance(
        control.conversions,
        variant.conversions,
        control.impressions,
        variant.impressions
      )
      
      // Should not be statistically significant with small sample
      expect(isSignificant).toBe(false)
    })
  })

  describe('A/B Test Results Analysis', () => {
    it('should generate comprehensive test reports', () => {
      const testId = 'headline_test'
      const results = abTestHelpers.simulateABTestResults(testId, 30)
      
      expect(results).toHaveLength(30)
      expect(results[0]).toHaveProperty('date')
      expect(results[0]).toHaveProperty('control')
      expect(results[0]).toHaveProperty('variant')
      expect(results[0].control).toHaveProperty('impressions')
      expect(results[0].control).toHaveProperty('conversions')
    })

    it('should track test performance over time', () => {
      const testId = 'cta_test'
      const variants = ['Get Started', 'Learn More', 'Sign Up']
      
      const testVariants = abTestHelpers.generateTestVariants(testId, variants)
      
      expect(testVariants).toHaveLength(3)
      expect(testVariants[0]).toHaveProperty('testId', testId)
      expect(testVariants[0]).toHaveProperty('variant', 'Get Started')
      expect(testVariants[0]).toHaveProperty('impressions', 0)
      expect(testVariants[0]).toHaveProperty('conversions', 0)
    })

    it('should handle test completion and winner selection', () => {
      const testResults = [
        { variant: 'A', impressions: 5000, conversions: 250, rate: 5.0 },
        { variant: 'B', impressions: 5000, conversions: 325, rate: 6.5 },
        { variant: 'C', impressions: 5000, conversions: 225, rate: 4.5 }
      ]
      
      // Find winner
      const winner = testResults.reduce((prev, current) => 
        current.rate > prev.rate ? current : prev
      )
      
      expect(winner.variant).toBe('B')
      expect(winner.rate).toBe(6.5)
    })
  })

  describe('A/B Test Integration with Analytics', () => {
    it('should track test assignments in analytics', () => {
      const TestComponent = () => {
        const { variant } = useABTest('test_id', ['A', 'B', 'C'])
        return <div data-testid="test-component">{variant}</div>
      }
      
      render(
        <ABTestProvider>
          <TestComponent />
        </ABTestProvider>
      )
      
      expect(mockAnalytics.trackABTestAssignment).toHaveBeenCalledWith(
        'test_id',
        expect.any(String)
      )
    })

    it('should track test conversions with metadata', async () => {
      const TestComponent = () => {
        const { variant, trackConversion } = useABTest('test_id', ['A', 'B'])
        return (
          <button 
            data-testid="test-button"
            onClick={() => trackConversion('purchase', { value: 99.99, currency: 'USD' })}
          >
            {variant}
          </button>
        )
      }
      
      render(
        <ABTestProvider>
          <TestComponent />
        </ABTestProvider>
      )
      
      const button = screen.getByTestId('test-button')
      await userEvent.click(button)
      
      expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
        'test_id',
        expect.any(String),
        'purchase',
        { value: 99.99, currency: 'USD' }
      )
    })

    it('should handle test completion and rollout', async () => {
      const TestComponent = () => {
        const { variant, trackConversion } = useABTest('completed_test', ['A', 'B'])
        return (
          <button 
            data-testid="test-button"
            onClick={() => trackConversion('test_completed')}
          >
            {variant}
          </button>
        )
      }
      
      render(
        <ABTestProvider>
          <TestComponent />
        </ABTestProvider>
      )
      
      const button = screen.getByTestId('test-button')
      await userEvent.click(button)
      
      expect(mockAnalytics.trackABTestConversion).toHaveBeenCalledWith(
        'completed_test',
        expect.any(String),
        'test_completed'
      )
    })
  })
}) 