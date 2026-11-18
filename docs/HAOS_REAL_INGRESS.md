# Actual Home Assistant OS Ingress acceptance protocol — Issue #8

**State: NOT YET VERIFIED on an actual HA OS device.** This repository can
build and smoke-test a disposable app container, but CI does not connect
browser → Home Assistant Core → Supervisor → local app. No test run from
a regular Docker container can substitute for the HAOS-01…HAOS-12 evidence.

**Scope and isolation:** This is a *temporary local test app*, not the official
Home Assistant File Editor or a production replacement. It mounts no
`/config`, `/share`, `/media`, Docker socket or user files, publishes no
host port, and restricts editing to `/data/hc-ingress-validation`.
Privileged shell/Git/network/HA-control routes remain disabled by #7 and
blocked again in the fixture nginx. Use an isolated/test HA OS installation.

References: [Official Ingress guide](https://contributors.home-assistant.io/apps/guides/ingress/),
[app configuration](https://contributors.home-assistant.io/apps/reference/configuration/),
[Supervisor/Core communication](https://contributors.home-assistant.io/apps/guides/communication/).

## 1. Generate the local app from the reviewed HEAD

From a clean checkout of the reviewed PR commit:

```sh
python scripts/prepare_haos_ingress_fixture.py \
  --output /tmp/hc_ingress_validation
```

Generator refuses to overwrite nonempty directories, verifies the installed
offline vendor manifest and all 460 resources, and copies this checkout
rather than fetching a package from PyPI. Keep
`fixture-provenance.json` locally; its commit SHA and vendor-manifest SHA
identify the source for HAOS-01. No HA configuration is copied.

Transfer the generated `hc_ingress_validation` directory to your HA OS
**Local apps** source (older UI/Samba installations may call it `addons`,
current UI may call it `local_apps`). Reload the local app store, install
the temporary test app, start it and select **Open Web UI**. Do not replace
the installed official File Editor.

This fixture uses `ingress: true`, `ingress_stream: true`, internal
port 8099 and nginx's documented Supervisor-only bridge allowlist
`172.30.32.2`; the Python editor binds solely to `127.0.0.1:3218`
inside the container. Nginx now **replaces** the forwarded Host with
`127.0.0.1:3218`, because #7 requires a local authority for loopback
access. It drops XFF, X-Ingress-Path and injected user-identity headers
before forwarding to Python. It does not authenticate based on them.

The fixture-only `__haos_probe` is reachable only through the
Supervisor-restricted nginx proxy. It returns `/api/version` with
`X-HC-Fixture-Id: hc-ingress-validation-v1`, an enumerated
`X-HC-Ingress-Path-Status: valid|invalid` and
`X-HC-User-Id-Status: present|absent|spoofed` (the latter detects only
the fixed test marker `forged-browser-identity`; no actual user ID is
returned). It never exposes the raw Ingress path or token. The real
browser suite injects deliberately invalid `X-Ingress-Path` and a
forged browser user-ID marker. It requires Core to overwrite the Ingress
path, but **does not assume** Core strips other arbitrary user headers:
`spoofed` is recorded as a possible upstream pass-through observation,
not automatically an auth bypass. The nginx fixture strips this
untrusted value before forwarding to the Python editor, regardless of
whether Core removed it. **A successful simulated CI peer is not proof
of real Core behavior.** The real user identity header is optional;
`absent` alone is not a failure. Never trust these headers on an
unrestricted port.

## 2. Real logged-in browser session (private test machine only)

The full `/api/hassio_ingress/<opaque-token>/` URL is a bearer-like
session secret. **Do not paste it into GitHub, logs, a HAR, a screenshot
or this chat.** Create a private Playwright storage state with a normal
test-device login:

```sh
cd e2e
mkdir -p .secrets
npx playwright codegen --save-storage=.secrets/haos-state.json \
  https://YOUR-HA-ORIGIN/
```

After authenticating, close that browser and set the private environment
variables locally (do not expose their values in a CI job):

```sh
export HAOS_STORAGE_STATE=./.secrets/haos-state.json
export HAOS_INGRESS_URL='https://YOUR-HA-ORIGIN/api/hassio_ingress/OPAQUE/'
npm run test:haos
```

The regular test suite does not run `haos-real.spec.cjs`; an actual session
and explicit `test:haos` invocation are mandatory. Browser exception
handling redacts the opaque prefix, but **raw traces, screenshots and HAR
are not automatically safe**. Keep all original evidence private until
manually sanitized. The suite refuses public-origin request attempts,
asserts MIME *families* rather than exact charset equality, checks lazy Ace
assets/worker annotations and probes Supervisor header replacement.

**File mutations are disabled by default.** For HAOS-07 only, use the
explicit flag after confirming the temporary app and sandbox root:

```sh
HAOS_TEST_MUTATIONS=1 npm run test:haos
```

The mutation test also requires the fixture-only diagnostic signature before
uploading. It must never run against the normal File Editor or real HA data.

## 3. Optional HAOS-11: Supervisor-local REST and event observer WS

The default fixture has `homeassistant_api: false`, no Supervisor token in
the editor and no attempt to contact Core REST/WS. To check actual local HA
Core connectivity on a **disposable test device**, generate a *separate* app
source directory with an explicit privileged opt-in:

```sh
python scripts/prepare_haos_ingress_fixture.py \
  --output /tmp/hc_ingress_api_probe --with-ha-api-probe \
  --fixture-version 0.0.2
```

Uninstall the first fixture before replacing it with this source (both use
the same local app slug), then reload/rebuild the local app in Supervisor.
`homeassistant_api: true` grants the app administrator-level Core proxy
permissions — this is **not** a minor read-only permission. Only the probe
script is read-only; it makes `GET http://supervisor/core/api/config` and
authenticates to `ws://supervisor/core/websocket` to subscribe/unsubscribe
to one HA event type. It never invokes a mutation. The app process and nginx
inherit **no `SUPERVISOR_TOKEN`** after the one-shot probe exits.

The probe prints only `REST=ok|failed WS-auth=ok|failed
WS-subscribe=ok|failed` in local app logs. Its fixture-only
`__haos_api_probe` endpoint exposes only these fixed status enums, never
Core state data, a WS frame or credentials. Verify through the same real
authenticated browser:

```sh
HAOS_TEST_HA_API=1 npm run test:haos
```

This checks **server-side Supervisor Core REST and event WS proxy reachability**
and the existing editor's *simulated failure handling*. It does **not**
establish that the browser's optional `ws_uri` observer has authenticated to
an actual HA WS with its own appropriate user token. That separate behavior
must be inspected manually with a dedicated, short-lived test-account token,
never with the Supervisor administrator token, and without recording
credentials or received events. The editor has **no application WS server**
to route through Ingress.

## 4. HAOS-12: actual warm-cache A → B upgrade

Use the **same normal browser profile**, without clearing its cache, and
two sequential versions of the same temporary local app. To generate
test-only asset changes without modifying the repo or vendored libraries:

```sh
python scripts/prepare_haos_ingress_fixture.py \
  --output /tmp/hc-ingress-A --fixture-version 0.0.1 --cache-revision A
python scripts/prepare_haos_ingress_fixture.py \
  --output /tmp/hc-ingress-B --fixture-version 0.0.2 --cache-revision B
```

The generator adds a harmless, validated CSS comment only inside each
generated fixture. It guarantees distinct asset digests; the source files
and vendored manifest remain unchanged. Install A, open Ingress in a real
browser, switch Ace YAML/theme and record *only* the 16-hex asset fingerprint.
In the same browser/profile, update the app to B through Supervisor's local
app mechanism, reopen its new Ingress URL, and confirm:

- HTML and API responses are revalidated/no-store; the new asset digest is
  different, and its JS/CSS/fonts/worker files load with accepted MIME.
- The previously loaded A assets do not cause a stale editor, old worker
  diagnostics, or broken CSS after the B update.
- A browser reload and a new tab remain under the newly issued opaque
  prefix. Record whether Supervisor rotated the ingress token.
- No public-origin requests occur. Preserve a **private** network trace to
  inspect cache hits/misses, then share only a redacted digest/status summary.

A fresh Playwright context is **not evidence** of a warm browser cache;
the same real browser profile is mandatory for HAOS-12.

## 5. Acceptance/evidence ledger — all require actual HA OS observations

| ID | Evidence to record (never record raw session secrets) | Status |
| --- | --- | --- |
| HAOS-01 | Fixture provenance SHA, vendor manifest SHA and installed app version | pending |
| HAOS-02 | Core → Supervisor → fixture page load at opaque prefix, trailing slash behavior | pending |
| HAOS-03 | JS, CSS, icons, fonts, lazy Ace modes/themes/workers resolve inside prefix | pending |
| HAOS-04 | YAML worker error appears and clears after correcting YAML | pending |
| HAOS-05 | Authenticated `/api/prefs` response no-store, no unwanted off-origin requests | pending |
| HAOS-06 | Open-in-new-tab remains under same ingress prefix | pending |
| HAOS-07 | File upload/download only in fixture's isolated `/data` root | pending |
| HAOS-08 | Browser public-origin attempts blocked/zero during cold and warm operation | pending |
| HAOS-09 | Core-overwritten Ingress path, status-only user-header pass-through observation, nginx stripping and real peer restriction | pending |
| HAOS-10 | Browser-accepted MIME after Core/Supervisor filtering (not exact header equality) | pending |
| HAOS-11 | Optional REST and event WS proxy with credential-safe diagnostics; client WS observer & loss fallback separately observed | pending |
| HAOS-12 | Real Supervisor A→B update in same warm browser profile; digest change and no stale assets | pending |

Record HA Core, Supervisor and OS versions, browser version, UTC timestamp,
fixture SHA/manifest, each HAOS result, any unexpected status/MIME and
a nonsecret asset-suffix/digest list. Do not upload Playwright
`storageState`, raw HAR, screenshots with session URLs, internal
headers, HA entity names or admin credentials.

Only after real evidence has been reviewed should
`docs/TRACEABILITY.md` upgrade FR-005/FR-006/FR-009,
ADR-004 and AT-11. A passing public CI proves the test fixture and
simulated peer, not an actual Supervisor. Downstream inclusion in the
official File Editor remains a separate packaging decision.

## 6. Cleanup

Stop and uninstall the temporary local app; delete both test app source
directories and Playwright `.secrets` data locally when no longer needed.
Never alter or uninstall the original official File Editor.
