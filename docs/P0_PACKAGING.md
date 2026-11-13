# P0 packaged-runtime checks (#5, #6, #14)

This document covers only automatically reproducible P0 checks. **It is not
approval to expose the editor publicly, replace the official File Editor, or
close P1 real Supervisor Ingress/security/license acceptance.**

## Single version authority

`hass_configurator/_version.py` contains the fork's current VERSION.
`setup.py` reads it as text when building distribution metadata, without
importing runtime dependencies. `configurator.py` imports it. The UI
About dialog shows it; the read-only `GET /api/version` endpoint returns
`{"version":"..."}`, with `Cache-Control: no-store`. CI tests equality
between the installed metadata, Python runtime, API and UI.

The new endpoint is **not** a substitute for authentication: when configured,
the existing Basic Auth handler also protects it. No credentials are included
in the response.

## Building and validating this fork

From a clean checkout of the reviewed commit:

```sh
python -m pip wheel --no-deps -w /tmp/hc-wheel .
python setup.py sdist --dist-dir /tmp/hc-sdist
python scripts/check_offline_artifacts.py /tmp/hc-wheel /tmp/hc-sdist
docker build -t hc-fork:p0 .
```

The main Dockerfile now builds a wheel from *this repository* in a build
stage and installs that wheel, never the unrelated public PyPI package.
The image's default is standalone mode, confined to `/config` when
`--enforce` is supplied, on internal port 3218. Bind only loopback when
testing outside HA OS:

```sh
mkdir -p /tmp/hc-editor-disposable
docker run --rm -p 127.0.0.1:3218:3218 \
  -v /tmp/hc-editor-disposable:/config hc-fork:p0
```

The container does not run npm/pip downloads **at runtime**; CI boots it
with `--network none` and verifies that the local API responds and its
packaged resource fingerprint matches source. It also runs Chromium
against the actual published container port, including an isolated
file-edit round trip.

Wheel/sdist installation is tested separately in isolated venvs, outside
the source checkout; CI prints installed site-packages import origins.
Both distributions validate all 460 vendor and six first-party resources,
plus the shared version file and distribution metadata. The asset version
continues to be a content-derived digest, not the software release string.

## Reproducibility boundary

The **asset/payload and fork origin** are verified automatically, but
byte-for-byte repeatable Docker image builds across time are **not yet
claimed**: the default Python base image tag and transitive Python package
dependencies are not fully digest/hash locked. Before any release, pass
an approved immutable base image reference:

```sh
docker build --build-arg PYTHON_BASE='python:3.11-slim-bookworm@sha256:REVIEWED_DIGEST' \
  -t hc-fork:release .
```

Replace `REVIEWED_DIGEST` with a *verified published digest*; it is
intentionally not invented here. Full image dependency freezing and
license/SBOM audit remain #5/#9 release work, not implied by a passing P0
smoke. Likewise the old `python_requires='>=3'` metadata does not establish
compatibility with every future Python major version.

## Negative controls and release gates

`tests/test_p0_failure_gates.py` intentionally injects a remote script and
removes first-party/vendor assets in isolated fixtures. The tests pass only
if strict offline inventory rejects the injected script and startup rejects
the missing assets. Existing E2E tests exercise actual cold-cache attempts,
YAML workers, simulated Ingress GET/POST, and root/prefix warm A→B updates.

The real HA OS Supervisor session and browser-visible proxy behavior,
unsafe privileged API operations, CSP, and supply-chain certification are
**P1** and need independent evidence (issues #7/#8/#9/#13). CI's temporary
HAOS fixture checks are NOT real Supervisor ingress validation.
