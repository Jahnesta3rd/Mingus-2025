import React, { useState } from 'react';
import { PhoneNumberInput } from './PhoneNumberInput';

export const PhoneNumberInputDemo: React.FC = () => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loadingPhone, setLoadingPhone] = useState('');
  const [disabledPhone, setDisabledPhone] = useState('');
  const [errorPhone, setErrorPhone] = useState('');
  const [customError, setCustomError] = useState('');

  // Simulate loading state
  const handleLoadingChange = (value: string) => {
    setLoadingPhone(value);
    if (value && value.length > 5) {
      // Simulate API call
      setTimeout(() => {
        setLoadingPhone(value);
      }, 2000);
    }
  };

  // Simulate error state
  const handleErrorChange = (value: string) => {
    setErrorPhone(value);
    if (value && value.length < 10) {
      setCustomError('Phone number must be at least 10 digits');
    } else {
      setCustomError('');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">
            Phone Number Input Component
          </h1>
          <p className="text-gray-400">
            A comprehensive phone number input with validation, accessibility, and Mingus theme integration
          </p>
        </div>

        {/* Basic Usage */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Basic Usage</h2>
          <PhoneNumberInput
            value={phoneNumber}
            onChange={setPhoneNumber}
            label="Phone Number"
            placeholder="Enter your phone number"
            required
          />
          <div className="mt-4 p-3 bg-gray-700 rounded text-sm text-gray-300">
            <strong>Current value:</strong> {phoneNumber || 'None'}
          </div>
        </div>

        {/* Loading State */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Loading State</h2>
          <PhoneNumberInput
            value={loadingPhone}
            onChange={handleLoadingChange}
            label="Phone Number (with loading)"
            placeholder="Type to see loading state"
            loading={loadingPhone.length > 5}
          />
          <div className="mt-2 text-sm text-gray-400">
            Type more than 5 characters to see the loading spinner
          </div>
        </div>

        {/* Disabled State */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Disabled State</h2>
          <PhoneNumberInput
            value={disabledPhone}
            onChange={setDisabledPhone}
            label="Phone Number (disabled)"
            placeholder="This input is disabled"
            disabled
          />
        </div>

        {/* Error State */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Error State</h2>
          <PhoneNumberInput
            value={errorPhone}
            onChange={handleErrorChange}
            label="Phone Number (with custom error)"
            placeholder="Enter a short number to see error"
            error={customError}
          />
        </div>

        {/* Different Sizes and Styles */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Different Styles</h2>
          
          <div className="space-y-4">
            <PhoneNumberInput
              value=""
              onChange={() => {}}
              label="Compact Style"
              placeholder="Compact input"
              className="max-w-xs"
            />
            
            <PhoneNumberInput
              value=""
              onChange={() => {}}
              label="Full Width Style"
              placeholder="Full width input"
              className="w-full"
            />
          </div>
        </div>

        {/* Accessibility Features */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Accessibility Features</h2>
          <div className="space-y-4">
            <PhoneNumberInput
              value=""
              onChange={() => {}}
              label="Screen Reader Friendly"
              placeholder="This input is optimized for screen readers"
              id="accessible-phone"
              name="accessible-phone"
              aria-describedby="accessibility-help"
            />
            <div id="accessibility-help" className="text-sm text-gray-400">
              This input includes proper ARIA labels, error announcements, and keyboard navigation support.
            </div>
          </div>
        </div>

        {/* Usage Examples */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Usage Examples</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-white mb-2">Form Integration</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`// In a form component
const [phone, setPhone] = useState('');

<PhoneNumberInput
  value={phone}
  onChange={setPhone}
  label="Contact Phone"
  required
  error={formErrors.phone}
/>`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">With Validation</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`// Custom validation
const validatePhone = (phone: string) => {
  if (!phone) return 'Phone number is required';
  if (phone.length < 10) return 'Phone number too short';
  return '';
};

<PhoneNumberInput
  value={phone}
  onChange={setPhone}
  error={validatePhone(phone)}
/>`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">Loading State</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`// With loading state
const [isLoading, setIsLoading] = useState(false);

<PhoneNumberInput
  value={phone}
  onChange={setPhone}
  loading={isLoading}
  disabled={isLoading}
/>`}
              </pre>
            </div>
          </div>
        </div>

        {/* Features List */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Domestic phone formatting
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Real-time validation
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Clear error messaging
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Keyboard navigation
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Screen reader friendly
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Mingus dark theme
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Loading states
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Disabled states
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 