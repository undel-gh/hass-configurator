/** Warm-browser P0 A→B resource upgrade without disabling Chromium's HTTP cache.
 * Separate server processes use byte-identical vendor packages and a changed
 * first-party stylesheet. This exercises real package asset digests/HTML.
 */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const { spawn } = require('node:child_process');

const PACKAGE = path.join(__dirname, '..', 'hass_configurator');

async function freePort() {
  return new Promise((resolve, reject) => {
    const listener = net.createServer();
    listener.once('error', reject);
    listener.listen(0, '127.0.0.1', () => {
      const port = listener.address().port;
      listener.close(() => resolve(port));
    });
  });
}
async function start(root, port) {
  const script = process.env.E2E_PYTHON || 'python';
  const proc = spawn(script, [
    '-m', 'hass_configurator.configurator', '--standalone', '--listen',
    '127.0.0.1', '--port', String(port), '--basepath', root, '--enforce',
  ], {
    cwd: root,
    env: { ...process.env, PYTHONPATH: root },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let stderr = '';
  proc.stderr.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-5000); });
  const origin = 'http://127.0.0.1:' + port;
  for (let i = 0; i < 100; i++) {
    if (proc.exitCode !== null) {
      throw new Error('Test editor process exited: ' + stderr);
    }
    try {
      const response = await fetch(origin + '/api/prefs', { cache: 'no-store' });
      if (response.ok) return { proc, origin };
    } catch { /* still starting */ }
    await new Promise(done => setTimeout(done, 100));
  }
  proc.kill('SIGTERM');
  throw new Error('Test editor did not become ready: ' + stderr);
}
async function stop(proc) {
  if (!proc || proc.exitCode !== null) return;
  const exited = new Promise(resolve => proc.once('exit', resolve));
  proc.kill('SIGTERM');
  await exited;
}

test('warm cache reload chooses new HTML, hashed CSS and Ace worker after A→B', async ({ page }) => {
  test.setTimeout(90000);
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'hc-warm-upgrade-'));
  let app;
  const requests = [];
  page.on('request', request => requests.push(new URL(request.url()).pathname));
  try {
    const dirA = path.join(temp, 'version-a');
    const dirB = path.join(temp, 'version-b');
    fs.mkdirSync(dirA);
    fs.mkdirSync(dirB);
    fs.cpSync(PACKAGE, path.join(dirA, 'hass_configurator'), { recursive: true });
    fs.cpSync(PACKAGE, path.join(dirB, 'hass_configurator'), { recursive: true });
    const styleB = path.join(dirB, 'hass_configurator', 'style.css');
    fs.appendFileSync(styleB, '\n/* e2e-build-b-content-difference */\n');
    const port = await freePort();

    app = await start(dirA, port);
    const firstHtml = await page.goto(app.origin + '/', { waitUntil: 'domcontentloaded' });
    expect(firstHtml.headers()['cache-control']).toContain('no-store');
    await expect.poll(() => page.evaluate(() => Boolean(window.ace && window.editor)))
      .toBe(true);
    const firstCss = await page.locator('link[href$="/style.css"]').getAttribute('href');
    const firstAcePath = await page.evaluate(() => ace.config.get('workerPath'));
    expect(firstCss).toMatch(/^assets\/v[a-f0-9]{16}\/style\.css$/);
    const vA = /assets\/(v[a-f0-9]{16})\//.exec(firstCss)[1];
    const firstAsset = await page.request.get(app.origin + '/' + firstCss);
    expect(firstAsset.status()).toBe(200);
    expect(firstAsset.headers()['cache-control']).toContain('immutable');

    await stop(app.proc);
    app = await start(dirB, port);
    const secondHtml = await page.reload({ waitUntil: 'domcontentloaded' });
    expect(secondHtml.headers()['cache-control']).toContain('no-store');
    await expect.poll(() => page.evaluate(() => Boolean(window.ace && window.editor)))
      .toBe(true);
    const secondCss = await page.locator('link[href$="/style.css"]').getAttribute('href');
    const secondAcePath = await page.evaluate(() => ace.config.get('workerPath'));
    expect(secondCss).toMatch(/^assets\/v[a-f0-9]{16}\/style\.css$/);
    const vB = /assets\/(v[a-f0-9]{16})\//.exec(secondCss)[1];
    expect(vB).not.toBe(vA);
    expect(secondCss).not.toBe(firstCss);
    expect(secondAcePath).not.toBe(firstAcePath);
    expect(secondAcePath).toContain('/' + vB + '/vendor/ace/');

    // The new process MUST NOT serve old-version resources, even if
    // Chromium has a warm local cache from version A.
    const oldFromNewServer = await page.request.get(app.origin + '/' + firstCss);
    expect(oldFromNewServer.status()).toBe(404);
    expect(requests).toContain('/' + secondCss);

    await page.evaluate(() => {
      editor.getSession().setMode('ace/mode/yaml');
      editor.getSession().setUseWorker(true);
      editor.setValue('bad: [item' + String.fromCharCode(10), -1);
    });
    await expect.poll(() => page.evaluate(() =>
      editor.getSession().getAnnotations().some(a => a.type === 'error')),
      { timeout: 12000 }).toBe(true);
    expect(requests.some(p => p.startsWith('/assets/' + vB + '/vendor/ace/worker-yaml.js')))
      .toBe(true);
    expect(requests.some(p => p.startsWith('/assets/' + vA + '/vendor/ace/worker-yaml.js')))
      .toBe(false);
  } finally {
    await stop(app?.proc);
    fs.rmSync(temp, { recursive: true, force: true });
  }
});
