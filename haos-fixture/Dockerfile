# Testing only. Built by Supervisor from this fork's copied checkout.
# Not a released or reproducible Docker artifact; #5 owns production images.
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install --no-install-recommends -y \
    nginx util-linux ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 11001 --home-dir /nonexistent \
       --shell /usr/sbin/nologin configurator-e2e

COPY app/ /opt/hass-configurator/
RUN python -m pip install --no-cache-dir /opt/hass-configurator/ \
    && rm -rf /opt/hass-configurator/

COPY nginx.conf /etc/nginx/nginx.conf
COPY run.sh /run.sh
RUN chmod 0755 /run.sh

EXPOSE 8099
CMD ["/run.sh"]
