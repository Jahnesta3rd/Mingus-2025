// server.js - Updated backend with PDF generation endpoints

const express = require('express')
const cors = require('cors')
const path = require('path')
const fs = require('fs')
const { Resend } = require('resend')
const { createClient } = require('@supabase/supabase-js')
const { generatePersonalizedPDF, cleanupOldPDFs } = require('./pdfGenerator.js')
require('dotenv').config()

const app = express()
const port = process.env.PORT || 3001

// Initialize services
const resend = new Resend(process.env.RESEND_API_KEY)
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)

// Middleware
app.use(cors())
app.use(express.json({ limit: '10mb' }))

// Ensure tmp directory exists
const tmpDir = path.join(__dirname, 'tmp')
if (!fs.existsSync(tmpDir)) {
  fs.mkdirSync(tmpDir, { recursive: true })
}

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    services: {
      pdf: 'available',
      email: 'available',
      database: 'available'
    }
  })
})

// **NEW: Generate PDF Report Endpoint**
app.post('/api/generate-report', async (req, res) => {
  try {
    const { leadId, email } = req.body

    if (!leadId && !email) {
      return res.status(400).json({ 
        success: false, 
        error: 'Either leadId or email is required' 
      })
    }

    console.log('PDF generation request:', { leadId, email })

    // Get lead data from Supabase
    let query = supabase.from('leads').select('*')
    
    if (leadId) {
      query = query.eq('id', leadId)
    } else {
      query = query.eq('email', email)
    }
    
    const { data: leadData, error: leadError } = await query.single()

    if (leadError) {
      console.error('Lead lookup error:', leadError)
      return res.status(404).json({ 
        success: false, 
        error: 'Lead not found' 
      })
    }

    if (!leadData.assessment_completed) {
      return res.status(400).json({
        success: false,
        error: 'Assessment not completed yet'
      })
    }

    console.log('Found lead data:', { 
      id: leadData.id, 
      email: leadData.email, 
      segment: leadData.segment,
      score: leadData.score 
    })

    // Generate PDF
    const pdfResult = await generatePersonalizedPDF(leadData)

    if (!pdfResult.success) {
      console.error('PDF generation failed:', pdfResult.error)
      return res.status(500).json({ 
        success: false, 
        error: pdfResult.error 
      })
    }

    // Store PDF info in database (optional table)
    try {
      await supabase
        .from('email_logs')
        .insert([{
          lead_id: leadData.id,
          email_type: 'pdf_generated',
          subject: 'PDF Report Generated',
          body: `PDF report generated: ${pdfResult.filename}`,
          status: 'sent',
          external_id: pdfResult.filename
        }])
    } catch (dbError) {
      console.error('Database logging error:', dbError)
      // Don't fail the request if logging fails
    }

    console.log('PDF generated successfully:', pdfResult.filename)

    res.json({
      success: true,
      downloadUrl: pdfResult.downloadUrl,
      filename: pdfResult.filename,
      message: 'PDF report generated successfully'
    })

  } catch (error) {
    console.error('Error in PDF generation endpoint:', error)
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    })
  }
})

// **NEW: Download PDF Endpoint**
app.get('/api/download/:filename', (req, res) => {
  try {
    const { filename } = req.params
    
    // Security: Only allow PDF files and sanitize filename
    if (!filename.endsWith('.pdf') || filename.includes('..') || filename.includes('/')) {
      return res.status(400).json({ error: 'Invalid filename' })
    }

    const filepath = path.join(tmpDir, filename)

    if (!fs.existsSync(filepath)) {
      return res.status(404).json({ error: 'File not found' })
    }

    // Set appropriate headers
    res.setHeader('Content-Type', 'application/pdf')
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`)
    res.setHeader('Cache-Control', 'private, max-age=3600') // Cache for 1 hour

    // Stream the file
    const fileStream = fs.createReadStream(filepath)
    fileStream.pipe(res)

    fileStream.on('error', (err) => {
      console.error('File stream error:', err)
      if (!res.headersSent) {
        res.status(500).json({ error: 'Download failed' })
      }
    })

  } catch (error) {
    console.error('Error in download endpoint:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// **ENHANCED: Send confirmation email (existing endpoint)**
app.post('/api/send-confirmation', async (req, res) => {
  try {
    const { email, leadId } = req.body

    if (!email || !leadId) {
      return res.status(400).json({ 
        success: false, 
        error: 'Email and leadId are required' 
      })
    }

    // Generate confirmation link
    const confirmationLink = `${process.env.FRONTEND_URL}?confirm=true&email=${encodeURIComponent(email)}`
    
    // Send email via Resend
    const { data: emailData, error: emailError } = await resend.emails.send({
      from: 'MINGUS <noreply@yourdomain.com>',
      to: [email],
      subject: 'Confirm Your Email - Start Your Money & Relationship Assessment',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1>Welcome to MINGUS</h1>
            <p>Your Personal Finance & Relationship Companion</p>
          </div>
          <div style="padding: 30px; background: white; border: 1px solid #ddd;">
            <h2>Hi there! 👋</h2>
            <p>Thanks for signing up for your personalized <strong>Money & Relationship Assessment</strong>.</p>
            <p>Click the button below to confirm your email and start your assessment:</p>
            <div style="text-align: center; margin: 20px 0;">
              <a href="${confirmationLink}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Confirm Email & Start Assessment
              </a>
            </div>
            <p><strong>What you'll discover:</strong></p>
            <ul>
              <li>Your unique money personality type</li>
              <li>How relationships influence your spending</li>
              <li>Personalized strategies for financial success</li>
              <li>A detailed action plan (FREE PDF report)</li>
            </ul>
            <p>Best regards,<br>The MINGUS Team</p>
          </div>
        </div>
      `,
    })

    if (emailError) {
      console.error('Resend error:', emailError)
      return res.status(500).json({ 
        success: false, 
        error: emailError.message 
      })
    }

    // Log email in Supabase
    await supabase
      .from('email_logs')
      .insert([{
        lead_id: leadId,
        email_type: 'confirmation',
        subject: 'Confirm Your Email - Start Your Money & Relationship Assessment',
        body: 'Confirmation email sent',
        external_id: emailData.id,
        status: 'sent'
      }])

    res.json({ 
      success: true, 
      emailId: emailData.id,
      message: 'Confirmation email sent successfully'
    })

  } catch (error) {
    console.error('Error sending confirmation email:', error)
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error' 
    })
  }
})

// **ENHANCED: Send assessment results with PDF (existing endpoint enhanced)**
app.post('/api/send-results', async (req, res) => {
  try {
    const { email, userSegment, score, firstName, leadId, pdfDownloadUrl } = req.body

    if (!email || !userSegment || score === undefined || !leadId) {
      return res.status(400).json({ 
        success: false, 
        error: 'Missing required fields' 
      })
    }

    // Generate PDF first if not provided
    let downloadUrl = pdfDownloadUrl
    if (!downloadUrl) {
      console.log('Generating PDF for results email...')
      const pdfResult = await generatePersonalizedPDF({ 
        email, 
        segment: userSegment, 
        score, 
        first_name: firstName,
        id: leadId 
      })
      
      if (pdfResult.success) {
        downloadUrl = pdfResult.downloadUrl
      } else {
        console.error('PDF generation failed for email:', pdfResult.error)
      }
    }

    // Segment-specific email content
    const emailContent = {
      'stress-free': {
        subject: '🎉 Congratulations! You\'re a Stress-Free Lover',
        title: 'Stress-Free Lover ✨',
        description: 'You have a healthy and balanced relationship with money and relationships!',
        color: '#4CAF50'
      },
      'relationship-spender': {
        subject: '💝 You\'re a Relationship Spender - Here\'s How to Find Balance',
        title: 'Relationship Spender 💝',
        description: 'You value relationships deeply and show love through spending.',
        color: '#FF9800'
      },
      'emotional-manager': {
        subject: '🧠 You\'re an Emotional Money Manager - Let\'s Build Better Habits',
        title: 'Emotional Money Manager 🧠',
        description: 'Your emotions significantly influence spending, but you can build better habits.',
        color: '#9C27B0'
      },
      'crisis-mode': {
        subject: '🚨 You\'re in Crisis Mode - Let\'s Get You Back in Control',
        title: 'Crisis Mode 🚨',
        description: 'Your financial stress is high, but help is available.',
        color: '#F44336'
      }
    }

    const content = emailContent[userSegment] || emailContent['stress-free']
    const signupLink = `${process.env.FRONTEND_URL}/signup?segment=${userSegment}&email=${encodeURIComponent(email)}&utm_source=email&utm_medium=results&utm_campaign=assessment`

    // Send email via Resend
    const { data: emailData, error: emailError } = await resend.emails.send({
      from: 'MINGUS <results@yourdomain.com>',
      to: [email],
      subject: content.subject,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: linear-gradient(135deg, ${content.color}, ${content.color}dd); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1>🎉 Assessment Complete!</h1>
            <p>Your personalized results are ready</p>
          </div>
          <div style="padding: 30px; background: white; border: 1px solid #ddd;">
            <h2>Hi ${firstName || 'there'}!</h2>
            
            <div style="background: ${content.color}15; border: 2px solid ${content.color}; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
              <h3 style="color: ${content.color}; margin-bottom: 10px;">Your Type: ${content.title}</h3>
              <p style="font-size: 18px; font-weight: bold; color: ${content.color};">Score: ${score}/100</p>
              <p style="margin: 0;">${content.description}</p>
            </div>
            
            ${downloadUrl ? `
            <div style="background: #f0fff4; border: 2px solid #68d391; padding: 25px; border-radius: 12px; text-align: center; margin: 25px 0;">
              <div style="font-size: 24px; margin-bottom: 10px;">📄</div>
              <h3 style="color: #2f855a; margin-bottom: 15px;">Your FREE Personal Action Plan</h3>
              <p style="color: #2f855a; margin-bottom: 20px;">
                We've created a detailed 10-page report with your personalized strategies, 
                emergency toolkit, and 30-day action plan.
              </p>
              <a href="${downloadUrl}" style="background: #38a169; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                📥 Download Your Free Report
              </a>
            </div>
            ` : ''}
            
            <p><strong>What's next?</strong></p>
            <p>Your assessment shows you would benefit most from our <strong>${userSegment === 'stress-free' ? 'Budget ($10)' : userSegment === 'crisis-mode' ? 'Professional ($50)' : 'Mid-tier ($20)'}</strong> plan.</p>
            
            <div style="text-align: center; margin: 30px 0;">
              <a href="${signupLink}" style="background: ${content.color}; color: white; padding: 18px 35px; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 16px; display: inline-block;">
                🚀 Get Your Personal Finance Plan
              </a>
            </div>
            
            <p style="font-size: 14px; color: #666; text-align: center;">
              Questions? Just reply to this email - we're here to help!
            </p>
            
            <p>Best regards,<br>The MINGUS Team</p>
          </div>
        </div>
      `,
    })

    if (emailError) {
      console.error('Resend error:', emailError)
      return res.status(500).json({ 
        success: false, 
        error: emailError.message 
      })
    }

    // Log email in Supabase
    await supabase
      .from('email_logs')
      .insert([{
        lead_id: leadId,
        email_type: 'assessment_results',
        subject: content.subject,
        body: 'Assessment results email with PDF',
        external_id: emailData.id,
        status: 'sent'
      }])

    res.json({ 
      success: true, 
      emailId: emailData.id,
      pdfDownloadUrl: downloadUrl,
      message: 'Results email sent successfully'
    })

  } catch (error) {
    console.error('Error sending results email:', error)
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error' 
    })
  }
})

// **NEW: Bulk PDF generation for existing leads**
app.post('/api/generate-bulk-pdfs', async (req, res) => {
  try {
    const { limit = 50 } = req.body // Process in batches

    // Get completed assessments without PDFs
    const { data: leads, error } = await supabase
      .from('leads')
      .select('*')
      .eq('assessment_completed', true)
      .limit(limit)

    if (error) {
      return res.status(500).json({ success: false, error: error.message })
    }

    const results = []
    
    for (const lead of leads) {
      try {
        const pdfResult = await generatePersonalizedPDF(lead)
        results.push({
          leadId: lead.id,
          email: lead.email,
          success: pdfResult.success,
          filename: pdfResult.filename,
          error: pdfResult.error
        })
      } catch (error) {
        results.push({
          leadId: lead.id,
          email: lead.email,
          success: false,
          error: error.message
        })
      }
    }

    res.json({
      success: true,
      processed: leads.length,
      results
    })

  } catch (error) {
    console.error('Error in bulk PDF generation:', error)
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error' 
    })
  }
})

// **NEW: PDF Analytics Endpoint**
app.get('/api/analytics/pdfs', async (req, res) => {
  try {
    const { days = 30 } = req.query
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - parseInt(days))

    const { data, error } = await supabase
      .from('email_logs')
      .select('*')
      .eq('email_type', 'pdf_generated')
      .gte('sent_at', startDate.toISOString())

    if (error) throw error

    const analytics = {
      totalGenerated: data.length,
      byDay: {},
      bySegment: {}
    }

    data.forEach(log => {
      const day = new Date(log.sent_at).toISOString().split('T')[0]
      analytics.byDay[day] = (analytics.byDay[day] || 0) + 1
    })

    res.json({ success: true, data: analytics })

  } catch (error) {
    console.error('Error fetching PDF analytics:', error)
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error' 
    })
  }
})

// Cleanup old PDFs on startup and every 6 hours
cleanupOldPDFs()
setInterval(cleanupOldPDFs, 6 * 60 * 60 * 1000)

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error)
  res.status(500).json({ 
    success: false, 
    error: 'Internal server error' 
  })
})

app.listen(port, () => {
  console.log(`🚀 MINGUS API server running on port ${port}`)
  console.log(`📄 PDF generation available at /api/generate-report`)
  console.log(`📥 PDF downloads available at /api/download/:filename`)
})

module.exports = app 