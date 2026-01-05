/**
 * Unit and Integration Tests for Profile Store
 * 
 * This file contains comprehensive tests for:
 * - Validation functions
 * - Save profile action
 * - Update profile action
 * - Fetch profile action
 * - Clear profile action
 * - State management functions
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import '@testing-library/jest-dom';
import { useProfileStore } from '../profileStore';
import { ProfileData } from '../../api/profileApis';
import * as profileAPI from '../../api/profileApis';

// Mock the API module
vi.mock('../../api/profileApis', () => ({
  saveProfile: vi.fn(),
  updateProfile: vi.fn(),
  getProfile: vi.fn(),
}));

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Helper function to create valid profile data
const createValidProfile = (overrides?: Partial<ProfileData>): ProfileData => {
  const today = new Date();
  const birthDate = new Date(today.getFullYear() - 25, today.getMonth(), today.getDate());
  
  return {
    username: 'testuser',
    dateOfBirth: birthDate.toISOString().split('T')[0],
    country: 'United States',
    education: 'Bachelor\'s Degree',
    motherTongue: 'English',
    gender: 'Male',
    learningPace: 'Medium',
    ...overrides,
  };
};

describe('Profile Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useProfileStore.setState({
      profile: null,
      isLoading: false,
      error: null,
      isSaving: false,
    });
    
    // Clear sessionStorage
    sessionStorageMock.clear();
    
    // Clear all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Validation Functions', () => {
    describe('validateProfile', () => {
      it('should validate a complete and valid profile', () => {
        const store = useProfileStore.getState();
        const validProfile = createValidProfile();
        const result = store.validateProfile(validProfile);

        expect(result.isValid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it('should reject profile with missing username', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ username: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Username is required');
      });

      it('should reject username shorter than 2 characters', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ username: 'a' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Username must be at least 2 characters');
      });

      it('should reject username longer than 50 characters', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ 
          username: 'a'.repeat(51) 
        });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Username must be less than 50 characters');
      });

      it('should reject profile with missing date of birth', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ dateOfBirth: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Date of birth is required');
      });

      it('should reject date of birth in the future', () => {
        const store = useProfileStore.getState();
        const futureDate = new Date();
        futureDate.setFullYear(futureDate.getFullYear() + 1);
        const invalidProfile = createValidProfile({ 
          dateOfBirth: futureDate.toISOString().split('T')[0] 
        });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Date of birth cannot be in the future');
      });

      it('should reject age less than 13', () => {
        const store = useProfileStore.getState();
        const today = new Date();
        const birthDate = new Date(today.getFullYear() - 10, today.getMonth(), today.getDate());
        const invalidProfile = createValidProfile({ 
          dateOfBirth: birthDate.toISOString().split('T')[0] 
        });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('You must be at least 13 years old');
      });

      it('should reject age greater than 120', () => {
        const store = useProfileStore.getState();
        const today = new Date();
        const birthDate = new Date(today.getFullYear() - 125, today.getMonth(), today.getDate());
        const invalidProfile = createValidProfile({ 
          dateOfBirth: birthDate.toISOString().split('T')[0] 
        });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Invalid date of birth');
      });

      it('should reject profile with missing country', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ country: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Country is required');
      });

      it('should reject country shorter than 2 characters', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ country: 'A' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Country name must be at least 2 characters');
      });

      it('should reject profile with missing education', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ education: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Education is required');
      });

      it('should reject profile with missing mother tongue', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ motherTongue: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Mother tongue is required');
      });

      it('should reject profile with missing gender', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ gender: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Gender is required');
      });

      it('should reject invalid gender value', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ gender: 'Invalid' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Invalid gender selection');
      });

      it('should accept valid gender values', () => {
        const store = useProfileStore.getState();
        
        ['Male', 'Female', 'Others'].forEach(gender => {
          const profile = createValidProfile({ gender });
          const result = store.validateProfile(profile);
          expect(result.isValid).toBe(true);
        });
      });

      it('should reject profile with missing learning pace', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ learningPace: '' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Learning pace is required');
      });

      it('should reject invalid learning pace value', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ learningPace: 'Invalid' });
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('Invalid learning pace selection');
      });

      it('should accept valid learning pace values', () => {
        const store = useProfileStore.getState();
        
        ['Low', 'Medium', 'High'].forEach(pace => {
          const profile = createValidProfile({ learningPace: pace });
          const result = store.validateProfile(profile);
          expect(result.isValid).toBe(true);
        });
      });

      it('should collect all validation errors at once', () => {
        const store = useProfileStore.getState();
        const invalidProfile: ProfileData = {
          username: '',
          dateOfBirth: '',
          country: '',
          education: '',
          motherTongue: '',
          gender: '',
          learningPace: '',
        };
        const result = store.validateProfile(invalidProfile);

        expect(result.isValid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(5);
      });
    });

    describe('hasAllRequiredFields', () => {
      it('should return true when all required fields are filled', () => {
        const store = useProfileStore.getState();
        const validProfile = createValidProfile();
        const result = store.hasAllRequiredFields(validProfile);

        expect(result).toBe(true);
      });

      it('should return false when username is missing', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ username: '' });
        const result = store.hasAllRequiredFields(invalidProfile);

        expect(result).toBe(false);
      });

      it('should return false when date of birth is missing', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ dateOfBirth: '' });
        const result = store.hasAllRequiredFields(invalidProfile);

        expect(result).toBe(false);
      });

      it('should return false when any required field is missing', () => {
        const store = useProfileStore.getState();
        const fields: (keyof ProfileData)[] = [
          'country', 'education', 'motherTongue', 'gender', 'learningPace'
        ];

        fields.forEach(field => {
          const invalidProfile = createValidProfile({ [field]: '' });
          const result = store.hasAllRequiredFields(invalidProfile);
          expect(result).toBe(false);
        });
      });

      it('should handle whitespace-only fields as empty', () => {
        const store = useProfileStore.getState();
        const invalidProfile = createValidProfile({ username: '   ' });
        const result = store.hasAllRequiredFields(invalidProfile);

        expect(result).toBe(false);
      });
    });
  });

  describe('State Management Functions', () => {
    describe('setProfile', () => {
      it('should set profile in store', () => {
        const store = useProfileStore.getState();
        const profile = createValidProfile();
        
        store.setProfile(profile);
        
        expect(useProfileStore.getState().profile).toEqual(profile);
      });
    });

    describe('setError', () => {
      it('should set error message', () => {
        const store = useProfileStore.getState();
        const errorMessage = 'Test error';
        
        store.setError(errorMessage);
        
        expect(useProfileStore.getState().error).toBe(errorMessage);
      });

      it('should clear error when set to null', () => {
        const store = useProfileStore.getState();
        store.setError('Some error');
        store.setError(null);
        
        expect(useProfileStore.getState().error).toBeNull();
      });
    });

    describe('setLoading', () => {
      it('should set loading state', () => {
        const store = useProfileStore.getState();
        
        store.setLoading(true);
        expect(useProfileStore.getState().isLoading).toBe(true);
        
        store.setLoading(false);
        expect(useProfileStore.getState().isLoading).toBe(false);
      });
    });

    describe('setSaving', () => {
      it('should set saving state', () => {
        const store = useProfileStore.getState();
        
        store.setSaving(true);
        expect(useProfileStore.getState().isSaving).toBe(true);
        
        store.setSaving(false);
        expect(useProfileStore.getState().isSaving).toBe(false);
      });
    });

    describe('clearError', () => {
      it('should clear error state', () => {
        const store = useProfileStore.getState();
        store.setError('Some error');
        store.clearError();
        
        expect(useProfileStore.getState().error).toBeNull();
      });
    });

    describe('clearProfile', () => {
      it('should clear all profile data and reset state', () => {
        const store = useProfileStore.getState();
        const profile = createValidProfile();
        
        store.setProfile(profile);
        store.setError('Some error');
        store.setLoading(true);
        store.setSaving(true);
        
        store.clearProfile();
        
        const state = useProfileStore.getState();
        expect(state.profile).toBeNull();
        expect(state.error).toBeNull();
        expect(state.isLoading).toBe(false);
        expect(state.isSaving).toBe(false);
      });
    });
  });

  describe('Save Profile Action', () => {
    it('should save valid profile successfully', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const mockResponse = { success: true, data: profile };

      vi.mocked(profileAPI.saveProfile).mockResolvedValue(mockResponse);

      const result = await store.saveProfileData(profile);

      expect(result.success).toBe(true);
      expect(useProfileStore.getState().profile).toEqual(profile);
      expect(useProfileStore.getState().isSaving).toBe(false);
      expect(useProfileStore.getState().error).toBeNull();
      expect(profileAPI.saveProfile).toHaveBeenCalledWith(profile);
    });

    it('should reject invalid profile without calling API', async () => {
      const store = useProfileStore.getState();
      const invalidProfile = createValidProfile({ username: '' });

      const result = await store.saveProfileData(invalidProfile);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Username is required');
      expect(useProfileStore.getState().profile).toBeNull();
      expect(useProfileStore.getState().isSaving).toBe(false);
      expect(profileAPI.saveProfile).not.toHaveBeenCalled();
    });

    it('should handle API error gracefully', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const mockError = { success: false, error: 'Server error' };

      vi.mocked(profileAPI.saveProfile).mockResolvedValue(mockError);

      const result = await store.saveProfileData(profile);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Server error');
      expect(useProfileStore.getState().profile).toBeNull();
      expect(useProfileStore.getState().isSaving).toBe(false);
      expect(useProfileStore.getState().error).toBe('Server error');
    });

    it('should handle network exceptions', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const networkError = new Error('Network request failed');

      vi.mocked(profileAPI.saveProfile).mockRejectedValue(networkError);

      const result = await store.saveProfileData(profile);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network request failed');
      expect(useProfileStore.getState().isSaving).toBe(false);
      expect(useProfileStore.getState().error).toBe('Network request failed');
    });

    it('should set isSaving state during API call', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(profileAPI.saveProfile).mockReturnValue(promise as any);

      const savePromise = store.saveProfileData(profile);

      // Check that isSaving is true during the call
      expect(useProfileStore.getState().isSaving).toBe(true);

      resolvePromise!({ success: true, data: profile });
      await savePromise;

      expect(useProfileStore.getState().isSaving).toBe(false);
    });
  });

  describe('Update Profile Action', () => {
    it('should update valid profile successfully', async () => {
      const store = useProfileStore.getState();
      const existingProfile = createValidProfile();
      const updatedProfile = createValidProfile({ username: 'updateduser' });
      const mockResponse = { success: true, data: updatedProfile };

      // Set existing profile
      store.setProfile(existingProfile);
      vi.mocked(profileAPI.updateProfile).mockResolvedValue(mockResponse);

      const result = await store.updateProfileData(updatedProfile);

      expect(result.success).toBe(true);
      expect(useProfileStore.getState().profile).toEqual(updatedProfile);
      expect(useProfileStore.getState().isSaving).toBe(false);
      expect(useProfileStore.getState().error).toBeNull();
      expect(profileAPI.updateProfile).toHaveBeenCalledWith(updatedProfile);
    });

    it('should reject invalid profile without calling API', async () => {
      const store = useProfileStore.getState();
      const invalidProfile = createValidProfile({ gender: 'Invalid' });

      const result = await store.updateProfileData(invalidProfile);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid gender selection');
      expect(profileAPI.updateProfile).not.toHaveBeenCalled();
    });

    it('should handle API error during update', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const mockError = { success: false, error: 'Update failed' };

      vi.mocked(profileAPI.updateProfile).mockResolvedValue(mockError);

      const result = await store.updateProfileData(profile);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Update failed');
      expect(useProfileStore.getState().isSaving).toBe(false);
    });
  });

  describe('Fetch Profile Action', () => {
    it('should fetch profile successfully', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const mockResponse = { success: true, data: profile };

      vi.mocked(profileAPI.getProfile).mockResolvedValue(mockResponse);

      const result = await store.fetchProfile();

      expect(result.success).toBe(true);
      expect(useProfileStore.getState().profile).toEqual(profile);
      expect(useProfileStore.getState().isLoading).toBe(false);
      expect(useProfileStore.getState().error).toBeNull();
      expect(profileAPI.getProfile).toHaveBeenCalled();
    });

    it('should handle fetch error', async () => {
      const store = useProfileStore.getState();
      const mockError = { success: false, error: 'Not found' };

      vi.mocked(profileAPI.getProfile).mockResolvedValue(mockError);

      const result = await store.fetchProfile();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not found');
      expect(useProfileStore.getState().profile).toBeNull();
      expect(useProfileStore.getState().isLoading).toBe(false);
      expect(useProfileStore.getState().error).toBe('Not found');
    });

    it('should set isLoading state during fetch', async () => {
      const store = useProfileStore.getState();
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(profileAPI.getProfile).mockReturnValue(promise as any);

      const fetchPromise = store.fetchProfile();

      expect(useProfileStore.getState().isLoading).toBe(true);

      resolvePromise!({ success: true, data: createValidProfile() });
      await fetchPromise;

      expect(useProfileStore.getState().isLoading).toBe(false);
    });
  });

  describe('Integration Tests', () => {
    it('should complete full save workflow', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const mockResponse = { success: true, data: profile };

      vi.mocked(profileAPI.saveProfile).mockResolvedValue(mockResponse);

      // 1. Validate profile
      const validation = store.validateProfile(profile);
      expect(validation.isValid).toBe(true);

      // 2. Check required fields
      const hasFields = store.hasAllRequiredFields(profile);
      expect(hasFields).toBe(true);

      // 3. Save profile
      const result = await store.saveProfileData(profile);
      expect(result.success).toBe(true);

      // 4. Verify state
      expect(useProfileStore.getState().profile).toEqual(profile);
      expect(useProfileStore.getState().isSaving).toBe(false);
      expect(useProfileStore.getState().error).toBeNull();
    });

    it('should complete full update workflow', async () => {
      const store = useProfileStore.getState();
      const originalProfile = createValidProfile();
      const updatedProfile = createValidProfile({ 
        username: 'newusername',
        country: 'Canada'
      });
      const mockSaveResponse = { success: true, data: originalProfile };
      const mockUpdateResponse = { success: true, data: updatedProfile };

      // 1. Save initial profile
      vi.mocked(profileAPI.saveProfile).mockResolvedValue(mockSaveResponse);
      await store.saveProfileData(originalProfile);
      expect(useProfileStore.getState().profile).toEqual(originalProfile);

      // 2. Update profile
      vi.mocked(profileAPI.updateProfile).mockResolvedValue(mockUpdateResponse);
      const result = await store.updateProfileData(updatedProfile);
      expect(result.success).toBe(true);

      // 3. Verify updated state
      expect(useProfileStore.getState().profile).toEqual(updatedProfile);
      expect(useProfileStore.getState().profile?.username).toBe('newusername');
      expect(useProfileStore.getState().profile?.country).toBe('Canada');
    });

    it('should handle validation failure in save workflow', async () => {
      const store = useProfileStore.getState();
      const invalidProfile = createValidProfile({ username: '' });

      // Should fail validation before API call
      const result = await store.saveProfileData(invalidProfile);

      expect(result.success).toBe(false);
      expect(profileAPI.saveProfile).not.toHaveBeenCalled();
      expect(useProfileStore.getState().error).toContain('Username is required');
    });

    it('should handle fetch then update workflow', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const updatedProfile = createValidProfile({ education: 'Master\'s Degree' });
      
      const mockFetchResponse = { success: true, data: profile };
      const mockUpdateResponse = { success: true, data: updatedProfile };

      // 1. Fetch profile
      vi.mocked(profileAPI.getProfile).mockResolvedValue(mockFetchResponse);
      await store.fetchProfile();
      expect(useProfileStore.getState().profile).toEqual(profile);

      // 2. Update fetched profile
      vi.mocked(profileAPI.updateProfile).mockResolvedValue(mockUpdateResponse);
      const result = await store.updateProfileData(updatedProfile);
      
      expect(result.success).toBe(true);
      expect(useProfileStore.getState().profile?.education).toBe('Master\'s Degree');
    });

    it('should handle clear profile after save', async () => {
      const store = useProfileStore.getState();
      const profile = createValidProfile();
      const mockResponse = { success: true, data: profile };

      vi.mocked(profileAPI.saveProfile).mockResolvedValue(mockResponse);

      // Save profile
      await store.saveProfileData(profile);
      expect(useProfileStore.getState().profile).toEqual(profile);

      // Clear profile
      store.clearProfile();
      expect(useProfileStore.getState().profile).toBeNull();
      expect(useProfileStore.getState().error).toBeNull();
      expect(useProfileStore.getState().isLoading).toBe(false);
      expect(useProfileStore.getState().isSaving).toBe(false);
    });
  });
});

