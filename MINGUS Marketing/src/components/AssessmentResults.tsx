import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail,
  User,
  Phone,
  Download,
  Star,
  CheckCircle,
  ArrowRight,
  Heart,
  TrendingUp,
  Shield,
  Gift
} from 'lucide-react'
import { RatchetMoneyAPI } from '../api'
import { PDFEmailService } from '../services/pdfEmailService'

interface AssessmentResultsProps {
  data: {
    totalScore: number
    segment: string
    answers: Record<string, any>
    leadId?: string // Added for potential existing lead ID
  }
  email: string
}

interface LeadFormData {
  email: string
  firstName: string
  phoneNumber: string
  contactMethod: 'email' | 'phone' | 'both'
  betaInterest: 'very' | 'somewhat' | 'not'
}

export const AssessmentResults: React.FC<AssessmentResultsProps> = ({ data, email }) => {
  const [showLeadForm, setShowLeadForm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<LeadFormData>({
    email: email || '',
    firstName: '',
    phoneNumber: '',
    contactMethod: 'email',
    betaInterest: 'somewhat'
  })

  const { totalScore, segment } = data
  const maxScore = 50
  const progressPercentage = (totalScore / maxScore) * 100

  // Segment-specific content
  const segmentContent = {
    'stress-free': {
      title: 'Stress-Free Lover',
      color: 'text-green-400',
      bgColor: 'bg-green-900/20',
      borderColor: 'border-green-500/30',
      message: 'Congratulations! You have a healthy and balanced relationship with money and relationships. You\'re already doing amazing!',
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
      title: 'Relationship Spender',
      color: 'text-blue-400',
      bgColor: 'bg-blue-900/20',
      borderColor: 'border-blue-500/30',
      message: 'You\'re aware of how relationships impact your spending, which is a great first step! You have the foundation for positive change.',
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
      title: 'Emotional Money Manager',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-900/20',
      borderColor: 'border-yellow-500/30',
      message: 'Your emotions significantly influence your spending decisions. This is common and completely fixable with the right strategies.',
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
      title: 'Crisis Mode',
      color: 'text-red-400',
      bgColor: 'bg-red-900/20',
      borderColor: 'border-red-500/30',
      message: 'Your relationship dynamics are creating significant financial stress. This is serious, but you\'re taking the right step by seeking help.',
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

  const currentSegment = segmentContent[segment as keyof typeof segmentContent]

  const handleFormChange = (field: keyof LeadFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Update lead information with form data
      if (data.leadId) {
        await RatchetMoneyAPI.updateLead(data.leadId, {
          name: formData.firstName,
          phone: formData.phoneNumber,
          contactMethod: formData.contactMethod,
          betaInterest: formData.betaInterest === 'very'
        })
      }

      // Generate and send PDF report
      const reportId = `report-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

      const emailResult = await PDFEmailService.sendAssessmentReport({
        to: formData.email,
        leadName: formData.firstName,
        leadId: data.leadId || '',
        assessmentResult: {
          totalScore,
          segment,
          challenges: Object.keys(data.answers)
        },
        reportId,
        options: {
          subject: 'Your Ratchet Money Assessment Report is Ready!',
          includeFullReport: true,
          customMessage: `Hi ${formData.firstName || 'there'},

Thank you for completing your assessment! Your personalized PDF report is attached to this email.

Your Results Summary:
• Score: ${totalScore}/50
• Segment: ${segment.charAt(0).toUpperCase() + segment.slice(1)}
• Key Areas: ${Object.keys(data.answers).length} areas identified

What's in your report:
📊 Detailed analysis of your relationship with money
💡 Personalized recommendations based on your results
🎯 Actionable next steps to improve your financial wellness
📈 Progress tracking tools and resources

We'll also send you follow-up resources and tips over the next few weeks to help you on your journey.

If you have any questions about your results, just reply to this email!

Best regards,
The Ratchet Money Team`
        }
      })

      if (emailResult.success) {
        console.log('PDF report sent successfully:', emailResult.reportPath)
      } else {
        console.error('Failed to send PDF report:', emailResult.message)
      }

      // Send follow-up email with resources
      await RatchetMoneyAPI.sendEmail({
        to: formData.email,
        subject: 'Your Ratchet Money Resources Are Ready!',
        body: `
          <h1>Your Personalized Resources</h1>
          <p>Hi ${formData.firstName || 'there'},</p>
          <p>Thank you for completing your assessment! Here are your personalized resources:</p>
          <ul>
            <li>📊 Detailed Relationship-Money Health Report (15-page analysis)</li>
            <li>💪 5 Ways to Strengthen Relationships While Building Wealth (PDF)</li>
            <li>🚀 Early access to Ratchet Money beta</li>
            <li>📧 Weekly tips connecting wellness to wealth</li>
          </ul>
          <p>Your segment: ${segment}</p>
          <p>Your score: ${totalScore}/50</p>
        `,
        leadId: data.leadId || '',
        emailType: 'assessment_results'
      })

      // Show success state
      console.log('Lead updated and email sent:', formData)

    } catch (error) {
      console.error('Error submitting form:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl mx-auto">
        <AnimatePresence mode="wait">
          {!showLeadForm ? (
            // Results Display
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-gray-800 to-gray-700 p-8 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="w-20 h-20 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <CheckCircle className="w-10 h-10 text-white" />
                </motion.div>
                <h1 className="text-3xl font-bold text-white mb-2">Your Assessment Results</h1>
                <p className="text-gray-300">Discover your relationship with money and get personalized strategies</p>
              </div>

              <div className="p-8">
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Score and Segment */}
                  <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="space-y-6"
                  >
                    {/* Circular Progress */}
                    <div className="text-center">
                      <div className="relative inline-block">
                        <svg className="w-32 h-32 transform -rotate-90">
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            className="text-gray-700"
                          />
                          <motion.circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            className="text-red-500"
                            initial={{ strokeDasharray: "0 352" }}
                            animate={{ strokeDasharray: `${(progressPercentage / 100) * 352} 352` }}
                            transition={{ delay: 0.5, duration: 1 }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-3xl font-bold text-white">{totalScore}</div>
                            <div className="text-sm text-gray-400">out of {maxScore}</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Segment */}
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 }}
                      className={`p-6 rounded-xl border ${currentSegment.bgColor} ${currentSegment.borderColor}`}
                    >
                      <h3 className={`text-xl font-bold ${currentSegment.color} mb-2`}>
                        {currentSegment.title}
                      </h3>
                      <p className="text-gray-300 text-sm">{currentSegment.message}</p>
                    </motion.div>
                  </motion.div>

                  {/* Challenges and Recommendations */}
                  <motion.div
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 }}
                    className="space-y-6"
                  >
                    {/* Top Challenges */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                        <Shield className="w-5 h-5 mr-2 text-red-500" />
                        Your Top Challenges
                      </h3>
                      <ul className="space-y-2">
                        {currentSegment.challenges.map((challenge, index) => (
                          <motion.li
                            key={index}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.7 + index * 0.1 }}
                            className="flex items-start text-gray-300 text-sm"
                          >
                            <div className="w-2 h-2 bg-red-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            {challenge}
                          </motion.li>
                        ))}
                      </ul>
                    </div>

                    {/* Recommended Next Steps */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                        <TrendingUp className="w-5 h-5 mr-2 text-green-500" />
                        Recommended Next Steps
                      </h3>
                      <ul className="space-y-2">
                        {currentSegment.recommendations.map((rec, index) => (
                          <motion.li
                            key={index}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.8 + index * 0.1 }}
                            className="flex items-start text-gray-300 text-sm"
                          >
                            <CheckCircle className="w-4 h-4 mr-3 mt-0.5 text-green-500 flex-shrink-0" />
                            {rec}
                          </motion.li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                </div>

                {/* CTA Button */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1 }}
                  className="text-center mt-8"
                >
                  <button
                    onClick={() => setShowLeadForm(true)}
                    className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 to-red-800 text-white font-semibold py-4 px-8 rounded-lg transition-all duration-200 hover:scale-105 flex items-center mx-auto"
                  >
                    Get Your Detailed Report & Resources
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </button>
                </motion.div>
              </div>
            </motion.div>
          ) : (
            // Lead Capture Form
            <motion.div
              key="lead-form"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-red-600 to-red-700 p-8 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <Gift className="w-8 h-8 text-white" />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">Unlock Your Free Resources</h2>
                <p className="text-red-100">Get instant access to personalized strategies and exclusive content</p>
              </div>

              <div className="p-8">
                <div className="grid lg:grid-cols-2 gap-8">
                  {/* Value Proposition */}
                  <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-6"
                  >
                    <h3 className="text-xl font-semibold text-white mb-4">What You'll Get:</h3>

                    <div className="space-y-4">
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="flex items-start p-4 bg-gray-700/50 rounded-lg"
                      >
                        <Download className="w-6 h-6 text-red-500 mr-3 mt-1 flex-shrink-0" />
                        <div>
                          <h4 className="font-semibold text-white">Detailed Relationship-Money Health Report</h4>
                          <p className="text-gray-300 text-sm">Your personalized 15-page analysis with actionable insights</p>
                        </div>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="flex items-start p-4 bg-gray-700/50 rounded-lg"
                      >
                        <Heart className="w-6 h-6 text-red-500 mr-3 mt-1 flex-shrink-0" />
                        <div>
                          <h4 className="font-semibold text-white">5 Ways to Strengthen Relationships While Building Wealth</h4>
                          <p className="text-gray-300 text-sm">Exclusive PDF guide with proven strategies</p>
                        </div>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 }}
                        className="flex items-start p-4 bg-gray-700/50 rounded-lg"
                      >
                        <Star className="w-6 h-6 text-red-500 mr-3 mt-1 flex-shrink-0" />
                        <div>
                          <h4 className="font-semibold text-white">Early Access to Ratchet Money Beta</h4>
                          <p className="text-gray-300 text-sm">Be among the first to try our revolutionary platform</p>
                        </div>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 }}
                        className="flex items-start p-4 bg-gray-700/50 rounded-lg"
                      >
                        <Mail className="w-6 h-6 text-red-500 mr-3 mt-1 flex-shrink-0" />
                        <div>
                          <h4 className="font-semibold text-white">Weekly Tips Connecting Wellness to Wealth</h4>
                          <p className="text-gray-300 text-sm">Curated insights delivered to your inbox</p>
                        </div>
                      </motion.div>
                    </div>

                    {/* Social Proof */}
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 }}
                      className="mt-8 p-4 bg-gray-700/30 rounded-lg"
                    >
                      <div className="flex items-center mb-3">
                        <div className="flex text-yellow-400">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} className="w-4 h-4 fill-current" />
                          ))}
                        </div>
                        <span className="text-white text-sm ml-2">4.9/5 from 2,847 users</span>
                      </div>
                      <p className="text-gray-300 text-sm italic">
                        "This assessment completely changed how I think about money and relationships. The personalized strategies are gold!" - Sarah M.
                      </p>
                    </motion.div>
                  </motion.div>

                  {/* Lead Capture Form */}
                  <motion.div
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-4"
                  >
                    <form onSubmit={handleSubmit} className="space-y-4">
                      {/* Email */}
                      <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                          Email Address *
                        </label>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <input
                            type="email"
                            id="email"
                            value={formData.email}
                            onChange={(e) => handleFormChange('email', e.target.value)}
                            required
                            className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
                            placeholder="Enter your email address"
                          />
                        </div>
                      </div>

                      {/* First Name */}
                      <div>
                        <label htmlFor="firstName" className="block text-sm font-medium text-gray-300 mb-2">
                          First Name *
                        </label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <input
                            type="text"
                            id="firstName"
                            value={formData.firstName}
                            onChange={(e) => handleFormChange('firstName', e.target.value)}
                            required
                            className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
                            placeholder="Enter your first name"
                          />
                        </div>
                      </div>

                      {/* Phone Number */}
                      <div>
                        <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-300 mb-2">
                          Phone Number (Optional)
                        </label>
                        <div className="relative">
                          <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <input
                            type="tel"
                            id="phoneNumber"
                            value={formData.phoneNumber}
                            onChange={(e) => handleFormChange('phoneNumber', e.target.value)}
                            className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
                            placeholder="Enter your phone number"
                          />
                        </div>
                      </div>

                      {/* Preferred Contact Method */}
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Preferred Contact Method
                        </label>
                        <div className="space-y-2">
                          {[
                            { value: 'email', label: 'Email only' },
                            { value: 'phone', label: 'Phone only' },
                            { value: 'both', label: 'Both email and phone' }
                          ].map((option) => (
                            <label key={option.value} className="flex items-center">
                              <input
                                type="radio"
                                name="contactMethod"
                                value={option.value}
                                checked={formData.contactMethod === option.value}
                                onChange={(e) => handleFormChange('contactMethod', e.target.value)}
                                className="mr-3"
                              />
                              <span className="text-gray-300">{option.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Beta Interest */}
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Interest in Beta Access
                        </label>
                        <div className="space-y-2">
                          {[
                            { value: 'very', label: 'Very interested - sign me up!' },
                            { value: 'somewhat', label: 'Somewhat interested - keep me updated' },
                            { value: 'not', label: 'Not interested right now' }
                          ].map((option) => (
                            <label key={option.value} className="flex items-center">
                              <input
                                type="radio"
                                name="betaInterest"
                                value={option.value}
                                checked={formData.betaInterest === option.value}
                                onChange={(e) => handleFormChange('betaInterest', e.target.value)}
                                className="mr-3"
                              />
                              <span className="text-gray-300">{option.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Submit Button */}
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-lg transition-all duration-200 hover:scale-105"
                      >
                        {isSubmitting ? (
                          <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            Processing...
                          </div>
                        ) : (
                          'Get My Free Resources Now'
                        )}
                      </button>
                    </form>

                    <p className="text-xs text-gray-400 text-center">
                      By submitting, you agree to receive personalized content and updates.
                      You can unsubscribe at any time.
                    </p>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
} 