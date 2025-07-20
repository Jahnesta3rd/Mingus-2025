import puppeteer from 'puppeteer'
import { AssessmentResult } from '../api'

export interface PDFReportData {
  leadName: string
  email: string
  assessmentResult: AssessmentResult
  generatedAt: Date
  reportId: string
}

export interface PDFReportOptions {
  format?: 'A4' | 'Letter'
  margin?: {
    top: string
    right: string
    bottom: string
    left: string
  }
  printBackground?: boolean
  preferCSSPageSize?: boolean
}

export class PDFReportService {
  private static browser: puppeteer.Browser | null = null

  /**
   * Initialize the Puppeteer browser instance
   */
  static async initialize(): Promise<void> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: 'new',
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ]
      })
    }
  }

  /**
   * Close the browser instance
   */
  static async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close()
      this.browser = null
    }
  }

  /**
   * Generate HTML content for the PDF report
   */
  private static generateReportHTML(data: PDFReportData): string {
    const { leadName, assessmentResult, generatedAt } = data
    const { totalScore, segment, challenges } = assessmentResult

    // Get segment-specific content
    const segmentContent = this.getSegmentContent(segment, totalScore)
    
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Ratchet Money Assessment Report</title>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
          
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          
          body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #ffffff;
          }
          
          .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
          }
          
          .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 3px solid #dc2626;
          }
          
          .logo {
            font-size: 28px;
            font-weight: 700;
            color: #dc2626;
            margin-bottom: 10px;
          }
          
          .subtitle {
            font-size: 16px;
            color: #6b7280;
            font-weight: 400;
          }
          
          .personal-info {
            background: #f9fafb;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            border-left: 4px solid #dc2626;
          }
          
          .personal-info h2 {
            color: #dc2626;
            margin-bottom: 15px;
            font-size: 20px;
          }
          
          .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
          }
          
          .info-item {
            display: flex;
            flex-direction: column;
          }
          
          .info-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
          }
          
          .info-value {
            font-size: 16px;
            font-weight: 600;
            color: #1f2937;
          }
          
          .score-section {
            text-align: center;
            margin: 40px 0;
            padding: 30px;
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            border-radius: 16px;
            color: white;
          }
          
          .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 36px;
            font-weight: 700;
          }
          
          .segment-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
          }
          
          .segment-description {
            font-size: 16px;
            opacity: 0.9;
          }
          
          .content-section {
            margin: 40px 0;
          }
          
          .section-title {
            font-size: 22px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
          }
          
          .challenges-list {
            list-style: none;
            margin-bottom: 30px;
          }
          
          .challenge-item {
            background: #f3f4f6;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #dc2626;
            font-weight: 500;
          }
          
          .recommendations {
            background: #f0fdf4;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #bbf7d0;
          }
          
          .recommendations h3 {
            color: #166534;
            margin-bottom: 15px;
            font-size: 18px;
          }
          
          .recommendations ul {
            list-style: none;
          }
          
          .recommendations li {
            padding: 8px 0;
            padding-left: 20px;
            position: relative;
          }
          
          .recommendations li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #16a34a;
            font-weight: bold;
          }
          
          .next-steps {
            background: #fef3c7;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #fde68a;
            margin-top: 30px;
          }
          
          .next-steps h3 {
            color: #92400e;
            margin-bottom: 15px;
            font-size: 18px;
          }
          
          .cta-button {
            display: inline-block;
            background: #dc2626;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 15px;
          }
          
          .footer {
            margin-top: 50px;
            padding-top: 30px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
          }
          
          .page-break {
            page-break-before: always;
          }
          
          @media print {
            body {
              -webkit-print-color-adjust: exact;
              color-adjust: exact;
            }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <!-- Header -->
          <div class="header">
            <div class="logo">Ratchet Money</div>
            <div class="subtitle">Your Personalized Relationship-Money Health Report</div>
          </div>
          
          <!-- Personal Information -->
          <div class="personal-info">
            <h2>Assessment Summary</h2>
            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">Name</div>
                <div class="info-value">${leadName || 'Valued Customer'}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Assessment Date</div>
                <div class="info-value">${generatedAt.toLocaleDateString()}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Report ID</div>
                <div class="info-value">${data.reportId}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Total Questions</div>
                <div class="info-value">${challenges.length}</div>
              </div>
            </div>
          </div>
          
          <!-- Score and Segment -->
          <div class="score-section">
            <div class="score-circle">${totalScore}</div>
            <div class="segment-title">${segmentContent.title}</div>
            <div class="segment-description">${segmentContent.description}</div>
          </div>
          
          <!-- Key Challenges -->
          <div class="content-section">
            <h2 class="section-title">Your Key Relationship-Money Challenges</h2>
            <ul class="challenges-list">
              ${challenges.map(challenge => `
                <li class="challenge-item">${this.getChallengeDescription(challenge)}</li>
              `).join('')}
            </ul>
          </div>
          
          <!-- Recommendations -->
          <div class="recommendations">
            <h3>Personalized Recommendations</h3>
            <ul>
              ${segmentContent.recommendations.map(rec => `
                <li>${rec}</li>
              `).join('')}
            </ul>
          </div>
          
          <!-- Next Steps -->
          <div class="next-steps">
            <h3>Your Next Steps</h3>
            <p>Based on your assessment results, here's what we recommend:</p>
            <ul>
              <li>Review your personalized recommendations above</li>
              <li>Join our exclusive community for ongoing support</li>
              <li>Access your custom resource library</li>
              <li>Schedule a free consultation call</li>
            </ul>
            <a href="https://ratchetmoney.com/dashboard" class="cta-button">
              Access Your Dashboard
            </a>
          </div>
          
          <!-- Footer -->
          <div class="footer">
            <p>This report was generated on ${generatedAt.toLocaleString()}</p>
            <p>© 2024 Ratchet Money. All rights reserved.</p>
            <p>For questions about this report, contact us at support@ratchetmoney.com</p>
          </div>
        </div>
      </body>
      </html>
    `
  }

  /**
   * Get segment-specific content based on assessment results
   */
  private static getSegmentContent(segment: string, score: number) {
    const content = {
      'stress-free': {
        title: 'Stress-Free Lover',
        description: 'You have a healthy relationship with money and strong emotional intelligence.',
        recommendations: [
          'Continue your balanced approach to financial planning',
          'Share your wisdom with others in your network',
          'Consider advanced wealth-building strategies',
          'Focus on legacy planning and generational wealth'
        ]
      },
      'balanced': {
        title: 'Relationship Spender',
        description: 'You balance relationships and finances well, with room for optimization.',
        recommendations: [
          'Set clearer boundaries around money conversations',
          'Create a shared financial vision with loved ones',
          'Develop emergency fund strategies',
          'Practice mindful spending habits'
        ]
      },
      'high-stress': {
        title: 'Emotional Money Manager',
        description: 'You\'re aware of the challenges and ready to make positive changes.',
        recommendations: [
          'Start with small, manageable financial goals',
          'Seek professional financial counseling',
          'Practice stress-reduction techniques',
          'Build a support network for accountability'
        ]
      }
    }

    return content[segment as keyof typeof content] || content.balanced
  }

  /**
   * Get human-readable challenge descriptions
   */
  private static getChallengeDescription(challenge: string): string {
    const descriptions: Record<string, string> = {
      'financial_communication': 'Difficulty discussing money with partners or family',
      'emotional_spending': 'Making purchases based on emotions rather than needs',
      'relationship_conflicts': 'Money causing tension in relationships',
      'financial_planning': 'Lack of structured financial planning',
      'debt_management': 'Challenges with debt and credit management',
      'savings_habits': 'Difficulty building and maintaining savings',
      'investment_fear': 'Fear or uncertainty about investing',
      'financial_goals': 'Unclear or conflicting financial goals'
    }

    return descriptions[challenge] || challenge.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  /**
   * Generate PDF report
   */
  static async generateReport(
    data: PDFReportData,
    options: PDFReportOptions = {}
  ): Promise<Buffer> {
    await this.initialize()

    if (!this.browser) {
      throw new Error('Browser not initialized')
    }

    const page = await this.browser.newPage()
    
    try {
      // Generate HTML content
      const html = this.generateReportHTML(data)
      
      // Set content and wait for network idle
      await page.setContent(html, { waitUntil: 'networkidle0' })
      
      // Generate PDF
      const pdfBuffer = await page.pdf({
        format: options.format || 'A4',
        margin: options.margin || {
          top: '20mm',
          right: '20mm',
          bottom: '20mm',
          left: '20mm'
        },
        printBackground: options.printBackground !== false,
        preferCSSPageSize: options.preferCSSPageSize || false
      })

      return pdfBuffer
    } finally {
      await page.close()
    }
  }

  /**
   * Generate and save PDF report to file system
   */
  static async generateAndSaveReport(
    data: PDFReportData,
    filePath: string,
    options: PDFReportOptions = {}
  ): Promise<string> {
    const fs = require('fs').promises
    const path = require('path')
    
    // Ensure directory exists
    const dir = path.dirname(filePath)
    await fs.mkdir(dir, { recursive: true })
    
    // Generate PDF
    const pdfBuffer = await this.generateReport(data, options)
    
    // Save to file
    await fs.writeFile(filePath, pdfBuffer)
    
    return filePath
  }

  /**
   * Generate PDF and return as base64 string
   */
  static async generateReportAsBase64(
    data: PDFReportData,
    options: PDFReportOptions = {}
  ): Promise<string> {
    const pdfBuffer = await this.generateReport(data, options)
    return pdfBuffer.toString('base64')
  }

  /**
   * Generate a simple email-friendly PDF
   */
  static async generateEmailReport(
    data: PDFReportData,
    options: PDFReportOptions = {}
  ): Promise<Buffer> {
    // Modify data for email version (shorter, more focused)
    const emailData = {
      ...data,
      assessmentResult: {
        ...data.assessmentResult,
        challenges: data.assessmentResult.challenges.slice(0, 3) // Top 3 challenges only
      }
    }

    return await this.generateReport(emailData, {
      ...options,
      format: 'A4',
      margin: {
        top: '15mm',
        right: '15mm',
        bottom: '15mm',
        left: '15mm'
      }
    })
  }
} 