# Third-party notices — HASS Configurator

This package includes offline third-party resources. Their upstream license
texts are distributed unmodified in `../vendor/licenses/` and `licenses/`.
See `inventory.json` for component-to-file ownership, checksums and
immutable license-source references. Existing vendor manifest covers the
510 resources on the #37 curated branch; this separate inventory covers inherited JS/font
assets and notices without making notice files web routes.

- Ace 1.45.2: Ajax.org B.V., BSD-3-Clause; curated subset of exact upstream build family.
- Materialize 0.100.2: Copyright 2014-2017 Materialize, MIT.
- Material Design Icons 3.4.93: Austin Andrews, reserved font name Material
  Design Icons (OFL-1.1); upstream notice also credits Google material icons
  (Apache-2.0). No modified font or standalone font sale.
- jQuery 3.6.0: OpenJS Foundation and other contributors, MIT.
- js-yaml 4.3.2: Vitaly Puzrin, MIT.
- Legacy Roboto fonts distributed by Materialize: Copyright 2011 Google Inc.
  All Rights Reserved. Name-table version 2.136 (2017); Apache-2.0 explicitly
  embedded in all ten font files; historical license included separately.
  Original separate font archive unresolved.
- Legacy Google Material Icons webfont: Copyright 2018 Google, Inc.
  All Rights Reserved. Name-table version 1.017; upstream Apache-2.0 license
  included. Exact original binary archive unresolved; no embedded license field.

The Python package depends on PyOTP, GitPython, legacy-cgi and their
transitive dependencies; their distributions carry their own license
notices. The hash-pinned Docker closure includes gitdb and smmap. Their
license identifiers are recorded in the inventory and actual installed
distribution metadata/notices are collected during CI. The project MIT
license does not relicense third-party files. This notice is not a legal
opinion or a claim that embedded subcomponent attribution is exhaustive.

## Embedded code attribution (not complete license clearance)

`embedded.json` distinguishes embedded libraries from unresolved review
records and links each to its containing file, exact upstream source
commit/blob, version evidence and available notices. Full texts and marked
source excerpts are in `licenses/embedded/`; source excerpts retain the
available copyright/conditions without implying a missing full license is
satisfied. Versioned libraries are included in the source BOM and scan when
a package ecosystem identity is supported. Parent file ownership remains
exclusive; no independent archive hash is invented for nested code.

Materialize embeds Hammer 2.0.4, Velocity (header 1.2.3/runtime 1.2.2),
Velocity jQuery Shim 1.0.1 (jQuery Foundation 2014), jQuery Easing 1.4.0
(George McGinley Smith and Robert Penner), Waves 0.6.4 (Alfiana E. Sibuea),
Pickadate 3.5.0 (Amsul), ClockPicker 0.0.7 (Wang Shenwei; further modified
2015 Ching Yaw Hao), jQuery ScrollSpy 0.1.2 (John Smart), jQuery Hammer
adapter, raf.js (Nicolas Gryman, original polyfill Erik Möller) and
Underscore fragments. Historical candidate notices do not establish exact
versions of copied fragments or the full original shim license.

Ace 1.45.2 retains 490 of the independently reviewed 495 upstream files.
Five unnecessary workers are physically excluded; all retained bytes unchanged.
Current embedded attribution is partial. Source evidence for ace-legacy-linters
(1.0.2, five retained exact published worker pairs; MIT source notice retained), @babel/parser and yaml is recorded;
remaining exact nested versions, worker dependencies, theme/snippet licenses
and full attribution remain OPEN. The old JSHint module and historical JSON
license literal were not found in the verified new family; this marker check
is not exhaustive license clearance. Historical Ace 1.9.6 records and
notices are retained as references, not as assertions of active components.
The original restricted JSHint 2.11.0 license was not retroactively changed.
jQuery 3.6.0 still embeds Sizzle 2.3.6; its MIT text is included.
No public redistribution approval is implied.

The inherited Google Material Icons font exactly matches the 2019-12-29
HASS Configurator introduction commit 6e3611006c84cf103318a9c4bb5a661e5da73411;
the previous HTML used Google's online stylesheet. The original CDN archive
was not recorded. A historical official repository WOFF2 differs. Do not
claim the original binary origin is fully resolved.

Further historical Ace 1.9.6 reference notices (not current worker identities): HTML5 parser upstream (MIT, Aria Stewart),
XQLint (Apache-2.0; both generated lexer source files at the 2014-07-24
commit are literal subsets of tagged Ace source bundles), and xmldom 0.1.19
(MIT/LGPL choice links, historical parent only). These references do not
establish the entire historical fork license/version; retain partial status.

Historical full-family XML worker contained lodash 4.17.21 (MIT) and Chevrotain 7.1.1 (Apache-2.0); #37 excludes that container. Their notices are retained pending whole-runtime attribution. No claim of complete component absence or risk acceptance. Other source-lock candidates and their attribution remain open. See docs/ACE_WORKER_ATTRIBUTION.md. The ace-legacy-linters npm LICENSE differs from the retained exact Git source LICENSE solely by 21 CRLF-to-LF line endings, verified against exact archive and notice pins.

Retained worker notice recovery: esrecurse 4.3.0 (BSD-2-Clause, full tagged
source header; bundled package metadata/version export), and @vscode/l10n
(MIT, exact source-reference license from tag l10n/v0.0.18; runtime version
not established) are mapped in embedded.json. Both npm archive root-notice
gaps remain recorded as archive facts. Remaining nested review open.

Retained Ace worker reference notices: all 15 source-lock candidates are now
mapped. The 13 additional candidates retain their original npm root notices
(15 files, including two Microsoft third-party notice files). Candidate npm
archive/member SHA-256 and SRI are verified in the build-time evidence gate.
No inferred exact versions or active OSV queries. The estraverse source
copyright header is retained separately; LLVM-derived code remains open.
JSON language service includes the BSD-2-Clause glob matching notice in its
original LICENSE.md. Microsoft generic third-party notices are preserved
without assuming a specific LGPL dependency. See ACE_WORKER_ATTRIBUTION.md.

All 15 retained replacement-worker package versions are now identified by
byte-exact reconstruction of the shipped minified runtime from pinned
archives and original lock paths (research #1; reviewed CRLF-to-LF relation
for all five published unminified forms). This supersedes earlier candidate
version-only notes. Exact versions/PURLs and main OSV queries now reflect
these identities. Original notices remain, including source references for
esrecurse and @vscode/l10n; source-level nested terms and independent review
are not cleared by this reconstruction. Native base is separate.

Additional retained attribution: estraverse includes an MIT-attributed LLVM
libc++ algorithm adaptation; historical full dual MIT/UIUC notice and
CREDITS.TXT retained, MIT elected for that fragment (no exact libc++ package
version claim). Both 2014 REx v5.30 generator headers and modern Apache-2.0
reference retained for XQuery/JSONiq lexer modes. Historical generated output redistribution confirmed by the REx author
in issue #80; grammar provenance and exact browser-pack version remain open.
Dracula theme carries its own MIT notice, now also distributed verbatim.

XQuery/JSONiq loader: browser-pack MIT prelude fragment separately mapped,
with original notice; exact package version unspecified (shared blob across
multiple tags). XQLint common lexer and both language wrappers verified
against pinned source with two exact require renames. Historic REx output redistribution confirmed for the two generated
files, including modified/minified copies under Apache-2.0, with no
additional requirements (author response: https://github.com/GuntherRademacher/rex-parser-generator/issues/80#issuecomment-7224280132).
Existing notices retained; grammar provenance remains open.

Historical theme attribution: Tomorrow (Chris Kempson, MIT, five themes,
Ace PR #432), Solarized (Ethan Schoonover, MIT, two themes, initial import
69778adb; Ace wrapper BSD relicensing PR #917), and Gruvbox Hard port
(Brian Reilly, MIT, two themes, Ace PR #3673) now retain pinned original
whole-file notices. Nine historical TextMate inputs match current Ace Git
blobs. Original Gruvbox rights, ordinary Gruvbox CLA/reintroduction and
historical wrapper copyright remain OPEN. No external package version or
full historical license clearance asserted. See embedded.json.

Historical Gozalishvili 2011 theme wrapper notice retained for Ambiance,
Chaos and Gruvbox (MIT permission text labelled BSD in original header).
Bounded source relations recorded; original color scheme rights and Gruvbox
CLA history remain open.

Original Gruvbox color scheme: Pavel Pertsev (morhetz), declared MIT/X11 in
README at the initial implementation commit 317ca28 (2012-12-02), retained
at descendant ef8864bb. Attribution covers the original scheme behind the
three retained Gruvbox variants. `gruvbox-original-license-reference.txt`
is the exact historical declaration excerpt. The separate
`gruvbox-original-mit-standard-reference.txt` is an unmodified SPDX MIT
license template with placeholders, NOT an original Gruvbox copyright
notice or a license grant from SPDX. Earlier original-license uncertainty
is superseded; exact historical port lineage and ordinary Gruvbox CLA /
2017 contribution independence remain open. No license clearance implied.

Nord Dark (Sven Greb / Nord) and One Dark (GitHub / Atom One Dark Syntax)
original MIT whole-file references retained. Ace PR #4203 and #4415
explicitly grant permission for the respective contributions. Historical
BSD Ace wrappers and current source pins recorded; exact original revision
and any intermediate port lineage remain open. See embedded.json.

GitHub Light Default: PR #5597 identifies official GitHub VS Code theme.
Historical Primer MIT LICENSE (Copyright (c) 2020 Primer) retained verbatim
as github-vscode-theme-mit.txt. Exact variant/version open. Applies only to
this theme, not legacy GitHub or GitHub Dark. See docs/ace-theme-dispositions.json.

SnipMate snippets collection (honza/vim-snippets): historical January 2013 MIT
LICENSE and its referenced AUTHORS file retained verbatim. The embedded
record maps historical MIT material in 33 retained Ace payloads: 22 exact
decoded matches (including cpp -> c_cpp and make -> makefile) and eight
modified descendants with reconstructed deltas and exact historical
endpoint-to-current relations, plus EDIFACT (two Java trigger replacements)
and Liquid (historical HTML payload with a fixed additional prefix), plus
retained Java material in Wollok (16 unique ordered shared spans). This is not a blanket MIT license for
Ace modifications, wrappers or other snippets; additional inputs and
contribution rights remain review-open. See docs/ACE_SNIPPET_RESEARCH.md.
No external version, PURL, full license clearance or risk acceptance is asserted.

TextMate Io snippets: repository-scope historical TextMate Bundle License
(including its file-specific exceptions) retained as textmate-io-bundle-license.txt.
All ten source dictionaries match the current Ace Io array. LicenseRef-TextMate-Bundle
is a source-specific custom identifier, not an MIT or BSD declaration.

Vala TextMate snippets: MIT LICENSE (Copyright (C) 2014 Matt Butcher) retained
verbatim as vala-tmbundle-mit.txt. All 31 source dictionaries match the current
Ace Vala array and the 2014-11-13 licensed tree is identical to the pre-import
2013 Snippets tree. The grant postdates Ace import; earlier Daniel Lucraft rights
remain open. Both mappings are partial and limited to snippet payloads; no
version, PURL, grammar rights, full clearance or risk acceptance asserted.
