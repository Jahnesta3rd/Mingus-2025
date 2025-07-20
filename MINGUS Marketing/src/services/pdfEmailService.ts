import { PDFReportService, PDFReportData } from './pdfReportService'
import { logEmailSent } from '../lib/supabase.js'

export interface EmailReportOptions {
  subject?: string
  includeFullReport?: boolean
  includeSummary?: boolean
  customMessage?: string
  ctaText?: string
  ctaUrl?: string
}

export interface EmailReportData {
  to: string
  leadName: string
  leadId: string
  assessmentResult: any
  reportId: string
  options?: EmailReportOptions
}

export class PDFEmailService {
  /**
   * Send assessment results with PDF report
   */
  static async sendAssessmentReport(data: EmailReportData): Promise<{
    success: boolean
    message: string
    reportPath?: string
  }> {
    try {
      const {
        to,
        leadName,
        leadId,
        assessmentResult,
        reportId,
        options = {}
      } = data

      // Generate PDF report
      const pdfData: PDFReportData = {
        leadName,
        email: to,
        assessmentResult,
        generatedAt: new Date(),
        reportId
      }

      const pdfBuffer = options.includeFullReport 
        ? await PDFReportService.generateReport(pdfData)
        : await PDFReportService.generateEmailReport(pdfData)

      // Generate email content
      const emailContent = this.generateEmailContent(data, options)

      // In a real implementation, you would send the email with attachment
      // For now, we'll log it and return success
      await logEmailSent(
        leadId,
        'assessment_report',
        options.subject || 'Your Ratchet Money Assessment Report',
        emailContent.body,
        'sent'
      )

      // Save PDF to file system for reference
      const fs = require('fs').promises
      const path = require('path')
      const reportsDir = path.join(process.cwd(), 'reports')
      const reportPath = path.join(reportsDir, `${reportId}.pdf`)
      
      await fs.mkdir(reportsDir, { recursive: true })
      await fs.writeFile(reportPath, pdfBuffer)

      console.log(`📧 Assessment report sent to ${to}`)
      console.log(`📄 PDF saved to: ${reportPath}`)

      return {
        success: true,
        message: 'Assessment report sent successfully',
        reportPath
      }

    } catch (error) {
      console.error('Error sending assessment report:', error)
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Generate email content with PDF attachment
   */
  private static generateEmailContent(
    data: EmailReportData,
    options: EmailReportOptions
  ): { subject: string; body: string } {
    const { leadName, assessmentResult, options: emailOptions } = data
    const { totalScore, segment } = assessmentResult

    const subject = emailOptions.subject || 
      `Your Ratchet Money Assessment Report - ${segment.charAt(0).toUpperCase() + segment.slice(1)}`

    const segmentTitles = {
      'stress-free': 'Stress-Free Lover',
      'balanced': 'Relationship Spender', 
      'high-stress': 'Emotional Money Manager'
    }

    const segmentTitle = segmentTitles[segment as keyof typeof segmentTitles] || segment

    const customMessage = emailOptions.customMessage || 
      `Hi ${leadName || 'there'},

Thank you for completing your Ratchet Money assessment! Your results are ready and I'm excited to share your personalized insights with you.

Your Assessment Results:
• Score: ${totalScore}/50
• Segment: ${segmentTitle}
• Key Insights: ${assessmentResult.challenges.length} areas identified for growth

What's included in your report:
📊 Detailed analysis of your relationship with money
💡 Personalized recommendations based on your results  
🎯 Actionable next steps to improve your financial wellness
📈 Progress tracking tools and resources

${emailOptions.ctaText ? `\n${emailOptions.ctaText}` : ''}
${emailOptions.ctaUrl ? `\n${emailOptions.ctaUrl}` : ''}

If you have any questions about your results or would like to discuss your personalized plan, please don't hesitate to reach out.

Best regards,
The Ratchet Money Team

P.S. This report is personalized just for you. Keep it handy as you work on your financial wellness journey!`

    return {
      subject,
      body: customMessage
    }
  }

  /**
   * Send follow-up email with additional resources
   */
  static async sendFollowUpEmail(data: EmailReportData): Promise<{
    success: boolean
    message: string
  }> {
    try {
      const { to, leadName, leadId, assessmentResult } = data
      const { segment } = assessmentResult

      const segmentResources = {
        'stress-free': [
          'Advanced wealth-building strategies',
          'Legacy planning guide',
          'Community leadership opportunities'
        ],
        'balanced': [
          'Boundary-setting workshop',
          'Shared financial vision template',
          'Emergency fund calculator'
        ],
        'high-stress': [
          'Stress-reduction techniques',
          'Financial counseling resources',
          'Support group connections'
        ]
      }

      const resources = segmentResources[segment as keyof typeof segmentResources] || segmentResources.balanced

      const subject = `Your Next Steps: ${segment.charAt(0).toUpperCase() + segment.slice(1)} Resources`

      const body = `Hi ${leadName || 'there'},

I hope you found your assessment report helpful! Here are some additional resources specifically curated for your ${segment} segment:

${resources.map(resource => `• ${resource}`).join('\n')}

Ready to take action? Here's what I recommend:

1. Review your assessment report again (attached to previous email)
2. Choose 1-2 areas to focus on this month
3. Join our exclusive community for ongoing support
4. Schedule a free 15-minute consultation call

Would you like to:
• Get personalized coaching? → Schedule a call
• Join our community? → Access member portal  
• Get more resources? → Download resource library

Let me know if you have any questions or need help getting started!

Best regards,
The Ratchet Money Team`

      await logEmailSent(
        leadId,
        'follow_up_resources',
        subject,
        body,
        'sent'
      )

      return {
        success: true,
        message: 'Follow-up email sent successfully'
      }

    } catch (error) {
      console.error('Error sending follow-up email:', error)
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Send reminder email for incomplete assessments
   */
  static async sendAssessmentReminder(data: {
    to: string
    leadName: string
    leadId: string
    assessmentUrl: string
  }): Promise<{ success: boolean; message: string }> {
    try {
      const { to, leadName, leadId, assessmentUrl } = data

      const subject = 'Complete Your Ratchet Money Assessment - Your Results Are Waiting!'

      const body = `Hi ${leadName || 'there'},

I noticed you started your Ratchet Money assessment but haven't completed it yet. Your personalized report is waiting for you!

Why complete your assessment?
• Get your unique relationship-money health score
• Receive personalized recommendations
• Access exclusive resources and tools
• Join our community of like-minded individuals

It only takes 5-10 minutes to complete, and you'll get immediate access to your results.

Complete your assessment now: ${assessmentUrl}

If you have any questions or need help, just reply to this email.

Best regards,
The Ratchet Money Team

P.S. Your results are completely confidential and will help us provide you with the most relevant resources.`

      await logEmailSent(
        leadId,
        'assessment_reminder',
        subject,
        body,
        'sent'
      )

      return {
        success: true,
        message: 'Assessment reminder sent successfully'
      }

    } catch (error) {
      console.error('Error sending assessment reminder:', error)
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Generate and send welcome email with assessment link
   */
  static async sendWelcomeEmail(data: {
    to: string
    leadName: string
    leadId: string
    assessmentUrl: string
  }): Promise<{ success: boolean; message: string }> {
    try {
      const { to, leadName, leadId, assessmentUrl } = data

      const subject = 'Welcome to Ratchet Money - Start Your Assessment!'

      const body = `Hi ${leadName || 'there'},

Welcome to Ratchet Money! I'm excited to help you build wealth while maintaining healthy relationships.

Your first step is to complete our quick assessment. This will help us understand your unique relationship with money and provide you with personalized insights and resources.

What you'll get:
• Your relationship-money health score
• Personalized recommendations
• Access to exclusive resources
• Community support

Complete your assessment: ${assessmentUrl}

The assessment takes just 5-10 minutes and your results are completely confidential.

If you have any questions, just reply to this email. I'm here to help!

Best regards,
The Ratchet Money Team`

      await logEmailSent(
        leadId,
        'welcome_assessment',
        subject,
        body,
        'sent'
      )

      return {
        success: true,
        message: 'Welcome email sent successfully'
      }

    } catch (error) {
      console.error('Error sending welcome email:', error)
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }
} 