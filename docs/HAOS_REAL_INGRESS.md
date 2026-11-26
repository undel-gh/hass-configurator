# Actual Home Assistant OS Ingress acceptance protocol — Issue #8

**Field acceptance status (2026-11-26): HAOS-01…10 and HAOS-12 PASS in their
recorded real-device scenarios; HAOS-11 PARTIAL / DEFERRED to [#26](https://github.com/undel-gh/hass-configurator/issues/26).**
This is **11/12 scoped checks**, not complete AT-11 or full P1 release
acceptance. Live browser and network tests were performed by the operator on
an actual HA OS installation; GitHub Actions still exercises a *simulated*
Supervisor peer. The privileged Core REST/WS success path and authenticated
browser WS observer have **not** been tested. Do not interpret deferral as
an HAOS-11 PASS or an unconditional waiver.

**Real-device environment:** HA OS 18.3; Core 2026.10.1; Supervisor
2026.11.0; Frontend 20260930.3; Chrome (exact build not recorded).
**Reviewed product source:** PR #22 `8ce8ffb1cd579431261329597f7b7ce10baba4b6`.
**Source CI:** [run 45135844692](https://github.com/undel-gh/hass-configurator/actions/runs/45135844692),
4/4 jobs passed on that exact **product-code** SHA (not the real-device
test result). **Test app A:** `0.0.1` at deployment-only
`c0a7a2405bdc5a3c3a88a1d8960eeb3abcb3a729`; **B:** `0.0.2` at
`66876e42108ed7e341f3987d23983071e017e432`, using the *same*
product source; B modifies app version, fixture provenance and a harmless
CSS test comment. Vendored manifest SHA-256:
`f2f35d2c38dc9edec6846bfedded278d7b18cf714b1efbe34a49ca5b102065c1`
(460 local resources). Evidence is operator-reported and recorded in [#8](https://github.com/undel-gh/hass-configurator/issues/8);
raw browser session URLs, authenticated storage state, HAR and token-bearing
screenshots were not retained or published.

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

**Alternative field-tested installation:** before merging draft PR #22, an
isolated GitHub app repository was published as
`https://github.com/undel-gh/hass-configurator#haos-ingress-validation`.
On the test HA OS it was added via **Settings → Apps → Install app → ⋮ →
Repositories**. Supervisor built and installed A locally from the deployment
branch; the operator then used Supervisor's *in-place Update* to B. The
branch is **test deployment packaging, not the reviewed PR source branch
or a release**. No user file mounts, published host ports or
`homeassistant_api: true` were enabled.

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

## 3. Deferred HAOS-11: Supervisor-local REST and event observer WS

**Status: PARTIAL / DEFERRED to [Issue #26](https://github.com/undel-gh/hass-configurator/issues/26).**
The real HA OS browser test demonstrated that a *simulated* WebSocket
connection failure does not prevent local editing; it did **not** establish
successful real Core REST/WS connectivity or browser observer authentication.
Do not run the privileged variant on the operator's working HA OS just to
close the acceptance matrix. The following commands describe a **future**
test on an explicitly authorized, disposable HA OS environment only.

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

**Real A→B field result: PASS (2026-11-25/26).** The operator updated
`0.0.1` to `0.0.2` via Supervisor (with an app backup), retaining the
same normal Chrome profile without clearing its cache and with DevTools
`Disable cache` off. The 16-hex asset fingerprint changed, and YAML/theme,
CSS/JS/fonts, Ace worker diagnostics, new-tab and `GET api/prefs`
(`200`, `Cache-Control: no-store`) continued working. No unwanted
public-origin CDN fetches were observed; the real-HAOS Playwright suite
passed again on B after renewing its *private* authenticated browser
session. An initial Playwright HTTP 401 did not recur, but its exact cause
was not independently isolated. The test did not demonstrate binary-identical
container images or prove whether the opaque Ingress token rotated.

## 5. Real HA OS acceptance/evidence ledger — operator-reported results

| ID | Real-device result and boundary | Status |
| --- | --- | --- |
| HAOS-01 | A 0.0.1 and B 0.0.2 installed via Supervisor; source and deployment SHAs, manifest and HA OS versions recorded. Exact Chrome build not recorded. | **PASS (scope)** |
| HAOS-02 | Authenticated Core → Supervisor → editor under canonical opaque `/api/hassio_ingress/<token>/` path: HTTP 200 HTML. Without trailing slash: HTTP **404**, `redirected=false`, plain text; Core 2026.10.1 does not redirect the noncanonical path. Expected Core routing, not an editor error. | **PASS (scope)** |
| HAOS-03 | Versioned local JS/CSS/fonts/icons, Ace YAML mode, theme and lazy worker load through actual Ingress; does not establish every unused Ace mode. | **PASS (scope)** |
| HAOS-04 | On a disposable clean YAML document with `Use Worker` enabled, malformed syntax emits an Ace worker error, and correction clears it. Custom HA/ESPHome `!secret` false positives are tracked separately in [#24](https://github.com/undel-gh/hass-configurator/issues/24). | **PASS** |
| HAOS-05 | Correct iframe context; same-origin `GET api/prefs` returned HTTP 200, `text/json`, `Cache-Control: no-store`. Browser network guard rejects unwanted off-origin attempts on tested paths. | **PASS** |
| HAOS-06 | Settings → New tab opens under the same opaque Ingress prefix; real-device Playwright and manual checks. | **PASS** |
| HAOS-07 | Explicit opt-in fixture-signature-guarded upload/download of disposable text file under isolated `/data/hc-ingress-validation` matched byte-for-byte; not a large/binary stress test. | **PASS (scope)** |
| HAOS-08 | Cold/browser Playwright request guard and same-profile warm B observation revealed no unwanted public CDN-origin attempts on tested paths (browser extensions are outside app scope). | **PASS (scope)** |
| HAOS-09 | Real-HAOS client-spoofed `X-Ingress-Path` was overwritten by Core; nginx strips identity/forwarded headers before Python. Direct `curl` from an **existing Terminal & SSH (`core-ssh`)** app to fixture internal DNS `:8099/__haos_probe` returned **HTTP 403**, while Supervisor Ingress succeeded. The source peer address was not separately captured; not an exhaustive network-topology proof. Operator's Autossh config has no extra `remote_forwarding`. | **PASS (tested peer)** |
| HAOS-10 | Browser-accepted MIME families: CSS assertion and functioning scripts, fonts and worker through Supervisor response filtering; exact raw header parity across all families was not independently catalogued. | **PASS (scope)** |
| HAOS-11 | Real-browser **simulated observer WS failure fallback PASS**. Default app has `homeassistant_api: false`. Actual server-side Supervisor Core REST/event WS auth/subscribe and real browser observer authentication were **not tested**; privileged isolated HA OS work tracked in [#26](https://github.com/undel-gh/hass-configurator/issues/26). | **PARTIAL — DEFERRED #26** |
| HAOS-12 | Supervisor in-place A→B upgrade, same warm browser profile, changed 16-hex asset digest, healthy updated assets/worker/API/new tab, B Playwright regression PASS. | **PASS (operator-attested)** |

**Evidence references:** [Issue #8 field chronology](https://github.com/undel-gh/hass-configurator/issues/8)
(Playwright 4/4, opt-in upload/download, A→B warm upgrade,
canonical-slash 200/404 and Terminal & SSH direct-peer 403).
**Evidence quality:** real-device observations were reported by the operator;
the public CI does not independently replay their authenticated session.
No session tokens, full Ingress URLs, Supervisor credentials, raw HAR, or
unredacted local Playwright reports should be checked in or posted.

Retain date/versions/source and both fixture SHAs with each acceptance
record. Distinguish **the already verified Core-to-Supervisor Ingress
boundary** from the **unverified privileged Core REST/WS API integration**
in FR-005/006/009, ADR-004 and AT-11. AT-11 overall remains **PARTIAL**,
and P1 release acceptance is **not** implied. An explicitly owned
deferral to #26 is not a proof of successful HAOS-11. Do not install the
privileged probe in the working HA OS; downstream inclusion in the official
File Editor is a separate packaging decision.

## CSP regression after #13 (not part of the historical #8 PASS)

Use a disposable fixture built from the reviewed #13 source SHA, with the default `homeassistant_api: false`. Re-run the `test:haos` suite including the new CSP test; also open the app from the actual HA sidebar iframe and in a new tab (direct navigation alone cannot prove `frame-ancestors` compatibility). Repeat local asset/worker, file roundtrip and warm-profile A→B checks. Record only PASS/FAIL, versions and SHAs; no raw policy, nonce, opaque URL or unredacted browser reports. A configured live observer remains #26; the standalone fixture must reject browser-supplied WS URLs without disrupting editing. See [P1 CSP](P1_CSP.md). Until performed, CSP real-HAOS acceptance is NOT VERIFIED.

## 6. Cleanup

Stop and uninstall the temporary local app; delete both test app source
directories and Playwright `.secrets` data locally when no longer needed.
Never alter or uninstall the original official File Editor.
