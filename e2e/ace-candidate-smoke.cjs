// Isolated candidate smoke. Not the production Configurator or real Supervisor.
const { chromium } = require('playwright');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

async function main() {
  const [candidate, output] = process.argv.slice(2);
  const root = path.resolve(candidate);
  const base = '/api/hassio_ingress/disposable/assets/v0123456789abcdef/';
  const policy = "default-src 'none'; script-src 'self'; script-src-attr 'none'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: blob:; worker-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'; frame-src 'none'";
  const init = "ace.require('ace/ext/language_tools'); window.editor=ace.edit('editor'); editor.setOptions({enableBasicAutocompletion:true,enableLiveAutocompletion:false,useWorker:true});";
  const bootstrap = fs.readFileSync(path.join(__dirname, '../hass_configurator/ace-bootstrap.js'));
  const editorHTML = '<!doctype html><html><head><meta charset="utf-8"><title>Candidate</title></head><body><div id="editor" style="height:400px;width:700px"></div><script src="' + base + 'vendor/ace/ace.js"></script><script src="' + base + 'ace-bootstrap.js"></script><script src="' + base + 'candidate-init.js"></script></body></html>';
  const requests = [], served = [], external = [], errors = [], violations = [], checks = {};
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    res.setHeader('Content-Security-Policy', policy);
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (url.pathname === '/api/hassio_ingress/disposable/') {
      res.setHeader('Content-Type', 'text/html; charset=utf-8'); return res.end(editorHTML);
    }
    if (url.pathname === base + 'ace-bootstrap.js' || url.pathname === base + 'candidate-init.js') {
      res.setHeader('Content-Type', 'application/javascript'); return res.end(url.pathname.endsWith('candidate-init.js') ? init : bootstrap);
    }
    if (url.pathname.startsWith(base + 'vendor/ace/')) {
      const rel = url.pathname.slice((base + 'vendor/ace/').length);
      if (!rel.split('/').every(p => /^[A-Za-z0-9_.-]+$/.test(p) && p !== '.' && p !== '..')) {
        res.statusCode = 400; return res.end();
      }
      const file = path.join(root, rel);
      if (fs.existsSync(file) && fs.statSync(file).isFile()) {
        served.push(rel);
        res.setHeader('Content-Type', rel.endsWith('.css') ? 'text/css' : 'application/javascript');
        return res.end(fs.readFileSync(file));
      }
    }
    res.statusCode = 404; res.end();
  });
  let browser;
  try {
    await new Promise((resolve, reject) => {server.once('error', reject);server.listen(0,'127.0.0.1',resolve);});
    const origin = 'http://127.0.0.1:' + server.address().port;
    browser = await chromium.launch();
    const ctx = await browser.newContext({serviceWorkers:'block'});
    await ctx.route('**/*', route => {
      const url = route.request().url();
      if (url.startsWith(origin + '/') || url.startsWith('blob:') || url.startsWith('data:')) return route.continue();
      external.push(url); return route.abort();
    });
    const page = await ctx.newPage();
    page.on('request', request => requests.push(request.url()));
    page.on('pageerror', error => errors.push(String(error)));
    page.on('response', response => {if(response.status() >= 400) errors.push('HTTP '+response.status()+' '+response.url());});
    await page.addInitScript(() => {
      window.__violations = [];
      document.addEventListener('securitypolicyviolation', e => window.__violations.push({directive:e.effectiveDirective, disposition:e.disposition}));
    });
    await page.goto(origin + '/api/hassio_ingress/disposable/');
    await page.waitForFunction(() => !!window.editor);
    checks.bootstrap = await page.evaluate(() => ['basePath','modePath','themePath','workerPath'].every(k => ace.config.get(k).endsWith('/vendor/ace/')));
    assert.ok(checks.bootstrap);
    async function diagnostics(mode, invalid, valid) {
      await page.evaluate(({mode,invalid}) => {editor.session.clearAnnotations();editor.session.setMode('ace/mode/'+mode);editor.session.setValue(invalid);}, {mode,invalid});
      await page.waitForFunction(() => editor.session.getAnnotations().some(a=>a.type==='error'), null, {timeout:12000});
      const bad = await page.evaluate(()=>editor.session.getAnnotations());
      await page.evaluate(valid => editor.session.setValue(valid),valid);
      await page.waitForFunction(()=>!editor.session.getAnnotations().some(a=>a.type==='error'),null,{timeout:12000});
      return {invalid:bad,valid:await page.evaluate(()=>editor.session.getAnnotations())};
    }
    checks.javascript = await diagnostics('javascript','const broken = ;','const x = 1;\nconsole.log(x);');
    checks.yaml = await diagnostics('yaml','bad: [one, two','good: [one, two]');
    await page.evaluate(()=>editor.session.setValue('automation: !include automation.yaml\npassword: !secret api_password'));
    await page.waitForTimeout(1200);
    checks.ha_tags = await page.evaluate(()=>editor.session.getAnnotations());
    for (const theme of ['monokai','github']) {
      await page.evaluate(theme=>editor.setTheme('ace/theme/'+theme),theme);
      await page.waitForFunction(theme=>editor.getTheme()==='ace/theme/'+theme,theme);
    }
    for (const binding of ['vim','emacs']) {
      await page.evaluate(binding=>editor.setKeyboardHandler('ace/keyboard/'+binding),binding);
      await page.waitForFunction(binding=>editor.getKeyboardHandler()?.$id==='ace/keyboard/'+binding,binding,{timeout:8000});
    }
    await page.evaluate(()=>{editor.setKeyboardHandler(null);editor.session.setUseWorker(false);});
    checks.worker_disabled = await page.evaluate(()=>editor.session.getUseWorker()===false);
    checks.requested_workers = served.filter(u=>/^worker-(javascript|yaml)\.js$/.test(u));
    checks.loaded_themes = served.filter(u=>/^theme-(monokai|github)\.js$/.test(u));
    checks.loaded_keybindings = served.filter(u=>/^keybinding-(vim|emacs)\.js$/.test(u));
    violations.push(...await page.evaluate(()=>window.__violations));
    assert.ok(checks.worker_disabled);
    assert.ok(checks.requested_workers.some(u=>u==='worker-javascript.js'));
    assert.ok(checks.requested_workers.some(u=>u==='worker-yaml.js'));
    assert.ok(checks.loaded_themes.includes('theme-monokai.js') && checks.loaded_themes.includes('theme-github.js'));
    assert.ok(checks.loaded_keybindings.includes('keybinding-vim.js') && checks.loaded_keybindings.includes('keybinding-emacs.js'));
    assert.deepEqual(external,[]);
    assert.deepEqual(errors,[]);
    assert.deepEqual(violations.filter(v=>v.disposition==='enforce'),[]);
    checks.status='passed';
  } catch (e) {
    checks.status='candidate-failed';
    checks.error=String(e);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
    fs.writeFileSync(output,JSON.stringify({candidate_only:true,checks,requests,served,external,errors,violations},null,2)+'\n');
    console.log('Candidate diagnostic status:', checks.status);
    // Candidate incompatibility is evidence, not a waiver or a shipped-runtime CI failure.
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
