# Temporary test app — read before installing

This test-only build isolates all editor access to `/data/hc-ingress-validation`, publishes no host port, and has **no** Home Assistant API permission. It is not the official File Editor. This build is pinned to source commit `8ce8ffb1cd579431261329597f7b7ce10baba4b6`.

The admin must create a backup, install manually, inspect logs, then follow the [real HA OS validation protocol](https://github.com/undel-gh/hass-configurator/blob/8ce8ffb1cd579431261329597f7b7ce10baba4b6/docs/HAOS_REAL_INGRESS.md). No credentials, unredacted HAR, or opaque ingress URLs may be shared. To remove, stop/uninstall the temporary app and remove its repository.
