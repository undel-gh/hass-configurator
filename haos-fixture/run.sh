#!/bin/sh
set -eu
umask 077

# No /config, /share, /media or host Docker socket is mounted.
test_root=/data/hc-ingress-validation
mkdir -p "$test_root"
chown configurator-e2e:configurator-e2e "$test_root"

# Drop application privileges; it can edit only its own temporary /data folder.
runuser -u configurator-e2e -- \
  python -m hass_configurator.configurator \
    --standalone --basepath "$test_root" --enforce \
    --listen 127.0.0.1 --port 3218 &
app_pid=$!

stop() {
  kill "$app_pid" 2>/dev/null || true
}
trap stop EXIT TERM INT

# The external port accepts only the Supervisor bridge peer.
nginx -c /etc/nginx/nginx.conf -g 'daemon off;' &
nginx_pid=$!
wait "$nginx_pid"
