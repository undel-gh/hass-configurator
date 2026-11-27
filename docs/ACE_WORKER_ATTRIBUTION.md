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

## Native worker re-check and first attribution finding

Both XQuery and JSONiq tokenizer literal-full-source relationships were
rechecked directly against current Ace source 68d7fd1c0f5ac50cdb610bf06b86074eab3be652. Both container Git
blobs are identical to the historical 1.9.6 source evidence. CoffeeScript
2.2.1 source blob is also unchanged and contains the compiler version header;
current minified worker marker already verified. These current source pins
are added to embedded.json, with partial component-mapping disposition.
The native base worker remains open.

First attribution run #350 / 45978322070 on 5895a9fa stopped at a real
ace-legacy-linters npm LICENSE vs pinned source/shipped notice mismatch.
Do not declare the linter notice accepted. The correction preserves actual
archive notice bytes (base64), Git blob, SHA-256 and source/shipped equality
flags in the report, still fails the attribution gate on mismatch, and
retains evidence for worker comparisons and candidate notices/OSV first.
No npm archive notice substituted into the runtime without review.

## Actual archive correlation and notice disposition

#351 source artifact [15187533994](https://github.com/undel-gh/hass-configurator/actions/runs/45978519039/artifacts/15187533994), exact HEAD 5c25067e2e1311fc70714e0e928ca527fe4b03db: downloaded and inspected, CRC and SHA-256
4bbf25465cf6fee3b2bb5c3cb364f35afffd18dfe12a560784938c270b3ad389 match.
All eight minified **and** unminified worker pairs match the official
ace-legacy-linters 1.0.2 npm archive byte-for-byte. Archive SHA-256
3b816b72064cbe56412885b2a22703ac2dbdc13784ece24bed46b5ee9c0a435f.
License archive SHA-256 3432ec591bb26b6461a86be1198f2c9538107cb8cf0c41107be53df0b9e56903,
Git blob c5b1603adc228961316de4dfd99a4d033c4a0bca; 21 CRLF, zero bare LF,
zero stray CR. Exact CRLF-to-LF conversion reproduces existing Git source
blob 319b7eddf9ad9ee57746f4bb486597c87a35929c and shipped LF SHA-256
33d28673699c4240c72143daf1fb349e39d0b0cd703d21c300bc4e0cdf2a3433.
This specific pinned relation is now checked; arbitrary normalization is
not allowed. No license content changed. Source inventory identifies the
linter package, not all dependencies.

25 unique source-lock candidate package/version pairs, all paths resolved;
23 packages with root notices, two without (@vscode/l10n 0.0.18 and
esrecurse 4.3.0; investigate source/embedded notices). 25 root notice files
collected. Source-lock candidates, **not verified installed versions**:

| Worker | Candidate versions from the exact path in published unminified build and pinned source lock |
|---|---|
| All 8 replacement workers | ace-code 1.43.6 |
| JavaScript | @babel/parser 7.29.2; eslint-scope 9.1.2; esrecurse 4.3.0; estraverse 5.3.0 (two distinct lock paths); globals 14.0.0 |
| YAML | yaml 2.8.3 (workspace-local) |
| CSS | vscode-css-languageservice 6.3.10; @vscode/l10n 0.0.18; vscode-languageserver-textdocument 1.0.12; vscode-languageserver-types 3.17.5 |
| JSON | vscode-json-languageservice 5.7.2; jsonc-parser 3.3.1; vscode-uri 3.1.0; same three shared @vscode/l10n/languageserver packages |
| HTML | htmlhint 1.9.2 |
| PHP | php-parser 3.4.0 |
| Lua | luaparse 0.3.1 (existing shipped version marker) |
| XML | @xml-tools/ast 5.0.5; common 0.1.6; constraints 1.1.1; parser 1.0.11; validation 1.0.16; chevrotain 7.1.1; lodash 4.17.21; regexp-to-ast 0.5.0 |

Candidate OSV 26 pairs including linter package, one matched pair:
lodash 4.17.21 (GHSA-r5fr-rjxr-66jc, GHSA-xxjr-mmjv-4gpg). Author then
verified specific version and module-path markers in actual minified XML
worker for lodash 4.17.21 and chevrotain 7.1.1, and exact npm LICENSE blob
identity against each immutable Git release. Both added as identified
active SBOM entries with exact notices. Lodash advisories must now be
tracked in the main scan and risk register; no automatic acceptance or
claim of exploitability. Other source-lock version candidates remain
separate pending stronger evidence. All 8 worker package mappings and
native coffee/XQuery mappings partial for nested closure; base open.

## Curated runtime and retained notice recovery — 2026-11-27

The preceding full-family sections describe historical evidence, not the
current shipped inventory. #37 removed XML/PHP/Lua/Coffee/XQuery workers.
Reviewed correction HEAD f72a78108a1c84f791efb0abe00876332eb91d0b: baseline #356 and
rehearsal #13 success, all three artifacts inspected by author and reviewer 2.
Five retained linter pairs, 15 source-lock candidates plus linter (16 OSV
candidate queries / zero matches), native base open. Former Lodash XML
findings are remediated by physical removal within the reviewed runtime
scope, not a VEX/risk waiver; see P1_SUPPLY_CHAIN.md.

The two candidate npm archives without root notice files were investigated:

| Candidate | Source provenance | Notice evidence | Identity disposition |
| --- | --- | --- | --- |
| esrecurse 4.3.0 | annotated tag v4.3.0 -> 8ceb63797813d9ac69572a671b95cf58ffdf35b6; package.json blob dec5b1bc1fd3ac43e74d7a575cc6bb98b453b2e3 | Full original BSD-2-Clause source header in esrecurse.js blob 15d57dfd0218f66036a7cb5c5fe8e18c26d82267; exact excerpt shipped | identified 4.3.0: minified worker contains name, description and version in package metadata; unminified module exports version from that metadata |
| @vscode/l10n 0.0.18 | tag l10n/v0.0.18 -> fc7e3d79ddb91a2cc24a9730aad912026a43dbf2; l10n/package.json blob 8ebb31b8d8635de35f382744b898c9579ee20a95 | Exact root MIT LICENSE blob 9e841e7a26e4eb057b24511e7b92d42b257a80e5, shipped as source-reference notice | partial: distinctive error literal and source paths establish CSS/JSON presence, exact version not proven |

Both source notices are checked by existing embedded-upstream verification
against immutable Git blobs and by local SHA-256. This does not claim either
npm archive contains a root license file; that observation remains valid.
esrecurse has archive SHA-256 3ecf9370d7296b47b570c88a11f70b35bb965af8d536536b259eb55f9b793b61;
@vscode/l10n archive SHA-256 f1c2dc897488595f6bb42121869f525c6c6a5f7c8dca550754199c3251ed7c5c
from verified #356 source evidence. Next correlate archive source members
against published unminified worker sections; no invented exact l10n version.
Remaining 13 candidate archive notices have been collected but their
shipped mappings and exact version attribution remain open. Base worker,
themes/snippets, XQuery lexer generator terms and Materialize findings
remain separate. New inventory CI and independent review required.

## Retained candidate mapping and archive notice pins

Exact #357 / #14 at 9b64354a: all jobs success; author inspected actual
source 15198574231, installed 15198804542 and rehearsal 15198309106 ZIPs,
CRC and published SHA-256 match. 172 Python; rehearsal 20/20; wheel/sdist
15 each, Docker 10; 30 source BOM entries, 31 verified notices, 72 Git
sources. 553 installed resources per artifact, 5 first-party checks; image
A/B equal sha256:5442b08d45bbbee9b1f4ca5e40364cbc59d82b9e1cf178d318195151c20f4db0.
Main OSV 220 queries / 77 matched, esrecurse 4.3.0 zero advisories. No
additional independent review of 9b64354a claimed.

All 15 candidates now have active component mappings, using published
unminified node_modules paths and corroborating minified literals. The
remaining 13 retain exact original candidate npm notice files (15 total)
from the #357 artifact. Archive SHA-256, SRI and exact member SHA-256 are
pinned in embedded.json. Existing build-time evidence verifies fresh
archives and exact member bytes including CRLF, duplicate/symlink rejection
and package metadata. Only esrecurse has exact version evidence; the
other 14 records remain partial without npm PURL or version-bound main
OSV query. Candidate notice license expressions are evidence, not final
runtime license clearance. Original archive root notices for estraverse
lack its source copyright header; we also retain the complete original
source header from pinned v5.3.0. LLVM libc++ upper_bound/lower_bound MIT
reference remains an additional lineage/notice review. JSON service's
full archive notice preserves glob-to-regexp BSD-2-Clause terms; two
Microsoft third-party notice files retained verbatim, not evidence of a
specific LGPL dependency. More exact identity evidence and all remaining
native/theme/snippet/lexer terms are required. No runtime code changed.
