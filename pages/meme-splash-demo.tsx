import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import MemeSplashPage from '../components/MemeSplashPage';

const MemeSplashDemo: React.FC = () => {
  const [showMeme, setShowMeme] = useState(false);
  const [demoConfig, setDemoConfig] = useState({
    autoAdvanceSeconds: 10,
    showOptOutModal: true,
    customHandlers: false
  });
  const router = useRouter();

  const handleContinue = () => {
    console.log('Demo: User continued to dashboard');
    setShowMeme(false);
    // In real app, this would navigate to dashboard
    alert('Demo: Would navigate to dashboard');
  };

  const handleOptOut = () => {
    console.log('Demo: User opted out of daily memes');
    setShowMeme(false);
    alert('Demo: User opted out of daily memes');
  };

  const handleSkip = () => {
    console.log('Demo: User skipped today');
    setShowMeme(false);
    alert('Demo: User skipped for today');
  };

  if (showMeme) {
    return (
      <MemeSplashPage
        onContinue={demoConfig.customHandlers ? handleContinue : undefined}
        onOptOut={demoConfig.customHandlers ? handleOptOut : undefined}
        onSkip={demoConfig.customHandlers ? handleSkip : undefined}
        autoAdvanceSeconds={demoConfig.autoAdvanceSeconds}
        showOptOutModal={demoConfig.showOptOutModal}
      />
    );
  }

  return (
    <>
      <Head>
        <title>Meme Splash Page Demo - Mingus</title>
        <meta name="description" content="Demo of the Meme Splash Page component" />
      </Head>

      <div className="min-h-screen bg-gray-100 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-6">
              Meme Splash Page Demo
            </h1>
            
            <p className="text-gray-600 mb-8">
              This demo showcases the Meme Splash Page component with different configurations.
              The component displays daily memes with analytics tracking, accessibility features,
              and smooth animations.
            </p>

            {/* Configuration Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Auto-advance seconds
                  </label>
                  <select
                    value={demoConfig.autoAdvanceSeconds}
                    onChange={(e) => setDemoConfig(prev => ({
                      ...prev,
                      autoAdvanceSeconds: parseInt(e.target.value)
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={0}>Disabled</option>
                    <option value={5}>5 seconds</option>
                    <option value={10}>10 seconds</option>
                    <option value={15}>15 seconds</option>
                    <option value={30}>30 seconds</option>
                  </select>
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={demoConfig.showOptOutModal}
                      onChange={(e) => setDemoConfig(prev => ({
                        ...prev,
                        showOptOutModal: e.target.checked
                      }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Show opt-out confirmation modal
                    </span>
                  </label>
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={demoConfig.customHandlers}
                      onChange={(e) => setDemoConfig(prev => ({
                        ...prev,
                        customHandlers: e.target.checked
                      }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Use custom event handlers (shows alerts)
                    </span>
                  </label>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Full-screen overlay design
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Prominent continue button
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Easy opt-out options
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Loading states & error handling
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Analytics tracking
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Accessibility features
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Mobile-first responsive
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Auto-advance countdown
                  </li>
                </ul>
              </div>
            </div>

            {/* Demo Buttons */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Try the Component</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setShowMeme(true)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50"
                >
                  Show Meme Splash Page
                </button>
                
                <button
                  onClick={() => router.push('/')}
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-gray-500 focus:ring-opacity-50"
                >
                  Back to Home
                </button>
              </div>
            </div>

            {/* Usage Examples */}
            <div className="mt-8 p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Examples</h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Basic Usage</h4>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-sm overflow-x-auto">
{`import MemeSplashPage from '../components/MemeSplashPage';

<MemeSplashPage />`}
                  </pre>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">With Custom Handlers</h4>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-sm overflow-x-auto">
{`<MemeSplashPage
  onContinue={() => router.push('/dashboard')}
  onOptOut={() => updateUserPreferences()}
  onSkip={() => router.push('/dashboard')}
  autoAdvanceSeconds={15}
  showOptOutModal={true}
/>`}
                  </pre>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Conditional Rendering</h4>
                  <pre className="bg-gray-800 text-green-400 p-3 rounded text-sm overflow-x-auto">
{`{shouldShowMeme && (
  <MemeSplashPage
    onContinue={() => setShouldShowMeme(false)}
    autoAdvanceSeconds={10}
  />
)}`}
                  </pre>
                </div>
              </div>
            </div>

            {/* Keyboard Shortcuts */}
            <div className="mt-8 p-6 bg-blue-50 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Keyboard Shortcuts</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <kbd className="bg-gray-200 px-2 py-1 rounded font-mono">Enter</kbd> or <kbd className="bg-gray-200 px-2 py-1 rounded font-mono">Space</kbd>
                  <p className="text-gray-600 mt-1">Continue to dashboard</p>
                </div>
                <div>
                  <kbd className="bg-gray-200 px-2 py-1 rounded font-mono">Escape</kbd>
                  <p className="text-gray-600 mt-1">Skip for today</p>
                </div>
                <div>
                  <kbd className="bg-gray-200 px-2 py-1 rounded font-mono">O</kbd>
                  <p className="text-gray-600 mt-1">Open opt-out modal</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default MemeSplashDemo;
