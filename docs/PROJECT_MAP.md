# Project Map

Status: based on `master` tree inspected 2026-11-13.

| Path | Responsibility | Offline work |
| --- | --- | --- |
| `hass_configurator/configurator.py` | HTTP routes, HA API access, file/Git/exec actions, template rendering | Asset service, security tests, ingress handling |
| `hass_configurator/dev.html` | Combined HTML and JS | Remove CDN tags, configure Ace asset URLs |
| `hass_configurator/style.css` | Core styles/theming | Audit imports and asset URLs |
| `hass_configurator/jquery-3.6.0.min.js` | Local jQuery | Keep pinned, audit |
| `hass_configurator/js-yaml.min.js` | Local lint parser | Validate supported YAML tags |
| `hass_configurator/materialize.min.js` | UI JS library | Pair with local compatible CSS |
| `hass_configurator/material-icons.fallback.css` | Local Material Icons | Validate font path and MIME |
| `hass_configurator/*.woff2` | Local font | Verify packaging |
| `hass_configurator/static/` (planned) | Vendor JS/CSS/fonts | Ace, modes, themes, workers, Materialize CSS, MDI |
| `MANIFEST.in`, `setup.py` | Python distribution | Include assets/licenses, synchronize package (0.6.0 today) and runtime (0.7.0 today) versions, validate artifacts |
| `Dockerfile` | Standalone container | Build/install code from this fork |
| `configurator.py`, `dev.html` (root) | Historical parallel entry points | Audit callers before deletion |
| `settings.conf`, `start.sh` | Runtime setup | Config/permissions checks |
| `.travis.yml` | Legacy CI | Add modern offline network-denial CI |
| `tests/` (planned) | HTTP/API tests | MIME, traversal, error handling, auth |
| `e2e/` (planned) | Browser tests | Early network-denial smoke with #2; grow #3–#5; P0 simulated ingress / P1 real HA Ingress |
| `docs/` | Project design | This map, roadmap, spec, architecture |

## Issue map
- P0 foundation: [#1](https://github.com/undel-gh/hass-configurator/issues/1) inventory, [#2](https://github.com/undel-gh/hass-configurator/issues/2) static router.
- P0 frontend: [#3](https://github.com/undel-gh/hass-configurator/issues/3) Ace, [#4](https://github.com/undel-gh/hass-configurator/issues/4) CSS/icons/fonts.
- P0 release pipeline: [#5](https://github.com/undel-gh/hass-configurator/issues/5) packaging, [#6](https://github.com/undel-gh/hass-configurator/issues/6) E2E.
- P1 quality: [#7](https://github.com/undel-gh/hass-configurator/issues/7) security, [#8](https://github.com/undel-gh/hass-configurator/issues/8) HA compatibility, [#9](https://github.com/undel-gh/hass-configurator/issues/9) supply chain, [#10](https://github.com/undel-gh/hass-configurator/issues/10) docs.
- P2 architecture: [#11](https://github.com/undel-gh/hass-configurator/issues/11) modular refactor.

## Cross-cutting acceptance
All browser-initiated public-origin fetch attempts fail tests during supported scenarios, even if nonblocking; only explicit external documentation navigation and approved internal HA REST/WS are exceptions. Implement the documented URL/base-path contract for assets, API calls, redirects, new tabs, and WebSocket URLs. P0 uses a simulated ingress prefix, P1 uses a real Home Assistant Ingress/add-on installation.

## Delivery branches
Base all work on `master`; use narrowly scoped feature branches and PRs. The original `offline` branch is 2 ahead/87 behind the upstream `master` and must not be merged wholesale. Preserve existing app behavior and incrementally make offline E2E mandatory.

## Links
- https://github.com/undel-gh/hass-configurator
- https://github.com/danielperna84/hass-configurator/tree/offline
- https://github.com/home-assistant/apps/issues/2811
