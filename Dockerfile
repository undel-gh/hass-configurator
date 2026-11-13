# syntax=docker/dockerfile:1
# Release default is the verified official *multiarch index* digest from
# GitHub Actions run #172 (2026-11-13), not a mutable tag.
# This non-slim bookworm image already contains git, OpenSSH and CA trust,
# eliminating mutable apt repositories from the fork's own Docker build.
# Its larger size is a deliberate repeatability tradeoff; see #5/#9.
ARG PYTHON_BASE=docker.io/library/python:3.11.18-bookworm@sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6
ARG SOURCE_DATE_EPOCH=1704067200

FROM ${PYTHON_BASE} AS dependency-wheelhouse
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

FROM ${PYTHON_BASE} AS fork-wheel-builder
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

FROM ${PYTHON_BASE}
ARG SOURCE_DATE_EPOCH
LABEL org.opencontainers.image.source="https://github.com/undel-gh/hass-configurator"
LABEL org.opencontainers.image.base.name="docker.io/library/python:3.11.18-bookworm"
LABEL org.opencontainers.image.base.digest="sha256:726d304906fa5eb468e5531e366548d1903286352f5adb54ef508ac01fbd80c6"
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} PYTHONDONTWRITEBYTECODE=1 PIP_NO_INDEX=1
COPY --from=dependency-wheelhouse /locked-wheels/ /opt/hc-locked-wheels/
COPY --from=fork-wheel-builder /fork-wheel/ /opt/hc-fork-wheel/
COPY requirements/docker-runtime.lock /usr/local/share/hass-configurator/runtime.lock
COPY requirements/normalize_mtimes.py /tmp/normalize_mtimes.py
# Install the five reviewed third-party wheels from an OFFLINE wheelhouse,
# re-checking their hashes. Install only THIS fork's locally built wheel.
# No external Python/OS package repository is contacted in final stage.
RUN python -m pip install --disable-pip-version-check --no-index --no-compile \
      --find-links=/opt/hc-locked-wheels --require-hashes \
      -r /usr/local/share/hass-configurator/runtime.lock \
    && python -m pip install --disable-pip-version-check --no-index \
      --no-compile --no-deps /opt/hc-fork-wheel/hass_configurator-*.whl \
    && python -m pip check \
    && git --version && ssh -V \
    && rm -rf /opt/hc-locked-wheels /opt/hc-fork-wheel \
    && python /tmp/normalize_mtimes.py --epoch "$SOURCE_DATE_EPOCH" \
         --installed /usr/local/share/hass-configurator/runtime.lock \
    && rm -f /tmp/normalize_mtimes.py

EXPOSE 3218
VOLUME /config
WORKDIR /config
ENV HC_GIT=false HC_BASEPATH=/config HC_ENFORCE_BASEPATH=true
ENTRYPOINT ["hass-configurator"]
CMD ["--standalone", "--listen", "0.0.0.0", "--port", "3218", "--basepath", "/config", "--enforce"]
