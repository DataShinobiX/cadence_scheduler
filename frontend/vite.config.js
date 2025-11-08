import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist'
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    watch: {
      usePolling: true,
    },
    port: 5173,
    open: true,
    fs: {
      allow: ['.'],
    },
  },
  // Optional fallback:
  appType: 'spa', // tells Vite this is a single-page app
});