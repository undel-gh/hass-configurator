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
Both distributions validate all 460 vendor assets plus seven first-party
resources (**the six asset routes and the complete `dev.html` UI page**),
plus the shared version file and distribution metadata. The archive verifier
also rejects a removed or modified `dev.html` (negative tests). The asset version
continues to be a content-derived digest, not the software release string.

## Reproducible Docker release build (P0 #5)

The default Docker base is now the **verified official digest**, not a mutable
`python:3.11-slim-bookworm` tag:

```
docker.io/library/python:3.11.18-bookworm@sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6
```

This is the multi-platform OCI index (checked against the official registry
in CI; the Linux amd64 manifest was also independently inspected). The **tested
release target is linux/amd64**. The full non-slim image includes Git,
OpenSSH and CA certificates, verified with a network-disabled container, so
the fork Dockerfile performs **no apt operations**. The tradeoff is a larger
base image and greater preinstalled OS-package surface than the slim build.
The base's complete filesystem, including OS package versions and bundled
Python build tools, is fixed by the digest. Refresh that digest deliberately
after security/compatibility review; do not rely on a mutable tag.

All direct and transitive Python runtime dependencies are fixed by
`requirements/docker-runtime.lock` with one **exact version and SHA-256
of a py3-none-any wheel per distribution**: PyOTP 2.10.0, GitPython 3.2.1,
legacy-cgi 2.6.4, gitdb 4.0.12 and smmap 5.0.3. They were resolved and
independently hashed in CI #172; `scripts/check_docker_runtime_lock.py`
checks their identity, closure and exact downloaded wheel bytes. A new
dependency in `setup.py` without an explicit lock entry fails CI.

The image build has three stages:

1. `dependency-wheelhouse` downloads **only** permitted binary wheels,
   with `pip download --require-hashes`. This is the only package-index
   access in the Dockerfile.
2. `fork-wheel-builder` builds the fork wheel **offline** with
   `--no-index --no-build-isolation --no-deps`, using a fixed
   `SOURCE_DATE_EPOCH` so wheel member dates cannot drift.
3. The runtime image installs only local wheels with
   `--no-index --require-hashes`, then installs the fork wheel with
   `--no-deps` and runs `pip check`. Both wheel directories enter the
   runtime stage as **read-only BuildKit bind mounts**, not COPY layers.
   Consequently there are no temporary wheel files to remove and no
   nondeterministic whiteout entries. The reviewed lock remains under
   `/usr/local/share/hass-configurator/`.
   No pip/npm/apt updates are attempted at runtime.

To reproduce the CI build with a given Git commit, check out that exact
commit and use the same epoch and platform:

```sh
export DOCKER_BUILDKIT=1
export SOURCE_DATE_EPOCH="$(git log -1 --format=%ct)"
docker buildx build --no-cache --platform linux/amd64 \
  --output type=docker,rewrite-timestamp=true \
  --build-arg SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
  -t hc-fork:build-a .
docker buildx build --no-cache --platform linux/amd64 \
  --output type=docker,rewrite-timestamp=true \
  --build-arg SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
  -t hc-fork:build-b .
docker image inspect --format '{{.Id}}' hc-fork:build-a
docker image inspect --format '{{.Id}}' hc-fork:build-b
```

The BuildKit exporter flag `rewrite-timestamp=true` is **mandatory**:
`SOURCE_DATE_EPOCH` alone sets image/config timestamps but does not rewrite
the filesystem timestamps in exported image layers. The offline wheel and
installed-file normalizer handles artifacts at their creation point, and the
exporter normalizes the final layer metadata. CI additionally normalizes
runtime parent directories; a prior proof showed the wheel **bytes** already
matched while directory and deletion-whiteout timestamps differed. Omitting
the exporter flag
will produce different image IDs even with identical wheel payloads.

The CI gate **fails** if two independent, cache-disabled builds differ in
their local image IDs. This is a stronger repeatability check than comparing
only the `assets/v<digest>/` namespace. For release provenance also retain
the tested Git SHA, `SOURCE_DATE_EPOCH`, exact image ID, base digest, lock,
architecture and CI log. Avoid claiming identical pushed registry digest
or cross-architecture bit-for-bit reproduction based on a local image ID
check alone; registry manifest compression and attestations can differ.

To update dependencies, choose reviewed versions, obtain binary wheels from
the official index, compute and verify each SHA-256, regenerate the **complete**
lock, and run the negative lock tests plus all wheel/sdist/Docker E2E tests.
Never use `pip freeze` from an arbitrary developer environment as release
provenance. A reviewed update of the official base digest is an explicit
security update even when the application files are unchanged.

The comprehensive third-party license, vulnerability, attestation and SBOM
audit remains **P1 #9**. A successful build is not a security clearance;
P1 #7/#13 still protect privileged routes, filesystem operations and CSP.

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
