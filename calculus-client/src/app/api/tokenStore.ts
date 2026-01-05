/**
 * Token store using cookies for SSR-safe persistence
 * Works on both client and server side
 */

import { 
  setTokenCookie, 
  getTokenCookie, 
  removeTokenCookie, 
  getTokenExpirationCookie,
  isTokenExpired 
} from '../utils/cookies';

export const tokenStore = {
  getToken: (): string | null => {
    // Check if token is expired
    if (isTokenExpired()) {
      removeTokenCookie();
      return null;
    }
    return getTokenCookie();
  },

  setToken: (token: string, expiresIn?: number): void => {
    setTokenCookie(token, expiresIn);
  },

  getTokenExpiration: (): string | null => {
    return getTokenExpirationCookie();
  },

  setTokenExpiration: (expiration: string): void => {
    // This is handled by setToken with expiresIn parameter
    // But we keep it for backward compatibility
    const expiresIn = parseInt(expiration, 10) - Date.now();
    if (expiresIn > 0) {
      setTokenCookie(getTokenCookie() || '', Math.floor(expiresIn / 1000));
    }
  },

  clearToken: (): void => {
    removeTokenCookie();
  },

  hasToken: (): boolean => {
    return getTokenCookie() !== null && !isTokenExpired();
  },
};
