# Ace snippet attribution — R5.3a initial source inventory

Status: **research / review-open**; not a disposition matrix or license clearance.
Baseline Configurator HEAD: `684ffe960f520808d40882945b903362c552fd79`. PR #36 remains Draft / HOLD.
Pinned Ace source: [68d7fd1c0f5ac50cdb610bf06b86074eab3be652](https://github.com/ajaxorg/ace/tree/68d7fd1c0f5ac50cdb610bf06b86074eab3be652).
Pinned Ace-builds commit: `c9ea63c0a0a436fbb477c918d6736644f77cab9f`.

## Scope and method

The existing native audit has already demonstrated static payload equality for
52 nonempty assets and exact loader/source-absence relations for 150 generated
empty stubs. This pass separately computed SHA-256 of the exact ASCII minified
stub template from `scripts/audit_ace_native_payloads.cjs` for each of the 202
`snippets/*.js` entries in `docs/ace-builds-1.45.2-lock.json` at the baseline.
150 hashes matched and the other 52 were fetched at the pinned Ace source
commit. The SHA-256 implementation was checked against the standard abc vector.
This was an interactive research calculation, not a new automated repository
gate or a rerun of the native audit.

GitHub contents API returned the source Git blob IDs below. Fifty payload
modules are separate .snippets.js files; io and vala instead use inline
exports.snippets arrays in their .js modules. JSONiq and XQuery have legacy
lib/ace paths. The other wrapper modules have not all been individually
examined in this pass; current payloads were searched for indicative
copyright/license/author/attribution markers, not exhaustively adjudicated.
No JS was executed. All rows are OPEN for historical lineage and legal review.

Root [Ace LICENSE](https://github.com/ajaxorg/ace/blob/68d7fd1c0f5ac50cdb610bf06b86074eab3be652/LICENSE)
blob `4760be2a6220cf545129b233e20574f2a7bb630e` is BSD-3-Clause
(Ajax.org B.V., 2010). It is the upstream project declaration, not
proof that every external snippet input is covered.

## Payload inventory

The historical candidate column is only a path/name lead from the 2013
SnipMate import (see below), not a demonstrated content relation.
A dash means no specific license/author marker was identified by the
initial heuristic (or inline payload not comprehensively scanned), not that
no additional terms exist.

| Shipped asset name | Pinned Ace payload path | Git blob | Historical lead / observation | Initial marker observation |
| --- | --- | --- | --- | --- |
| abc | `src/snippets/abc.snippets.js` | `41035c73a79246055c9593ae4baaf27b87bc3e6d` | History open | — |
| actionscript | `src/snippets/actionscript.snippets.js` | `b10121bd8310024585ed5d9c56349828616dce76` | 2013 SnipMate import: same basename; relation open | — |
| c_cpp | `src/snippets/c_cpp.snippets.js` | `e1eac56f12283df6ad2cbfa0155f977f48e377ac` | 2013 import has c and cpp separately; merge lineage open | — |
| cedar | `src/snippets/cedar.snippets.js` | `ca5eb44499acbf392db9df314818a607db4c2878` | History open | — |
| cedarschema | `src/snippets/cedarschema.snippets.js` | `ba70be9b386bf7bbac399e3ac3a1eca84cc1b5c9` | History open | — |
| clojure | `src/snippets/clojure.snippets.js` | `94ad67acbb52e0a52bdc73cb28f289cfd866e363` | 2013 SnipMate import: same basename; relation open | — |
| coffee | `src/snippets/coffee.snippets.js` | `bae3b1f30e39ba19b24fa8d0572fa9a12d481bad` | 2013 SnipMate import: same basename; relation open | — |
| csound_document | `src/snippets/csound_document.snippets.js` | `ba8c191728befe34749e3f6c9a137f67387d9eab` | History open | — |
| csound_orchestra | `src/snippets/csound_orchestra.snippets.js` | `569378661e1221e3372c5f70ab5f402ec67d9ea1` | History open | — |
| css | `src/snippets/css.snippets.js` | `773b7d5bcb873f30a3a5c13cf6fdfe49c14ae7d5` | 2013 SnipMate import: same basename; relation open | — |
| dart | `src/snippets/dart.snippets.js` | `fa6a8452fcd7faec4f7aa1a70d0a93fc47059f55` | 2013 SnipMate import: same basename; relation open | — |
| diff | `src/snippets/diff.snippets.js` | `ed377fe0effec9f945d3ab406b4e0e35ef3f6af3` | 2013 SnipMate import: same basename; relation open | Author placeholder (line 7) |
| django | `src/snippets/django.snippets.js` | `a8ddfe0fdee63b598b46829eb6034b971ceceb8d` | 2013 SnipMate import: same basename; relation open | — |
| drools | `src/snippets/drools.snippets.js` | `a4fe36f71d5850ffb061dcab8c4dab3097d457bf` | History open | — |
| edifact | `src/snippets/edifact.snippets.js` | `afe85e064b4594d344b7b101d82cefc42460565f` | Java-like template marker; compare historical payload to java | Generated @author template (line 143) |
| erlang | `src/snippets/erlang.snippets.js` | `a42e85530b6763cf0703125dcdecb024fac32a1a` | 2013 SnipMate import: same basename; relation open | — |
| fsl | `src/snippets/fsl.snippets.js` | `099f8e1004b4c55ffbef1c9a2c47675aec6841b1` | MIT string is machine_license template field, not a source license | machine_license template (line 4) |
| gobstones | `src/snippets/gobstones.snippets.js` | `4bf2fa6b6ce71bc6ad4e0215984426ccd5f8798d` | History open | — |
| graphqlschema | `src/snippets/graphqlschema.snippets.js` | `5fa4ce4f53dd90c0cd4c9f01cacc45cca1e91739` | History open | — |
| haml | `src/snippets/haml.snippets.js` | `53dcc1e812e53bbb6bee3fee4fa88876f75c5787` | 2013 SnipMate import: same basename; relation open | — |
| haskell | `src/snippets/haskell.snippets.js` | `4816ad347223dfaad96d1144d973219ec2d043f6` | 2013 SnipMate import: same basename; relation open | Copyright and License placeholders (lines 6–7) |
| html | `src/snippets/html.snippets.js` | `8fd5affd801799b79f14f645c7ddd3c95dc1a1da` | 2013 SnipMate import: same basename; relation open | — |
| io | `src/snippets/io.js` | `500eb8b25ca88e35a0dc4ce97011c577a72ed057` | Inline array; TextMate-format metadata; origin open | — |
| java | `src/snippets/java.snippets.js` | `3bec07b58d5aec26436d4e4a5ddf0e3597ed830f` | 2013 SnipMate import: same basename; relation open | Generated @author template (line 143) |
| javascript | `src/snippets/javascript.snippets.js` | `6e4d29a4dbab301680f762d7bd0838059ebe0d55` | 2013 SnipMate import: same basename; relation open | — |
| jsoniq | `lib/ace/snippets/jsoniq.snippets.js` | `c0ba6047ab9b247931c5eb9bf3c09e5052effbfe` | Legacy path; identical payload blob to xquery | — |
| jsp | `src/snippets/jsp.snippets.js` | `deeb529b6b7d7287c58e050bbb14dec076ee94d2` | 2013 SnipMate import: same basename; relation open | — |
| liquid | `src/snippets/liquid.snippets.js` | `7c72fe03a9fce8c65f6b486d83fbc88f618a97b5` | History open | — |
| lsl | `src/snippets/lsl.snippets.js` | `7e33bdc2855b5f7e3ff0cb5d4f5f546dc809ccf5` | History open | — |
| lua | `src/snippets/lua.snippets.js` | `92a188db337d7a01d404eb456286a89c3c00664f` | 2013 SnipMate import: same basename; relation open | — |
| makefile | `src/snippets/makefile.snippets.js` | `a7c9cfeb7843eba2cfce8f573506facd8aa98aab` | 2013 import has make; rename lineage open | — |
| markdown | `src/snippets/markdown.snippets.js` | `26ad61345a037c5197d28ef1798a252f585ae149` | 2013 SnipMate import: same basename; relation open | — |
| maze | `src/snippets/maze.snippets.js` | `beb0a00d4bf6e60605b658140f4089d64f7fc216` | History open | — |
| perl | `src/snippets/perl.snippets.js` | `1b3bf183786e41160a1d4f9a7d815b77461e76da` | 2013 SnipMate import: same basename; relation open | — |
| php | `src/snippets/php.snippets.js` | `987e34d04474aa6cb5ffa64a7bb31731f60d0f8d` | 2013 SnipMate import: same basename; relation open | Generated @author and @copyright fields (lines 108–194) |
| python | `src/snippets/python.snippets.js` | `5d556cf6f7d6f54eb41d815b1b9862e9e80397e7` | 2013 SnipMate import: same basename; relation open | Author placeholder (line 11) |
| r | `src/snippets/r.snippets.js` | `dbac55301a26b64aedf8342d4b883a81ee44a4c9` | 2013 SnipMate import: same basename; relation open | — |
| razor | `src/snippets/razor.snippets.js` | `f8172f131c853ec4ffd11a305efac355f0b30d8f` | History open | — |
| robot | `src/snippets/robot.snippets.js` | `41d3316b49a64bbb812a5c63e5f0bb7b86bf8956` | History open | — |
| rst | `src/snippets/rst.snippets.js` | `25e8f1690021aae84ee99aa466801ef03b7ced23` | 2013 SnipMate import: same basename; relation open | — |
| ruby | `src/snippets/ruby.snippets.js` | `405d8224c39827f5ae8f51db1fdd4de9a8d842dd` | 2013 SnipMate import: same basename; relation open | — |
| sh | `src/snippets/sh.snippets.js` | `8c5e7f6c288d2078e4d4dfe9bc481ab536b3a7fe` | 2013 SnipMate import: same basename; relation open | — |
| snippets | `src/snippets/snippets.snippets.js` | `c87a3ddf3405495c12ef422533301a634d7fd4df` | 2013 SnipMate import: same basename; relation open | — |
| sql | `src/snippets/sql.snippets.js` | `8ad44a2fe7bf05540c20f7838dfe329b6c39d837` | 2013 SnipMate import: same basename; relation open | — |
| sqlserver | `src/snippets/sqlserver.snippets.js` | `18328505dc5a94e2c112e61e2413fbc2d3fda1c9` | History open | Author placeholders (lines 38, 56) |
| tcl | `src/snippets/tcl.snippets.js` | `ecfb33b3e89b297c5520a5945c0ea0b51f25277a` | 2013 SnipMate import: same basename; relation open | — |
| tex | `src/snippets/tex.snippets.js` | `551abde4957b0b3d81e64b18e93b8fe0d1507c51` | 2013 SnipMate import: same basename; relation open | — |
| textile | `src/snippets/textile.snippets.js` | `396439e19c2729f91addc113ccbd0ba97e8ff9f6` | 2013 SnipMate import: same basename; relation open | — |
| vala | `src/snippets/vala.js` | `b1230e6871d9f08406d16dd862f371c36bbabc6f` | Inline array; source origin open | — |
| velocity | `src/snippets/velocity.snippets.js` | `b91238f3a298fa5d64439579c2e535de0f63c933` | History open | — |
| wollok | `src/snippets/wollok.snippets.js` | `04d3c58efa7c958cb98aa84e76bcbdcc0bb6dd8b` | History open | — |
| xquery | `lib/ace/snippets/xquery.snippets.js` | `c0ba6047ab9b247931c5eb9bf3c09e5052effbfe` | Legacy path; identical payload blob to jsoniq | — |

## Historical evidence and priority leads

- [Ace d16daddc5ea91e578fafde6c9c17b41cdb036579](https://github.com/ajaxorg/ace/commit/d16daddc5ea91e578fafde6c9c17b41cdb036579), 2013-03-17, commit message `add snipmate snippets`: actual changed-file list includes 28 same-basename historical payloads corresponding to retained assets, plus separate c/cpp and make paths. This is evidence of an import event, not of the exact upstream SnipMate collection or its licensing. Trace those inputs and intervening Ace changes; preserve notices from their actual historical scope. In particular investigate vim-snipmate vs snippets collections, without assuming that plugin license governs data files.
- [Ace b8eb5a1feca2691cf1807c3f61c98c44859da02e](https://github.com/ajaxorg/ace/commit/b8eb5a1feca2691cf1807c3f61c98c44859da02e), 2013-03-17, `add support for TextMate snippets`: introduces tool/tmsnippets.js and demo JS snippet data. This establishes a historical converter/demo, not current payload ancestry. Current converter blob `febc7946e892692859402053b45369033c516a3b` reads tmSnippet, sublime-snippet and plist inputs; converter capability does not imply all these origins occur in shipped data.
- io and vala are inline arrays, not missing payloads. Their upstream input needs individual tracing. JSONiq and XQuery are two shipped names with the same source payload blob; do not collapse the distribution inventory or infer snippet rights from the REx output grant.
- Author/copyright/license strings in diff, edifact, fsl, haskell, java, php, python and sqlserver are template content or placeholders, not reliable declarations of ownership or terms for the snippet collection. The similar Java/EDIFACT marker is a lead to compare payload histories, not a claimed copy relation.

## Remaining work

Obtain per-path introduction/change history and immutable historical payload
and license blobs; compare upstream collections at the corresponding
revisions with bounded documented transformations; inspect wrapper and
per-file notices; resolve attribution obligations (or request a maintainer
decision where unresolved). R5.3b separately covers the shared empty-stub
template license. R5.3c–g cover external lineage, notices, dispositions,
SBOM/research gate and independent exact-HEAD acceptance.

No runtime, vendor, SBOM, notices, accepted license dispositions or curated
profile changes are authorized by this document. No issue or release gate
is closed. The baseline CI and supplied Round 6 approvals do not transfer
to this documentation commit. Correction-HEAD artifact content inspection
remains separately open.


## R5.3a follow-up — SnipMate historical source and current payload comparison

Research baseline `4861322a331812b98f0606f8ed4eff5173491e57`. This section supersedes initial
name-only leads for the investigated group; earlier observations are
retained as historical evidence.

### Immutable historical match

Ace import [d16daddc5ea91e578fafde6c9c17b41cdb036579](https://github.com/ajaxorg/ace/commit/d16daddc5ea91e578fafde6c9c17b41cdb036579)
(2013-03-17, add snipmate snippets) contains 31 relevant historical files
under `lib/ace/snippets/*.snippets`: 28 same-basename leads plus c, cpp
and make. GitHub contents API comparisons gave 27/31 matching blob IDs
at [honza/vim-snippets 91f24bd88b9aaf040eeea78024e1e2d786219a2b](https://github.com/honza/vim-snippets/tree/91f24bd88b9aaf040eeea78024e1e2d786219a2b)
(2013-03-15). Line comparison found two changed HTML lines, JavaScript
loop/object-template edits, four added Python property lines, and
Ruby additions and a spacing change.

All **31/31** historical blob IDs match [honza/vim-snippets 02593f7d57b4944bd857e0aeacfcd5410c0e81f2](https://github.com/honza/vim-snippets/tree/02593f7d57b4944bd857e0aeacfcd5410c0e81f2)
(2013-01-17), paths `snippets/<name>.snippets`. The four previously
different blobs also match snapshot `6c1721a78b79067f2ec21ea1021a3bf4c4ce1e4e`
(2012-12-21; only those four checked there). These are content-matching
snapshots, not proof of a unique checkout or direct copying event.
No complete import-directory closure is claimed.

### Historical license evidence

Files fetched at the January matching snapshot:

| File | Git blob |
| --- | --- |
| [LICENSE](https://github.com/honza/vim-snippets/blob/02593f7d57b4944bd857e0aeacfcd5410c0e81f2/LICENSE) | `495ced27810b679dad1c75375e48db9ae9c9c9aa` |
| [AUTHORS](https://github.com/honza/vim-snippets/blob/02593f7d57b4944bd857e0aeacfcd5410c0e81f2/AUTHORS) | `1261dc82ddfea218e2a61077fb4ed0d64b42c2bb` |
| [README.md](https://github.com/honza/vim-snippets/blob/02593f7d57b4944bd857e0aeacfcd5410c0e81f2/README.md) | `a242eca196cc56c47121319f1a815f6754d78181` |

LICENSE contains MIT terms and the literal copyright line
`Copyright (c) 2011 see AUTHORS`. README explicitly declares MIT
for the snippets collection. Preserve both original LICENSE and
AUTHORS when promoting the notice; do not substitute a generic MIT
template or the plugin license. This establishes the historical
collection's declaration, not independent clearance of all earlier
third-party contributions.

### Import-to-current static payload comparison

Fetch historical Ace raw snippets and current payload modules at the
pinned Ace source commit above. Require a single complete
module.exports template-literal assignment; reject unescaped interpolation
and unknown escapes; decode only escaped backslash, backtick, dollar,
n/r/t and two-digit xHH. No JS execution, trimming or whitespace
normalization for equality. This was interactive research, not an
automated repository gate. For differences, old/new/LCS counts are
exact-line longest common subsequence lengths using LF splitting,
including final empty lines; they are similarity evidence only.

| Historical basename | Shared January / import blob | Current asset | Import-to-current comparison |
| --- | --- | --- | --- |
| actionscript | `af9611c3f6deb8a640817b1739822c52b32aff9b` | actionscript | Exact decoded text |
| clojure | `e247debf68403a3adbb7258033123ac04363c278` | clojure | Exact decoded text |
| coffee | `83b77ebab2e56351e9d5581f741a21734aaed3ec` | coffee | Exact decoded text |
| css | `72212d2d8dde088fda8e6ec2f75373e9cba11259` | css | Exact decoded text |
| dart | `6f0b8ac5e5ba87851513a3f9dd2b808e2e70ad81` | dart | Different; old / new / LCS lines 83 / 84 / 76 |
| diff | `7ba288ded0c8e8aefb16d73560ec7da102c7486b` | diff | Exact decoded text |
| django | `8296cce25dfd071313a1b5bd8a76d7293be867b8` | django | Exact decoded text |
| erlang | `acc6fd195eebf7ab6d99fe3ff7a23bfeb461e4b0` | erlang | Exact decoded text |
| haml | `61e9cf28779936f1acb9acdd0dabae6d07ce6042` | haml | Exact decoded text |
| haskell | `bcda8a5b4974c2de4037ddb18ad05ef04a5340a0` | haskell | Exact decoded text |
| html | `0f75efd08a2c7917bc9b880a7952de97479fb3ec` | html | Different; old / new / LCS lines 829 / 854 / 824 |
| java | `854f14ac22f148309d4f9ec450fda38244ede6ec` | java | Exact decoded text |
| javascript | `fc845fa02198562dda841591126d2eb107fd2ae8` | javascript | Different; old / new / LCS lines 157 / 196 / 121 |
| jsp | `a5239f5eb13c3bd7fa0c7b6b9c4873ab6a539399` | jsp | Exact decoded text |
| lua | `34ae25eb6ae64b914b8ce0b3bce3c82c08d65ef2` | lua | Exact decoded text |
| markdown | `e4efd3c2d014fe8a9b6ba92fd08e1483aea5d1c3` | markdown | Different; old / new / LCS lines 88 / 89 / 83 |
| perl | `9cebedeacf033a78d8b3fab3ee4e16033b4efc7d` | perl | Exact decoded text |
| php | `e861a5be96827edc8a2182d76d864b5b4a8a6b60` | php | Different; old / new / LCS lines 378 / 384 / 337 |
| python | `dd2e8123dcc8db911c92a260a771f2116146ff57` | python | Different; old / new / LCS lines 159 / 159 / 156 |
| r | `71186e35b47f2aa8d46071d89ab9ffcfc727a888` | r | Different; old / new / LCS lines 122 / 122 / 117 |
| rst | `97845de3f0f6d140b670e606e9cbea20901ff2d2` | rst | Exact decoded text |
| ruby | `0500aaa13d52594f671f85eba5765eccd1c7d0a9` | ruby | Exact decoded text |
| sh | `9a48eb514c5306d2fa7223a0e45703381d7b69bd` | sh | Different; old / new / LCS lines 84 / 84 / 83 |
| snippets | `4223fa3943bc1438622fbd28b94cb3dcc1eab520` | snippets | Exact decoded text |
| sql | `eb4b37caf1cd65c7218c05f22fac3b6063244d94` | sql | Exact decoded text |
| tcl | `1fe1cb960eb2f2c83c879bd24d5eada9b8c6501c` | tcl | Exact decoded text |
| tex | `10fa82eff7ac04fb9114ecfd4319f0e6ea8f3037` | tex | Exact decoded text |
| textile | `c78d6ec81b5252c92c3646f3d563cea702ccf953` | textile | Exact decoded text |
| c | `c476de4abf842c2490ae6842c35d32563c71f8f6` | c_cpp (candidate only) | Not equal; old / new / LCS lines 236 / 132 / 12; no separate C attribution inferred |
| cpp | `c3e19fe9370f0d0f80f89a5334719d4664225b59` | c_cpp | Exact decoded text |
| make | `43648136382429fc97d61964c9dceaf63fd7d1ea` | makefile | Exact decoded text |

**22/30** current assets match historical raw snippet text exactly:
20 same-basename assets plus c_cpp from cpp and makefile from make.
The original C payload is not an exact match; do not describe c_cpp
as the merged C and C++ payload. The other 8/30 current candidates
differ with substantial line overlap; intervening edits and additional
rights/notices remain open. For the other 22 of 52 nonempty assets,
this comparison establishes no SnipMate relation.

Proposed disposition for independent review: historical collection MIT
attribution supported for 22 exact current payloads; investigate the
eight modified descendants and retain applicable historical attribution
after edit-history review. No blanket MIT assignment to Ace wrappers
or all 52 snippets, exact source version, PURL, automated provenance
gate, final license clearance or merge approval. Wrapper and external
origin checks remain open; final notice/inventory promotion belongs to
R5.3d–f. No shipped files, SBOM, notices or curated profile changed.

### Baseline verification

At `4861322a331812b98f0606f8ed4eff5173491e57` GitHub workflow metadata confirmed all three runs
completed successfully: Offline foundation 46061855401, migration
rehearsal 46061855442, retained/native research 46061855452. Job logs,
ZIP content and independent review were not checked in this increment.
Results do not transfer to the follow-up commit; 684ffe9 artifact
content review remains separately OPEN.


## R5.3a follow-up — modified snapshots and scoped notice promotion

Baseline `355327e62b5e785ff2b26207059d839cbb77497d`: all three CI workflows completed SUCCESS (46062801461,
46062801378, 46062801390); metadata only, no archive inspection or
independent review in this increment.

All eight modified SnipMate candidates now have immutable Ace historical
raw payloads exactly matching the current decoded template literals.
Each snapshot root LICENSE was fetched and had the same BSD-3-Clause blob
`4760be2a6220cf545129b233e20574f2a7bb630e`.
GitHub commit patches were inspected; bounded line-position/context
checked patch replay reproduced the exact historical endpoint from the
import for four assets (Dart, Markdown, Python, Shell). This is a
net-delta proof, not exhaustive path history, individual grants, or
third-party license clearance. The other four have intermediate changes
not completely reconstructed.

| Asset | Ace snapshot | Historical raw payload blob | Patch evidence |
| --- | --- | --- | --- |
| dart | [93673bbe](https://github.com/ajaxorg/ace/blob/93673bbe8b0a1e90a773aa3dd94fe8fa112f7af5/lib/ace/snippets/dart.snippets) | `14a1c3e5939d691de25aa390ff7f17c4e5b42a70` | 5746c2001ced240c4e827eb51aef6a63176777a6 patch exact from import |
| html | [96850288](https://github.com/ajaxorg/ace/blob/96850288dca9b632aaa79b4f9bdf1305ae5d9694/lib/ace/snippets/html.snippets) | `5f0e46b476083398e70a53e7d9630383bfb4fe99` | d9b38ac adds HTML5 variants; final video fix; complete intervening delta open |
| javascript | [2d0b980c](https://github.com/ajaxorg/ace/blob/2d0b980c65966e45260ba341e176b9cde0c57399/lib/ace/snippets/javascript.snippets) | `83b15aab6f41fdf08692dd8e9167a5b95fc266c5` | 3d43f42, f87f542, 202ecaac earlier changes; complete intervening delta open; 5d7b65c hex escapes preserve decoded text |
| markdown | [3c6cd4d1](https://github.com/ajaxorg/ace/blob/3c6cd4d16f89de0531d7e8f06c5e791839ab9eb6/lib/ace/snippets/markdown.snippets) | `a5110fc9a3d79f0aa98796237773393e4a836e97` | patch exact from import; original Octopress mention needs separate review |
| php | [f36ade16](https://github.com/ajaxorg/ace/blob/f36ade1647e90d20480d93ac6da6169fc55e65e5/lib/ace/snippets/php.snippets) | `12b6c358d6927bd245ac3a8e1f9a5fe47f8f4b2a` | 62c5141 filename changes; final context changes; direct patch from import differs, remaining chain open |
| python | [eac48f51](https://github.com/ajaxorg/ace/blob/eac48f519040e8e2d17dd1a5b76c2818ecf58cd1/lib/ace/snippets/python.snippets) | `347bbdebfd9d13e17cdd0131523eef30db186a26` | patch exact from import |
| r | [f17c67cd](https://github.com/ajaxorg/ace/blob/f17c67cd01316d4fdbbd5625594d81e28c894083/lib/ace/snippets/r.snippets) | `948542f5bbacc0de657e65d95dc2d54c52c0f13e` | sapply fix; direct patch from import differs, remaining chain open |
| sh | [b6463844](https://github.com/ajaxorg/ace/blob/b6463844b04758745f99b1553416f4cf4b8ad013/lib/ace/snippets/sh.snippets) | `305fb661ed25a75093d8e168f46deb012f662c07` | patch exact from import |

Retain original MIT attribution for historical material; root BSD does
not supersede the original MIT license. The historical HTML change
contains CDN URL examples in snippet content; no external runtime
requests or bundled CDN library identity are inferred from this alone.
Review generated snippet behavior separately if needed.

Promote only the 22 exact payload matches to a partial library record
`ace-snipmate-snippets` in embedded.json, with null version/ecosystem
(no PURL), original whole LICENSE and AUTHORS as separately pinned
notices. Preserve the eight modified candidates as review-open;
the original notice is retained, but their additional rights and
full scope remain unresolved. No blanket MIT claim for wrappers or
other snippets. A new named source relation
`ace-snippet-template-literal` compares the complete decoded source
text against historical raw input in the existing networked evidence
gate. All 22 raw/source Git pins and imported blob evidence are bound;
unit regressions cover exact scope, notices, SBOM and adverse literal
forms. This is not a new automated historical patch replay gate.
No vendor/curated runtime bytes changed. Final R5.3 disposition matrix,
empty stubs, remaining 22 payloads, exact-HEAD CI/artifacts and independent
review remain open. No issue or merge/release gate closed.


## R5.3a follow-up — four remaining modified payload histories and scoped expansion

Baseline Configurator `0790b24516656b00465d7d522565dad3fbc9c28c`: all three exact-HEAD workflows SUCCESS after rerun of the failed Routing/inventory job (46063743806; initial HTTP 503 Backend.max_conn reached in upstream evidence fetch; no code relaxation), rehearsal 46063743784, research 46063743797. Workflow metadata verified; archive content and independent review remain open.

GitHub REST path history, `GET /repos/ajaxorg/ace/commits?sha=<endpoint>&path=lib/ace/snippets/<name>.snippets&per_page=100`, returned the import plus 3 HTML, 10 JavaScript, 3 PHP and 2 R changes. Replayed each file-specific patch from the preceding path snapshot in chronological ancestry order (not author-date order), requiring exact old and new hunk positions, counts and context; no fuzzy matching, normalization or JS execution. Every reconstructed complete text equals the next immutable snapshot (18/18). All 17 distinct change commits have the same root LICENSE blob `4760be2a6220cf545129b233e20574f2a7bb630e` (BSD-3-Clause). This is path-history/net-change evidence, not proof of every merge parent, contributor grant or independent origin of newly added material. The API's path-history simplification is not exhaustive DAG traversal.

| Asset | Ace change commit | Resulting raw blob | Added / removed lines |
| --- | --- | --- | --- |
| html | [d9b38ac3](https://github.com/ajaxorg/ace/commit/d9b38ac378d0dea6e1ca820c0e8294f04c46010a) | `20a73d72e339c352216ce4803e6c5b842f7d7212` | +28 / -1 |
| html | [9d930d82](https://github.com/ajaxorg/ace/commit/9d930d829d263c02bb624edcf9b28b04e194943b) | `e3286ab04550fa1874d8c3e558b6f64276cf2517` | +1 / -3 |
| html | [96850288](https://github.com/ajaxorg/ace/commit/96850288dca9b632aaa79b4f9bdf1305ae5d9694) | `5f0e46b476083398e70a53e7d9630383bfb4fe99` | +1 / -1 |
| javascript | [3d43f42f](https://github.com/ajaxorg/ace/commit/3d43f42f8ab1b5239ad4359467b5469d349fe2c3) | `73f7b93f24239f36ed2ec3630e94f5fbfd387552` | +41 / -19 |
| javascript | [f87f542c](https://github.com/ajaxorg/ace/commit/f87f542c8e1bbec23637d4c62ec740c834a97311) | `fe1d5bcf78110deca583e027e7960be8f689c1f0` | +44 / -18 |
| javascript | [943e690b](https://github.com/ajaxorg/ace/commit/943e690bf60bd9d973532cf6ab7d4966f280dd11) | `b5c4f72c4df4890ecc06fd14cc1bdd75ad9d4e9e` | +15 / -13 |
| javascript | [47ba638f](https://github.com/ajaxorg/ace/commit/47ba638f4bc49d1e9b0ec73b13ef3514918d8581) | `0019314e6d64103f83f8debe02153ea36acf6f68` | +7 / -20 |
| javascript | [336e30c6](https://github.com/ajaxorg/ace/commit/336e30c62d84378abe35d0dc711c24d90f32c112) | `313e61196f26fd5197f4e87821c9c7a913b9b4f7` | +7 / -9 |
| javascript | [19ea0fe9](https://github.com/ajaxorg/ace/commit/19ea0fe979462838d93f58df13a7364ffa89f8f1) | `813876e277f214f5e40b1f625782b1d1c1ab5538` | +1 / -1 |
| javascript | [f9ed2055](https://github.com/ajaxorg/ace/commit/f9ed205557aa979d4d1b05d2878b7438add4367d) | `9c2ad1b2650ec7a40c31f7f584b0a184b845eb39` | +4 / -4 |
| javascript | [e7fa7eb3](https://github.com/ajaxorg/ace/commit/e7fa7eb390d0e9965366b4f5919eafcefde3cbf9) | `d55c86c6dc49833709710a3efa5f31da3bd245a9` | +3 / -0 |
| javascript | [28943dcf](https://github.com/ajaxorg/ace/commit/28943dcf1d594c957d21a9e3342938aa89e3b3f5) | `287862eb40e4f3b642a71a5414bc34f3dc1d015b` | +5 / -4 |
| javascript | [2d0b980c](https://github.com/ajaxorg/ace/commit/2d0b980c65966e45260ba341e176b9cde0c57399) | `83b15aab6f41fdf08692dd8e9167a5b95fc266c5` | +2 / -2 |
| php | [0479acfe](https://github.com/ajaxorg/ace/commit/0479acfea78f4fb3f4cd8e9c122b41748f5844e3) | `97f17bc18f011235383707a9850dde0d85ac4154` | +1 / -1 |
| php | [62c51413](https://github.com/ajaxorg/ace/commit/62c514135d5ebd912c3a0c8e7c200b59ad0f6fca) | `8d11a2815ced35d9610e8ec3a8f6ba22f5fa4268` | +6 / -6 |
| php | [f36ade16](https://github.com/ajaxorg/ace/commit/f36ade1647e90d20480d93ac6da6169fc55e65e5) | `12b6c358d6927bd245ac3a8e1f9a5fe47f8f4b2a` | +40 / -34 |
| r | [0479acfe](https://github.com/ajaxorg/ace/commit/0479acfea78f4fb3f4cd8e9c122b41748f5844e3) | `cfe482bc5508f76e221cced1ac190a83589be294` | +4 / -4 |
| r | [f17c67cd](https://github.com/ajaxorg/ace/commit/f17c67cd01316d4fdbbd5625594d81e28c894083) | `948542f5bbacc0de657e65d95dc2d54c52c0f13e` | +1 / -1 |

All eight historical endpoints were freshly fetched and their complete decoded current template literals matched exactly (8/8). The previous four direct net-delta proofs (Dart, Markdown, Python, Shell) remain separately described above. PHP endpoint full revision is `f36ade1647e90d20480d93ac6da6169fc55e65e5`. HTML CDN URLs are snippet text, not bundled or automatically fetched libraries; JavaScript class/module templates have earlier demo lineage to assess if needed, and Markdown Octopress mention remains open. Low priority PHP/R do not justify a weaker license standard; no exclusion or runtime profile change is necessary on the basis of the present reconstruction. Revisit exclusion only if unresolved rights warrant a maintainer-approved change.

Promote historical MIT attribution to all 30 demonstrated SnipMate descendants (22 exact and eight modified). Existing MIT LICENSE and AUTHORS bytes stay unchanged. The partial component maps historical material, not the entire modified file under MIT. Add the eight original collection/import pins and endpoint-to-current static relations to the existing networked verification; unit regression separates the exact and modified source sets. Patch replay is interactive evidence, not a new automated history replay gate. Additional source rights, wrapper origins, 22 other nonempty assets, 150 empty stubs, dispositions, artifact inspection and independent exact-HEAD review remain OPEN. No runtime, vendor, license text or curated profile change; no final clearance or merge/release approval.


## R5.3a follow-up — remaining 22 nonempty payloads, historical endpoints and two derived mappings

Baseline `2a54aed1ff35851cdde314d591fd842442b5ff0a`: all three workflows SUCCESS (46065047564, 46065047450, 46065047438), metadata checked; archive content and independent review open. GitHub path history at pinned Ace source `68d7fd1c0f5ac50cdb610bf06b86074eab3be652` checked for historical raw and current paths; GraphQL original path queried at rename parent `cd9b91b07cd38e5f21d5b4ce3f3801367ab3300b`. The table lists first observed nonempty contribution (or first observed historical path where content introduction is not yet checked) and a historical endpoint, not an exhaustive DAG replay. Historical endpoint bytes compared with current pinned sources: 16 raw/template-literal exact matches, two Cedar exact module blobs, two inline module exact blobs (Io/Vala), two legacy single-quoted JS string payloads (JSONiq/XQuery) decoded without execution using only observed escapes and line continuations. All 22 equal at the indicated endpoint. All 19 distinct endpoint commits have root LICENSE blob `4760be2a6220cf545129b233e20574f2a7bb630e` (BSD-3-Clause). This is evidence of the Ace declaration, not individual contributor grants or third-party clearance. All comparisons were interactive research; only the two newly promoted derivative paths are added to the networked embedded evidence gate in this increment.

| Payload | First contribution / observed path | Verified endpoint | Historical Git blob | Open lead / scoped result |
| --- | --- | --- | --- | --- | --- |
| abc | [8019a214](https://github.com/ajaxorg/ace/commit/8019a21475618b03127459e43b4825660208c3ac) | [07d01fda](https://github.com/ajaxorg/ace/blob/07d01fda44ffb7d26e522ced7a8ab06a950e1096/lib/ace/snippets/abc.snippets) | `5c3cd677cb9c1c053638501a39b0ee896c942f31` | Zupfnoter conventions; highlight rules cite SublimeABC, not proof of snippet import |
| cedar | [c5c19dc4](https://github.com/ajaxorg/ace/commit/c5c19dc4c0c87b0f1e727def6b69f00943c1f5a3) | [c5c19dc4](https://github.com/ajaxorg/ace/blob/c5c19dc4c0c87b0f1e727def6b69f00943c1f5a3/src/snippets/cedar.snippets.js) | `ca5eb44499acbf392db9df314818a607db4c2878` | Cedar contribution #5944; external grammar lead is not snippet provenance |
| cedarschema | [c5c19dc4](https://github.com/ajaxorg/ace/commit/c5c19dc4c0c87b0f1e727def6b69f00943c1f5a3) | [c5c19dc4](https://github.com/ajaxorg/ace/blob/c5c19dc4c0c87b0f1e727def6b69f00943c1f5a3/src/snippets/cedarschema.snippets.js) | `ba70be9b386bf7bbac399e3ac3a1eca84cc1b5c9` | Same contribution; vscode-cedar TextMate grammar cited for highlighting |
| csound_document | [c583c816](https://github.com/ajaxorg/ace/commit/c583c816f44fbc1f24e79977e21fe722b4f1d7df) | [c583c816](https://github.com/ajaxorg/ace/blob/c583c816f44fbc1f24e79977e21fe722b4f1d7df/lib/ace/snippets/csound_document.snippets) | `5f6ef467d2a1bbe365e93fb2420c9645fa4b9f7c` | Csound language contribution; grammar/lexer references not payload evidence |
| csound_orchestra | [c583c816](https://github.com/ajaxorg/ace/commit/c583c816f44fbc1f24e79977e21fe722b4f1d7df) | [c583c816](https://github.com/ajaxorg/ace/blob/c583c816f44fbc1f24e79977e21fe722b4f1d7df/lib/ace/snippets/csound_orchestra.snippets) | `a73bcc1bebab3e21af09417a4882d895be9ba239` | Same contribution; investigate original input |
| drools | [68f9b22d](https://github.com/ajaxorg/ace/commit/68f9b22df35451a9cdda62144cae825fe42e8ecf) | [68f9b22d](https://github.com/ajaxorg/ace/blob/68f9b22df35451a9cdda62144cae825fe42e8ecf/lib/ace/snippets/drools.snippets) | `3687bec18dadd5d26b76a927e94ff618aa6769fe` | Drools contribution; mode BSD header not a separate snippet license |
| edifact | [f884c8fd](https://github.com/ajaxorg/ace/commit/f884c8fd6394d60311782c50e6d233dbc6da4ecc) | [f884c8fd](https://github.com/ajaxorg/ace/blob/f884c8fd6394d60311782c50e6d233dbc6da4ecc/lib/ace/snippets/edifact.snippets) | `624b87ad3d9e135050ba3415237fff3e38241bbc` | Exact two-trigger replacement of 2013 Java; scoped SnipMate MIT |
| fsl | [5c8d7513](https://github.com/ajaxorg/ace/commit/5c8d7513beb4f1230e24768e7b9336debb6e97b1) | [5c8d7513](https://github.com/ajaxorg/ace/blob/5c8d7513beb4f1230e24768e7b9336debb6e97b1/lib/ace/snippets/fsl.snippets) | `2158da5c9123c0a1db058d47aaa9d2c8647901dd` | machine_license MIT is inserted template content |
| gobstones | [92b97ba8](https://github.com/ajaxorg/ace/commit/92b97ba82bc924aa6861801d17567c083bdc8f45) | [e740aa81](https://github.com/ajaxorg/ace/blob/e740aa81444974866c28f4722ebd5feb7008fa5c/lib/ace/snippets/gobstones.snippets) | `c50e8d5b6fdb73bb4e97fa34853d25b720b080db` | Large 1705-line payload, original inputs/change review open |
| graphqlschema | [f5a98d4f](https://github.com/ajaxorg/ace/commit/f5a98d4f87751e77eb0ac27bcfdd6dae2bf985b6) | [4cfeb90e](https://github.com/ajaxorg/ace/blob/4cfeb90e96b0fedb5e5b345b33e6f92830685dd5/lib/ace/snippets/graphqlschema.snippets) | `32c6286c42d1b728bbd50840b177d8d9d7e73030` | Original graphqlscheme path; unchanged blob at rename parent cd9b91b0 |
| io | [09ddbeb3](https://github.com/ajaxorg/ace/commit/09ddbeb3417d668cdb47a46225d3f46a68f42d80) | [f2f6bd7e](https://github.com/ajaxorg/ace/blob/f2f6bd7ebe91fed147bc8f13b7e70b48300b0c2b/lib/ace/snippets/io.js) | `500eb8b25ca88e35a0dc4ce97011c577a72ed057` | Inline TextMate-shaped array; original bundle open |
| jsoniq | [f6faeb35](https://github.com/ajaxorg/ace/commit/f6faeb3547d66cfc095ec2f9ca3a39454208de52) | [431facf0](https://github.com/ajaxorg/ace/blob/431facf08b397bf6517893efccf17d2cdb32d12e/lib/ace/snippets/jsoniq.snippets) | `965034b7e9dc611fa959c2dba04bdc8f55d74c36` | JSONiq/XQuery shared raw blob; source rights separate from REx |
| liquid | [58fcde32](https://github.com/ajaxorg/ace/commit/58fcde32061df7d7f6ef38a6bfcf306b0f800f92) | [58fcde32](https://github.com/ajaxorg/ace/blob/58fcde32061df7d7f6ef38a6bfcf306b0f800f92/lib/ace/snippets/liquid.snippets) | `b3e3c982cfa70d04544b74652bbe85e702f5ebf2` | Exact 26-line prefix + historical HTML; scoped SnipMate MIT |
| lsl | [78ca93fb](https://github.com/ajaxorg/ace/commit/78ca93fb16eee011b3b4eca3cc74b0e6a26b0111) | [fb038432](https://github.com/ajaxorg/ace/blob/fb0384329602f0ea99aa1fd983f094f7b0c31797/lib/ace/snippets/lsl.snippets) | `352d26e7b4ed7389ddefb8365b4e2d985e63d037` | 1233-line API templates; external API source and edit history open |
| maze | [5de512c1](https://github.com/ajaxorg/ace/commit/5de512c1d37efadb1d16c965ba931ecd58abca9b) | [5de512c1](https://github.com/ajaxorg/ace/blob/5de512c1d37efadb1d16c965ba931ecd58abca9b/lib/ace/snippets/maze.snippets) | `76e52884b2bc3a52553d0b2fcb80680651798515` | Two short snippets; original contribution rights open |
| razor | [cb6dd551](https://github.com/ajaxorg/ace/commit/cb6dd5514da2b5dda41d10b117ff26e515e711b6) | [cb6dd551](https://github.com/ajaxorg/ace/blob/cb6dd5514da2b5dda41d10b117ff26e515e711b6/lib/ace/snippets/razor.snippets) | `f851b0547b3a27b0ae09a22cd8a0443d521b6438` | Short conditional; original contribution rights open |
| robot | [5d7cf109](https://github.com/ajaxorg/ace/commit/5d7cf10916e671bd7f81427be622c641c01fc36e) | [e91705e4](https://github.com/ajaxorg/ace/blob/e91705e41cb32deab6d827386b1c3905d4e007c2/lib/ace/snippets/robot.snippets) | `2cb13946ec15c85866c414dcb9b53119d3a56ee9` | Robot Framework templates; intervening edit review open |
| sqlserver | [f0b3aa0a](https://github.com/ajaxorg/ace/commit/f0b3aa0a6f697898fb07a36a92019b0db5902b4e) | [cf0c81a2](https://github.com/ajaxorg/ace/blob/cf0c81a25fa5373409b086d824e4405698622f64/lib/ace/snippets/sqlserver.snippets) | `403bd6bc551a0fcb224e84fd5c996a0ca6c26984` | MSDN link and SQL procedure templates; external source review open |
| vala | [a7cac946](https://github.com/ajaxorg/ace/commit/a7cac9466d563ed31bad9e0fa8d13b463ee5f6d9) | [ed5c3198](https://github.com/ajaxorg/ace/blob/ed5c3198f3fbe4698fbec8359c1725e5f5c88a65/lib/ace/snippets/vala.js) | `b1230e6871d9f08406d16dd862f371c36bbabc6f` | Inline array; original bundle open |
| velocity | [69b14468](https://github.com/ajaxorg/ace/commit/69b144686a9d7946a89bbcdeb3a83ce9ae248c04) | [69b14468](https://github.com/ajaxorg/ace/blob/69b144686a9d7946a89bbcdeb3a83ce9ae248c04/lib/ace/snippets/velocity.snippets) | `dedca58934a99cc5073e326ede9bd974f0d0f03c` | Directive templates added after placeholder; external input open |
| wollok | [1693305c](https://github.com/ajaxorg/ace/commit/1693305c8974a5dd4f350bb0b9d48b134fca113c) | [1693305c](https://github.com/ajaxorg/ace/blob/1693305c8974a5dd4f350bb0b9d48b134fca113c/lib/ace/snippets/wollok.snippets) | `f98f8587908fefe10bc9dc3a9fa02443a60bb1aa` | Java-like content; 49 exact LCS lines of 85 vs 241, not a proved bounded derivation |
| xquery | [f6faeb35](https://github.com/ajaxorg/ace/commit/f6faeb3547d66cfc095ec2f9ca3a39454208de52) | [431facf0](https://github.com/ajaxorg/ace/blob/431facf08b397bf6517893efccf17d2cdb32d12e/lib/ace/snippets/xquery.snippets) | `965034b7e9dc611fa959c2dba04bdc8f55d74c36` | Same historical and current blob as JSONiq; distinct shipped location |

### Two additional proven SnipMate descendants

- EDIFACT at `f884c8fd6394d60311782c50e6d233dbc6da4ecc` is byte-identical to the 2013 imported Java raw snippet after replacing exactly the two initial protected/public triggers with UN/UNB (four lines; 237/241 exact LCS lines including final empty line). Java raw blob `854f14ac22f148309d4f9ec450fda38244ede6ec` already matches the historical MIT collection. The new relation requires that exact prefix and single occurrence, and equality of all remaining bytes. The retained Java-like body warrants functional review; no assertion that it is appropriate EDIFACT completion behavior.
- Liquid at `58fcde32061df7d7f6ef38a6bfcf306b0f800f92` is exactly a fixed 26-line Liquid-specific prefix ending in the HTML inclusion comment, followed by the entire HTML raw snapshot at `d9b38ac378d0dea6e1ca820c0e8294f04c46010a` (blob `20a73d72e339c352216ce4803e6c5b842f7d7212`). The prior 18-transition replay established HTML lineage including this endpoint. The new relation requires exact prefix and unchanged suffix; no arbitrary substring or fuzzy normalization. CDN references are snippet text, not bundled dependencies.

Both raw derivatives equal their current static template payloads. The two bounded raw-to-raw relations and existing template-literal relations are pinned in embedded inventory with regression checks; existing original MIT LICENSE and AUTHORS remain intact. Scope expands from 30 to 32 locations for historical material only. The 20 other assets, the additional inputs of modified descendants, wrapper/mode rights and 150 stubs remain open. In particular Io and Vala original bundles, large LSL/Gobstones, Wollok Java-like material, and SQL Server template origin need targeted research. No exclusions, new external package identity, runtime/vendor bytes, license text or curated profile changes. No full license clearance, issue closure, or merge approval.
