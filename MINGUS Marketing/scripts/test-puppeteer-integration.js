// Test script for Puppeteer PDF generation
require('dotenv').config()

console.log('🔍 Testing Puppeteer PDF Integration...')
console.log('================================')

async function testPuppeteerIntegration() {
  try {
    // Import the PDF service
    const { PDFReportService } = require('../src/services/pdfReportService.js')
    
    console.log('✅ PDFReportService imported successfully')
    
    // Test data
    const testData = {
      leadName: 'Test User',
      email: 'test@example.com',
      assessmentResult: {
        totalScore: 25,
        segment: 'balanced',
        challenges: ['financial_communication', 'emotional_spending', 'financial_planning']
      },
      generatedAt: new Date(),
      reportId: `test-report-${Date.now()}`
    }
    
    console.log('📊 Test data prepared:')
    console.log(`   Name: ${testData.leadName}`)
    console.log(`   Score: ${testData.assessmentResult.totalScore}/50`)
    console.log(`   Segment: ${testData.assessmentResult.segment}`)
    console.log(`   Challenges: ${testData.assessmentResult.challenges.length}`)
    
    // Test PDF generation
    console.log('\n🖨️  Testing PDF generation...')
    const pdfBuffer = await PDFReportService.generateReport(testData)
    
    console.log('✅ PDF generated successfully')
    console.log(`   Buffer size: ${pdfBuffer.length} bytes`)
    console.log(`   File size: ${(pdfBuffer.length / 1024).toFixed(2)} KB`)
    
    // Test saving to file
    console.log('\n💾 Testing file save...')
    const fs = require('fs').promises
    const path = require('path')
    
    const reportsDir = path.join(process.cwd(), 'reports')
    const testFilePath = path.join(reportsDir, `${testData.reportId}.pdf`)
    
    await fs.mkdir(reportsDir, { recursive: true })
    await fs.writeFile(testFilePath, pdfBuffer)
    
    console.log('✅ PDF saved to file successfully')
    console.log(`   File path: ${testFilePath}`)
    
    // Test email service
    console.log('\n📧 Testing email service...')
    const { PDFEmailService } = require('../src/services/pdfEmailService.js')
    
    console.log('✅ PDFEmailService imported successfully')
    
    // Test email generation (without actually sending)
    const emailContent = PDFEmailService.generateEmailContent({
      to: 'test@example.com',
      leadName: 'Test User',
      leadId: 'test-lead-123',
      assessmentResult: testData.assessmentResult,
      reportId: testData.reportId
    }, {
      subject: 'Test Report',
      customMessage: 'This is a test email with PDF report.'
    })
    
    console.log('✅ Email content generated successfully')
    console.log(`   Subject: ${emailContent.subject}`)
    console.log(`   Body length: ${emailContent.body.length} characters`)
    
    // Test base64 generation
    console.log('\n🔢 Testing base64 generation...')
    const base64String = await PDFReportService.generateReportAsBase64(testData)
    
    console.log('✅ Base64 generation successful')
    console.log(`   Base64 length: ${base64String.length} characters`)
    console.log(`   Starts with: ${base64String.substring(0, 20)}...`)
    
    // Clean up test file
    console.log('\n🧹 Cleaning up test file...')
    await fs.unlink(testFilePath)
    console.log('✅ Test file cleaned up')
    
    // Close browser
    console.log('\n🔒 Closing browser...')
    await PDFReportService.close()
    console.log('✅ Browser closed successfully')
    
    console.log('\n🎉 Puppeteer integration test completed successfully!')
    console.log('================================')
    console.log('✅ PDF generation: Working')
    console.log('✅ File saving: Working')
    console.log('✅ Email service: Working')
    console.log('✅ Base64 encoding: Working')
    console.log('✅ Browser management: Working')
    
    return true
    
  } catch (error) {
    console.error('❌ Test failed:', error.message)
    console.error('Stack trace:', error.stack)
    return false
  }
}

// Run the test
testPuppeteerIntegration()
  .then(success => {
    if (success) {
      console.log('\n🚀 Puppeteer integration is ready for use!')
    } else {
      console.log('\n⚠️  Puppeteer integration needs attention.')
      process.exit(1)
    }
  })
  .catch(error => {
    console.error('💥 Unexpected error:', error)
    process.exit(1)
  }) 