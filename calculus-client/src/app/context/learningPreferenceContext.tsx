"use client";

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createSSRStorage } from '../utils/storage';
import { ButtonStates } from '../types/learningPreference';
import { handleLearningFormSubmission } from '../api/learningForm';






interface LearningPreferenceState {
  preferences: ButtonStates;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  lastSaved: string | null;
}

interface LearningPreferenceActions {
  // Basic CRUD operations
  setPreferences: (preferences: ButtonStates) => void;
  updatePreference: (key: keyof ButtonStates, value: boolean | string) => void;
  resetPreferences: () => void;
  
  // Loading and error states
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  setSaving: (isSaving: boolean) => void;
  // Async operations
  savePreferences: () => Promise<{ success: boolean; error?: string }>;
  loadPreferences: (id?: string) => Promise<{ success: boolean; error?: string }>;
  
  // Utility functions
  getPreferences: () => ButtonStates;
  hasChanges: () => boolean;
}

const defaultPreferences: ButtonStates = {
  webSearch: false,
  youtubeSearch: false,
  diagramsAndFlowcharts: false,
  imagesAndIllustrations: false,
  chartsAndGraphs: false,
  mindMaps: false,
  stepByStepExplanation: false,
  workedExamples: false,
  practiceProblems: false,
  learnThroughStories: false,
  explainWithRealWorldExamples: false,
  analogiesAndComparisons: false,
  funAndCuriousFacts: false,
  handlingDifficulty: 'explainCompletlyDifferentApproachThenTheCurrentApproach',
};

const initialState: LearningPreferenceState = {
  preferences: defaultPreferences,
  isLoading: false,
  isSaving: false,
  error: null,
  lastSaved: null,
};

export const useLearningPreferenceStore = create<LearningPreferenceState & LearningPreferenceActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Basic operations
      setPreferences: (preferences: ButtonStates) => {
        set({
          preferences: {
            ...preferences,
          },
          isSaving: false,
          error: null,
          lastSaved: new Date().toISOString(),
        });
      },

      updatePreference: (key: keyof ButtonStates, value: boolean | string) => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            [key]: value,
          },
          isSaving: true,
          error: null,
        }));
      },

      resetPreferences: () => {
        set({
          preferences: { ...defaultPreferences },
          isSaving: false,
          error: null,
        });
      },

      // Loading and error states
      setLoading: (isLoading: boolean) => {
        set({ isLoading });
      },
      setSaving: (isSaving: boolean) => {
        set({ isSaving });
      },

      setError: (error: string | null) => {
        set({ error, isSaving: false });
      },

      clearError: () => {
        set({ error: null, isSaving: false });
      },

      // Async operations
      savePreferences: async () => {
        const { setLoading, setError, setPreferences, preferences, setSaving } = get();
        
        try {
          setLoading(true);
          setSaving(true);
          setError(null);
             console.log( "this is preferences", preferences);
          const response = await handleLearningFormSubmission(preferences);

          if (response.success) {
            const savedPreferences = {
              ...preferences,
              id: response.data?.id || preferences.id,
              updatedAt: new Date().toISOString(),
              createdAt: response.data?.createdAt 
            };
            setPreferences(savedPreferences);
            return { success: true };
          } else {
            const errorMessage = response.error || 'Failed to save preferences';
            setError(errorMessage);
            return { success: false, error: errorMessage };
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'An error occurred while saving';
          setError(errorMessage);
          return { success: false, error: errorMessage };
        } finally {
          setLoading(false);
        }
      },

      loadPreferences: async (id?: string) => {
        const { setLoading, setError, setPreferences, preferences } = get();
        
        const preferenceId = id || preferences.id;
        if (!preferenceId) {
          return { success: false, error: 'No preference ID provided' };
        }

        try {
          setLoading(true);
          setError(null);

          // You'll need to implement this API call
          // const response = await fetchLearningPreferences(preferenceId);
          // For now, simulate success
          const response = { success: true, data: preferences };

          if (response.success && response.data) {
            setPreferences(response.data);
            return { success: true };
          } else {
            const errorMessage = 'Failed to load preferences';
            setError(errorMessage);
            return { success: false, error: errorMessage };
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'An error occurred while loading';
          setError(errorMessage);
          return { success: false, error: errorMessage };
        } finally {
          setLoading(false);
        }
      },

      // Utility functions
      getPreferences: () => {
        return get().preferences;
      },

      hasChanges: () => {
        const { preferences } = get();
        // Compare current preferences with default ones
        return JSON.stringify(preferences) !== JSON.stringify(defaultPreferences);
      },
    }),
    {
      name: 'learning-preferences-storage',
      storage: createSSRStorage() as any,
      // Only persist preferences and lastSaved, not loading/error states
      partialize: (state) => ({
        preferences: state.preferences,
        lastSaved: state.lastSaved,
      }) as any,
    }
  )
);

export default useLearningPreferenceStore;