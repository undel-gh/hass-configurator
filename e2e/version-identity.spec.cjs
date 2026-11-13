/** P0 browser release identity: UI and API must represent installed package. */
const { test, expect } = require('@playwright/test');

const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const origin = new URL(server).origin;

test('release identity agrees between HTML About dialog and API without external calls', async ({ page }) => {
  const publicAttempts = [];
  const pageErrors = [];
  page.on('pageerror', err => pageErrors.push(err.message));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!['blob:', 'data:'].includes(url.protocol) && url.origin !== origin) {
      publicAttempts.push(url.origin);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  const html = await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  expect(html.status()).toBe(200);
  expect(html.headers()['cache-control']).toContain('no-store');
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);

  const api = await page.evaluate(async () => {
    const reply = await fetch('api/version', { cache: 'no-store' });
    return { status: reply.status, cache: reply.headers.get('cache-control'),
             version: (await reply.json()).version };
  });
  expect(api.status).toBe(200);
  expect(api.cache).toContain('no-store');
  expect(api.version).toMatch(/^\d+\.\d+\.\d+/);
  await expect(page.locator('#modal_about .modal-content')).toContainText('Version: ' + api.version);
  await expect(page.locator('#modal_about .modal-content a[href*="/releases"]'))
    .toHaveAttribute('href', 'https://github.com/undel-gh/hass-configurator/releases');
  // The fork release link must not erase attribution to the original author.
  await expect(page.locator('#modal_about a[href="https://github.com/danielperna84"]'))
    .toContainText('Daniel Perna');
  expect(pageErrors).toEqual([]);
  expect(publicAttempts).toEqual([]);
});
