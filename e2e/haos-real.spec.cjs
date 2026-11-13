/** Manual P1 validation against an ACTUAL Home Assistant OS/Supervisor Ingress.
 *
 * Never run with production File Editor or user files. The only permitted
 * mutation target is the generated isolated local app /data fixture.
 *
 * A storage-state file and ingress URL can contain SECRET session tokens:
 * never attach them, echo them in errors, or commit them.
 */
const { test, expect } = require('@playwright/test');
const path = require('node:path');

const ingress = process.env.HAOS_INGRESS_URL || '';
const storageState = process.env.HAOS_STORAGE_STATE || '';
const mayMutate = process.env.HAOS_TEST_MUTATIONS === '1';
const fixtureRoot = '/data/hc-ingress-validation';
const enabled = Boolean(ingress && storageState);
const base = enabled ? new URL(ingress) : null;
const prefix = base ? base.pathname.replace(/\/?$/, '/') : '';

test.use({ storageState: storageState || { cookies: [], origins: [] } });

function redactPath(p) {
  return p.replace(/\/api\/hassio_ingress\/[^/]+/g,
                   '/api/hassio_ingress/<REDACTED>');
}

function guardBrowser(page) {
  const failedPublic = [];
  const jsErrors = [];
  const requestPaths = [];
  const successfulResources = [];
  page.on('pageerror', err => jsErrors.push(redactPath(err.message)));
  page.on('request', req => {
    const url = new URL(req.url());
    if (url.origin === base.origin) requestPaths.push(url.pathname);
  });
  page.on('response', res => {
    const url = new URL(res.url());
    if (url.origin === base.origin && url.pathname.includes('/assets/')) {
      successfulResources.push({
        suffix: url.pathname.slice(url.pathname.indexOf('/assets/')),
        status: res.status(),
        type: (res.headers()['content-type'] || '').split(';')[0],
      });
    }
  });
  return page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!['blob:', 'data:'].includes(url.protocol) && url.origin !== base.origin) {
      // No secrets, query values or full URLs enter saved diagnostic traces.
      failedPublic.push({ origin: url.origin, type: route.request().resourceType() });
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  }).then(() => ({
    requestPaths, successfulResources, failedPublic, jsErrors,
    assert() {
      expect(failedPublic).toEqual([]);
      expect(jsErrors).toEqual([]);
      // Ignore requests to HA's own authentication machinery. App-origin
      // resources must always remain below the opaque Ingress path.
      expect(requestPaths.every(p => !p.includes('/assets/') ||
        p.startsWith(prefix))).toBe(true);
    },
  }));
}

test('real HA OS Ingress: full HTML, font, API, route and cache behavior', async ({ page }) => {
  test.skip(!enabled, 'Requires local HAOS_INGRESS_URL + HAOS_STORAGE_STATE');
  test.setTimeout(90000);
  expect(base.pathname).toMatch(/^\/api\/hassio_ingress\/[^/]+\/$/);
  const guard = await guardBrowser(page);
  await page.goto(ingress, { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor && window.ace)))
    .toBe(true);
  const staticResponses = guard.successfulResources;
  for (const end of [
    '/vendor/ace/ace.js',
    '/vendor/materialize/css/materialize.min.css',
    '/vendor/mdi/css/materialdesignicons.min.css',
    '/style.css',
  ]) {
    await expect.poll(() => staticResponses.some(r =>
      r.suffix.endsWith(end) && r.status === 200),
      { message: 'Missing real Ingress local asset: ' + end }).toBe(true);
  }
  const response = await page.evaluate(() => fetch('api/prefs', {
    cache: 'no-store', credentials: 'same-origin',
  }).then(r => ({ ok: r.ok, cache: r.headers.get('cache-control') })));
  expect(response.ok).toBe(true);
  expect(response.cache).toContain('no-store');
  // Supervisor may rewrite charset. Verify accepted MIME *families* only.
  expect(staticResponses.some(r => r.suffix.endsWith('/style.css') &&
    r.type === 'text/css')).toBe(true);
  const v = await page.evaluate(() => (
    ace.config.get('workerPath')
  ));
  expect(/^\/api\/hassio_ingress\/[^/]+\/assets\/v[a-f0-9]{16}\/vendor\/ace\/$/
    .test(new URL(v).pathname)).toBe(true);

  await page.evaluate(() => {
    editor.setTheme('ace/theme/monokai');
    editor.getSession().setMode('ace/mode/yaml');
    editor.getSession().setUseWorker(true);
    editor.setValue('invalid: [list' + String.fromCharCode(10), -1);
  });
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().some(a => a.type === 'error')),
    { timeout: 12000 }).toBe(true);
  await page.evaluate(() =>
    editor.setValue('valid: [list]' + String.fromCharCode(10), -1));
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().filter(a => a.type === 'error').length),
    { timeout: 12000 }).toBe(0);
  guard.assert();
  await test.info().attach('haos-ingress-redacted.json', {
    body: Buffer.from(JSON.stringify({
      source: 'real-haos-supervisor',
      ingress: 'REDACTED',
      resourceCount: staticResponses.length,
      localAssetSuffixes: staticResponses.map(r => r.suffix),
      successful: true,
      includesMimeFamilyAssertions: true,
    }, null, 2)),
    contentType: 'application/json',
  });
});

test('real HA OS Ingress: Settings > New tab retains opaque base', async ({ page }) => {
  test.skip(!enabled, 'Requires local HAOS_INGRESS_URL + HAOS_STORAGE_STATE');
  test.setTimeout(90000);
  const guard = await guardBrowser(page);
  await page.goto(ingress, { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  await page.locator('a[data-activates="dropdown_menu"]').first().click();
  const popupPromise = page.waitForEvent('popup');
  await page.locator('#dropdown_menu > li > a').first().click();
  const popup = await popupPromise;
  await popup.waitForLoadState('domcontentloaded');
  expect(new URL(popup.url()).pathname === prefix).toBe(true);
  await popup.close();
  guard.assert();
});

test('real HA OS Ingress: upload and download in isolated fixture ONLY', async ({ page }) => {
  test.skip(!enabled || !mayMutate, 'Requires HAOS_TEST_MUTATIONS=1 on disposable fixture');
  test.setTimeout(90000);
  const guard = await guardBrowser(page);
  await page.goto(ingress, { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  const name = 'haos-ingress-upload-check-' + Date.now().toString(36) + '.txt';
  await page.evaluate(root => listdir(root), fixtureRoot);
  await expect(page.locator('#fbheader')).toHaveText(fixtureRoot);
  await page.evaluate(() => window.$('#modal_upload').modal('open'));
  await page.locator('#uploadfile').setInputFiles({
    name, mimeType: 'text/plain', buffer: Buffer.from('real ingress file test\n'),
  });
  const responsePromise = page.waitForResponse(res =>
    res.url().includes('/api/upload') && res.request().method() === 'POST');
  await page.evaluate(() => upload());
  const uploadResponse = await responsePromise;
  expect(uploadResponse.ok()).toBe(true);
  const result = await uploadResponse.json();
  expect(result.error).toBe(false);

  const contents = await page.evaluate(async filename => {
    const response = await fetch('api/download?filename=' +
      encodeURIComponent(filename), { credentials: 'same-origin' });
    return { status: response.status, body: await response.text(),
             disposition: response.headers.get('content-disposition') };
  }, path.posix.join(fixtureRoot, name));
  expect(contents.status).toBe(200);
  expect(contents.body).toBe('real ingress file test\n');
  expect(contents.disposition).toContain(name);
  guard.assert();
});
