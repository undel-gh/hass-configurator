# P1 API security audit and threat model — Issue #7

**Status (2026-11-14): security migration under review in PR #21.**
This is **not** a sign-off for public exposure or a real Home Assistant OS
Supervisor deployment. CI must pass on the final PR SHA, and the independent
security review must resolve all high-severity findings before closing #7.

## Trust boundaries and adversaries

| Entry / trust boundary | Abuse scenario | Required P1 disposition |
| --- | --- | --- |
| HTTP requests to a network listener | Unauthenticated remote client reaches editor or sensitive APIs | Server-side route admission: dynamic HTML and APIs require verified Basic Auth or a listener **bound to loopback** with a loopback peer; untrusted forwarded Host/Ingress/identity headers grant nothing |
| Browser with cached Basic credentials | Malicious third-party page induces state changes using simple forms/GETs | Per-process cryptographically random CSRF token rendered only into authenticated/local HTML, required as `X-CSRF-Token` on **all POST**; browser AJAX prefilter adds it only for same-origin URLs. No CORS opt-in. HA-control actions are POST-only (GET returns 405) |
| Client-controlled file paths and uploads | `..`, sibling-prefix, symlink escape, rename/write/delete, file metadata leakage or symlink swap races | `ConfinedFS` restricts every file path to `BASEPATH` (or the process working directory), rejects symlink traversal, and anchors file reads/mutations and directory listing/stat to directory descriptors via `O_NOFOLLOW` and `dir_fd`; symlinks are not advertised in the file browser |
| Shell endpoint | Shell commands or arbitrary binaries executed under service privileges | `/api/exec_command` disabled by default; enable only through `ALLOW_SHELL_COMMANDS` **and** a reviewed nonempty `EXEC_ALLOWED_BINARIES` list of absolute paths. Never `shell=True`; execute the canonical resolved allowlisted binary (not a caller-supplied symlink), with bounded timeout, constrained cwd and environment. This is still **not** an OS sandbox: permitted tools and arguments can access other paths with the service account's privileges |
| Git endpoints | Hooks, remote pushes, branch changes, GitPython invoking external commands | Git disabled by default. HTTP operations require `GIT` plus `ALLOW_GIT_OPERATIONS`. Worktree paths are checked against the configured workspace, including when GitPython searches parent directories. An explicitly enabled repository with malicious hooks is a residual high-risk capability; run with least-privilege OS permissions and review it as an admin operation |
| Network admin endpoints | Client changes allowed networks, grants global access, locks out operator | `/api/allowed_networks` and `/api/banned_ips` disabled by default; explicit `ALLOW_NETWORK_ADMIN` plus auth/CSRF required. Allowlist/banlist changes are serialized across concurrent HTTP handlers. Removing the final allowlist entry is refused atomically (empty list means allow-all in legacy logic); bans accept individual IPs, not silently ineffective CIDR ranges |
| Home Assistant control endpoints | Cross-site or browser prefetch calls restart/reload/check-config service actions | Six mutating actions now **POST only**, require `ALLOW_HA_CONTROL`, API authorization and CSRF. Read-only HA REST is still optional; no new application WebSocket endpoint |
| HTML template, file history, git branches, server errors | Reflected/stored XSS via file name, URL query, HA data or inline JS event attributes; HA token disclosure | Query-sourced JavaScript is JSON-encoded with HTML-script terminator escaping; HA-provided JSON is script-escaped, dynamic filename/error labels use text nodes and event listeners, server-held `HASS_API_PASSWORD` is never rendered into the page. Full CSP and remaining frontend refactor are tracked by #13 |
| Reverse proxies / true HA OS Ingress | Forged `X-Ingress-Path`/identity header or unauthenticated backend port | No proxy header grants authorization. Loopback trust is **only** valid when the process is bound directly to loopback and not exposed by an untrusted local forwarder. Validate Supervisor peer, port isolation and Ingress login/session behavior on a real installation under #8 before enabling HA OS access |

### Default behavior and compatibility

The old default of listening on `0.0.0.0` without credentials is no longer
sufficient to open an editable UI: dynamic HTML and API requests are **403**.
For standalone local testing use `--listen 127.0.0.1` (and bind the backend
socket directly; do **not** forward an unauthenticated reverse proxy to it).
Unauthenticated local access also requires a strict loopback HTTP `Host`
(`localhost`, `127.0.0.1`, or `[::1]` with an optional valid port), rejecting
DNS-rebinding aliases and malformed Host authority strings.
For network access configure `USERNAME`/`PASSWORD` (or CLI equivalents),
TLS or a reviewed secure proxy, and restrictive network/firewall rules.

The file confinement root is always enforced. `ENFORCE_BASEPATH=false` is
ignored with an explicit warning. Use a dedicated low-privilege process account
and a narrow `BASEPATH`. Only files under that path can be read and modified
through the editor. Symlinked directories and files are not supported. Writing to regular
files with multiple hardlinks is also refused, preventing a workspace hardlink
from truncating an inode also named outside the workspace. A same-UID local
attacker able to mutate filesystem links concurrently remains within the OS
trust boundary; do not treat these checks as a sandbox for a compromised
service account.

**Fork Docker runs as non-root UID/GID 10001:10001** by default. Existing
root-owned host bind mounts at `/config` may become unwritable: grant UID/GID
10001 access to a dedicated configuration directory, using appropriate ACLs
or ownership on the host. Example for an isolated local test, from the checked-out reviewed
commit of this fork (not a production HA OS Ingress deployment):

```sh
docker build --tag hc-fork:local .
sudo install -d -m 0750 -o 10001 -g 10001 /srv/hc-config
docker run --rm -p 127.0.0.1:3218:3218 \
  -v /srv/hc-config:/config \
  -e HC_USERNAME=review-user -e HC_PASSWORD='replace-with-a-real-secret' \
  hc-fork:local
```

The example still requires an authenticated HTTPS entry point and is **not**
Home Assistant Supervisor Ingress validation. CI's temporary browser mount
is deliberately writable by the host runner and container user; do **not**
copy the CI fixture permissions into production.

Privileged actions now require explicit booleans, all **false** by default:
`ALLOW_SHELL_COMMANDS`, `ALLOW_GIT_OPERATIONS`, `ALLOW_NETWORK_ADMIN`,
`ALLOW_HA_CONTROL`. Settings loaded from JSON/environment must contain actual
boolean values: `true` or `false`. String values such as `"false"`, numeric `0`/`1`
and `null` are rejected at startup, and the HTTP admission boundary never
treats a truthy value as an opt-in. Shell execution additionally requires a nonempty list
`EXEC_ALLOWED_BINARIES`, whose entries must be absolute executable paths.
Do not grant access to interpreters such as `python` or `bash` unless arbitrary
command execution as the service user is explicitly acceptable.

Previously supported GET requests to `/api/restart`, `/api/check_config`,
`/api/reload_automations`, `/api/reload_scripts`, `/api/reload_groups`
and `/api/reload_core` now return **405 Allow: POST**. Clients must issue
an authenticated POST with the CSRF header. The UI has been migrated.

### Bounded privileged execution and reads

Opt-in commands run in their own Unix process group. The server terminates
that entire group when the configured 1–30 s deadline expires, including child
processes that inherited stdout/stderr. Captured stdout+stderr is bounded to
256 KiB combined. This prevents a blocked worker from waiting indefinitely
in a second `communicate()` call after killing only the parent. This is not an
OS sandbox: an explicitly enabled executable may still spawn processes that
detach into other sessions or write files outside the workspace using the
service account's permissions.

`GET /api/file` and `GET /api/download` impose a 100 MiB in-memory read
limit and return HTTP 413 for oversized files; descriptor-based reads bound
bytes even if a file grows concurrently. Large-file streaming is outside
this change and would require additional API and browser compatibility tests.

### Secret-safe request logging

`SESAME`, passwords, TOTP secrets and credentials are redacted in debug
settings output. `HASS_API` and `HASS_WS_API` URLs are entirely masked,
including userinfo, query parameters and paths. HTTP request access logs
do not include the raw URL path/query: SESAME/TOTP bearer URLs must never
appear in server logs. Administrators should also avoid logging secrets in
arbitrary shell arguments or other externally configured components.

### Concurrent request safety

Network allowlist/banlist changes are synchronized across worker threads, so
concurrent removals cannot clear the final allowed range. `BANLIMIT`'s Basic
Auth failure counters are also synchronized: multiple simultaneous bad login
requests cannot lose updates and bypass the configured threshold. These
controls are tested through real multi-threaded HTTP requests.

### CSRF security model and limitations

The token is generated with `secrets.token_urlsafe(32)` once per process.
It is placed in a `Cache-Control: no-store` HTML response and sent by same-origin
jQuery AJAX. It is intentionally not placed in a cookie, URL or localStorage.
The token is neither a login credential nor proof of a user session. A client
must **first** pass the transport-side Basic/local-only access policy to
obtain it; a client cannot self-authenticate by supplying an arbitrary token,
`X-Forwarded-For` or `X-Ingress-Path`. The token changes across service
restarts, requiring browser reload for further POST operations.

Residual risk: the token is shared across authenticated users of this
single-admin process. This is acceptable for the current single Basic
credential model; it does not provide multi-tenant user isolation and must
be revisited if multiple session identities are added. A full XSS bypass of
same-origin scripting can recover the token — a reason to finish #13 CSP
and complete remaining XSS audit before public release.

### Explicit limitations and release blockers

- **Real Supervisor Ingress is NOT VERIFIED** (#8). Loopback binding alone
  does not authenticate an exposed reverse proxy. Don't grant privileges
  solely from peer IP or user-provided forwarded headers.
- **Strict CSP is NOT VERIFIED** (#13). Existing inline handlers/scripts
  require a separate staged CSP migration and report-only then enforced tests.
  This PR reduces specific injection paths; it cannot certify that all XSS
  sinks were found.
- **GitPython TOCTOU remains an explicit residual risk.** `validated_repo`
  checks the worktree lies inside the workspace, but GitPython resolves
  `.git`, indexes, and hooks via pathname-based filesystem operations after
  that validation. An attacker with the same Unix UID and concurrent write
  access may race symlink/path swaps. Enabling Git is therefore an
  administrator-only capability with OS-level trust, not a confinement proof.
- **Allowlisted shell tools and opt-in Git operations are privileged by
  design** and are not sandboxed by the application. Their public deployment
  requires a separate decision to disable them entirely or add host/container
  isolation and audited command policies. The safe default is **off**.
- **TOCTOU-resistant `openat`/dir-fd operations require Unix/Linux semantics**
  (`O_NOFOLLOW`, `dir_fd`). Actual HA OS runtime support is part of #8;
  non-Unix platforms cannot claim equivalent hardening until tested.
- **No public release sign-off.** Security/CSRF tests and P0 regressions
  are necessary, not sufficient. Security review must audit the exact PR SHA.

## Complete route and HTTP response-emitter audit (Issue #7)

This inventory was checked against every `send_response(...)`,
`write_http_response(...)`, and pre-router `_send_block(...)` occurrence
in `configurator.py`, plus the explicit `GET_API` and `POST_API`
sets in `http_routing.py`. There are **8 GET API routes** and **24 POST
API routes**, as well as the GET page `/`. All of those routes pass
`RequestHandler._dispatch_route` (and its `Router.security.authorize`)
**before any legacy response or request-body processing**.

| Entry points / route set | Security admission and mutations | Response owner |
| --- | --- | --- |
| GET `/` (editor) | Basic-authenticated request or trusted local-only listener + strict local Host; no mutation | Legacy `send_response` + `end_headers` adds one no-store/nosniff pair |
| GET `/api/file`, `/api/download` | Same admission; 100 MiB read limit and no-follow file descriptor access | `_serve_file` + shared response writer; 200/400/403/404/413 |
| GET `/api/listdir`, `/api/abspath`, `/api/parent`, `/api/prefs`, `/api/version`, `/api/netstat` | Same admission; no client-requested write | Legacy `send_response` + `end_headers` |
| POST `/api/save`, `/api/upload`, `/api/rename`, `/api/delete`, `/api/newfolder`, `/api/newfile`, `/api/prefs` | Auth + CSRF, confined file mutations; bounded request sizes | Legacy `send_response` + `end_headers`; early body-limit 413 uses shared writer |
| POST `/api/exec_command` | Auth + CSRF + `ALLOW_SHELL_COMMANDS` + nonempty binary allowlist; process-group timeout and output cap | Legacy success/error emitter, after router gate |
| POST `/api/gitadd`, `/api/gitdiff`, `/api/commit`, `/api/checkout`, `/api/newbranch`, `/api/init`, `/api/push`, `/api/stash` | Auth + CSRF + `GIT` + `ALLOW_GIT_OPERATIONS`; worktree path validation; GitPython residual below | Legacy success/error emitters, after router gate |
| POST `/api/allowed_networks`, `/api/banned_ips` | Auth + CSRF + `ALLOW_NETWORK_ADMIN`; serialized state changes | Legacy success/error emitters, after router gate |
| POST `/api/restart`, `/api/check_config`, `/api/reload_automations`, `/api/reload_scripts`, `/api/reload_groups`, `/api/reload_core` | Auth + CSRF + `ALLOW_HA_CONTROL`; no GET alias | Legacy success/error emitters, after router gate |
| Non-API asset aliases and versioned static resources | Exact GET-only allowlist, immutable digest or revalidation; cannot access arbitrary files | Router/Assets shared response writer |
| Invalid method, unknown or encoded route | Exact-match 400/404/405, before legacy handlers | Router shared response writer |
| Router admission refusals (missing auth, CSRF, disabled capability) | 403 before handling request body | Shared response writer, exactly one no-store/nosniff pair |
| Pre-router Host/network policy denial | 403/420, no API processing | Private `_send_block`; explicit no-store/nosniff |
| Basic Auth challenge or ban | 401/420, no API processing | `AuthHandler._send_auth_challenge` / `_send_block`; explicit no-store/nosniff |
| **Exceptional pre-router bearer URL** `SESAME` or `TOTP` | Exact GET token path intentionally changes the caller's IP allowlist. This is not a normal API session or a CSRF exemption available to other routes; the secret URL/TOTP is itself the authority. It must remain disabled or tightly network restricted on exposed installations; token guessing, browser history and reverse-proxy logs remain residual risks | Explicit 302 with no-store/nosniff, before router |

**Evidence:** `tests/test_api_security.py` iterates every registered GET/POST
route and verifies missing authentication, missing CSRF, and disabled
capabilities; socket-level checks verify the exact refusal headers. Additional
HTTP regressions cover the shell process tree, stdout ceiling, oversized
reads, XSS and concurrent requests. Browser regressions cover malicious
filenames, CSRF and repeated uplink navigation. None of the legacy direct
emitters is reachable before router admission; the pre-router bearer-URL
exceptions are explicitly identified above, not silently counted as ordinary
CSRF-protected APIs.

## Automated evidence mapping

| Security requirement | Source / test |
| --- | --- |
| NFR-003 filesystem confinement | `hass_configurator/api_security.py`, `tests/test_api_security.py` (prefix/sibling traversal, symlink and descriptor-bound operations) |
| NFR-006 route auth, CSRF, privileged API | `Router.security` and `RequestHandler._dispatch_route`, `tests/test_api_security.py`, `tests/test_legacy_contract.py` |
| NFR-010 XSS/CSP | Script-context JSON escaping and frontend safe text sinks in `configurator.py`/`dev.html`; **CSP remains pending #13** |
| ADR-003 and ADR-005 | Policy enforced by permanent exact-method Router; `tests/test_routing.py` and socket-level abuse fixtures |
| ADR-008 | This threat model and #13 staged CSP responsibility |
| AT-12 | API security abuse suite plus P0 browser/wheel/sdist/Docker regression. **Not fully verified until final PR CI, independent review and real #8/#13 evidence as applicable** |

Keep [`docs/TRACEABILITY.md`](TRACEABILITY.md) and the PR body tied to
the exact reviewed commit and current CI run. Previous #20 P0 evidence is
a historical baseline, not proof of this security change.
