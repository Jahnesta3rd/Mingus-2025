import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { OnboardingCompletionService } from '../../services/onboardingCompletionService';

interface OnboardingCompletionProps {
  userId: string;
  onComplete?: () => void;
}

interface CompletionData {
  user_name: string;
  goals_count: number;
  profile_completion: number;
  first_checkin_date?: string;
  mobile_app_available: boolean;
  community_stats: {
    total_members: number;
    active_this_week: number;
    average_savings: number;
  };
}

const OnboardingCompletion: React.FC<OnboardingCompletionProps> = ({
  userId,
  onComplete
}) => {
  const [currentStep, setCurrentStep] = useState<'congratulations' | 'engagement'>('congratulations');
  const [completionData, setCompletionData] = useState<CompletionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [reminderPreferences, setReminderPreferences] = useState({
    enabled: true,
    frequency: 'weekly',
    day: 'wednesday',
    time: '10:00',
    email: true,
    push: true
  });
  const navigate = useNavigate();

  useEffect(() => {
    const loadCompletionData = async () => {
      try {
        const data = await OnboardingCompletionService.getCompletionData(userId);
        setCompletionData(data);
      } catch (error) {
        console.error('Failed to load completion data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCompletionData();
  }, [userId]);

  const handleScheduleCheckin = async () => {
    setSavingPreferences(true);
    try {
      await OnboardingCompletionService.scheduleFirstCheckin(userId, reminderPreferences);
      setCurrentStep('engagement');
    } catch (error) {
      console.error('Failed to schedule check-in:', error);
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleDownloadApp = () => {
    // Detect platform and redirect to appropriate app store
    const userAgent = navigator.userAgent.toLowerCase();
    if (/iphone|ipad|ipod/.test(userAgent)) {
      window.open('https://apps.apple.com/app/mingus-financial-wellness', '_blank');
    } else if (/android/.test(userAgent)) {
      window.open('https://play.google.com/store/apps/details?id=com.mingus.app', '_blank');
    } else {
      // Show QR code or app store options
      window.open('/mobile-app-download', '_blank');
    }
  };

  const handleGoToDashboard = () => {
    if (onComplete) {
      onComplete();
    } else {
      navigate('/dashboard');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Preparing your celebration...</h2>
          <p className="text-gray-600">Setting up your personalized experience</p>
        </div>
      </div>
    );
  }

  if (currentStep === 'congratulations') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header with celebration animation */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-8 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-black opacity-10"></div>
            <div className="relative z-10">
              <div className="text-8xl mb-6 animate-bounce">🎉</div>
              <h1 className="text-4xl font-bold mb-4">
                Welcome to the Mingus Community!
              </h1>
              <p className="text-xl opacity-90">
                You've successfully completed your financial wellness setup
              </p>
            </div>
            
            {/* Floating celebration elements */}
            <div className="absolute top-4 left-4 text-2xl animate-pulse">✨</div>
            <div className="absolute top-8 right-8 text-3xl animate-spin">🌟</div>
            <div className="absolute bottom-4 left-8 text-2xl animate-bounce">💫</div>
            <div className="absolute bottom-8 right-4 text-3xl animate-pulse">🎊</div>
          </div>

          <div className="p-8">
            {/* Empowerment Message */}
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                You're Now Empowered to Transform Your Financial Future
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                You've taken the first step toward financial wellness. Your personalized dashboard, 
                insights, and community support are ready to help you achieve your goals.
              </p>
            </div>

            {/* Achievement Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                <div className="text-3xl mb-2">✅</div>
                <h3 className="font-semibold text-green-800 mb-1">Profile Complete</h3>
                <p className="text-base leading-relaxed text-green-700">
                  {completionData?.profile_completion || 100}% of your profile is set up
                </p>
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
                <div className="text-3xl mb-2">🎯</div>
                <h3 className="font-semibold text-blue-800 mb-1">Goals Set</h3>
                <p className="text-base leading-relaxed text-blue-700">
                  {completionData?.goals_count || 0} financial goals configured
                </p>
              </div>
              
              <div className="bg-purple-50 border border-purple-200 rounded-xl p-6 text-center">
                <div className="text-3xl mb-2">💡</div>
                <h3 className="font-semibold text-purple-800 mb-1">Insights Active</h3>
                <p className="text-base leading-relaxed text-purple-700">
                  Personalized recommendations ready
                </p>
              </div>
            </div>

            {/* Community Celebration */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-6 mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Join {completionData?.community_stats.total_members.toLocaleString()}+ Members
                  </h3>
                  <p className="text-gray-600 mb-4">
                    You're now part of a community of {completionData?.community_stats.active_this_week.toLocaleString()} 
                    active members this week, with an average savings of ${completionData?.community_stats.average_savings}.
                  </p>
                  <div className="flex items-center space-x-4 text-base leading-relaxed text-gray-500">
                    <span>👥 {completionData?.community_stats.total_members.toLocaleString()} total members</span>
                    <span>🔥 {completionData?.community_stats.active_this_week.toLocaleString()} active this week</span>
                    <span>💰 ${completionData?.community_stats.average_savings} average savings</span>
                  </div>
                </div>
                <div className="text-4xl">🤝</div>
              </div>
            </div>

            {/* First Check-in Invitation */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-xl p-6 mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Ready for Your First Weekly Check-in?
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Set up your first wellness check-in reminder to start building healthy financial habits.
                    It only takes 2 minutes and helps you track your progress.
                  </p>
                  <div className="flex items-center space-x-2 text-base leading-relaxed text-gray-500">
                    <span>⏰ Takes 2 minutes</span>
                    <span>📊 Track your progress</span>
                    <span>🎯 Build healthy habits</span>
                  </div>
                </div>
                <div className="text-4xl">📅</div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleScheduleCheckin}
                disabled={savingPreferences}
                className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white font-semibold py-4 px-8 rounded-xl hover:from-green-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savingPreferences ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Setting up...
                  </>
                ) : (
                  'Schedule My First Check-in'
                )}
              </button>
              
              <button
                onClick={handleGoToDashboard}
                className="flex-1 bg-gray-100 text-gray-700 font-semibold py-4 px-8 rounded-xl hover:bg-gray-200 transition-all duration-300"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Engagement Setup Step
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 text-center">
          <div className="text-6xl mb-4">🚀</div>
          <h1 className="text-3xl font-bold mb-2">
            Set Up Your Ongoing Engagement
          </h1>
          <p className="text-xl opacity-90">
            Customize your experience and stay connected
          </p>
        </div>

        <div className="p-8">
          {/* Check-in Reminder Setup */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Weekly Check-in Reminders
            </h2>
            
            <div className="bg-gray-50 rounded-xl p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Enable Weekly Reminders</h3>
                  <p className="text-gray-600">Get gentle nudges to complete your wellness check-ins</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reminderPreferences.enabled}
                    onChange={(e) => setReminderPreferences(prev => ({
                      ...prev,
                      enabled: e.target.checked
                    }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {reminderPreferences.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">Frequency</label>
                    <select
                      value={reminderPreferences.frequency}
                      onChange={(e) => setReminderPreferences(prev => ({
                        ...prev,
                        frequency: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="weekly">Weekly</option>
                      <option value="biweekly">Every 2 weeks</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">Day</label>
                    <select
                      value={reminderPreferences.day}
                      onChange={(e) => setReminderPreferences(prev => ({
                        ...prev,
                        day: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="monday">Monday</option>
                      <option value="tuesday">Tuesday</option>
                      <option value="wednesday">Wednesday</option>
                      <option value="thursday">Thursday</option>
                      <option value="friday">Friday</option>
                      <option value="saturday">Saturday</option>
                      <option value="sunday">Sunday</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">Time</label>
                    <select
                      value={reminderPreferences.time}
                      onChange={(e) => setReminderPreferences(prev => ({
                        ...prev,
                        time: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="09:00">9:00 AM</option>
                      <option value="10:00">10:00 AM</option>
                      <option value="11:00">11:00 AM</option>
                      <option value="12:00">12:00 PM</option>
                      <option value="13:00">1:00 PM</option>
                      <option value="14:00">2:00 PM</option>
                      <option value="15:00">3:00 PM</option>
                      <option value="16:00">4:00 PM</option>
                      <option value="17:00">5:00 PM</option>
                      <option value="18:00">6:00 PM</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Notification Preferences */}
            <div className="bg-gray-50 rounded-xl p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Notification Preferences</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reminderPreferences.email}
                    onChange={(e) => setReminderPreferences(prev => ({
                      ...prev,
                      email: e.target.checked
                    }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-base leading-relaxed font-medium text-gray-900">Email Notifications</span>
                </label>
                
                <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reminderPreferences.push}
                    onChange={(e) => setReminderPreferences(prev => ({
                      ...prev,
                      push: e.target.checked
                    }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-base leading-relaxed font-medium text-gray-900">Push Notifications</span>
                </label>
              </div>
            </div>
          </div>

          {/* Mobile App Download */}
          {completionData?.mobile_app_available && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Get the Mobile App
              </h2>
              
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      Take Mingus With You
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Download our mobile app for quick check-ins, real-time insights, and 
                      notifications on the go. Available for iOS and Android.
                    </p>
                    <div className="flex items-center space-x-4 text-base leading-relaxed text-gray-500">
                      <span>📱 Quick check-ins</span>
                      <span>🔔 Real-time notifications</span>
                      <span>📊 Mobile insights</span>
                    </div>
                  </div>
                  <div className="text-6xl">📱</div>
                </div>
                
                <button
                  onClick={handleDownloadApp}
                  className="mt-4 w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-300"
                >
                  Download Mobile App
                </button>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGoToDashboard}
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-4 px-8 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105"
            >
              Start My Journey
            </button>
            
            <button
              onClick={() => setCurrentStep('congratulations')}
              className="flex-1 bg-gray-100 text-gray-700 font-semibold py-4 px-8 rounded-xl hover:bg-gray-200 transition-all duration-300"
            >
              Back to Summary
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingCompletion; 