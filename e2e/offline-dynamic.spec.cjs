/** Dynamic Ace and local webfont integration under browser network denial. */
const { test, expect } = require('@playwright/test');
const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const origin = new URL(server).origin;

test('Ace modes, themes, shortcuts, completion and workers are same-origin', async ({ page }) => {
  const external = [];
  const loaded = [];
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.origin === origin && url.pathname.includes('/vendor/')) {
      loaded.push({ path: url.pathname, status: response.status() });
    }
  });
  await page.route('**/*', async route => {
    if (new URL(route.request().url()).origin !== origin) {
      external.push(route.request().url());
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });

  await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() =>
    Boolean(window.ace && window.editor && window.editor.session))).toBe(true);

  await page.evaluate(() => {
    const e = window.editor;
    e.setTheme('ace/theme/monokai');
    e.getSession().setMode('ace/mode/python');
    e.setKeyboardHandler('ace/keyboard/vim');
    e.setOptions({ enableBasicAutocompletion: true, enableSnippets: true });
  });
  for (const filename of ['mode-python.js', 'theme-monokai.js', 'keybinding-vim.js']) {
    await expect.poll(() => loaded.some(r => r.path.endsWith('/vendor/ace/' + filename) &&
      r.status === 200), { message: 'Ace dynamic asset ' + filename }).toBe(true);
  }
  await page.evaluate(() => {
    const e = window.editor;
    e.setKeyboardHandler('ace/keyboard/emacs');
    e.setTheme('ace/theme/github');
    e.getSession().setMode('ace/mode/yaml');
    e.getSession().setUseWorker(true);
    e.setValue('example: [valid]\n', -1);
  });
  for (const filename of ['keybinding-emacs.js', 'theme-github.js', 'mode-yaml.js']) {
    await expect.poll(() => loaded.some(r => r.path.endsWith('/vendor/ace/' + filename) &&
      r.status === 200), { message: 'Ace dynamic asset ' + filename }).toBe(true);
  }
  // Worker must actually be configured to use the fingerprinted app origin.
  const cfg = await page.evaluate(() => ({
    base: ace.config.get('basePath'),
    mode: ace.config.get('modePath'),
    theme: ace.config.get('themePath'),
    worker: ace.config.get('workerPath'),
    languageTools: typeof ace.require('ace/ext/language_tools').textCompleter,
  }));
  for (const value of [cfg.base, cfg.mode, cfg.theme, cfg.worker]) {
    expect(new URL(value).origin).toBe(origin);
    expect(new URL(value).pathname).toMatch(/\/assets\/v[a-f0-9]{16}\/vendor\/ace\/$/);
  }
  expect(cfg.languageTools).not.toBe('undefined');
  await page.waitForTimeout(800);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});

test('MDI, Roboto and fallback Material Icons have locally served fonts', async ({ page }) => {
  const requests = [];
  const external = [];
  page.on('response', resp => {
    const url = new URL(resp.url());
    if (url.origin === origin && url.pathname.includes('/assets/')) {
      requests.push({ path: url.pathname, status: resp.status() });
    }
  });
  await page.route('**/*', async route => {
    if (new URL(route.request().url()).origin !== origin) {
      external.push(route.request().url());
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  await page.evaluate(async () => {
    const mdi = document.createElement('i');
    mdi.className = 'mdi mdi-git';
    document.body.appendChild(mdi);
    const local = document.createElement('span');
    local.className = 'material-icons';
    local.textContent = 'home';
    document.body.appendChild(local);
    await Promise.all([
      document.fonts.load('24px "Material Design Icons"'),
      document.fonts.load('16px Roboto'),
      document.fonts.load('24px "Material Icons"', 'home'),
    ]);
  });
  for (const ending of [
    '/mdi/fonts/materialdesignicons-webfont.woff2',
    '/materialize/fonts/roboto/Roboto-Regular.woff2',
    '/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2',
  ]) {
    await expect.poll(() => requests.some(r =>
      r.path.endsWith(ending) && r.status === 200),
      { message: 'Missing local webfont: ' + ending }).toBe(true);
  }
  expect(external).toEqual([]);
});
test('YAML syntax worker reports and clears errors with public network blocked', async ({ page }) => {
  const outbound = [];
  const workers = [];
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  page.on('worker', worker => workers.push(worker.url()));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) {
      outbound.push(url.href);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  await page.evaluate(() => {
    const session = editor.getSession();
    session.setMode('ace/mode/yaml');
    session.setUseWorker(true);
    editor.setValue('example: [unfinished\\n', -1);
  });
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().some(a => a.type === 'error')),
    { timeout: 12000, message: 'Ace YAML worker should report invalid YAML' }).toBe(true);
  await page.evaluate(() => editor.setValue('example: [valid]\\n', -1));
  await page.waitForTimeout(1400);
  console.log('YAML_WORKER_DIAGNOSTICS', JSON.stringify(await page.evaluate(() => ({
    annotations: editor.getSession().getAnnotations(),
    value: editor.getValue(),
    mode: editor.getSession().getMode().$id,
    workerEnabled: editor.getSession().getUseWorker(),
  }))));
  console.log('YAML_WORKER_URLS', JSON.stringify(workers));
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().filter(a => a.type === 'error').length),
    { timeout: 12000 }).toBe(0);
  expect(workers.length).toBeGreaterThan(0);
  expect(outbound).toEqual([]);
  expect(errors).toEqual([]);
});

