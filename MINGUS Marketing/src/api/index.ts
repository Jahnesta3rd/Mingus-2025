// Main API entry point for Ratchet Money Marketing Funnel
// Uses the simplified Supabase configuration with helper functions

import { 
  supabase,
  createLead,
  confirmEmail,
  startAssessment,
  getAssessmentQuestions,
  submitAssessmentResponse,
  completeAssessment,
  getLeadByEmail,
  logEmailSent
} from '../lib/supabase.js'

// Types for the marketing funnel
export interface AssessmentSubmission {
  email: string
  firstName?: string
  phoneNumber?: string
  contactMethod?: 'email' | 'phone' | 'both'
  betaInterest?: 'very' | 'somewhat' | 'not'
  answers: Record<string, number>
  leadSource?: string
  utmData?: {
    source?: string
    medium?: string
    campaign?: string
    term?: string
    content?: string
  }
}

export interface CreateLeadData {
  email: string
  firstName?: string
  phoneNumber?: string
  leadSource?: string
  utmData?: {
    source?: string
    medium?: string
    campaign?: string
    term?: string
    content?: string
  }
}

export interface UpdateLeadData {
  name?: string
  phone?: string
  contactMethod?: 'email' | 'phone' | 'both'
  betaInterest?: boolean
  lead_source?: string
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
  utm_term?: string
  utm_content?: string
}

export interface EmailData {
  to: string
  subject: string
  body: string
  leadId?: string
  emailType?: string
}

export interface AssessmentResult {
  totalScore: number
  segment: string
  challenges: string[]
  leadId: string
}

// Main API class using the simplified Supabase configuration
export class RatchetMoneyAPI {
  // Lead management
  static async createLead(data: CreateLeadData) {
    const result = await createLead(data.email)
    if (result.success && result.data) {
      // Update with additional data if provided
      if (data.firstName || data.phoneNumber || data.leadSource || data.utmData) {
        const updateData: any = {}
        if (data.firstName) updateData.name = data.firstName
        if (data.phoneNumber) updateData.phone = data.phoneNumber
        if (data.leadSource) updateData.lead_source = data.leadSource
        if (data.utmData) {
          updateData.utm_source = data.utmData.source
          updateData.utm_medium = data.utmData.medium
          updateData.utm_campaign = data.utmData.campaign
          updateData.utm_term = data.utmData.term
          updateData.utm_content = data.utmData.content
        }
        
        await supabase
          .from('leads')
          .update(updateData)
          .eq('id', result.data.id)
      }
    }
    return result
  }

  static async getLeadByEmail(email: string) {
    return await getLeadByEmail(email)
  }

  static async updateLead(leadId: string, data: UpdateLeadData) {
    try {
      const { data: result, error } = await supabase
        .from('leads')
        .update(data)
        .eq('id', leadId)
        .select()
      
      if (error) throw error
      return { success: true, data: result[0] }
    } catch (error) {
      console.error('Error updating lead:', error)
      return { success: false, error: error.message }
    }
  }

  static async confirmLead(email: string) {
    return await confirmEmail(email)
  }

  // Assessment management
  static async getAssessmentQuestions() {
    return await getAssessmentQuestions()
  }

  static async startAssessment(email: string) {
    return await startAssessment(email)
  }

  static async submitAssessmentResponse(leadId: string, questionId: string, responseValue: string, responsePoints: number) {
    return await submitAssessmentResponse(leadId, questionId, responseValue, responsePoints)
  }

  static async completeAssessment(submission: AssessmentSubmission): Promise<AssessmentResult> {
    // First, ensure we have a lead
    let lead = await getLeadByEmail(submission.email)
    if (!lead.success || !lead.data) {
      // Create lead if it doesn't exist
      const createResult = await this.createLead({
        email: submission.email,
        firstName: submission.firstName,
        phoneNumber: submission.phoneNumber,
        leadSource: submission.leadSource,
        utmData: submission.utmData
      })
      if (!createResult.success) {
        throw new Error('Failed to create lead')
      }
      lead = { success: true, data: createResult.data }
    }

    // Calculate total score
    const totalScore = Object.values(submission.answers).reduce((sum, score) => sum + score, 0)
    
    // Determine segment based on score
    let segment = 'stress-free'
    if (totalScore <= 15) segment = 'stress-free'
    else if (totalScore <= 30) segment = 'balanced'
    else segment = 'high-stress'

    // Use the database function to complete assessment
    const result = await completeAssessment(submission.email, submission.answers, totalScore)
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to complete assessment')
    }

    return {
      totalScore,
      segment,
      challenges: Object.keys(submission.answers),
      leadId: result.leadId || lead.data.id
    }
  }

  // Email management
  static async sendEmail(data: EmailData) {
    // For now, we'll just log the email
    // In a real implementation, you'd integrate with an email service
    if (data.leadId) {
      await logEmailSent(data.leadId, data.emailType || 'general', data.subject, data.body)
    }
    
    console.log('Email would be sent:', {
      to: data.to,
      subject: data.subject,
      body: data.body
    })
    
    return { success: true, message: 'Email logged successfully' }
  }

  static async sendWelcomeEmail(email: string, leadId?: string) {
    const subject = 'Welcome to Ratchet Money!'
    const body = `
      <h1>Welcome to Ratchet Money!</h1>
      <p>Thank you for joining us on your journey to better financial wellness.</p>
      <p>We're excited to help you build wealth while maintaining healthy relationships.</p>
    `
    
    return await this.sendEmail({
      to: email,
      subject,
      body,
      leadId,
      emailType: 'welcome'
    })
  }

  static async sendFollowUpEmail(email: string, segment: string, leadId?: string) {
    const subject = `Your Personalized ${segment.charAt(0).toUpperCase() + segment.slice(1)} Plan`
    const body = `
      <h1>Your Personalized Plan</h1>
      <p>Based on your assessment, you're in the <strong>${segment}</strong> segment.</p>
      <p>We'll be sending you tailored resources and tips to help you on your journey.</p>
    `
    
    return await this.sendEmail({
      to: email,
      subject,
      body,
      leadId,
      emailType: 'follow_up'
    })
  }

  // Analytics
  static async getAnalytics() {
    try {
      const { data: leads, error: leadsError } = await supabase
        .from('leads')
        .select('created_at, confirmed, segment, score')
      
      if (leadsError) throw leadsError

      const { data: emails, error: emailsError } = await supabase
        .from('email_logs')
        .select('created_at, status, email_type')
      
      if (emailsError) throw emailsError

      return {
        success: true,
        data: {
          totalLeads: leads?.length || 0,
          confirmedLeads: leads?.filter(l => l.confirmed).length || 0,
          totalEmails: emails?.length || 0,
          successfulEmails: emails?.filter(e => e.status === 'sent').length || 0,
          segmentBreakdown: leads?.reduce((acc, lead) => {
            acc[lead.segment] = (acc[lead.segment] || 0) + 1
            return acc
          }, {} as Record<string, number>) || {}
        }
      }
    } catch (error) {
      console.error('Error fetching analytics:', error)
      return { success: false, error: error.message }
    }
  }

  // High-level workflows
  static async createLeadAndConfirm(data: CreateLeadData) {
    const createResult = await this.createLead(data)
    if (!createResult.success) {
      return createResult
    }

    const confirmResult = await this.confirmLead(data.email)
    if (!confirmResult.success) {
      return confirmResult
    }

    // Send welcome email
    await this.sendWelcomeEmail(data.email, createResult.data?.id)

    return { success: true, data: createResult.data }
  }
}

// Export individual services for backward compatibility
export const assessmentService = {
  submitAssessment: RatchetMoneyAPI.completeAssessment,
  getAssessmentQuestions: RatchetMoneyAPI.getAssessmentQuestions,
  getLeadByEmail: RatchetMoneyAPI.getLeadByEmail
}

export const emailService = {
  sendEmail: RatchetMoneyAPI.sendEmail,
  sendWelcomeEmail: RatchetMoneyAPI.sendWelcomeEmail,
  sendFollowUpEmail: RatchetMoneyAPI.sendFollowUpEmail
}

export const leadService = {
  createLead: RatchetMoneyAPI.createLead,
  getLeadByEmail: RatchetMoneyAPI.getLeadByEmail,
  updateLead: RatchetMoneyAPI.updateLead,
  confirmLead: RatchetMoneyAPI.confirmLead
}

// Default export
export default RatchetMoneyAPI 