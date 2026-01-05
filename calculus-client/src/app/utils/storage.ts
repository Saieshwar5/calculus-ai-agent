/**
 * SSR-safe storage adapter for Zustand persist middleware
 * Uses localStorage on client, in-memory on server
 */

import { StateStorage } from 'zustand/middleware';

export const createSSRStorage = (): StateStorage => {
  return {
    getItem: (name: string): string | null => {
      if (typeof window === 'undefined') {
        return null;
      }
      try {
        return localStorage.getItem(name);
      } catch (error) {
        console.warn('localStorage.getItem failed:', error);
        return null;
      }
    },
    setItem: (name: string, value: string): void => {
      if (typeof window === 'undefined') {
        return;
      }
      try {
        localStorage.setItem(name, value);
      } catch (error) {
        console.warn('localStorage.setItem failed:', error);
      }
    },
    removeItem: (name: string): void => {
      if (typeof window === 'undefined') {
        return;
      }
      try {
        localStorage.removeItem(name);
      } catch (error) {
        console.warn('localStorage.removeItem failed:', error);
      }
    },
  };
};

