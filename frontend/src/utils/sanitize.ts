import DOMPurify from 'dompurify';

export class Sanitizer {
  /**
   * Control characters + length only. No HTML pass — required for email and any
   * string where DOMPurify would treat paste/clipboard `<`...`>` fragments as tags
   * and strip them (e.g. `user@gmail.co<m` → `user@gmail.co`).
   */
  static sanitizePlainText(input: string, maxLen = 1000): string {
    if (typeof input !== 'string') {
      return '';
    }
    let sanitized = input.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
    return sanitized.substring(0, maxLen);
  }

  static sanitizeString(input: string): string {
    if (typeof input !== 'string') {
      return '';
    }
    
    // Remove null bytes and control characters
    let sanitized = input.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
    
    // Note: Don't trim here - preserve spaces during input
    // Trimming happens on final submission
    
    // Limit length
    sanitized = sanitized.substring(0, 1000);
    
    // Sanitize HTML
    sanitized = DOMPurify.sanitize(sanitized);
    
    return sanitized;
  }
  
  static sanitizeObject(obj: any): any {
    if (obj === null || obj === undefined) {
      return obj;
    }
    
    if (typeof obj === 'string') {
      return this.sanitizeString(obj);
    }
    
    if (Array.isArray(obj)) {
      return obj.map(item => this.sanitizeObject(item));
    }
    
    if (typeof obj === 'object') {
      const sanitized: any = {};
      for (const [key, value] of Object.entries(obj)) {
        const sanitizedKey = this.sanitizeString(key);
        sanitized[sanitizedKey] = this.sanitizeObject(value);
      }
      return sanitized;
    }
    
    return obj;
  }
  
  static escapeHtml(unsafe: string): string {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  
  static validateAndSanitizeEmail(email: string): string | null {
    if (!email || typeof email !== 'string') {
      return null;
    }
    
    const sanitized = this.sanitizePlainText(email, 254);
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    if (!emailRegex.test(sanitized)) {
      return null;
    }
    
    return sanitized.toLowerCase();
  }
}
