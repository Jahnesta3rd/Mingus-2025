export interface QuestionnaireConfig {
  api: {
    baseUrl: string;
    endpoints: {
      submit: string;
      history: string;
      latest: string;
    };
    timeout: number;
  };
  validation: {
    maxTextLength: number;
    minScaleValue: number;
    maxScaleValue: number;
  };
  insights: {
    thresholds: {
      stress: {
        high: number;
        medium: number;
      };
      sleep: {
        low: number;
        medium: number;
      };
      satisfaction: {
        low: number;
        medium: number;
      };
    };
    updateFrequency: number; // in milliseconds
  };
  ui: {
    progressBar: {
      height: string;
      colors: {
        background: string;
        fill: string;
        text: string;
      };
    };
    questionnaire: {
      maxWidth: string;
      spacing: string;
      colors: {
        primary: string;
        secondary: string;
        success: string;
        error: string;
        background: string;
      };
    };
  };
}

const config: QuestionnaireConfig = {
  api: {
    baseUrl: process.env.REACT_APP_API_BASE_URL || '/api',
    endpoints: {
      submit: '/questionnaires/submit',
      history: '/questionnaires/history',
      latest: '/questionnaires/latest',
    },
    timeout: 30000, // 30 seconds
  },
  validation: {
    maxTextLength: 1000,
    minScaleValue: 1,
    maxScaleValue: 10,
  },
  insights: {
    thresholds: {
      stress: {
        high: 8,
        medium: 5,
      },
      sleep: {
        low: 4,
        medium: 6,
      },
      satisfaction: {
        low: 4,
        medium: 6,
      },
    },
    updateFrequency: 24 * 60 * 60 * 1000, // 24 hours
  },
  ui: {
    progressBar: {
      height: '4px',
      colors: {
        background: '#E5E7EB',
        fill: '#3B82F6',
        text: '#1F2937',
      },
    },
    questionnaire: {
      maxWidth: '800px',
      spacing: '1.5rem',
      colors: {
        primary: '#3B82F6',
        secondary: '#6B7280',
        success: '#10B981',
        error: '#EF4444',
        background: '#FFFFFF',
      },
    },
  },
};

export default config; 