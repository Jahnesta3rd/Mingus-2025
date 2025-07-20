import { 
  ValidationRule, 
  ValidationState, 
  ValidationError, 
  FormData,
  VALIDATION_MESSAGES,
  ENCOURAGING_MESSAGES 
} from '../types/validation-types'

// Validation Patterns
export const VALIDATION_PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^[\+]?[1-9][\d]{0,15}$/,
  age: /^\d{1,2}$/,
  name: /^[a-zA-Z\s'-]{2,50}$/,
  income: /^\d{1,3}(,\d{3})*$/
} as const

// Custom Validation Functions
export const CUSTOM_VALIDATORS = {
  age: (value: string): boolean => {
    const age = parseInt(value)
    return age >= 25 && age <= 35
  },
  
  phone: (value: string): boolean => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '')
    return digits.length >= 10 && digits.length <= 15
  },
  
  income: (value: string): boolean => {
    // Check if it's a valid income range selection
    const validRanges = [
      'under-30k', '30k-50k', '50k-75k', '75k-100k', 
      '100k-150k', '150k-200k', 'over-200k'
    ]
    return validRanges.includes(value)
  },
  
  email: (value: string): boolean => {
    return VALIDATION_PATTERNS.email.test(value)
  },
  
  name: (value: string): boolean => {
    return VALIDATION_PATTERNS.name.test(value) && value.trim().length >= 2
  }
} as const

// Validation Configuration
export const VALIDATION_CONFIG: Record<string, ValidationRule[]> = {
  email: [
    { required: true, message: ENCOURAGING_MESSAGES.email.empty },
    { pattern: VALIDATION_PATTERNS.email, message: ENCOURAGING_MESSAGES.email.invalid }
  ],
  
  firstName: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required },
    { minLength: 2, message: VALIDATION_MESSAGES.minLength(2) },
    { maxLength: 50, message: VALIDATION_MESSAGES.maxLength(50) },
    { custom: CUSTOM_VALIDATORS.name, message: 'Please enter a valid first name' }
  ],
  
  lastName: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required },
    { minLength: 2, message: VALIDATION_MESSAGES.minLength(2) },
    { maxLength: 50, message: VALIDATION_MESSAGES.maxLength(50) },
    { custom: CUSTOM_VALIDATORS.name, message: 'Please enter a valid last name' }
  ],
  
  phoneNumber: [
    { custom: CUSTOM_VALIDATORS.phone, message: ENCOURAGING_MESSAGES.phone.invalid }
  ],
  
  age: [
    { required: true, message: ENCOURAGING_MESSAGES.age.empty },
    { pattern: VALIDATION_PATTERNS.age, message: 'Please enter a valid age' },
    { custom: CUSTOM_VALIDATORS.age, message: ENCOURAGING_MESSAGES.age.tooYoung }
  ],
  
  income: [
    { required: true, message: ENCOURAGING_MESSAGES.income.empty },
    { custom: CUSTOM_VALIDATORS.income, message: 'Please select a valid income range' }
  ],
  
  occupation: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required },
    { minLength: 2, message: VALIDATION_MESSAGES.minLength(2) }
  ],
  
  relationshipStatus: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required }
  ],
  
  financialGoals: [
    { 
      required: true, 
      custom: (value: string[]) => value.length > 0,
      message: 'Please select at least one financial goal'
    }
  ],
  
  stressLevel: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required }
  ],
  
  spendingHabits: [
    { 
      required: true, 
      custom: (value: string[]) => value.length > 0,
      message: 'Please select at least one spending habit'
    }
  ],
  
  emergencyFund: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required }
  ],
  
  debtAmount: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required }
  ],
  
  investmentExperience: [
    { required: true, message: ENCOURAGING_MESSAGES.general.required }
  ]
}

// Main Validation Function
export const validateField = (
  fieldName: string, 
  value: any, 
  rules: ValidationRule[]
): ValidationError | null => {
  for (const rule of rules) {
    // Required validation
    if (rule.required && (!value || (Array.isArray(value) && value.length === 0))) {
      return {
        field: fieldName,
        message: rule.message || VALIDATION_MESSAGES.required,
        type: 'required'
      }
    }
    
    // Skip other validations if value is empty and not required
    if (!value || (Array.isArray(value) && value.length === 0)) {
      continue
    }
    
    // Min length validation
    if (rule.minLength && typeof value === 'string' && value.length < rule.minLength) {
      return {
        field: fieldName,
        message: rule.message || VALIDATION_MESSAGES.minLength(rule.minLength),
        type: 'format'
      }
    }
    
    // Max length validation
    if (rule.maxLength && typeof value === 'string' && value.length > rule.maxLength) {
      return {
        field: fieldName,
        message: rule.message || VALIDATION_MESSAGES.maxLength(rule.maxLength),
        type: 'format'
      }
    }
    
    // Pattern validation
    if (rule.pattern && typeof value === 'string' && !rule.pattern.test(value)) {
      return {
        field: fieldName,
        message: rule.message || VALIDATION_MESSAGES.pattern,
        type: 'format'
      }
    }
    
    // Custom validation
    if (rule.custom && !rule.custom(value)) {
      return {
        field: fieldName,
        message: rule.message || VALIDATION_MESSAGES.custom,
        type: 'custom'
      }
    }
  }
  
  return null
}

// Validate entire form
export const validateForm = (formData: Partial<FormData>): ValidationError[] => {
  const errors: ValidationError[] = []
  
  Object.keys(VALIDATION_CONFIG).forEach(fieldName => {
    const fieldRules = VALIDATION_CONFIG[fieldName as keyof typeof VALIDATION_CONFIG]
    const fieldValue = formData[fieldName as keyof FormData]
    
    const error = validateField(fieldName, fieldValue, fieldRules)
    if (error) {
      errors.push(error)
    }
  })
  
  return errors
}

// Real-time validation for single field
export const validateFieldRealTime = (
  fieldName: string, 
  value: any
): ValidationState => {
  const rules = VALIDATION_CONFIG[fieldName as keyof typeof VALIDATION_CONFIG] || []
  const error = validateField(fieldName, value, rules)
  
  return {
    isValid: !error,
    errorMessage: error?.message || '',
    isDirty: true,
    isTouched: true
  }
}

// Format phone number for display
export const formatPhoneNumber = (value: string): string => {
  // Remove all non-digits
  const digits = value.replace(/\D/g, '')
  
  // Format based on length
  if (digits.length <= 3) {
    return digits
  } else if (digits.length <= 6) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  } else {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
  }
}

// Parse phone number for storage
export const parsePhoneNumber = (value: string): string => {
  return value.replace(/\D/g, '')
}

// Check if form is valid
export const isFormValid = (validationState: Record<string, ValidationState>): boolean => {
  return Object.values(validationState).every(state => state.isValid)
}

// Get encouraging message based on field and error type
export const getEncouragingMessage = (
  fieldName: string, 
  errorType: string, 
  value?: any
): string => {
  const fieldMessages = ENCOURAGING_MESSAGES[fieldName as keyof typeof ENCOURAGING_MESSAGES]
  
  if (fieldMessages && typeof fieldMessages === 'object') {
    if (errorType === 'required' && !value && 'empty' in fieldMessages) {
      return (fieldMessages as any).empty || ENCOURAGING_MESSAGES.general.required
    }
    if ((errorType === 'format' || errorType === 'custom') && 'invalid' in fieldMessages) {
      return (fieldMessages as any).invalid || ENCOURAGING_MESSAGES.general.required
    }
  }
  
  return ENCOURAGING_MESSAGES.general.required
} 