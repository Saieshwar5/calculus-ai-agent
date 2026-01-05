import { defineConfig } from 'vitest/config';
import path from 'path';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()] as any,
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  css: {
    postcss: {
      // Use a minimal PostCSS config for tests
      plugins: [],
    },
  },
});

