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
const { parseIngressUrl, readPrivateStorageState, assertStorageState, redactIngressText, navigatePrivate, waitPrivatePopup } = require('./haos-private.cjs');

const ingress = process.env.HAOS_INGRESS_URL || '';
const storageState = process.env.HAOS_STORAGE_STATE || '';
const mayMutate = process.env.HAOS_TEST_MUTATIONS === '1';
const fixtureRoot = '/data/hc-ingress-validation';
const enabled = Boolean(ingress && storageState);
const base = parseIngressUrl(ingress);
const prefix = base ? base.pathname.replace(/\/?$/, '/') : '';

// A mistyped private state path must not fail during context initialization,
// before a helpful sanitized error can be emitted by the suite itself.
const parsedState = readPrivateStorageState(storageState);
test.use({ storageState: parsedState || { cookies: [], origins: [] } });
test.beforeEach(() => {
  if (!enabled) return;
  assertStorageState(storageState);
  if (!base || !['http:', 'https:'].includes(base.protocol)) {
    throw new Error('HAOS_INGRESS_URL is invalid (private value omitted).');
  }
});

function guardBrowser(page) {
  const failedPublic = [];
  const jsErrors = [];
  const requestPaths = [];
  const successfulResources = [];
  page.on('pageerror', err => jsErrors.push(redactIngressText(err.message)));
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

async function probeFixture(page, { spoof = false } = {}) {
  // Relative URL stays in the user's real opaque Ingress path. Never print it.
  // Only nonsecret enumerated values are returned to the test runner.
  return page.evaluate(async shouldSpoof => {
    const headers = shouldSpoof ? {
      'X-Ingress-Path': '/malicious-client-value',
      'X-Remote-User-Id': 'forged-browser-identity',
      'X-Forwarded-For': '203.0.113.42',
    } : {};
    const response = await fetch('__haos_probe', {
      credentials: 'same-origin', cache: 'no-store', headers,
    });
    return {
      status: response.status,
      fixture: response.headers.get('x-hc-fixture-id'),
      ingressPath: response.headers.get('x-hc-ingress-path-status'),
      userStatus: response.headers.get('x-hc-user-id-status'),
      cache: response.headers.get('cache-control'),
    };
  }, spoof);
}

function assertTemporaryFixture(status) {
  expect(status.status).toBe(200);
  expect(status.fixture).toBe('hc-ingress-validation-v1');
  expect(status.ingressPath).toBe('valid');
  expect(['present', 'absent']).toContain(status.userStatus);
  expect(status.cache).toContain('no-store');
}

test('real HA OS: actual Supervisor-provided header overrides client spoof', async ({ page }) => {
  test.skip(!enabled, 'Requires local HAOS_INGRESS_URL + HAOS_STORAGE_STATE');
  test.setTimeout(90000);
  const guard = await guardBrowser(page);
  await navigatePrivate(page, ingress);
  const observed = await probeFixture(page);
  assertTemporaryFixture(observed);
  const tampered = await probeFixture(page, { spoof: true });
  // Valid after injecting an intentionally INVALID browser value proves
  // Core/Supervisor overwrote it before nginx saw the request.
  assertTemporaryFixture(tampered);
  guard.assert();
  await test.info().attach('haos-proxy-boundary-redacted.json', {
    body: Buffer.from(JSON.stringify({
      source: 'real-haos-supervisor',
      fixture: observed.fixture,
      ingressHeader: observed.ingressPath,
      clientInjectionRejected: tampered.ingressPath === 'valid',
      remoteUserHeaderStatus: observed.userStatus,
      clientUserIdInjectionRejected: tampered.userStatus !== 'spoofed',
      directNonSupervisorPeer: 'requires separate network-layer check',
    }, null, 2)),
    contentType: 'application/json',
  });
});

test('real HA OS: opt-in local Supervisor REST/observer WebSocket probe', async ({ page }) => {
  test.skip(!enabled || process.env.HAOS_TEST_HA_API !== '1',
    'Requires deliberate --with-ha-api-probe fixture and HAOS_TEST_HA_API=1');
  test.setTimeout(90000);
  const guard = await guardBrowser(page);
  await navigatePrivate(page, ingress);
  assertTemporaryFixture(await probeFixture(page));
  // No token, HA configuration, entity data or WebSocket frames are served:
  // only fixed enum statuses from a read-only probe inside the app container.
  const result = await page.evaluate(async () => {
    const response = await fetch('__haos_api_probe',
      { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) return { status: response.status };
    const body = await response.json();
    return {
      status: response.status, mode: body.mode,
      rest: body.rest, wsAuth: body.ws_auth,
      wsSubscribe: body.ws_subscribe,
    };
  });
  expect(result).toEqual({
    status: 200,
    mode: 'supervisor-readonly',
    rest: 'ok', wsAuth: 'ok', wsSubscribe: 'ok',
  });
  guard.assert();
  await test.info().attach('haos-local-api-redacted.json', {
    body: Buffer.from(JSON.stringify(result, null, 2)),
    contentType: 'application/json',
  });
});

test('real HA OS: observer WebSocket failure does not block local editing', async ({ page }) => {
  test.skip(!enabled, 'Requires local HAOS_INGRESS_URL + HAOS_STORAGE_STATE');
  test.setTimeout(90000);
  await navigatePrivate(page, ingress);
  assertTemporaryFixture(await probeFixture(page));
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  // Failure injection only. This is NOT a new app WS endpoint; it verifies
  // that the existing optional client observer's exception path is isolated
  // from editor operations when an HA observer cannot connect.
  const result = await page.evaluate(() => {
    const original = window.WebSocket;
    try {
      window.WebSocket = class {
        constructor() { throw new Error('test observer disconnected'); }
      };
      ws_connect();
      editor.setValue('local_edit_survives: true\n', -1);
      return editor.getValue();
    } finally {
      window.WebSocket = original;
    }
  });
  expect(result).toBe('local_edit_survives: true\n');
});

test('real HA OS Ingress: full HTML, font, API, route and cache behavior', async ({ page }) => {
  test.skip(!enabled, 'Requires local HAOS_INGRESS_URL + HAOS_STORAGE_STATE');
  test.setTimeout(90000);
  expect(/^\/api\/hassio_ingress\/[^/]+\/$/.test(base.pathname)).toBe(true);
  const guard = await guardBrowser(page);
  await navigatePrivate(page, ingress);
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
  await navigatePrivate(page, ingress);
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  await page.locator('a[data-activates="dropdown_menu"]').first().click();
  const popupPromise = page.waitForEvent('popup');
  await page.locator('#dropdown_menu > li > a').first().click();
  const popup = await popupPromise;
  await waitPrivatePopup(popup);
  expect(new URL(popup.url()).pathname === prefix).toBe(true);
  await popup.close();
  guard.assert();
});

test('real HA OS Ingress: upload and download in isolated fixture ONLY', async ({ page }) => {
  test.skip(!enabled || !mayMutate, 'Requires HAOS_TEST_MUTATIONS=1 on disposable fixture');
  test.setTimeout(90000);
  const guard = await guardBrowser(page);
  await navigatePrivate(page, ingress);
  // A mutation is never allowed against a regular File Editor or unknown
  // application even if HAOS_TEST_MUTATIONS was set accidentally.
  assertTemporaryFixture(await probeFixture(page));
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
