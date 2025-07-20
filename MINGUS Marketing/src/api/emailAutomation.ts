import { supabase, supabaseAdmin } from '../lib/supabase'
import { Database } from '../types/database'

type Lead = Database['public']['Tables']['leads']['Row']
type LeadInsert = Database['public']['Tables']['leads']['Insert']
type EmailLog = Database['public']['Tables']['email_logs']['Row']
type EmailLogInsert = Database['public']['Tables']['email_logs']['Insert']

// Email service configuration
interface EmailServiceConfig {
  provider: 'mailchimp' | 'convertkit' | 'sendgrid'
  apiKey: string
  listId: string
  baseUrl: string
}

// Segment mapping based on assessment scores
const SEGMENT_MAPPING = {
  'stress-free': { min: 0, max: 25, tier: 'Budget ($10)' },
  'relationship-spender': { min: 26, max: 50, tier: 'Mid-tier ($20)' },
  'emotional-manager': { min: 51, max: 75, tier: 'Mid-tier ($20)' },
  'crisis-mode': { min: 76, max: 100, tier: 'Professional ($50)' }
}

// API Response types
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

interface QuestionnaireSubmission {
  email: string
  name?: string
  phone?: string
  responses: Record<string, string>
  score: number
  contactMethod: 'email' | 'phone' | 'both'
  betaInterest: boolean
}

interface EmailSubscription {
  email: string
  name?: string
  preferences: {
    marketing: boolean
    transactional: boolean
    frequency: 'daily' | 'weekly' | 'monthly'
  }
}

// 1. Questionnaire Submission API
export async function submitQuestionnaire(data: QuestionnaireSubmission): Promise<ApiResponse<Lead>> {
  try {
    // Validate input
    if (!data.email || !data.responses || typeof data.score !== 'number') {
      return { success: false, error: 'Missing required fields' }
    }

    // Determine segment based on score
    const segment = determineSegment(data.score)
    const productTier = SEGMENT_MAPPING[segment].tier

    // Create lead record
    const leadData: LeadInsert = {
      email: data.email,
      name: data.name || null,
      phone: data.phone || null,
      segment,
      score: data.score,
      product_tier: productTier,
      confirmed: false,
      assessment_completed: true,
      assessment_answers: data.responses,
      email_sequence_sent: 0,
      email_preferences: {
        marketing: true,
        transactional: true,
        frequency: 'weekly'
      },
      engagement_metrics: {
        emails_opened: 0,
        emails_clicked: 0,
        last_engaged: null
      }
    }

    const { data: lead, error } = await supabase
      .from('leads')
      .insert(leadData)
      .select()
      .single()

    if (error) throw error

    // Store individual responses
    await storeAssessmentResponses(lead.id, data.responses)

    // Send immediate results email
    await sendResultsEmail(lead)

    // Add to email service
    await addToEmailService(lead)

    return { success: true, data: lead, message: 'Questionnaire submitted successfully' }
  } catch (error) {
    console.error('Questionnaire submission error:', error)
    return { success: false, error: 'Failed to submit questionnaire' }
  }
}

// 2. Email List Subscription API
export async function subscribeToEmailList(data: EmailSubscription): Promise<ApiResponse<Lead>> {
  try {
    // Check if lead already exists
    const { data: existingLead } = await supabase
      .from('leads')
      .select()
      .eq('email', data.email)
      .single()

    if (existingLead) {
      // Update preferences
      const { data: updatedLead, error } = await supabase
        .from('leads')
        .update({
          email_preferences: data.preferences,
          confirmed: true
        })
        .eq('id', existingLead.id)
        .select()
        .single()

      if (error) throw error
      return { success: true, data: updatedLead, message: 'Email preferences updated' }
    }

    // Create new lead
    const leadData: LeadInsert = {
      email: data.email,
      name: data.name || null,
      segment: 'stress-free', // Default segment
      score: 0,
      product_tier: 'Budget ($10)',
      confirmed: true,
      assessment_completed: false,
      email_sequence_sent: 0,
      email_preferences: data.preferences,
      engagement_metrics: {
        emails_opened: 0,
        emails_clicked: 0,
        last_engaged: null
      }
    }

    const { data: lead, error } = await supabase
      .from('leads')
      .insert(leadData)
      .select()
      .single()

    if (error) throw error

    // Add to email service
    await addToEmailService(lead)

    // Send welcome email
    await sendWelcomeEmail(lead)

    return { success: true, data: lead, message: 'Successfully subscribed to email list' }
  } catch (error) {
    console.error('Email subscription error:', error)
    return { success: false, error: 'Failed to subscribe to email list' }
  }
}

// 3. Results Delivery API
export async function deliverResults(leadId: string): Promise<ApiResponse<EmailLog>> {
  try {
    const { data: lead, error: leadError } = await supabase
      .from('leads')
      .select()
      .eq('id', leadId)
      .single()

    if (leadError || !lead) {
      return { success: false, error: 'Lead not found' }
    }

    const emailLog = await sendResultsEmail(lead)
    return { success: true, data: emailLog, message: 'Results delivered successfully' }
  } catch (error) {
    console.error('Results delivery error:', error)
    return { success: false, error: 'Failed to deliver results' }
  }
}

// 4. Segment Tagging API
export async function updateSegment(leadId: string, newSegment: string): Promise<ApiResponse<Lead>> {
  try {
    const { data: lead, error } = await supabase
      .from('leads')
      .update({
        segment: newSegment,
        product_tier: SEGMENT_MAPPING[newSegment as keyof typeof SEGMENT_MAPPING]?.tier || 'Budget ($10)'
      })
      .eq('id', leadId)
      .select()
      .single()

    if (error) throw error

    // Update email service tags
    await updateEmailServiceTags(lead)

    return { success: true, data: lead, message: 'Segment updated successfully' }
  } catch (error) {
    console.error('Segment update error:', error)
    return { success: false, error: 'Failed to update segment' }
  }
}

// Helper functions
function determineSegment(score: number): string {
  for (const [segment, range] of Object.entries(SEGMENT_MAPPING)) {
    if (score >= range.min && score <= range.max) {
      return segment
    }
  }
  return 'stress-free' // Default fallback
}

async function storeAssessmentResponses(leadId: string, responses: Record<string, string>) {
  const responseData = Object.entries(responses).map(([questionId, response]) => ({
    lead_id: leadId,
    question_id: questionId,
    response
  }))

  const { error } = await supabase
    .from('assessment_responses')
    .insert(responseData)

  if (error) {
    console.error('Failed to store assessment responses:', error)
  }
}

async function sendResultsEmail(lead: Lead): Promise<EmailLog> {
  const template = await getEmailTemplate('assessment_results', lead.segment)
  const emailBody = replaceTemplateVariables(template.body, lead)
  const subject = replaceTemplateVariables(template.subject, lead)

  const emailLog: EmailLogInsert = {
    lead_id: lead.id,
    email_type: 'assessment_results',
    subject,
    body: emailBody,
    status: 'sent',
    template_id: template.id
  }

  const { data: log, error } = await supabase
    .from('email_logs')
    .insert(emailLog)
    .select()
    .single()

  if (error) throw error

  // Send actual email via service
  await sendEmailViaService(lead.email, subject, emailBody)

  return log
}

async function sendWelcomeEmail(lead: Lead): Promise<EmailLog> {
  const template = await getEmailTemplate('welcome', null)
  const emailBody = replaceTemplateVariables(template.body, lead)
  const subject = replaceTemplateVariables(template.subject, lead)

  const emailLog: EmailLogInsert = {
    lead_id: lead.id,
    email_type: 'welcome',
    subject,
    body: emailBody,
    status: 'sent',
    template_id: template.id
  }

  const { data: log, error } = await supabase
    .from('email_logs')
    .insert(emailLog)
    .select()
    .single()

  if (error) throw error

  await sendEmailViaService(lead.email, subject, emailBody)
  return log
}

async function getEmailTemplate(type: string, segment: string | null) {
  const { data: template, error } = await supabase
    .from('email_templates')
    .select()
    .eq('template_type', type)
    .eq('is_active', true)
    .eq('segment', segment)
    .single()

  if (error || !template) {
    // Fallback to generic template
    const { data: fallbackTemplate } = await supabase
      .from('email_templates')
      .select()
      .eq('template_type', type)
      .eq('is_active', true)
      .is('segment', null)
      .single()

    return fallbackTemplate
  }

  return template
}

function replaceTemplateVariables(template: string, lead: Lead): string {
  return template
    .replace('{{name}}', lead.name || 'there')
    .replace('{{segment}}', lead.segment)
    .replace('{{score}}', lead.score.toString())
    .replace('{{product_tier}}', lead.product_tier)
    .replace('{{email}}', lead.email)
}

async function addToEmailService(lead: Lead) {
  // Implementation depends on email service provider
  // This is a placeholder for Mailchimp/ConvertKit integration
  const emailServiceConfig = getEmailServiceConfig()
  
  try {
    const response = await fetch(`${emailServiceConfig.baseUrl}/lists/${emailServiceConfig.listId}/members`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${emailServiceConfig.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email_address: lead.email,
        status: 'subscribed',
        merge_fields: {
          FNAME: lead.name || '',
          SEGMENT: lead.segment,
          SCORE: lead.score,
          PRODUCT_TIER: lead.product_tier
        },
        tags: [lead.segment, lead.product_tier]
      })
    })

    if (!response.ok) {
      throw new Error(`Email service error: ${response.statusText}`)
    }
  } catch (error) {
    console.error('Failed to add to email service:', error)
  }
}

async function updateEmailServiceTags(lead: Lead) {
  const emailServiceConfig = getEmailServiceConfig()
  
  try {
    const response = await fetch(`${emailServiceConfig.baseUrl}/lists/${emailServiceConfig.listId}/members/${lead.email}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${emailServiceConfig.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        merge_fields: {
          SEGMENT: lead.segment,
          PRODUCT_TIER: lead.product_tier
        },
        tags: [lead.segment, lead.product_tier]
      })
    })

    if (!response.ok) {
      throw new Error(`Email service error: ${response.statusText}`)
    }
  } catch (error) {
    console.error('Failed to update email service tags:', error)
  }
}

async function sendEmailViaService(to: string, subject: string, body: string) {
  const emailServiceConfig = getEmailServiceConfig()
  
  try {
    const response = await fetch(`${emailServiceConfig.baseUrl}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${emailServiceConfig.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        to: [{ email: to }],
        subject,
        html: body
      })
    })

    if (!response.ok) {
      throw new Error(`Email service error: ${response.statusText}`)
    }
  } catch (error) {
    console.error('Failed to send email:', error)
  }
}

function getEmailServiceConfig(): EmailServiceConfig {
  return {
    provider: (process.env.REACT_APP_EMAIL_PROVIDER as 'mailchimp' | 'convertkit' | 'sendgrid') || 'mailchimp',
    apiKey: process.env.REACT_APP_EMAIL_API_KEY!,
    listId: process.env.REACT_APP_EMAIL_LIST_ID!,
    baseUrl: process.env.REACT_APP_EMAIL_BASE_URL!
  }
}

// Analytics and tracking functions
export async function trackEmailOpen(emailLogId: string): Promise<void> {
  await supabase
    .from('email_logs')
    .update({ 
      opened_at: new Date().toISOString(),
      status: 'delivered'
    })
    .eq('id', emailLogId)
}

export async function trackEmailClick(emailLogId: string): Promise<void> {
  await supabase
    .from('email_logs')
    .update({ 
      clicked_at: new Date().toISOString()
    })
    .eq('id', emailLogId)
}

export async function updateEngagementMetrics(leadId: string): Promise<void> {
  const { data: lead } = await supabase
    .from('leads')
    .select('engagement_metrics')
    .eq('id', leadId)
    .single()

  if (lead) {
    const metrics = lead.engagement_metrics
    metrics.emails_opened += 1
    metrics.last_engaged = new Date().toISOString()

    await supabase
      .from('leads')
      .update({ engagement_metrics: metrics })
      .eq('id', leadId)
  }
} 