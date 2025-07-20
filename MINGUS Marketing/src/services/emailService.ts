import { Database } from '../types/database'
import { logSecurityEvent } from '../utils/security'

type Lead = Database['public']['Tables']['leads']['Row']

// Email service interfaces
interface EmailServiceProvider {
  addSubscriber(lead: Lead): Promise<{ success: boolean; error?: string; subscriberId?: string }>
  updateSubscriber(lead: Lead): Promise<{ success: boolean; error?: string }>
  sendEmail(to: string, subject: string, body: string, campaignId?: string): Promise<{ success: boolean; error?: string; messageId?: string }>
  addTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }>
  removeTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }>
  getSubscriber(email: string): Promise<{ success: boolean; subscriber?: any; error?: string }>
  createCampaign(name: string, subject: string, body: string, segment?: string): Promise<{ success: boolean; campaignId?: string; error?: string }>
  sendCampaign(campaignId: string, segment?: string): Promise<{ success: boolean; error?: string }>
}

// Mailchimp implementation
class MailchimpService implements EmailServiceProvider {
  private apiKey: string
  private listId: string
  private serverPrefix: string
  private baseUrl: string

  constructor() {
    this.apiKey = process.env.REACT_APP_MAILCHIMP_API_KEY!
    this.listId = process.env.REACT_APP_MAILCHIMP_LIST_ID!
    this.serverPrefix = process.env.REACT_APP_MAILCHIMP_SERVER_PREFIX || 'us1'
    this.baseUrl = `https://${this.serverPrefix}.api.mailchimp.com/3.0`
  }

  private async makeRequest(endpoint: string, method: string = 'GET', data?: any): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      logSecurityEvent('email_service_error', { provider: 'mailchimp', endpoint, error: error.message })
      throw error
    }
  }

  async addSubscriber(lead: Lead): Promise<{ success: boolean; error?: string; subscriberId?: string }> {
    try {
      const data = {
        email_address: lead.email,
        status: 'subscribed',
        merge_fields: {
          FNAME: lead.name || '',
          SEGMENT: lead.segment,
          SCORE: lead.score,
          PRODUCT_TIER: lead.product_tier,
          PHONE: lead.phone || ''
        },
        tags: [lead.segment, lead.product_tier, 'assessment_completed']
      }

      const result = await this.makeRequest(`/lists/${this.listId}/members`, 'POST', data)
      
      return { success: true, subscriberId: result.id }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async updateSubscriber(lead: Lead): Promise<{ success: boolean; error?: string }> {
    try {
      const subscriberHash = this.getSubscriberHash(lead.email)
      const data = {
        merge_fields: {
          FNAME: lead.name || '',
          SEGMENT: lead.segment,
          SCORE: lead.score,
          PRODUCT_TIER: lead.product_tier,
          PHONE: lead.phone || ''
        }
      }

      await this.makeRequest(`/lists/${this.listId}/members/${subscriberHash}`, 'PATCH', data)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async sendEmail(to: string, subject: string, body: string, campaignId?: string): Promise<{ success: boolean; error?: string; messageId?: string }> {
    try {
      // For individual emails, we'll use the transactional API
      const data = {
        message: {
          to: [{ email: to }],
          subject,
          html: body
        }
      }

      const result = await this.makeRequest('/messages', 'POST', data)
      return { success: true, messageId: result._id }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async addTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
    try {
      const data = {
        tags: tags.map(tag => ({ name: tag, status: 'active' }))
      }

      await this.makeRequest(`/lists/${this.listId}/members/${subscriberId}`, 'PATCH', data)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async removeTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
    try {
      const data = {
        tags: tags.map(tag => ({ name: tag, status: 'inactive' }))
      }

      await this.makeRequest(`/lists/${this.listId}/members/${subscriberId}`, 'PATCH', data)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async getSubscriber(email: string): Promise<{ success: boolean; subscriber?: any; error?: string }> {
    try {
      const subscriberHash = this.getSubscriberHash(email)
      const result = await this.makeRequest(`/lists/${this.listId}/members/${subscriberHash}`)
      return { success: true, subscriber: result }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async createCampaign(name: string, subject: string, body: string, segment?: string): Promise<{ success: boolean; campaignId?: string; error?: string }> {
    try {
      const data = {
        type: 'regular',
        recipients: {
          list_id: this.listId,
          segment_opts: segment ? {
            match: 'all',
            conditions: [{
              condition_type: 'TextMerge',
              op: 'is',
              field: 'SEGMENT',
              value: segment
            }]
          } : undefined
        },
        settings: {
          subject_line: subject,
          title: name,
          from_name: 'Ratchet Money',
          reply_to: 'support@ratchetmoney.com'
        }
      }

      const result = await this.makeRequest('/campaigns', 'POST', data)
      
      // Set the campaign content
      await this.makeRequest(`/campaigns/${result.id}/content`, 'PUT', {
        html: body
      })

      return { success: true, campaignId: result.id }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async sendCampaign(campaignId: string, segment?: string): Promise<{ success: boolean; error?: string }> {
    try {
      await this.makeRequest(`/campaigns/${campaignId}/actions/send`, 'POST')
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  private getSubscriberHash(email: string): string {
    // Mailchimp uses MD5 hash of lowercase email
    return btoa(email.toLowerCase()).replace(/[^a-zA-Z0-9]/g, '')
  }
}

// ConvertKit implementation
class ConvertKitService implements EmailServiceProvider {
  private apiKey: string
  private formId: string
  private sequenceId: string
  private baseUrl: string

  constructor() {
    this.apiKey = process.env.REACT_APP_CONVERTKIT_API_KEY!
    this.formId = process.env.REACT_APP_CONVERTKIT_FORM_ID!
    this.sequenceId = process.env.REACT_APP_CONVERTKIT_SEQUENCE_ID!
    this.baseUrl = 'https://api.convertkit.com/v3'
  }

  private async makeRequest(endpoint: string, method: string = 'GET', data?: any): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Content-Type': 'application/json'
    }

    const params = new URLSearchParams()
    params.append('api_key', this.apiKey)

    try {
      const response = await fetch(`${url}?${params}`, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      logSecurityEvent('email_service_error', { provider: 'convertkit', endpoint, error: error.message })
      throw error
    }
  }

  async addSubscriber(lead: Lead): Promise<{ success: boolean; error?: string; subscriberId?: string }> {
    try {
      const data = {
        email: lead.email,
        first_name: lead.name || '',
        fields: {
          segment: lead.segment,
          score: lead.score.toString(),
          product_tier: lead.product_tier,
          phone: lead.phone || ''
        },
        tags: [lead.segment, lead.product_tier, 'assessment_completed']
      }

      const result = await this.makeRequest('/forms/' + this.formId + '/subscribe', 'POST', data)
      
      return { success: true, subscriberId: result.subscription.subscriber.id.toString() }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async updateSubscriber(lead: Lead): Promise<{ success: boolean; error?: string }> {
    try {
      const { subscriber } = await this.getSubscriber(lead.email)
      if (!subscriber) {
        return { success: false, error: 'Subscriber not found' }
      }

      const data = {
        first_name: lead.name || '',
        fields: {
          segment: lead.segment,
          score: lead.score.toString(),
          product_tier: lead.product_tier,
          phone: lead.phone || ''
        }
      }

      await this.makeRequest(`/subscribers/${subscriber.id}`, 'PUT', data)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async sendEmail(to: string, subject: string, body: string, campaignId?: string): Promise<{ success: boolean; error?: string; messageId?: string }> {
    try {
      // ConvertKit doesn't have a direct transactional email API
      // We'll need to use their broadcast feature or integrate with a transactional service
      const data = {
        subject: subject,
        content: body,
        recipients: [to]
      }

      const result = await this.makeRequest('/broadcasts', 'POST', data)
      return { success: true, messageId: result.broadcast.id.toString() }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async addTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
    try {
      for (const tag of tags) {
        await this.makeRequest(`/subscribers/${subscriberId}/tags`, 'POST', { tag })
      }
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async removeTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
    try {
      for (const tag of tags) {
        await this.makeRequest(`/subscribers/${subscriberId}/tags/${tag}`, 'DELETE')
      }
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async getSubscriber(email: string): Promise<{ success: boolean; subscriber?: any; error?: string }> {
    try {
      const result = await this.makeRequest(`/subscribers?email_address=${encodeURIComponent(email)}`)
      if (result.subscribers && result.subscribers.length > 0) {
        return { success: true, subscriber: result.subscribers[0] }
      }
      return { success: false, error: 'Subscriber not found' }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async createCampaign(name: string, subject: string, body: string, segment?: string): Promise<{ success: boolean; campaignId?: string; error?: string }> {
    try {
      const data = {
        name,
        subject,
        content: body
      }

      const result = await this.makeRequest('/broadcasts', 'POST', data)
      return { success: true, campaignId: result.broadcast.id.toString() }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async sendCampaign(campaignId: string, segment?: string): Promise<{ success: boolean; error?: string }> {
    try {
      await this.makeRequest(`/broadcasts/${campaignId}/send`, 'POST')
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
}

// SendGrid implementation
class SendGridService implements EmailServiceProvider {
  private apiKey: string
  private fromEmail: string
  private fromName: string
  private baseUrl: string

  constructor() {
    this.apiKey = process.env.REACT_APP_SENDGRID_API_KEY!
    this.fromEmail = process.env.REACT_APP_SENDGRID_FROM_EMAIL!
    this.fromName = process.env.REACT_APP_SENDGRID_FROM_NAME!
    this.baseUrl = 'https://api.sendgrid.com/v3'
  }

  private async makeRequest(endpoint: string, method: string = 'GET', data?: any): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.errors?.[0]?.message || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      logSecurityEvent('email_service_error', { provider: 'sendgrid', endpoint, error: error.message })
      throw error
    }
  }

  async addSubscriber(lead: Lead): Promise<{ success: boolean; error?: string; subscriberId?: string }> {
    try {
      const data = {
        contacts: [{
          email: lead.email,
          first_name: lead.name || '',
          custom_fields: {
            segment: lead.segment,
            score: lead.score,
            product_tier: lead.product_tier,
            phone: lead.phone || ''
          }
        }],
        list_ids: [process.env.REACT_APP_EMAIL_LIST_ID!]
      }

      const result = await this.makeRequest('/marketing/contacts', 'PUT', data)
      return { success: true, subscriberId: lead.email }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async updateSubscriber(lead: Lead): Promise<{ success: boolean; error?: string }> {
    try {
      const data = {
        contacts: [{
          email: lead.email,
          first_name: lead.name || '',
          custom_fields: {
            segment: lead.segment,
            score: lead.score,
            product_tier: lead.product_tier,
            phone: lead.phone || ''
          }
        }]
      }

      await this.makeRequest('/marketing/contacts', 'PATCH', data)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async sendEmail(to: string, subject: string, body: string, campaignId?: string): Promise<{ success: boolean; error?: string; messageId?: string }> {
    try {
      const data = {
        personalizations: [{
          to: [{ email: to }],
          subject
        }],
        from: {
          email: this.fromEmail,
          name: this.fromName
        },
        content: [{
          type: 'text/html',
          value: body
        }]
      }

      const result = await this.makeRequest('/mail/send', 'POST', data)
      return { success: true, messageId: result.headers?.['x-message-id'] }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async addTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
    try {
      // SendGrid uses segments instead of tags
      for (const tag of tags) {
        await this.makeRequest('/marketing/segments', 'POST', {
          name: tag,
          query_dsl: {
            conditions: [{
              field: 'email',
              operator: 'is',
              value: subscriberId
            }]
          }
        })
      }
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async removeTags(subscriberId: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
    try {
      // Remove from segments
      for (const tag of tags) {
        // Implementation depends on SendGrid's segment management
        // This is a simplified version
        return { success: true }
      }
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async getSubscriber(email: string): Promise<{ success: boolean; subscriber?: any; error?: string }> {
    try {
      const result = await this.makeRequest(`/marketing/contacts/search`, 'POST', {
        query: `email = '${email}'`
      })
      
      if (result.contact_count > 0) {
        return { success: true, subscriber: result.contacts[0] }
      }
      return { success: false, error: 'Subscriber not found' }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async createCampaign(name: string, subject: string, body: string, segment?: string): Promise<{ success: boolean; campaignId?: string; error?: string }> {
    try {
      const data = {
        title: name,
        subject: subject,
        sender_id: 1, // You'll need to set up a sender ID
        list_ids: [process.env.REACT_APP_EMAIL_LIST_ID!],
        html_content: body
      }

      const result = await this.makeRequest('/marketing/campaigns', 'POST', data)
      return { success: true, campaignId: result.id.toString() }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async sendCampaign(campaignId: string, segment?: string): Promise<{ success: boolean; error?: string }> {
    try {
      await this.makeRequest(`/marketing/campaigns/${campaignId}/send`, 'POST')
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
}

// Email service factory
export function createEmailService(): EmailServiceProvider {
  const provider = process.env.REACT_APP_EMAIL_PROVIDER || 'mailchimp'

  switch (provider) {
    case 'mailchimp':
      return new MailchimpService()
    case 'convertkit':
      return new ConvertKitService()
    case 'sendgrid':
      return new SendGridService()
    default:
      throw new Error(`Unsupported email provider: ${provider}`)
  }
}

// Email automation service
export class EmailAutomationService {
  private emailService: EmailServiceProvider

  constructor() {
    this.emailService = createEmailService()
  }

  async processLead(lead: Lead): Promise<{ success: boolean; error?: string }> {
    try {
      // Add or update subscriber
      const { subscriber } = await this.emailService.getSubscriber(lead.email)
      
      if (subscriber) {
        await this.emailService.updateSubscriber(lead)
      } else {
        await this.emailService.addSubscriber(lead)
      }

      // Add segment tags
      await this.emailService.addTags(lead.email, [lead.segment, lead.product_tier])

      // Trigger welcome sequence if new subscriber
      if (!subscriber) {
        await this.triggerWelcomeSequence(lead)
      }

      return { success: true }
    } catch (error) {
      logSecurityEvent('email_automation_error', { leadId: lead.id, error: error.message })
      return { success: false, error: error.message }
    }
  }

  async triggerWelcomeSequence(lead: Lead): Promise<void> {
    // This would integrate with your email sequence system
    // For now, we'll just send a welcome email
    const welcomeSubject = `Welcome to Ratchet Money, ${lead.name || 'there'}!`
    const welcomeBody = `
      <h1>Welcome to Ratchet Money!</h1>
      <p>Hi ${lead.name || 'there'},</p>
      <p>Thank you for joining us! Based on your assessment, you're a <strong>${lead.segment}</strong>.</p>
      <p>We'll be sending you personalized content to help you achieve your financial goals.</p>
    `

    await this.emailService.sendEmail(lead.email, welcomeSubject, welcomeBody)
  }

  async sendSegmentSpecificEmail(segment: string, subject: string, body: string): Promise<{ success: boolean; error?: string }> {
    try {
      const campaignId = await this.emailService.createCampaign(
        `Segment: ${segment}`,
        subject,
        body,
        segment
      )

      if (campaignId.campaignId) {
        await this.emailService.sendCampaign(campaignId.campaignId, segment)
      }

      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async trackEmailEvent(email: string, eventType: string, data?: any): Promise<void> {
    // This would integrate with your analytics system
    logSecurityEvent('email_event', { email, eventType, data })
  }
} 