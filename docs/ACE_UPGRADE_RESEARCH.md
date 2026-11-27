# Ace upgrade research — #9 / #33 / #24

## Historical research scope

This research describes the old-runtime checkpoint and candidate selection. The #33 migration branch now contains the verified candidate bytes; see P1_ACE_YAML_MIGRATION.md. Historical results below do not verify new installed artifacts.

Status: **candidate investigation; runtime remains Ace 1.9.6**.

- First known update to relicensed JSHint: Ace 1.10.0 (2022-08-31),
  [2401fbd](https://github.com/ajaxorg/ace/commit/2401fbd93f0d61cc01150c1071145e974dd6693f)
  updates JSHint to 2.13.5. [JSHint licensing history](https://jshint.com/about/)
  states the old partial JSON restriction applied before 2.12.0. Historical
  lower bound, not a recommendation to freeze a 2022 build.
- Preferred research candidate: ace-builds 1.45.2 (2026-10-21).
  [Source](https://github.com/ajaxorg/ace/tree/68d7fd1c0f5ac50cdb610bf06b86074eab3be652);
  [build](https://github.com/ajaxorg/ace-builds/tree/c9ea63c0a0a436fbb477c918d6736644f77cab9f).
  Source package.json declares ace-legacy-linters ^1.0.2. Historical source
  [e0d223c](https://github.com/mkslanc/ace-linters/tree/e0d223c5a880cb2f258c96ccd22feaaffb29e5a5/packages/ace-legacy-linters)
  identifies 1.0.2 and new workers: JS imports @babel/parser and scope
  analysis, YAML imports yaml.parseAllDocuments. Candidate built JS lacks
  the old JSHint module literal, YAML lacks old yaml-lint module literal.
  Marker absence is not exhaustive removal/license proof. Declared ranges
  (yaml ^2.8.3, @babel/parser ^7.29.2, eslint-scope ^9.1.2) are **not exact
  bundle versions**. Review actual bundled source/license closure including
  HTMLHint, VSCode language services, PHP parser, XML tools and other code.
- Candidate Git build family: 495 files (55 added, none removed relative to
  440), all 174 UI-required filenames. Not proof of functional compatibility.

## Reproduce

Candidate Git blob manifest is separate from runtime lock. CI obtains exact
npm archive with scripts disabled, checks registry SRI and exact Git blob
identities of 495 family files and LICENSE, records SHA-256 of archive and
members. Only then extracts verified regular files into a new directory
outside checkout. It does not write to hass_configurator/vendor. Separate
exploratory OSV queries for candidate package, source minimum versions and
ambiguous legacy Velocity versions do not assert actual nested identities.

Disposable browser harness uses current ace-bootstrap.js, simulated opaque
Ingress-like prefix, local resources only, enforced script/worker policy
(no inline script, no unsafe-eval). Checks JS/YAML error detection/clearing,
HA tag diagnostics observation, themes, keyboard handlers and worker toggle.
A candidate-failed report is a compatibility finding, not a shipped runtime
CI failure; archive/integrity failures are CI errors. Not full editor,
actual Supervisor or release test. Never auto-promote candidate.

## Migration acceptance (separate implementation)

1. Pin independently reviewed exact SHA-256/SRI, family and license closure;
   determine exact bundled dependencies, remaining coffee/xquery, generated
   tokenizer, theme/snippet terms. No license inference from absent marker.
2. #33/#24: one authoritative bounded YAML validator if possible. Standalone
   js-yaml 4.1.0 is unaffected by Ace upgrade. HA/ESPHome custom tags, merge
   keys, multi-document, anchors and diagnostic severity/positions require
   regression tests. Candidate yaml 2.8.3 fixes GHSA-48c2-rrv3-qjmp, but
   dependency range not proof of installed version. No production stress tests.
3. Regenerate lock, vendor manifest, embedded records, notices/SBOM in
   dedicated migration. Full E2E, modes/themes/keyboard/worker, CSP/offline,
   wheel/sdist/Docker, exact-HEAD OSV; actual HAOS sidebar/new tab and
   same-profile fingerprint A/B. Preserve auth, path/HTTP and privilege rules.
4. #34 Materialize XSS/nested attribution and #35 OS/Python remain separate.
5. Record decisions in #9. Research does not clear the historical JSHint
   restriction in the currently distributed archive.
