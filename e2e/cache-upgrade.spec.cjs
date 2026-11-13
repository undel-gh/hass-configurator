/** Browser A→B warm-cache regression in root AND ingress-prefixed scenarios.
 * The ingress proxy is a real local HTTP server; Playwright page.route()
 * disables Chromium HTTP cache and would make this test misleading.
 */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const { spawn } = require('node:child_process');

const PACKAGE = path.join(__dirname, '..', 'hass_configurator');
const PREFIX = '/ingress/test/';

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
  const python = process.env.E2E_PYTHON || 'python';
  const proc = spawn(python, [
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
    if (proc.exitCode !== null) throw new Error('Editor process exited: ' + stderr);
    try {
      const response = await fetch(origin + '/api/prefs', { cache: 'no-store' });
      if (response.ok) return { proc, origin };
    } catch { /* waiting for startup */ }
    await new Promise(done => setTimeout(done, 100));
  }
  proc.kill('SIGTERM');
  throw new Error('Editor did not become ready: ' + stderr);
}

async function stop(proc) {
  if (!proc || proc.exitCode !== null) return;
  const exited = new Promise(resolve => proc.once('exit', resolve));
  proc.kill('SIGTERM');
  await exited;
}

/** Prefix-stripping HTTP proxy retains Chromium's native cache semantics. */
async function startIngressProxy(upstreamPort) {
  const proxy = http.createServer((req, res) => {
    const incoming = new URL(req.url, 'http://127.0.0.1');
    if (!incoming.pathname.startsWith(PREFIX)) {
      res.writeHead(404, { 'Cache-Control': 'no-store' });
      res.end('Unknown simulated Ingress path');
      return;
    }
    const backendPath = '/' + incoming.pathname.slice(PREFIX.length) + incoming.search;
    const upstream = http.request({
      host: '127.0.0.1',
      port: upstreamPort,
      method: req.method,
      path: backendPath,
      headers: {
        ...req.headers,
        host: '127.0.0.1:' + upstreamPort,
      },
    }, response => {
      res.writeHead(response.statusCode, response.headers);
      response.pipe(res);
    });
    upstream.on('error', () => {
      if (!res.headersSent) res.writeHead(502, { 'Cache-Control': 'no-store' });
      res.end('Upstream failed');
    });
    req.pipe(upstream);
  });
  await new Promise((resolve, reject) => {
    proxy.once('error', reject);
    proxy.listen(0, '127.0.0.1', resolve);
  });
  return {
    proxy,
    origin: 'http://127.0.0.1:' + proxy.address().port,
  };
}

async function stopIngressProxy(proxy) {
  if (!proxy) return;
  proxy.closeAllConnections();
  await new Promise(resolve => proxy.close(resolve));
}

for (const variant of ['root', 'ingress-prefixed']) {
  test('warm cache A→B loads new assets and YAML worker via ' + variant, async ({ page }) => {
    test.setTimeout(90000);
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'hc-warm-upgrade-'));
    let app;
    let proxy;
    const requests = [];
    const offOrigin = [];
    const pageErrors = [];
    page.on('request', request => {
      const url = new URL(request.url());
      requests.push(url.pathname);
      if (url.protocol !== 'blob:' && url.protocol !== 'data:' &&
          url.hostname !== '127.0.0.1') offOrigin.push(url.origin);
    });
    page.on('pageerror', error => pageErrors.push(error.message));
    try {
      const dirA = path.join(temp, 'version-a');
      const dirB = path.join(temp, 'version-b');
      fs.mkdirSync(dirA);
      fs.mkdirSync(dirB);
      fs.cpSync(PACKAGE, path.join(dirA, 'hass_configurator'), { recursive: true });
      fs.cpSync(PACKAGE, path.join(dirB, 'hass_configurator'), { recursive: true });
      fs.appendFileSync(path.join(dirB, 'hass_configurator', 'style.css'),
        '\n/* e2e-build-b-content-difference */\n');
      const port = await freePort();
      const prefixed = variant === 'ingress-prefixed';
      app = await start(dirA, port);
      if (prefixed) proxy = await startIngressProxy(port);
      const browserOrigin = proxy ? proxy.origin : app.origin;
      const urlBase = browserOrigin + (prefixed ? PREFIX : '/');
      const requestPrefix = prefixed ? PREFIX : '/';
      const firstHtml = await page.goto(urlBase, { waitUntil: 'domcontentloaded' });
      expect(firstHtml.headers()['cache-control']).toContain('no-store');
      await expect.poll(() => page.evaluate(() => Boolean(window.ace && window.editor)))
        .toBe(true);
      const firstCss = await page.locator('link[href$="/style.css"]').getAttribute('href');
      const firstAcePath = await page.evaluate(() => ace.config.get('workerPath'));
      expect(firstCss).toMatch(/^assets\/v[a-f0-9]{16}\/style\.css$/);
      const vA = /assets\/(v[a-f0-9]{16})\//.exec(firstCss)[1];
      const firstAsset = await page.request.get(urlBase + firstCss);
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
      expect(new URL(secondAcePath).pathname)
        .toBe(requestPrefix + 'assets/' + vB + '/vendor/ace/');
      const oldFromNewServer = await page.request.get(urlBase + firstCss);
      expect(oldFromNewServer.status()).toBe(404);
      expect(requests).toContain(requestPrefix + secondCss);

      await page.evaluate(() => {
        editor.getSession().setMode('ace/mode/yaml');
        editor.getSession().setUseWorker(true);
        editor.setValue('bad: [item' + String.fromCharCode(10), -1);
      });
      await expect.poll(() => page.evaluate(() =>
        editor.getSession().getAnnotations().some(a => a.type === 'error')),
        { timeout: 12000 }).toBe(true);
      const workerPath = requestPrefix + 'assets/' + vB + '/vendor/ace/worker-yaml.js';
      expect(requests).toContain(workerPath);
      expect(requests).not.toContain(requestPrefix +
        'assets/' + vA + '/vendor/ace/worker-yaml.js');
      expect(requests.filter(p => p.includes('/assets/') &&
        !p.startsWith(requestPrefix))).toEqual([]);
      expect(pageErrors).toEqual([]);
      expect(offOrigin).toEqual([]);
    } finally {
      await stop(app?.proc);
      await stopIngressProxy(proxy?.proxy);
      fs.rmSync(temp, { recursive: true, force: true });
    }
  });
}
