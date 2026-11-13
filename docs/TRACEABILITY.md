# Requirements and evidence traceability

**Status: all runtime requirements are PENDING.** This is a normative **tracking contract**, not evidence of implementation. CI has not yet been configured in this documentation PR. Mark `verified` only after referencing reproducible passing automated checks or recorded manual artifacts on the matching commit.

## Usage rules
- Every code PR MUST identify impacted requirement IDs and controlling ADRs, GitHub Issue(s), test paths and CI run numbers; if no test is appropriate, include rationale and a named manual validation record.
- Change `Status` to `verified` only when linkable tests have passed against the relevant implementation commit. On changed requirements or regressions, reset to `pending` until re-verified. Never mark a requirement verified simply because a document or Issue exists.
- A risk waiver MUST identify severity, owner, remediation Issue and expiry; it cannot silently override high-severity release blockers.
- The paths in the `Planned evidence` column are proposals, not claims that files or CI jobs already exist. They can change, but ownership/coverage cannot disappear without updated ADR and reviewer approval.
- Root and simulated ingress tests are P0; actual HA OS add-on Ingress is P1.

## Functional requirements

| ID | Owner Issues | Planned evidence | Status |
| --- | --- | --- | --- |
| FR-001 | #3, #4 | e2e/offline.spec: cold start, styles, icons, images, Ace files | pending |
| FR-002 | #3, #6 | e2e/offline.spec: YAML/lint/themes/modes/workers | pending |
| FR-003 | #2, #6 | tests/test_routing.py + e2e/offline.spec: read/edit/save/upload/download | pending |
| FR-004 | #7, #8 | tests/test_api_security.py + HA OS manual matrix | pending |
| FR-005 | #2, #8 | e2e/ingress.spec (P0 simulated), HA OS Ingress test record (P1) | pending |
| FR-006 | #6, #8 | e2e/offline.spec: HA REST/WS unavailable | pending |
| FR-007 | #1, #6 | e2e/offline.spec: no link prefetch | pending |
| FR-008 | #2, #5, #6 | e2e/cache-upgrade.spec: versions A→B | pending |
| FR-009 | #2, #8 | browser test of configured `ws_uri`, no app WS endpoint | pending |

## Nonfunctional requirements

| ID | Owner Issues | Planned evidence | Status |
| --- | --- | --- | --- |
| NFR-001 | #6, #14 | attempted-network-request intercept + deliberate exceptions | pending |
| NFR-002 | #1, #3, #5, #9 | vendored artifact lock, integrity/hashes/license CI | pending |
| NFR-003 | #2, #7 | tests/test_routing.py: exact-method, traversal, symlinks | pending |
| NFR-004 | #2 | tests/test_routing.py: MIME, single response, 404/405/nosniff | pending |
| NFR-005 | #2, #6 | early E2E GH Actions smoke, full E2E later | pending |
| NFR-006 | #7 | tests/test_api_security.py: auth/CSRF/confinement/exec | pending |
| NFR-007 | #5, #10 | installed wheel/sdist/container version tests | pending |
| NFR-008 | #14 | GitHub Actions workflow + PR template + this matrix | pending |
| NFR-009 | #2, #5, #6 | cache headers tests, warm upgrade, immutable digest | pending |
| NFR-010 | #13, #7 | CSP header/report-only/enforcement/violation tests | pending |
| NFR-011 | #1, #3 | Ace tarball integrity + single-family closure check | pending |

## Architectural decisions

| ID | Owner Issues | Planned evidence | Status |
| --- | --- | --- | --- |
| ADR-001 | #1 | base branch and migration analysis documented | pending |
| ADR-002 | #6, #14 | network-attempt E2E | pending |
| ADR-003 | #2, #7 | permanent dispatcher contract and response tests | pending |
| ADR-004 | #2, #8 | simulated/real ingress traces, trusted header tests | pending |
| ADR-005 | #7 | API security regression suite | pending |
| ADR-006 | #1, #3 | ace-builds@1.9.6 lock + family compatibility validation | pending |
| ADR-007 | #14 | PR checklist + required CI/evidence policy | pending |
| ADR-008 | #13 | CSP review, tests, release-risk disposition | pending |
| ADR-009 | #2, #5, #6 | stable digest/headers/upgrade tests | pending |

## Release gates

| Gate | Required scenarios | Verification state |
| --- | --- | --- |
| P0 | AT-01–AT-10 as applicable, with simulated ingress and blocked public Internet | pending |
| P1 | P0 regression, AT-11 real HA OS Ingress, AT-12 API security+CSP and license/release checks | pending |

## PR evidence log template
Copy one row per impacted requirement:

| Requirement | Issue | Implementing PR/commit | Test path | CI run or manual evidence | Status |
| --- | --- | --- | --- | --- | --- |
| FR-005 | #2 | — | planned e2e/ingress.spec | — | pending |

No implementation PR should leave unfilled evidence fields when claiming a `verified` requirement.


## Implementation checkpoint — PR #15 (#1, #2, #14)

**Not a release sign-off.** Full P0 NFR-001, FR-001, AT-01, AT-03, AT-05, AT-09 and HA OS P1 acceptance remain pending. No requirement row above is changed to `verified` by this checkpoint.

| Requirement / ADR | Evidence introduced | Verification state |
| --- | --- | --- |
| FR-005 / ADR-004 | `tests/test_routing.py`, `e2e/offline-smoke.spec.cjs`: root, versioned assets and simulated ingress prefix asset requests; no real HA OS Ingress | **partial**, P1 #8 pending |
| NFR-003 / ADR-003 | `hass_configurator/http_routing.py` exact-path/method dispatcher, `tests/test_routing.py` including route collisions/traversal | **partial**; legacy API policy migration #7 pending |
| NFR-004 | Central response writer for new static/errors, MIME, nosniff, 404/405, single-response HTTP checks | **partial**; legacy API handlers remain direct |
| NFR-009 / ADR-009 | 16-hex-digest versioned namespace, private immutable static and no-store HTML/API; `tests/test_routing.py` | **partial**; warm-cache A→B test #5/#6 pending |
| NFR-001 / ADR-002 | `e2e/offline-smoke.spec.cjs` intercepts browser requests at initiation, proves off-origin fixture detection, persists baseline JSON artifact | **not met**; full UI test explicitly expected failure (#3/#4) |
| NFR-002 / NFR-011 / ADR-006 | `docs/ace-builds-1.9.6-lock.json`, `scripts/verify_ace_archive.py` official npm SRI + full file hashes | **partial**; 3 obsolete modes / dynamic closure #3 pending |
| NFR-008 / ADR-007 | `.github/workflows/offline-foundation.yml`, `tests/test_traceability.py`, PR checklist | **partial**; CI HEAD outcome and repo branch protection not yet recorded |
| NFR-005 | Minimum Chromium smoke plus Python routing tests, early CI | **partial**; full E2E gate #6 pending |

### Independent review follow-up (two reviews)
- `e2e/offline-smoke.spec.cjs` now opens **real HTML at /ingress/test/** and asserts browser-requested same-prefix JS, CSS, font and `api/prefs`. The original synthetic `page.setContent` test has been removed.
- `tests/test_legacy_contract.py` independently pins all GET/POST legacy routes and executes safe `POST /api/prefs`, `POST /api/save` and `GET /api/file?filename=...` round trips. Both unauthenticated and successful authenticated `AuthHandler` access to API/static are covered.
- HEAD, PUT and DELETE are intentionally **unimplemented 501** (rather than a superficially implemented but unauthenticated HEAD). Future HEAD support requires safe RFC-compliant semantics without replaying state-changing GET routes.
- `e2e/package-lock.json` pins transitive Playwright packages, installed by `npm ci`. Source-level JS MIME is now `text/javascript` per RFC 9239; Supervisor Ingress rewriting must be tested by behavior, not exact backend header equality.
- Local-assets-on-startup fail-fast, root-path compatibility change and operational consequences are documented in `FOUNDATION_IMPLEMENTATION.md`. Required P1 release scenarios **remain pending**.

For the current/last CI runs and exact commit evidence see [PR #15](https://github.com/undel-gh/hass-configurator/pull/15) checks and [foundation notes](FOUNDATION_IMPLEMENTATION.md). Avoid copying an obsolete CI run ID as evidence for a newer commit.

## PR #16 — Offline Ace and CSS/MDI implementation checkpoint (#3, #4)

**Full application release gates remain pending.** This checkpoint records tested implementation scope without upgrading P1 real HA OS Ingress, Docker deployment, CSRF/security, warm-cache upgrade, all-dialog E2E or SBOM to `verified`.

| Requirement | Implementation | Evidence / status |
| --- | --- | --- |
| FR-001 | All Ace, Materialize CSS, MDI icons, Roboto and fallback fonts served from local versioned static paths | `tests/test_vendored_assets.py`, `e2e/offline-smoke.spec.cjs`, `e2e/offline-dynamic.spec.cjs`; scoped **verified in CI**, full release pending |
| FR-002 | YAML worker diagnostics, language modes, theme loading, keyboard modules, language tools | `e2e/offline-dynamic.spec.cjs`: invalid→corrected YAML annotations and lazy loads; **partial** until broad UI matrix #6 |
| FR-005 / ADR-004 | App-relative URLs and Ace dynamic worker/config paths behind simulated prefix | Actual HTML + fonts and API exercised in Playwright; **partial**, real HA OS #8 pending |
| NFR-001 / ADR-002 | All five initial CDN loads replaced; all 13 automatic external avatars removed; cold-cache browser attempts blocked/checked | `scripts/audit_runtime_assets.py --strict-offline` and Playwright root+simulated ingress; **partial**, full #6 scenarios pending |
| NFR-002 / ADR-006 | npm tarballs pinned by SHA-512 SRI + SHA-256; all 460 resources verified by digest, complete archive reconstruction CI | `hass_configurator/vendor/manifest.json`, `scripts/vendor_offline_assets.py --verify-only`; **partial**, license/SBOM review #9 pending |
| NFR-011 | Single `ace-builds@1.9.6` `src-min-noconflict` build (440 files), all currently offered modes available | `scripts/verify_ace_archive.py`, `tests/test_vendored_assets.py`; three obsolete selectors removed, **verified for supported UI choices** |
| NFR-009 / ADR-009 | Bundled resources in fingerprinted immutable namespace; SHA digest and MIME verified | `tests/test_vendored_assets.py`; warm-cache upgrades remain **pending** #5/#6 |
| NFR-007 | Wheel and sdist include all local assets and manifest | `scripts/check_offline_artifacts.py` in GitHub Actions; **partial**, single version source and fork-built Docker #5 pending |

**Verification pointer:** [PR #16 checks](https://github.com/undel-gh/hass-configurator/pull/16). Review the CI run on the implementing HEAD, not an earlier branch commit. The independent strict-offline browser test is now a real passing assertion; no `test.fail()` or skip is used.

## PR #17 — Expanded P0 E2E matrix and P1 real Ingress validation kit (#6, #8)

**Do not equate an executable HA OS test fixture with a completed AT-11.** The
following results concern CI on an isolated runner and a synthetic Ingress
prefix only. Real Home Assistant Core/Supervisor traffic has not been tested
and the P1 acceptance rows remain **pending**.

| Scenario / Requirement | Implemented evidence | State / remaining work |
| --- | --- | --- |
| AT-01 / FR-001 / NFR-001 | `e2e/offline-smoke.spec.cjs`, `e2e/offline-dynamic.spec.cjs`, new UI interaction tests; abort and count every attempted unapproved browser origin | **scoped pass** on tested browser paths; complete UI matrix review pending |
| AT-02 / FR-002 / FR-003 | `e2e/offline-dynamic.spec.cjs` real YAML worker invalid→corrected, `e2e/release-matrix.spec.cjs` browse/edit/save/reload/download | **scoped pass** in temporary workspace |
| AT-03 / FR-002 / NFR-011 | Existing dynamic Ace mode/theme/keybindings, language tools, workers including prefixed loads | **scoped pass** |
| AT-04 / FR-003 | `e2e/release-matrix.spec.cjs` opens/closes all 30 dialogs **without executing privileged confirmation actions**; file navigation, upload/download, new-tab and theme smoke | **partial**: individual privileged business operations are intentionally not executed; #7 owns security |
| AT-05 / FR-005 / ADR-004 | Real HTML through simulated prefix; new `e2e/ingress-operations.spec.cjs` verifies GET file/listdir/download and POST save/upload; `tests/test_ingress_redirect.py` checks 302 Location './' | **partial**: no actual Supervisor, trailing slash variations require real check |
| AT-06 / FR-006 / FR-009 | `e2e/ha-outage.spec.cjs` uses a disconnected local HA REST endpoint and refused client WS; local editor still saves | **scoped pass**, real HA WS authentication pending #8/#7 |
| AT-07 / NFR-003 / NFR-004 | Existing router/method/traversal/cache/symlink tests retained | **scoped pass** |
| AT-08 / NFR-007 | wheel/sdist byte-exact tests (460 vendor + 6 first-party) plus selected browser tests against each **isolated** installed artifact (server cwd outside checkout; Python asserts imported module paths inside the venv); temporary HA OS app container build/health/ACL smoke | **partial**: production fork Docker image reproducibility/version is #5 |
| AT-09 / FR-008 / NFR-009 | `e2e/cache-upgrade.spec.cjs` runs two real app instances with changed first-party stylesheet in the **same warm Chromium browser**, both at root and via a real local prefix-stripping HTTP proxy (no Playwright route interception/cache disabling); asserts new digest, no-store HTML, immutable resources and the B-version YAML worker | **scoped pass**; real HA OS warm upgrade pending |
| AT-10 / NFR-005 | CI browser interception fixture proves public-origin denial, integrity tests reject missing/corrupt vendored file; traceability assertions | **scoped pass**; branch protection remains repository setting |
| AT-11 / FR-005 / ADR-004 | `haos-fixture/`, `scripts/prepare_haos_ingress_fixture.py`, `e2e/haos-real.spec.cjs`, `docs/HAOS_REAL_INGRESS.md` | **NOT VERIFIED:** a real Home Assistant OS device, Supervisor session and redacted evidence required; HA REST/WS and warm upgrade remain untested |
| AT-12 / NFR-006 / NFR-010 | Security issues #7/#13 own auth, CSRF, filesystem, CSP | **pending**, not included in #17 |

The actual `e2e/haos-real.spec.cjs` suite is **opt-in** through
`npm run test:haos` with local authenticated browser state, and is excluded
from public CI. Its test URLs and session state MUST remain private. All real Ingress navigation errors are masked by `e2e/haos-private.cjs`; browser session state is parsed defensively before Playwright creates the context, and `e2e/haos-privacy.spec.cjs` checks the behavior with a synthetic bearer-like URL. Nevertheless, **real local browser reports remain potentially sensitive** and must never be uploaded unreviewed.

For exact run/commit evidence consult [PR #17](https://github.com/undel-gh/hass-configurator/pull/17)
and its checks rather than treating an older run identifier as permanent proof.

## PR #18 — automated P0 fork packaging and release identity (#5, #6, #14)

**Scope-specific evidence; not full P0/P1 release sign-off.** Reference the
current PR HEAD check run; no verification claim is inherited from #17.
The runtime/package version is now read from a single
`hass_configurator/_version.py` file; the read-only `GET /api/version`
uses an exact method-aware router route and `no-store` caching.

| ID / gate | Implemented check | Pending boundary |
| --- | --- | --- |
| FR-008 / NFR-007 / AT-08 | `setup.py`, `hass_configurator/_version.py`, `tests/test_legacy_contract.py`: metadata=runtime=UI=API; `scripts/check_offline_artifacts.py` verifies wheel/sdist distribution metadata, shared version file and all 460 vendor + 7 first-party files (including `dev.html`) | Release image base digest/transitive dependencies not hash-pinned; full byte-identical builds still #5/#9 |
| NFR-002 / NFR-007 / NFR-011 / AT-08 | New multistage main `Dockerfile` installs **this checkout's wheel**; `e2e/docker-runtime.spec.cjs` exercises local editor/file operations on the actual fork-built image; CI checks resource fingerprint matches source and image can boot with `--network none` | Real HA OS app integration/HTTP ingress remains separate P1; Docker image is not the official File Editor |
| NFR-001 / NFR-005 / AT-10 | `tests/test_p0_failure_gates.py` injects an external script and simulates absent local/vendor assets, asserting negative failures; existing browser tests preserve strict public-origin attempt checks | Owner #14 for repository branch protection settings |
| NFR-009 / ADR-009 / AT-09 | Existing root + prefixed warm A→B tests retained; expected same exact immutable fingerprint across source, installed packages and container | Actual Supervisor warm upgrade remains pending |

The new distribution API does not eliminate authentication, CSRF or privileged
operation risks. Do not mark AT-11/AT-12, #7, #9, #13 or full #5 verified
from this implementation. Reproducible build of transitive Python packages
and immutable Docker base still requires a reviewed pin/update process. See
[docs/P0_PACKAGING.md](P0_PACKAGING.md).

## PR #19 — immutable Docker runtime closure, deterministic build release gate (#5)

**No real HA OS/Supervisor checks are performed by this PR.** Record a green
run for the exact reviewed HEAD before promoting any state to verified.

| Requirement / gate | Automated evidence | Review boundary |
| --- | --- | --- |
| NFR-002 / NFR-011 / ADR-006 | Official `python:3.11.18-bookworm` index digest is pinned in the Dockerfile; the full `requirements/docker-runtime.lock` lists direct/transitive distributions with binary wheel SHA-256; `scripts/check_docker_runtime_lock.py` plus `tests/test_docker_runtime_lock.py` enforce exact hash, unique versions and setup requirements | Base image is larger than slim; supply-chain license/SBOM/vulnerability adjudication remains #9 |
| NFR-007 / FR-008 / AT-08 | Fork wheel built with `--no-index --no-build-isolation --no-deps`; runtime deps installed from an offline wheelhouse with `--require-hashes` and `pip check`; container's installed versions and origin are verified with network disabled | Only linux/amd64 is demonstrated in CI; multi-architecture reproducibility not claimed |
| NFR-009 / ADR-009 / AT-09 | CI performs **two no-cache builds from one commit and SOURCE_DATE_EPOCH**, compares Docker image IDs, then runs installed-container/browser tests and preserves the existing root/Ingress A→B asset warm-cache tests | Registry push artifacts/attestations may have different OCI manifest digests; real Supervisor upgrades remain #8 |

A matching browser asset digest alone is never sufficient as proof that the
entire image is repeatable. See `docs/P0_PACKAGING.md` for source-epoch and
lock regeneration. Real HA OS Ingress and privileged API hardening remain
separate P1 acceptance (#8/#7/#13).
