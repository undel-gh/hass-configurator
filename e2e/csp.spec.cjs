/** CSP enforcement and local report-only evidence. No report collector or external service. */
const { test, expect } = require('@playwright/test');
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
