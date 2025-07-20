export interface Question {
  id: string;
  type: 'scale' | 'counter' | 'number' | 'spending' | 'boolean' | 'textarea';
  question: string;
  min?: number;
  max?: number;
  labels?: Record<number, string>;
  required: boolean;
  allowNA?: boolean;
  placeholder?: string;
  maxLength?: number;
  hasAmount?: boolean;
  examples?: string[];
  unit?: string;
}

export interface QuestionnaireSection {
  title: string;
  subtitle: string;
  emoji: string;
  questions: Question[];
}

export interface QuestionnaireType {
  health: QuestionnaireSection;
  relationships: QuestionnaireSection;
  career: QuestionnaireSection;
}

export interface DailyQuestionnaire {
  quick_pulse: QuestionnaireSection;
}

export interface QuestionnaireConfig {
  weekly: QuestionnaireType;
  daily: DailyQuestionnaire;
}

export const QUESTIONNAIRE_CONFIG: QuestionnaireConfig = {
  weekly: {
    health: {
      title: "How did your body feel this week?",
      subtitle: "Your physical wellness impacts your financial decisions",
      emoji: "💪",
      questions: [
        {
          id: "energy_level",
          type: "scale",
          question: "Rate your energy level this week",
          min: 1,
          max: 5,
          labels: {1: "Exhausted", 5: "Energized"},
          required: true
        },
        {
          id: "sleep_quality", 
          type: "scale",
          question: "How would you rate your sleep this week?",
          min: 1,
          max: 5,
          labels: {1: "Poor", 5: "Excellent"},
          required: true
        },
        {
          id: "stress_level",
          type: "scale", 
          question: "Rate your overall stress level",
          min: 1,
          max: 5,
          labels: {1: "Very Low", 5: "Very High"},
          required: true
        },
        {
          id: "exercise_days",
          type: "counter",
          question: "How many days did you exercise or move your body?", 
          min: 0,
          max: 7,
          unit: "days",
          required: true
        },
        {
          id: "mindfulness_minutes",
          type: "number",
          question: "Minutes spent on meditation, prayer, or mindfulness",
          placeholder: "Enter minutes",
          min: 0,
          required: false
        },
        {
          id: "health_spending",
          type: "spending",
          question: "Did health concerns lead to unexpected spending this week?",
          hasAmount: true,
          required: true
        }
      ]
    },
    
    relationships: {
      title: "How are your connections?",
      subtitle: "Strong relationships support better financial decisions", 
      emoji: "💝",
      questions: [
        {
          id: "family_satisfaction",
          type: "scale",
          question: "Rate satisfaction with family relationships",
          min: 1,
          max: 5,
          labels: {1: "Very Unsatisfied", 5: "Very Satisfied"},
          required: true
        },
        {
          id: "romantic_satisfaction",
          type: "scale",
          question: "Rate satisfaction with romantic relationship",
          min: 1,
          max: 5,
          labels: {1: "Very Unsatisfied", 5: "Very Satisfied"},
          allowNA: true,
          required: false
        },
        {
          id: "friendship_satisfaction",
          type: "scale", 
          question: "Rate satisfaction with friendships/social connections",
          min: 1,
          max: 5,
          labels: {1: "Very Unsatisfied", 5: "Very Satisfied"},
          required: true
        },
        {
          id: "social_support",
          type: "scale",
          question: "I feel supported by people in my life",
          min: 1,
          max: 5,
          labels: {1: "Strongly Disagree", 5: "Strongly Agree"},
          required: true
        },
        {
          id: "relationship_spending_impact",
          type: "boolean",
          question: "Did relationship issues affect your spending this week?",
          required: true
        },
        {
          id: "social_spending_comfort",
          type: "scale",
          question: "Rate comfort level with social/relationship spending",
          min: 1,
          max: 5,
          labels: {1: "Very Uncomfortable", 5: "Very Comfortable"},
          required: true
        },
        {
          id: "childcare_stress",
          type: "scale",
          question: "Rate stress level about childcare costs",
          min: 1,
          max: 5,
          labels: {1: "No Stress", 5: "Extreme Stress"},
          allowNA: true,
          required: false
        },
        {
          id: "relationship_notes",
          type: "textarea",
          question: "Briefly describe any relationship factor affecting your finances (optional)",
          placeholder: "e.g., 'Had to help family member with emergency'",
          maxLength: 200,
          required: false
        }
      ]
    },
    
    career: {
      title: "How secure do you feel at work?",
      subtitle: "Job confidence impacts your spending confidence",
      emoji: "💼", 
      questions: [
        {
          id: "job_security",
          type: "scale",
          question: "How secure do you feel in your current job?",
          min: 1,
          max: 5,
          labels: {1: "Very Insecure", 5: "Very Secure"},
          required: true
        },
        {
          id: "income_satisfaction",
          type: "scale",
          question: "Rate satisfaction with current income",
          min: 1,
          max: 5,
          labels: {1: "Very Unsatisfied", 5: "Very Satisfied"},
          required: true
        },
        {
          id: "career_growth_optimism",
          type: "scale",
          question: "Rate optimism about career advancement opportunities",
          min: 1,
          max: 5,
          labels: {1: "Very Pessimistic", 5: "Very Optimistic"},
          required: true
        },
        {
          id: "workplace_stress",
          type: "scale",
          question: "Rate stress level at work",
          min: 1,
          max: 5,
          labels: {1: "Very Low", 5: "Very High"},
          required: true
        },
        {
          id: "pursuing_side_income",
          type: "boolean",
          question: "Are you actively pursuing additional income sources?",
          required: true
        },
        {
          id: "career_investment",
          type: "spending",
          question: "Did you spend money on career development this week?",
          hasAmount: true,
          examples: ["Course, certification, networking event, professional clothes"],
          required: true
        }
      ]
    }
  },

  daily: {
    quick_pulse: {
      title: "Yesterday's quick check-in",
      subtitle: "How did yesterday go?",
      emoji: "📊",
      questions: [
        {
          id: "overall_mood",
          type: "scale",
          question: "How was your overall mood yesterday?",
          min: 1,
          max: 5,
          labels: {1: "Rough day", 5: "Great day"},
          required: true
        },
        {
          id: "spending_comfort",
          type: "scale", 
          question: "How comfortable were you with your spending yesterday?",
          min: 1,
          max: 5,
          labels: {1: "Regretful", 5: "Confident"},
          required: true
        },
        {
          id: "stress_spending",
          type: "boolean",
          question: "Did stress influence any purchases yesterday?",
          required: true
        }
      ]
    }
  }
};

export interface SupportContent {
  quote: string;
  breathing_exercise?: {
    title: string;
    steps: string[];
  };
  affirmation?: string;
  reframe?: string;
  action?: string;
  perspective?: string;
}

export interface SupportContentConfig {
  high_stress: SupportContent;
  overspending: SupportContent;
  job_insecurity: SupportContent;
}

export const SUPPORT_CONTENT: SupportContentConfig = {
  high_stress: {
    quote: "You are stronger than your circumstances. Every financial setback is temporary, but your resilience is permanent.",
    breathing_exercise: {
      title: "4-7-8 Breathing",
      steps: [
        "Breathe in for 4 counts",
        "Hold for 7 counts", 
        "Breathe out for 8 counts",
        "Repeat 3 times"
      ]
    },
    affirmation: "Others have walked this path and found their way. You will too."
  },
  
  overspending: {
    quote: "One difficult day doesn't define your financial future. Tomorrow is a fresh start with fresh choices.",
    reframe: "Think of spending mistakes as tuition for life lessons. You're investing in wisdom.",
    action: "What's one small positive financial action you can take right now?"
  },
  
  job_insecurity: {
    quote: "Your value isn't determined by your current job security. You have skills, experience, and resilience that no one can take away.",
    perspective: "Many successful people faced uncertain times. This challenge is shaping you for something better.",
    action: "Focus on what you can control today - your effort, your learning, your network."
  }
}; 