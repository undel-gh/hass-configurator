# P0 closeout audit — issues #1, #2, #6, #14

**Status (2026-11-14): ready for evidence-based review, not yet accepted or merged.**
This page defines the **automated P0 subset**. A test that uses a local
prefix-stripping proxy, HA REST outage fixture, or ephemeral container is
**not a test against real Home Assistant OS Supervisor Ingress**. Privileged
operation confirmation is deliberately excluded pending #7. Closing P0
must not be interpreted as readiness to expose the editor to the public
Internet or to production HA configurations.

## Evidence baseline and approval rule

- Prior accepted release build: [PR #19](https://github.com/undel-gh/hass-configurator/pull/19)
  and [CI #206](https://github.com/undel-gh/hass-configurator/actions/runs/43502177693)
  on PR source HEAD `b111986521d7c769ea339f2ba5a1aabb21ba4c62`.
  Four jobs passed: 47 Python tests, 18 source Playwright tests, five each
  on installed wheel, installed sdist and actual fork-built Docker image.
  That run is **historical evidence**, not verification of this PR's HEAD.
- This closeout PR adds executable contracts in `tests/test_p0_closeout.py`
  for the inventory, pinned Ace family, method-aware API dispatch,
  single-write HTTP responses, negative CI probes, and P1 exclusions.
- **Current PR HEAD / CI:** pending; record the exact commit and green run
  in the PR body before requesting approval. Do not reuse #206 as proof
  of changes made after #19.
- A maintainer must review the final evidence and decide issue closure
  **after merge**. Neither this document nor a green test automatically
  closes issues or waives their acceptance criteria.

## Issue-by-issue acceptance

| Issue / owner | P0 requirement | Implemented and testable evidence | Boundary and disposition |
| --- | --- | --- | --- |
| [#1](https://github.com/undel-gh/hass-configurator/issues/1) — inventory | Classify cold/dynamic public-origin attempts, initial CDN/avatar footprint, approved HA REST/WS and user-opened documentation; lock provenance of Ace 1.9.6 `src-min-noconflict` | `docs/runtime-dependencies.json`; `docs/ace-builds-1.9.6-lock.json`; `hass_configurator/vendor/manifest.json` provenance and source license paths; `scripts/audit_runtime_assets.py --strict-offline`; `scripts/verify_ace_archive.py`; `tests/test_vendored_assets.py`; `tests/test_p0_closeout.py`; `e2e/offline-smoke.spec.cjs` runtime-attempts JSON | **P0 candidate accepted subject to current PR CI**. Only automatic browser requests in supported scenarios are prohibited; deliberate external links are not preloaded. Full license/SBOM/vulnerability adjudication: #9 |
| [#2](https://github.com/undel-gh/hass-configurator/issues/2) — routing | Permanent exact/method-aware router, package-only versioned static resources, canonical 400/404/405 and headers, root and simulated prefix behavior | `hass_configurator/http_routing.py`; `tests/test_routing.py`; `tests/test_legacy_contract.py`; `tests/test_ingress_redirect.py`; `tests/test_p0_closeout.py`; `e2e/ingress-operations.spec.cjs`; `e2e/cache-upgrade.spec.cjs` | **P0 scoped adapter only**: `Router.match()` is the mandatory exact-path/method gate for all legacy API routes; `send_response()` is the single writer for router-owned static/error responses. Legacy handler implementations continue to emit their own responses under the gate. Moving privileged API operations to controller-owned policy/response objects and end-to-end security belongs to #7; real proxy/header semantics to #8. Do not claim global response-writer centralization |
| [#6](https://github.com/undel-gh/hass-configurator/issues/6) — E2E | Cold and warm browser testing, blocked public requests, supported Ace modes, simulated Ingress API and file operations, outage, package and Docker tests | `e2e/offline-smoke.spec.cjs`; `e2e/offline-dynamic.spec.cjs`; `e2e/release-matrix.spec.cjs`; `e2e/ingress-operations.spec.cjs`; `e2e/ha-outage.spec.cjs`; `e2e/cache-upgrade.spec.cjs`; `e2e/docker-runtime.spec.cjs`; `tests/test_p0_failure_gates.py` | **P0 supported/low-risk flows**. Privileged Git/exec/restart confirmation actions are **NOT VERIFIED**; #7 owns safe authorization/CSRF and confirmation testing. Real HA OS browser integration and upgrade are #8 |
| [#14](https://github.com/undel-gh/hass-configurator/issues/14) — governance | Required CI, negative fixtures, traceability and PR review contract | `.github/workflows/offline-foundation.yml`; `.github/pull_request_template.md`; `tests/test_traceability.py`; `tests/test_p0_closeout.py`; this audit and `docs/TRACEABILITY.md` | **P0 repository-file controls testable**. Branch protection/rulesets are **NOT VERIFIED** from repository files, and cannot be enabled by a CI documentation PR. Maintainer action below must be recorded independently |

### Permanent router versus legacy API — accepted P0/P1 boundary

P0 owns route *admission*, not the complete privileged API rewrite:
`RequestHandler._dispatch_route()` uses `HTTP_ROUTER.match(method, self.path)`
before ordinary GET/POST legacy API dispatch. Unknown/suffixed paths, wrong
methods and malformed asset paths fail before any legacy implementation runs.
Router-owned assets/errors use a structured `Response` and a shared writer;
`end_headers()` adds no-store/nosniff on legacy output. A real socket HTTP
suite checks actual route behavior; the closeout contract checks that
router-owned paths emit one status and header block.

**Exception:** the existing SESAME/TOTP authentication redirect is handled
before the router by design because its access-token path is not a public API
route. This transition is not a new authorization control. Legacy
`configurator.py` handlers still have direct `send_response` /
`end_headers` branches. A rewrite of authenticated/privileged endpoints
must preserve compatibility and be reviewed under **#7 (P1)**, not silently
claimed as complete in #2. Backend direct clients cannot make the HTML
honor a supplied `X-Ingress-Path`: browser URLs are relative; the true
trusted proxy header / slash contract must be tested in **#8**.

## AT-01–AT-10 automated P0 release matrix

| Scenario | Checked P0 behavior | Evidence | Current status |
| --- | --- | --- | --- |
| AT-01 | Cold UI uses local scripts, CSS, icons and fonts; off-origin attempt is a failure | `offline-smoke.spec.cjs`, `offline-dynamic.spec.cjs` | scoped verified in CI #206; recheck this PR |
| AT-02 | Supported YAML lint and file browse/edit/save/reopen/download | `offline-dynamic.spec.cjs`, `release-matrix.spec.cjs` | scoped verified in CI #206; recheck |
| AT-03 | Ace workers, themes, modes, extensions load locally from one release | `test_vendored_assets.py`, `offline-dynamic.spec.cjs` | scoped verified in CI #206; recheck |
| AT-04 | All 30 dialogs open/close; safe UI paths and upload/download | `release-matrix.spec.cjs` | **partial**: privileged confirmations intentionally excluded (#7) |
| AT-05 | Simulated prefix-stripping Ingress: HTML/static/API/file/save/upload/download, new tab, relative redirects | `ingress-operations.spec.cjs`, `offline-smoke.spec.cjs`, `test_ingress_redirect.py` | P0 simulated verified; real #8 **NOT VERIFIED** |
| AT-06 | HA REST and observer WS unavailable; local editing stays functional | `ha-outage.spec.cjs` | scoped verified in CI #206; real HA #8 pending |
| AT-07 | Exact methods, API/static collisions, malformed paths, symlink and MIME/cache protections | `test_routing.py`, `test_legacy_contract.py`, `test_p0_closeout.py` | scoped P0 verified; privileged data confinement #7 pending |
| AT-08 | Source/wheel/sdist/fork Docker metadata, binary resource closure and version identity | `check_offline_artifacts.py`, `check_docker_runtime_lock.py`, `version-identity.spec.cjs` | scoped verified in CI #206; OS architecture limits per #5 |
| AT-09 | Warm A→B in same Chromium context under root and local prefix-stripping proxy | `cache-upgrade.spec.cjs` | P0 simulated verified; real Supervisor upgrade #8 **NOT VERIFIED** |
| AT-10 | Negative fixtures for public fetch, missing bundle and failure-gate validation | `test_p0_failure_gates.py`, `offline-smoke.spec.cjs`, CI | scoped verified in CI #206; required branch checks require maintainer |

“Scoped verified” denotes tested supported scenarios, **not** broad assurance
of untested privileged operations. Historical results are not current-HEAD
approval; the CI run for this PR must also pass.

## Maintainer-controlled required checks (#14)

The workflow contains these **exact current job names**, whose checks should
be required in the default branch protection/ruleset for `master`:

- `P0 immutable Docker base and exact Python wheel closure`
- `Routing / inventory (Python)`
- `Disposable HA OS app container smoke (NOT real Supervisor)`
- `Network-attempt smoke (Chromium)`

Recommended maintainer action in GitHub: **Settings → Rules → Rulesets**
(or **Settings → Branches → Branch protection rules**), target `master`,
require a PR and all four passing checks before merge, and prevent bypasses
according to the repository's governance policy. Confirm that checks are
reported by the expected GitHub Actions workflow, and record the settings
review with a date outside this PR. **The existence of a workflow does not
prove that branch protection is enabled.** Required status checks/settings
cannot be attested by this repository-file-only P0 PR. If governance decides
not to enable them, record that explicitly rather than calling it verified.

## Explicitly not included in P0

- **#7**: privileged route auth, CSRF, confirmation paths, filesystem
  confinement, command/Git execution and migration of legacy controllers.
- **#8**: **real** Home Assistant OS/Supervisor Ingress, request/redirect and
  header rewriting, peer trust, REST/WS connectivity and warm upgrade.
- **#9**: vulnerability decisions, dependency/license compliance and SBOM,
  beyond pinned artifact origin and integrity hashes.
- **#13**: CSP policy, deployment-specific framing, workers and violations.

P1 gates are **NOT VERIFIED**. Do not publicly expose or install this fork
over a live editor on the strength of P0 simulator tests alone.
