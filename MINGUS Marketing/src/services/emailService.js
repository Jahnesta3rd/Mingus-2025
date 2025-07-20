// Updated emailService.js - Frontend service with PDF integration

import { supabase } from './supabase'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001'

// Generate PDF report
export const generateReport = async (leadId) => {
  try {
    console.log('Requesting PDF generation for lead:', leadId)
    
    const response = await fetch(`${API_BASE_URL}/api/generate-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ leadId }),
    })

    const result = await response.json()

    if (!response.ok) {
      console.error('PDF generation API error:', result.error)
      return { success: false, error: result.error || 'Failed to generate PDF' }
    }

    console.log('PDF generated successfully:', result.filename)
    return { 
      success: true, 
      downloadUrl: result.downloadUrl, 
      filename: result.filename 
    }
  } catch (error) {
    console.error('Network error generating PDF:', error)
    return { success: false, error: 'Network error - please try again' }
  }
}

// Enhanced assessment results email with PDF
export const sendAssessmentResults = async (email, userSegment, score, firstName = '', leadId, pdfDownloadUrl = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/send-results`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        email, 
        userSegment, 
        score, 
        firstName, 
        leadId,
        pdfDownloadUrl
      }),
    })

    const result = await response.json()

    if (!response.ok) {
      console.error('Results email API error:', result.error)
      return { success: false, error: result.error || 'Failed to send email' }
    }

    return { success: true, data: result }
  } catch (error) {
    console.error('Network error sending results:', error)
    return { success: false, error: 'Network error - please try again' }
  }
}

// Check if PDF exists for a lead
export const checkPDFExists = async (leadId) => {
  try {
    // This could check the database or just try to generate
    // For now, we'll always try to generate
    return { exists: false }
  } catch (error) {
    console.error('Error checking PDF existence:', error)
    return { exists: false }
  }
}

// Rest of the existing email service functions...
export const sendConfirmationEmail = async (email, leadId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/send-confirmation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, leadId }),
    })

    const result = await response.json()

    if (!response.ok) {
      console.error('API error:', result.error)
      return { success: false, error: result.error || 'Failed to send email' }
    }

    return { success: true, data: result }
  } catch (error) {
    console.error('Network error:', error)
    return { success: false, error: 'Network error - please try again' }
  }
}

export const getEmailAnalytics = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/analytics/emails?days=${days}`)
    
    const result = await response.json()

    if (!response.ok) {
      console.error('API error:', result.error)
      return { success: false, error: result.error || 'Failed to fetch analytics' }
    }

    return { success: true, data: result.data }
  } catch (error) {
    console.error('Network error:', error)
    return { success: false, error: 'Network error - please try again' }
  }
}

export const checkEmailServiceHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    const result = await response.json()
    
    if (response.ok && result.status === 'OK') {
      return { success: true, data: result }
    } else {
      return { success: false, error: 'Email service unavailable' }
    }
  } catch (error) {
    console.error('Health check failed:', error)
    return { success: false, error: 'Email service unavailable' }
  }
} 