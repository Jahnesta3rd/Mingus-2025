import DOMPurify from 'dompurify';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  sanitizedValue?: any;
}

export class InputValidator {
  static validateEmail(email: string): ValidationResult {
    const errors: string[] = [];
    
    if (!email) {
      errors.push('Email is required');
      return { isValid: false, errors };
    }
    
    if (typeof email !== 'string') {
      errors.push('Email must be a string');
      return { isValid: false, errors };
    }
    
    if (email.length > 254) {
      errors.push('Email is too long');
      return { isValid: false, errors };
    }
    
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) {
      errors.push('Invalid email format');
      return { isValid: false, errors };
    }
    
    return { isValid: true, errors: [], sanitizedValue: email.toLowerCase().trim() };
  }
  
  static validateName(name: string): ValidationResult {
    const errors: string[] = [];
    
    if (!name) {
      errors.push('Name is required');
      return { isValid: false, errors };
    }
    
    if (typeof name !== 'string') {
      errors.push('Name must be a string');
      return { isValid: false, errors };
    }
    
    if (name.length < 1 || name.length > 100) {
      errors.push('Name must be between 1 and 100 characters');
      return { isValid: false, errors };
    }
    
    // Check for potentially malicious content
    if (/<script|javascript:|on\w+\s*=/i.test(name)) {
      errors.push('Name contains potentially malicious content');
      return { isValid: false, errors };
    }
    
    const sanitized = DOMPurify.sanitize(name.trim());
    return { isValid: true, errors: [], sanitizedValue: sanitized };
  }
  
  static validatePhone(phone: string): ValidationResult {
    const errors: string[] = [];
    
    if (!phone) {
      return { isValid: true, errors: [], sanitizedValue: '' };
    }
    
    if (typeof phone !== 'string') {
      errors.push('Phone must be a string');
      return { isValid: false, errors };
    }
    
    // Remove all non-digit characters
    const digitsOnly = phone.replace(/\D/g, '');
    
    if (digitsOnly.length < 10 || digitsOnly.length > 15) {
      errors.push('Phone number must be between 10 and 15 digits');
      return { isValid: false, errors };
    }
    
    return { isValid: true, errors: [], sanitizedValue: digitsOnly };
  }
  
  static sanitizeHtml(html: string): string {
    return DOMPurify.sanitize(html);
  }
  
  static validateAssessmentAnswers(answers: Record<string, any>): ValidationResult {
    const errors: string[] = [];
    
    if (!answers || typeof answers !== 'object') {
      errors.push('Answers must be an object');
      return { isValid: false, errors };
    }
    
    // Check for excessive data size
    const jsonString = JSON.stringify(answers);
    if (jsonString.length > 10000) {
      errors.push('Assessment answers are too large');
      return { isValid: false, errors };
    }
    
    // Validate each answer
    for (const [key, value] of Object.entries(answers)) {
      if (typeof key !== 'string' || key.length > 100) {
        errors.push('Invalid answer key');
        continue;
      }
      
      if (typeof value === 'string' && value.length > 1000) {
        errors.push(`Answer for ${key} is too long`);
        continue;
      }
      
      // Sanitize string values
      if (typeof value === 'string') {
        answers[key] = DOMPurify.sanitize(value);
      }
    }
    
    return { isValid: true, errors: [], sanitizedValue: answers };
  }
}