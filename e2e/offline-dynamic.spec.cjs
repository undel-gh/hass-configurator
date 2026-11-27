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
    editor.setValue('example: [unfinished' + String.fromCharCode(10), -1);
  });
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().some(a => a.type === 'error')),
    { timeout: 12000, message: 'Ace YAML worker should report invalid YAML' }).toBe(true);
  await page.evaluate(() => editor.setValue('example: [valid]' + String.fromCharCode(10), -1));
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().filter(a => a.type === 'error').length),
    { timeout: 12000 }).toBe(0);
  expect(workers.length).toBeGreaterThan(0);
  expect(outbound).toEqual([]);
  expect(errors).toEqual([]);
});

test('simulated Ingress preserves lazy Ace mode/theme/keybinding and YAML worker paths', async ({ page }) => {
  const requested = [];
  const received = [];
  const publicAttempts = [];
  const pageErrors = [];
  const workers = [];
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.origin === origin) requested.push(url.pathname);
  });
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.origin === origin) {
      received.push({ path: url.pathname, status: response.status() });
    }
  });
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('worker', worker => workers.push(worker.url()));

  // Intercept requests before Chromium can use the network. The route
  // below emulates Supervisor stripping the public Ingress path segment.
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.protocol !== 'blob:' && url.protocol !== 'data:' && url.origin !== origin) {
      publicAttempts.push(url.href);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  await page.route('**/ingress/test/**', async route => {
    const target = new URL(route.request().url());
    if (!target.pathname.startsWith('/ingress/test/')) {
      throw new Error('Unexpected Ingress route: ' + target.pathname);
    }
    target.pathname = target.pathname.replace(/^\/ingress\/test\//, '/');
    const upstream = await route.fetch({ url: target.toString() });
    await route.fulfill({ response: upstream });
  });

  await page.goto(server + '/ingress/test/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() =>
    Boolean(window.ace && window.editor && window.editor.session))).toBe(true);
  const prefix = /^\/ingress\/test\/assets\/v[a-f0-9]{16}\/vendor\/ace\//;

  // This is specifically a regression guard for lazy script resolution.
  // Checking only the HTML's initial <script> URLs would miss this failure.
  const configuredPaths = await page.evaluate(() =>
    ['basePath', 'modePath', 'themePath', 'workerPath'].map(key =>
      ace.config.get(key)));
  for (const configured of configuredPaths) {
    expect(new URL(configured).origin).toBe(origin);
    expect(new URL(configured).pathname).toMatch(prefix);
  }
  await page.evaluate(() => {
    editor.setTheme('ace/theme/monokai');
    editor.getSession().setMode('ace/mode/python');
    editor.setKeyboardHandler('ace/keyboard/vim');
  });

  const assertPrefixedLoad = async filename => {
    const end = '/vendor/ace/' + filename;
    await expect.poll(() => received.some(item => prefix.test(item.path) &&
      item.path.endsWith(end) && item.status === 200),
      { message: 'Ace lazy file must succeed via Ingress: ' + filename }).toBe(true);
    expect(requested.some(path => prefix.test(path) && path.endsWith(end))).toBe(true);
  };
  for (const file of ['mode-python.js', 'theme-monokai.js', 'keybinding-vim.js']) {
    await assertPrefixedLoad(file);
  }

  await page.evaluate(() => {
    const session = editor.getSession();
    session.setMode('ace/mode/yaml');
    session.setUseWorker(true);
    editor.setValue('broken: [list' + String.fromCharCode(10), -1);
  });
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().some(a => a.type === 'error')),
    { timeout: 12000, message: 'YAML worker must validate through Ingress' }).toBe(true);
  await page.evaluate(() =>
    editor.setValue('valid: [list]' + String.fromCharCode(10), -1));
  await expect.poll(() => page.evaluate(() =>
    editor.getSession().getAnnotations().filter(a => a.type === 'error').length),
    { timeout: 12000 }).toBe(0);

  for (const file of ['mode-yaml.js', 'worker-yaml.js']) {
    await assertPrefixedLoad(file);
  }
  expect(workers.length).toBeGreaterThan(0);
  expect(requested.filter(path => path.startsWith('/assets/'))).toEqual([]);
  expect(publicAttempts).toEqual([]);
  expect(pageErrors).toEqual([]);
});

for (const variant of ['direct', 'ingress']) {
test('Ace worker profile blocks excluded modes and preserves preference via ' + variant, async ({ page }) => {
  test.setTimeout(60000);
  const forbidden = [];
  const external = [];
  const errors = [];
  const workers = [];
  const excluded = ['xml', 'php', 'lua', 'coffee', 'xquery'];
  page.on('pageerror', error => errors.push(error.message));
  page.on('worker', worker => workers.push(worker));
  page.on('request', req => {
    if (excluded.some(name => new URL(req.url()).pathname.endsWith('/worker-' + name + '.js')))
      forbidden.push(req.url());
  });
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin && url.protocol !== 'blob:' && url.protocol !== 'data:') {
      external.push(url.href);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  if (variant === 'ingress') {
    await page.route('**/ingress/test/**', async route => {
      const target = new URL(route.request().url());
      target.pathname = target.pathname.replace(/^\/ingress\/test\//, '/');
      await route.fulfill({ response: await route.fetch({ url: target.toString() }) });
    });
  }
  await page.addInitScript(() => {
    window.hcWorkerCspViolations = [];
    document.addEventListener('securitypolicyviolation', e => {
      if (e.disposition === 'enforce') window.hcWorkerCspViolations.push(e.violatedDirective);
    });
  });
  await page.goto(server + (variant === 'ingress' ? '/ingress/test/' : '/'), { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  expect(await page.evaluate(() => editor.session.getUseWorker())).toBe(false);
  const mode = async name => {
    await page.evaluate(name => new Promise(resolve => editor.session.setMode('ace/mode/' + name, resolve)), name);
    await expect.poll(() => page.evaluate(() => editor.session.getMode().$id)).toBe('ace/mode/' + name);
  };
  await mode('yaml');
  const beforeYaml = workers.length;
  await page.evaluate(() => {
    editor.session.setUseWorker(true);
    editor.setValue('broken: [list\n', -1);
  });
  await expect.poll(() => page.evaluate(() => editor.session.getAnnotations().some(a => a.type === 'error')),
    { timeout: 12000 }).toBe(true);
  await expect.poll(() => workers.length).toBeGreaterThan(beforeYaml);
  for (const name of [...excluded, 'svg', 'scss', 'jsoniq', 'text']) {
    await mode(name);
    expect(await page.evaluate(() => ({
      preference: editor.session.getUseWorker(),
      active: Boolean(editor.session.$worker),
      annotations: editor.session.getAnnotations().length,
      supported: hcAceSupportsWorker(editor.session.getMode().$id)
    }))).toEqual({ preference: true, active: false, annotations: 0, supported: false });
    await page.evaluate(() => {
      editor.setValue('editable content', -1);
      editor.session.setUseWorker(false);
      editor.session.setUseWorker(true);
    });
    expect(await page.evaluate(() => editor.getValue())).toBe('editable content');
    expect(await page.evaluate(() => Boolean(editor.session.$worker))).toBe(false);
  }
  await mode('yaml');
  await page.evaluate(() => editor.setValue('again: [invalid\n', -1));
  await expect.poll(() => page.evaluate(() => editor.session.getAnnotations().some(a => a.type === 'error')),
    { timeout: 12000 }).toBe(true);
  await page.evaluate(() => editor.setValue('again: [valid]\n', -1));
  await expect.poll(() => page.evaluate(() => editor.session.getAnnotations().filter(a => a.type === 'error').length),
    { timeout: 12000 }).toBe(0);
  // Every allowed language must actually create its own worker.
  for (const [name, sample] of [
    ['json', '{"valid":true}'], ['javascript', 'var value = 1;'],
    ['css', 'body { color: red; }'], ['html', '<div>valid</div>']
  ]) {
    const before = workers.length;
    await mode(name);
    expect(await page.evaluate(() => Boolean(editor.session.$worker))).toBe(true);
    await page.evaluate(value => editor.setValue(value, -1), sample);
    await expect.poll(() => workers.length, { message: 'New worker for ' + name }).toBeGreaterThan(before);
  }
  // Check the lower-level worker creation guard before it allocates a Worker.
  const rejected = await page.evaluate(() => {
    const Client = ace.require('ace/worker/worker_client').WorkerClient;
    const result = [];
    for (const args of [
      [['ace'], 'ace/mode/xml_worker', 'Worker'],
      [['ace'], 'ace/mode/yaml_worker', 'YamlWorker', 'https://example.invalid/worker-yaml.js'],
      [['ace'], 'ace/mode/yaml_worker', 'WrongClass']
    ]) {
      try { new Client(...args); result.push(false); } catch (error) { result.push(true); }
    }
    return result;
  });
  expect(rejected).toEqual([true, true, true]);
  const beforeDenied = workers.length;
  const denied = await page.evaluate(async names => {
    const { UIWorkerClient } = ace.require('ace/worker/worker_client');
    const result = [];
    function rejects(action) {
      try { action(); return false; } catch (error) {
        return /Unsupported Ace worker/.test(error.message);
      }
    }
    for (const name of names) {
      const modeId = 'ace/mode/' + name;
      const mod = modeId + '_worker';
      const Mode = await new Promise(resolve => ace.config.loadModule(modeId, resolve));
      result.push({ name,
        ui: rejects(() => new UIWorkerClient(['ace'], mod, 'Worker')),
        loader: rejects(() => ace.config.loadModule(['worker', mod], () => {})),
        direct: rejects(() => new Mode.Mode().createWorker(editor.session))
      });
    }
    return result;
  }, excluded);
  expect(denied).toEqual(excluded.map(name => ({ name, ui: true, loader: true, direct: true })));
  expect(workers.length).toBe(beforeDenied);
  expect(workers.length).toBeGreaterThan(0);
  expect(forbidden).toEqual([]);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => hcWorkerCspViolations)).toEqual([]);
  // Deliberate HTTP probes happen only AFTER asserting no automatic requests.
  // The curated server must deny each removed resource even when requested.
  const statuses = await page.evaluate(async names => {
    const base = ace.config.get('workerPath');
    return Promise.all(names.map(async name =>
      (await fetch(new URL('worker-' + name + '.js', base))).status));
  }, excluded);
  expect(statuses).toEqual(excluded.map(() => 404));
});
}

for (const savedMode of ['xml', 'yaml']) {
  test('Ace worker profile restored settings remain default-off: ' + savedMode, async ({ page }) => {
    const workers = [];
    const requests = [];
    const errors = [];
    page.on('worker', worker => workers.push(worker));
    page.on('request', req => {
      if (/\/worker-[^/]+\.js$/.test(new URL(req.url()).pathname)) requests.push(req.url());
    });
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(name => {
      localStorage.setItem('pochass', JSON.stringify({
        mode: 'ace/mode/' + name, useWorker: true
      }));
      // Record calls with the original native constructor, including workers
      // terminated before the editor's final settings become observable.
      window.hcStartupWorkerCalls = [];
      const NativeWorker = window.Worker;
      window.Worker = new Proxy(NativeWorker, {
        construct(target, args, newTarget) {
          window.hcStartupWorkerCalls.push(String(args[0]));
          return Reflect.construct(target, args, newTarget);
        }
      });
    }, savedMode);
    await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => window.editor && editor.session.getMode().$id))
      .toBe('ace/mode/' + savedMode);
    expect(await page.evaluate(() => ({
      preference: editor.session.getUseWorker(),
      active: Boolean(editor.session.$worker),
      startupCalls: hcStartupWorkerCalls
    }))).toEqual({ preference: false, active: false, startupCalls: [] });
    expect(workers).toEqual([]);
    expect(requests).toEqual([]);
    expect(errors).toEqual([]);
  });
}

for (const variant of ['direct', 'ingress']) {
  test('Ace curated theme restores legacy krTheme settings via ' + variant, async ({ page }) => {
    const forbidden = [];
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', req => {
      if (new URL(req.url()).pathname.endsWith('/theme-kr_theme.js')) forbidden.push(req.url());
    });
    if (variant === 'ingress') {
      await page.route('**/ingress/test/**', async route => {
        const target = new URL(route.request().url());
        target.pathname = target.pathname.replace(/^\/ingress\/test\//, '/');
        await route.fulfill({ response: await route.fetch({ url: target.toString() }) });
      });
    }
    await page.addInitScript(savedTheme => {
      localStorage.setItem('pochass', JSON.stringify({
        theme: savedTheme, tabSize: 3, mode: 'ace/mode/yaml', useWorker: false
      }));
    }, variant === 'direct' ? 'ace/theme/kr_theme' : 'kr_theme');
    await page.goto(server + (variant === 'ingress' ? '/ingress/test/' : '/'), { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await expect.poll(() => page.evaluate(() => editor.getSession().getTabSize())).toBe(3);
    await expect(page.locator('#theme option[value="ace/theme/kr_theme"]')).toHaveCount(0);
    expect(await page.evaluate(() => [
      hcAceResolveTheme('ace/theme/kr_theme'), hcAceResolveTheme('kr_theme'),
      hcAceResolveTheme('ace/theme/github')
    ])).toEqual(['ace/theme/monokai', 'ace/theme/monokai', 'ace/theme/github']);
    expect(await page.evaluate(() => editor.getTheme())).not.toContain('kr_theme');
    await page.evaluate(() => editor.setTheme('ace/theme/monokai'));
    await expect.poll(() => page.evaluate(() => editor.getTheme())).toBe('ace/theme/monokai');
    await page.evaluate(() => editor.setTheme('ace/theme/github'));
    await expect.poll(() => page.evaluate(() => editor.getTheme())).toBe('ace/theme/github');
    expect(forbidden).toEqual([]);
    expect(errors).toEqual([]);
    // Explicit HTTP probe only after verifying no automatic request.
    expect(await page.evaluate(async () =>
      (await fetch(new URL('theme-kr_theme.js', ace.config.get('themePath')))).status)).toBe(404);
  });
}


for (const variant of ['direct', 'ingress']) {
  test('Ace curated snippet excludes payloads but preserves modes via ' + variant, async ({ page }) => {
    test.setTimeout(120000);
    const names = ["abc","cedar","cedarschema","csound_document","csound_orchestra","drools","edifact","fsl","gobstones","jsoniq","lsl","maze","razor","velocity","wollok","xquery"];
    const forbidden = [], external = [], errors = [], responses = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', req => {
      const url = new URL(req.url());
      if (names.some(name => url.pathname.endsWith('/vendor/ace/snippets/' + name + '.js')))
        forbidden.push(url.href);
    });
    page.on('response', res => {
      responses.push({path: new URL(res.url()).pathname, status: res.status()});
    });
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== origin && url.protocol !== 'blob:' && url.protocol !== 'data:') {
        external.push(url.href);
        return route.abort('blockedbyclient');
      }
      if (variant === 'ingress' && url.pathname.startsWith('/ingress/test/')) {
        url.pathname = url.pathname.replace(/^\/ingress\/test\//, '/');
        return route.fulfill({response: await route.fetch({url: url.href})});
      }
      return route.continue();
    });
    await page.addInitScript(() => {
      window.hcSnippetCspViolations = [];
      document.addEventListener('securitypolicyviolation', e => {
        if (e.disposition === 'enforce') hcSnippetCspViolations.push(e.violatedDirective);
      });
    });
    await page.goto(server + (variant === 'ingress' ? '/ingress/test/' : '/'), {waitUntil: 'domcontentloaded'});
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await page.evaluate(() => editor.setOptions({enableSnippets: true, enableBasicAutocompletion: true}));
    const samples = [
      ["abc","X:1"],
      ["cedar","permit(principal, action, resource);"],
      ["cedarschema","entity Light;"],
      ["csound_document","<CsoundSynthesizer>"],
      ["csound_orchestra","instr 1"],
      ["drools","rule Light"],
      ["edifact","UNH+1+ORDERS:D:96A:UN'"],
      ["fsl","a -> b;"],
      ["gobstones","program { Skip }"],
      ["jsoniq","1"],
      ["lsl","default { state_entry() {} }"],
      ["maze","move"],
      ["razor","@if (true) {"],
      ["velocity","#set($x = 1)"],
      ["wollok","object light {}"],
      ["xquery","1"]
    ];
    expect(samples.map(([name]) => name)).toEqual(names);
    for (const [name, sample] of [...samples, ...samples]) {
      const actual = await page.evaluate(async ({name, sample}) => {
        await new Promise(resolve => editor.session.setMode('ace/mode/' + name, resolve));
        editor.setValue(sample, -1);
        const mode = editor.session.getMode();
        const tokens = mode.getTokenizer().getLineTokens(sample, 'start').tokens;
        const manager = ace.require('ace/snippets').snippetManager;
        const lang = ace.require('ace/ext/language_tools');
        const callbacks = [];
        const id = 'ace/snippets/' + name;
        ace.config.loadModule(id, m => callbacks.push(m === undefined));
        ace.config.loadModule(['snippets', id], m => callbacks.push(m === undefined));
        ace.config.loadModule(id);
        return {mode: mode.$id, text: tokens.map(t => t.value).join(''),
                value: editor.getValue(), callbacks,
                fileEmpty: Object.keys(manager.files[mode.$id] || {}).length === 0,
                snippets: (manager.snippetMap[name] || []).length,
                enabled: editor.getOption('enableSnippets'),
                basic: editor.getOption('enableBasicAutocompletion'),
                ordinary: editor.completers.includes(lang.textCompleter) &&
                          editor.completers.includes(lang.keyWordCompleter)};
      }, {name, sample});
      expect(actual).toEqual({mode: 'ace/mode/' + name, text: sample, value: sample,
        callbacks: [true, true], fileEmpty: true, snippets: 0, enabled: true, basic: true, ordinary: true});
      // A retained mode may already have been loaded as a bundled dependency.
      // HTTP availability for every retained mode is checked explicitly below.
    }
    // Exercise a retained, nonempty snippet collection after repeated exclusions.
    await page.evaluate(() => new Promise(resolve => editor.session.setMode('ace/mode/java', resolve)));
    await expect.poll(() => page.evaluate(() =>
      (ace.require('ace/snippets').snippetManager.snippetMap.java || []).length)).toBeGreaterThan(0);
    expect(responses.some(r => r.path.endsWith('/vendor/ace/snippets/java.js') && r.status === 200)).toBe(true);
    await page.evaluate(() => new Promise(resolve => editor.session.setMode('ace/mode/sqlserver', resolve)));
    await expect.poll(() => page.evaluate(() =>
      (ace.require('ace/snippets').snippetManager.snippetMap.sqlserver || []).length)).toBeGreaterThan(0);
    expect(responses.some(r => r.path.endsWith('/vendor/ace/snippets/sqlserver.js') && r.status === 200)).toBe(true);
    expect(forbidden).toEqual([]);
    expect(external).toEqual([]);
    expect(errors).toEqual([]);
    expect(await page.evaluate(() => hcSnippetCspViolations)).toEqual([]);
    // Separate deliberate requests from the preceding no-automatic-request test.
    const modeStatuses = await page.evaluate(async names =>
      Promise.all(names.map(async name =>
        (await fetch(new URL('mode-' + name + '.js', ace.config.get('basePath')))).status)), names);
    expect(modeStatuses).toEqual(names.map(() => 200));
    const statuses = await page.evaluate(async names =>
      Promise.all(names.map(async name =>
        (await fetch(new URL('snippets/' + name + '.js', ace.config.get('basePath')))).status)), names);
    expect(statuses).toEqual(names.map(() => 404));
  });
}
