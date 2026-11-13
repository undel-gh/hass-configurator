# syntax=docker/dockerfile:1
# Release default is the verified official *multiarch index* digest from
# GitHub Actions run #172 (2026-11-13), not a mutable tag.
# This non-slim bookworm image already contains git, OpenSSH and CA trust,
# eliminating mutable apt repositories from the fork's own Docker build.
# Its larger size is a deliberate repeatability tradeoff; see #5/#9.
# Base is deliberately not an ARG: permitting a different FROM would
# invalidate the fixed OCI base provenance labels and image security review.
ARG SOURCE_DATE_EPOCH=1704067200

FROM docker.io/library/python:3.11.18-bookworm@sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6 AS dependency-wheelhouse
ARG SOURCE_DATE_EPOCH
WORKDIR /lock
COPY requirements/docker-runtime.lock ./runtime.lock
COPY requirements/normalize_mtimes.py /tmp/normalize_mtimes.py
# Fetch is permitted ONLY here, with a complete version/hash-locked list.
# Every wheel is byte-checked by pip; no sdist or arbitrary resolver upgrades.
RUN python -m pip download --disable-pip-version-check --no-cache-dir \
    --only-binary=:all: --require-hashes -r runtime.lock -d /locked-wheels \
    && python /tmp/normalize_mtimes.py --epoch "$SOURCE_DATE_EPOCH" \
         --tree /locked-wheels

FROM docker.io/library/python:3.11.18-bookworm@sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6 AS fork-wheel-builder
ARG SOURCE_DATE_EPOCH
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} PYTHONDONTWRITEBYTECODE=1
WORKDIR /src
COPY setup.py MANIFEST.in ./
COPY hass_configurator/ hass_configurator/
COPY requirements/normalize_mtimes.py /tmp/normalize_mtimes.py
# The official digest-pinned base already contains the wheel build toolchain.
# No build-isolation/PEP517 package fetch, no external dependencies.
RUN python -m pip wheel --disable-pip-version-check --no-index \
    --no-build-isolation --no-deps --wheel-dir /fork-wheel . \
    && python /tmp/normalize_mtimes.py --epoch "$SOURCE_DATE_EPOCH" \
         --tree /fork-wheel

FROM docker.io/library/python:3.11.18-bookworm@sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6
ARG SOURCE_DATE_EPOCH
LABEL org.opencontainers.image.source="https://github.com/undel-gh/hass-configurator"
LABEL org.opencontainers.image.base.name="docker.io/library/python:3.11.18-bookworm"
LABEL org.opencontainers.image.base.digest="sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6"
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} PYTHONDONTWRITEBYTECODE=1 PIP_NO_INDEX=1
# Read-only BuildKit mounts avoid adding then deleting wheelhouses in image
# layers. COPY+rm produced variable directory/whiteout timestamps even with
# identical wheel SHA-256s and SOURCE_DATE_EPOCH.
# No runtime-stage package-index, apt, npm or public network request.
RUN --mount=type=bind,from=dependency-wheelhouse,source=/locked-wheels,target=/mnt/locked-wheels,readonly \
    --mount=type=bind,from=fork-wheel-builder,source=/fork-wheel,target=/mnt/fork-wheel,readonly \
    --mount=type=bind,source=requirements/docker-runtime.lock,target=/tmp/docker-runtime.lock,readonly \
    --mount=type=bind,source=requirements/normalize_mtimes.py,target=/tmp/normalize_mtimes.py,readonly \
    mkdir -p /usr/local/share/hass-configurator \
    && cp /tmp/docker-runtime.lock /usr/local/share/hass-configurator/runtime.lock \
    && python -m pip install --disable-pip-version-check --no-index --no-compile \
      --find-links=/mnt/locked-wheels --require-hashes \
      -r /usr/local/share/hass-configurator/runtime.lock \
    && python -m pip install --disable-pip-version-check --no-index \
      --no-compile --no-deps /mnt/fork-wheel/hass_configurator-*.whl \
    && python -m pip check \
    && git --version && ssh -V \
    && python /tmp/normalize_mtimes.py --epoch "$SOURCE_DATE_EPOCH" \
      --installed /usr/local/share/hass-configurator/runtime.lock \
    && touch -d "@$SOURCE_DATE_EPOCH" \
      /etc /opt /tmp /usr/local/share /usr/local/share/hass-configurator \
      /usr/local/share/hass-configurator/runtime.lock

# Never run the network-facing editor as root by default. A host bind
# mount at /config must be writable by UID/GID 10001; see P1_API_SECURITY.md.
RUN groupadd --gid 10001 configurator \
    && useradd --uid 10001 --gid 10001 --no-create-home \
       --home-dir /config --shell /usr/sbin/nologin configurator \
    && mkdir -p /config \
    && chown 10001:10001 /config \
    # useradd/groupadd touch passwd/group/shadow and parent directories
    # with wall-clock timestamps. Normalize exactly those layer entries
    # to preserve the two independent no-cache image-ID P0 check.
    && touch -d "@$SOURCE_DATE_EPOCH" \
       /config /etc /etc/passwd /etc/group /etc/shadow /etc/gshadow \
       /etc/subuid /etc/subgid
EXPOSE 3218
VOLUME /config
WORKDIR /config
USER 10001:10001
ENV HC_GIT=false HC_BASEPATH=/config HC_ENFORCE_BASEPATH=true
ENTRYPOINT ["hass-configurator"]
CMD ["--standalone", "--listen", "0.0.0.0", "--port", "3218", "--basepath", "/config", "--enforce"]
