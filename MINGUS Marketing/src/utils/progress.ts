import { FormData, SavedProgress } from '../types/validation-types'

const STORAGE_KEY = 'ratchet_money_assessment_progress'
const SESSION_KEY = 'ratchet_money_session_id'

// Generate a unique session ID
export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Get or create session ID
export const getSessionId = (): string => {
  let sessionId = localStorage.getItem(SESSION_KEY)
  if (!sessionId) {
    sessionId = generateSessionId()
    localStorage.setItem(SESSION_KEY, sessionId)
  }
  return sessionId
}

// Save progress to localStorage
export const saveProgress = (
  formData: Partial<FormData>,
  currentStep: number
): void => {
  const sessionId = getSessionId()
  const progress: SavedProgress = {
    formData,
    currentStep,
    timestamp: Date.now(),
    sessionId
  }
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress))
    console.log('Progress saved:', { currentStep, timestamp: progress.timestamp })
  } catch (error) {
    console.error('Failed to save progress:', error)
  }
}

// Load progress from localStorage
export const loadProgress = (): SavedProgress | null => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return null
    
    const progress: SavedProgress = JSON.parse(saved)
    
    // Check if progress is less than 24 hours old
    const isExpired = Date.now() - progress.timestamp > 24 * 60 * 60 * 1000
    if (isExpired) {
      clearProgress()
      return null
    }
    
    console.log('Progress loaded:', { currentStep: progress.currentStep, timestamp: progress.timestamp })
    return progress
  } catch (error) {
    console.error('Failed to load progress:', error)
    return null
  }
}

// Clear saved progress
export const clearProgress = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(SESSION_KEY)
    console.log('Progress cleared')
  } catch (error) {
    console.error('Failed to clear progress:', error)
  }
}

// Auto-save progress after each field change
export const autoSaveProgress = (
  formData: Partial<FormData>,
  currentStep: number,
  debounceMs: number = 1000
): (() => void) => {
  let timeoutId: NodeJS.Timeout | null = null
  
  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    
    timeoutId = setTimeout(() => {
      saveProgress(formData, currentStep)
    }, debounceMs)
  }
}

// Check if user has existing progress
export const hasExistingProgress = (): boolean => {
  return loadProgress() !== null
}

// Get progress summary for user
export const getProgressSummary = (): { step: number; fields: number } | null => {
  const progress = loadProgress()
  if (!progress) return null
  
  const filledFields = Object.keys(progress.formData).filter(
    key => progress.formData[key as keyof FormData] !== undefined && 
           progress.formData[key as keyof FormData] !== ''
  ).length
  
  return {
    step: progress.currentStep,
    fields: filledFields
  }
}

// Resume progress confirmation
export const showResumeDialog = (): Promise<boolean> => {
  return new Promise((resolve) => {
    const progress = getProgressSummary()
    if (!progress) {
      resolve(false)
      return
    }
    
    const message = `We found your previous progress (${progress.fields} fields completed). Would you like to continue where you left off?`
    const shouldResume = window.confirm(message)
    resolve(shouldResume)
  })
}

// Save specific field value
export const saveFieldValue = (
  fieldName: keyof FormData,
  value: any,
  currentStep: number
): void => {
  const existingProgress = loadProgress()
  if (existingProgress) {
    const updatedFormData = {
      ...existingProgress.formData,
      [fieldName]: value
    }
    saveProgress(updatedFormData, currentStep)
  } else {
    saveProgress({ [fieldName]: value }, currentStep)
  }
}

// Get field value from saved progress
export const getFieldValue = (fieldName: keyof FormData): any => {
  const progress = loadProgress()
  return progress?.formData[fieldName] || ''
}

// Check if field has been filled
export const isFieldFilled = (fieldName: keyof FormData): boolean => {
  const value = getFieldValue(fieldName)
  if (Array.isArray(value)) {
    return value.length > 0
  }
  return value !== undefined && value !== '' && value !== null
}

// Get completion percentage
export const getCompletionPercentage = (): number => {
  const progress = loadProgress()
  if (!progress) return 0
  
  const totalFields = Object.keys(progress.formData).length
  const filledFields = Object.keys(progress.formData).filter(
    key => isFieldFilled(key as keyof FormData)
  ).length
  
  return totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0
}

// Export progress data for debugging
export const exportProgressData = (): string => {
  const progress = loadProgress()
  return progress ? JSON.stringify(progress, null, 2) : 'No progress data found'
}

// Import progress data (for testing)
export const importProgressData = (data: string): boolean => {
  try {
    const progress: SavedProgress = JSON.parse(data)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress))
    return true
  } catch (error) {
    console.error('Failed to import progress data:', error)
    return false
  }
} 