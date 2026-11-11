import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  plugins: [react()],
  build: { chunkSizeWarningLimit: 2000 },
  test: { include: ['src/**/*.test.ts'] },
} as never);
