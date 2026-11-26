# Temporary HA OS Ingress and CSP validation app (Issues #8 / #13)

**TEST ONLY. Not a production replacement for the official File Editor.**

Fixture 0.0.4 (CSP-B) is pinned to [PR #30](https://github.com/undel-gh/hass-configurator/pull/30) source commit `bbab9cc7051c1a90db256ffbb30a06360f3226fc` ([exact source CI 4/4](https://github.com/undel-gh/hass-configurator/actions/runs/45848462928)). The copied package differs from the source only by a harmless CSS cache revision comment. No Core API privilege, host ports, configuration or shared-directory mounts; editing is confined to `/data/hc-ingress-validation`.

Install/update manually through Home Assistant Settings → Apps → Install app → Repositories:
`https://github.com/undel-gh/hass-configurator#haos-ingress-validation`

Use an isolated test installation, make a backup, keep the same slug, and use Supervisor Update (not uninstall/reinstall) for the A→B warm-cache test. Keep the same normal browser profile, do not clear cache, and keep DevTools Disable cache off. Do not enable Home Assistant API or other privileges. Supervisor builds locally; no prebuilt image or release is published.

Follow the [real HA OS runbook](https://github.com/undel-gh/hass-configurator/blob/bbab9cc7051c1a90db256ffbb30a06360f3226fc/docs/HAOS_REAL_INGRESS.md) and [CSP policy](https://github.com/undel-gh/hass-configurator/blob/bbab9cc7051c1a90db256ffbb30a06360f3226fc/docs/P1_CSP.md). Never share ingress URLs, cookies, tokens, raw HAR, or private Playwright state/reports.

See `hc_ingress_validation/fixture-provenance.json` for the source and vendor manifest identity. Issue #13 remains open; PR #30 remains Draft / HOLD pending real HAOS and inline-style disposition. Issue #26 is out of scope. Installation is controlled by the administrator.
