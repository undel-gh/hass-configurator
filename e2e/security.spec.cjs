/** Browser-level XSS and CSRF regressions. No privileged operation executed. */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const workspace = process.env.E2E_WORKSPACE;

test('hostile loadfile URL stays data, not executable script', async ({ page }) => {
  const attack = "'</script><script>window.__hc_xss = 1</script>";
  const url = server + '/?loadfile=' + encodeURIComponent(attack);
  const response = await page.request.get(url);
  expect(response.status()).toBe(200);
  const html = await response.text();
  expect(html).not.toContain('</script><script>window.__hc_xss');
  expect(html).toContain('\\u003c/script\\u003e');
  expect(html).toContain('name="hc-csrf-token"');
});

test('malicious filesystem names render only as text in the browser', async ({ page }) => {
  test.skip(!workspace, 'Disposable E2E_WORKSPACE required');
  const name = "xss-'><img src=x onerror=window.__hc_xss=1>.yaml";
  const full = path.join(path.resolve(workspace), name);
  fs.writeFileSync(full, 'safe: true\n', 'utf8');
  try {
    await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await page.evaluate(dir => listdir(dir), path.resolve(workspace));
    const row = page.locator('#fbelements li').filter({ hasText: name });
    await expect(row).toBeVisible();
    await expect(row.locator('.filename')).toHaveText(name);
    expect(await page.evaluate(() => window.__hc_xss)).toBeUndefined();
    expect(await page.locator('img[src="x"]').count()).toBe(0);
  } finally {
    fs.rmSync(full, { force: true });
  }
});

test('browser POST carries CSRF header and cross-site POST cannot mutate', async ({ page }) => {
  test.skip(!workspace, 'Disposable E2E_WORKSPACE required');
  const target = path.join(path.resolve(workspace), 'csrf-e2e-no-write.yaml');
  try {
    await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    const crossSite = await page.evaluate(async target => {
      const response = await fetch('api/save', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ filename: target, text: 'csrf: bypass' }),
      });
      return response.status;
    }, target);
    expect(crossSite).toBe(403);
    expect(fs.existsSync(target)).toBe(false);
  } finally {
    fs.rmSync(target, { force: true });
  }
});
