import React, { useState, useEffect } from 'react'
import { useAnalyticsConsent } from '../hooks/useAnalytics'

interface GDPRConsentProps {
  onConsentChange?: (granted: boolean) => void
  showDetails?: boolean
  className?: string
}

export const GDPRConsent: React.FC<GDPRConsentProps> = ({
  onConsentChange,
  showDetails = false,
  className = ''
}) => {
  const { consentGranted, grantConsent, denyConsent } = useAnalyticsConsent()
  const [showBanner, setShowBanner] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [preferences, setPreferences] = useState({
    analytics: true,
    marketing: false,
    necessary: true
  })

  useEffect(() => {
    // Show banner if no consent decision has been made
    const hasConsentDecision = localStorage.getItem('analytics_consent')
    if (!hasConsentDecision) {
      setShowBanner(true)
    }
  }, [])

  const handleGrantConsent = () => {
    grantConsent()
    setShowBanner(false)
    onConsentChange?.(true)
  }

  const handleDenyConsent = () => {
    denyConsent()
    setShowBanner(false)
    onConsentChange?.(false)
  }

  const handleSavePreferences = () => {
    if (preferences.analytics) {
      grantConsent()
    } else {
      denyConsent()
    }
    setShowModal(false)
    onConsentChange?.(preferences.analytics)
  }

  // Consent Banner
  if (showBanner) {
    return (
      <div className={`fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-4 z-50 ${className}`}>
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between">
          <div className="flex-1 mb-4 sm:mb-0">
            <h3 className="text-lg font-semibold mb-2">We value your privacy</h3>
            <p className="text-gray-300 text-sm">
              We use cookies and analytics to improve your experience and provide personalized content. 
              By continuing to use our site, you consent to our use of cookies.
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleDenyConsent}
              className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Decline
            </button>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
            >
              Customize
            </button>
            <button
              onClick={handleGrantConsent}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Accept All
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Consent Modal
  if (showModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Cookie Preferences</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              {/* Necessary Cookies */}
              <div className="border-b pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900">Necessary Cookies</h3>
                    <p className="text-sm text-gray-600">
                      Essential for the website to function properly
                    </p>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.necessary}
                      disabled
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-500">Always Active</span>
                  </div>
                </div>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Session management</li>
                  <li>• Security features</li>
                  <li>• Basic functionality</li>
                </ul>
              </div>

              {/* Analytics Cookies */}
              <div className="border-b pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900">Analytics Cookies</h3>
                    <p className="text-sm text-gray-600">
                      Help us understand how visitors interact with our website
                    </p>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.analytics}
                      onChange={(e) => setPreferences(prev => ({ ...prev, analytics: e.target.checked }))}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                  </div>
                </div>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Google Analytics tracking</li>
                  <li>• User behavior analysis</li>
                  <li>• Performance optimization</li>
                  <li>• A/B testing</li>
                </ul>
              </div>

              {/* Marketing Cookies */}
              <div className="border-b pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900">Marketing Cookies</h3>
                    <p className="text-sm text-gray-600">
                      Used to deliver personalized advertisements
                    </p>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.marketing}
                      onChange={(e) => setPreferences(prev => ({ ...prev, marketing: e.target.checked }))}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                  </div>
                </div>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Personalized ads</li>
                  <li>• Social media integration</li>
                  <li>• Email marketing tracking</li>
                </ul>
              </div>

              {/* Privacy Information */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Your Privacy Rights</h4>
                <div className="text-sm text-gray-600 space-y-2">
                  <p>
                    Under GDPR, you have the right to:
                  </p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Access your personal data</li>
                    <li>Request data correction or deletion</li>
                    <li>Withdraw consent at any time</li>
                    <li>Export your data</li>
                    <li>Lodge a complaint with authorities</li>
                  </ul>
                  <p className="mt-3">
                    <a href="/privacy" className="text-blue-600 hover:underline">
                      Read our full Privacy Policy
                    </a>
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePreferences}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return null
}

// Privacy Controls Component
export const PrivacyControls: React.FC = () => {
  const { consentGranted, deleteUserData, exportUserData } = useAnalyticsConsent()
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleDeleteData = async () => {
    if (!confirm('Are you sure you want to delete all your data? This action cannot be undone.')) {
      return
    }

    setIsLoading(true)
    setMessage('')
    
    try {
      // Get user ID from session or localStorage
      const userId = localStorage.getItem('user_id') || 'anonymous'
      await deleteUserData(userId)
      setMessage('Your data has been successfully deleted.')
    } catch (error) {
      setMessage('Error deleting data. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExportData = async () => {
    setIsLoading(true)
    setMessage('')
    
    try {
      const userId = localStorage.getItem('user_id') || 'anonymous'
      const data = await exportUserData(userId)
      
      // Create and download file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'my-data.json'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      setMessage('Your data has been exported successfully.')
    } catch (error) {
      setMessage('Error exporting data. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="privacy-controls bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Privacy Controls</h3>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <h4 className="font-medium text-gray-900">Analytics Consent</h4>
            <p className="text-sm text-gray-600">
              {consentGranted ? 'Analytics tracking is enabled' : 'Analytics tracking is disabled'}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            consentGranted ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {consentGranted ? 'Active' : 'Inactive'}
          </span>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleExportData}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Exporting...' : 'Export My Data'}
          </button>
          
          <button
            onClick={handleDeleteData}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Deleting...' : 'Delete My Data'}
          </button>
        </div>

        {message && (
          <div className={`p-3 rounded-lg text-sm ${
            message.includes('Error') ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
          }`}>
            {message}
          </div>
        )}

        <div className="text-xs text-gray-500">
          <p>
            <strong>Note:</strong> Data deletion will remove all your information from our systems, 
            including assessment results and email preferences. This action cannot be undone.
          </p>
        </div>
      </div>
    </div>
  )
}

// Cookie Policy Component
export const CookiePolicy: React.FC = () => {
  return (
    <div className="cookie-policy bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Cookie Policy</h3>
      
      <div className="space-y-4 text-sm text-gray-600">
        <div>
          <h4 className="font-medium text-gray-900 mb-2">What are cookies?</h4>
          <p>
            Cookies are small text files that are stored on your device when you visit our website. 
            They help us provide you with a better experience and understand how you use our site.
          </p>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-2">Types of cookies we use:</h4>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Necessary cookies:</strong> Essential for website functionality</li>
            <li><strong>Analytics cookies:</strong> Help us understand user behavior</li>
            <li><strong>Marketing cookies:</strong> Used for personalized advertising</li>
          </ul>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-2">How to manage cookies:</h4>
          <p>
            You can control and manage cookies through your browser settings. However, 
            disabling certain cookies may affect the functionality of our website.
          </p>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-2">Third-party cookies:</h4>
          <p>
            We use third-party services like Google Analytics that may set their own cookies. 
            These services have their own privacy policies.
          </p>
        </div>
      </div>
    </div>
  )
} 