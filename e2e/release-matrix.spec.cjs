/** P0 user-action browser regression matrix. Only disposable test files are mutated. */
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const server = process.env.EDITOR_URL || 'http://127.0.0.1:3218';
const origin = new URL(server).origin;
const workspace = process.env.E2E_WORKSPACE;

const ALL_MODALS = [
  'modal_acekeyboard', 'modal_events', 'modal_save', 'modal_upload',
  'modal_init', 'modal_commit', 'modal_push', 'modal_stash', 'modal_close',
  'modal_rename', 'modal_delete', 'modal_gitadd', 'modal_check_config',
  'modal_reload_automations', 'modal_reload_scripts', 'modal_reload_groups',
  'modal_reload_core', 'modal_restart', 'modal_a_net_remove',
  'modal_a_net_add', 'modal_unban', 'modal_ban', 'modal_exec_command',
  'modal_markdirty', 'modal_newfolder', 'modal_newfile', 'modal_newbranch',
  'modal_netstat', 'modal_about', 'modal_lint',
];

async function guardNetwork(page) {
  const external = [];
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!['blob:', 'data:'].includes(url.protocol) && url.origin !== origin) {
      external.push(url.href);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  return () => {
    expect(external, 'No automatic public-origin requests').toEqual([]);
    expect(errors, 'No unhandled browser JS errors').toEqual([]);
  };
}

test('all 30 dialogs can be opened and dismissed without executing privileged actions', async ({ page }) => {
  const assertClean = await guardNetwork(page);
  test.setTimeout(90000);
  await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor && window.jQuery))).toBe(true);
  const actual = await page.locator('.modal[id^="modal_"]').evaluateAll(nodes =>
    nodes.map(node => node.id).sort());
  expect(actual).toEqual([...ALL_MODALS].sort());
  // Never click an OK/Yes button for Git, shell, reload, restart or IP changes.
  // Exercise Materialize's real modal initialization, rendering and teardown.
  for (const id of ALL_MODALS) {
    await page.evaluate(name => window.$('#' + name).modal('open'), id);
    await expect(page.locator('#' + id), 'Opened: ' + id).toBeVisible();
    await expect(page.locator('#' + id + ' .modal-content')).toBeVisible();
    await page.evaluate(name => window.$('#' + name).modal('close'), id);
    await expect(page.locator('#' + id), 'Dismissed: ' + id).toBeHidden();
  }
  assertClean();
});

test('file browser → open → edit → save → reopen and download', async ({ page }, info) => {
  test.skip(!workspace, 'E2E_WORKSPACE required to avoid modifying user files');
  const directory = path.resolve(workspace);
  fs.mkdirSync(directory, { recursive: true });
  const name = 'matrix-roundtrip-' + info.workerIndex + '.yaml';
  const filename = path.join(directory, name);
  fs.writeFileSync(filename, 'before: value\n', 'utf8');
  try {
    const assertClean = await guardNetwork(page);
    await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await page.evaluate(dir => listdir(dir), directory);
    await expect(page.locator('#fbheader')).toHaveText(directory);
    const entry = page.locator('#fbelements li[title="' + name + '"]');
    await expect(entry).toBeVisible();
    await entry.locator('a').first().click();
    await expect(page.locator('#currentfile')).toHaveValue(filename);
    await expect.poll(() => page.evaluate(() => editor.getValue())).toBe('before: value\n');
    await page.evaluate(() => editor.setValue('after: [value]\n', -1));
    await page.evaluate(() => save_check());
    await expect.poll(() => fs.readFileSync(filename, 'utf8')).toBe('after: [value]\n');
    // Reload without clearing the browser cache; saved file should be restored.
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => editor.getValue())).toBe('after: [value]\n');

    // Download API gets the same bytes and a content-disposition header.
    const url = server + '/api/download?filename=' + encodeURIComponent(filename);
    const reply = await page.request.get(url);
    expect(reply.status()).toBe(200);
    expect(reply.headers()['content-disposition']).toContain(name);
    expect(await reply.text()).toBe('after: [value]\n');
    assertClean();
  } finally {
    fs.rmSync(filename, { force: true });
  }
});

test('upload UI creates a file in a disposable workspace', async ({ page }, info) => {
  test.skip(!workspace, 'E2E_WORKSPACE required to avoid modifying user files');
  const directory = path.resolve(workspace);
  const name = 'matrix-upload-' + info.workerIndex + '.txt';
  const filename = path.join(directory, name);
  const content = 'browser multipart upload\n';
  fs.mkdirSync(directory, { recursive: true });
  try {
    const assertClean = await guardNetwork(page);
    await page.goto(server + '/', { waitUntil: 'domcontentloaded' });
    await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
    await page.evaluate(dir => listdir(dir), directory);
    await expect(page.locator('#fbheader')).toHaveText(directory);
    await page.evaluate(() => $('#modal_upload').modal('open'));
    await expect(page.locator('#modal_upload')).toBeVisible();
    await page.locator('#uploadfile').setInputFiles({
      name, mimeType: 'text/plain', buffer: Buffer.from(content),
    });
    await page.evaluate(() => upload());
    await expect.poll(() => fs.existsSync(filename)).toBe(true);
    expect(fs.readFileSync(filename, 'utf8')).toBe(content);
    assertClean();
  } finally {
    fs.rmSync(filename, { force: true });
  }
});

test('new tab retains the application base, including simulated ingress', async ({ page }) => {
  const assertClean = await guardNetwork(page);
  await page.route('**/ingress/test/**', async route => {
    const url = new URL(route.request().url());
    url.pathname = url.pathname.replace(/^\/ingress\/test\//, '/');
    const upstream = await route.fetch({ url: url.toString() });
    await route.fulfill({ response: upstream });
  });
  await page.goto(server + '/ingress/test/', { waitUntil: 'domcontentloaded' });
  await expect.poll(() => page.evaluate(() => Boolean(window.editor))).toBe(true);
  // Click the real settings menu item instead of synthesizing window.open().
  await page.locator('a[data-activates="dropdown_menu"]').first().click();
  await expect(page.locator('#dropdown_menu')).toBeVisible();
  const popupPromise = page.waitForEvent('popup');
  await page.locator('#dropdown_menu > li > a').first().click();
  const popup = await popupPromise;
  await popup.waitForLoadState('domcontentloaded');
  expect(new URL(popup.url()).pathname).toBe('/ingress/test/');
  await popup.close();
  assertClean();
});
