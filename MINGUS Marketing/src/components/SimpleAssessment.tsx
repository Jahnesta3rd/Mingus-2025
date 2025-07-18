import React, { useState } from 'react'

interface Question {
  id: string
  question: string
  type: 'radio' | 'checkbox' | 'rating'
  options: Array<{
    value: string
    label: string
    points: number
  }>
}

const QUESTIONS: Question[] = [
  {
    id: 'q1',
    question: 'How often do you lose sleep thinking about money?',
    type: 'radio',
    options: [
      { value: 'never', label: 'Never (0 points)', points: 0 },
      { value: 'monthly', label: 'Once a month (1 point)', points: 1 },
      { value: 'weekly', label: 'Weekly (2 points)', points: 2 },
      { value: 'multiple_weekly', label: 'Multiple times per week (3 points)', points: 3 },
      { value: 'daily', label: 'Daily (4 points)', points: 4 }
    ]
  },
  {
    id: 'q2',
    question: 'Which situation most often leads to unplanned spending?',
    type: 'radio',
    options: [
      { value: 'work_stress', label: 'After a stressful day at work', points: 2 },
      { value: 'argument', label: 'Following an argument with someone close to me', points: 3 },
      { value: 'lonely', label: 'When I\'m feeling lonely or disconnected', points: 2 },
      { value: 'comparison', label: 'When I see others enjoying things I can\'t afford', points: 3 },
      { value: 'celebration', label: 'When I\'m trying to celebrate or connect with others', points: 2 }
    ]
  }
]

export const SimpleAssessment: React.FC = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [showResults, setShowResults] = useState(false)

  const handleAnswer = (questionId: string, value: any) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }))
  }

  const handleNext = () => {
    if (currentQuestion < QUESTIONS.length - 1) {
      setCurrentQuestion(prev => prev + 1)
    } else {
      calculateResults()
    }
  }

  const calculateResults = () => {
    let totalScore = 0
    QUESTIONS.forEach(question => {
      const answer = answers[question.id]
      if (answer) {
        const option = question.options.find(opt => opt.value === answer)
        totalScore += option?.points || 0
      }
    })

    let segment = 'stress-free'
    if (totalScore > 16 && totalScore <= 30) {
      segment = 'relationship-spender'
    } else if (totalScore > 30 && totalScore <= 45) {
      segment = 'emotional-manager'
    } else if (totalScore > 45) {
      segment = 'crisis-mode'
    }

    setAnswers(prev => ({
      ...prev,
      totalScore,
      segment
    }))
    setShowResults(true)
  }

  const renderQuestion = (question: Question) => {
    const answer = answers[question.id]

    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-white mb-4">{question.question}</h2>
        <div className="space-y-3">
          {question.options.map((option) => (
            <label
              key={option.value}
              className={`flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all ${
                answer === option.value
                  ? 'border-red-500'
                  : 'border-gray-600 hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name={question.id}
                value={option.value}
                checked={answer === option.value}
                onChange={(e) => handleAnswer(question.id, e.target.value)}
                className="mr-3"
              />
              <span className="text-white">{option.label}</span>
            </label>
          ))}
        </div>
      </div>
    )
  }

  const renderResults = () => {
    const { totalScore, segment } = answers
    return (
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-4">Assessment Results</h2>
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="text-4xl font-bold text-red-500 mb-2">{totalScore}</div>
          <div className="text-lg text-gray-300 mb-4">Total Score</div>
          <div className="text-xl font-semibold text-white mb-4">
            Your Type: {segment.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
          <p className="text-gray-400">
            Based on your responses, you fall into the {segment} category. 
            This indicates how your relationships impact your financial decisions.
          </p>
        </div>
      </div>
    )
  }

  if (showResults) {
    return renderResults()
  }

  const question = QUESTIONS[currentQuestion]
  const progress = ((currentQuestion + 1) / QUESTIONS.length) * 100

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-400">Question {currentQuestion + 1} of {QUESTIONS.length}</span>
          <span className="text-sm text-gray-400">{(progress).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-red-500 to-red-600 to-red-700 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        {renderQuestion(question)}
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-6">
        <button
          onClick={() => setCurrentQuestion(prev => prev - 1)}
          disabled={currentQuestion === 0}
          className="px-4 py-2 text-gray-400 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Previous
        </button>

        <button
          onClick={handleNext}
          disabled={!answers[question.id]}
          className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 hover:scale-105"
        >
          {currentQuestion === QUESTIONS.length - 1 ? 'Get Results' : 'Next'}
        </button>
      </div>
    </div>
  )
} 