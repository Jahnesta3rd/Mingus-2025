import React from 'react'
import { AssessmentResults } from './AssessmentResults'

export const ResultsDemo: React.FC = () => {
  // Sample assessment data for demonstration
  const sampleData = {
    totalScore: 28,
    segment: 'relationship-spender',
    answers: {
      q1: { answer: 'weekly', points: 2 },
      q2: { answer: ['impress_date', 'keep_up_friends'], points: 4 },
      q3: { answer: { partner: 3, family: 2, friends: 4 }, points: 3 },
      q4: { answer: 'friends', points: 3 },
      q5: { answer: 'argument', points: 3 },
      q6: { answer: 'mental', points: 2 },
      q7: { answer: 'sometimes', points: 3 },
      q8: { answer: 'surprised_costs', points: 3 },
      q9: { answer: 'uncertain', points: 3 },
      q10: { answer: 'some_connection', points: 3 }
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <AssessmentResults 
        data={sampleData} 
        email="demo@example.com" 
      />
    </div>
  )
} 