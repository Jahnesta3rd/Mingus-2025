import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { VerificationCodeInput } from '../common/VerificationCodeInput';

interface PreferencesData {
  risk_tolerance: string;
  investment_experience: string;
  financial_goals: string[];
  preferred_communication: string;
  notification_preferences: string[];
}

const PreferencesStep: React.FC = () => {
  const [formData, setFormData] = useState<PreferencesData>({
    risk_tolerance: '',
    investment_experience: '',
    financial_goals: [],
    preferred_communication: 'email',
    notification_preferences: [],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const [showVerification, setShowVerification] = useState(false);
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [verificationError, setVerificationError] = useState('');
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [phone, setPhone] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (name === 'preferred_communication' && value === 'sms') {
      setShowVerification(true);
    } else if (name === 'preferred_communication') {
      setShowVerification(false);
    }
  };

  const handleGoalToggle = (goal: string) => {
    setFormData(prev => ({
      ...prev,
      financial_goals: prev.financial_goals.includes(goal)
        ? prev.financial_goals.filter(g => g !== goal)
        : [...prev.financial_goals, goal]
    }));
  };

  const handleNotificationToggle = (notification: string) => {
    setFormData(prev => ({
      ...prev,
      notification_preferences: prev.notification_preferences.includes(notification)
        ? prev.notification_preferences.filter(n => n !== notification)
        : [...prev.notification_preferences, notification]
    }));
  };

  const handleVerifyCode = async (code: string) => {
    setVerificationLoading(true);
    setVerificationError('');
    setVerificationSuccess(false);
    try {
      // Replace with your API call
      const res = await fetch('/api/verify-phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code })
      });
      if (res.ok) {
        setVerificationSuccess(true);
        setShowVerification(false);
      } else {
        setVerificationError('Invalid code. Please try again.');
      }
    } catch (e) {
      setVerificationError('Network error. Please try again.');
    } finally {
      setVerificationLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/onboarding/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        navigate('/onboarding/financial-questionnaire');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save preferences');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const financialGoals = [
    'Emergency Fund',
    'Debt Payoff',
    'Home Purchase',
    'Retirement Savings',
    'Investment Portfolio',
    'Education Fund',
    'Travel Fund',
    'Business Startup'
  ];

  const notificationTypes = [
    'Weekly Progress Updates',
    'Goal Milestones',
    'Financial Tips',
    'Market Insights',
    'Account Alerts'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Progress Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Preferences</h1>
            <span className="text-base text-gray-500">Step 4 of 7</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-green-500 to-blue-600 h-2 rounded-full" style={{ width: '57%' }}></div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Your Financial Preferences</h2>
            <p className="text-gray-600">Help us tailor your experience with personalized recommendations.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
              </div>
            )}

            {/* Risk Tolerance */}
            <div>
              <label className="block text-base font-medium text-gray-700 mb-4">
                What's your risk tolerance for investments?
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { value: 'conservative', label: 'Conservative', desc: 'Low risk, steady returns' },
                  { value: 'moderate', label: 'Moderate', desc: 'Balanced risk and return' },
                  { value: 'aggressive', label: 'Aggressive', desc: 'Higher risk, higher potential' }
                ].map(option => (
                  <div
                    key={option.value}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                      formData.risk_tolerance === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setFormData(prev => ({ ...prev, risk_tolerance: option.value }))}
                  >
                    <div className="font-medium text-gray-900">{option.label}</div>
                    <div className="text-base text-gray-600">{option.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Investment Experience */}
            <div>
              <label className="block text-base font-medium text-gray-700 mb-2">
                Investment Experience Level
              </label>
              <select
                name="investment_experience"
                value={formData.investment_experience}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select your experience level</option>
                <option value="beginner">Beginner - New to investing</option>
                <option value="intermediate">Intermediate - Some experience</option>
                <option value="advanced">Advanced - Experienced investor</option>
                <option value="expert">Expert - Professional level</option>
              </select>
            </div>

            {/* Financial Goals */}
            <div>
              <label className="block text-base font-medium text-gray-700 mb-4">
                What are your primary financial goals? (Select all that apply)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {financialGoals.map(goal => (
                  <label key={goal} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.financial_goals.includes(goal)}
                      onChange={() => handleGoalToggle(goal)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-base font-medium text-gray-900">{goal}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Communication Preferences */}
            <div>
              <label className="block text-base font-medium text-gray-700 mb-2">
                Preferred Communication Method
              </label>
              <select
                name="preferred_communication"
                value={formData.preferred_communication}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="push">Push Notifications</option>
                <option value="in_app">In-App Only</option>
              </select>
              {formData.preferred_communication === 'sms' && (
                <div className="mt-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6 text-[var(--text-primary)]">
                  <label className="block text-base font-medium mb-2" htmlFor="phone">Phone Number</label>
                  <input
                    id="phone"
                    type="tel"
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    className="form-input mb-4"
                    placeholder="Enter your phone number"
                  />
                  <VerificationCodeInput
                    length={6}
                    onComplete={handleVerifyCode}
                    loading={verificationLoading}
                    error={verificationError}
                    success={verificationSuccess}
                    disabled={verificationLoading}
                    autoFocus={true}
                    className="mb-4"
                  />
                  {verificationSuccess && (
                    <div className="text-green-400 mt-2">Phone verified successfully!</div>
                  )}
                </div>
              )}
            </div>

            {/* Notification Preferences */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                What notifications would you like to receive?
              </label>
              <div className="space-y-3">
                {notificationTypes.map(notification => (
                  <label key={notification} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.notification_preferences.includes(notification)}
                      onChange={() => handleNotificationToggle(notification)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm font-medium text-gray-900">{notification}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between pt-6">
              <button
                type="button"
                onClick={() => navigate('/onboarding/goals')}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-8 py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : 'Continue'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PreferencesStep; 