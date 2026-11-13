# Real HA OS Ingress validation protocol (#8)

**NOT VERIFIED on actual Home Assistant OS.** Simulated prefix stripping in CI
does not establish browser → Home Assistant Core → Supervisor → app behavior.

This procedure deploys a **temporary, sandbox-only local app**, NOT the
official File Editor. Never install it over an existing app, and never expose
a port or mount your real HA configuration.

References:
- https://contributors.home-assistant.io/apps/guides/ingress/
- https://contributors.home-assistant.io/apps/reference/configuration/
- https://contributors.home-assistant.io/apps/how-apps-work/

## 1. Generate the disposable local app

From a clean checkout of the reviewed branch/commit:

    python scripts/prepare_haos_ingress_fixture.py --output /tmp/hc_ingress_validation

This refuses to overwrite a nonempty destination and verifies all 460
vendored files before copying the fork package into the app build context.
The output includes a fixture-provenance.json with commit and manifest hash.
No user configuration, credentials or device files are copied.

Transfer the generated hc_ingress_validation directory into the local apps
area of your HA OS device. Depending on release/mount, this may be exposed by
the addons Samba share (/addons), or as local_apps. Reload the app store,
install "HASS Configurator Ingress Validation (temporary)" and Open Web UI.

Its app config enables ingress on internal port 8099 with request streaming.
The nginx proxy allows only Supervisor's documented bridge peer 172.30.32.2;
all others are denied. A nonroot Python process serves only
/data/hc-ingress-validation; there are **no host directory mounts** or
exposed host ports. Privileged shell/Git/restart/network administration API
routes are blocked by the fixture proxy. The fixture runs with standalone
HA API disabled intentionally, pending #7 security hardening.

Docker base/dependencies are fetched at **build time**, not at runtime.
Reproducible production Docker builds remain #5.

## 2. Store a real authenticated browser session locally

The actual UI URL contains an opaque /api/hassio_ingress/<token>/ segment:
**treat it as secret**. Do not put it in a PR comment, CI, log, screenshot,
HAR or this conversation.

In a local shell, create Playwright storage state through a normal HA login:

    cd e2e
    mkdir -p .secrets
    npx playwright codegen --save-storage=.secrets/haos-state.json https://YOUR-HA-ORIGIN/

Log in, then close that browser. Set environment variables privately:

    HAOS_STORAGE_STATE=./.secrets/haos-state.json
    HAOS_INGRESS_URL='https://YOUR-HA-ORIGIN/api/hassio_ingress/OPAQUE/'
    export HAOS_STORAGE_STATE HAOS_INGRESS_URL
    npm run test:haos

The checked-in .gitignore protects e2e/.secrets/. If authentication expires,
refresh local storage state rather than sharing session tokens. Real browser
test reports should be kept private until sanitized.

File mutation is OFF by default. To test only the disposable fixture's
private /data sandbox, explicitly run:

    HAOS_TEST_MUTATIONS=1 npm run test:haos

Never enable it against the normal File Editor or a production file root.

## 3. Actual Ingress acceptance matrix

| Test | Required actual-HA-OS observation | Status |
| --- | --- | --- |
| HAOS-01 | Local test app source commit and manifest match reviewed HEAD | pending |
| HAOS-02 | Core/Supervisor session loads app through the real opaque prefix | pending |
| HAOS-03 | JS/CSS/fonts and lazy Ace theme/mode/worker use the opaque prefix | pending |
| HAOS-04 | YAML worker detects an error and clears it after correction | pending |
| HAOS-05 | API prefs works, no-store, zero off-origin attempts | pending |
| HAOS-06 | New-tab action preserves the external Ingress prefix | pending |
| HAOS-07 | Upload/download inside the isolated test app /data directory | pending |
| HAOS-08 | No public resource requests under network denial | pending |
| HAOS-09 | Real Supervisor X-Ingress-Path semantics and trusted peer policy verified; direct unauthorized access blocked | pending |
| HAOS-10 | Browser handles MIME after Supervisor header filtering | pending |
| HAOS-11 | Optional local Home Assistant REST/observer WS and loss recovery | not covered by standalone fixture |
| HAOS-12 | App upgrade and warm-cache/reload through real Supervisor | not covered by initial fixture |

The optional e2e/haos-real.spec.cjs tests the first-pass real browser flow
and attaches a redacted result summary (asset suffixes and status only).
Any captured raw HAR, browser trace, HTTP headers, cookies, filenames,
HA credentials, Ingress tokens or screenshots require separate redaction.
Never attach storageState or a full Ingress URL to public CI/PRs.

### HA API/WS limitation

The existing editor has only a *client* event-observer WebSocket to a
configured HA endpoint; it does not implement an application WS server.
The sandbox test app uses --standalone, because putting a Supervisor
credential into the legacy client HTML would be unsafe until #7.
HAOS-11 needs a separate secure HA-connected test; do not mark it passed
from this standalone fixture.

The real Supervisor can reconstruct/filter Content-Type. Assert successful
browser loading and compatible MIME families, not byte-for-byte charset
equality to direct Python headers.

## 4. Reviewer evidence and cleanup

Record HA Core/Supervisor/OS versions, browser version, fixture version and
commit, timestamp, pass/fail for each HAOS row, sanitized request/response
findings and any follow-up PR. Link the resulting nonsecret evidence in
docs/TRACEABILITY.md before marking AT-11 verified.

Uninstall the temporary local app and delete its generated local source
after the validation; do not alter the original File Editor installation.
