import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, CheckCircle, AlertCircle } from 'lucide-react'

interface EmailCollectionProps {
  onEmailSubmitted: (email: string) => void
}

export const EmailCollection: React.FC<EmailCollectionProps> = ({ onEmailSubmitted }) => {
  const [email, setEmail] = useState('')
  const [isValid, setIsValid] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setEmail(value)
    if (value) {
      setIsValid(validateEmail(value))
    } else {
      setIsValid(true)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateEmail(email)) {
      setIsValid(false)
      return
    }

    setIsSubmitting(true)
    
    try {
      // Simulate API call to save email
      await new Promise(resolve => setTimeout(resolve, 10))
      
      // Send confirmation email
      await sendConfirmationEmail(email)
      
      setIsSubmitted(true)
      setTimeout(() => {
        onEmailSubmitted(email)
      }, 2000)
    } catch (error) {
      console.error('Error submitting email:', error)
      setIsValid(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  const sendConfirmationEmail = async (email: string) => {
    // This would integrate with your email service (SendGrid, Mailgun, etc.)
    console.log('Sending confirmation email to:', email)
    
    // For now, we'll simulate the email sending
    // In production, this would be a serverless function or API endpoint
  }

  if (isSubmitted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center p-8 bg-gradient-to-br from-green-900 to-green-800 rounded-2xl border border-green-500/30"
      >
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-green-400 mb-4">Check Your Email!</h2>
        <p className="text-gray-300 text-base mb-4">
          We've sent a confirmation link to <span className="text-green-400 font-semibold">{email}</span>
        </p>
        <p className="text-sm text-gray-400">
          Click the link in your email to continue to your personalized assessment.
        </p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-md mx-auto"
    >
      <div className="text-center mb-8">
        <Mail className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-white mb-4">
          Discover Your Money & Relationship Type
        </h1>
        <p className="text-gray-300 text-lg">
          Get your personalized assessment and actionable strategies to improve your financial harmony.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
            Email Address
          </label>
          <div className="relative">
            <input
              type="email"
              id="email"
              value={email}
              onChange={handleEmailChange}
              className={`w-full px-4 py-3 bg-gray-800 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-all ${
                isValid 
                  ? 'border-gray-600 focus:border-red-500 focus:ring-red-500/20' 
                  : 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
              }`}
              placeholder="Enter your email address"
              disabled={isSubmitting}
            />
            {!isValid && (
              <AlertCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-red-500" />
            )}
          </div>
          {!isValid && (
            <p className="mt-2 text-sm text-red-400">
              Please enter a valid email address
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !email || !isValid}
          className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-all duration-200 hover:scale-105"
        >
          {isSubmitting ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Sending...
            </div>
          ) : (
            'Start Your Assessment'
          )}
        </button>

        <p className="text-xs text-gray-400 text-center">
          By continuing, you agree to receive personalized content and updates. 
          You can unsubscribe at any time.
        </p>
      </form>
    </motion.div>
  )
} 