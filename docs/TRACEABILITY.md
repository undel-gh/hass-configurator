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
