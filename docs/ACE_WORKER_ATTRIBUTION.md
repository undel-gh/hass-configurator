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

## Selective rebuild research

A separate read-only CI workflow reconstructs only the five retained linter
workers in a disposable pinned upstream checkout. It materializes exact
candidate npm archives at source-lock paths, plus explicit esbuild/Terser
tool closure and YAML alias; no npm install or lifecycle scripts. Tool
archives missing source-lock integrity are recorded as registry-integrity
observations, not historical toolchain pins. The reviewed upstream builder
is instrumented only to select retained nonconflict targets and collect
esbuild metafiles. Both output forms are compared byte-for-byte with the
pinned official linter package; actual contributing archive inputs and
additional bootstrap/CSS generator input hashes are recorded. No generated
JS is promoted. Failure/mismatch retains a report and blocks the research
claim, not a reason to invent versions or alter shipped bytes.

## Research #1 result and version attribution

Exact source HEAD 74fdc6e8046f81000642d2e59536021359b2e8c7, research run
46008174383, actual artifact 15202630304 (ZIP SHA-256
37fbc3d25be8328a8193af57d8242df512d7c358c42739734c33baca13aca71b, CRC clean).
31 package paths materialized without npm install or scripts; 16 retained
candidate paths (15 package/version pairs; two estraverse paths), 15 build
or alias paths. All five retained minified workers match exact shipped bytes.
All contributing dependency inputs are verified archive members; none
unverified. All 16 candidate paths contribute bytes. Build-only path-browserify,
source-map and @jridgewell/resolve-uri lacked upstream SRI; their observed
registry archives now have explicit SHA-256/SRI pins from this artifact.
None contributed runtime code. Node v22.23.5, esbuild 0.27.2, Terser 5.31.6.

The strict first research run failed because every published unminified form
was 216 bytes longer, first difference at offset 16. Author fetched all five
immutable Ace-builds Git files, checked raw SHA-256 against official linter
archive hashes, counted exactly 216 CRLF and no stray CR, and verified that
CRLF->LF conversion reproduces each actual rebuilt SHA-256. All five raw
minified comparisons remain exact. The new gate pins both hashes for every
unminified file, exact CRLF count and equality after that single specified
conversion; no generalized normalization. Raw equality remains false in the
report; relation is explicit. Recheck all contributing original lock paths.
All 15 exact versions now mapped to active npm PURL/OSV scope based on
reconstructed runtime, not on source-lock candidate assumptions. Historical
candidate-only sections above remain chronology. Independent re-review,
new exact-HEAD CI and source-level license review remain open.

## Exact version review checkpoint and non-linter attribution

At b22c9f0, baseline #360 / 46008745027 (4/4), rehearsal #17 / 46008744839
(20/20) and research #2 / 46008744855 succeeded. Actual source 15201929622,
installed 15202334975, rehearsal 15203605070 and rebuild 15202079765 ZIPs
inspected, CRC and published SHA-256 match. 41 BOM entries, 47 notices, 76
Git source files; 569 installed resources each; 10 image layers/498 JS/0
hits, final browser 10/10; equal A/B sha256:f2eb717d4eba94e27f2c0987875daf0fb6dc4252eefa2db982cdd8eb69d26708.
Main OSV 234 queries / 77 matched (2026-11-27T13:41:18Z), all 15 retained
linter dependency queries have zero advisories. No new independent review.

Native base: published unminified worker starts with exact bootstrap from
Ace source commit 68d7fd1c. It has nine named Ace modules (oop, apply_delta,
event_emitter, range, anchor, document, deep_copy, lang, mirror). The first
eight are src/ modules transformed by the upstream TypeScript 5.9.2
Makefile.dryice.js; mirror is in lib/ace/worker. Native base is 1.45.2, not
ace-code 1.43.6 from replacement workers. Full source/build comparison
pending. No additional npm identity asserted for native Ace's own code.

Estraverse: the original 5.3.0 source attributes upperBound to libc++ and
MIT. llvm-mirror/libcxx release_32 commit 1b3775e3 contains a matching
algorithm pattern and historical dual MIT/UIUC license. Distribute original
LICENSE.TXT and CREDITS.TXT; select MIT for the adapted fragment and retain
BSD-2-Clause source and archive notices. Exact revision not established.

XQuery/JSONiq: XQLint source commit 1778846e (Apache-2.0) supplies both
lexer grammar and tokenizer files; exact original REx 5.30 headers from
2014 preserved. REx author's 2026 source is Apache-2.0, but historical
output grant not established by that statement. Both lexers also contain a
Browserify-style loader and other XQLint modules. Keep finding OPEN until
historic output/grammar/loader terms confirmed or scoped removal agreed.
Do not claim current REx tool package version, complete XQLint npm package,
or automatic retrospective clearance. No runtime code removed or modified.

Themes and snippets: current TextMate reference license explicitly permits
per-file exceptions; current converter has limited mapping, generic snippet
converter does not establish origin. Dracula MIT header identified in exact
minified CSS payload, separate original source excerpt shipped. Detailed
all-file comparison and source notice scan pending.

A separate research job now verifies the exact source checkout and Git blobs,
pinned published archive and shipped minified bytes for the native base,
all theme resources and all snippet resources. It compares the native
bootstrap raw prefix, exact nine-module top-level closure and canonical
AST printer output after upstream TypeScript transpilation; does not
claim a raw minified native rebuild. For themes and snippets, parse
static exported data from source/unminified/minified (no eval), distinguish
empty generated stubs, record exact source and runtime hashes and scan
source files/individual TextMate metadata for attribution indicators.
All partial/mismatch results are retained as evidence, not cleared by a
successful native comparison. Historical origin/terms remain per-file work.

XQuery/JSONiq further source checks: common lexer.js blob a6b3cddc is a
literal full-source substring in both current source containers. Language
wrappers xquery_lexer.js (95ceb595) and jsoniq_lexer.js (461cebd4) match
after exactly two require( -> _dereq_( renames, no other changes. The
browser-pack prelude at historical tag 3.1.0 commit 9d4039e5, blob
3cbac8e6, matches both container prefixes after removing comment-only and
blank lines and changing return newRequire; to return newRequire(entry[0]);.
Identical prelude blobs in 3.1.1/3.2.0/4.0.0; no exact package version.
Full original MIT notice added; verification now explicitly checks these
two bounded transformations and reports them separately from literal source
relations. REx output/grammar licensing remains OPEN.

Research #3 failed because one historic TextMate plist is malformed XML
(ExpatError). Preserve error in per-file report rather than stop scanning
or infer no notice; raw source hashes and textual evidence still checked.
No native/theme result claimed from the failed job.

## Research #4: native source mapping and first theme/snippet pass

At 2ecdaf8f, research #4 (46014275424) succeeded in both jobs. Actual
native artifact 15205796171 SHA-256
246efcaf74d4e23444a739982acf96c48ce1b198c2f8ea946ed4307cfc063ad1;
rebuild artifact 15205041609 SHA-256
25e1879338575ef65b4736ae89c2fe1f6ff08e9e5e025be702014cdedd55cb8e.
CRC and published hashes verified. Native bootstrap exact, nine expected
modules and nine canonical source/TypeScript relations equal. Parent Ace
BSD-3-Clause notice; no additional runtime npm component. Raw native
minified rebuild and independent review not claimed. TS archive now pinned.

First pass: 48 themes (47 static payload equal; TextMate wrapper needs
core ace.js CSS), 202 snippets (50 static payload equal, two legacy
lib/ace/snippets sources and 150 loader-only candidates unresolved by the
first comparator). Follow-up checks use exact loader template, both source
locations and core CSS, and record converter input provenance per theme.
Brilliance Black and Brilliance Dull historical plist files are malformed;
neither is a current converter mapping. Preserve parse errors; no blanket
license inference. Per-file origin/terms remain open even for equal data.


## R5.1 historical lexer attribution and upstream clarification (2026-11-27)

Independent reviews supplied for c62292449d35f8a9b6167c959b0df302bb2840f0
report 177 Python tests / 939 subtests, 20/20 browser regression and 7/7 CI
jobs successful. Reviewer 1 independently reproduced five retained workers,
nine native modules, 48/48 theme static payloads and 52 nonempty snippet
payloads plus 150 exact empty stubs. Scoped approval only; actual CI artifact
contents not inspected in this round. No release or merge signoff.

Historical XQLint source evidence (retrieved via immutable Git references):

- XQuery introduction 840c3f05963eb07390112e582c1a2e5affbbb432,
  lib/XQueryTokenizer.ebnf, blob 2dbde102f96306b9c23bddf0271946fad2a91f76:
  https://github.com/wcandillon/xqlint/blob/840c3f05963eb07390112e582c1a2e5affbbb432/lib/XQueryTokenizer.ebnf
- JSONiq introduction 23cca84bb0c18a99362e3890f92b0e3ee3740de3,
  lib/JSONiqTokenizer.ebnf, blob b03294875246a4b5d7ff1e84af5c9b984b69085a:
  https://github.com/wcandillon/xqlint/blob/23cca84bb0c18a99362e3890f92b0e3ee3740de3/lib/JSONiqTokenizer.ebnf
- Original generation scripts generate_xquery_lexer.xq and
  generate_jsoniq_lexer.xq at those respective commits, blobs
  eb714917cf9175c8188570e5ebdd926e24ae947b and
  b69d9312b30aec340c6434ed8a13cef9cd13be6f, POST input to REx with
  -ll 2 -backtrack -tree -javascript -a xqlint.

Both original EBNF headers identify Ajax.org B.V., 2010, BSD three-clause.
Ad hoc programmatic comparison: remove leading comment decoration, extract
from Copyright (c) through before END LICENSE BLOCK, collapse whitespace
and trim; compare with similarly whitespace-normalized shipped
hass_configurator/vendor/licenses/ace.txt (blob
4760be2a6220cf545129b233e20574f2a7bb630e). Both exact normalized text
comparisons returned true. This is not raw-byte equality, an automated CI
gate, or proof of complete grammar ancestry. Known historical BSD notice
text is already shipped; no duplicate notice added.

The maintainer opened https://github.com/GuntherRademacher/rex-parser-generator/issues/80
on 2026-11-27 to request explicit historical output redistribution terms.
No comments at author-side check. The REx author's XQLint contribution
6645a0c348512990536b011b1497e2f67e6d1f6d in 2022 corroborates familiarity,
not a license grant. Historical web service terms not recovered.
REx output rights and remaining grammar ancestry remain OPEN / HOLD.
No change to component license expression or runtime scope in this research
checkpoint.

## R5.2 preliminary theme upstream references

The reviewed static-payload matches establish shipped Ace content identity,
not original license clearance. The following original-project reference
files were fetched from immutable commits; these are candidate attribution
references, not verified historical input equivalence or new shipped notices.

| Family | Reference (commit / file) | Git blob | Observed terms |
| --- | --- | --- | --- |
| Tomorrow | [ccf6666d / LICENSE.md](https://github.com/chriskempson/tomorrow-theme/blob/ccf6666d888198d341b26b3a99d0bc96500ad503/LICENSE.md) | 0e689d0a004eb37155ef430fe615a6e27209d30f | MIT, Chris Kempson 2011 |
| Solarized | [62f656a0 / LICENSE](https://github.com/altercation/solarized/blob/62f656a02f93c5190a8753159e34b385588d5ff3/LICENSE) | ee08d7e44f15108ef5359550399dad55955b56ca | MIT, Ethan Schoonover 2011 |
| Gruvbox port | [75407cc8 / LICENSE](https://github.com/Briles/gruvbox/blob/75407cc80c51814d61beb1df07e380d6f58ad767/LICENSE) | 1d533cf6dcb3dd57aba8c955001f89d4ed03db81 | MIT, Brian Reilly 2016 |
| Nord | [1cef7160 / license](https://github.com/nordtheme/nord/blob/1cef71605416a222e57225b544540ce0fcec18d4/license) | 996f8fb61226844c6bbd2167a8b1a118be10609f | MIT, Sven Greb 2016-present |
| One Dark | [9c96f445 / LICENSE.md](https://github.com/atom/one-dark-syntax/blob/9c96f4454362267ac45322063e193ccf9d2debb1/LICENSE.md) | 4e47b02a28a95c1d3001e4b747ce0638f11475e1 | MIT, GitHub Inc. 2016 |

At Ace source 68d7fd1c0f5ac50cdb610bf06b86074eab3be652,
tool/tmthemes/Tomorrow.tmTheme (8c98c22657b272436fd55d6ce4ab3b99a1382877)
references Chris Kempson's website; gruvboxDarkHard.tmTheme
(64c80d32a27dad6d38edc1b74005f805c802b979) explicitly names Brian Reilly
and Pavel Pertsev. Solarized-dark.tmTheme
(4efdabdbd5ca5e588d0357c2b3d8aa7b255f7813) has no observed individual
license marker. The current morhetz/gruvbox tree at
ef8864bb42bf244f0295d1c5a403b27e3d139695 has no root LICENSE; the header
of colors/gruvbox.vim (66246fba24fd49eeb50dd833094d272f0bbab640)
identifies morhetz but has no explicit license grant. Do not infer an
original license from the port's MIT terms. Further history, exact input
relationships, per-file exceptions and original notices required. No
new SBOM/PURL or license clearance asserted.

## R5.2 external reference comparison gate

Extend the native research job with seven pinned Tomorrow/Solarized TextMate comparisons and five pinned historical Tomorrow Ace ports. Verify each original Git blob and two original license blobs before comparison; record SHA-256. Compare complete parsed plist dictionaries and ordered settings, retaining differences (including metadata). Compare literal CSS strings via TypeScript AST, never execute external JS. Differences are reported, not treated as proof of lineage or clearance. Pin mismatch fails research. No runtime/notice/SBOM change. Gruvbox historical references, Nord/One Dark lineage and all license dispositions remain open. REx issue #80 still has no comments at check. New CI and artifacts pending.

## R5.2 historical contributions and recovered theme notices

Ace PR #432 (Chris Kempson) merged five Tomorrow inputs; all five match current Git blobs. Signed CLA promised, actual agreement not inspected. Solarized import 69778adb (David Alan Hjelle) explicitly credits Ethan Schoonover; both input blobs unchanged. PR #917 merge 16b2f1c9 replaced both historical tri-license wrapper headers with BSD-3-Clause; root LICENSE blob matches shipped Ace. Ace PR #3673 explicitly imports Briles/gruvbox; both Hard input blobs unchanged. Three original MIT whole-file notices now tracked by embedded.json, with immutable historical/current source pins and runtime locations. Partial records, no PURLs or exact external releases. Ordinary Gruvbox initial 8a5fa7fb reverted by 88520c29 for missing CLA; reintroduced via PR #3269 / d9199ac2, with Irakli Gozalishvili 2011 MIT-like header labelled BSD. Original Pavel Pertsev license, CSS reuse and wrapper lineage remain OPEN. REx #80 still awaiting clarification. No runtime changes or release approval. New CI pending.

## R5.2b Gozalishvili wrapper recovery

At Ace commit d9199ac2, all 36 historical theme JS files were inspected for copyright markers: 33 Ajax.org headers, three Gozalishvili headers (Ambiance, Chaos, Gruvbox). The latter share MIT permission terms labelled BSD; Gruvbox differs by one whitespace-only line. Its complete header is retained verbatim as a source excerpt. Three exact AMD-to-CommonJS relations and the 2017 Gruvbox CSS plus active-indent-guide relation are now pinned and fail closed. This is wrapper attribution, not a license claim for color schemes. Original Gruvbox rights and the 2016 CLA/reintroduction question remain open. Baseline 8f46250 workflows succeeded after rerunning Chromium infrastructure failure. No runtime changes; new CI pending.

## R5.2b original Gruvbox MIT/X11 declaration (supersedes earlier uncertainty)

User identified morhetz/gruvbox commit 317ca28a8e4306cdfcd43d45a41355a2a0aa25d8 (Vanilla colorscheme, 2012-12-02, author morhetz). It adds colors/gruvbox.vim and a README License section explicitly linking MIT/X11. README blob fc5bd3a2cffb45a7365064abe47ea7c9de663b87, Vim blob 70a8a50b8f0b5a15d8afaef54761b0b6aca77669. Descendant ef8864bb42bf244f0295d1c5a403b27e3d139695 (GitHub compare 193 ahead / 0 behind) still declares MIT/X11: README 008de69c071f2b783b8822739e0d6258dbde18c4, Vim 66246fba24fd49eeb50dd833094d272f0bbab640. Absence of root LICENSE is not absence of a license declaration. Both snapshots pinned; not a claim about every intervening revision or exact original revision used in Ace. Preserve exact 2012 README license excerpt and unmodified SPDX standard MIT template at cc4fe1ac462bd3ad3c81a07234baf7d9541ee871, text/MIT.txt blob d817195dad53ec992418c28ffca5fbd1cd86502a, explicitly a reference with placeholders, not original copyright text. Add original scheme attribution (Pavel Pertsev / morhetz) for all three retained variants, separate from Brian Reilly Hard port and Gozalishvili wrapper. Partial status, no version or PURL. Remaining exact port lineage, 2016 CLA revert, independence of 2017 contribution and other original-source notices OPEN. Baseline ea257b1 three workflows success; artifacts not independently reviewed in this step. New CI pending. No runtime changes or release approval.

## R5.2b CLA discussion and R5.2c Nord / One Dark

Original Gruvbox PR #2916 merged 2016-02-27; maintainer nightwing requested CLA on 2016-05-24 (https://github.com/ajaxorg/ace/pull/2916#issuecomment-221365903), confirmed revert due to missing CLA on 2016-06-03 (https://github.com/ajaxorg/ace/pull/2916#issuecomment-223543383; PR #2985 Fix license issues). Issue #3268 2017-04-12 and PR #3269 merged 2017-04-18 establish reintroduction by another contributor. No later signature evidenced. Missing CLA alone does not establish absence of copyright license. Remaining question is reuse of independently protected 2016 contribution in current 2017-derived CSS, not original morhetz MIT/X11 declaration. No closure or risk acceptance.

Nord Dark: Ace PR #4203 merged 2020-03-08 (9115b68e); author now shown as ghost, original Nord site explicitly referenced. PR includes explicit permission to use/modify/copy/redistribute contribution under terms of choice. One Dark: PR #4415 by nkean merged 2021-03-02 (3359dfc1); explicitly references atom/one-dark-syntax and same permission statement. Historic CSS/wrappers and current source pinned; both historical wrappers contain Ajax.org BSD-3-Clause. One Dark historical CSS is current literal payload prefix with active-indent-guide addition; Nord also changes stray closing-brace comma. Original MIT whole-file notices now preserved from nordtheme/nord and atom/one-dark-syntax pins. Exact external version and any intermediate port lineage remain open. No package versions or PURLs. Baseline 128c234 three workflows SUCCESS; artifact contents not reviewed in this step. New CI pending. No runtime changes or public release approval.
 
## R5.2d historical TextMate input evidence

Original textmate/themes.tmbundle README.mdown at 9af146748ca3f0d3935985b6c731ccc7781831d9 (2011-11-12), blob 32d8f85a4c5f41b1fd636664c7a4ca776f511b9f, unchanged at e6e918506291b2dec178ad1b7e6f04653d25818c, contains the permission and individual-file exceptions corresponding to Ace tool/tmthemes/LICENSE added 2010-11-05 in cba64d86 (blob 08f1380f3a9bce3135253bc69f5861dec3dcae17). Scope wording repository vs directory and whitespace only; original README postdates Ace import, not proof of 2010 individual grants. Existing shipped Ace license reference retained, original README pinned in review record. Do not label this text MIT/BSD without evidence.

Four exact initial imports: Cobalt TextMate 0635502e -> Ace cba64d86 (3c685f253c723122c55800f7ce7ee7374963c428), Dawn TextMate 2746dd84 -> Ace 242cfb76 (12cff9b6e2e9d6e1255678e7af2a685116c5ac32), both unchanged current inputs. Pastels on Dark TextMate c2fcd871 -> Ace cba64d86 (e3928606e60f437527a03eb5f96fda92cde95bf4), later 9ef05262 changes palette/settings to 47b836318087d53ac60db65b83c29ca07afa327f. Twilight TextMate c2fcd871 -> Ace 242cfb76 (a83f7ecbbe46792e321a1c823fb56d159bade152), later f5a5e705 adds function-name rule, current a5984e82e22654f4df93363c23f882645e6df3b4. Author metadata c2fcd871 explicitly based on best guesses from SVN log; corroborating original contributions: Jacob Rus Cobalt 1460c67a (2006), David Powers Dawn 2051f9e0 (2006), Mats Persson Pastels 2d56b38f (2005), Michael Sheets Twilight 0abc270a (2005). Cobalt identifies Slate by Wilson Miner as basis; rights/lineage OPEN.

Kuroir (Stanley Rost, ab6aa3be, 36acd588d1f636c411071c0d48fefc8c6d1f14d4), Xcode default (comment Carmine Paolino, ecfdc5fb, c7b5072cd31169ec9582bab8de3e007adfaede01), krTheme (comment Kenneth Reitz, cba64d86, 65c5c9b6aac1d42dc65c1ee537093404fe207b64): current inputs match historical Ace additions; external origins/individual terms not established. No companion -license file observed in current Ace directory; historical and external per-file exceptions remain to be reviewed.

Research gate now verifies pinned source identities, exact initial import byte equality, compares full parsed current inputs without discarding ordered settings, and checks the bounded license scope wording change. No runtime changes, new shipped notices or SBOM components. Baseline 41ae327 three workflows SUCCESS; artifacts not reviewed in this step. New CI pending. REx #80 no response at check. No release approval.
