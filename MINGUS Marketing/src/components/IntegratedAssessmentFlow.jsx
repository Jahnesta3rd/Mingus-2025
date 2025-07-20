// Updated IntegratedAssessmentFlow.jsx with PDF generation

import React, { useState, useEffect } from 'react'
import { 
  createLead, 
  getAssessmentQuestions, 
  submitAssessmentResponse, 
  completeAssessment,
  confirmEmail,
  getLeadByEmail 
} from '../lib/supabase'
import { 
  sendConfirmationEmail, 
  sendAssessmentResults, 
  generateReport 
} from '../services/emailService'

const IntegratedAssessmentFlow = () => {
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [questions, setQuestions] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [responses, setResponses] = useState({})
  const [totalScore, setTotalScore] = useState(0)
  const [leadId, setLeadId] = useState(null)
  const [userSegment, setUserSegment] = useState('')
  const [step, setStep] = useState('email') // email, confirmation, assessment, generating, results
  const [loading, setLoading] = useState(false)
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState(null)
  const [generatingPDF, setGeneratingPDF] = useState(false)

  // Load assessment questions on component mount
  useEffect(() => {
    loadQuestions()
    
    // Check if user is coming back from email confirmation
    const urlParams = new URLSearchParams(window.location.search)
    const confirmToken = urlParams.get('confirm')
    const emailParam = urlParams.get('email')
    
    if (confirmToken && emailParam) {
      handleEmailConfirmation(emailParam)
    }
  }, [])

  const loadQuestions = async () => {
    const result = await getAssessmentQuestions()
    if (result.success) {
      setQuestions(result.data)
    } else {
      console.error('Failed to load questions:', result.error)
    }
  }

  // Step 1: Handle email submission and send confirmation
  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Create lead in database
      const result = await createLead(email)
      
      if (result.success) {
        setLeadId(result.data.id)
        
        // Send confirmation email
        const emailResult = await sendConfirmationEmail(email, result.data.id)
        
        if (emailResult.success) {
          setStep('confirmation')
        } else {
          alert('Account created but email failed to send. Please try again.')
          console.error('Email error:', emailResult.error)
        }
      } else {
        // Handle case where email already exists
        if (result.error.includes('duplicate key')) {
          const existingLead = await getLeadByEmail(email)
          if (existingLead.success) {
            setLeadId(existingLead.data.id)
            if (existingLead.data.confirmed) {
              setStep('assessment')
            } else {
              await sendConfirmationEmail(email, existingLead.data.id)
              setStep('confirmation')
            }
          }
        } else {
          alert('Error: ' + result.error)
        }
      }
    } catch (error) {
      console.error('Error submitting email:', error)
      alert('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Handle email confirmation from link click
  const handleEmailConfirmation = async (emailParam) => {
    setLoading(true)
    setEmail(emailParam)

    try {
      const result = await confirmEmail(emailParam)
      
      if (result.success) {
        setLeadId(result.data.id)
        setStep('assessment')
      } else {
        alert('Confirmation failed. Please try again.')
      }
    } catch (error) {
      console.error('Error confirming email:', error)
      alert('Confirmation failed. Please try again.')
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

  // Step 3: Complete assessment, generate PDF, and send results email
  const handleAssessmentComplete = async () => {
    setLoading(true)
    setStep('generating') // Show PDF generation step

    try {
      // Calculate total score
      const score = Object.values(responses).reduce((sum, response) => sum + response.points, 0)
      setTotalScore(score)

      // Complete assessment in database
      const result = await completeAssessment(email, responses, score)
      
      if (result.success) {
        // Determine user segment
        let segment = 'stress-free'
        if (score > 16 && score <= 30) segment = 'relationship-spender'
        else if (score > 30 && score <= 45) segment = 'emotional-manager'
        else if (score > 45) segment = 'crisis-mode'
        
        setUserSegment(segment)

        // **NEW: Generate PDF report**
        setGeneratingPDF(true)
        console.log('Generating PDF report...')
        
        const pdfResult = await generateReport(leadId)
        
        let downloadUrl = null
        if (pdfResult.success) {
          downloadUrl = pdfResult.downloadUrl
          setPdfDownloadUrl(downloadUrl)
          console.log('PDF generated successfully:', downloadUrl)
        } else {
          console.error('PDF generation failed:', pdfResult.error)
          // Continue without PDF - don't block the flow
        }
        
        setGeneratingPDF(false)

        // Send results email with PDF download link
        const emailResult = await sendAssessmentResults(
          email, 
          segment, 
          score, 
          firstName, 
          leadId,
          downloadUrl
        )
        
        if (emailResult.success) {
          setStep('results')
        } else {
          console.error('Results email failed:', emailResult.error)
          // Still show results even if email fails
          setStep('results')
        }
      } else {
        alert('Error completing assessment: ' + result.error)
      }
    } catch (error) {
      console.error('Error completing assessment:', error)
      alert('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
      setGeneratingPDF(false)
    }
  }

  // Get user segment display name
  const getUserSegmentDisplay = (segment) => {
    const segments = {
      'stress-free': 'Stress-Free Lover',
      'relationship-spender': 'Relationship Spender',
      'emotional-manager': 'Emotional Money Manager',
      'crisis-mode': 'Crisis Mode'
    }
    return segments[segment] || segment
  }

  const getProductTier = (score) => {
    if (score <= 16) return 'Budget ($10)'
    if (score <= 30) return 'Mid-tier ($20)'
    if (score <= 45) return 'Mid-tier ($20)'
    return 'Professional ($50)'
  }

  const getSegmentColor = (segment) => {
    const colors = {
      'stress-free': 'green',
      'relationship-spender': 'orange',
      'emotional-manager': 'purple',
      'crisis-mode': 'red'
    }
    return colors[segment] || 'blue'
  }

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      {step === 'email' && (
        <div>
          <h2 className="text-2xl font-bold mb-4 text-center text-gray-800">
            Money & Relationship Assessment
          </h2>
          <p className="text-gray-600 mb-6 text-center">
            Discover how your relationships impact your financial decisions
          </p>
          
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700">
                First Name (Optional):
              </label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your first name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700">
                Email Address:
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="your@email.com"
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-md hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 font-semibold"
            >
              {loading ? 'Starting Assessment...' : 'Start Free Assessment'}
            </button>
          </form>
          
          <p className="text-xs text-gray-500 mt-4 text-center">
            We'll send you a confirmation email to start your assessment.<br/>
            <strong>Plus:</strong> Get a FREE personalized PDF action plan!
          </p>
        </div>
      )}

      {step === 'confirmation' && (
        <div className="text-center">
          <div className="mb-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📧</span>
            </div>
            <h2 className="text-2xl font-bold mb-2 text-gray-800">Check Your Email</h2>
            <p className="text-gray-600">
              We've sent a confirmation link to <strong>{email}</strong>
            </p>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              <strong>Next steps:</strong>
            </p>
            <ol className="text-sm text-blue-700 mt-2 text-left">
              <li>1. Check your inbox (and spam folder)</li>
              <li>2. Click the confirmation link</li>
              <li>3. Complete your assessment</li>
              <li>4. Get your FREE personalized PDF report</li>
            </ol>
          </div>
          
          <button
            onClick={() => setStep('email')}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Need to change your email?
          </button>
        </div>
      )}

      {step === 'assessment' && questions.length > 0 && (
        <div>
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">
                Question {currentQuestion + 1} of {questions.length}
              </span>
              <span className="text-sm text-gray-600">
                {Math.round(((currentQuestion + 1) / questions.length) * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              {questions[currentQuestion]?.question_text}
            </h3>

            {questions[currentQuestion]?.question_type === 'radio' && (
              <div className="space-y-3">
                {JSON.parse(questions[currentQuestion].options).map((option, index) => (
                  <button
                    key={option.value}
                    onClick={() => handleQuestionResponse(
                      questions[currentQuestion].question_id,
                      option.value,
                      JSON.parse(questions[currentQuestion].points)[index]
                    )}
                    className="w-full p-4 text-left border border-gray-300 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 focus:ring-2 focus:ring-blue-500"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}

            {questions[currentQuestion]?.question_type === 'checkbox' && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600 mb-3">Select all that apply:</p>
                {JSON.parse(questions[currentQuestion].options).map((option, index) => (
                  <label key={option.value} className="flex items-start space-x-3 p-4 border border-gray-300 rounded-lg hover:bg-blue-50 cursor-pointer">
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
                      className="h-4 w-4 text-blue-600 mt-1 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm">{option.label}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {step === 'generating' && (
        <div className="text-center space-y-6">
          <div className="mb-6">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
            <h2 className="text-2xl font-bold mb-2 text-gray-800">
              Creating Your Personal Report
            </h2>
            <p className="text-gray-600">
              We're analyzing your responses and generating your custom action plan...
            </p>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="space-y-3">
              <div className="flex items-center text-sm text-purple-700">
                <span className="w-4 h-4 bg-purple-600 rounded-full mr-3 flex-shrink-0"></span>
                Assessment completed ✓
              </div>
              <div className="flex items-center text-sm text-purple-700">
                <div className="w-4 h-4 border-2 border-purple-600 rounded-full mr-3 flex-shrink-0 animate-pulse"></div>
                {generatingPDF ? 'Generating your PDF report...' : 'Preparing your results...'}
              </div>
              <div className="flex items-center text-sm text-gray-500">
                <span className="w-4 h-4 border-2 border-gray-300 rounded-full mr-3 flex-shrink-0"></span>
                Sending email with download link
              </div>
            </div>
          </div>
          
          <p className="text-xs text-gray-500">
            This usually takes 10-15 seconds. Please don't close this window.
          </p>
        </div>
      )}

      {step === 'results' && (
        <div className="text-center space-y-6">
          <div className="mb-6">
            <div className={`w-16 h-16 bg-${getSegmentColor(userSegment)}-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
              <span className="text-2xl">🎉</span>
            </div>
            <h2 className="text-2xl font-bold text-green-600 mb-2">
              Assessment Complete!
            </h2>
            <p className="text-gray-600">
              Your personalized results are ready
            </p>
          </div>
          
          <div className={`bg-gradient-to-r from-${getSegmentColor(userSegment)}-50 to-${getSegmentColor(userSegment)}-100 p-6 rounded-lg border border-${getSegmentColor(userSegment)}-200`}>
            <h3 className="text-lg font-semibold mb-2 text-gray-800">Your Results:</h3>
            <p className={`text-xl font-bold text-${getSegmentColor(userSegment)}-600 mb-2`}>
              {getUserSegmentDisplay(userSegment)}
            </p>
            <p className="text-sm text-gray-600 mb-3">
              Score: {totalScore}/100
            </p>
            <div className={`border-t border-${getSegmentColor(userSegment)}-200 pt-3 mt-3`}>
              <p className="text-sm font-medium text-gray-700">
                Recommended Plan: {getProductTier(totalScore)}
              </p>
            </div>
          </div>

          {/* PDF Download Section */}
          {pdfDownloadUrl && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-center mb-3">
                <span className="text-2xl mr-2">📄</span>
                <h4 className="text-lg font-semibold text-green-800">Your Free Personal Action Plan</h4>
              </div>
              <p className="text-sm text-green-700 mb-4">
                We've created a detailed 10-page report with your personalized strategies, 
                emergency toolkit, and 30-day action plan.
              </p>
              <button
                onClick={() => window.open(pdfDownloadUrl, '_blank')}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 text-sm font-medium"
              >
                📥 Download Your Free Report
              </button>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={() => {
                const signupUrl = `https://your-app.com/signup?segment=${userSegment}&email=${encodeURIComponent(email)}&score=${totalScore}&utm_source=assessment&utm_medium=results`
                window.open(signupUrl, '_blank')
              }}
              className="w-full bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 px-4 rounded-md hover:from-green-700 hover:to-blue-700 font-semibold"
            >
              Get Your Personal Finance Plan
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 text-sm"
            >
              Take Assessment Again
            </button>
          </div>

          <p className="text-xs text-gray-500">
            {pdfDownloadUrl ? 
              `Your detailed report and next steps have been sent to ${email}` :
              `Your results have been sent to ${email}. Your PDF report will arrive shortly.`
            }
          </p>
        </div>
      )}

      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-center text-gray-600">
              {step === 'generating' ? 'Creating your report...' : 'Loading...'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default IntegratedAssessmentFlow 