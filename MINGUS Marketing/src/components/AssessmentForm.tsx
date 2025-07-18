import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight, CheckCircle } from 'lucide-react'
import { ASSESSMENT_QUESTIONS } from '../types/assessment-types'

interface AssessmentFormProps {
  onCompleted: (data: any) => void
}

export const AssessmentForm: React.FC<AssessmentFormProps> = ({ onCompleted }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const currentQuestion = ASSESSMENT_QUESTIONS[currentQuestionIndex]
  const progress = ((currentQuestionIndex + 1) / ASSESSMENT_QUESTIONS.length) * 100
  // Auto-save answers to localStorage
  useEffect(() => {
    localStorage.setItem('assessment_answers', JSON.stringify(answers))
  }, [answers])

  // Load saved answers on component mount
  useEffect(() => {
    const savedAnswers = localStorage.getItem('assessment_answers')
    if (savedAnswers) {
      setAnswers(JSON.parse(savedAnswers))
    }
  }, [])

  const validateCurrentQuestion = () => {
    if (!currentQuestion.required) return true
    
    const answer = answers[currentQuestion.id]
    if (!answer || (Array.isArray(answer) && answer.length === 0)) {
      setValidationErrors(prev => ({
        ...prev,
        [currentQuestion.id]: 'This question is required'
      }))
      return false
    }
    
    setValidationErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[currentQuestion.id]
      return newErrors
    })
    return true
  }

  const handleAnswerChange = (questionId: string, value: any) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }))
  }

  const handleNext = () => {
    if (!validateCurrentQuestion()) return
    
    if (currentQuestionIndex < ASSESSMENT_QUESTIONS.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    } else {
      handleSubmit()
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    
    try {
      // Calculate total score
      let totalScore = 0
      const answersWithPoints: Record<string, any> = {}
      
      ASSESSMENT_QUESTIONS.forEach(question => {
        const answer = answers[question.id]
        if (answer) {
          if (question.type === 'checkbox' && Array.isArray(answer)) {
            // For checkboxes, sum up points for all selected options
            const points = answer.reduce((sum: number, selectedValue: string) => {
              const option = question.options?.find(opt => opt.value === selectedValue)
              return sum + (option?.points || 0)
            }, 0)
            totalScore += points
            answersWithPoints[question.id] = { answer, points }
          } else if (question.type === 'rating') {
            // For ratings, calculate average score
            const ratingValues = Object.values(answer).filter((rating): rating is number => typeof rating === 'number')
            const ratingSum = ratingValues.reduce((sum: number, rating: number) => sum + rating, 0)
            const ratingCount = ratingValues.length
            const averageRating = ratingCount > 0 ? ratingSum / ratingCount : 0
            const points = Math.round(averageRating * 2) // Convert to 0-10 points
            totalScore += points
            answersWithPoints[question.id] = { answer, points }
          } else {
            // For radio buttons and other types
            const option = question.options?.find(opt => opt.value === answer)
            const points = option?.points || 0
            totalScore += points
            answersWithPoints[question.id] = { answer, points }
          }
        }
      })

      // Determine user segment based on score
      let segment = 'stress-free'
      if (totalScore > 16 && totalScore <= 30) {
        segment = 'relationship-spender'
      } else if (totalScore > 30 && totalScore <= 45) {
        segment = 'emotional-manager'
      } else if (totalScore > 45) {
        segment = 'crisis-mode'
      }

      const resultData = {
        email: localStorage.getItem('user_email'),
        answers: answersWithPoints,
        totalScore,
        segment,
        timestamp: new Date().toISOString()
      }

      // Save to database (this would be a Supabase call)
      await saveAssessmentResults(resultData)
      
      // Clear localStorage
      localStorage.removeItem('assessment_answers')
      localStorage.removeItem('user_email')
      onCompleted(resultData)
    } catch (error) {
      console.error('Error submitting assessment:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const saveAssessmentResults = async (data: any) => {
    // This would be a Supabase call
    console.log('Saving assessment results:', data)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
  }

  const renderQuestion = () => {
    const answer = answers[currentQuestion.id]
    const error = validationErrors[currentQuestion.id]

    switch (currentQuestion.type) {
      case 'radio':
        return (
          <div className="space-y-3">
            {currentQuestion.options?.map((option) => (
              <label
                key={option.value}
                className={`flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  answer === option.value
                    ? 'border-red-500 text-white'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <input
                  type="radio"
                  name={currentQuestion.id}
                  value={option.value}
                  checked={answer === option.value}
                  onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                  className="mr-3"
                />
                <span className="text-white">{option.label}</span>
              </label>
            ))}
          </div>
        )

      case 'checkbox':
        return (
          <div className="space-y-3">
            {currentQuestion.options?.map((option) => (
              <label
                key={option.value}
                className={`flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  Array.isArray(answer) && answer.includes(option.value)
                    ? 'border-red-500 text-white'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <input
                  type="checkbox"
                  value={option.value}
                  checked={Array.isArray(answer) && answer.includes(option.value)}
                  onChange={(e) => {
                    const currentAnswers = Array.isArray(answer) ? answer : []
                    const newAnswers = e.target.checked
                      ? [...currentAnswers, option.value]
                      : currentAnswers.filter((a: string) => a !== option.value)
                    handleAnswerChange(currentQuestion.id, newAnswers)
                  }}
                  className="mr-3"
                />
                <span className="text-white">{option.label}</span>
              </label>
            ))}
          </div>
        )

      case 'rating':
        return (
          <div className="space-y-4">
            {currentQuestion.options?.map((option) => (
              <div key={option.value} className="space-y-2">
                <label className="text-white font-medium">{option.label}</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      type="button"
                      onClick={() => {
                        const currentRatings = answer || {}
                        handleAnswerChange(currentQuestion.id, {
                          ...currentRatings,
                          [option.value]: rating
                        })
                      }}
                      className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                        answer?.[option.value] === rating
                          ? 'bg-red-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {rating}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )

      default:
        return (
          <input
            type="text"
            value={answer || ''}
            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
            className="w-full px-4 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
            placeholder="Enter your answer..."
          />
        )
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-400">Question {currentQuestionIndex + 1}/{ASSESSMENT_QUESTIONS.length}</span>
          <span className="text-sm text-gray-400">{(progress).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestionIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="bg-gray-800 rounded-xl p-6 border border-gray-700"
        >
          <h2 className="text-xl font-semibold text-white mb-6">{currentQuestion.question}</h2>

          {renderQuestion()}

          {validationErrors[currentQuestion.id] && (
            <p className="text-red-400 text-sm">{validationErrors[currentQuestion.id]}</p>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-8">
        <button
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
          className="flex items-center px-4 py-2 text-gray-400 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-5 h-5 mr-1" />
          Previous
        </button>

        <button
          onClick={handleNext}
          disabled={isSubmitting}
          className="flex items-center px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-20 hover:scale-105"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Processing...
            </>
          ) : currentQuestionIndex === ASSESSMENT_QUESTIONS.length -1 ? (
            <>
              Get Results
              <CheckCircle className="w-5 h-5 ml-2" />
            </>
          ) : (
            <>
              Next
              <ChevronRight className="w-5 h-5 ml-1" />
            </>
          )}
        </button>
      </div>
    </div>
  )
} 