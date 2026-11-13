/** End-to-end failure handling for configured but unavailable local HA API/WS. */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const net = require('node:net');
const { spawn } = require('node:child_process');

function port() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const n = server.address().port;
      server.close(() => resolve(n));
    });
  });
}
async function ready(url, proc) {
  for (let i = 0; i < 100; i++) {
    if (proc.exitCode !== null) throw new Error('Local HA outage test app exited');
    try {
      const response = await fetch(url + '/api/prefs');
      if (response.ok) return;
    } catch { /* not started yet */ }
    await new Promise(done => setTimeout(done, 100));
  }
  throw new Error('Local HA outage editor did not become ready');
}
async function stop(proc) {
  if (proc && proc.exitCode === null) {
    const done = new Promise(resolve => proc.once('exit', resolve));
    proc.kill('SIGTERM');
    await done;
  }
}
test('HA REST and observer WS unavailable: editor still opens, edits and saves', async ({ page }) => {
  test.setTimeout(70000);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'hc-ha-outage-'));
  const filename = path.join(dir, 'ha-failure-edit.yaml');
  const settings = path.join(dir, 'settings.json');
  fs.writeFileSync(filename, 'initial: 1\n');
  const listen = await port();
  const unreachable = await port();
  const target = 'http://127.0.0.1:' + listen;
  const socket = 'ws://127.0.0.1:' + unreachable + '/api/websocket';
  fs.writeFileSync(settings, JSON.stringify({
    HASS_API: 'http://127.0.0.1:' + unreachable + '/api/',
    HASS_WS_API: socket,
  }));
  const proc = spawn(process.env.E2E_PYTHON || 'python', [
    '-m', 'hass_configurator.configurator', settings,
    '--basepath', dir, '--enforce',
    '--listen', '127.0.0.1', '--port', String(listen),
  ], { stdio: 'ignore' });
  const external = [];
  const scriptErrors = [];
  page.on('pageerror', err => scriptErrors.push(err.message));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== target && !['data:', 'blob:'].includes(url.protocol)) {
      external.push(url.origin);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  try {
    await ready(target, proc);
    const documentResponse = await page.goto(target + '/', { waitUntil: 'domcontentloaded' });
    expect(documentResponse.status()).toBe(200);
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await expect(page.locator('#ws_uri')).toHaveValue(socket);
    // A refused WS handshake may never produce a Playwright "websocket"
    // event, so assert attempted construction directly while preserving the
    // browser's real native WebSocket connection/close behavior.
    await page.evaluate(() => {
      const NativeSocket = window.WebSocket;
      window.WebSocket = class extends NativeSocket {
        constructor(url, protocols) {
          window.__e2eAttemptedSocket = String(url);
          if (protocols === undefined) super(url);
          else super(url, protocols);
        }
      };
    });
    await page.evaluate(() => ws_connect());
    await expect.poll(() => page.evaluate(() => window.__e2eAttemptedSocket))
      .toBe(socket);
    await expect.poll(() => page.locator('#ws_events').inputValue(),
      { timeout: 12000 }).toContain('Socket closed');
    await page.evaluate(name => loadfile(name, 'ha-failure-edit.yaml'), filename);
    await expect(page.locator('#currentfile')).toHaveValue(filename);
    await expect.poll(() => page.evaluate(() => editor.getValue())).toBe('initial: 1\n');
    await page.evaluate(() => editor.setValue('survives: true\n', -1));
    await page.evaluate(() => save_check());
    await expect.poll(() => fs.readFileSync(filename, 'utf8')).toBe('survives: true\n');
    expect(external).toEqual([]);
    expect(scriptErrors).toEqual([]);
  } finally {
    await stop(proc);
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
