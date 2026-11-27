# Ace 1.45.2 worker attribution — #33 / #9

Status: **partial, evidence collection; no release clearance**.

## Historical runtime gate

Exact HEAD 66ac33422ac5083ac7da4bd7f2090fa4400128a7:
baseline #349 / 45977275984 4/4 success (158 Python, 27 Chromium + one
expected skip, wheel/sdist/Docker 6 each); rehearsal #6 / 45977275853
11/11. Actual three archives 15187442808 / 15187752539 / 15187088520
downloaded and inspected, ZIP CRC and GitHub SHA-256 match. Source BOM
30 components, 57 upstream files, 27 notices, zero current literal source
relationships; 554 resources verified in each installed distribution.
Exact standalone js-yaml archive/member relation; Docker lock matched,
429 Debian binary packages, equal image IDs. Main OSV 220 queries/77 matches,
zero for ace-builds 1.45.2 and js-yaml 4.3.2; incomplete nested identity coverage.
No external attempts. Rehearsal #6 is additional evidence, not real Supervisor.

## New upstream architecture evidence

Ace source 68d7fd1c0f5ac50cdb610bf06b86074eab3be652
[Makefile.dryice.js](https://github.com/ajaxorg/ace/blob/68d7fd1c0f5ac50cdb610bf06b86074eab3be652/Makefile.dryice.js)
(blob 2d4596dee98c8b09333b192a8f4cd9cd09331185) copies
ace-legacy-linters/build over all four generated families. Its package.json
specifies ^1.0.2, not an exact installed version.

The candidate linter build script at source e0d223c5a880cb2f258c96ccd22feaaffb29e5a5
([build-worker.mjs](https://github.com/mkslanc/ace-linters/blob/e0d223c5a880cb2f258c96ccd22feaaffb29e5a5/packages/ace-legacy-linters/build-worker.mjs),
blob f052326468c9ad723174aea0153ef8f6d9de5fd3) defines eight replacement
workers and uses esbuild and Terser. The upstream monorepo package-lock.json
Git blob 17e9297cb3a744c12b1bd2a6c55a7b3138b39918 is a *source-lock candidate*,
not a proof of the published build dependency closure.

| Worker | Source-level candidate attribution |
| --- | --- |
| JavaScript | @babel/parser, eslint-scope, globals; source imports and unminified path comments |
| YAML | yaml, workspace-local node_modules/yaml (2.8.3 in pinned source lock, not root 2.7.1) |
| CSS | vscode-css-languageservice and transitive source paths |
| JSON | vscode-json-languageservice, JSON diagnostics wrapper |
| HTML | htmlhint |
| PHP | php-parser |
| Lua | luaparse (0.3.1 version marker already present) |
| XML | @xml-tools parser/ast/constraints/validation, namespace validator |
| Coffee | Native Ace worker; CoffeeScript 2.2.1 marker; exact nested closure open |
| XQuery | Native Ace worker; XQLint/tokenizer lineage needs current source checks |
| Base | Native worker bootstrap; nested review open |

## Evidence method and boundaries

The build-time attribution command compares both minified and unminified
worker members of the registry-integrity-verified ace-legacy-linters 1.0.2
archive with the independently pinned Ace archive and actual runtime workers.
Only equal pairs qualify as exact linter build matches. Source path comments
then select the deepest node_modules package and exact workspace lock path;
missing lock entries remain unresolved. It collects root license/NOTICE
reference files from candidate npm archives with registry SRI, and source-lock
SRI where present, and performs separate candidate OSV queries. It never
executes npm code or writes to runtime. Archive/license evidence failures and
missing notices remain visible. Candidate reports are not the shipped SBOM.

No automatic promotion of exact nested versions from source lock. Next:
review the actual attribution artifact, pin the linter archive and matched
worker hashes, reconcile active records and notices; use reproducible build
or stronger byte evidence where needed for exact dependency versions. Retain
native, theme/snippet and residual risk gates. #33/#9 remain open.
