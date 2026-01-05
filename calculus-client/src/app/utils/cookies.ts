/**
 * SSR-safe cookie utilities
 * Works on both client and server side
 */

import Cookies from 'js-cookie';

const TOKEN_COOKIE_NAME = 'auth_token';
const TOKEN_EXPIRATION_COOKIE_NAME = 'auth_token_expiration';

// Cookie options for security
const cookieOptions = {
  expires: 7, // 7 days
  secure: process.env.NODE_ENV === 'production', // HTTPS only in production
  sameSite: 'strict' as const, // CSRF protection
  path: '/',
};

/**
 * Set authentication token in cookie
 */
export function setTokenCookie(token: string, expiresIn?: number): void {
  if (typeof window === 'undefined') {
    // Server-side: can't set cookies directly in API routes
    // This will be handled by the API response headers
    return;
  }
  
  Cookies.set(TOKEN_COOKIE_NAME, token, cookieOptions);
  
  if (expiresIn) {
    const expirationTime = new Date().getTime() + (expiresIn * 1000);
    Cookies.set(TOKEN_EXPIRATION_COOKIE_NAME, expirationTime.toString(), cookieOptions);
  }
}

/**
 * Get authentication token from cookie
 */
export function getTokenCookie(): string | null {
  if (typeof window === 'undefined') {
    // Server-side: return null (cookies should be read from request headers)
    return null;
  }
  
  return Cookies.get(TOKEN_COOKIE_NAME) || null;
}

/**
 * Get token expiration from cookie
 */
export function getTokenExpirationCookie(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  
  return Cookies.get(TOKEN_EXPIRATION_COOKIE_NAME) || null;
}

/**
 * Remove authentication token from cookie
 */
export function removeTokenCookie(): void {
  if (typeof window === 'undefined') {
    return;
  }
  
  Cookies.remove(TOKEN_COOKIE_NAME, { path: '/' });
  Cookies.remove(TOKEN_EXPIRATION_COOKIE_NAME, { path: '/' });
}

/**
 * Check if token is expired
 */
export function isTokenExpired(): boolean {
  const expiration = getTokenExpirationCookie();
  if (!expiration) {
    return true;
  }
  
  const expirationTime = parseInt(expiration, 10);
  return Date.now() >= expirationTime;
}

