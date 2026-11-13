/** GET/POST, upload and download regression using actual HTML via prefix stripping. */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const origin = new URL(server).origin;
const workspace = process.env.E2E_WORKSPACE;
const PREFIX = '/ingress/test/';

test('Ingress prefix survives real file GET, save POST, upload POST and download GET', async ({ page }, info) => {
  test.skip(!workspace, 'Requires disposable E2E_WORKSPACE');
  const folder = path.resolve(workspace);
  const name = 'ingress-operations-' + info.workerIndex + '.yaml';
  const uploadName = 'ingress-multipart-' + info.workerIndex + '.txt';
  const filename = path.join(folder, name);
  const uploadFile = path.join(folder, uploadName);
  fs.mkdirSync(folder, { recursive: true });
  fs.writeFileSync(filename, 'initial: true\n');
  const requests = [];
  const errors = [];
  const publicAttempts = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', req => {
    if (new URL(req.url()).origin === origin) {
      requests.push({
        method: req.method(), path: new URL(req.url()).pathname,
      });
    }
  });
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin && !['data:', 'blob:'].includes(url.protocol)) {
      publicAttempts.push(url.origin);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  await page.route('**/ingress/test/**', async route => {
    const url = new URL(route.request().url());
    url.pathname = url.pathname.replace(/^\/ingress\/test\//, '/');
    const upstream = await route.fetch({ url: url.href });
    await route.fulfill({ response: upstream });
  });
  try {
    await page.goto(server + PREFIX, { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await page.evaluate(f => loadfile(f, f.split('/').pop()), filename);
    await expect(page.locator('#currentfile')).toHaveValue(filename);
    await expect.poll(() => page.evaluate(() => editor.getValue())).toBe('initial: true\n');
    await page.evaluate(() => editor.setValue('prefix: [preserved]\n', -1));
    await page.evaluate(() => save_check());
    await expect.poll(() => fs.readFileSync(filename, 'utf8')).toBe('prefix: [preserved]\n');

    await page.evaluate(dir => listdir(dir), folder);
    await expect(page.locator('#fbheader')).toHaveText(folder);
    await page.evaluate(() => $('#modal_upload').modal('open'));
    await page.locator('#uploadfile').setInputFiles({
      name: uploadName,
      mimeType: 'text/plain',
      buffer: Buffer.from('ingress upload OK\n'),
    });
    await page.evaluate(() => upload());
    await expect.poll(() => fs.existsSync(uploadFile)).toBe(true);

    // Browser resolves the download relative to the actual ingress document.
    const downloaded = await page.evaluate(async file => {
      const r = await fetch('api/download?filename=' + encodeURIComponent(file), {
        cache: 'no-store',
        credentials: 'same-origin',
      });
      return { status: r.status, body: await r.text(),
               disposition: r.headers.get('content-disposition') };
    }, filename);
    expect(downloaded.status).toBe(200);
    expect(downloaded.body).toBe('prefix: [preserved]\n');
    expect(downloaded.disposition).toContain(name);

    for (const [method, suffix] of [
      ['GET', 'api/file'],
      ['GET', 'api/listdir'],
      ['POST', 'api/save'],
      ['POST', 'api/upload'],
      ['GET', 'api/download'],
    ]) {
      expect(requests.some(r => r.method === method &&
        r.path === PREFIX + suffix),
      method + ' ' + suffix + ' must retain the browser prefix').toBe(true);
    }
    expect(requests.filter(r => r.path.startsWith('/api/'))).toEqual([]);
    expect(publicAttempts).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    fs.rmSync(filename, { force: true });
    fs.rmSync(uploadFile, { force: true });
  }
});
