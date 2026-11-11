import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 180_000,
  expect: { timeout: 30_000 },
  workers: 2,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:4317/',
    viewport: { width: 1280, height: 860 },
    launchOptions: { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] },
  },
  webServer: {
    command: 'npx vite preview --port 4317 --strictPort --host 127.0.0.1',
    url: 'http://127.0.0.1:4317/',
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
