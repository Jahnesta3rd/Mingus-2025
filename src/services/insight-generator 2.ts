import { QuestionnaireResponse } from './questionnaire-api';

export interface Insight {
  category: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  recommendations: string[];
}

export class InsightGenerator {
  private static readonly THRESHOLDS = {
    stress: {
      high: 8,
      medium: 5
    },
    sleep: {
      low: 4,
      medium: 6
    },
    satisfaction: {
      low: 4,
      medium: 6
    }
  };

  static generateInsights(responses: QuestionnaireResponse[]): Insight[] {
    const insights: Insight[] = [];
    const latestResponse = responses[responses.length - 1];

    // Health Insights
    if (latestResponse.responses.stress_level) {
      const stressLevel = Number(latestResponse.responses.stress_level);
      if (stressLevel >= this.THRESHOLDS.stress.high) {
        insights.push({
          category: 'health',
          title: 'High Stress Level Detected',
          description: 'Your stress level is significantly elevated. This could impact your overall well-being.',
          severity: 'high',
          recommendations: [
            'Consider practicing daily meditation',
            'Take regular breaks during work',
            'Engage in physical exercise',
            'Maintain a consistent sleep schedule'
          ]
        });
      }
    }

    if (latestResponse.responses.sleep_quality) {
      const sleepQuality = Number(latestResponse.responses.sleep_quality);
      if (sleepQuality <= this.THRESHOLDS.sleep.low) {
        insights.push({
          category: 'health',
          title: 'Poor Sleep Quality',
          description: 'Your sleep quality is below optimal levels, which can affect your daily performance.',
          severity: 'medium',
          recommendations: [
            'Establish a regular bedtime routine',
            'Limit screen time before bed',
            'Create a comfortable sleep environment',
            'Consider consulting a sleep specialist'
          ]
        });
      }
    }

    // Career Insights
    if (latestResponse.responses.job_satisfaction) {
      const jobSatisfaction = Number(latestResponse.responses.job_satisfaction);
      if (jobSatisfaction <= this.THRESHOLDS.satisfaction.low) {
        insights.push({
          category: 'career',
          title: 'Low Job Satisfaction',
          description: 'Your current job satisfaction is below optimal levels.',
          severity: 'medium',
          recommendations: [
            'Identify specific aspects of your job that need improvement',
            'Schedule a discussion with your manager',
            'Explore opportunities for growth and development',
            'Consider if your current role aligns with your career goals'
          ]
        });
      }
    }

    // Relationship Insights
    if (latestResponse.responses.social_support) {
      const socialSupport = Number(latestResponse.responses.social_support);
      if (socialSupport <= this.THRESHOLDS.satisfaction.low) {
        insights.push({
          category: 'relationship',
          title: 'Limited Social Support',
          description: 'Your social support network could be strengthened.',
          severity: 'medium',
          recommendations: [
            'Join social groups or clubs aligned with your interests',
            'Reach out to old friends',
            'Participate in community events',
            'Consider professional networking opportunities'
          ]
        });
      }
    }

    return insights;
  }

  static generateTrends(responses: QuestionnaireResponse[]): Record<string, any> {
    const trends: Record<string, any> = {};
    
    // Calculate trends for numerical responses
    const numericalFields = ['stress_level', 'sleep_quality', 'job_satisfaction', 'social_support'];
    
    numericalFields.forEach(field => {
      const values = responses
        .map(r => Number(r.responses[field]))
        .filter(v => !isNaN(v));
      
      if (values.length > 0) {
        trends[field] = {
          average: values.reduce((a, b) => a + b, 0) / values.length,
          trend: values[values.length - 1] > values[0] ? 'increasing' : 'decreasing',
          change: values[values.length - 1] - values[0]
        };
      }
    });

    return trends;
  }
} 