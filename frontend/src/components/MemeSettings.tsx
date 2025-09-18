import React, { useState, useEffect, useCallback } from 'react';

// Types for meme preferences
export interface MemePreferences {
  enabled: boolean;
  categories: {
    faith: boolean;
    work_life: boolean;
    friendships: boolean;
    children: boolean;
    relationships: boolean;
    going_out: boolean;
  };
  frequency: 'every_login' | 'once_per_day' | 'weekly';
}

export interface MemeSettingsProps {
  userId?: string;
  onPreferencesChange?: (preferences: MemePreferences) => void;
  className?: string;
}

// Default preferences
const DEFAULT_PREFERENCES: MemePreferences = {
  enabled: true,
  categories: {
    faith: true,
    work_life: true,
    friendships: true,
    children: true,
    relationships: true,
    going_out: true,
  },
  frequency: 'once_per_day',
};

// Category labels and descriptions
const CATEGORY_INFO = {
  faith: {
    label: 'Faith & Spirituality',
    description: 'Religious and spiritual financial struggles',
  },
  work_life: {
    label: 'Work & Career',
    description: 'Work-related financial challenges and career expenses',
  },
  friendships: {
    label: 'Friendships',
    description: 'Social spending and friend-related expenses',
  },
  children: {
    label: 'Children & Family',
    description: 'Parenting and child-related financial stress',
  },
  relationships: {
    label: 'Relationships',
    description: 'Dating, marriage, and relationship financial dynamics',
  },
  going_out: {
    label: 'Going Out',
    description: 'Entertainment, dining out, and social activities',
  },
};

// Frequency options
const FREQUENCY_OPTIONS = [
  {
    value: 'every_login' as const,
    label: 'Every Login',
    description: 'Show a meme every time you log in',
  },
  {
    value: 'once_per_day' as const,
    label: 'Once Per Day',
    description: 'Show one meme per day maximum',
  },
  {
    value: 'weekly' as const,
    label: 'Weekly',
    description: 'Show one meme per week maximum',
  },
];

const MemeSettings: React.FC<MemeSettingsProps> = ({
  userId,
  onPreferencesChange,
  className = '',
}) => {
  // State management
  const [preferences, setPreferences] = useState<MemePreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewMeme, setPreviewMeme] = useState<any>(null);

  // Fetch user preferences from API
  const fetchPreferences = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/user-meme-preferences/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences(data.preferences || DEFAULT_PREFERENCES);
      } else if (response.status === 404) {
        // User has no preferences yet, use defaults
        setPreferences(DEFAULT_PREFERENCES);
      } else {
        throw new Error('Failed to fetch preferences');
      }
    } catch (err) {
      console.error('Error fetching preferences:', err);
      setError('Failed to load your meme preferences. Using default settings.');
      setPreferences(DEFAULT_PREFERENCES);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Save preferences to API
  const savePreferences = useCallback(async (newPreferences: MemePreferences) => {
    if (!userId) {
      setError('User ID is required to save preferences');
      return false;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch(`/api/user-meme-preferences/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        credentials: 'include',
        body: JSON.stringify({ preferences: newPreferences }),
      });

      if (response.ok) {
        setSuccess('Your meme preferences have been saved successfully!');
        setPreferences(newPreferences);
        onPreferencesChange?.(newPreferences);
        return true;
      } else {
        throw new Error('Failed to save preferences');
      }
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError('Failed to save your preferences. Please try again.');
      return false;
    } finally {
      setSaving(false);
    }
  }, [userId, onPreferencesChange]);

  // Preview memes functionality
  const previewMemes = useCallback(async () => {
    try {
      setPreviewLoading(true);
      setError(null);

      const response = await fetch('/api/user-meme', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId || '',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const meme = await response.json();
        setPreviewMeme(meme);
      } else {
        throw new Error('Failed to load preview meme');
      }
    } catch (err) {
      console.error('Error loading preview meme:', err);
      setError('Failed to load preview meme. Please try again.');
    } finally {
      setPreviewLoading(false);
    }
  }, [userId]);

  // Reset to default preferences
  const resetPreferences = useCallback(async () => {
    const confirmed = window.confirm(
      'Are you sure you want to reset all meme preferences to default settings?'
    );
    
    if (confirmed) {
      await savePreferences(DEFAULT_PREFERENCES);
    }
  }, [savePreferences]);

  // Handle preference changes with optimistic updates
  const handlePreferenceChange = useCallback(async (
    key: keyof MemePreferences,
    value: any
  ) => {
    const newPreferences = { ...preferences, [key]: value };
    setPreferences(newPreferences);
    
    // Auto-save after a short delay
    setTimeout(() => {
      savePreferences(newPreferences);
    }, 500);
  }, [preferences, savePreferences]);

  // Handle category toggle
  const handleCategoryToggle = useCallback(async (category: keyof MemePreferences['categories']) => {
    const newCategories = {
      ...preferences.categories,
      [category]: !preferences.categories[category],
    };
    
    await handlePreferenceChange('categories', newCategories);
  }, [preferences.categories, handlePreferenceChange]);

  // Load preferences on mount
  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  // Clear success message after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  // Loading state
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white mb-2">
          Meme Splash Page Settings
        </h2>
        <p className="text-slate-300 text-sm">
          Customize your daily meme experience. Choose which categories you'd like to see
          and how often memes should appear.
        </p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="mb-4 p-3 bg-emerald-900/20 border border-emerald-600/30 rounded-md">
          <p className="text-emerald-200 text-sm">{success}</p>
        </div>
      )}
      
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-600/30 rounded-md">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Main Toggle */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white">Enable Daily Memes</h3>
            <p className="text-slate-300 text-sm">
              Turn on or off the meme splash page feature completely
            </p>
          </div>
          <button
            onClick={() => handlePreferenceChange('enabled', !preferences.enabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
              preferences.enabled ? 'bg-gradient-to-r from-violet-600 to-purple-600' : 'bg-slate-600'
            }`}
            role="switch"
            aria-checked={preferences.enabled}
            aria-label="Enable daily memes"
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-all duration-300 ${
                preferences.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Settings Content - Only show when enabled */}
      {preferences.enabled && (
        <div className="space-y-6">
          {/* Category Selection */}
          <fieldset>
            <legend className="text-lg font-medium text-white mb-3">Meme Categories</legend>
            <p className="text-slate-300 text-sm mb-4">
              Choose which types of memes you'd like to see. You can select multiple categories.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(CATEGORY_INFO).map(([category, info]) => (
                <label
                  key={category}
                  className="flex items-start space-x-3 p-3 border border-slate-600 rounded-lg hover:bg-slate-700 hover:border-violet-500 cursor-pointer transition-all duration-300"
                >
                  <input
                    type="checkbox"
                    checked={preferences.categories[category as keyof MemePreferences['categories']]}
                    onChange={() => handleCategoryToggle(category as keyof MemePreferences['categories'])}
                    className="mt-1 h-4 w-4 text-violet-600 focus:ring-violet-500 focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-800 border-slate-500 rounded"
                    aria-describedby={`${category}-description`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white">
                      {info.label}
                    </div>
                    <div id={`${category}-description`} className="text-xs text-slate-400">
                      {info.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Frequency Selection */}
          <fieldset>
            <legend className="text-lg font-medium text-white mb-3">Frequency</legend>
            <p className="text-slate-300 text-sm mb-4">
              How often would you like to see memes?
            </p>
            
            <div className="space-y-2">
              {FREQUENCY_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className="flex items-center space-x-3 p-3 border border-slate-600 rounded-lg hover:bg-slate-700 hover:border-violet-500 cursor-pointer transition-all duration-300"
                >
                  <input
                    type="radio"
                    name="frequency"
                    value={option.value}
                    checked={preferences.frequency === option.value}
                    onChange={() => handlePreferenceChange('frequency', option.value)}
                    className="h-4 w-4 text-violet-600 focus:ring-violet-500 focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-800 border-slate-500"
                    aria-describedby={`${option.value}-description`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white">
                      {option.label}
                    </div>
                    <div id={`${option.value}-description`} className="text-xs text-slate-400">
                      {option.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Preview Section */}
          <div>
            <h3 className="text-lg font-medium text-white mb-3">Preview</h3>
            <p className="text-slate-300 text-sm mb-4">
              See what a meme would look like with your current settings.
            </p>
            
            <button
              onClick={previewMemes}
              disabled={previewLoading || saving}
              className="inline-flex items-center px-4 py-2 border border-slate-600 rounded-md shadow-sm text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 hover:border-violet-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {previewLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading...
                </>
              ) : (
                'Preview Memes'
              )}
            </button>

            {/* Preview Meme Display */}
            {previewMeme && (
              <div className="mt-4 p-4 border border-slate-600 rounded-lg bg-slate-700">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-16 h-16 bg-slate-600 rounded-lg flex items-center justify-center">
                      <span className="text-slate-300 text-xs">Meme</span>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white capitalize">
                      {previewMeme.category?.replace('_', ' ')}
                    </div>
                    <div className="text-sm text-slate-300 mt-1">
                      {previewMeme.caption}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-6 pt-6 border-t border-slate-700 flex flex-col sm:flex-row gap-3">
        <button
          onClick={resetPreferences}
          disabled={saving}
          className="inline-flex items-center px-4 py-2 border border-slate-600 rounded-md shadow-sm text-sm font-medium text-white bg-slate-700 hover:bg-slate-600 hover:border-violet-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
        >
          Reset to Defaults
        </button>
        
        {saving && (
          <div className="flex items-center text-sm text-slate-400">
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Saving...
          </div>
        )}
      </div>
    </div>
  );
};

export default MemeSettings;
