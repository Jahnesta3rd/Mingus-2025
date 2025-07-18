// Assessment Types for Ratchet Money Questionnaire

export interface AssessmentQuestion {
  id: string
  type: 'radio' | 'checkbox' | 'rating' | 'text'
  question: string
  required: boolean
  options?: AssessmentOption[]
  subQuestions?: AssessmentSubQuestion[]
}

export interface AssessmentOption {
  value: string
  label: string
  points: number
}

export interface AssessmentSubQuestion {
  id: string
  question: string
  type: 'rating'
  min: number
  max: number
  labels: {
    min: string
    max: string
  }
}

export const ASSESSMENT_QUESTIONS: AssessmentQuestion[] = [
  {
    id: 'relationship_status',
    type: 'radio',
    question: 'What best describes your current relationship status?',
    required: true,
    options: [
      { value: 'single', label: 'Single', points: 0 },
      { value: 'dating', label: 'Dating', points: 2 },
      { value: 'serious', label: 'In a serious relationship', points: 4 },
      { value: 'married', label: 'Married', points: 6 },
      { value: 'complicated', label: 'It\'s complicated', points: 8 }
    ]
  },
  {
    id: 'spending_habits',
    type: 'radio',
    question: 'How do you typically handle spending when you\'re in a relationship?',
    required: true,
    options: [
      { value: 'independent', label: 'I keep my finances completely separate', points: 0 },
      { value: 'shared_expenses', label: 'We share some expenses but keep most separate', points: 2 },
      { value: 'joint_accounts', label: 'We have joint accounts for most things', points: 4 },
      { value: 'spend_more', label: 'I tend to spend more when I\'m in a relationship', points: 6 },
      { value: 'overspend', label: 'I often overspend to impress or keep up', points: 8 }
    ]
  },
  {
    id: 'financial_stress',
    type: 'radio',
    question: 'How often do you experience financial stress related to relationships?',
    required: true,
    options: [
      { value: 'never', label: 'Never', points: 0 },
      { value: 'rarely', label: 'Rarely', points: 2 },
      { value: 'sometimes', label: 'Sometimes', points: 4 },
      { value: 'often', label: 'Often', points: 6 },
      { value: 'always', label: 'Always', points: 8 }
    ]
  },
  {
    id: 'emotional_spending',
    type: 'checkbox',
    question: 'Which of these trigger emotional spending for you? (Select all that apply)',
    required: true,
    options: [
      { value: 'breakup', label: 'After a breakup', points: 3 },
      { value: 'fights', label: 'After arguments with partner', points: 3 },
      { value: 'loneliness', label: 'When feeling lonely', points: 2 },
      { value: 'jealousy', label: 'When jealous of others', points: 2 },
      { value: 'pressure', label: 'Social pressure to keep up', points: 2 },
      { value: 'none', label: 'None of the above', points: 0 }
    ]
  },
  {
    id: 'relationship_money_rating',
    type: 'rating',
    question: 'Rate how much your relationships affect your financial decisions:',
    required: true,
    subQuestions: [
      {
        id: 'spending_decisions',
        question: 'How much do relationships influence your spending decisions?',
        type: 'rating',
        min: 1,
        max: 5,
        labels: {
          min: 'Not at all',
          max: 'Completely'
        }
      },
      {
        id: 'financial_goals',
        question: 'How much do relationships impact your financial goals?',
        type: 'rating',
        min: 1,
        max: 5,
        labels: {
          min: 'No impact',
          max: 'Major impact'
        }
      },
      {
        id: 'money_anxiety',
        question: 'How much anxiety do you feel about money in relationships?',
        type: 'rating',
        min: 1,
        max: 5,
        labels: {
          min: 'No anxiety',
          max: 'Extreme anxiety'
        }
      }
    ]
  },
  {
    id: 'financial_boundaries',
    type: 'radio',
    question: 'How comfortable are you setting financial boundaries in relationships?',
    required: true,
    options: [
      { value: 'very_comfortable', label: 'Very comfortable', points: 0 },
      { value: 'somewhat_comfortable', label: 'Somewhat comfortable', points: 2 },
      { value: 'neutral', label: 'Neutral', points: 4 },
      { value: 'uncomfortable', label: 'Uncomfortable', points: 6 },
      { value: 'very_uncomfortable', label: 'Very uncomfortable', points: 8 }
    ]
  },
  {
    id: 'money_talks',
    type: 'radio',
    question: 'How often do you discuss money with your partner?',
    required: true,
    options: [
      { value: 'never', label: 'Never', points: 8 },
      { value: 'rarely', label: 'Rarely', points: 6 },
      { value: 'sometimes', label: 'Sometimes', points: 4 },
      { value: 'often', label: 'Often', points: 2 },
      { value: 'always', label: 'Always', points: 0 }
    ]
  },
  {
    id: 'financial_goals',
    type: 'checkbox',
    question: 'What are your primary financial goals? (Select all that apply)',
    required: true,
    options: [
      { value: 'emergency_fund', label: 'Build emergency fund', points: 1 },
      { value: 'debt_free', label: 'Become debt-free', points: 1 },
      { value: 'savings', label: 'Save for future', points: 1 },
      { value: 'investment', label: 'Invest for growth', points: 1 },
      { value: 'retirement', label: 'Plan for retirement', points: 1 },
      { value: 'no_goals', label: 'I don\'t have clear financial goals', points: 3 }
    ]
  },
  {
    id: 'relationship_money_conflicts',
    type: 'radio',
    question: 'How often do you have conflicts about money in your relationships?',
    required: true,
    options: [
      { value: 'never', label: 'Never', points: 0 },
      { value: 'rarely', label: 'Rarely', points: 2 },
      { value: 'sometimes', label: 'Sometimes', points: 4 },
      { value: 'often', label: 'Often', points: 6 },
      { value: 'always', label: 'Always', points: 8 }
    ]
  },
  {
    id: 'financial_independence',
    type: 'radio',
    question: 'How important is financial independence to you in relationships?',
    required: true,
    options: [
      { value: 'very_important', label: 'Very important', points: 0 },
      { value: 'important', label: 'Important', points: 1 },
      { value: 'somewhat_important', label: 'Somewhat important', points: 3 },
      { value: 'not_important', label: 'Not very important', points: 5 },
      { value: 'not_at_all', label: 'Not important at all', points: 7 }
    ]
  }
]

// Scoring system for different segments
export const SEGMENT_SCORES = {
  'stress-free': { min: 0, max: 15, color: 'green' },
  'relationship-spender': { min: 16, max: 30, color: 'blue' },
  'emotional-manager': { min: 31, max: 45, color: 'yellow' },
  'crisis-mode': { min: 46, max: 100, color: 'red' }
}

// Helper function to determine segment based on score
export const getSegmentFromScore = (score: number): string => {
  if (score <= 15) return 'stress-free'
  if (score <= 30) return 'relationship-spender'
  if (score <= 45) return 'emotional-manager'
  return 'crisis-mode'
} 