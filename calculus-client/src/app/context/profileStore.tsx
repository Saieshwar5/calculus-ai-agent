"use client";

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createSSRStorage } from '../utils/storage';
import { ProfileData, saveProfile, updateProfile, getProfile } from '../api/profileApis';

interface ProfileState {
  profile: ProfileData | null;
  isLoading: boolean;
  error: string | null;
  isSaving: boolean;
}

interface ProfileActions {
  // Profile operations
  saveProfileData: (profileData: ProfileData) => Promise<{ success: boolean; error?: string }>;
  updateProfileData: (profileData: ProfileData) => Promise<{ success: boolean; error?: string }>;
  fetchProfile: () => Promise<{ success: boolean; error?: string }>;
  clearProfile: () => void;
  
  // State management
  setProfile: (profile: ProfileData) => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  setSaving: (isSaving: boolean) => void;
  clearError: () => void;
  
  // Validation
  validateProfile: (profileData: ProfileData) => { isValid: boolean; errors: string[] };
  hasAllRequiredFields: (profileData: ProfileData) => boolean;
}

const initialState: ProfileState = {
  profile: null,
  isLoading: false,
  error: null,
  isSaving: false,
};

export const useProfileStore = create<ProfileState & ProfileActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Validation function
      validateProfile: (profileData: ProfileData) => {
        const errors: string[] = [];

        // Username validation
        if (!profileData.username || profileData.username.trim().length === 0) {
          errors.push('Username is required');
        } else if (profileData.username.trim().length < 2) {
          errors.push('Username must be at least 2 characters');
        } else if (profileData.username.trim().length > 50) {
          errors.push('Username must be less than 50 characters');
        }

        // Date of Birth validation
        if (!profileData.dateOfBirth) {
          errors.push('Date of birth is required');
        } else {
          const birthDate = new Date(profileData.dateOfBirth);
          const today = new Date();
          const age = today.getFullYear() - birthDate.getFullYear();
          
          if (isNaN(birthDate.getTime())) {
            errors.push('Invalid date of birth');
          } else if (birthDate > today) {
            errors.push('Date of birth cannot be in the future');
          } else if (age < 13) {
            errors.push('You must be at least 13 years old');
          } else if (age > 120) {
            errors.push('Invalid date of birth');
          }
        }

        // Country validation
        if (!profileData.country || profileData.country.trim().length === 0) {
          errors.push('Country is required');
        } else if (profileData.country.trim().length < 2) {
          errors.push('Country name must be at least 2 characters');
        }

        // Education validation
        if (!profileData.education || profileData.education.trim().length === 0) {
          errors.push('Education is required');
        }

        // Mother Tongue validation
        if (!profileData.motherTongue || profileData.motherTongue.trim().length === 0) {
          errors.push('Mother tongue is required');
        }

        // Gender validation
        if (!profileData.gender) {
          errors.push('Gender is required');
        } else if (!['Male', 'Female', 'Others'].includes(profileData.gender)) {
          errors.push('Invalid gender selection');
        }

        // Learning Pace validation
        if (!profileData.learningPace) {
          errors.push('Learning pace is required');
        } else if (!['Low', 'Medium', 'High'].includes(profileData.learningPace)) {
          errors.push('Invalid learning pace selection');
        }

        return {
          isValid: errors.length === 0,
          errors,
        };
      },

      // Check if all required fields are filled
      hasAllRequiredFields: (profileData: ProfileData) => {
        return !!(
          profileData.username?.trim() &&
          profileData.dateOfBirth &&
          profileData.country?.trim() &&
          profileData.education?.trim() &&
          profileData.motherTongue?.trim() &&
          profileData.gender &&
          profileData.learningPace
        );
      },

      // Save profile (create new)
      saveProfileData: async (profileData: ProfileData) => {
        const { validateProfile } = get();
        
        // Validate before sending
        const validation = validateProfile(profileData);
        if (!validation.isValid) {
          const errorMessage = validation.errors.join(', ');
          set({ error: errorMessage });
          console.error('❌ Validation failed:', validation.errors);
          return { success: false, error: errorMessage };
        }

        set({ isSaving: true, error: null });

        try {
          const result = await saveProfile(profileData);
          
          if (result.success && result.data) {
            set({ 
              profile: result.data, 
              isSaving: false,
              error: null 
            });
            return { success: true };
          } else {
            set({ 
              isSaving: false, 
              error: result.error || 'Failed to save profile' 
            });
            return { success: false, error: result.error };
          }
        } catch (error) {
          const errorMessage = (error as Error).message || 'Failed to save profile';
          set({ 
            isSaving: false, 
            error: errorMessage 
          });
          return { success: false, error: errorMessage };
        }
      },

      // Update existing profile
      updateProfileData: async (profileData: ProfileData) => {
        const { validateProfile } = get();
        
        // Validate before sending
        const validation = validateProfile(profileData);
        if (!validation.isValid) {
          const errorMessage = validation.errors.join(', ');
          set({ error: errorMessage });
          console.error('❌ Validation failed:', validation.errors);
          return { success: false, error: errorMessage };
        }

        set({ isSaving: true, error: null });

        try {
          const result = await updateProfile(profileData);
          
          if (result.success && result.data) {
            set({ 
              profile: result.data, 
              isSaving: false,
              error: null 
            });
            return { success: true };
          } else {
            set({ 
              isSaving: false, 
              error: result.error || 'Failed to update profile' 
            });
            return { success: false, error: result.error };
          }
        } catch (error) {
          const errorMessage = (error as Error).message || 'Failed to update profile';
          set({ 
            isSaving: false, 
            error: errorMessage 
          });
          return { success: false, error: errorMessage };
        }
      },

      // Fetch profile from server
      fetchProfile: async () => {
        set({ isLoading: true, error: null });

        try {
          const result = await getProfile();
          
          if (result.success && result.data) {
            set({ 
              profile: result.data, 
              isLoading: false,
              error: null 
            });
            return { success: true };
          } else {
            set({ 
              isLoading: false, 
              error: result.error || 'Failed to fetch profile' 
            });
            return { success: false, error: result.error };
          }
        } catch (error) {
          const errorMessage = (error as Error).message || 'Failed to fetch profile';
          set({ 
            isLoading: false, 
            error: errorMessage 
          });
          return { success: false, error: errorMessage };
        }
      },

      // Clear profile from store
      clearProfile: () => {
        set({ 
          profile: null, 
          error: null,
          isLoading: false,
          isSaving: false
        });
      },

      // State setters
      setProfile: (profile: ProfileData) => {
        set({ profile });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setLoading: (isLoading: boolean) => {
        set({ isLoading });
      },

      setSaving: (isSaving: boolean) => {
        set({ isSaving });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'profile-storage',
      storage: createSSRStorage() as any,
      // Only persist profile data, not loading/error states
      partialize: (state) => ({
        profile: state.profile,
      }) as any,
    }
  )
);

