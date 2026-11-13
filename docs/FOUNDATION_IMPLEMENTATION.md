# Offline foundation implementation notes (PR #15)

**Status:** implementation in draft PR #15. The application is **not fully offline**. P0 mandatory external-request policy (NFR-001) is not yet satisfied; #3, #4 and #6 remain responsible for removing external loads and lifting the expected-failure test.

## #1 — source inventory and Ace provenance
- Machine inventory: `docs/runtime-dependencies.json`, checked by `python scripts/audit_runtime_assets.py`. Source-level baseline records **five** CDN URL references (Ace core + two extensions, Materialize CSS and MDI CSS), **13** auto-loaded GitHub avatar images, **137** advertised Ace language modes, and **35** themes. External documentation URLs are listed separately.
- Dynamic browser attempts: `e2e/offline-smoke.spec.cjs` intercepts at **request initiation**, aborts public-origin requests and saves `artifacts/runtime-attempts.json` as a CI artifact. The full-UI offline assertion is deliberately `test.fail()` with reference to #3/#4, never reported as satisfying AT-01.
- Ace candidate: official `ace-builds@1.9.6` npm package archive, **`src-min-noconflict`** family. `docs/ace-builds-1.9.6-lock.json` records npm `dist.integrity`, tarball SHA-256, SHA-256 of **440** files and 11 workers, reproducibly checked with `npm pack` and `python scripts/verify_ace_archive.py`.
- Compatibility finding: current UI advertises three modes absent in the pinned npm archive: `bro`, `dummy`, `dummysyntax`. This is **explicit unresolved #3 work**. The archive verification fails on any unexpected missing mode or changed hash, but records these three known obsolete selections until #3 resolves them.
- This is a source inventory plus initial browser trace, **not** proof that every Ace runtime code path has been exercised. Complete dynamic closure tests belong to #3/#6.

## #2 — permanent transport/dispatch boundary
- New `hass_configurator/http_routing.py`: exact GET/POST API allowlist, explicit HTML root route, package-only static registry, normalized path rejection, method-aware 404/405, centralized status/header/body writer **for newly routed paths**.
- `RequestHandler` calls router **before** legacy API branches and never does suffix matching for API paths. Existing API bodies are deliberately not rewritten in P0; this is compatibility staging for #7.
- Static paths: `/assets/v<16-hex-digest>/<allowlisted-filename>`. Digest is derived from SHA-256 of **currently packaged** local files at process startup. Future #3/#4 must extend the asset registry to all vendored resources.
- For fingerprinted assets: `Cache-Control: private, max-age=31536000, immutable` and `X-Content-Type-Options: nosniff`. Transitional `/<old-filename>` aliases revalidate with `no-cache, must-revalidate`. HTML and legacy API responses are `no-store`.
- `hass_configurator/dev.html` now uses relative URLs for existing bundled local assets; old Ace/Materialize/MDI CDN URLs still exist until #3/#4. CSS font URLs remain relative to the stylesheet path.
- The backend currently **ignores** client `X-Ingress-Path`: relative browser URLs need no trusted header for these routes. Ingress is **only simulated** via browser path-prefix stripping in P0. True HA OS Ingress trust semantics remain P1 #8.
- This phase does **not** claim global response centralization: legacy API/page implementations still contain direct `send_response` and `end_headers` calls and have separate P1 hardening work (#7). No CSRF or filesystem confinement claim is made.

## #14 — early CI and traceability
- `.github/workflows/offline-foundation.yml` uses a pinned Ubuntu 24.04 runner; launches Python unittest and early Chromium Playwright smoke, records browser attempts and verifies the official Ace artifact.
- `tests/test_routing.py` covers exact route/method behavior, immutable cache, denied traversal and wrong paths, response headers, optional HA API, and spoofed ingress header.
- `tests/test_traceability.py` ensures every FR/NFR/ADR row has a tracked Issue and planned/verified evidence slot.
- `.github/pull_request_template.md` requires tests and requirement impacts. CI **does not automatically force branch protection**; a repo administrator must configure required checks separately.
- Full UI offline test is **expected to fail** until #3/#4; this is a visible tracked debt, not a waived P0 gate for a stable release.

## Local verification (once dependencies are installed)

```sh
python -m pip install -e .
python scripts/audit_runtime_assets.py
python -m unittest discover -s tests -p 'test_*.py' -v

# Build-time provenance check (Internet allowed during build only)
npm pack ace-builds@1.9.6 --pack-destination /tmp
python scripts/verify_ace_archive.py /tmp/ace-builds-1.9.6.tgz

python -m hass_configurator.configurator --standalone --listen 127.0.0.1 --port 3218
# In another shell:
cd e2e && npm install && npx playwright install chromium && npm test
```

**Never run `python scripts/audit_runtime_assets.py --strict-offline` expecting success yet**: it intentionally fails as long as remote UI dependencies remain. Run the strict mode to measure progress in #3/#4.

## Cross-phase compatibility constraints
- Root/simulated ingress tested in P0, real Home Assistant ingress + proxy trust in P1.
- Per-resource cache digest is start-up stable. Real rolling upgrades/open old pages require #5/#6 warm-cache tests.
- Legacy privileged file, Git and command API security is P1 #7, while CSP is P1 #13.
- Build packaging, single version authority (0.6.0 vs 0.7.0) and full vendored asset closure remain #5.
