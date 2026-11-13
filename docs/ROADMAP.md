# Offline Revival Roadmap

Status: proposed, 2026-11-13. Baseline: `master`; `offline` branch is historical prototype (2 commits ahead / 87 behind).

## Mission
Make HASS Configurator usable from a clean, uncached browser without external Internet, while preserving existing file-editing functionality. The upstream issue is https://github.com/home-assistant/apps/issues/2811. This Python application and the official HA OS File Editor add-on are separate codebases and release tracks.

## P0 — functional offline MVP
1. [#1](https://github.com/undel-gh/hass-configurator/issues/1) Inventory runtime requests: CDN CSS/JS/fonts, images, CSS imports, Ace dynamic modes/themes/workers. Produce pinned asset manifest.
2. [#2](https://github.com/undel-gh/hass-configurator/issues/2) Implement safe package-based static router and ingress-safe relative asset URLs.
3. [#3](https://github.com/undel-gh/hass-configurator/issues/3) Vendor Ace 1.9.6-compatible core, language tools, themes, modes and workers; configure runtime paths.
4. [#4](https://github.com/undel-gh/hass-configurator/issues/4) Vendor Materialize CSS, MDI and associated fonts; remove mandatory external images and other runtime assets.
5. [#5](https://github.com/undel-gh/hass-configurator/issues/5) Package static files in wheel/sdist and fork-built container, pinned and license-reviewed.
6. [#6](https://github.com/undel-gh/hass-configurator/issues/6) Implement cold-cache network-denial E2E gate and HTTP tests.

**P0 exit:** on a cold browser with Internet blocked, layout, icons, file open/edit/save, YAML diagnostics, Ace themes/modes, worker scripts and dialogs work. No mandatory request to external origin. Works at root and simulated ingress prefix.

## P1 — release candidate
7. [#7](https://github.com/undel-gh/hass-configurator/issues/7) Secure privileged API: file roots, symlinks, Git, command execution, authentication, tokens, CSRF, ingress/proxy behavior.
8. [#8](https://github.com/undel-gh/hass-configurator/issues/8) HA OS and File Editor interoperability smoke matrix. Verify internal LAN HA REST/WS optional behavior; no editor failure when HA unavailable.
9. [#9](https://github.com/undel-gh/hass-configurator/issues/9) Licenses, SBOM, dependency/security inventory and reproducible vendored asset updates.
10. [#10](https://github.com/undel-gh/hass-configurator/issues/10) Installation, validation, compatibility, troubleshooting, release and rollback documentation.

**P1 exit:** stable offline E2E/HTTP/HA OS smoke, no known high severity release blockers, license compliance and reproducible artifacts. Integration into official HA add-on requires its own PR and maintainers' acceptance.

## P2 — maintainability
11. [#11](https://github.com/undel-gh/hass-configurator/issues/11) Break up monolithic frontend and Python request handler incrementally; retain offline gate.

## Sequence
Inventory → router → Ace and CSS/fonts in parallel → packaging → E2E → security, HA compatibility and docs → release candidate → modular refactor. Never wholesale-merge old `offline` branch. Avoid massive dependency upgrades during P0 except where required for security or compatibility.

## Risks and decisions
- Ace lazily fetches modules, themes and workers; copying three top-level files is insufficient.
- Materialize/MDI stylesheets can fetch additional fonts; audit CSS `url()`.
- Ingress prefixes and caching can conceal broken offline runtime resources.
- Legacy server handles powerful filesystem/command/Git functions; minimize privileges.
- No mandatory runtime network/CDN fallback, even as a convenience feature.
