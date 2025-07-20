// TypeScript Interfaces for Ratchet Money Assessment System

export interface AssessmentQuestion {
  id: string;
  type: 'radio' | 'heckbox' | 'rating' | 'text' | 'dropdown';
  question: string;
  options?: AssessmentOption[];
  points: number[];
  required: boolean;
}

export interface AssessmentOption {
  value: string | number;
  label: string;
  points: number;
}

export interface AssessmentResponse {
  email: string;
  answers: Record<string, string | number | number>;
  totalScore: number;
  segment: UserSegment;
  results: AssessmentResults;
  timestamp: string;
}

export interface AssessmentResults {
  segment: UserSegment;
  score: number;
  title: string;
  description: string;
  challenges: string[];
  recommendations: string;
  emailContent: EmailContent;
}

export type UserSegment = 
  | 'stress-free'
  | 'relationship-spender'
  | 'emotional-manager' | 'crisis-mode';

export type ProductTier = 'Budget ($10)' | 'Mid-tier ($20)' | 'Professional ($50)';

export interface EmailContent {
  subject: string;
  body: string;
  followUpSequence: FollowUpEmail[];
}

export interface FollowUpEmail {
  day: number;
  subject: string;
  body: string;
}

export interface DatabaseLead {
  email: string;
  segment: UserSegment;
  score: number;
  productTier: ProductTier;
  createdAt: string;
  confirmed: boolean;
  assessmentCompleted: boolean;
}

// Assessment Questions Configuration
export const ASSESSMENT_QUESTIONS: AssessmentQuestion[] = [
  {
    id: 'q1',
    type: 'radio',
    question: 'How often do you lose sleep thinking about money?',
    options: [
      { value: 'never', label: 'Never (0 points)', points: 0 },
      { value: 'monthly', label: 'Once a month (1 point)', points: 1 },
      { value: 'weekly', label: 'Weekly (2 points)', points: 2 },
      { value: 'multiple_weekly', label: 'Multiple times per week (3 points)', points: 3 },
      { value: 'daily', label: 'Daily (4 points)', points: 4 }
    ],
    points: [0, 1, 2, 3,4],
    required: true
  },
  {
    id: 'q2',
    type: 'checkbox',
    question: 'In the past month, how often have you spent money you didn\'t plan to spend because of: (Select all that apply)?',
    options: [
      { value: 'impress_date', label: 'Wanting to impress someone on a date (2 points)', points: 2 },
      { value: 'stress_shopping', label: 'Stress-shopping after an argument with family/partner (3 points)', points: 3 },
      { value: 'keep_up_friends', label: 'Keeping up with friends\' social activities (2 points)', points: 2 },
      { value: 'guilt_family', label: 'Guilt purchases for family members (2 points)', points: 2 },
      { value: 'emotional_eating', label: 'Emotional eating/drinking after relationship stress (2 points)', points: 2 },
      { value: 'none', label: 'None of the above (0 points)', points: 0 }
    ],
    points: [2, 3, 2, 2, 2,0],
    required: true
  },
  {
    id: 'q3',
    type: 'rating',
    question: 'How comfortable are you discussing money with: (Rate 1-5: 1=Very Uncomfortable, 5=Very Comfortable)?',
    options: [
      { value: 'partner', label: 'Your romantic partner', points: 0 },
      { value: 'family', label: 'Your family', points: 0 },
      { value: 'friends', label: 'Close friends', points: 0 }
    ],
    points: [1, 2, 3, 4,5],
    required: true
  },
  {
    id: 'q4',
    type: 'radio',
    question: 'When you\'re stressed about money, who do you talk to?',
    options: [
      { value: 'partner', label: 'My partner/spouse', points: 1 },
      { value: 'family', label: 'Close family members', points: 2 },
      { value: 'friends', label: 'Friends', points: 3 },
      { value: 'myself', label: 'I keep it to myself', points: 4 },
      { value: 'professional', label: 'A professional (therapist, financial advisor, etc.)', points: 5 }
    ],
    points: [1, 2, 3, 4,5],
    required: true
  },
  {
    id: 'q5',
    type: 'radio',
    question: 'Which situation most often leads to unplanned spending?',
    options: [
      { value: 'work_stress', label: 'After a stressful day at work', points: 2 },
      { value: 'argument', label: 'Following an argument with someone close to me', points: 3 },
      { value: 'lonely', label: 'When I\'m feeling lonely or disconnected', points: 2 },
      { value: 'comparison', label: 'When I see others enjoying things I can\'t afford', points: 3 },
      { value: 'celebration', label: 'When I\'m trying to celebrate or connect with others', points: 2 }
    ],
    points: [2, 3, 2, 3,2],
    required: true
  },
  {
    id: 'q6',
    type: 'radio',
    question: 'How do you currently track your spending?',
    options: [
      { value: 'detailed', label: 'Detailed budgeting app/spreadsheet', points: 1 },
      { value: 'mental', label: 'Mental notes and bank account checks', points: 2 },
      { value: 'major_only', label: 'I track major expenses only', points: 3 },
      { value: 'no_tracking', label: 'I don\'t really track spending', points: 4 },
      { value: 'partner_handles', label: 'My partner handles most of it', points: 3 }
    ],
    points: [1, 2, 3, 4,3],
    required: true
  },
  {
    id: 'q7',
    type: 'radio',
    question: 'How often do your relationship goals conflict with your financial goals?',
    options: [
      { value: 'never', label: 'Never - they align perfectly', points: 1 },
      { value: 'rarely', label: 'Rarely - minor conflicts', points: 2 },
      { value: 'sometimes', label: 'Sometimes - noticeable tension', points: 3 },
      { value: 'often', label: 'Often - significant stress', points: 4 },
      { value: 'always', label: 'Always - major source of anxiety', points: 5 }
    ],
    points: [1, 2, 3, 4,5],
    required: true
  },
  {
    id: 'q8',
    type: 'radio',
    question: 'Which statement best describes your approach to planning major expenses?',
    options: [
      { value: 'advance_planning', label: 'I plan everything months in advance with my partner/family', points: 1 },
      { value: 'solo_planning', label: 'I plan solo but inform others', points: 2 },
      { value: 'surprised_costs', label: 'I plan some things but often get surprised by relationship-related costs', points: 3 },
      { value: 'monthly_only', label: 'I rarely plan beyond next month', points: 4 },
      { value: 'impossible', label: 'Planning feels impossible with my current situation', points: 5 }
    ],
    points: [1, 2, 3, 4,5],
    required: true
  },
  {
    id: 'q9',
    type: 'radio',
    question: 'If you had a relationship emergency (breakup, family crisis, etc.), how confident are you that you could handle it financially?',
    options: [
      { value: 'very_confident', label: 'Very confident - I have 6ths saved', points: 1 },
      { value: 'somewhat_confident', label: 'Somewhat confident - I have some savings', points: 2 },
      { value: 'uncertain', label: 'Uncertain - depends on the situation', points: 3 },
      { value: 'not_confident', label: 'Not confident - it would be very stressful', points: 4 },
      { value: 'devastating', label: 'Not confident at all - it would be devastating', points: 5 }
    ],
    points: [1, 2, 3, 4,5],
    required: true
  },
  {
    id: 'q10',
    type: 'radio',
    question: 'Do you notice a connection between your physical/mental wellness and your spending habits?',
    options: [
      { value: 'strong_connection', label: 'Strong connection - when I\'m stressed/unhealthy, I spend more', points: 4 },
      { value: 'some_connection', label: 'Some connection - I notice patterns sometimes', points: 3 },
      { value: 'weak_connection', label: 'Weak connection - maybe a little', points: 2 },
      { value: 'no_connection', label: 'No connection - they\'re separate for me', points: 1 },
      { value: 'never_thought', label: 'I\'ve never thought about it', points: 0 }
    ],
    points: [4, 3, 2, 1,0],
    required: true
  }
];

// Scoring Algorithm Configuration
export const SEGMENT_THRESHOLDS = {
  'stress-free': { min: 0 },
  'relationship-spender': { min: 1630, max: 30 },
  'emotional-manager': { min: 31, max: 45 },
  'crisis-mode': { min: 46, max: 100 }
};

// Email Templates for Each Segment
export const EMAIL_TEMPLATES: Record<UserSegment, EmailContent> = {
  'stress-free': {
    subject: 'Congratulations! You\'re a Stress-Free Lover',
    body: `Youre doing amazing! Your relationship with money and relationships is healthy and balanced. Here are some ways to maintain and enhance your current success...`,
    followUpSequence: [
      { day: 3, subject: 'Share Your Success: Help Others Achieve Financial Harmony', body: 'Your balanced approach to relationships and money is inspiring...' },
      { day: 7, subject: 'Advanced Strategies for Long-Term Relationship & Financial Success', body: 'Ready to take your already-strong foundation to the next level...' }
    ]
  },
  'relationship-spender': {
    subject: 'You\'re a Relationship Spender - Here\'s How to Find Balance',
    body: `You're aware of how relationships impact your spending, which is a great first step! Here are practical strategies to maintain your generosity while protecting your financial future...`,
    followUpSequence: [
      { day: 3, subject: 'Setting Boundaries: How to Say No Without Guilt', body: 'Learning to set healthy financial boundaries is crucial...' },
      { day: 7, subject: 'Creating a Spending Plan That Works for Both You and Your Relationships', body: 'Let\'s create a budget that honors your relationships while protecting your future...' }
    ]
  },
  'emotional-manager': {
    subject: 'You\'re an Emotional Money Manager - Let\'s Build Better Habits',
    body: `Your emotions significantly influence your spending decisions. This is common and fixable! Here are proven strategies to recognize triggers and develop healthier coping mechanisms...`,
    followUpSequence: [
      { day: 3, subject: 'Identifying Your Emotional Spending Triggers', body: 'The first step to change is awareness. Let\'s identify your specific triggers...' },
      { day: 7, subject: 'Building Your Emergency Fund: A Safety Net for Emotional Times', body: 'Having savings reduces the stress that leads to emotional spending...' }
    ]
  },
  'crisis-mode': {
    subject: 'You\'re in Crisis Mode - Let\'s Get You Back in Control',
    body: `Your relationship dynamics are creating significant financial stress. This is serious, but you're taking the right step by seeking help. Here's your immediate action plan...`,
    followUpSequence: [
      { day: 1, subject: 'Emergency Action Plan: Your First 24urs', body: 'Immediate steps to stop the financial bleeding and regain control...' },
      { day: 3, subject: 'Breaking the Cycle: Understanding Your Patterns', body: 'Let\'s identify the root causes of your financial stress...' },
      { day: 7, subject: 'Building Your Support System: You Don\'t Have to Do This Alone', body: 'Professional help and community support can make all the difference...' }
    ]
  }
}; 