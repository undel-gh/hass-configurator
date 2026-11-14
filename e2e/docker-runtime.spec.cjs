/** P0 browser round trip against the FORK Docker image and its mounted /config.
 * Skipped on source/wheel/sdist because host and container paths differ.
 * The sandbox host mount is removed by the CI runner, never user's /config.
 */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const workspace = process.env.E2E_WORKSPACE;
const containerRoot = process.env.E2E_CONTAINER_PATH;

test('fork-built Docker browser: no external requests and file round trip', async ({ page }, info) => {
  test.skip(!workspace || !containerRoot,
    'Explicit E2E_CONTAINER_PATH + disposable E2E_WORKSPACE required');
  const name = 'docker-p0-' + info.workerIndex + '.yaml';
  const host = path.join(path.resolve(workspace), name);
  const inside = path.posix.join(containerRoot, name);
  const attempts = [];
  const errors = [];
  const appOrigin = new URL(server).origin;
  fs.mkdirSync(workspace, { recursive: true });
  fs.writeFileSync(host, 'fork: true\n', 'utf8');
  // This fixture alone is deliberately writable by the non-root Docker
  // process (UID 10001), while the temporary host sandbox is disposable.
  fs.chmodSync(host, 0o666);
  page.on('pageerror', err => errors.push(err.message));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!['data:', 'blob:'].includes(url.protocol) && url.origin !== appOrigin) {
      attempts.push(url.origin);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  try {
    await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor && window.ace)))
      .toBe(true);
    const reported = await page.evaluate(async () => {
      const response = await fetch('api/version');
      return { status: response.status, cache: response.headers.get('cache-control'),
               data: await response.json() };
    });
    expect(reported.status).toBe(200);
    expect(reported.cache).toContain('no-store');
    expect(reported.data.version).toMatch(/^\d+\.\d+\.\d+/);

    await page.evaluate(filename => loadfile(filename, filename.split('/').pop()), inside);
    await expect(page.locator('#currentfile')).toHaveValue(inside);
    await expect.poll(() => page.evaluate(() => editor.getValue())).toBe('fork: true\n');
    await page.evaluate(() => editor.setValue('fork: offline\n', -1));
    await page.evaluate(() => save_check());
    await expect.poll(() => fs.readFileSync(host, 'utf8')).toBe('fork: offline\n');
    const download = await page.request.get(server + '/api/download?filename=' +
      encodeURIComponent(inside));
    expect(download.status()).toBe(200);
    expect(await download.text()).toBe('fork: offline\n');
    expect(attempts).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    fs.rmSync(host, { force: true });
  }
});
