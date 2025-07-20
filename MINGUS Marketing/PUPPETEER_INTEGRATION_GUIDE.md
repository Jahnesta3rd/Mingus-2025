# Puppeteer PDF Report Integration Guide

## Overview

This guide explains how to integrate Puppeteer for generating and sending personalized PDF reports from your Ratchet Money assessment results. The integration includes PDF generation, email delivery, and automated follow-up sequences.

## What's Included

- **PDF Report Generation**: Personalized reports based on assessment results
- **Email Integration**: Automatic email delivery with PDF attachments
- **Follow-up Sequences**: Automated email sequences with additional resources
- **Report Storage**: Local file system storage for generated reports
- **Customization**: Fully customizable report templates and styling

## Quick Start

### 1. Installation

```bash
npm install puppeteer
```

### 2. Basic Usage

```javascript
import { PDFReportService } from '../services/pdfReportService'
import { PDFEmailService } from '../services/pdfEmailService'

// Generate a PDF report
const pdfBuffer = await PDFReportService.generateReport({
  leadName: 'John Doe',
  email: 'john@example.com',
  assessmentResult: {
    totalScore: 25,
    segment: 'balanced',
    challenges: ['financial_communication', 'emotional_spending']
  },
  generatedAt: new Date(),
  reportId: 'report-123'
})

// Send report via email
const result = await PDFEmailService.sendAssessmentReport({
  to: 'john@example.com',
  leadName: 'John Doe',
  leadId: 'lead-123',
  assessmentResult: {
    totalScore: 25,
    segment: 'balanced',
    challenges: ['financial_communication', 'emotional_spending']
  },
  reportId: 'report-123'
})
```

## PDF Report Service

### Features

- **Personalized Content**: Reports tailored to assessment results
- **Professional Design**: Clean, modern PDF layout
- **Multiple Formats**: Full reports and email-friendly summaries
- **Customizable**: Easy to modify templates and styling

### Usage Examples

#### Generate Full Report

```javascript
const pdfData = {
  leadName: 'Jane Smith',
  email: 'jane@example.com',
  assessmentResult: {
    totalScore: 35,
    segment: 'high-stress',
    challenges: ['financial_planning', 'debt_management', 'savings_habits']
  },
  generatedAt: new Date(),
  reportId: 'report-' + Date.now()
}

const pdfBuffer = await PDFReportService.generateReport(pdfData)
```

#### Generate Email-Friendly Report

```javascript
const pdfBuffer = await PDFReportService.generateEmailReport(pdfData)
```

#### Save Report to File

```javascript
const filePath = await PDFReportService.generateAndSaveReport(
  pdfData,
  './reports/jane-smith-report.pdf'
)
```

#### Generate Base64 String

```javascript
const base64String = await PDFReportService.generateReportAsBase64(pdfData)
```

### Customization Options

```javascript
const options = {
  format: 'A4', // or 'Letter'
  margin: {
    top: '20mm',
    right: '20mm',
    bottom: '20mm',
    left: '20mm'
  },
  printBackground: true,
  preferCSSPageSize: false
}

const pdfBuffer = await PDFReportService.generateReport(pdfData, options)
```

## Email Service Integration

### Features

- **Automatic PDF Attachment**: Attaches generated reports to emails
- **Personalized Content**: Customized email content based on results
- **Follow-up Sequences**: Automated follow-up emails with resources
- **Email Logging**: Tracks all email communications in database

### Usage Examples

#### Send Assessment Report

```javascript
const result = await PDFEmailService.sendAssessmentReport({
  to: 'user@example.com',
  leadName: 'John Doe',
  leadId: 'lead-123',
  assessmentResult: {
    totalScore: 25,
    segment: 'balanced',
    challenges: ['financial_communication']
  },
  reportId: 'report-123',
  options: {
    subject: 'Your Personalized Assessment Report',
    includeFullReport: true,
    customMessage: 'Hi John, here is your personalized report...'
  }
})
```

#### Send Follow-up Email

```javascript
const result = await PDFEmailService.sendFollowUpEmail({
  to: 'user@example.com',
  leadName: 'John Doe',
  leadId: 'lead-123',
  assessmentResult: {
    totalScore: 25,
    segment: 'balanced',
    challenges: ['financial_communication']
  },
  reportId: 'report-123'
})
```

#### Send Assessment Reminder

```javascript
const result = await PDFEmailService.sendAssessmentReminder({
  to: 'user@example.com',
  leadName: 'John Doe',
  leadId: 'lead-123',
  assessmentUrl: 'https://yourapp.com/assessment'
})
```

## Integration with Assessment Flow

### 1. Update AssessmentResults Component

The `AssessmentResults.tsx` component has been updated to automatically generate and send PDF reports when users submit their contact information.

### 2. Automated Workflow

```javascript
// In your assessment completion handler
const handleAssessmentComplete = async (assessmentData) => {
  // 1. Save assessment results
  const result = await RatchetMoneyAPI.completeAssessment(assessmentData)
  
  // 2. Generate and send PDF report
  const reportId = `report-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  
  await PDFEmailService.sendAssessmentReport({
    to: assessmentData.email,
    leadName: assessmentData.firstName,
    leadId: result.leadId,
    assessmentResult: {
      totalScore: result.totalScore,
      segment: result.segment,
      challenges: result.challenges
    },
    reportId
  })
  
  // 3. Schedule follow-up email
  setTimeout(async () => {
    await PDFEmailService.sendFollowUpEmail({
      to: assessmentData.email,
      leadName: assessmentData.firstName,
      leadId: result.leadId,
      assessmentResult: {
        totalScore: result.totalScore,
        segment: result.segment,
        challenges: result.challenges
      },
      reportId
    })
  }, 24 * 60 * 60 * 1000) // 24 hours later
}
```

## Report Templates

### Default Report Structure

1. **Header**: Company branding and report title
2. **Personal Information**: Lead details and assessment summary
3. **Score Section**: Visual score display with segment information
4. **Key Challenges**: List of identified areas for improvement
5. **Recommendations**: Personalized recommendations based on segment
6. **Next Steps**: Action items and call-to-action
7. **Footer**: Contact information and disclaimers

### Customizing Templates

To customize the report template, modify the `generateReportHTML` method in `PDFReportService`:

```javascript
private static generateReportHTML(data: PDFReportData): string {
  // Customize the HTML template here
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          /* Your custom CSS */
        </style>
      </head>
      <body>
        <!-- Your custom HTML structure -->
      </body>
    </html>
  `
}
```

## Email Templates

### Assessment Report Email

- **Subject**: Personalized based on segment
- **Content**: Summary of results with PDF attachment
- **CTA**: Link to dashboard or next steps

### Follow-up Email

- **Subject**: Additional resources for segment
- **Content**: Curated resources and next steps
- **CTA**: Schedule consultation or join community

### Reminder Email

- **Subject**: Complete assessment reminder
- **Content**: Benefits of completing assessment
- **CTA**: Direct link to assessment

## File Management

### Report Storage

Reports are automatically saved to the `./reports/` directory with the following structure:

```
reports/
├── report-1234567890-abc123.pdf
├── report-1234567891-def456.pdf
└── ...
```

### Cleanup Strategy

Implement a cleanup strategy to manage disk space:

```javascript
// Clean up reports older than 30 days
const cleanupOldReports = async () => {
  const fs = require('fs').promises
  const path = require('path')
  
  const reportsDir = path.join(process.cwd(), 'reports')
  const files = await fs.readdir(reportsDir)
  
  const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000)
  
  for (const file of files) {
    const filePath = path.join(reportsDir, file)
    const stats = await fs.stat(filePath)
    
    if (stats.mtime.getTime() < thirtyDaysAgo) {
      await fs.unlink(filePath)
      console.log(`Deleted old report: ${file}`)
    }
  }
}
```

## Error Handling

### Common Issues

1. **Browser Launch Failures**: Ensure proper system dependencies
2. **Memory Issues**: Close browser instances properly
3. **File Permission Errors**: Check write permissions for reports directory
4. **Email Delivery Failures**: Implement retry logic

### Error Handling Example

```javascript
try {
  const result = await PDFEmailService.sendAssessmentReport(data)
  if (!result.success) {
    console.error('Failed to send report:', result.message)
    // Implement retry logic or fallback
  }
} catch (error) {
  console.error('Unexpected error:', error)
  // Log error and notify admin
}
```

## Performance Optimization

### Browser Management

```javascript
// Initialize browser once at startup
await PDFReportService.initialize()

// Close browser on application shutdown
process.on('SIGINT', async () => {
  await PDFReportService.close()
  process.exit(0)
})
```

### Caching

Consider caching generated reports for users who request them multiple times:

```javascript
const cache = new Map()

const getCachedReport = async (reportId: string) => {
  if (cache.has(reportId)) {
    return cache.get(reportId)
  }
  
  const report = await PDFReportService.generateReport(data)
  cache.set(reportId, report)
  
  return report
}
```

## Testing

### Unit Tests

```javascript
describe('PDF Report Service', () => {
  test('should generate PDF report', async () => {
    const pdfBuffer = await PDFReportService.generateReport(testData)
    expect(pdfBuffer).toBeInstanceOf(Buffer)
    expect(pdfBuffer.length).toBeGreaterThan(0)
  })
  
  test('should handle invalid data gracefully', async () => {
    await expect(
      PDFReportService.generateReport(null)
    ).rejects.toThrow()
  })
})
```

### Integration Tests

```javascript
describe('PDF Email Service', () => {
  test('should send assessment report', async () => {
    const result = await PDFEmailService.sendAssessmentReport(testData)
    expect(result.success).toBe(true)
    expect(result.reportPath).toBeDefined()
  })
})
```

## Deployment Considerations

### Environment Setup

1. **Install Dependencies**: Ensure Puppeteer dependencies are installed
2. **File Permissions**: Set proper permissions for reports directory
3. **Memory Allocation**: Allocate sufficient memory for PDF generation
4. **Email Configuration**: Configure email service credentials

### Production Checklist

- [ ] Install Puppeteer dependencies
- [ ] Set up reports directory with proper permissions
- [ ] Configure email service (SendGrid, Mailgun, etc.)
- [ ] Implement error monitoring and logging
- [ ] Set up automated cleanup for old reports
- [ ] Test PDF generation in production environment
- [ ] Monitor memory usage and performance

## Next Steps

1. **Customize Templates**: Modify report and email templates to match your brand
2. **Add Analytics**: Track report downloads and email engagement
3. **Implement A/B Testing**: Test different report formats and email content
4. **Add Personalization**: Include more dynamic content based on user behavior
5. **Integrate with CRM**: Connect with your customer relationship management system

The Puppeteer integration is now ready to generate and send personalized PDF reports for your marketing funnel! 