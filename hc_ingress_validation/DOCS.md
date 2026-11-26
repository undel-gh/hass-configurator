# Temporary CSP test app 0.0.3 (CSP-A)

Test only; not the official File Editor. Source: `bbab9cc7051c1a90db256ffbb30a06360f3226fc` (PR #30). No Core API privilege, host ports or shared mounts. Only `/data/hc-ingress-validation` is editable.

Use the [real HA OS runbook](https://github.com/undel-gh/hass-configurator/blob/bbab9cc7051c1a90db256ffbb30a06360f3226fc/docs/HAOS_REAL_INGRESS.md) and [CSP policy](https://github.com/undel-gh/hass-configurator/blob/bbab9cc7051c1a90db256ffbb30a06360f3226fc/docs/P1_CSP.md). Keep the same browser profile/cache during A→B Supervisor Update. Never share session secrets or raw traces. Stop/uninstall the temporary app after testing.
