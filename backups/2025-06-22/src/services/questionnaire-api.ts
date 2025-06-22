import { Questionnaire } from '../data/questionnaire-prompts';

export interface QuestionnaireResponse {
  questionnaireId: string;
  userId: string;
  responses: Record<string, any>;
  timestamp: string;
}

export interface QuestionnaireSubmission {
  questionnaireId: string;
  responses: Record<string, any>;
}

class QuestionnaireApi {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  async submitQuestionnaire(submission: QuestionnaireSubmission): Promise<QuestionnaireResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/questionnaires/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submission),
      });

      if (!response.ok) {
        throw new Error('Failed to submit questionnaire');
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting questionnaire:', error);
      throw error;
    }
  }

  async getQuestionnaireHistory(userId: string): Promise<QuestionnaireResponse[]> {
    try {
      const response = await fetch(`${this.baseUrl}/questionnaires/history/${userId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch questionnaire history');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching questionnaire history:', error);
      throw error;
    }
  }

  async getLatestResponses(userId: string): Promise<Record<string, any>> {
    try {
      const response = await fetch(`${this.baseUrl}/questionnaires/latest/${userId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch latest responses');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching latest responses:', error);
      throw error;
    }
  }
}

export const questionnaireApi = new QuestionnaireApi(); 