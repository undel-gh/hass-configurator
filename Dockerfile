# Fork-built offline editor image. All browser runtime assets come from THIS
# checkout; never install the unrelated published PyPI hass-configurator.
# Supply an immutable digest-pinned PYTHON_BASE for a release build (P0 #5).
ARG PYTHON_BASE=python:3.11-slim-bookworm
FROM ${PYTHON_BASE} AS wheel-builder
WORKDIR /src
COPY setup.py MANIFEST.in ./
COPY hass_configurator/ hass_configurator/
RUN python -m pip wheel --no-deps --wheel-dir /wheelhouse .

FROM ${PYTHON_BASE}
LABEL org.opencontainers.image.source="https://github.com/undel-gh/hass-configurator"
RUN apt-get update && apt-get install -y --no-install-recommends \
    git openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=wheel-builder /wheelhouse/ /wheelhouse/
# All Python installs occur when BUILDING the image. Runtime does not
# execute pip, npm, curl or fetch the offline UI assets.
RUN python -m pip install --no-cache-dir /wheelhouse/hass_configurator-*.whl \
    && rm -rf /wheelhouse
EXPOSE 3218
VOLUME /config
WORKDIR /config
ENV HC_GIT=false HC_BASEPATH=/config HC_ENFORCE_BASEPATH=true
ENTRYPOINT ["hass-configurator"]
CMD ["--standalone", "--listen", "0.0.0.0", "--port", "3218", "--basepath", "/config", "--enforce"]
