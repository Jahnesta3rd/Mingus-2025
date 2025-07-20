import { supabase, supabaseAdmin, type Lead, type UserSegment, type ProductTier } from '../lib/supabase'
import { ASSESSMENT_QUESTIONS } from '../types/assessment-types'

export interface AssessmentSubmission {
  email: string
  firstName?: string
  phoneNumber?: string
  contactMethod: 'email' | 'phone' | 'both'
  betaInterest: 'very' | 'somewhat' | 'not'
  answers: Record<string, any>
  leadSource?: string
  utmData?: {
    source?: string
    medium?: string
    campaign?: string
    term?: string
    content?: string
  }
}

export interface AssessmentResult {
  totalScore: number
  segment: UserSegment
  productTier: ProductTier
  challenges: string[]
  recommendations: string[]
  leadId: string
}

export interface AssessmentError {
  code: string
  message: string
  field?: string
}

class AssessmentService {
  /**
   * Calculate assessment score and determine user segment
   */
  private calculateScore(answers: Record<string, any>): { score: number; segment: UserSegment; productTier: ProductTier } {
    let totalScore = 0

    // Calculate score based on answers
    Object.entries(answers).forEach(([questionId, answer]) => {
      const question = ASSESSMENT_QUESTIONS.find(q => q.id === questionId)
      if (!question) return

      if (question.type === 'radio' && typeof answer === 'string') {
        const option = question.options?.find(opt => opt.value === answer)
        if (option) {
          totalScore += option.points
        }
      } else if (question.type === 'checkbox' && Array.isArray(answer)) {
        answer.forEach((selectedValue: string) => {
          const option = question.options?.find(opt => opt.value === selectedValue)
          if (option) {
            totalScore += option.points
          }
        })
      } else if (question.type === 'rating' && typeof answer === 'object') {
        // Handle rating questions with sub-questions
        Object.values(answer).forEach((rating: any) => {
          if (typeof rating === 'number' && rating >= 1 && rating <= 5) {
            totalScore += rating
          }
        })
      }
    })

    // Determine segment based on score
    let segment: UserSegment
    let productTier: ProductTier

    if (totalScore <= 16) {
      segment = 'stress-free'
      productTier = 'Budget ($10)'
    } else if (totalScore <= 25) {
      segment = 'relationship-spender'
      productTier = 'Mid-tier ($20)'
    } else if (totalScore <= 35) {
      segment = 'emotional-manager'
      productTier = 'Mid-tier ($20)'
    } else {
      segment = 'crisis-mode'
      productTier = 'Professional ($50)'
    }

    return { score: totalScore, segment, productTier }
  }

  /**
   * Get segment-specific content
   */
  private getSegmentContent(segment: UserSegment) {
    const content = {
      'stress-free': {
        challenges: [
          'Maintaining this balance during life changes',
          'Helping others achieve similar harmony',
          'Taking your success to the next level'
        ],
        recommendations: [
          'Share your wisdom with others',
          'Consider becoming a mentor',
          'Explore advanced financial strategies'
        ]
      },
      'relationship-spender': {
        challenges: [
          'Setting healthy financial boundaries',
          'Balancing generosity with self-care',
          'Planning for long-term financial security'
        ],
        recommendations: [
          'Learn boundary-setting techniques',
          'Create a relationship spending budget',
          'Build an emergency fund for emotional times'
        ]
      },
      'emotional-manager': {
        challenges: [
          'Identifying emotional spending triggers',
          'Developing healthier coping mechanisms',
          'Building financial resilience'
        ],
        recommendations: [
          'Track your emotional spending patterns',
          'Create a 30-day spending pause strategy',
          'Build a support system for financial goals'
        ]
      },
      'crisis-mode': {
        challenges: [
          'Breaking the cycle of financial stress',
          'Creating immediate financial stability',
          'Building healthy relationship boundaries'
        ],
        recommendations: [
          'Implement emergency financial controls',
          'Seek professional financial counseling',
          'Create a 90-day recovery plan'
        ]
      }
    }

    return content[segment]
  }

  /**
   * Submit assessment and create lead
   */
  async submitAssessment(submission: AssessmentSubmission): Promise<AssessmentResult> {
    try {
      // Calculate score and segment
      const { score, segment, productTier } = this.calculateScore(submission.answers)
      const segmentContent = this.getSegmentContent(segment)

      // Check if lead already exists
      const { data: existingLead, error: checkError } = await supabase
        .from('leads')
        .select('id, email, assessment_completed')
        .eq('email', submission.email)
        .single()

      if (checkError && checkError.code !== 'PGRST116') {
        throw new Error(`Database error: ${checkError.message}`)
      }

      let leadId: string

      if (existingLead) {
        // Update existing lead
        const { data: updatedLead, error: updateError } = await supabase
          .from('leads')
          .update({
            segment,
            score,
            product_tier: productTier,
            assessment_completed: true,
            assessment_answers: submission.answers,
            assessment_completed_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            name: submission.firstName,
            phone: submission.phoneNumber,
            contact_method: submission.contactMethod,
            beta_interest: submission.betaInterest === 'very',
            lead_source: submission.leadSource,
            utm_source: submission.utmData?.source,
            utm_medium: submission.utmData?.medium,
            utm_campaign: submission.utmData?.campaign,
            utm_term: submission.utmData?.term,
            utm_content: submission.utmData?.content
          })
          .eq('id', existingLead.id)
          .select('id')
          .single()

        if (updateError) {
          throw new Error(`Failed to update lead: ${updateError.message}`)
        }

        leadId = updatedLead.id
      } else {
        // Create new lead
        const { data: newLead, error: insertError } = await supabase
          .from('leads')
          .insert({
            email: submission.email,
            name: submission.firstName,
            phone: submission.phoneNumber,
            segment,
            score,
            product_tier: productTier,
            assessment_completed: true,
            assessment_answers: submission.answers,
            assessment_completed_at: new Date().toISOString(),
            contact_method: submission.contactMethod,
            beta_interest: submission.betaInterest === 'very',
            lead_source: submission.leadSource,
            utm_source: submission.utmData?.source,
            utm_medium: submission.utmData?.medium,
            utm_campaign: submission.utmData?.campaign,
            utm_term: submission.utmData?.term,
            utm_content: submission.utmData?.content,
            confirmed: true // Auto-confirm since they completed assessment
          })
          .select('id')
          .single()

        if (insertError) {
          throw new Error(`Failed to create lead: ${insertError.message}`)
        }

        leadId = newLead.id
      }

      // Log assessment completion
      await this.logAssessmentCompletion(leadId, submission.email, score, segment)

      return {
        totalScore: score,
        segment,
        productTier,
        challenges: segmentContent.challenges,
        recommendations: segmentContent.recommendations,
        leadId
      }
    } catch (error) {
      console.error('Assessment submission error:', error)
      throw new Error(`Failed to submit assessment: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Log assessment completion for analytics
   */
  private async logAssessmentCompletion(leadId: string, email: string, score: number, segment: UserSegment) {
    try {
      // Log to email_logs for tracking
      await supabase
        .from('email_logs')
        .insert({
          lead_id: leadId,
          email_type: 'assessment_results',
          subject: 'Your Assessment Results Are Ready',
          body: `Assessment completed for ${email} with score ${score} and segment ${segment}`,
          status: 'sent'
        })

      // Track analytics event
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', 'assessment_completed', {
          event_category: 'engagement',
          event_label: segment,
          value: score
        })
      }
    } catch (error) {
      console.error('Failed to log assessment completion:', error)
      // Don't throw - this is not critical
    }
  }

  /**
   * Get assessment questions
   */
  async getAssessmentQuestions() {
    return ASSESSMENT_QUESTIONS
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
   * Update lead information
   */
  async updateLead(leadId: string, updates: Partial<Lead>): Promise<Lead> {
    try {
      const { data, error } = await supabase
        .from('leads')
        .update({
          ...updates,
          updated_at: new Date().toISOString()
        })
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
   * Get assessment statistics
   */
  async getAssessmentStats() {
    try {
      const { data, error } = await supabase
        .from('leads')
        .select('segment, score, created_at')
        .eq('assessment_completed', true)

      if (error) {
        throw new Error(`Failed to fetch stats: ${error.message}`)
      }

      const stats = {
        totalAssessments: data.length,
        averageScore: data.reduce((sum, lead) => sum + lead.score, 0) / data.length,
        segmentDistribution: data.reduce((acc, lead) => {
          acc[lead.segment] = (acc[lead.segment] || 0) + 1
          return acc
        }, {} as Record<string, number>),
        recentAssessments: data.filter(lead => {
          const createdAt = new Date(lead.created_at)
          const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
          return createdAt > oneWeekAgo
        }).length
      }

      return stats
    } catch (error) {
      console.error('Error fetching assessment stats:', error)
      throw new Error(`Failed to fetch stats: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
}

export const assessmentService = new AssessmentService() 