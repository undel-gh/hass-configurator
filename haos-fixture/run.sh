#!/bin/sh
set -eu
umask 077

# No /config, /share, /media or host Docker socket is mounted.
test_root=/data/hc-ingress-validation
mkdir -p "$test_root"
# Supervisor's /data is commonly root-only (0700); allow traversal without
# allowing users to enumerate or modify other app data.
chmod 0711 /data
chown configurator-e2e:configurator-e2e "$test_root"
chmod 0700 "$test_root"

# setpriv execs Python itself: app_pid is the service PID, not a runuser
# wrapper. SIGTERM/exit can therefore reap the actual application process.
setpriv --reuid=configurator-e2e --regid=configurator-e2e --init-groups -- \
  python -m hass_configurator.configurator \
    --standalone --basepath "$test_root" --enforce \
    --listen 127.0.0.1 --port 3218 &
app_pid=$!

stop() {
  trap - EXIT TERM INT
  kill "$app_pid" 2>/dev/null || true
  wait "$app_pid" 2>/dev/null || true
}
trap stop EXIT TERM INT

# The external port accepts only the Supervisor bridge peer.
nginx -c /etc/nginx/nginx.conf -g 'daemon off;' &
nginx_pid=$!
wait "$nginx_pid"
