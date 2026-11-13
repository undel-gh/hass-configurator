/** Baseline offline network-attempt gate; full UI is expected to fail until #3/#4. */
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

test('local immutable assets load through simulated ingress prefix', async ({ page, request }) => {
  const html = await (await request.get(server + '/')).text();
  const match = /assets\/v([a-f0-9]{16})\/jquery-3\.6\.0\.min\.js/.exec(html);
  expect(match, 'HTML should refer to fingerprinted local jQuery').not.toBeNull();
  const version = match[1];
  const external = await interceptAttempts(page);

  // Emulate Home Assistant ingress stripping an opaque prefix before forwarding.
  await page.route('**/ingress/test/**', async (route) => {
    const incoming = new URL(route.request().url());
    incoming.pathname = incoming.pathname.replace(/^\/ingress\/test\//, '/');
    const response = await route.fetch({ url: incoming.toString() });
    await route.fulfill({ response });
  });

  await page.goto(server + '/api/prefs');
  await page.setContent('<html><head></head><body><script src="' +
    server + '/ingress/test/assets/v' + version +
    '/jquery-3.6.0.min.js"></script></body></html>');
  await expect.poll(() => page.evaluate(() => typeof window.jQuery)).toBe('function');
  expect(external).toEqual([]);

  const response = await request.get(server + '/assets/v' + version + '/style.css');
  expect(response.status()).toBe(200);
  expect(response.headers()['cache-control']).toContain('immutable');
});

test('full UI sends no public-origin requests (KNOWN OFFLINE DEBT #3/#4)', async ({ page }) => {
  test.fail(true, 'Known CDN and avatar requests remain until Ace/CSS bundling (#3/#4). This test MUST become green and lose fail() before release.');
  const attempts = await interceptAttempts(page);
  await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(700); // give CSS fonts / optional images time to attempt loading
  fs.mkdirSync(path.join(__dirname, 'artifacts'), { recursive: true });
  fs.writeFileSync(path.join(__dirname, 'artifacts', 'runtime-attempts.json'),
                   JSON.stringify(attempts, null, 2) + '\n');
  await test.info().attach('runtime-attempts.json', {
    body: Buffer.from(JSON.stringify(attempts, null, 2)),
    contentType: 'application/json',
  });
  expect(attempts).toEqual([]);
});
