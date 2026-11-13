/** Never surface the opaque HA OS Ingress session segment in test failures. */
const fs = require('node:fs');

function parseIngressUrl(value) {
  try { return value ? new URL(value) : null; }
  catch { return null; } // URL parsing diagnostics can echo input secrets.
}

function readPrivateStorageState(path) {
  if (!path) return null;
  try {
    const state = JSON.parse(fs.readFileSync(path, 'utf8'));
    if (!state || !Array.isArray(state.cookies) || !Array.isArray(state.origins)) {
      return null;
    }
    return state;
  } catch {
    // Read errors can contain absolute file paths and must not reach Playwright.
    return null;
  }
}

function assertStorageState(path) {
  if (!readPrivateStorageState(path)) {
    throw new Error('HAOS_STORAGE_STATE is missing, unreadable or invalid (private path omitted).');
  }
}

function redactIngressText(text) {
  return String(text).replace(/\/api\/hassio_ingress\/[^/\s?#]+/g,
    '/api/hassio_ingress/<REDACTED>');
}

async function navigatePrivate(page, url) {
  try {
    return await page.goto(url, { waitUntil: 'domcontentloaded' });
  } catch {
    // NEVER attach the original Playwright error as a cause: it includes
    // the opaque bearer-like URL in both message and navigation call logs.
    throw new Error('HA OS Ingress navigation failed (URL and browser details redacted).');
  }
}

async function waitPrivatePopup(popup) {
  try {
    await popup.waitForLoadState('domcontentloaded');
  } catch {
    throw new Error('HA OS Ingress popup failed to load (URL and browser details redacted).');
  }
}

module.exports = { parseIngressUrl, readPrivateStorageState, assertStorageState, redactIngressText, navigatePrivate, waitPrivatePopup };
