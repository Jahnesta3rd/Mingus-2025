import React from 'react'
import { useABTesting } from '../hooks/useAnalytics'

// A/B Test Headlines Component
interface HeadlineTestProps {
  testId: string
  controlHeadline: string
  variantAHeadline: string
  variantBHeadline: string
  subheadline?: string
  className?: string
}

export const HeadlineTest: React.FC<HeadlineTestProps> = ({
  testId,
  controlHeadline,
  variantAHeadline,
  variantBHeadline,
  subheadline,
  className = ''
}) => {
  const { variant, trackConversion } = useABTesting(testId)

  const getHeadline = () => {
    switch (variant) {
      case 'variant_a':
        return variantAHeadline
      case 'variant_b':
        return variantBHeadline
      default:
        return controlHeadline
    }
  }

  const handleClick = () => {
    trackConversion('headline_click')
  }

  return (
    <div className={`headline-test ${className}`} onClick={handleClick}>
      <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
        {getHeadline()}
      </h1>
      {subheadline && (
        <p className="text-xl md:text-2xl text-gray-300 mb-8">
          {subheadline}
        </p>
      )}
      <div className="text-xs text-gray-400 opacity-50">
        Test: {testId} | Variant: {variant}
      </div>
    </div>
  )
}

// A/B Test Question Order Component
interface QuestionOrderTestProps {
  testId: string
  questions: Array<{
    id: string
    text: string
    options?: string[]
    type: string
  }>
  onQuestionComplete: (questionId: string, response: string) => void
  currentQuestion: number
}

export const QuestionOrderTest: React.FC<QuestionOrderTestProps> = ({
  testId,
  questions,
  onQuestionComplete,
  currentQuestion
}) => {
  const { variant, trackConversion } = useABTesting(testId)

  const getQuestionOrder = () => {
    switch (variant) {
      case 'reversed':
        return [...questions].reverse()
      case 'random':
        // Use consistent random order based on session
        const shuffled = [...questions]
        for (let i = shuffled.length - 1; i > 0; i--) {
          const j = Math.floor((Math.random() * (i + 1)) * 100) % (i + 1)
          ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
        }
        return shuffled
      default:
        return questions
    }
  }

  const orderedQuestions = getQuestionOrder()
  const currentQuestionData = orderedQuestions[currentQuestion - 1]

  const handleQuestionComplete = (response: string) => {
    trackConversion('question_completed')
    onQuestionComplete(currentQuestionData.id, response)
  }

  if (!currentQuestionData) {
    return <div>Question not found</div>
  }

  return (
    <div className="question-order-test">
      <div className="mb-4 text-sm text-gray-400">
        Question {currentQuestion} of {orderedQuestions.length}
        <span className="ml-2 opacity-50">| Test: {testId} | Variant: {variant}</span>
      </div>
      
      <div className="question-container">
        <h3 className="text-xl font-semibold mb-4">
          {currentQuestionData.text}
        </h3>
        
        {currentQuestionData.type === 'multiple_choice' && currentQuestionData.options && (
          <div className="options-container">
            {currentQuestionData.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleQuestionComplete(option)}
                className="option-button w-full p-4 mb-3 text-left bg-white bg-opacity-10 hover:bg-opacity-20 rounded-lg transition-all"
              >
                {option}
              </button>
            ))}
          </div>
        )}
        
        {currentQuestionData.type === 'scale' && (
          <div className="scale-container">
            <div className="flex justify-between mb-2">
              <span>Strongly Disagree</span>
              <span>Strongly Agree</span>
            </div>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  onClick={() => handleQuestionComplete(value.toString())}
                  className="scale-button flex-1 p-3 bg-white bg-opacity-10 hover:bg-opacity-20 rounded-lg transition-all"
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// A/B Test Results Page Layout Component
interface ResultsLayoutTestProps {
  testId: string
  segment: string
  score: number
  recommendations: string[]
  ctaText: string
  onCTAClick: () => void
}

export const ResultsLayoutTest: React.FC<ResultsLayoutTestProps> = ({
  testId,
  segment,
  score,
  recommendations,
  ctaText,
  onCTAClick
}) => {
  const { variant, trackConversion } = useABTesting(testId)

  const handleCTAClick = () => {
    trackConversion('results_cta_click')
    onCTAClick()
  }

  const renderLayout = () => {
    switch (variant) {
      case 'variant_a':
        return (
          <div className="results-layout-a">
            <div className="text-center mb-8">
              <div className="score-circle mx-auto w-32 h-32 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-3xl font-bold mb-4">
                {score}/100
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                You're a {segment}
              </h2>
              <p className="text-gray-300">
                Based on your responses, here's your personalized financial profile
              </p>
            </div>
            
            <div className="recommendations-section mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">
                Your Recommendations
              </h3>
              <ul className="space-y-3">
                {recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-green-400 mr-3">✓</span>
                    <span className="text-gray-300">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <button
              onClick={handleCTAClick}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-4 px-6 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              {ctaText}
            </button>
          </div>
        )
      
      case 'variant_b':
        return (
          <div className="results-layout-b">
            <div className="bg-white bg-opacity-10 rounded-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-white">
                  Financial Profile: {segment}
                </h2>
                <div className="score-badge bg-green-500 text-white px-4 py-2 rounded-full font-bold">
                  {score}/100
                </div>
              </div>
              <p className="text-gray-300">
                Your personalized financial strategy is ready
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-white bg-opacity-5 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-3">
                  Key Insights
                </h3>
                <p className="text-gray-300 text-sm">
                  Based on your responses, we've identified your financial personality and created a custom action plan.
                </p>
              </div>
              
              <div className="bg-white bg-opacity-5 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-3">
                  Next Steps
                </h3>
                <ul className="text-gray-300 text-sm space-y-1">
                  {recommendations.slice(0, 3).map((rec, index) => (
                    <li key={index}>• {rec}</li>
                  ))}
                </ul>
              </div>
            </div>
            
            <button
              onClick={handleCTAClick}
              className="w-full bg-white text-gray-900 py-4 px-6 rounded-lg font-semibold hover:bg-gray-100 transition-all"
            >
              {ctaText}
            </button>
          </div>
        )
      
      default:
        return (
          <div className="results-layout-control">
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-white mb-2">
                Your Results
              </h2>
              <p className="text-gray-300 mb-4">
                Financial Profile: {segment}
              </p>
              <div className="score-display inline-block bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-lg font-bold text-xl">
                Score: {score}/100
              </div>
            </div>
            
            <div className="recommendations-list mb-6">
              <h3 className="text-xl font-semibold text-white mb-4">
                Personalized Recommendations
              </h3>
              <div className="space-y-3">
                {recommendations.map((rec, index) => (
                  <div key={index} className="bg-white bg-opacity-10 rounded-lg p-4">
                    <p className="text-gray-300">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
            
            <button
              onClick={handleCTAClick}
              className="w-full bg-blue-600 text-white py-4 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-all"
            >
              {ctaText}
            </button>
          </div>
        )
    }
  }

  return (
    <div className="results-layout-test">
      {renderLayout()}
      <div className="mt-4 text-xs text-gray-400 opacity-50 text-center">
        Test: {testId} | Variant: {variant}
      </div>
    </div>
  )
}

// A/B Test CTA Button Component
interface CTAButtonTestProps {
  testId: string
  controlText: string
  urgentText: string
  benefitText: string
  onClick: () => void
  className?: string
}

export const CTAButtonTest: React.FC<CTAButtonTestProps> = ({
  testId,
  controlText,
  urgentText,
  benefitText,
  onClick,
  className = ''
}) => {
  const { variant, trackConversion } = useABTesting(testId)

  const getButtonConfig = () => {
    switch (variant) {
      case 'urgent':
        return {
          text: urgentText,
          className: 'bg-red-600 hover:bg-red-700 text-white'
        }
      case 'benefit':
        return {
          text: benefitText,
          className: 'bg-green-600 hover:bg-green-700 text-white'
        }
      default:
        return {
          text: controlText,
          className: 'bg-blue-600 hover:bg-blue-700 text-white'
        }
    }
  }

  const buttonConfig = getButtonConfig()

  const handleClick = () => {
    trackConversion('cta_button_click')
    onClick()
  }

  return (
    <button
      onClick={handleClick}
      className={`cta-button-test w-full py-4 px-6 rounded-lg font-semibold transition-all ${buttonConfig.className} ${className}`}
    >
      {buttonConfig.text}
    </button>
  )
}

// A/B Test Wrapper Component
interface ABTestWrapperProps {
  testId: string
  children: React.ReactNode
  fallback?: React.ReactNode
}

export const ABTestWrapper: React.FC<ABTestWrapperProps> = ({
  testId,
  children,
  fallback
}) => {
  const { variant } = useABTesting(testId)

  // If no variant is assigned, show fallback or nothing
  if (!variant || variant === 'control') {
    return fallback ? <>{fallback}</> : <>{children}</>
  }

  return <>{children}</>
}

// A/B Test Analytics Component
interface ABTestAnalyticsProps {
  testId: string
  showDebug?: boolean
}

export const ABTestAnalytics: React.FC<ABTestAnalyticsProps> = ({
  testId,
  showDebug = false
}) => {
  const { variant, trackConversion } = useABTesting(testId)

  if (!showDebug) {
    return null
  }

  return (
    <div className="ab-test-analytics fixed bottom-4 right-4 bg-black bg-opacity-80 text-white p-4 rounded-lg text-xs">
      <div className="font-bold mb-2">A/B Test Debug</div>
      <div>Test ID: {testId}</div>
      <div>Variant: {variant}</div>
      <button
        onClick={() => trackConversion('debug_click')}
        className="mt-2 bg-blue-600 px-2 py-1 rounded text-xs"
      >
        Test Conversion
      </button>
    </div>
  )
}

// A/B Test Results Component
interface ABTestResultsProps {
  testId: string
  results: {
    control: { conversions: number; impressions: number }
    variant_a: { conversions: number; impressions: number }
    variant_b: { conversions: number; impressions: number }
  }
}

export const ABTestResults: React.FC<ABTestResultsProps> = ({
  testId,
  results
}) => {
  const calculateConversionRate = (conversions: number, impressions: number) => {
    return impressions > 0 ? (conversions / impressions * 100).toFixed(2) : '0.00'
  }

  const getWinner = () => {
    const rates = {
      control: parseFloat(calculateConversionRate(results.control.conversions, results.control.impressions)),
      variant_a: parseFloat(calculateConversionRate(results.variant_a.conversions, results.variant_a.impressions)),
      variant_b: parseFloat(calculateConversionRate(results.variant_b.conversions, results.variant_b.impressions))
    }

    const maxRate = Math.max(rates.control, rates.variant_a, rates.variant_b)
    return Object.keys(rates).find(key => rates[key as keyof typeof rates] === maxRate)
  }

  const winner = getWinner()

  return (
    <div className="ab-test-results bg-white rounded-lg p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-4">A/B Test Results: {testId}</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(results).map(([variant, data]) => (
          <div
            key={variant}
            className={`p-4 rounded-lg border-2 ${
              variant === winner ? 'border-green-500 bg-green-50' : 'border-gray-200'
            }`}
          >
            <div className="font-semibold text-lg mb-2 capitalize">
              {variant.replace('_', ' ')}
              {variant === winner && <span className="ml-2 text-green-600">🏆</span>}
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {calculateConversionRate(data.conversions, data.impressions)}%
            </div>
            <div className="text-sm text-gray-600">
              {data.conversions} / {data.impressions} conversions
            </div>
          </div>
        ))}
      </div>
      
      {winner && (
        <div className="mt-4 p-3 bg-green-100 rounded-lg">
          <div className="font-semibold text-green-800">
            Winner: {winner.replace('_', ' ').toUpperCase()}
          </div>
          <div className="text-sm text-green-600">
            Highest conversion rate: {calculateConversionRate(
              results[winner as keyof typeof results].conversions,
              results[winner as keyof typeof results].impressions
            )}%
          </div>
        </div>
      )}
    </div>
  )
} 