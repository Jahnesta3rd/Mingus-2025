import React, { useState, useEffect } from 'react';
import { 
  UserIcon, 
  HomeIcon, 
  MapPinIcon, 
  CalendarIcon,
  CurrencyDollarIcon,
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import { useDashboardStore, useDashboardSelectors } from '../stores/dashboardStore';

interface UserProfile {
  id: string;
  name: string;
  email: string;
  current_address?: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
  };
  vehicle_info?: {
    make: string;
    model: string;
    year: number;
    monthly_miles: number;
  };
  preferences?: {
    max_commute_time: number;
    preferred_housing_type: string;
    budget_range: {
      min: number;
      max: number;
    };
    priority_factors: string[];
  };
}

interface HousingProfileIntegrationProps {
  className?: string;
}

const HousingProfileIntegration: React.FC<HousingProfileIntegrationProps> = ({ className = '' }) => {
  const { user } = useAuth();
  const { setLeaseInfo, updateLeaseInfo } = useDashboardStore();
  const { leaseInfo, housingSearches, housingScenarios } = useDashboardSelectors();
  
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEditForm, setShowEditForm] = useState(false);

  useEffect(() => {
    if (user) {
      fetchUserProfile();
    }
  }, [user]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'X-CSRF-Token': 'test-token'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const data = await response.json();
      setProfile(data.profile);
      
      // Sync profile data with housing store
      if (data.profile.current_address) {
        // Update lease info if we have address data
        setLeaseInfo({
          id: 'current-lease',
          property_address: `${data.profile.current_address.street}, ${data.profile.current_address.city}, ${data.profile.current_address.state} ${data.profile.current_address.zip_code}`,
          lease_start_date: new Date().toISOString(),
          lease_end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year from now
          monthly_rent: data.profile.preferences?.budget_range?.max || 0,
          is_active: true,
          renewal_reminder_days: 60
        });
      }
      
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (updates: Partial<UserProfile>) => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'X-CSRF-Token': 'test-token',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ profile: updates })
      });

      if (!response.ok) {
        throw new Error('Failed to update profile');
      }

      const data = await response.json();
      setProfile(data.profile);
      
      // Update housing store if address changed
      if (updates.current_address) {
        updateLeaseInfo({
          property_address: `${updates.current_address.street}, ${updates.current_address.city}, ${updates.current_address.state} ${updates.current_address.zip_code}`
        });
      }
      
      setShowEditForm(false);
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const getProfileCompleteness = () => {
    if (!profile) return 0;
    
    let completed = 0;
    const total = 5;
    
    if (profile.current_address) completed++;
    if (profile.vehicle_info) completed++;
    if (profile.preferences?.budget_range) completed++;
    if (profile.preferences?.max_commute_time) completed++;
    if (profile.preferences?.priority_factors?.length) completed++;
    
    return Math.round((completed / total) * 100);
  };

  const getMissingFields = () => {
    if (!profile) return [];
    
    const missing = [];
    if (!profile.current_address) missing.push('Current Address');
    if (!profile.vehicle_info) missing.push('Vehicle Information');
    if (!profile.preferences?.budget_range) missing.push('Budget Range');
    if (!profile.preferences?.max_commute_time) missing.push('Max Commute Time');
    if (!profile.preferences?.priority_factors?.length) missing.push('Priority Factors');
    
    return missing;
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-red-600">
          <ExclamationTriangleIcon className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const completeness = getProfileCompleteness();
  const missingFields = getMissingFields();

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <UserIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Profile Integration</h3>
              <p className="text-sm text-gray-500">Housing preferences sync</p>
            </div>
          </div>
          <button
            onClick={() => setShowEditForm(true)}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Edit Profile
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Profile Completeness */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-900">Profile Completeness</h4>
            <span className="text-sm text-gray-500">{completeness}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                completeness >= 80 ? 'bg-green-500' : 
                completeness >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${completeness}%` }}
            ></div>
          </div>
          {completeness < 100 && (
            <p className="text-xs text-gray-500 mt-1">
              Complete your profile for better housing recommendations
            </p>
          )}
        </div>

        {/* Current Information */}
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Current Information</h4>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <MapPinIcon className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {profile?.current_address ? 
                    `${profile.current_address.city}, ${profile.current_address.state}` : 
                    'No address set'
                  }
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <HomeIcon className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {profile?.preferences?.budget_range ? 
                    `$${profile.preferences.budget_range.min}-${profile.preferences.budget_range.max}/mo` : 
                    'No budget set'
                  }
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <CalendarIcon className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {profile?.preferences?.max_commute_time ? 
                    `${profile.preferences.max_commute_time} min max commute` : 
                    'No commute preference'
                  }
                </span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Housing Activity</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Recent Searches</span>
                <span className="text-sm font-medium text-gray-900">{housingSearches.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Saved Scenarios</span>
                <span className="text-sm font-medium text-gray-900">{housingScenarios.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Profile Sync</span>
                <span className="text-sm font-medium text-green-600">Active</span>
              </div>
            </div>
          </div>
        </div>

        {/* Missing Fields Alert */}
        {missingFields.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">Complete Your Profile</h4>
                <p className="text-sm text-yellow-700 mt-1">
                  Add the following information for better housing recommendations:
                </p>
                <ul className="text-sm text-yellow-700 mt-2 list-disc list-inside">
                  {missingFields.map((field) => (
                    <li key={field}>{field}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-3">
            <button 
              onClick={() => setShowEditForm(true)}
              className="flex items-center justify-center space-x-2 p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <CogIcon className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-600">Edit Profile</span>
            </button>
            <button 
              onClick={fetchUserProfile}
              className="flex items-center justify-center space-x-2 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <CheckCircleIcon className="h-4 w-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-600">Sync Data</span>
            </button>
          </div>
        </div>
      </div>

      {/* Edit Form Modal */}
      {showEditForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Edit Profile
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                This would contain a form to edit profile information. 
                For now, this is a placeholder.
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowEditForm(false)}
                  className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setShowEditForm(false)}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HousingProfileIntegration;
