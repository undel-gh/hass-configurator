# Offline Ace / UI resource vendor contract

**Status:** PR #16 implements P0 Issues #3 and #4. Source checkout + wheel/sdist are verified by CI on their tested commit; this document is not a claim of real HA OS Ingress or the P1 security release gate.

## Source of truth

| Component | Version and authoritative artifact | Runtime files |
| --- | --- | --- |
| Ace | `ace-builds@1.9.6` official npm release, `src-min-noconflict` family, immutable npm SHA-512 SRI and SHA-256 recorded in `docs/ace-builds-1.9.6-lock.json` | 440 files including core, extensions, 134 offered language modes, 35 offered themes, Vim/Emacs keybindings, snippets, 11 workers |
| Materialize CSS | `materialize-css@0.100.2` npm package with pinned archive SHA-512 SRI / SHA-256 | `vendor/materialize/css/materialize.min.css` and ten CSS-relative Roboto font files |
| Material Design Icons | `@mdi/font@3.4.93` npm package with pinned archive SHA-512 SRI / SHA-256 | `vendor/mdi/css/materialdesignicons.min.css` and five CSS-relative icon font files |

Machine-readable provenance and **per-file** checksums: `hass_configurator/vendor/manifest.json`. All three upstream license texts are stored under `hass_configurator/vendor/licenses/`. There is **no runtime npm, CDN or registry dependency**.

The temporary GitHub Actions workflow that fetched and committed the binary snapshot was removed after the snapshot was generated. To rebuild from pinned upstream releases, run:

```sh
npm pack ace-builds@1.9.6 --pack-destination /tmp
npm pack materialize-css@0.100.2 --pack-destination /tmp
npm pack @mdi/font@3.4.93 --pack-destination /tmp
python scripts/vendor_offline_assets.py --ace /tmp/ace-builds-1.9.6.tgz \
    --materialize /tmp/materialize-css-0.100.2.tgz \
    --mdi /tmp/mdi-font-3.4.93.tgz
```

Review new npm SRI with the lock manifest before updating a published bundle. Archive files are independently hash-verified, and `scripts/vendor_offline_assets.py` rejects unknown Ace contents and CSS references to external URLs.

## Runtime URL and cache policy

- The HTML loads Ace, Materialize CSS and MDI as `assets/v<digest>/vendor/...`, **relative to the document**. The digest includes the bytes and resource paths of every packaged local and vendor asset.
- Ace explicitly uses the same document-derived `basePath`, `modePath`, `themePath` and `workerPath`. This supports prefix-stripping HA-style reverse proxies without trusting client-supplied `X-Ingress-Path`.
- CSS uses its original font-relative paths, which work behind the same prefixed URL.
- The router allows exactly the resource names declared in the manifest. The startup snapshot verifies their hashes; an absent/corrupted vendor file is a **startup error**, not a remote fallback. Versioned static assets are `private, max-age=31536000, immutable` with appropriate MIME; dynamic HTML and API are `no-store`.
- Standalone and simulated Ingress are exercised in browser CI; **real** HA OS Ingress remains P1 #8. Warm-cache upgrade A→B is #5/#6.

## Intentional compatibility and UI changes

- Ace 1.9.6's official npm build does not contain `mode-bro.js`, `mode-dummy.js` or `mode-dummysyntax.js`. These **three broken selectors were removed**. The 134 remaining mode selectors map to actual archive modules.
- Thirteen contributor profile pictures previously loaded automatically from `avatars*.githubusercontent.com`. Names and explicit links to GitHub profiles remain, but images are replaced by a CSS-styled local Material Icons glyph. Optional user-initiated external documentation navigation is still allowed.
- Existing local Material Icons fallback font remains; it is loaded from the versioned first-party asset URL.
- Materialize JS remains the previously bundled local version. CSS version is pinned to the matching 0.100.2 family; no runtime CDN fallback.

## Verification

- `python scripts/audit_runtime_assets.py --strict-offline` confirms **no external automatic resources in the HTML** and checks mode/theme selector drift.
- `python -m unittest discover -s tests -p 'test_*.py' -v` verifies the 460 bundled resources, hashes, original Ace lock, route allowlisting, CSS font closure and MIME.
- `python scripts/check_offline_artifacts.py` validates exact vendored contents in built wheel and sdist.
- `cd e2e && npm ci && npx playwright install chromium && npm test`: cold-cache external-request interception, real HTML through simulated Ingress, modal/UI initialization, Ace dynamic mode/theme/keyboard paths and worker-related behavior, local MDI/Roboto/Material Icons fonts.
- The former expected-failure strict-offline test was made a **required passing test**, not converted to a skip.

## Follow-ups before a stable/public release
- #5: unified package/runtime version source and Docker image based on this fork, warm-cache version upgrade and release artifact provenance.
- #6: comprehensive browser interaction/negative-network matrix including every UI dialog, mode/worker, upload and download.
- #7/#13: API security hardening and CSP.
- #8: physical HA OS add-on Ingress testing, since simulated prefix is insufficient proof.
- #9: complete SBOM and third-party license audit, **including Roboto font licensing** and eventual vulnerability review.
