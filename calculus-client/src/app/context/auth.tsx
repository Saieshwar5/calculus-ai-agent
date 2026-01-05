"use client";

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createSSRStorage } from '../utils/storage';

import {useProfileStore} from './profileStore';
import {useLearningPreferenceStore} from './learningPreferenceContext';
import { useQueryStore } from './queriesStore';
import { signup as signupApi, signin as signinApi, logout as logoutApi, checkAuthStatus as checkAuthStatusApi } from '../api/authApi';
import { tokenStore } from '../api/tokenStore';

interface User {
  userID: string;
  email: string;
}

interface SignupData {
  email: string;
  password: string;
}

interface ValidateAuthData extends SignupData {
  confirmPassword: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  // Auth operations
  login: (data: SignupData) => Promise<{ success: boolean; error?: string; data?: User }>;
  signup: (data: SignupData) => Promise<{ success: boolean; error?: string; data?: User }>;
  logout: () => Promise<void>;
  
  // State management
  setUser: (user: User) => void;
  clearUser: () => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  clearError: () => void;
  
  // Validation & Status
  validateAuthData: (data: ValidateAuthData) => { isValid: boolean; errors: string[] };
  checkAuthStatus: () => Promise<void>;
  isLoggedIn: () => boolean;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Auth operations
      login: async (data: SignupData) => {
        const { setLoading, setError, setUser } = get();
        
        try {
          setLoading(true);
          setError(null);

          const result = await signinApi(data);

          if (!result.success) {
            setError(result.error || 'Login failed');
            return { success: false, error: result.error };
          }

          const responseData = result.data;
          console.log("Login response data:", responseData);
          
          // Set user
          const user: User = {
            userID: responseData?.data?.uuid || responseData?.data?.userID || '',
            email: responseData?.data?.email || data.email
          };
          
          setUser(user);
          return { success: true, data: user };

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Network error occurred';
          setError(errorMessage);
          return { success: false, error: errorMessage };
        } finally {
          setLoading(false);
        }
      },

      signup: async (data: SignupData) => {
        const { setLoading, setError, setUser } = get();
        
        try {
          setLoading(true);
          setError(null);

          const result = await signupApi(data);

          if (!result.success) {
            setError(result.error || 'Signup failed');
            return { success: false, error: result.error };
          }

          const responseData = result.data;
          console.log("Signup response data:", responseData);

          // Set user
          const user: User = {
            userID: responseData?.data?.uuid || responseData?.data?.userID || '',
            email: responseData?.data?.email || data.email
          };
          
          setUser(user);
          return { success: true, data: user };

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Network error occurred';
          setError(errorMessage);
          return { success: false, error: errorMessage };
        } finally {
          setLoading(false);
        }
      },

      logout: async () => {
        const { setLoading, clearUser } = get();
        
        try {
          setLoading(true);
          
          // Call logout API (handles token clearing)
          await logoutApi();

        } catch (error) {
          console.warn('Logout request failed:', error);
        } finally {
          // Clear all state and storage
          const {clearProfile} = useProfileStore.getState();
          const {resetPreferences} = useLearningPreferenceStore.getState();
          const {clearMessages} = useQueryStore.getState();
          
          clearUser();
          clearProfile();
          resetPreferences();
          clearMessages();
          
          setLoading(false);
        }
      },

      // State management
      setUser: (user: User) => {
        set({ user, isAuthenticated: true, error: null });
      },

      clearUser: () => {
        set({ user: null, isAuthenticated: false });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setLoading: (isLoading: boolean) => {
        set({ isLoading });
      },

      clearError: () => {
        set({ error: null });
      },

      // Validation
      validateAuthData: (data: ValidateAuthData) => {
        const errors: string[] = [];
        
        if (!data.email) {
          errors.push('Email is required');
        } else if (!/\S+@\S+\.\S+/.test(data.email)) {
          errors.push('Email format is invalid');
        }
        
        if (!data.password) {
          errors.push('Password is required');
        } else if (data.password.length < 6) {
          errors.push('Password must be at least 6 characters long');
        }
        
        if (!data.confirmPassword) {
          errors.push('Confirm Password is required');
        } else if (data.password !== data.confirmPassword) {
          errors.push('Passwords do not match');
        }

        console.log("Validation errors:", errors);

        
        return { isValid: errors.length === 0, errors };
      },

      // Auth status
      checkAuthStatus: async () => {
        const token = tokenStore.getToken();
        
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        try {
          const result = await checkAuthStatusApi();

          if (result.success && result.data) {
            const userData = result.data;
            const user: User = {
              userID: userData.data?.uuid || userData.data?.userID || '',
              email: userData.data?.email || ''
            };
            set({ user, isAuthenticated: true });
          } else {
            set({ isAuthenticated: false, user: null });
          }
        } catch (error) {
          set({ isAuthenticated: false, user: null });
        }
      },

      isLoggedIn: () => {
        return get().isAuthenticated && !!get().user;
      },
    }),
    {
      name: 'auth-storage',
      storage: createSSRStorage() as any,
      // Only persist user and isAuthenticated, not loading/error states
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }) as any,
    }
  )
);







