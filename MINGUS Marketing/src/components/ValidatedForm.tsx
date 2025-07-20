import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mail, 
  User, 
  Phone, 
  Calendar,
  DollarSign,
  Briefcase,
  Heart,
  Target,
  TrendingUp,
  CreditCard,
  Shield,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  ArrowLeft
} from 'lucide-react'
import { 
  FormData, 
  ValidationState, 
  SubmissionState,
  ACCESSIBILITY_LABELS 
} from '../types/validation-types'
import { 
  validateFieldRealTime, 
  validateForm, 
  formatPhoneNumber, 
  parsePhoneNumber,
  isFormValid 
} from '../utils/validation'
import { 
  saveProgress, 
  loadProgress, 
  clearProgress, 
  autoSaveProgress,
  hasExistingProgress,
  showResumeDialog 
} from '../utils/progress'

interface ValidatedFormProps {
  onComplete: (data: FormData) => void
  onProgressResume?: (data: Partial<FormData>) => void
}

export const ValidatedForm: React.FC<ValidatedFormProps> = ({ 
  onComplete, 
  onProgressResume 
}) => {
  const [formData, setFormData] = useState<Partial<FormData>>({})
  const [validationState, setValidationState] = useState<Record<string, ValidationState>>({})
  const [submissionState, setSubmissionState] = useState<SubmissionState>({
    isSubmitting: false,
    isSubmitted: false,
    error: null,
    successMessage: null
  })
  const [currentStep, setCurrentStep] = useState(0)
  const [showResumePrompt, setShowResumePrompt] = useState(false)

  // Auto-save function
  const autoSave = useCallback(
    autoSaveProgress(formData, currentStep, 1000),
    [formData, currentStep]
  )

  // Load existing progress on mount
  useEffect(() => {
    const existingProgress = loadProgress()
    if (existingProgress) {
      setShowResumePrompt(true)
    }
  }, [])

  // Handle resume progress
  const handleResumeProgress = async () => {
    const shouldResume = await showResumeDialog()
    if (shouldResume) {
      const progress = loadProgress()
      if (progress) {
        setFormData(progress.formData)
        setCurrentStep(progress.currentStep)
        if (onProgressResume) {
          onProgressResume(progress.formData)
        }
      }
    }
    setShowResumePrompt(false)
  }

  // Handle field change with real-time validation
  const handleFieldChange = (
    fieldName: keyof FormData, 
    value: any
  ) => {
    const newFormData = { ...formData, [fieldName]: value }
    setFormData(newFormData)

    // Real-time validation
    const validation = validateFieldRealTime(fieldName, value)
    setValidationState(prev => ({
      ...prev,
      [fieldName]: validation
    }))

    // Auto-save progress
    autoSave()
  }

  // Handle field blur (for touch validation)
  const handleFieldBlur = (fieldName: keyof FormData) => {
    const value = formData[fieldName]
    const validation = validateFieldRealTime(fieldName, value)
    setValidationState(prev => ({
      ...prev,
      [fieldName]: { ...validation, isTouched: true }
    }))
  }

  // Handle phone number formatting
  const handlePhoneChange = (value: string) => {
    const formatted = formatPhoneNumber(value)
    handleFieldChange('phoneNumber', formatted)
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate all fields
    const errors = validateForm(formData)
    if (errors.length > 0) {
      // Update validation state for all fields
      const newValidationState: Record<string, ValidationState> = {}
      errors.forEach(error => {
        newValidationState[error.field] = {
          isValid: false,
          errorMessage: error.message,
          isDirty: true,
          isTouched: true
        }
      })
      setValidationState(prev => ({ ...prev, ...newValidationState }))
      return
    }

    setSubmissionState(prev => ({ ...prev, isSubmitting: true, error: null }))

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Clear saved progress
      clearProgress()
      
      setSubmissionState({
        isSubmitting: false,
        isSubmitted: true,
        error: null,
        successMessage: 'Excellent! Your information has been saved successfully'
      })

      // Call completion handler
      onComplete(formData as FormData)
      
    } catch (error) {
      setSubmissionState({
        isSubmitting: false,
        isSubmitted: false,
        error: 'Connection issue - let\'s try again!',
        successMessage: null
      })
    }
  }

  // Render form field with validation
  const renderField = (
    fieldName: keyof FormData,
    type: 'text' | 'email' | 'tel' | 'number' | 'select' | 'radio' | 'checkbox',
    label: string,
    options?: Array<{ value: string; label: string }>,
    placeholder?: string
  ) => {
    const value = formData[fieldName] || ''
    const validation = validationState[fieldName] || {
      isValid: true,
      errorMessage: '',
      isDirty: false,
      isTouched: false
    }

    const showError = validation.isTouched && !validation.isValid

    return (
      <div className="space-y-2">
        <label 
          htmlFor={fieldName} 
          className="block text-sm font-medium text-gray-300"
        >
          {label}
          {validationState[fieldName]?.isValid === false && (
            <span className="text-red-400 ml-1">*</span>
          )}
        </label>

        {type === 'text' || type === 'email' || type === 'tel' || type === 'number' ? (
          <div className="relative">
            <input
              type={type}
              id={fieldName}
              value={value as string}
              onChange={(e) => {
                if (type === 'tel') {
                  handlePhoneChange(e.target.value)
                } else {
                  handleFieldChange(fieldName, e.target.value)
                }
              }}
              onBlur={() => handleFieldBlur(fieldName)}
              placeholder={placeholder}
              aria-describedby={`${fieldName}-error`}
              aria-invalid={showError}
              className={`w-full px-4 py-3 bg-gray-700 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-all ${
                showError 
                  ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' 
                  : 'border-gray-600 focus:border-red-500 focus:ring-red-500/20'
              }`}
            />
            {showError && (
              <AlertCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-red-500" />
            )}
          </div>
        ) : type === 'select' ? (
          <select
            id={fieldName}
            value={value as string}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            onBlur={() => handleFieldBlur(fieldName)}
            aria-describedby={`${fieldName}-error`}
            aria-invalid={showError}
            className={`w-full px-4 py-3 bg-gray-700 border rounded-lg text-white focus:outline-none focus:ring-2 transition-all ${
              showError 
                ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' 
                : 'border-gray-600 focus:border-red-500 focus:ring-red-500/20'
            }`}
          >
            <option value="">Select an option</option>
            {options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : type === 'radio' ? (
          <div className="space-y-2">
            {options?.map(option => (
              <label key={option.value} className="flex items-center">
                <input
                  type="radio"
                  name={fieldName}
                  value={option.value}
                  checked={value === option.value}
                  onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                  onBlur={() => handleFieldBlur(fieldName)}
                  className="mr-3"
                />
                <span className="text-gray-300">{option.label}</span>
              </label>
            ))}
          </div>
        ) : type === 'checkbox' ? (
          <div className="space-y-2">
            {options?.map(option => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  value={option.value}
                  checked={Array.isArray(value) && value.includes(option.value)}
                  onChange={(e) => {
                    const currentValues = Array.isArray(value) ? value : []
                    const newValues = e.target.checked
                      ? [...currentValues, option.value]
                      : currentValues.filter(v => v !== option.value)
                    handleFieldChange(fieldName, newValues)
                  }}
                  onBlur={() => handleFieldBlur(fieldName)}
                  className="mr-3"
                />
                <span className="text-gray-300">{option.label}</span>
              </label>
            ))}
          </div>
        ) : null}

        {showError && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            id={`${fieldName}-error`}
            className="text-sm text-red-400 flex items-center"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 mr-1" />
            {validation.errorMessage}
          </motion.p>
        )}
      </div>
    )
  }

  // Resume prompt modal
  if (showResumePrompt) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-gray-800 rounded-xl p-6 max-w-md w-full border border-gray-700"
        >
          <h3 className="text-xl font-semibold text-white mb-4">
            Welcome Back!
          </h3>
          <p className="text-gray-300 mb-6">
            We found your previous progress. Would you like to continue where you left off?
          </p>
          <div className="flex space-x-3">
            <button
              onClick={handleResumeProgress}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Continue Progress
            </button>
            <button
              onClick={() => {
                clearProgress()
                setShowResumePrompt(false)
              }}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Start Fresh
            </button>
          </div>
        </motion.div>
      </motion.div>
    )
  }

  // Success state
  if (submissionState.isSubmitted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center p-8 bg-green-900/20 rounded-xl border border-green-500/30"
      >
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-green-400 mb-2">
          Success!
        </h2>
        <p className="text-gray-300 mb-4">
          {submissionState.successMessage}
        </p>
        <p className="text-sm text-gray-400">
          You'll receive your personalized results shortly.
        </p>
      </motion.div>
    )
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-400">
            Step {currentStep + 1} of 3
          </span>
          <span className="text-sm text-gray-400">
            {Math.round(((currentStep + 1) / 3) * 100)}% Complete
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep + 1) / 3) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700"
          >
            {currentStep === 0 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-white mb-4">
                  Basic Information
                </h2>
                
                {renderField('email', 'email', 'Email Address', undefined, 'Enter your email')}
                {renderField('firstName', 'text', 'First Name', undefined, 'Enter your first name')}
                {renderField('lastName', 'text', 'Last Name', undefined, 'Enter your last name')}
                {renderField('phoneNumber', 'tel', 'Phone Number (Optional)', undefined, '(555) 123-4567')}
                {renderField('age', 'number', 'Age', undefined, '25')}
                
                {renderField('income', 'select', 'Income Range', [
                  { value: 'under-30k', label: 'Under $30,000' },
                  { value: '30k-50k', label: '$30,000 - $50,000' },
                  { value: '50k-75k', label: '$50,000 - $75,000' },
                  { value: '75k-100k', label: '$75,000 - $100,000' },
                  { value: '100k-150k', label: '$100,000 - $150,000' },
                  { value: '150k-200k', label: '$150,000 - $200,000' },
                  { value: 'over-200k', label: 'Over $200,000' }
                ])}
              </div>
            )}

            {currentStep === 1 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-white mb-4">
                  Financial Profile
                </h2>
                
                {renderField('occupation', 'text', 'Occupation', undefined, 'Enter your job title')}
                {renderField('relationshipStatus', 'select', 'Relationship Status', [
                  { value: 'single', label: 'Single' },
                  { value: 'dating', label: 'Dating' },
                  { value: 'engaged', label: 'Engaged' },
                  { value: 'married', label: 'Married' },
                  { value: 'divorced', label: 'Divorced' },
                  { value: 'other', label: 'Other' }
                ])}
                
                {renderField('financialGoals', 'checkbox', 'Financial Goals (Select all that apply)', [
                  { value: 'emergency-fund', label: 'Build emergency fund' },
                  { value: 'debt-payoff', label: 'Pay off debt' },
                  { value: 'savings', label: 'Save for big purchase' },
                  { value: 'investment', label: 'Start investing' },
                  { value: 'retirement', label: 'Plan for retirement' },
                  { value: 'business', label: 'Start a business' }
                ])}
                
                {renderField('stressLevel', 'radio', 'How stressed are you about money?', [
                  { value: 'very', label: 'Very stressed' },
                  { value: 'somewhat', label: 'Somewhat stressed' },
                  { value: 'neutral', label: 'Neutral' },
                  { value: 'confident', label: 'Confident' },
                  { value: 'very-confident', label: 'Very confident' }
                ])}
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-white mb-4">
                  Spending & Investment
                </h2>
                
                {renderField('spendingHabits', 'checkbox', 'Spending Habits (Select all that apply)', [
                  { value: 'impulse', label: 'Impulse buying' },
                  { value: 'emotional', label: 'Emotional spending' },
                  { value: 'planned', label: 'Planned purchases' },
                  { value: 'budget-conscious', label: 'Budget conscious' },
                  { value: 'relationship-driven', label: 'Relationship-driven spending' }
                ])}
                
                {renderField('emergencyFund', 'select', 'Emergency Fund Status', [
                  { value: 'none', label: 'No emergency fund' },
                  { value: 'less-than-1k', label: 'Less than $1,000' },
                  { value: '1k-5k', label: '$1,000 - $5,000' },
                  { value: '5k-10k', label: '$5,000 - $10,000' },
                  { value: '10k-plus', label: '$10,000+' }
                ])}
                
                {renderField('debtAmount', 'select', 'Total Debt Amount', [
                  { value: 'none', label: 'No debt' },
                  { value: 'under-10k', label: 'Under $10,000' },
                  { value: '10k-25k', label: '$10,000 - $25,000' },
                  { value: '25k-50k', label: '$25,000 - $50,000' },
                  { value: '50k-plus', label: '$50,000+' }
                ])}
                
                {renderField('investmentExperience', 'select', 'Investment Experience', [
                  { value: 'none', label: 'No experience' },
                  { value: 'beginner', label: 'Beginner' },
                  { value: 'intermediate', label: 'Intermediate' },
                  { value: 'advanced', label: 'Advanced' }
                ])}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Error Message */}
        {submissionState.error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg"
          >
            <p className="text-red-400 text-sm flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              {submissionState.error}
            </p>
          </motion.div>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
            disabled={currentStep === 0}
            className="flex items-center px-4 py-2 text-gray-400 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ArrowLeft className="w-5 h-5 mr-1" />
            Previous
          </button>

          {currentStep < 2 ? (
            <button
              type="button"
              onClick={() => setCurrentStep(prev => prev + 1)}
              disabled={!isFormValid(validationState)}
              className="flex items-center px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 hover:scale-105"
            >
              Next
              <ArrowRight className="w-5 h-5 ml-1" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={submissionState.isSubmitting || !isFormValid(validationState)}
              className="flex items-center px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 hover:scale-105"
            >
              {submissionState.isSubmitting ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  Complete Assessment
                  <CheckCircle className="w-5 h-5 ml-1" />
                </>
              )}
            </button>
          )}
        </div>
      </form>
    </div>
  )
} 