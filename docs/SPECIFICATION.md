# Offline Runtime Specification

Status: proposal, 2026-11-13.

## Definition of offline
The app is installed beforehand. Client browser has empty cache and no access to public Internet or public DNS. Application's own origin and optionally local Home Assistant REST/WebSocket remain reachable. Optional user-clicked external documentation links are permitted but cannot be required for functionality.

## Functional requirements
- **FR-001:** Serve UI, editor scripts, CSS, icons, fonts and optional functional imagery solely from packaged local assets.
- **FR-002:** Preserve syntax highlighting, YAML linting, Ace modes/themes, autocompletion, keyboard options, search, settings and worker behavior.
- **FR-003:** Preserve current file list/read/edit/save/create/rename/delete and upload/download behaviors, with no data loss.
- **FR-004:** Preserve optional Git, command and HA operations subject to existing authorization and security-hardening work.
- **FR-005:** Support root deployment and an arbitrary externally mounted HA Ingress prefix using the URL-routing contract defined in `ARCHITECTURE.md`: HTML entry/canonical slash, same-origin static and `/api/*` URLs, redirects, new-tab navigation and WebSockets; test the proxy-prefix behavior without assuming a specific fixed ingress path.
- **FR-006:** The editor remains usable if Home Assistant REST/WS is unavailable.
- **FR-007:** Third-party outbound documentation links must not be auto-fetched for core UI initialization.

## Nonfunctional requirements
- **NFR-001:** During supported user scenarios, **any browser-initiated attempt to request a public external origin is a test failure**, regardless of success, failure, fallback behavior or UI impact. This includes CSS imports, icons, images, CDN fallbacks, Ace dynamic modules and worker scripts. Exceptions: a deliberate user action opening external documentation; specifically approved local/LAN Home Assistant REST or WebSocket endpoints. Record and audit each exception.
- **NFR-002:** Pinned, license-compliant, hash-verified resources are present in wheel, sdist and container.
- **NFR-003:** Static server serves only allowlisted installed resources, never arbitrary filesystem content or `/config`; no path traversal/symlink escapes.
- **NFR-004:** Correct MIME, 200/404 semantics, safe request normalization, only one response per request.
- **NFR-005:** Introduce a minimum cold-cache browser network-denial smoke concurrently with static routing (#2); expand coverage across Ace (#3), CSS/fonts (#4), distribution (#5), and complete the E2E/HTTP release gate (#6). Detect **attempted** external requests, not only failed responses.
- **NFR-006:** Secure authenticated state-changing operations and least privilege for HA deployments.
- **NFR-007:** Pin and document Python, browser and HA OS/add-on compatibility matrix. Distribute one consistent application version across `setup.py`, runtime UI/API metadata, wheel/sdist and container labels; fail build on mismatch.

## Verification scenarios
1. Install built artifact, clear browser cache and disconnect Internet: UI loads with icons; all required requests are same origin.
2. Load YAML, edit, lint an invalid value, correct it, save and reopen.
3. Toggle Ace theme and language mode; exercise autocomplete and worker; verify no missing resources.
4. Use navigation, dialogs, file browser, upload/download and settings offline.
5. **P0:** repeat root and API/asset/redirect/new-tab/WS path tests behind a **simulated** HA ingress prefix, including missing trailing slash and untrusted `X-Ingress-Path`. **P1:** repeat with **real** HA Ingress/add-on setup.
6. Make internal HA REST/WS unavailable: local file editing continues.
7. Attempt encoded traversal, symlink escapes and static/API route collisions; requests are denied safely.
8. Install wheel, sdist and image independently; assert complete asset manifest.
9. Browser network interception/log: **zero attempted requests to public external origins** during supported scenarios (successful and failed requests both count). Allow only deliberate user-opened documentation links and explicitly approved LAN HA REST/WS. CI fails on regressions.

## Ingress URL contract (acceptance-level)
- No hard-coded root-relative `/assets/*` or `/api/*` references from a prefixed UI. All browser-facing URLs resolve relative to the active application document base; see `ARCHITECTURE.md` for canonical-path and proxy design.
- Local static/API HTTP requests, redirects and new tabs must stay within the external prefix. WebSocket URLs are derived separately with `ws:`/`wss:` and a matching prefix only where the WebSocket is served through the same ingress; configured LAN HA WebSocket URLs remain explicitly allowed.
- The backend must not infer the public ingress prefix from untrusted client headers. Use relative URLs as the default. Only if an explicit trusted reverse-proxy deployment requires it may an ingress header be used; do not blindly trust `X-Ingress-Path`.

## Release acceptance
P0 functional scenarios pass; then P1 security, HA OS smoke and compliance checks pass. A fork application release does not by itself update the official HA OS add-on.
