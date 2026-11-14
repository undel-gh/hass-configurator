const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.cjs',
  // Real HA OS testing requires an authenticated local session and must never
  // run by accident in public CI or against someone else's File Editor.
  testIgnore: process.env.npm_lifecycle_event === 'test:haos' ? [] : ['**/haos-real.spec.cjs'],
  timeout: 30000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    browserName: 'chromium', headless: true,
    // Optional CI-only credentials for the authenticated fork container.
    // Never connect an arbitrary external editor; real HA OS is a separate gate.
    ...(process.env.E2E_BASIC_USER ? {
      httpCredentials: {
        username: process.env.E2E_BASIC_USER,
        password: process.env.E2E_BASIC_PASSWORD || '',
        send: 'always',
      },
    } : {}),
  },
});
