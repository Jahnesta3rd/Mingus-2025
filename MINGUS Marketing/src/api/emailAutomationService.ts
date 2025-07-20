import { supabase, supabaseAdmin, type Lead, type EmailType, type EmailStatus } from '../lib/supabase-config'
import { getEmailProvider, getAppUrl } from './configAdapter'

export interface EmailTemplate {
  id: string
  name: string
  subject: string
  body: string
  variables: string[]
  segment?: string
  emailType: EmailType
}

export interface EmailData {
  to: string
  subject: string
  body: string
  leadId: string
  emailType: EmailType
  templateId?: string
  variables?: Record<string, string>
}

export interface EmailResult {
  success: boolean
  messageId?: string
  error?: string
}

class EmailAutomationService {
  private emailProvider: 'mailchimp' | 'sendgrid' | 'convertkit' | 'mock'

  constructor() {
    this.emailProvider = getEmailProvider()
  }

  /**
   * Send email using configured provider
   */
  async sendEmail(emailData: EmailData): Promise<EmailResult> {
    try {
      // Log email attempt
      const { data: emailLog, error: logError } = await supabase
        .from('email_logs')
        .insert({
          lead_id: emailData.leadId,
          email_type: emailData.emailType,
          subject: emailData.subject,
          body: emailData.body,
          status: 'sent'
        })
        .select('id')
        .single()

      if (logError) {
        console.error('Failed to log email:', logError)
      }

      // Send email based on provider
      let result: EmailResult

      switch (this.emailProvider) {
        case 'mailchimp':
          result = await this.sendViaMailchimp(emailData)
          break
        case 'sendgrid':
          result = await this.sendViaSendGrid(emailData)
          break
        case 'convertkit':
          result = await this.sendViaConvertKit(emailData)
          break
        default:
          result = await this.sendViaMock(emailData)
      }

      // Update email log with result
      if (emailLog?.id) {
        await supabase
          .from('email_logs')
          .update({
            status: result.success ? 'delivered' : 'failed',
            external_id: result.messageId,
            error_message: result.error
          })
          .eq('id', emailLog.id)
      }

      return result
    } catch (error) {
      console.error('Email sending error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Send welcome email after assessment completion
   */
  async sendWelcomeEmail(lead: Lead): Promise<EmailResult> {
    const template = await this.getEmailTemplate('welcome', lead.segment)
    if (!template) {
      throw new Error('Welcome email template not found')
    }

    const variables = {
      firstName: lead.name || 'there',
      segment: lead.segment,
      score: lead.score.toString(),
      productTier: lead.product_tier
    }

    const subject = this.replaceVariables(template.subject, variables)
    const body = this.replaceVariables(template.body, variables)

    return this.sendEmail({
      to: lead.email,
      subject,
      body,
      leadId: lead.id,
      emailType: 'assessment_results',
      templateId: template.id,
      variables
    })
  }

  /**
   * Send follow-up email sequence
   */
  async sendFollowUpEmail(lead: Lead, sequenceStep: number): Promise<EmailResult> {
    const template = await this.getEmailTemplate(`follow_up_${sequenceStep}`, lead.segment)
    if (!template) {
      throw new Error(`Follow-up email template ${sequenceStep} not found`)
    }

    const variables = {
      firstName: lead.name || 'there',
      segment: lead.segment,
      score: lead.score.toString(),
      productTier: lead.product_tier
    }

    const subject = this.replaceVariables(template.subject, variables)
    const body = this.replaceVariables(template.body, variables)

    return this.sendEmail({
      to: lead.email,
      subject,
      body,
      leadId: lead.id,
      emailType: 'follow_up',
      templateId: template.id,
      variables
    })
  }

  /**
   * Get email template from database
   */
  private async getEmailTemplate(templateName: string, segment?: string): Promise<EmailTemplate | null> {
    try {
      let query = supabase
        .from('email_templates')
        .select('*')
        .eq('template_name', templateName)

      if (segment) {
        query = query.eq('segment', segment)
      }

      const { data, error } = await query.single()

      if (error) {
        if (error.code === 'PGRST116') {
          // Try to get template without segment
          const { data: fallbackData, error: fallbackError } = await supabase
            .from('email_templates')
            .select('*')
            .eq('template_name', templateName)
            .is('segment', null)
            .single()

          if (fallbackError) {
            return null
          }

          return fallbackData
        }
        return null
      }

      return data
    } catch (error) {
      console.error('Error fetching email template:', error)
      return null
    }
  }

  /**
   * Replace variables in email template
   */
  private replaceVariables(text: string, variables: Record<string, string>): string {
    let result = text
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`{{${key}}}`, 'g'), value)
    })
    return result
  }

  /**
   * Send email via Mailchimp
   */
  private async sendViaMailchimp(emailData: EmailData): Promise<EmailResult> {
    try {
      const apiKey = process.env.REACT_APP_MAILCHIMP_API_KEY
      const serverPrefix = process.env.REACT_APP_MAILCHIMP_SERVER_PREFIX || 'us1'

      if (!apiKey) {
        throw new Error('Mailchimp API key not configured')
      }

      const response = await fetch(`https://${serverPrefix}.api.mailchimp.com/3.0/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: {
            to: [{ email: emailData.to }],
            subject: emailData.subject,
            html: emailData.body
          }
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(`Mailchimp error: ${error.detail}`)
      }

      const result = await response.json()
      return {
        success: true,
        messageId: result.id
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Mailchimp error'
      }
    }
  }

  /**
   * Send email via SendGrid
   */
  private async sendViaSendGrid(emailData: EmailData): Promise<EmailResult> {
    try {
      const apiKey = process.env.REACT_APP_SENDGRID_API_KEY
      const fromEmail = process.env.REACT_APP_SENDGRID_FROM_EMAIL || 'noreply@ratchetmoney.com'
      const fromName = process.env.REACT_APP_SENDGRID_FROM_NAME || 'Ratchet Money'

      if (!apiKey) {
        throw new Error('SendGrid API key not configured')
      }

      const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          personalizations: [
            {
              to: [{ email: emailData.to }]
            }
          ],
          from: {
            email: fromEmail,
            name: fromName
          },
          subject: emailData.subject,
          content: [
            {
              type: 'text/html',
              value: emailData.body
            }
          ]
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(`SendGrid error: ${JSON.stringify(error)}`)
      }

      return {
        success: true,
        messageId: response.headers.get('x-message-id') || undefined
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'SendGrid error'
      }
    }
  }

  /**
   * Send email via ConvertKit
   */
  private async sendViaConvertKit(emailData: EmailData): Promise<EmailResult> {
    try {
      const apiKey = process.env.REACT_APP_CONVERTKIT_API_KEY
      const formId = process.env.REACT_APP_CONVERTKIT_FORM_ID

      if (!apiKey || !formId) {
        throw new Error('ConvertKit API key or form ID not configured')
      }

      // ConvertKit doesn't have direct email sending, so we'll add to sequence
      const response = await fetch(`https://api.convertkit.com/v3/forms/${formId}/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          api_key: apiKey,
          email: emailData.to,
          first_name: emailData.variables?.firstName || '',
          fields: {
            segment: emailData.variables?.segment || '',
            score: emailData.variables?.score || ''
          }
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(`ConvertKit error: ${JSON.stringify(error)}`)
      }

      return {
        success: true
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'ConvertKit error'
      }
    }
  }

  /**
   * Mock email sending for development
   */
  private async sendViaMock(emailData: EmailData): Promise<EmailResult> {
    console.log('📧 Mock Email Sent:', {
      to: emailData.to,
      subject: emailData.subject,
      type: emailData.emailType,
      leadId: emailData.leadId
    })

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 100))

    return {
      success: true,
      messageId: `mock-${Date.now()}`
    }
  }

  /**
   * Get email statistics for a lead
   */
  async getEmailStats(leadId: string) {
    try {
      const { data, error } = await supabase
        .from('email_logs')
        .select('*')
        .eq('lead_id', leadId)
        .order('sent_at', { ascending: false })

      if (error) {
        throw new Error(`Failed to fetch email stats: ${error.message}`)
      }

      return {
        totalEmails: data.length,
        emailsSent: data.filter(email => email.status === 'sent').length,
        emailsDelivered: data.filter(email => email.status === 'delivered').length,
        emailsFailed: data.filter(email => email.status === 'failed').length,
        lastEmailSent: data[0]?.sent_at || null,
        emailHistory: data
      }
    } catch (error) {
      console.error('Error fetching email stats:', error)
      throw new Error(`Failed to fetch email stats: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Update email preferences
   */
  async updateEmailPreferences(leadId: string, preferences: Record<string, any>) {
    try {
      const { error } = await supabase
        .from('leads')
        .update({
          email_preferences: preferences,
          updated_at: new Date().toISOString()
        })
        .eq('id', leadId)

      if (error) {
        throw new Error(`Failed to update email preferences: ${error.message}`)
      }

      return { success: true }
    } catch (error) {
      console.error('Error updating email preferences:', error)
      throw new Error(`Failed to update email preferences: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Unsubscribe lead from emails
   */
  async unsubscribeLead(leadId: string, reason?: string) {
    try {
      // Update lead status
      const { error: leadError } = await supabase
        .from('leads')
        .update({
          status: 'unsubscribed',
          updated_at: new Date().toISOString()
        })
        .eq('id', leadId)

      if (leadError) {
        throw new Error(`Failed to unsubscribe lead: ${leadError.message}`)
      }

      // Log unsubscribe event
      await supabase
        .from('email_logs')
        .insert({
          lead_id: leadId,
          email_type: 'follow_up',
          subject: 'Unsubscribe Request',
          body: `User unsubscribed${reason ? `: ${reason}` : ''}`,
          status: 'sent'
        })

      return { success: true }
    } catch (error) {
      console.error('Error unsubscribing lead:', error)
      throw new Error(`Failed to unsubscribe lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
}

export const emailAutomationService = new EmailAutomationService() 