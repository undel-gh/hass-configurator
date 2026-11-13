# Offline Revival Roadmap

Status: proposed, 2026-11-13. Baseline: `master`; `offline` branch is historical prototype (2 commits ahead / 87 behind).

## Mission
Make HASS Configurator usable from a clean, uncached browser without external Internet, while preserving existing file-editing functionality. The upstream issue is https://github.com/home-assistant/apps/issues/2811. This Python application and the official HA OS File Editor add-on are separate codebases and release tracks.

## P0 — functional offline MVP
1. [#1](https://github.com/undel-gh/hass-configurator/issues/1) Inventory runtime requests: CDN CSS/JS/fonts, images, CSS imports, Ace dynamic modes/themes/workers. Produce pinned asset manifest.
2. [#2](https://github.com/undel-gh/hass-configurator/issues/2) Specify the request/base-URL contract (HTML, assets, API, redirects, new tabs, WebSocket and trusted proxy behavior), implement safe package-based static routing, and introduce an initial cold-cache network-denial smoke test alongside the router.
3. [#3](https://github.com/undel-gh/hass-configurator/issues/3) Vendor Ace 1.9.6-compatible core, language tools, themes, modes and workers; configure runtime paths.
4. [#4](https://github.com/undel-gh/hass-configurator/issues/4) Vendor Materialize CSS, MDI and associated fonts; remove mandatory external images and other runtime assets.
5. [#5](https://github.com/undel-gh/hass-configurator/issues/5) Package static files in wheel/sdist and fork-built container, pin and audit dependencies, and make package/runtime version metadata consistent (currently `setup.py` 0.6.0 vs packaged application 0.7.0).
6. [#6](https://github.com/undel-gh/hass-configurator/issues/6) Expand the smoke introduced with #2 into full cold-cache E2E and HTTP release gates; grow scenario coverage incrementally with #3–#5.

**P0 exit:** on a cold browser with Internet blocked, layout, icons, file open/edit/save, YAML diagnostics, Ace themes/modes, worker scripts and dialogs work at root and a **simulated ingress prefix**. Any browser attempt to fetch a public external origin during supported scenarios fails the gate, even if the UI recovers using cached/local fallback. Only explicitly user-opened external documentation and approved internal HA REST/WS are exceptions; tests must record those exceptions.

## P1 — release candidate
7. [#7](https://github.com/undel-gh/hass-configurator/issues/7) Secure privileged API: file roots, symlinks, Git, command execution, authentication, tokens, CSRF, ingress/proxy behavior.
8. [#8](https://github.com/undel-gh/hass-configurator/issues/8) HA OS and File Editor interoperability smoke matrix. Verify internal LAN HA REST/WS optional behavior; no editor failure when HA unavailable.
9. [#9](https://github.com/undel-gh/hass-configurator/issues/9) Licenses, SBOM, dependency/security inventory and reproducible vendored asset updates.
10. [#10](https://github.com/undel-gh/hass-configurator/issues/10) Installation, validation, compatibility, troubleshooting, release and rollback documentation.

**P1 exit:** validate against **real Home Assistant Ingress in an add-on environment** (not just simulated prefix), alongside stable offline E2E/HTTP/HA OS smoke, no known high severity release blockers, license compliance and reproducible artifacts. Integration into official HA add-on requires its own PR and maintainers' acceptance.

## P2 — maintainability
11. [#11](https://github.com/undel-gh/hass-configurator/issues/11) Break up monolithic frontend and Python request handler incrementally; retain offline gate.

## Sequence
Inventory → **Ingress URL contract + minimal network-denial smoke with router** → Ace and CSS/fonts in parallel (extend smoke per feature) → packaging (verify artifact and version) → comprehensive E2E gate → real HA Ingress/security/docs → release candidate → modular refactor. Never wholesale-merge old `offline` branch. Avoid massive dependency upgrades during P0 except where required for security or compatibility.

## Risks and decisions
- Ace lazily fetches modules, themes and workers; copying three top-level files is insufficient.
- Materialize/MDI stylesheets can fetch additional fonts; audit CSS `url()`.
- Ingress prefixes and caching can conceal broken offline runtime resources.
- Legacy server handles powerful filesystem/command/Git functions; minimize privileges.
- Any attempted browser fetch to a public external origin during supported scenarios is a failure, including nonblocking CDN fallbacks; deliberate user-initiated external documentation navigation is excluded.
