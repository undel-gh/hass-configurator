# Temporary HA OS Ingress validation app (Issue #8)

**TEST-ONLY, not the official File Editor. Do not install as a production replacement.**

Pinned from [PR #22](https://github.com/undel-gh/hass-configurator/pull/22), source commit `8ce8ffb1cd579431261329597f7b7ce10baba4b6` (exact-HEAD [CI run](https://github.com/undel-gh/hass-configurator/actions/runs/45135844692) green). The app uses only `/data/hc-ingress-validation`; no real HA configuration, shared directories, supervisor admin API access, or published host port. It starts manually and is accessible exclusively through Supervisor Ingress.

## Install on Home Assistant OS

1. Make a Home Assistant backup and confirm the OS architecture is **amd64** or **aarch64**.
2. Settings → Apps → Install app → menu **⋮** → **Repositories** → **Add**:
   `https://github.com/undel-gh/hass-configurator#haos-ingress-validation`
3. Open **HASS Configurator Ingress Validation (temporary)** from the new repository section and choose **Install**. Supervisor builds this disposable Docker image on the HA OS device; **no prebuilt GHCR image is published**.
4. Start manually; open **Open Web UI**. Inspect the app logs if the build/start fails. Do **not** enable homeassistant_api or change mounts/privileges.
5. Follow the acceptance [runbook](https://github.com/undel-gh/hass-configurator/blob/8ce8ffb1cd579431261329597f7b7ce10baba4b6/docs/HAOS_REAL_INGRESS.md). Never share opaque ingress URLs, cookie or token, Playwright storageState, HAR, or unredacted traces.
6. When testing is complete, stop/uninstall the app and remove this custom repository if no longer needed. This repository is **not** a replacement for the official File Editor.

## Evidence

See `hc_ingress_validation/fixture-provenance.json` for source SHA and vendor manifest SHA-256. Issue #8 remains **open** until real HAOS-01…12 evidence; PR #22 stays **Draft**.

Installation is initiated and controlled by the Home Assistant administrator. Nothing in this branch installs software automatically.
