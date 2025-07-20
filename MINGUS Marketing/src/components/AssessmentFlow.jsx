// AssessmentFlow.jsx - Example component showing how to use Supabase functions

import React, { useState, useEffect } from 'react'
import { 
  createLead, 
  getAssessmentQuestions, 
  submitAssessmentResponse, 
  completeAssessment,
  confirmEmail 
} from '../lib/supabase.js'

const AssessmentFlow = () => {
  const [email, setEmail] = useState('')
  const [questions, setQuestions] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [responses, setResponses] = useState({})
  const [totalScore, setTotalScore] = useState(0)
  const [leadId, setLeadId] = useState(null)
  const [step, setStep] = useState('email') // email, assessment, results
  const [loading, setLoading] = useState(false)

  // Load assessment questions on component mount
  useEffect(() => {
    loadQuestions()
  }, [])

  const loadQuestions = async () => {
    const result = await getAssessmentQuestions()
    if (result.success) {
      setQuestions(result.data)
    } else {
      console.error('Failed to load questions:', result.error)
    }
  }

  // Step 1: Handle email submission
  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Create lead in database
      const result = await createLead(email)
      
      if (result.success) {
        setLeadId(result.data.id)
        
        // In a real app, you'd send confirmation email here
        // For now, let's auto-confirm for testing
        await confirmEmail(email)
        
        setStep('assessment')
      } else {
        alert('Error: ' + result.error)
      }
    } catch (error) {
      console.error('Error submitting email:', error)
      alert('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Step 2: Handle assessment question response
  const handleQuestionResponse = async (questionId, value, points) => {
    // Store response locally
    setResponses(prev => ({
      ...prev,
      [questionId]: { value, points }
    }))

    // Save to database
    if (leadId) {
      await submitAssessmentResponse(leadId, questionId, value, points)
    }

    // Move to next question or complete assessment
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1)
    } else {
      await handleAssessmentComplete()
    }
  }

  // Step 3: Complete assessment and calculate results
  const handleAssessmentComplete = async () => {
    setLoading(true)

    try {
      // Calculate total score
      const score = Object.values(responses).reduce((sum, response) => sum + response.points, 0)
      setTotalScore(score)

      // Complete assessment in database
      const result = await completeAssessment(email, responses, score)
      
      if (result.success) {
        setStep('results')
      } else {
        alert('Error completing assessment: ' + result.error)
      }
    } catch (error) {
      console.error('Error completing assessment:', error)
      alert('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Get user segment based on score
  const getUserSegment = (score) => {
    if (score <= 16) return 'Stress-Free Lover'
    if (score <= 30) return 'Relationship Spender'
    if (score <= 45) return 'Emotional Money Manager'
    return 'Crisis Mode'
  }

  const getProductTier = (score) => {
    if (score <= 16) return 'Budget ($10)'
    if (score <= 30) return 'Mid-tier ($20)'
    if (score <= 45) return 'Mid-tier ($20)'
    return 'Professional ($50)'
  }

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      {step === 'email' && (
        <div>
          <h2 className="text-2xl font-bold mb-4 text-center">
            Money & Relationship Assessment
          </h2>
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Enter your email to start:
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="your@email.com"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Starting Assessment...' : 'Start Assessment'}
            </button>
          </form>
        </div>
      )}

      {step === 'assessment' && questions.length > 0 && (
        <div>
          <div className="mb-4">
            <div className="text-sm text-gray-600 mb-2">
              Question {currentQuestion + 1} of {questions.length}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold">
              {questions[currentQuestion]?.question_text}
            </h3>

            {questions[currentQuestion]?.question_type === 'radio' && (
              <div className="space-y-2">
                {JSON.parse(questions[currentQuestion].options).map((option, index) => (
                  <button
                    key={option.value}
                    onClick={() => handleQuestionResponse(
                      questions[currentQuestion].question_id,
                      option.value,
                      JSON.parse(questions[currentQuestion].points)[index]
                    )}
                    className="w-full p-3 text-left border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}

            {questions[currentQuestion]?.question_type === 'checkbox' && (
              <div className="space-y-2">
                <p className="text-sm text-gray-600 mb-3">Select all that apply:</p>
                {JSON.parse(questions[currentQuestion].options).map((option, index) => (
                  <label key={option.value} className="flex items-center space-x-3 p-3 border border-gray-300 rounded-md hover:bg-gray-50">
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleQuestionResponse(
                            questions[currentQuestion].question_id,
                            option.value,
                            JSON.parse(questions[currentQuestion].points)[index]
                          )
                        }
                      }}
                      className="h-4 w-4 text-blue-600"
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {step === 'results' && (
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-green-600">
            Assessment Complete!
          </h2>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Your Results:</h3>
            <p className="text-xl font-bold text-blue-600">
              {getUserSegment(totalScore)}
            </p>
            <p className="text-sm text-gray-600 mt-2">
              Score: {totalScore}/100
            </p>
            <p className="text-sm font-medium mt-3">
              Recommended Plan: {getProductTier(totalScore)}
            </p>
          </div>

          <button
            onClick={() => window.location.reload()}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700"
          >
            Take Assessment Again
          </button>
        </div>
      )}
    </div>
  )
}

export default AssessmentFlow 