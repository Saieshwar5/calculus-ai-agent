/**
 * Authentication API functions
 * Centralized API calls for authentication operations
 */

import { tokenStore } from './tokenStore';

interface UserCredentials {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token?: string;
  expires_in?: number;
  data?: {
    uuid?: string;
    userID?: string;
    email?: string;
  };
  message?: string;
}

interface ApiResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

const BASE_URL = 'http://127.0.0.1:8000';

/**
 * Sign up a new user
 */
export async function signup({ email, password }: UserCredentials): Promise<ApiResult<AuthResponse>> {
  try {
    const response = await fetch(`${BASE_URL}/api/auth/join`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Signup failed' }));
      const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
      return { success: false, error: errorMessage };
    }

    const data: AuthResponse = await response.json();
    
    // Store token if provided
    if (data.access_token) {
      tokenStore.setToken(data.access_token, data.expires_in);
    }

    return { success: true, data };
  } catch (error) {
    console.error('Signup error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
}

/**
 * Sign in an existing user
 */
export async function signin({ email, password }: UserCredentials): Promise<ApiResult<AuthResponse>> {
  try {
    const response = await fetch(`${BASE_URL}/api/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Login failed' }));
      const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
      return { success: false, error: errorMessage };
    }

    const data: AuthResponse = await response.json();
    
    // Store token if provided
    if (data.access_token) {
      tokenStore.setToken(data.access_token, data.expires_in);
    }

    return { success: true, data };
  } catch (error) {
    console.error('Signin error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
}

/**
 * Logout the current user
 */
export async function logout(): Promise<ApiResult> {
  try {
    const token = tokenStore.getToken();
    
    if (token) {
      await fetch(`${BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
      });
    }
    
    // Clear tokens regardless of API call success
    tokenStore.clearToken();
    
    return { success: true };
  } catch (error) {
    console.warn('Logout request failed:', error);
    // Still clear tokens even if API call fails
    tokenStore.clearToken();
    return { success: true }; // Consider logout successful even if API fails
  }
}

/**
 * Check authentication status by verifying token with server
 */
export async function checkAuthStatus(): Promise<ApiResult<AuthResponse>> {
  const token = tokenStore.getToken();
  
  if (!token) {
    return { success: false, error: 'No token found' };
  }

  try {
    const response = await fetch(`${BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      // Token is invalid, clear it
      tokenStore.clearToken();
      return { success: false, error: 'Invalid token' };
    }

    const data: AuthResponse = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('Auth status check error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to check auth status',
    };
  }
}
