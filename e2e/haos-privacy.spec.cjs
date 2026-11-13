/** Regression tests: a failed HA OS navigation must not expose session tokens. */
const { test, expect } = require('@playwright/test');
const { navigatePrivate, redactIngressText, assertStorageState, parseIngressUrl } =
  require('./haos-private.cjs');

test('manual Ingress navigation failure sanitizes opaque tokens', async ({ page }) => {
  const token = 'FAKE_SECRET_TOKEN_ONLY_FOR_TEST';
  const url = 'http://127.0.0.1:9/api/hassio_ingress/' + token + '/';
  let failure;
  try { await navigatePrivate(page, url); }
  catch (err) { failure = err; }
  expect(failure).toBeTruthy();
  expect(failure.message).not.toContain(token);
  expect(failure.message).not.toContain(url);
  expect(failure.cause).toBeUndefined();
  expect(redactIngressText('navigation ' + url)).toContain('<REDACTED>');
});

test('missing storage state fails with a sanitized actionable message', () => {
  const privatePath = 'unlikely-private-session-state-does-not-exist.json';
  expect(() => assertStorageState(privatePath)).toThrow(/HAOS_STORAGE_STATE is missing/);
  try { assertStorageState(privatePath); }
  catch (err) { expect(err.message).not.toContain(privatePath); }
  expect(parseIngressUrl('not-a-valid-URL')).toBeNull();
});
