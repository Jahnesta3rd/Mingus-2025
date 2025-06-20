import { Question } from './questionnaire-prompts';

export interface ValidationError {
  field: string;
  message: string;
}

export const validateResponse = (question: Question, value: any): ValidationError | null => {
  if (question.required && (value === undefined || value === null || value === '')) {
    return {
      field: question.id,
      message: 'This field is required'
    };
  }

  if (value === undefined || value === null) {
    return null;
  }

  switch (question.type) {
    case 'number':
    case 'scale':
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return {
          field: question.id,
          message: 'Please enter a valid number'
        };
      }
      if (question.validation?.min !== undefined && numValue < question.validation.min) {
        return {
          field: question.id,
          message: `Value must be at least ${question.validation.min}`
        };
      }
      if (question.validation?.max !== undefined && numValue > question.validation.max) {
        return {
          field: question.id,
          message: `Value must be at most ${question.validation.max}`
        };
      }
      break;

    case 'select':
      if (!question.options?.includes(value)) {
        return {
          field: question.id,
          message: 'Please select a valid option'
        };
      }
      break;

    case 'multiselect':
      if (!Array.isArray(value)) {
        return {
          field: question.id,
          message: 'Please select at least one option'
        };
      }
      if (value.length === 0) {
        return {
          field: question.id,
          message: 'Please select at least one option'
        };
      }
      if (!value.every(v => question.options?.includes(v))) {
        return {
          field: question.id,
          message: 'Please select valid options'
        };
      }
      break;

    case 'text':
      if (question.validation?.pattern && !new RegExp(question.validation.pattern).test(value)) {
        return {
          field: question.id,
          message: 'Please enter a valid value'
        };
      }
      break;
  }

  return null;
};

export const validateQuestionnaire = (questions: Question[], responses: Record<string, any>): ValidationError[] => {
  const errors: ValidationError[] = [];
  
  questions.forEach(question => {
    const error = validateResponse(question, responses[question.id]);
    if (error) {
      errors.push(error);
    }
  });

  return errors;
}; 