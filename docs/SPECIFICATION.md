# Offline Runtime Specification

Status: proposal, 2026-11-13.

## Definition of offline
The app is installed beforehand. Client browser has empty cache and no access to public Internet or public DNS. Application's own origin and optionally local Home Assistant REST/WebSocket remain reachable. Optional user-clicked external documentation links are permitted but cannot be required for functionality.

## Functional requirements
- **FR-001:** Serve UI, editor scripts, CSS, icons, fonts and optional functional imagery solely from packaged local assets.
- **FR-002:** Preserve syntax highlighting, YAML linting, Ace modes/themes, autocompletion, keyboard options, search, settings and worker behavior.
- **FR-003:** Preserve current file list/read/edit/save/create/rename/delete and upload/download behaviors, with no data loss.
- **FR-004:** Preserve optional Git, command and HA operations subject to existing authorization and security-hardening work.
- **FR-005:** Support root deployment and arbitrary Home Assistant ingress prefix without hard-coded absolute asset paths.
- **FR-006:** The editor remains usable if Home Assistant REST/WS is unavailable.
- **FR-007:** Third-party outbound documentation links must not be auto-fetched for core UI initialization.

## Nonfunctional requirements
- **NFR-001:** Zero mandatory external runtime requests, including dynamically resolved Ace workers, modes and themes.
- **NFR-002:** Pinned, license-compliant, hash-verified resources are present in wheel, sdist and container.
- **NFR-003:** Static server serves only allowlisted installed resources, never arbitrary filesystem content or `/config`; no path traversal/symlink escapes.
- **NFR-004:** Correct MIME, 200/404 semantics, safe request normalization, only one response per request.
- **NFR-005:** Automated cold-cache browser network-denial checks and Python static server tests gate release.
- **NFR-006:** Secure authenticated state-changing operations and least privilege for HA deployments.
- **NFR-007:** Pin and document Python, browser and HA OS/add-on compatibility matrix.

## Verification scenarios
1. Install built artifact, clear browser cache and disconnect Internet: UI loads with icons; all required requests are same origin.
2. Load YAML, edit, lint an invalid value, correct it, save and reopen.
3. Toggle Ace theme and language mode; exercise autocomplete and worker; verify no missing resources.
4. Use navigation, dialogs, file browser, upload/download and settings offline.
5. Repeat tests under simulated HA ingress subpath.
6. Make internal HA REST/WS unavailable: local file editing continues.
7. Attempt encoded traversal, symlink escapes and static/API route collisions; requests are denied safely.
8. Install wheel, sdist and image independently; assert complete asset manifest.
9. Browser log: no mandatory external requests or console errors; CI failure on regressions.

## Release acceptance
P0 functional scenarios pass; then P1 security, HA OS smoke and compliance checks pass. A fork application release does not by itself update the official HA OS add-on.
