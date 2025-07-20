import { supabase, supabaseAdmin, type Lead, type UserSegment, type ProductTier } from '../lib/supabase'

export interface CreateLeadData {
  email: string
  name?: string
  phone?: string
  leadSource?: string
  utmData?: {
    source?: string
    medium?: string
    campaign?: string
    term?: string
    content?: string
  }
  contactMethod?: 'email' | 'phone' | 'both'
  betaInterest?: boolean
}

export interface UpdateLeadData {
  name?: string
  phone?: string
  segment?: UserSegment
  score?: number
  productTier?: ProductTier
  assessmentCompleted?: boolean
  assessmentAnswers?: Record<string, any>
  emailPreferences?: Record<string, any>
  status?: string
  tags?: string[]
  contactMethod?: 'email' | 'phone' | 'both'
  betaInterest?: boolean
  lead_source?: string
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
  utm_term?: string
  utm_content?: string
}

export interface LeadAnalytics {
  totalLeads: number
  confirmedLeads: number
  assessmentCompletions: number
  segmentDistribution: Record<string, number>
  averageScore: number
  conversionRate: number
  recentLeads: number
  topLeadSources: Array<{ source: string; count: number }>
}

class LeadService {
  /**
   * Create a new lead
   */
  async createLead(leadData: CreateLeadData): Promise<Lead> {
    try {
      // Check if lead already exists
      const { data: existingLead, error: checkError } = await supabase
        .from('leads')
        .select('id, email, confirmed, name, phone')
        .eq('email', leadData.email)
        .single()

      if (checkError && checkError.code !== 'PGRST116') {
        throw new Error(`Database error: ${checkError.message}`)
      }

      if (existingLead) {
        // Update existing lead with new information
        const { data: updatedLead, error: updateError } = await supabase
          .from('leads')
          .update({
            name: leadData.name || existingLead.name,
            phone: leadData.phone || existingLead.phone,
            lead_source: leadData.leadSource,
            utm_source: leadData.utmData?.source,
            utm_medium: leadData.utmData?.medium,
            utm_campaign: leadData.utmData?.campaign,
            utm_term: leadData.utmData?.term,
            utm_content: leadData.utmData?.content,
            contact_method: leadData.contactMethod || 'email',
            beta_interest: leadData.betaInterest || false,
            updated_at: new Date().toISOString()
          })
          .eq('id', existingLead.id)
          .select('*')
          .single()

        if (updateError) {
          throw new Error(`Failed to update lead: ${updateError.message}`)
        }

        return updatedLead
      }

      // Create new lead
      const { data: newLead, error: insertError } = await supabase
        .from('leads')
        .insert({
          email: leadData.email,
          name: leadData.name,
          phone: leadData.phone,
          lead_source: leadData.leadSource,
          utm_source: leadData.utmData?.source,
          utm_medium: leadData.utmData?.medium,
          utm_campaign: leadData.utmData?.campaign,
          utm_term: leadData.utmData?.term,
          utm_content: leadData.utmData?.content,
          contact_method: leadData.contactMethod || 'email',
          beta_interest: leadData.betaInterest || false,
          status: 'active'
        })
        .select('*')
        .single()

      if (insertError) {
        throw new Error(`Failed to create lead: ${insertError.message}`)
      }

      // Track lead creation
      this.trackLeadCreation(newLead)

      return newLead
    } catch (error) {
      console.error('Error creating lead:', error)
      throw new Error(`Failed to create lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get lead by email
   */
  async getLeadByEmail(email: string): Promise<Lead | null> {
    try {
      const { data, error } = await supabase
        .from('leads')
        .select('*')
        .eq('email', email)
        .single()

      if (error) {
        if (error.code === 'PGRST116') {
          return null // Lead not found
        }
        throw new Error(`Database error: ${error.message}`)
      }

      return data
    } catch (error) {
      console.error('Error fetching lead:', error)
      throw new Error(`Failed to fetch lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get lead by ID
   */
  async getLeadById(leadId: string): Promise<Lead | null> {
    try {
      const { data, error } = await supabase
        .from('leads')
        .select('*')
        .eq('id', leadId)
        .single()

      if (error) {
        if (error.code === 'PGRST116') {
          return null // Lead not found
        }
        throw new Error(`Database error: ${error.message}`)
      }

      return data
    } catch (error) {
      console.error('Error fetching lead:', error)
      throw new Error(`Failed to fetch lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Update lead information
   */
  async updateLead(leadId: string, updates: UpdateLeadData): Promise<Lead> {
    try {
      const updateData: any = {
        ...updates,
        updated_at: new Date().toISOString()
      }

      // Handle assessment completion
      if (updates.assessmentCompleted) {
        updateData.assessment_completed_at = new Date().toISOString()
      }

      const { data, error } = await supabase
        .from('leads')
        .update(updateData)
        .eq('id', leadId)
        .select('*')
        .single()

      if (error) {
        throw new Error(`Failed to update lead: ${error.message}`)
      }

      return data
    } catch (error) {
      console.error('Error updating lead:', error)
      throw new Error(`Failed to update lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Confirm lead email
   */
  async confirmLead(leadId: string): Promise<Lead> {
    try {
      const { data, error } = await supabase
        .from('leads')
        .update({
          confirmed: true,
          confirmed_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .eq('id', leadId)
        .select('*')
        .single()

      if (error) {
        throw new Error(`Failed to confirm lead: ${error.message}`)
      }

      return data
    } catch (error) {
      console.error('Error confirming lead:', error)
      throw new Error(`Failed to confirm lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get lead analytics
   */
  async getLeadAnalytics(timeframe: 'day' | 'week' | 'month' | 'all' = 'all'): Promise<LeadAnalytics> {
    try {
      let dateFilter = ''
      if (timeframe !== 'all') {
        const now = new Date()
        let startDate: Date

        switch (timeframe) {
          case 'day':
            startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000)
            break
          case 'week':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
            break
          case 'month':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
            break
        }

        dateFilter = `created_at.gte.${startDate.toISOString()}`
      }

      // Get all leads with optional date filter
      const { data: leads, error } = await supabase
        .from('leads')
        .select('*')
        .filter(dateFilter ? dateFilter : 'id', 'neq', '')
        .order('created_at', { ascending: false })

      if (error) {
        throw new Error(`Failed to fetch leads: ${error.message}`)
      }

      // Calculate analytics
      const totalLeads = leads.length
      const confirmedLeads = leads.filter(lead => lead.confirmed).length
      const assessmentCompletions = leads.filter(lead => lead.assessment_completed).length
      const averageScore = leads
        .filter(lead => lead.assessment_completed && lead.score)
        .reduce((sum, lead) => sum + lead.score, 0) / Math.max(assessmentCompletions, 1)

      // Segment distribution
      const segmentDistribution = leads.reduce((acc, lead) => {
        if (lead.segment) {
          acc[lead.segment] = (acc[lead.segment] || 0) + 1
        }
        return acc
      }, {} as Record<string, number>)

      // Lead sources
      const leadSources = leads.reduce((acc, lead) => {
        const source = lead.lead_source || 'direct'
        acc[source] = (acc[source] || 0) + 1
        return acc
      }, {} as Record<string, number>)

      const topLeadSources = Object.entries(leadSources)
        .map(([source, count]) => ({ source, count: count as number }))
        .sort((a, b) => (b.count as number) - (a.count as number))
        .slice(0, 5)

      // Recent leads (last 7 days)
      const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      const recentLeads = leads.filter(lead => new Date(lead.created_at) > oneWeekAgo).length

      // Conversion rate (confirmed leads / total leads)
      const conversionRate = totalLeads > 0 ? (confirmedLeads / totalLeads) * 100 : 0

      return {
        totalLeads,
        confirmedLeads,
        assessmentCompletions,
        segmentDistribution,
        averageScore: Math.round(averageScore * 100) / 100,
        conversionRate: Math.round(conversionRate * 100) / 100,
        recentLeads,
        topLeadSources
      }
    } catch (error) {
      console.error('Error fetching lead analytics:', error)
      throw new Error(`Failed to fetch analytics: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Search leads
   */
  async searchLeads(query: string, filters?: Record<string, any>): Promise<Lead[]> {
    try {
      let supabaseQuery = supabase
        .from('leads')
        .select('*')

      // Apply text search
      if (query) {
        supabaseQuery = supabaseQuery.or(`email.ilike.%${query}%,name.ilike.%${query}%`)
      }

      // Apply filters
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            supabaseQuery = supabaseQuery.eq(key, value)
          }
        })
      }

      const { data, error } = await supabaseQuery.order('created_at', { ascending: false })

      if (error) {
        throw new Error(`Failed to search leads: ${error.message}`)
      }

      return data || []
    } catch (error) {
      console.error('Error searching leads:', error)
      throw new Error(`Failed to search leads: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Delete lead (soft delete)
   */
  async deleteLead(leadId: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('leads')
        .update({
          status: 'deleted',
          updated_at: new Date().toISOString()
        })
        .eq('id', leadId)

      if (error) {
        throw new Error(`Failed to delete lead: ${error.message}`)
      }
    } catch (error) {
      console.error('Error deleting lead:', error)
      throw new Error(`Failed to delete lead: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Track lead creation for analytics
   */
  private trackLeadCreation(lead: Lead) {
    try {
      // Track with Google Analytics if available
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', 'lead_created', {
          event_category: 'engagement',
          event_label: lead.lead_source || 'direct',
          value: 1
        })
      }

      // Track with Facebook Pixel if available
      if (typeof window !== 'undefined' && (window as any).fbq) {
        (window as any).fbq('track', 'Lead', {
          content_name: 'Email Signup',
          content_category: 'Lead Generation'
        })
      }
    } catch (error) {
      console.error('Error tracking lead creation:', error)
      // Don't throw - tracking is not critical
    }
  }

  /**
   * Export leads data
   */
  async exportLeads(format: 'csv' | 'json' = 'csv'): Promise<string> {
    try {
      const { data: leads, error } = await supabase
        .from('leads')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) {
        throw new Error(`Failed to fetch leads: ${error.message}`)
      }

      if (format === 'json') {
        return JSON.stringify(leads, null, 2)
      }

      // CSV format
      const headers = [
        'ID',
        'Email',
        'Name',
        'Phone',
        'Segment',
        'Score',
        'Product Tier',
        'Confirmed',
        'Assessment Completed',
        'Created At',
        'Lead Source',
        'UTM Source',
        'UTM Medium',
        'UTM Campaign'
      ]

      const csvRows = [
        headers.join(','),
        ...leads.map(lead => [
          lead.id,
          lead.email,
          lead.name || '',
          lead.phone || '',
          lead.segment || '',
          lead.score || '',
          lead.product_tier || '',
          lead.confirmed ? 'Yes' : 'No',
          lead.assessment_completed ? 'Yes' : 'No',
          lead.created_at,
          lead.lead_source || '',
          lead.utm_source || '',
          lead.utm_medium || '',
          lead.utm_campaign || ''
        ].join(','))
      ]

      return csvRows.join('\n')
    } catch (error) {
      console.error('Error exporting leads:', error)
      throw new Error(`Failed to export leads: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
}

export const leadService = new LeadService() 