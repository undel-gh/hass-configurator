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
