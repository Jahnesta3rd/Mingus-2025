import React, { useState, useEffect } from 'react';
import { VerificationCodeInput } from './VerificationCodeInput';

export const VerificationCodeInputDemo: React.FC = () => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const [demoMode, setDemoMode] = useState<'basic' | 'loading' | 'error' | 'success' | 'disabled'>('basic');

  // Simulate verification process
  const handleComplete = async (verificationCode: string) => {
    console.log('Verification code completed:', verificationCode);
    
    if (demoMode === 'loading') {
      setLoading(true);
      setError('');
      setSuccess(false);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate success/failure
      if (verificationCode === '123456') {
        setSuccess(true);
        setError('');
      } else {
        setError('Invalid verification code. Please try again.');
        setSuccess(false);
      }
      
      setLoading(false);
    } else if (demoMode === 'error') {
      setError('This is a demo error message');
      setSuccess(false);
    } else if (demoMode === 'success') {
      setSuccess(true);
      setError('');
    }
  };

  // Reset states when demo mode changes
  useEffect(() => {
    setCode('');
    setLoading(false);
    setError('');
    setSuccess(false);
    setDisabled(demoMode === 'disabled');
  }, [demoMode]);

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">
            Verification Code Input Component
          </h1>
          <p className="text-gray-400">
            A comprehensive verification code input with auto-advance, paste support, and mobile optimization
          </p>
        </div>

        {/* Demo Mode Selector */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Demo Modes</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {[
              { key: 'basic', label: 'Basic', description: 'Standard input' },
              { key: 'loading', label: 'Loading', description: 'With verification' },
              { key: 'error', label: 'Error', description: 'Error state' },
              { key: 'success', label: 'Success', description: 'Success state' },
              { key: 'disabled', label: 'Disabled', description: 'Disabled state' },
            ].map((mode) => (
              <button
                key={mode.key}
                onClick={() => setDemoMode(mode.key as any)}
                className={`p-3 rounded-lg text-sm font-medium transition-colors ${
                  demoMode === mode.key
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                title={mode.description}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        {/* Main Demo */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">
            {demoMode.charAt(0).toUpperCase() + demoMode.slice(1)} Mode
          </h2>
          
          <div className="flex flex-col items-center space-y-6">
            <VerificationCodeInput
              length={6}
              onComplete={handleComplete}
              onCodeChange={setCode}
              loading={loading}
              error={error}
              success={success}
              disabled={disabled}
              autoFocus={true}
              className="mb-4"
            />

            {/* Current State Display */}
            <div className="w-full max-w-md space-y-2">
              <div className="p-3 bg-gray-700 rounded text-sm text-gray-300">
                <strong>Current code:</strong> {code || 'None'}
              </div>
              
              <div className="p-3 bg-gray-700 rounded text-sm text-gray-300">
                <strong>Status:</strong> {
                  loading ? 'Verifying...' :
                  error ? 'Error' :
                  success ? 'Success' :
                  disabled ? 'Disabled' :
                  'Ready'
                }
              </div>

              {/* Instructions */}
              <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded text-sm text-blue-300">
                <strong>Instructions:</strong>
                <ul className="mt-1 space-y-1 text-xs">
                  <li>• Type digits to auto-advance</li>
                  <li>• Use backspace to go back</li>
                  <li>• Paste a 6-digit code</li>
                  <li>• Use arrow keys to navigate</li>
                  <li>• Press Enter when complete</li>
                </ul>
              </div>

              {/* Demo-specific instructions */}
              {demoMode === 'loading' && (
                <div className="p-3 bg-yellow-900/20 border border-yellow-500/30 rounded text-sm text-yellow-300">
                  <strong>Demo:</strong> Enter "123456" for success, any other code for error
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Features Showcase */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                6 individual input fields
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Auto-advance on input
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Paste functionality
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Auto-submit when complete
              </div>
            </div>
            <div className="space-y-2">
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
                Backspace navigation
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Mobile-friendly
              </div>
              <div className="flex items-center text-green-400">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Haptic feedback
              </div>
            </div>
          </div>
        </div>

        {/* Usage Examples */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Usage Examples</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-white mb-2">Basic Usage</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`const [code, setCode] = useState('');

<VerificationCodeInput
  onComplete={(code) => console.log('Code:', code)}
  onCodeChange={setCode}
/>`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">With Loading State</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`const [loading, setLoading] = useState(false);

const handleComplete = async (code) => {
  setLoading(true);
  try {
    await verifyCode(code);
    // Handle success
  } catch (error) {
    // Handle error
  } finally {
    setLoading(false);
  }
};

<VerificationCodeInput
  onComplete={handleComplete}
  loading={loading}
/>`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">With Error Handling</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`const [error, setError] = useState('');

<VerificationCodeInput
  onComplete={handleComplete}
  error={error}
  success={!error && code.length === 6}
/>`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">Custom Length</h3>
              <pre className="bg-gray-900 p-4 rounded text-sm text-green-400 overflow-x-auto">
{`<VerificationCodeInput
  length={4}
  onComplete={handleComplete}
/>`}
              </pre>
            </div>
          </div>
        </div>

        {/* Accessibility Features */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Accessibility Features</h2>
          <div className="space-y-2">
            <div className="flex items-center text-green-400">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Proper ARIA labels for each digit field
            </div>
            <div className="flex items-center text-green-400">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Screen reader announcements for status changes
            </div>
            <div className="flex items-center text-green-400">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Keyboard navigation with arrow keys
            </div>
            <div className="flex items-center text-green-400">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Error announcements for invalid codes
            </div>
            <div className="flex items-center text-green-400">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Mobile-optimized with haptic feedback
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 