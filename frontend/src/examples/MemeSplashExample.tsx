import React, { useState } from 'react';
import MemeSplashPage from '../components/MemeSplashPage';
import MoodDashboard from '../components/MoodDashboard';

/**
 * Example usage of MemeSplashPage component
 * This demonstrates how to integrate the meme splash page into your app
 */
const MemeSplashExample: React.FC = () => {
  const [showMemeSplash, setShowMemeSplash] = useState(true);
  const [showMoodDashboard, setShowMoodDashboard] = useState(false);
  const [currentUser, setCurrentUser] = useState('user123');
  const [currentSession, setCurrentSession] = useState('session456');

  const handleContinueToDashboard = () => {
    console.log('User continued to dashboard');
    setShowMemeSplash(false);
    // Navigate to your dashboard component here
    // Example: navigate('/dashboard');
  };

  const handleSkipMeme = () => {
    console.log('User skipped meme feature');
    setShowMemeSplash(false);
    // Navigate to your main app or dashboard
    // Example: navigate('/dashboard');
  };

  if (showMemeSplash) {
    return (
      <MemeSplashPage
        onContinue={handleContinueToDashboard}
        onSkip={handleSkipMeme}
        userId={currentUser}
        sessionId={currentSession}
        autoAdvanceDelay={10000} // 10 seconds
        enableMoodTracking={true} // Enable mood tracking
        className="z-50" // Ensure it's on top
      />
    );
  }

  if (showMoodDashboard) {
    return (
      <div className="min-h-screen bg-gray-100 p-4">
        <div className="max-w-6xl mx-auto">
          <MoodDashboard
            userId={currentUser}
            sessionId={currentSession}
          />
          <div className="mt-6 text-center">
            <button
              onClick={() => setShowMoodDashboard(false)}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors mr-4"
            >
              Back to Dashboard
            </button>
            <button
              onClick={() => setShowMemeSplash(true)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Show Meme Splash Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Your main app content would go here
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to Your Dashboard!
        </h1>
        <p className="text-gray-600 mb-6">
          The meme splash page has been dismissed.
        </p>
        <div className="space-x-4">
          <button
            onClick={() => setShowMemeSplash(true)}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Show Meme Splash Again
          </button>
          <button
            onClick={() => setShowMoodDashboard(true)}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            View Mood Analytics
          </button>
        </div>
      </div>
    </div>
  );
};

export default MemeSplashExample;
