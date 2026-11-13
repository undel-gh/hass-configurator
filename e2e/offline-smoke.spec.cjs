/** Offline network-attempt gate for bundled Ace and UI assets. */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const appOrigin = new URL(server).origin;

async function interceptAttempts(page) {
  const external = [];
  await page.route('**/*', async (route) => {
    const url = route.request().url();
    if (!url.startsWith('data:') && new URL(url).origin !== appOrigin) {
      external.push({ url, type: route.request().resourceType() });
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  return external;
}

test('network interceptor sees even a blocked external request', async ({ page }) => {
  const attempts = await interceptAttempts(page);
  await page.goto(server + '/api/prefs');
  // Deliberately inject an off-origin request to prove the guard detects attempts.
  await page.evaluate(() => {
    const img = document.createElement('img');
    img.src = 'https://example.invalid/network-denial-fixture.png';
    document.body.appendChild(img);
  });
  await expect.poll(() => attempts.length).toBeGreaterThan(0);
  expect(attempts[0].url).toContain('example.invalid');
});

test('real HTML resolves local assets and API under simulated ingress prefix', async ({ page }) => {
  const external = await interceptAttempts(page);
  const requested = [];
  const assets = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.origin === appOrigin) requested.push(url.pathname);
  });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.origin === appOrigin && url.pathname.includes('/assets/')) {
      assets.push({ path: url.pathname, status: response.status() });
    }
  });

  // Load the actual dev.html at the external URL. Simulate Supervisor
  // stripping the opaque prefix before forwarding to HASS Configurator.
  await page.route('**/ingress/test/**', async (route) => {
    const incoming = new URL(route.request().url());
    if (!incoming.pathname.startsWith('/ingress/test/')) {
      throw new Error('Unexpected ingress request: ' + incoming.pathname);
    }
    incoming.pathname = incoming.pathname.replace(/^\/ingress\/test\//, '/');
    const response = await route.fetch({ url: incoming.toString() });
    await route.fulfill({ response });
  });

  await page.goto(server + '/ingress/test/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => typeof window.jQuery)).toBe('function');
  const refs = await page.evaluate(() => [
    ...document.querySelectorAll('link[href],script[src]'),
  ].map((node) => node.getAttribute('href') || node.getAttribute('src')));
  // This fails if dev.html regresses from assets/... to /assets/...
  for (const filename of ['jquery-3.6.0.min.js', 'style.css',
                          'material-icons.fallback.css', 'materialize.min.js',
                          'js-yaml.min.js']) {
    expect(refs.some((ref) => /^assets\/v[a-f0-9]{16}\//.test(ref) &&
      ref.endsWith('/' + filename)), filename + ' must use a relative URL').toBe(true);
    await expect.poll(() => assets.some((r) =>
      r.path.endsWith('/' + filename) && r.status === 200)).toBe(true);
    expect(requested.some((p) =>
      /^\/ingress\/test\/assets\/v[a-f0-9]{16}\//.test(p) &&
      p.endsWith('/' + filename)), filename + ' must load under the prefix').toBe(true);
  }

  // Exercise an actual font from dev.html's fallback stylesheet.
  await page.evaluate(async () => {
    const icon = document.createElement('span');
    icon.className = 'material-icons';
    icon.textContent = 'home';
    document.body.appendChild(icon);
    await document.fonts.load('24px "Material Icons"', 'home');
  });
  await expect.poll(() => assets.some((r) =>
    r.path.endsWith('/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2') &&
    r.status === 200)).toBe(true);

  // Browser resolves this relative API URL against the real ingress document.
  const prefs = await page.evaluate(async () => {
    const response = await fetch('api/prefs');
    if (!response.ok) throw new Error('API: ' + response.status);
    return response.json();
  });
  expect(prefs).toHaveProperty('ui_theme');
  expect(requested).toContain('/ingress/test/api/prefs');

  expect(requested.filter((p) => p.startsWith('/assets/') ||
    p.startsWith('/api/'))).toEqual([]);
  // The actual prefixed HTML, not synthetic markup, must not attempt
  // public-origin script, CSS, font or image loads. No expected failures.
  expect(external).toEqual([]);
  expect(await page.locator('img[src^="http"]').count()).toBe(0);
  await expect.poll(() => page.evaluate(() => Boolean(window.ace && window.editor))).toBe(true);
  for (const filename of [
    'vendor/ace/ace.js',
    'vendor/ace/ext-modelist.js',
    'vendor/ace/ext-language_tools.js',
    'vendor/materialize/css/materialize.min.css',
    'vendor/mdi/css/materialdesignicons.min.css',
    'vendor/mdi/fonts/materialdesignicons-webfont.woff2',
  ]) {
    await expect.poll(() => assets.some((r) =>
      r.path.endsWith('/' + filename) && r.status === 200),
      { message: 'Missing local dependency: ' + filename }).toBe(true);
  }
});

test('full UI attempts no public-origin requests with cold cache', async ({ page }) => {
  const attempts = await interceptAttempts(page);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() =>
    Boolean(window.ace && window.editor && window.jQuery))).toBe(true);
  await page.waitForTimeout(600);
  fs.mkdirSync(path.join(__dirname, 'artifacts'), { recursive: true });
  fs.writeFileSync(path.join(__dirname, 'artifacts', 'runtime-attempts.json'),
                   JSON.stringify(attempts, null, 2) + '\n');
  // Keep the downloadable CI artifact independently machine-readable.
  const recordedAttempts = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'artifacts', 'runtime-attempts.json'), 'utf8'));
  expect(recordedAttempts).toEqual(attempts);
  await test.info().attach('runtime-attempts.json', {
    body: Buffer.from(JSON.stringify(attempts, null, 2)),
    contentType: 'application/json',
  });
  expect(errors).toEqual([]);
  expect(attempts).toEqual([]);
});
