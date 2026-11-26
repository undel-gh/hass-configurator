# P1 Content Security Policy (#13)

Status (2026-11-26): scoped #13 implementation reviewed and real-HAOS
CSP-HAOS-01…09 accepted within tested paths; temporary inline CSS exception
explicitly accepted by the maintainer and tracked in #31. PR #30 is not a
public-release signoff; final documentation-only HEAD CI/merge remain separate.
Owner of the issue: repository maintainer (`undel-gh`), with independent #7
security co-review. No new HA OS or external service permissions are requested.

## Threat model and inventory

- Stored/reflected HTML or script injection through paths, names, errors or HA
  bootstrap data could bypass CSRF by executing as the authenticated origin.
  Existing #7 escaping, server-side privilege gates and confinement remain required.
- The base template contained eight inline script blocks and 94 static
  `onclick`/`onchange` attributes (76 distinct event/action combinations).
  The Ace bootstrap and fixed handler functions are now versioned local assets;
  remaining seven script blocks carry a cryptographically random per-page nonce.
  Binding uses fixed JS functions and existing controls, not eval, dynamic
  handler source or document-wide delegation. Dynamic file browser callbacks
  were already JS function bindings. No first-party eval/new Function is needed.
- Ace core, lazy modes/themes/keyboard modules and YAML worker use the pinned
  same-origin versioned asset directory. Ace uses a blob-backed worker launcher;
  style injection by Ace and Materialize plus legacy style attributes requires
  a staged CSS migration. Third-party assets are not patched in this change.
  The entrypoint lexical inventory (base and extracted first-party scripts,
  jQuery, js-yaml, Materialize, Ace core, ext-language_tools and worker-yaml)
  found no direct eval/new Function in the first-party files or jQuery/js-yaml.
  Materialize contains one new Function in a string callback branch;
  worker-yaml has two new Function occurrences in bundled JS-function parsing
  and one Function fallback for global-object detection. Ace core contains the
  expected blob launcher with importScripts/createObjectURL. This is a lexical
  scan, not proof that every runtime path is safe. No string callback or eval
  waiver is added; exercised normal paths must work without unsafe-eval.
  Unexercised modes/plugins are not certified.
- Browser HA observer uses the configured `HASS_WS_API` or WS derived from
  `HASS_API`. Server-side REST and the isolated Supervisor probe are not
  browser CSP connections. No app-origin WebSocket endpoint is introduced.
  Same-origin requests are necessary for the editor API and assets.
- Editable SVG and other file responses are untrusted documents, not the
  nonce-bearing application. Direct navigation must not execute script.

## Policy and staging

| Directive | Enforced candidate | Report-only target / rationale |
| --- | --- | --- |
| default-src | 'none' | deny unspecified resource types |
| script-src | 'self' + fresh nonce | same; no unsafe-inline, unsafe-eval, remote host, or blob script source |
| script-src-attr | 'none' | no inline event attributes |
| style-src | 'self' 'unsafe-inline' | 'self'; observe legacy inline style and vendor style creation |
| font-src | 'self' | local vendored fonts |
| img-src | 'self' data: blob: | local images and editor previews |
| worker-src | 'self' blob: | Ace blob launcher and local worker scripts; no public URL |
| connect-src | 'self' + explicit configured WS URL, when valid | same; no blanket ws:/wss: or wildcard host |
| object-src / base-uri | 'none' | deny plugin objects and injected base tags |
| frame-ancestors | 'self' | HA same-origin Ingress iframe; operator-confirmed real Supervisor/browser PASS |
| form-action | 'self' | no off-origin form submission |
| frame-src | 'none' | no embedded child frames required |

Both headers are emitted once for the authenticated no-store editor page.
The Report-Only header differs only for style-src, so it can detect the
CSS migration debt while script/network controls already enforce in the
draft candidate. There is no report-uri, report-to, report collector or
external telemetry. Tests collect only effectiveDirective/disposition.
This is not a general client-side XSS sandbox: same-origin script allowance
is necessary for current Ace loading; shared reverse-proxy origins and
trusted vendor code remain part of the trust model. CSP cannot constrain
server-side network requests or all navigation types. HTTPS/mixed-content
rules still apply.

The nonce is generated before rendering, never cached; it appears only on
explicit static script tags, never on injected DOM or user file responses.
HA services/events/states are parsed and reserialized as JSON lists before
script interpolation; invalid/non-finite content fails closed to [].
File/download responses receive a separate sandbox + default-src none policy
so an editable SVG cannot execute as a same-origin page.

## Configuration compatibility

The observer URI is read-only in the UI: set HASS_WS_API on the server or
derive from HASS_API; no ad-hoc browser WS override is supported. A missing or
invalid configuration leaves the editor operational and observer disabled.
Explicit invalid/empty overrides do not fall back. Only header-safe
ASCII DNS/IPv4 hosts with optional canonical port and simple exact URL paths
are accepted. Credentials, query/fragment, wildcard, escaped/ambiguous paths,
and IPv6 literals are intentionally not admitted by this candidate; document
any needed compatibility work rather than allowing broad CSP sources.
The operator must approve the actual HA LAN endpoint and maintain network
policy/DNS trust; CSP is not a DNS/IP firewall. 'self' retains the app API
origin and browser CSP scheme/redirect semantics apply.

## Verification matrix

| Gate | Evidence |
| --- | --- |
| Headers and nonce | tests/test_routing.py: exact headers, per-response nonce, static cache/API separation, no inline attributes |
| Source allowlist and injection | tests/test_csp.py: derivation, invalid input, no policy injection; tests/test_api_security.py: bootstrap JSON and untrusted file sandbox |
| Browser enforcement | e2e/csp.spec.cjs: real editor/handler, script + event denial, report-only style event, same-origin frame, direct SVG sandbox |
| Existing UX and worker behavior | e2e/offline-dynamic.spec.cjs, offline-smoke, ingress-operations, release-matrix, Docker/wheel/sdist |
| Observer | e2e/ha-outage.spec.cjs: configured URI and failed connection do not prevent editing; invalid browser override refused; native local mock handshake on approved endpoint and denial on another path (not HA authentication) |
| Real Supervisor | e2e/haos-real.spec.cjs plus actual sidebar iframe/new tab, isolated file CRUD/roundtrip, warm-profile upgrade; CSP-HAOS-01…09 PASS within exercised scope (operator evidence) |
| Acceptance | two independent reviews and exact-HEAD CI; #26 actual Core REST/WS still separate |

Tests-only RED and all follow-up CI results belong in PR #30 with exact SHAs.
Public CI simulates Ingress; prior #8 field evidence is not evidence for new
CSP headers or framing behavior. The new #13 field results are recorded in
[HAOS_REAL_INGRESS.md](HAOS_REAL_INGRESS.md), separate from historical #8.
Reviewed runtime/test source `bbab9cc7051c1a90db256ffbb30a06360f3226fc`
passed [CI 4/4](https://github.com/undel-gh/hass-configurator/actions/runs/45848462928)
(131 Python tests), two independent reviews and focused mutation follow-up.
Both real HAOS fixtures were built from this source with only a harmless CSS
cache marker in the copied package. Final documentation-only changes do not
alter tested runtime/test files; verify CI on their exact new HEAD.

## Release-risk decision (explicit temporary acceptance)

| Residual | Owner / issue | Expiry / gate | Disposition |
| --- | --- | --- | --- |
| Inline styles allowed in enforcement, strict CSS only Report-Only | maintainer `undel-gh` / [#31](https://github.com/undel-gh/hass-configurator/issues/31) | expiry/review 2026-12-31 or before first public release, whichever comes first | TEMPORARILY ACCEPTED by maintainer 2026-11-26 for scoped #13, not unconditional release approval. Remove/narrow or explicitly re-evaluate with dated signoff; no silent rollover. |
| Real HA OS CSP/iframe compatibility | maintainer `undel-gh` / #13 | before #13 acceptance | PASS (operator-reported CSP-HAOS-01…09, including same-profile warm upgrade); tested paths only. |
| Live Core REST/WS observer/auth | maintainer / #26 | before claiming live support | DEFERRED, not validated by this PR. |

The exception is limited to inline CSS for the template, Ace and Materialize;
no script unsafe-inline/unsafe-eval or other policy relaxation is accepted.
Inline CSS still permits UI manipulation and potentially CSS-based disclosure
through allowed resource channels. Strict CSS Report-Only is diagnostic, not
preventive; enforced script/resource restrictions and #7 remain compensating
controls. See [maintainer decision](https://github.com/undel-gh/hass-configurator/issues/13#issuecomment-7198566758)
and [field completion](https://github.com/undel-gh/hass-configurator/issues/13#issuecomment-7198608252).
Do not mark NFR-010, ADR-008, AT-12 or overall P1/public release unconditionally
verified merely because the scoped #13 implementation is accepted. Broader frontend
architecture work remains #11, not a blanket waiver of CSP requirements.
