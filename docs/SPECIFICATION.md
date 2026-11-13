# Offline Runtime Specification — FR / NFR

**Status:** normative proposal in draft PR #12. Once approved, `MUST` statements are binding for implementation; deviations require explicit documented ADR changes. Requirements start **unverified** until supported by CI/manual evidence. No assertion of passing offline tests is made here.

## 1. Product boundary and actors
**Product:** HASS Configurator Python application. Integration into the official Home Assistant OS File Editor add-on is a separate downstream change that cannot be assumed from this fork.

**Offline:** app/dependencies installed before testing; empty browser cache; public Internet and DNS unavailable to the client. The app's own origin and an explicitly configured local Home Assistant REST/WebSocket endpoint may remain accessible. Any **attempt** at public-origin browser fetch during supported scenarios is a failure even if blocked or nonessential. A deliberate user click opening external documentation is exempt, but no background link prefetch is exempt.

**Modes:** standalone Python, fork-built container, simulated reverse-proxy path prefix (P0), and real HA OS add-on Ingress (P1). `X-Ingress-Path` is supported in HA ingress but trusted only if injected by the configured ingress proxy (see `ARCHITECTURE.md`).

## 2. Functional requirements

| ID | Requirement (MUST unless otherwise stated) | Owner |
| --- | --- | --- |
| FR-001 | Serve editor/UI scripts, styles, required images, fonts, modes/themes/workers from packaged assets without Internet | #3, #4 |
| FR-002 | Preserve syntax highlighting, YAML diagnostics, editor options, autocompletion, keyboard bindings, search and themes | #3, #6 |
| FR-003 | Preserve filesystem browse/read/save/create/rename/delete and upload/download without data loss | #2, #6 |
| FR-004 | Preserve existing optional Git/exec and local HA operations subject to stronger authorization in P1 | #7, #8 |
| FR-005 | Work at root and arbitrary ingress path: canonical HTML, static resources, `api/*`, redirects, new-tab navigation, prefix rewriting and trusted header handling | #2, #8 |
| FR-006 | Local editor remains usable when optional HA REST or observer WS is unavailable | #6, #8 |
| FR-007 | No background fetch of outbound documentation links; external documentation opens only by explicit user action | #1, #6 |
| FR-008 | A new installed build is selected by reloading HTML and its fingerprinted asset manifest, even with previously warm browser cache | #2, #5, #6 |
| FR-009 | Only existing HA observer WS is required: read configured `ws_uri` / `HASS_WS_API`, handle failures; application MUST NOT implement an invented WS endpoint for offline work | #2, #8 |

## 3. Nonfunctional requirements

| ID | Normative requirement | Owner |
| --- | --- | --- |
| NFR-001 | **Any attempted public-origin browser request** during supported runtime scenarios fails test, including unsuccessful CDN fallbacks; only deliberate external documentation navigation and explicitly approved LAN HA REST/WS are exceptions | #6, #14 |
| NFR-002 | All bundled libraries are pinned, sourced from a single known artifact per library, hash-verifiable, and shipped with license notices | #1, #3, #5, #9 |
| NFR-003 | Permanent route dispatcher isolates exact/method-matched API paths from manifest-allowlisted static resources; no traversal/symlink escape or arbitrary file serving | #2, #7 |
| NFR-004 | One centralized HTTP response writer emits one status/header set with correct 404/405, MIME, `nosniff`, and deterministic errors | #2 |
| NFR-005 | Start cold-cache browser attempted-request smoke with #2, extend #3–#5 and finish full matrix with #6; distinguish P0 simulated ingress from P1 real ingress | #2, #6 |
| NFR-006 | Mutating APIs require appropriate authentication, authorization, CSRF defenses and confinement; dangerous Git/exec capabilities require reviewed defaults | #7 |
| NFR-007 | App version is consistent across runtime, package metadata, wheel/sdist/container; support matrix documented | #5, #10 |
| NFR-008 | Every code-affecting PR maps impacted FR/NFR/ADR to issue, tests/manual evidence and docs update (or justified N/A); GitHub Actions is the maintained CI baseline | #14 |
| NFR-009 | Fingerprinted immutable versioned assets; no-store for dynamic HTML and `/api/*`, with upgrades tested against cold and warm caches | #2, #5, #6 |
| NFR-010 | CSP has a dedicated owner, report-only/enforcement strategy and explicit disposition of unsafe inline behaviors and residual exceptions | #13, #7 |
| NFR-011 | Ace initial candidate MUST be audited `ace-builds@1.9.6` release tarball, **one** `src-min-noconflict` family, with npm integrity and per-file hashes; alternate choice requires ADR change | #1, #3 |

## 4. Architecture contracts that implement these requirements

### 4.1 HTTP routing
Application transport MAY initially remain Python `BaseHTTPRequestHandler`. **Permanent** router, static/package dispatcher and centralized HTTP response emission MUST be introduced in #2 and reused in P1 security hardening. This does not mandate a framework rewrite. Use exact route/method matches, explicit prefix handling, no duplicate responses and audited authorization boundaries.

### 4.2 Ingress and URL resolution
- At browser URL `https://ha.example/api/hassio_ingress/opaque/`, `assets/vDIGEST/ace/ace.js` and `api/file` MUST remain under that prefix externally; the proxy MAY strip it before forwarding to normalized internal handlers.
- HTML canonical base MUST end in `/`; redirects and new tabs MUST preserve the public prefix. No origin-root URLs for internal actions.
- Explicitly configured HA observer WS URI is a separate allowed **local HA endpoint**; no new application WS router is required.
- `X-Ingress-Path` MAY be used for response rendering only when received from **a trusted, explicitly configured ingress reverse proxy** that sanitizes user input; otherwise use relative URLs and ignore it. Direct clients MUST NOT be able to change the externally presented path.
- P0 verifies simulation and P1 verifies actual HA OS Ingress. Contract details and trust assumptions are in `ARCHITECTURE.md`.

### 4.3 Asset provenance and caching
- Select ONE verified Ace build family from an immutable published archive, including `ace.js`, `ext-*.js`, supported `mode-*.js`, `theme-*.js`, keyboard handlers, workers and transitive dependencies. Do not pull matching-named modules from arbitrary CDN copies.
- Bundle in URL namespace `assets/v<manifest-digest>/...` and use `Cache-Control: public, max-age=31536000, immutable` for hashed, non-secret static resources. All dynamic HTML, authenticated redirects and `/api/*` MUST send `Cache-Control: no-store`. Transitional fixed paths MUST revalidate and MUST NOT be served as immutable.
- A change to any asset or asset manifest MUST change digest; after an upgrade, refreshed HTML MUST resolve new digest and corresponding worker/module URLs.
- SHA-256 per file, package-integrity metadata and third-party licenses MUST be included in the build manifest; package and container version MUST match runtime.

### 4.4 CSP
CSP MUST be explicitly reviewed in #13, with report-only evidence, enforceable target, test coverage and public release decision. Existing inline scripts/handlers MUST NOT be silently treated as compatible with a strict policy; implement minimum necessary extraction during P1, leaving unrelated broad UI refactoring for P2. Residual exceptions require recorded acceptance and owner.

## 5. Acceptance matrix / test scenarios

| Scenario ID | Phase | Input, operation and observable pass condition | Related requirements |
| --- | --- | --- | --- |
| AT-01 | P0 | Cold browser cache, no public network: all supported UI paths render with **zero attempted external-origin fetches** (including failures) | FR-001, NFR-001 |
| AT-02 | P0 | Edit YAML, introduce error, see diagnostics, correct, save, reopen; content preserved | FR-002, FR-003 |
| AT-03 | P0 | Toggle supported Ace mode, theme and worker/language tools; all files fetched from same pinned build | FR-002, NFR-011 |
| AT-04 | P0 | Open all main dialogs, upload/download, navigation and theme controls offline | FR-003, NFR-001 |
| AT-05 | P0 | Simulated ingress prefix: HTML, scripts/fonts, REST GET/POST, redirects and new tabs retain external prefix; no trailing slash and spoofed ingress header tested | FR-005, NFR-003 |
| AT-06 | P0 | Disable local HA API/observer WS: editor still operates; no public fallback | FR-006, FR-009 |
| AT-07 | P0 | Static and API traversal/symlink/method collision tests; correct 403/404/405 and no double response | NFR-003, NFR-004 |
| AT-08 | P0 | Install wheel, sdist and container: all resources present; versions/hashes consistent | NFR-002, NFR-007, NFR-011 |
| AT-09 | P0 | Warm-cache install version A then B: HTML and Ace workers from B, old paths never masquerade as B; headers verified | FR-008, NFR-009 |
| AT-10 | P0 | GitHub Actions fails on injected public-origin fetch or missing asset; requirement-to-test mapping present | NFR-001, NFR-005, NFR-008 |
| AT-11 | P1 | Real HA OS add-on ingress: match simulated root/prefix functionality, trusted proxy behavior and local HA WS | FR-005, FR-009 |
| AT-12 | P1 | Auth, CSRF, file confinement, command/Git restrictions, XSS/CSP test evidence; high severity blockers closed | NFR-006, NFR-010 |

Tests are **planned** until recorded in `docs/TRACEABILITY.md`. No release gate is satisfied by merely having an issue or text in a document.

## 6. Traceability and release governance
- Each PR MUST state impacted requirement IDs (including ADRs), closing/related issues, automated test paths + CI run ID or manual test evidence, and changes to the traceability matrix. Reviewers MUST reject unsupported claims of passing tests.
- All normative changes MUST update relevant docs and test/issue mapping **in the same PR**. Deviations require explicit ADR, risk owner and expiry.
- P0 sign-off requires AT-01–AT-10 where applicable, simulated ingress only; P1 includes AT-11–AT-12 real deployment and security evidence. Blocking failures MUST NOT be waived silently.
- Branch protection requiring CI checks is recommended and tracked in #14; repository settings require a separate maintainer operation.
