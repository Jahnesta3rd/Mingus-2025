import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserProfile {
  id?: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  zipCode?: string;
  dependentsCount?: number;
  relationshipStatus?: string;
  industry?: string;
  jobTitle?: string;
  employmentStatus?: string;
  profileCompletionPercentage?: number;
  onboardingStep?: number;
}

interface UserStore {
  user: UserProfile | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: UserProfile) => void;
  updateUser: (updates: Partial<UserProfile>) => void;
  clearUser: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // API calls
  fetchUserProfile: () => Promise<void>;
  updateUserProfile: (data: Partial<UserProfile>) => Promise<boolean>;
  saveOnboardingProgress: (step: number, data: Partial<UserProfile>) => Promise<boolean>;
  completeOnboarding: () => Promise<boolean>;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      error: null,
      
      setUser: (user) => set({ user }),
      
      updateUser: (updates) => {
        const currentUser = get().user;
        if (currentUser) {
          set({ user: { ...currentUser, ...updates } });
        }
      },
      
      clearUser: () => set({ user: null }),
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      setError: (error) => set({ error }),
      
      fetchUserProfile: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch('/api/user/profile', {
            credentials: 'include'
          });
          
          if (response.ok) {
            const data = await response.json();
            if (data.success) {
              set({ user: data.profile });
            }
          }
        } catch (error) {
          set({ error: 'Failed to fetch user profile' });
        } finally {
          set({ isLoading: false });
        }
      },
      
      updateUserProfile: async (data) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data)
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              set({ user: result.profile });
              return true;
            }
          }
          
          return false;
        } catch (error) {
          set({ error: 'Failed to update user profile' });
          return false;
        } finally {
          set({ isLoading: false });
        }
      },
      
      saveOnboardingProgress: async (step, data) => {
        try {
          const response = await fetch(`/api/onboarding/step/${step}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data)
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              get().updateUser(data);
              return true;
            }
          }
          
          return false;
        } catch (error) {
          set({ error: 'Failed to save onboarding progress' });
          return false;
        }
      },
      
      completeOnboarding: async () => {
        try {
          const response = await fetch('/api/onboarding/complete', {
            method: 'POST',
            credentials: 'include'
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              get().updateUser({ onboardingStep: 6 });
              return true;
            }
          }
          
          return false;
        } catch (error) {
          set({ error: 'Failed to complete onboarding' });
          return false;
        }
      }
    }),
    {
      name: 'user-store',
      partialize: (state) => ({ user: state.user })
    }
  )
);
