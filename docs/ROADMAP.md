# Offline Revival Roadmap — normative gates

**Status:** normative proposal for PR #12. Once approved, feature PRs MUST meet phase gates and reference requirement IDs in `SPECIFICATION.md`. Current implementation/test status is **not** implied by this plan.

## Product objective
Ship HASS Configurator as a reproducibly packaged, cold-cache offline editor on `master`, preserving its existing functions. This fork does **not** automatically change the official HA OS File Editor add-on ([reported issue](https://github.com/home-assistant/apps/issues/2811)). The historical `offline` branch is a reference, not a merge target.

## Development decisions and priorities
1. Start from `master`; avoid wholesale merger of divergent `offline` branch (ADR-001).
2. Preserve `BaseHTTPRequestHandler` as transport adapter, but extract a **permanent** router/response boundary in P0 #2, suitable for P1 security policies (ADR-003). General UI/framework refactoring stays P2.
3. Initial Ace candidate: published `ace-builds@1.9.6` tarball, single `src-min-noconflict` build family and complete dynamic worker/module closure. Lock distribution integrity and per-file hashes before vendoring (ADR-006).
4. Version asset URLs using content-fingerprinted namespace; no-store for HTML/API and immutable long-lived caching only on fingerprinted static resources (ADR-009).
5. Any attempted public browser runtime fetch fails a supported scenario, including failed CDN requests (ADR-002).
6. Requirements are binding once approved. A PR MUST link FR/NFR/ADR IDs to Issue(s) and test or manual evidence, updating `TRACEABILITY.md` (ADR-007).

## P0 — functional offline MVP

| Sequence | Issue | Output / acceptance gate |
| --- | --- | --- |
| 0 | [#1](https://github.com/undel-gh/hass-configurator/issues/1) | Confirm network dependency inventory; choose/pin Ace tarball, family and module closure; capture immutable integrity metadata |
| 1a | [#2](https://github.com/undel-gh/hass-configurator/issues/2) | **Permanent**, exact/method-aware route dispatcher, single response writer, safe package-asset serving, route-prefix API separation, cache headers, trusted ingress URL contract |
| 1b | [#14](https://github.com/undel-gh/hass-configurator/issues/14) | GitHub Actions minimum CI and requirements-to-tests PR contract. Start cold-cache external-attempt-denial smoke **alongside #2**, not after feature implementation |
| 2 | [#3](https://github.com/undel-gh/hass-configurator/issues/3) | Vendor Ace from one verified artifact with complete mode/theme/worker closure and correct ingress URLs; extend smoke |
| 2 | [#4](https://github.com/undel-gh/hass-configurator/issues/4) | Vendor compatible CSS/icons/fonts; remove outbound CSS/font/image fetches; extend smoke |
| 3 | [#5](https://github.com/undel-gh/hass-configurator/issues/5) | Reproducible wheel/sdist/fork-built container; package/runtime version alignment; fingerprinted assets and upgrade-cache behavior |
| 4 | [#6](https://github.com/undel-gh/hass-configurator/issues/6) | Complete E2E test matrix: blocked external requests, root/simulated ingress, dynamic Ace, missing assets, warm-cache upgrade, reliable regression failures |

**P0 must pass:** AT-01 through AT-10 from `SPECIFICATION.md` (where applicable), backed by executable CI/manual artifact. No browser-initiated attempt to public origin except deliberate explicit external doc navigation. **Simulated** Ingress is sufficient at P0; **real** Ingress is P1.

**Critical dependencies:** #1 → #3; #2 ↔ #14 initial CI + smoke; #2 → #3/#4 (asset URL router); #3/#4 → #5 → #6. #2 MUST NOT be declared complete with a temporary `endswith` handler.

## P1 — secure release candidate

| Issue | Output / release gate |
| --- | --- |
| [#7](https://github.com/undel-gh/hass-configurator/issues/7) | Authorization/CSRF/filesystem confinement/symlink/TOCTOU/exec/Git security integrated with permanent router, with abuse tests |
| [#8](https://github.com/undel-gh/hass-configurator/issues/8) | **Real** HA OS add-on Ingress smoke tests (correct X-Ingress-Path/proxy trust, redirects, optional HA WS, upgrades) |
| [#9](https://github.com/undel-gh/hass-configurator/issues/9) | Third-party licenses, SBOM, hashes, vulnerability review, supply-chain update process |
| [#10](https://github.com/undel-gh/hass-configurator/issues/10) | Production/docs matrix, installation, rollback, security model, compat versions and operational instructions |
| [#13](https://github.com/undel-gh/hass-configurator/issues/13) | CSP threat model, report-only and enforceable policy path; minimum extraction of blocking inline JS/handlers in P1; explicit reviewed exceptions |

**P1 must pass:** AT-11/AT-12 real HA OS/security evidence plus all P0 regression checks. Unknown or high-severity defects must not be silently exempted. CSP restrictions that remain report-only/unsafe must have a named risk owner, issue and explicit release decision; strict policy cannot be claimed unless actually enforced.

## P2 — maintainable codebase
[#11](https://github.com/undel-gh/hass-configurator/issues/11): broad extraction of inline UI JavaScript and modular decomposition of HTTP API / potential transport migration *after* permanent routing and security boundaries are established. P1 CSP minimum extraction is **not** postponed to P2 by this issue.

## CI and documentation synchronization
- **Before #2 merges:** at least one working GitHub Actions workflow and early offline network-attempt smoke; branch protection/required checks configuration to be reviewed separately (#14).
- Each implementation PR MUST include a requirement impact list, owner Issues, test names and CI run evidence, plus updated `TRACEABILITY.md`. A requirement without a passing automated test or recorded manual evidence remains `pending`.
- Changes to architecture decisions require a simultaneously updated ADR and test plan. Do not accept a docs-only `checked` box as proof of behavior.
- #6 graduation: run the same smoke on **installed** wheel/sdist/fork image, not only checkout development server.
- Full release gate includes repeated cold-cache and warm-cache upgrade tests behind simulated Ingress and real HA Ingress.

## Risks and mitigations

| Risk | Mitigation / owner |
| --- | --- |
| P1 hardening blocked by monolithic HTTP handlers | Permanent router + centralized response and policy hook in #2; authorization in #7 |
| Inline JS prevents meaningful CSP | Dedicated #13, carve out P1 prerequisite extraction, broad #11 only after |
| CDN attempt hidden by successful fallback or cache | Intercept every request at initiation; #14 minimal gate and #6 complete gate |
| Ace worker/mode artifacts mixed from CDNs | Single locked `ace-builds@1.9.6` artifact/family; #1/#3 |
| Ingress path/header spoofing or bad redirects | Relative URLs and trusted proxy policy; #2 simulated, #8 real |
| Stale assets on HA add-on upgrade | Fingerprinted URLs, cache policy and warm-cache upgrade tests; #2/#5/#6 |
| Requirement drift due to weak CI | `TRACEABILITY.md`, PR template, GH Actions; #14 |
| Misleading release identity | Single source of version and installed artifact tests; #5 |

## Release process
For each milestone, maintain a traceability/evidence snapshot; never claim tests were run unless CI logs or recorded manual reproduction exists. Ship a fork prerelease first, validate with real HA OS add-on independently, then seek official upstream adoption through the appropriate Home Assistant repository.
