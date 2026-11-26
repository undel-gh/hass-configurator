/** CSP enforcement and local report-only evidence. No report collector or external service. */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';

test('real HTML resolves with CSP: trusted UI runs, injected scripts and handlers are blocked', async ({ page }) => {
  await page.addInitScript(() => {
    window.__hcPolicyEvents = [];
    document.addEventListener('securitypolicyviolation', e => {
      // Never collect blocked URLs, document URLs, samples or credentials.
      window.__hcPolicyEvents.push({ directive: e.effectiveDirective, disposition: e.disposition });
    });
  });
  const response = await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  expect(response.status()).toBe(200);
  expect(response.headers()['content-security-policy']).toContain("script-src 'self' 'nonce-");
  expect(response.headers()['content-security-policy-report-only']).toContain("style-src 'self';");
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  await page.evaluate(() => {
    const size = document.getElementById('fontSize');
    size.value = '18';
    size.dispatchEvent(new Event('change'));
  });
  await expect.poll(() => page.evaluate(() => parseInt(editor.getOption('fontSize'), 10))).toBe(18);
  // A working editor and real migrated control must not need an enforcement waiver.
  expect(await page.evaluate(() => window.__hcPolicyEvents.filter(e => e.disposition === 'enforce'))).toEqual([]);
  await page.evaluate(() => {
    const script = document.createElement('script');
    script.textContent = 'window.__hcInjectedScript = true';
    document.body.appendChild(script);
    const button = document.createElement('button');
    button.setAttribute('onclick', 'window.__hcInjectedHandler = true');
    document.body.appendChild(button);
    button.click();
    const style = document.createElement('style');
    style.textContent = '#hc-csp-test { color: red; }';
    document.head.appendChild(style);
  });
  await expect.poll(() => page.evaluate(() => window.__hcPolicyEvents.some(e =>
    e.directive === 'script-src-elem' && e.disposition === 'enforce'))).toBe(true);
  await expect.poll(() => page.evaluate(() => window.__hcPolicyEvents.some(e =>
    e.directive === 'script-src-attr' && e.disposition === 'enforce'))).toBe(true);
  await expect.poll(() => page.evaluate(() => window.__hcPolicyEvents.some(e =>
    e.directive === 'style-src-elem' && e.disposition === 'report'))).toBe(true);
  expect(await page.evaluate(() => Boolean(window.__hcInjectedScript || window.__hcInjectedHandler))).toBe(false);
});

test('editable SVG is sandboxed even as a top-level document', async ({ page }, info) => {
  const workspace = process.env.E2E_WORKSPACE;
  test.skip(!workspace || Boolean(process.env.E2E_CONTAINER_PATH),
    'Requires source editor and disposable local workspace');
  const filename = path.join(path.resolve(workspace), 'csp-svg-' + info.workerIndex + '.svg');
  fs.writeFileSync(filename, '<svg xmlns="http://www.w3.org/2000/svg">' +
    '<script>document.documentElement.setAttribute("data-executed","yes");window.hcSvgExecuted=true</script>' +
    '<rect width="10" height="10"/></svg>');
  try {
    const response = await page.goto(server + '/api/file?filename=' + encodeURIComponent(filename));
    expect(response.status()).toBe(200);
    expect(response.headers()['content-security-policy']).toContain('sandbox;');
    expect(response.headers()['content-type']).toContain('image/svg+xml');
    const ran = await page.evaluate(() => Boolean(window.hcSvgExecuted) ||
      document.documentElement.hasAttribute('data-executed'));
    expect(ran).toBe(false);
  } finally {
    fs.rmSync(filename, { force: true });
  }
});

test('same-origin parent can frame the editor under enforced frame-ancestors', async ({ page }) => {
  const parent = server + '/__csp_test_parent';
  await page.route(parent, route => route.fulfill({
    contentType: 'text/html',
    body: '<!doctype html><iframe id="hc-test-frame" src="/"></iframe>',
  }));
  await page.goto(parent);
  await expect(page.frameLocator('#hc-test-frame').locator('#editor')).toBeVisible();
  const frame = page.frames().find(f => f.parentFrame() && new URL(f.url()).origin === new URL(server).origin);
  expect(Boolean(frame)).toBe(true);
  await expect.poll(() => frame.evaluate(() => Boolean(window.editor && window.ace))).toBe(true);
});
