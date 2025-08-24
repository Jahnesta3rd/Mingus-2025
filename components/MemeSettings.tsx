import React, { useState, useEffect, useCallback } from 'react';

// TypeScript interfaces
interface MemePreferences {
  memes_enabled: boolean;
  preferred_categories: string[];
  frequency_setting: 'every_login' | 'once_per_day' | 'weekly';
  custom_frequency_days?: number;
  last_meme_shown_at?: string;
  opt_out_reason?: string;
  opt_out_date?: string;
}

interface MemeAnalytics {
  total_interactions: number;
  interactions_by_type: Record<string, number>;
  favorite_categories: string[];
  skip_rate: number;
  engagement_rate: number;
  last_updated: string;
}

interface MemePreview {
  id: string;
  image_url: string;
  caption: string;
  category: string;
  alt_text: string;
}

interface MemeSettingsProps {
  userId: string;
  onClose?: () => void;
  className?: string;
}

// Meme categories with descriptions
const MEME_CATEGORIES = [
  {
    id: 'faith',
    label: 'Faith & Spirituality',
    description: 'Inspirational content related to faith, spirituality, and personal growth',
    icon: '🙏'
  },
  {
    id: 'work_life',
    label: 'Work & Career',
    description: 'Motivational content about professional development and work-life balance',
    icon: '💼'
  },
  {
    id: 'friendships',
    label: 'Friendships',
    description: 'Content about building and maintaining meaningful friendships',
    icon: '👥'
  },
  {
    id: 'children',
    label: 'Parenting & Children',
    description: 'Family-focused content about parenting and raising children',
    icon: '👶'
  },
  {
    id: 'relationships',
    label: 'Relationships',
    description: 'Content about romantic relationships and partnership',
    icon: '❤️'
  },
  {
    id: 'going_out',
    label: 'Social Life',
    description: 'Content about social activities, entertainment, and leisure',
    icon: '🎉'
  }
];

// Frequency options
const FREQUENCY_OPTIONS = [
  {
    value: 'every_login',
    label: 'Every Login',
    description: 'See a meme every time you log into MINGUS'
  },
  {
    value: 'once_per_day',
    label: 'Once Per Day',
    description: 'See one meme per day, even with multiple logins'
  },
  {
    value: 'weekly',
    label: 'Weekly',
    description: 'See one meme per week'
  }
];

// Loading skeleton component
const SettingsSkeleton: React.FC = () => (
  <div className="animate-pulse space-y-6">
    <div className="h-8 bg-gray-200 rounded w-1/3"></div>
    <div className="space-y-4">
      <div className="h-6 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    </div>
    <div className="space-y-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="h-16 bg-gray-200 rounded"></div>
      ))}
    </div>
  </div>
);

// Main component
const MemeSettings: React.FC<MemeSettingsProps> = ({
  userId,
  onClose,
  className = ''
}) => {
  // State management
  const [preferences, setPreferences] = useState<MemePreferences>({
    memes_enabled: true,
    preferred_categories: [],
    frequency_setting: 'once_per_day'
  });
  const [analytics, setAnalytics] = useState<MemeAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewMeme, setPreviewMeme] = useState<MemePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Fetch user preferences
  const fetchPreferences = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/user-meme-preferences/${userId}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Map API response to our interface
        const mappedPreferences: MemePreferences = {
          memes_enabled: data.preferences.memes_enabled,
          preferred_categories: data.preferences.preferred_categories || [],
          frequency_setting: mapFrequencySetting(data.preferences.frequency_setting),
          custom_frequency_days: data.preferences.custom_frequency_days,
          last_meme_shown_at: data.preferences.last_meme_shown_at,
          opt_out_reason: data.preferences.opt_out_reason,
          opt_out_date: data.preferences.opt_out_date
        };

        setPreferences(mappedPreferences);
        setAnalytics(data.analytics);
      } else {
        throw new Error(data.error || 'Failed to load preferences');
      }
    } catch (err) {
      console.error('Error fetching preferences:', err);
      setError(err instanceof Error ? err.message : 'Failed to load preferences');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Map API frequency setting to our interface
  const mapFrequencySetting = (apiSetting: string): MemePreferences['frequency_setting'] => {
    switch (apiSetting) {
      case 'daily':
        return 'once_per_day';
      case 'weekly':
        return 'weekly';
      case 'disabled':
        return 'once_per_day'; // Default fallback
      default:
        return 'once_per_day';
    }
  };

  // Map our frequency setting to API format
  const mapToApiFrequency = (setting: MemePreferences['frequency_setting']): string => {
    switch (setting) {
      case 'every_login':
        return 'daily'; // API doesn't have every_login, use daily
      case 'once_per_day':
        return 'daily';
      case 'weekly':
        return 'weekly';
      default:
        return 'daily';
    }
  };

  // Save preferences
  const savePreferences = useCallback(async (newPreferences: MemePreferences) => {
    try {
      setSaving(true);
      setError(null);

      const apiData = {
        memes_enabled: newPreferences.memes_enabled,
        preferred_categories: newPreferences.preferred_categories,
        frequency_setting: mapToApiFrequency(newPreferences.frequency_setting),
        custom_frequency_days: newPreferences.custom_frequency_days || 1
      };

      const response = await fetch(`/api/user-meme-preferences/${userId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setPreferences(newPreferences);
        setSuccess('Preferences saved successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error(data.error || 'Failed to save preferences');
      }
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError(err instanceof Error ? err.message : 'Failed to save preferences');
    } finally {
      setSaving(false);
    }
  }, [userId]);

  // Reset preferences to defaults
  const resetPreferences = useCallback(async () => {
    const defaultPreferences: MemePreferences = {
      memes_enabled: true,
      preferred_categories: ['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out'],
      frequency_setting: 'once_per_day'
    };

    await savePreferences(defaultPreferences);
  }, [savePreferences]);

  // Preview meme functionality
  const handlePreviewMeme = useCallback(async () => {
    try {
      setPreviewLoading(true);
      setError(null);

      const response = await fetch('/api/user-meme', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.meme) {
        setPreviewMeme({
          id: data.meme.id,
          image_url: data.meme.image_url,
          caption: data.meme.caption,
          category: data.meme.category,
          alt_text: data.meme.alt_text
        });
        setShowPreview(true);
      } else {
        throw new Error('No meme available for preview');
      }
    } catch (err) {
      console.error('Error previewing meme:', err);
      setError(err instanceof Error ? err.message : 'Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  }, []);

  // Handle preference changes
  const handleToggleChange = (enabled: boolean) => {
    const newPreferences = { ...preferences, memes_enabled: enabled };
    setPreferences(newPreferences);
    savePreferences(newPreferences);
  };

  const handleCategoryToggle = (categoryId: string) => {
    const newCategories = preferences.preferred_categories.includes(categoryId)
      ? preferences.preferred_categories.filter(cat => cat !== categoryId)
      : [...preferences.preferred_categories, categoryId];
    
    const newPreferences = { ...preferences, preferred_categories: newCategories };
    setPreferences(newPreferences);
    savePreferences(newPreferences);
  };

  const handleFrequencyChange = (frequency: MemePreferences['frequency_setting']) => {
    const newPreferences = { ...preferences, frequency_setting: frequency };
    setPreferences(newPreferences);
    savePreferences(newPreferences);
  };

  // Load preferences on mount
  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  // Loading state
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
        <SettingsSkeleton />
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Meme Settings</h2>
            <p className="text-blue-100 text-sm">Customize your daily inspiration experience</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-white hover:text-blue-100 transition-colors"
              aria-label="Close settings"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Success/Error Messages */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 transition-all duration-300">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-green-800 font-medium">{success}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 transition-all duration-300">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800 font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Main Toggle */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Daily Memes</h3>
              <p className="text-gray-600 text-sm">
                {preferences.memes_enabled 
                  ? 'Get inspired with daily motivational content'
                  : 'Daily memes are currently disabled'
                }
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.memes_enabled}
                onChange={(e) => handleToggleChange(e.target.checked)}
                className="sr-only peer"
                disabled={saving}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 disabled:opacity-50"></div>
            </label>
          </div>
        </div>

        {/* Category Selection */}
        {preferences.memes_enabled && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Content Categories</h3>
              <p className="text-gray-600 text-sm mb-4">
                Choose which types of content you'd like to see. Select all that interest you.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {MEME_CATEGORIES.map((category) => (
                <label
                  key={category.id}
                  className={`relative flex items-start p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    preferences.preferred_categories.includes(category.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={preferences.preferred_categories.includes(category.id)}
                    onChange={() => handleCategoryToggle(category.id)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    disabled={saving}
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center">
                      <span className="text-2xl mr-2">{category.icon}</span>
                      <span className="font-medium text-gray-900">{category.label}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{category.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Frequency Settings */}
        {preferences.memes_enabled && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Frequency</h3>
              <p className="text-gray-600 text-sm mb-4">
                How often would you like to see memes?
              </p>
            </div>
            
            <div className="space-y-3">
              {FREQUENCY_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className={`relative flex items-start p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    preferences.frequency_setting === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="frequency"
                    value={option.value}
                    checked={preferences.frequency_setting === option.value}
                    onChange={() => handleFrequencyChange(option.value as MemePreferences['frequency_setting'])}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    disabled={saving}
                  />
                  <div className="ml-3 flex-1">
                    <div className="font-medium text-gray-900">{option.label}</div>
                    <p className="text-sm text-gray-600">{option.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Section */}
        {analytics && preferences.memes_enabled && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Your Engagement</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{analytics.total_interactions}</div>
                <div className="text-sm text-gray-600">Total Views</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{analytics.engagement_rate}%</div>
                <div className="text-sm text-gray-600">Engagement Rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{analytics.skip_rate}%</div>
                <div className="text-sm text-gray-600">Skip Rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{analytics.favorite_categories.length}</div>
                <div className="text-sm text-gray-600">Favorite Categories</div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
                     <button
             onClick={handlePreviewMeme}
             disabled={previewLoading || !preferences.memes_enabled}
             className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50"
           >
            {previewLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading Preview...
              </span>
            ) : (
              'Preview Memes'
            )}
          </button>
          
          <button
            onClick={resetPreferences}
            disabled={saving}
            className="flex-1 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-800 font-semibold py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-gray-500 focus:ring-opacity-50"
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      {/* Meme Preview Modal */}
      {showPreview && previewMeme && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50 transition-opacity duration-300"
          onClick={() => setShowPreview(false)}
        >
          <div
            className="bg-white rounded-lg max-w-md w-full overflow-hidden shadow-xl transform transition-all duration-300"
            onClick={(e) => e.stopPropagation()}
          >
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Sample Meme</h3>
                  <button
                    onClick={() => setShowPreview(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label="Close preview"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div className="p-4">
                <div className="bg-gray-100 rounded-lg overflow-hidden mb-4">
                  <img
                    src={previewMeme.image_url}
                    alt={previewMeme.alt_text}
                    className="w-full h-auto"
                    loading="lazy"
                  />
                </div>
                
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-600 capitalize">{previewMeme.category.replace('_', ' ')}</span>
                  <span className="text-xs text-gray-500">Sample Content</span>
                </div>
                
                <p className="text-gray-800 text-center text-lg font-medium leading-relaxed">
                  {previewMeme.caption}
                </p>
              </div>
              
              <div className="p-4 border-t border-gray-200">
                <button
                  onClick={() => setShowPreview(false)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Got it!
                </button>
                             </div>
             </div>
           </div>
         )}
       </div>
     );
   };

export default MemeSettings;
