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


## R5.3a follow-up — Io and Vala TextMate bundle inputs, Wollok comparison

Baseline Configurator `ed62f11aab6b4d6e8d5d36e9df177a18790fe46a`: all three exact-HEAD workflows SUCCESS (46065961387, 46065961298, 46065961408), metadata checked. Archive content and independent review remain open.

### Exact external source collections

Both external trees were obtained at snapshots preceding their Ace import commit dates, with complete non-truncated recursive tree listings. Compared each XML plist dictionary to its unique named entry in the pinned Ace inline JSON array (no JavaScript execution). The observed conversion is deletion of UUID and removal of `source.` from scope, plus XML entity decoding. All retained string values and field sets compare exactly, including content whitespace, triggers and key equivalents where present. The interactive comparator accepts only the observed key/string dictionary structure, rejects unparsed fields and duplicate keys, and compares per-name entries, not array ordering. The observed conversion agrees with historical Ace [tool/tmsnippets.js](https://github.com/ajaxorg/ace/blob/09ddbeb3417d668cdb47a46225d3f46a68f42d80/tool/tmsnippets.js) blob `febc7946e892692859402053b45369033c516a3b`. This is not a byte rebuild of the JS wrapper, a unique proof of the checkout used by Ace, or an automated gate yet.

| Payload | External historical snapshot | Ace import (committer date UTC) | Current Ace module blob | Result |
| --- | --- | --- | --- | --- |
| Io | [textmate/io.tmbundle e8f7b377](https://github.com/textmate/io.tmbundle/tree/e8f7b3773544cfc14a7ede7344ed94683f7ed602/Snippets), 2014-06-18 | [09ddbeb3](https://github.com/ajaxorg/ace/commit/09ddbeb3417d668cdb47a46225d3f46a68f42d80), 2014-09-02 | `500eb8b25ca88e35a0dc4ce97011c577a72ed057` | 10/10 exact dictionaries |
| Vala | [technosophos/Vala-TMBundle 40ec6f4f](https://github.com/technosophos/Vala-TMBundle/tree/40ec6f4f5e1cf921d521d0589fd9e7fc6ba0b305/Snippets), 2013-11-12 | [a7cac946](https://github.com/ajaxorg/ace/commit/a7cac9466d563ed31bad9e0fa8d13b463ee5f6d9), 2014-06-01 | `b1230e6871d9f08406d16dd862f371c36bbabc6f` | 31/31 exact dictionaries |

Current source modules pinned at Ace `68d7fd1c0f5ac50cdb610bf06b86074eab3be652`. Io Snippets tree `c0b78b8dfa7b3e03abfb40879a15a572b5d90484`; Vala Snippets tree `2506df0b1ff0b4b3d360c1c74d829d0457e44d31`. The external counts equal the current Ace array counts. No copyright/license marker found in the 41 individual XML files; no accompanying license-suffix file in either historical Snippets tree.

#### Io file pins (all 10 exact)

| Path relative to Snippets/ | Git blob |
| --- | --- |
| `Indented Bracketed Line.plist` | `98bb36feff73383d6398ba5e03e757b154679106` |
| `Indented return.plist` | `97bfd34c245f79c304f9e3f6c2810477b1037958` |
| `Method.plist` | `b082f3d68bde632a4649e28408553cb3f040f4f6` |
| `Object clone do.plist` | `3bbf7cc53380be415fa0c15ff2e1085e4dc43516` |
| `UnitTest.plist` | `e0fb79c4666d214fd4a79fca8d2a35b0b9f0dff1` |
| `assertEquals.plist` | `6ca41752bc0b6dfba3f94cdb1224113656805ef9` |
| `clone do.plist` | `c27be9c3bc7050aedd9ee24aa645b528384cae99` |
| `docSlot.plist` | `4345e801e14beb4c63e8de998b97bd976670ea57` |
| `newSlot.plist` | `ec84683c68570ea0afd0d8a09078d6365e019146` |
| `testMethod.plist` | `7f3693713cbb0f59ef6609379dfac9618488031a` |

Historical [README.mdown](https://github.com/textmate/io.tmbundle/blob/e8f7b3773544cfc14a7ede7344ed94683f7ed602/README.mdown) blob `32d8f85a4c5f41b1fd636664c7a4ca776f511b9f` grants copy/use/modify/sell/distribute permission at repository scope, with exceptions for files containing their own terms or accompanied by same-directory license files. No such exception identified for the ten checked inputs. The README blob is identical to the previously recorded themes.tmbundle historical README, but the Io repository scope is separately established; a generic converter or theme notice alone is not source-specific evidence. Proposed disposition: retain, recover source-specific TextMate permission reference and map the Io payload, subject to exact gate/independent review. No other Io grammar rights inferred.

#### Vala file pins (all 31 exact)

| Path relative to Snippets/ | Git blob |
| --- | --- |
| `Comment (multiline).tmSnippet` | `1f58883393206674f86d8eced7e1225876b46398` |
| `Console.WriteLine (writeline).tmSnippet` | `d7828633f15704389c7027eff003dc88e37072de` |
| `DBus annotation.tmSnippet` | `e8f6e1c54bd760612a9c8fba4bad1d2bdced3f29` |
| `DocBlock.tmSnippet` | `d00916a9d4fa1d7f44b947318f146655e9c24fef` |
| `Gee_ArrayList.tmSnippet` | `d67415cbdc1c243d235601356145ce52e5dcf326` |
| `Gee_HashMap.tmSnippet` | `e96031b7ab04d5afefd0b1467b7894cfcbf38cd7` |
| `Gee_HashSet.tmSnippet` | `6b3b6806665841cd03255ddfd17a4fc9a7acfc37` |
| `Main function.tmSnippet` | `bd86c7e4ca31823ce41e6fa46945911d0d2d51ca` |
| `String template (@).tmSnippet` | `6e488970ee80ecdf6829d50cfc032dc063433e00` |
| `Verbatim string (""").tmSnippet` | `c3afa7bfd0d7dc71abd5341cd5e620c8104e7a75` |
| `case.tmSnippet` | `818d8e9586479c0e981866c547e07664dc5261d3` |
| `class.tmSnippet` | `bafc69bdcab709bffebcb9d93f9687133363e92f` |
| `closure.tmSnippet` | `e63ee79c17f2c963f3cd5791e1515b1302649ef0` |
| `delegate.tmSnippet` | `7e79b111ca44585948fc1eb5be7ba9af4cb7cf23` |
| `do while.tmSnippet` | `9dd440145033f6fc0a5ac2a62a4f33ddbfe4547a` |
| `else if (elseif).tmSnippet` | `a637fbb794e3ae72b872bb2297ac748c3d1291e3` |
| `else.tmSnippet` | `0fb763415925f90fcd870c8947ea094dc5d2eb14` |
| `enum.tmSnippet` | `5b1f36bc90d9f31c5e427222db2749b1601897d5` |
| `error domain.tmSnippet` | `730dd21376c574b72a93d0e14e2257152675c66d` |
| `for.tmSnippet` | `e26a938aff3e8f48e486fd9a54b8ae86a95d6c18` |
| `foreach.tmSnippet` | `5d0254b6fc3773ebf0427ec0008d44e45ea1fc42` |
| `if.tmSnippet` | `fb5a269903b238fc14ddeca5807b1b658a9a328d` |
| `interface.tmSnippet` | `e7cf218c5415533d0153640e9e3841a06600770f` |
| `namespace (ns).tmSnippet` | `2682216c02b2a77f892f7d0d74cca2a7f903b075` |
| `printf.tmSnippet` | `274ee7a3a2347aa18142590228615a595c5af679` |
| `property (prop).tmSnippet` | `572447dc0595f4b3c0c97e63e0405c96110711e6` |
| `read-only property (roprop).tmSnippet` | `333d5fb20dee592811fd246098fd326e9a6d3a68` |
| `struct.tmSnippet` | `3ed0b3ffff5fc71895f07c023b321e8946aeb225` |
| `switch.tmSnippet` | `b44baff8fc7fcec7537521b6ed03a4ee86a12846` |
| `try:catch.tmSnippet` | `610ede504a37d18f9f9f9a9f3ac5f9524002db72` |
| `while.tmSnippet` | `eb784d1a64de35902ae8466baafe17acc7d88128` |

The pre-import [README.md](https://github.com/technosophos/Vala-TMBundle/blob/40ec6f4f5e1cf921d521d0589fd9e7fc6ba0b305/README.md) blob `d74231b55b3f6caa79067ddc8666aa4733b18921` credits Daniel Lucraft's original bundle; no explicit grant in that snapshot. A later first LICENSE addition [2fd9373f](https://github.com/technosophos/Vala-TMBundle/commit/2fd9373f90bf74eef0b15f43c7240c28d55bebaa), 2014-11-13, adds only LICENSE, MIT, copyright 2014 Matt Butcher. Its [LICENSE](https://github.com/technosophos/Vala-TMBundle/blob/2fd9373f90bf74eef0b15f43c7240c28d55bebaa/LICENSE) blob `1ee64503bcb3ae31e5b01f5cf61e9a02846cb3a3` is also present at later snapshot `935bd21c13068158435f64b3dbd8423c8d812c92`. All 31 path/blob pairs match the 2013 snapshot at both later revisions, and the LICENSE addition has exactly the same Snippets tree hash `2506df0b1ff0b4b3d360c1c74d829d0457e44d31`. This is direct evidence of a later published MIT grant for identical bundle material, not a claim that MIT was declared at Ace import or that the later grant settles all pre-existing contributors' rights. The earlier Daniel Lucraft bundle grant remains open. Linguist metadata was a lead to the actual upstream LICENSE, not the source of the grant. Proposed disposition: retain review-open and recover original MIT text with explicit later-grant and earlier-rights limitations, or consider maintainer-approved snippet-only exclusion if remaining rights cannot be resolved. No exact package release/PURL inferred.

### Wollok — evidence of Java adaptation, not full origin clearance

Compared historical Wollok raw blob `f98f8587908fefe10bc9dc3a9fa02443a60bb1aa` at [1693305c](https://github.com/ajaxorg/ace/commit/1693305c8974a5dd4f350bb0b9d48b134fca113c) to historical imported Java raw blob `854f14ac22f148309d4f9ec450fda38244ede6ec` (SnipMate MIT already mapped for Java). Seven exact same-trigger bodies: im, cl, /*, el, if, thr, /**. The re trigger differs only by the final line terminator in the isolated body comparison. Eight same-trigger bodies differ (m, as, ca, try, print, set, get, re); several clearly parallel Java structure with Wollok syntax, but exact generic snippets alone do not prove unique origin. The earlier 49/85 Wollok vs 241 Java LCS result is similarity evidence only. The contribution preserves Java-oriented section headings including the initial Java packages/import heading and Javadocs. This supports a targeted bounded block/section lineage investigation, not a blanket SnipMate MIT grant or full-file derivation. No promotion of Wollok in this increment.

### Next implementation gate / scope

Record only research here. Existing immutable_raw_url validation accepts a restricted path alphabet; several demonstrated source filenames contain spaces, parentheses, quotes, @ or colon. Do not silently relax the URL allowlist or omit such files to obtain a partial apparent closure. Design a narrowly scoped canonical encoded-path validator with traversal/double-encoding/control rejection, strict XML plist/JSON-array comparison and one-to-one set/count closure, or an equivalently bounded source-blob retrieval method; add tamper/negative tests. Then preserve the actual Io README license section and Vala original LICENSE and promote source-specific partial attribution records. The existing 32 SnipMate locations remain unchanged. No runtime, vendor, notices, inventory, curated profile or production audit code changed here. No independent acceptance, final license clearance, issue closure or merge approval.


## R5.3a follow-up — automated TextMate collection gate and original notices

Baseline `071a00b280c654236abbdfeeaa7b003a9d034d06`: all three workflows SUCCESS (46066705193, 46066705253, 46066705449), metadata checked only. The existing raw URL allowlist now has a narrowly scoped canonical percent-encoded filename exception for the two pinned TextMate collection revisions, limited to Snippets/ and the observed ASCII filename characters/extensions. Canonical round-trip encoding rejects encoded separators, percent aliases, traversal and controls; other repositories retain prior restrictions. XML parser accepts only the observed plist string dictionary structure and strips known standard declarations before parsing (no external DTD resolution), rejects duplicate/unknown fields and executable or extra wrapper text; JSON array parsing rejects duplicate keys. Whole-collection comparison requires 10 or 31 unique names and exact field dictionaries after UUID removal and source. scope conversion. Evidence pins, count, module blob and shipped location are checked offline; network gate verifies all 41 source blobs and compares full arrays, reports collection results. Vala inputs fetched at later MIT-licensed revision `2fd9373f90bf74eef0b15f43c7240c28d55bebaa`, which prior research showed has the same full Snippets tree as 2013. Prior tree comparison remains interactive research, not networked tree verification. Two partial embedded library records, source-specific Io permission excerpt (custom LicenseRef-TextMate-Bundle) and original Vala MIT text added. No version/PURL/OSV identity or full clearance. Wollok and earlier Daniel Lucraft rights remain open. No runtime or curated profile change. CI and independent artifact/review acceptance pending.


### TextMate gate correction — literal CR in Io Return key

Exact HEAD `d423bec44f907377874ce0e4a8573ff7547bfc3c`: migration rehearsal 46067395117 and retained worker research 46067395102 SUCCESS; Offline foundation 46067395123 FAILURE in routing/inventory job 140735930472, at networked upstream evidence, `TextMate snippet collection mismatch: io`. Other three jobs SUCCESS. All evidence pins passed before the comparison. The immutable Io `Indented return.plist` blob `97bfd34c245f79c304f9e3f6c2810477b1037958` contains exactly one literal CR in the keyEquivalent string; current Ace array stores CR, while XML 1.0 parsing converts literal CR to LF. Reproduce the observed historical conversion only for that exact blob and exact field, by substituting a numeric XML character reference before parsing. Other literal CRs are rejected, no general newline normalization or reduced collection cardinality. Regression pins exact original XML bytes, CR value, tampered source rejection and whole-array CR-vs-LF distinction. New HEAD CI pending. No change to vendor bytes, notices, inventory or curated profile.


## R5.3a follow-up — Wollok retained Java material, ABC and XQuery/JSONiq leads

Corrective baseline `7306364cf8667fa29bb60b83456898217d9bba6e`: routing/inventory job 140737913037 SUCCESS including networked Io/Vala evidence, 208 Python tests (all four TextMate regression methods OK), distribution artifact build; artifact supply-chain-source 15230974085 metadata from logs, content not inspected. Other two workflows 46068011370 and 46068011409 SUCCESS; Offline foundation 46068011369 browser job still in progress at time of this research. No independent review.

### Wollok scoped shared-material attribution

The immediate parent of [Wollok introduction 1693305c](https://github.com/ajaxorg/ace/commit/1693305c8974a5dd4f350bb0b9d48b134fca113c) is `4f9cd17910cfe36dc504b456ea5ef62c15189f2d`. Its [Java raw input](https://github.com/ajaxorg/ace/blob/4f9cd17910cfe36dc504b456ea5ef62c15189f2d/lib/ace/snippets/java.snippets) has exactly the 2013 SnipMate import blob `854f14ac22f148309d4f9ec450fda38244ede6ec`. Java has 80 snippet triggers; Wollok has 20: 15 shared triggers in identical relative order, five new (w.l, w.i, obj, te, inh). Seven identical complete bodies, one return body with EOF LF removed, seven adapted bodies. Eight exact section headings, including the distinctive unchanged Basic Java packages and import and Javadocs, survive in the same relative order. Compared 16 non-overlapping unique ordered literal spans (510 ASCII bytes total), including the exact Filename placeholder and comments/Javadocs bodies, not merely generic syntax. Java-to-Wollok line start pairs: 25→1, 41→11, 53→23, 65→30, 73→32, 77→34, 83→37, 111→44, 113→49, 115→51, 119→53, 136→59, 176→66, 196→71, 202→77, 206→82. This is strong retained-material evidence, not proof of the precise editing sequence or original author grant for every line.

New bounded relation `ace-wollok-java-retained-blocks` checks all 16 spans for uniqueness, order and exact bytes, including the observed final return boundary. Network gate independently pins both full raw blobs and current source module, with existing exact template-literal relation; the new partial relation alone is not a whole-file derivation or a detector of changes in unshared regions. Original SnipMate MIT and AUTHORS already retained; scope expands 32→33 for original Java material only, no claim of MIT for Wollok adaptations/new contributions. Tamper regression checks changed shared blocks, duplicate/reordered blocks and EOF boundary. No new package version/PURL or runtime bytes.

### ABC: exact intermediate Zupfnoter correspondence, licensing scope open

All three nonempty Ace raw historical versions by bwl21 (committer dates UTC) were checked. Both consecutive unified patches replay exactly (full context, line counts and next snapshot equality, interactive):

| Ace revision | Date | ABC raw Git blob |
| --- | --- | --- |
| [8019a214](https://github.com/ajaxorg/ace/commit/8019a21475618b03127459e43b4825660208c3ac) | 2014-12-14 | `11e2d73579dd7378a1e7d6a293163c1b2a0f0eea` |
| [95eed254](https://github.com/ajaxorg/ace/commit/95eed254393eeda6079a0386d87e0fe2a6807024) | 2014-12-14 | `65b0fd65b11f2e288c5b227dfcb6f6d8edaedfec` |
| [07d01fda](https://github.com/ajaxorg/ace/commit/07d01fda44ffb7d26e522ced7a8ab06a950e1096) | 2014-12-29 | `5c3cd677cb9c1c053638501a39b0ee896c942f31` |

The historical [Zupfnoter snapshot 6ebab62d](https://github.com/bwl21/zupfnoter/tree/6ebab62d50168b6d2e66479492224dde83866273), 2014-12-29 19:24 UTC, contains [vendored Ace abc.js](https://github.com/bwl21/zupfnoter/blob/6ebab62d50168b6d2e66479492224dde83866273/30_sources/SRC_Zupfnoter/vendor/ace/snippets/abc.js), blob `069ec886e66ee6b28098a0b512e46189885596f1`. Its statically decoded 349-byte snippetText is exactly the intermediate Ace raw `65b0fd65...` (not final endpoint), using only observed newline escapes, no JS execution. The Zupfnoter tree predating Ace import [23c8802f](https://github.com/bwl21/zupfnoter/tree/23c8802fe93823775cddf2fe3a6e04d67b28e4ec) has spreadsheet `30_sources/900_snippets/snippets.xlsx` blob `5cabd73eee08df8e14a2f380678ab855e528d503` but no ABC snippet module in vendored Ace. At original investigation the binary was not retrieved. Round 7 reviewer independently extracted the exact blob and reported a single sheet with only two unrelated Hugo rows (see Round 7 addendum below); this lead is closed on reviewer evidence, not a new author-side extraction. Both historical READMEs (blobs `85167522d69e33e65a5dd6a747f5ec410897e0d2`, `92d397a68b462e7094d1fd743091ba5d01852cb8`) declare GPL/Commercial dual licensing for Zupfnoter software and describe the specific notation conventions. Same contributor introduced/updated Ace ABC and Zupfnoter includes the intermediate vendored Ace version, so direction and scope of licensing cannot be inferred from the vendored copy. No blanket GPL assignment to Ace contribution or clearance under Ace BSD solely from root declaration. Historical [SublimeABC snapshot 452f7973](https://github.com/jimhawkridge/SublimeABC/tree/452f797361b43cbe40847b6b58baaded79f4ba0d) contains two syntax grammar files, README and test.abc, no snippet files; Ace highlight-rule citation is not evidence of snippet import. Proposed ABC disposition: review-open, obtain source-specific grant or maintainer-approved snippet-only exclusion (not approved here). No new license notice or runtime/profile change.

### JSONiq/XQuery: separate from lexer attribution

Both introduced by wcandillon at `f6faeb3547d66cfc095ec2f9ca3a39454208de52` and identical endpoint blob `965034b7e9dc611fa959c2dba04bdc8f55d74c36` at `431facf08b397bf6517893efccf17d2cdb32d12e`, separately shipped assets. Historical [XQLint pre-import snapshot ff77139c](https://github.com/wcandillon/xqlint/tree/ff77139ca231ee4cbc9107a498fed476b588be86) (2014-04-04 13:01 UTC) and the previously pinned `1778846ed8e707780d791fd3ffb41feccdf9de04` have no dedicated snippet files in complete recursive tree listings. Their lib/completion/completer.js blobs `40dcf59f12a9af3430a5e6908fdf78c75473fd28` and `e949c611782a0bf4565b084dd10172a79e4ef988` implement dynamic completion, not the static raw Ace payload; later file builds function-call snippets dynamically. No exact external origin demonstrated. Same-author contribution and shared grammar/worker history are leads, not grounds to extend XQLint Apache-2.0 or REx grant to snippets. Retain review-open. No reopen of REx output permission.

No runtime/vendor bytes, notices themselves or curated profile changes. Existing Io/Vala records unchanged; full license clearance, exact-HEAD artifact inspection and independent reviews remain open. PR #36/#32 Draft/HOLD and #9/#33/#37 open.


## R5.3a follow-up — Gobstones, LSL, SQL Server and GraphQLSchema

Baseline `c376ec1bd28c3b473c17a2d232fa7a7637a06f4b`: all three exact-HEAD workflows SUCCESS (46068394195, 46068394155, 46068394153); metadata checked, independent artifact content/reviews not completed. All four raw endpoints re-read: Gobstones 1705 LF-split lines / 479 triggers (8 duplicate names), LSL 1233 / 481, SQL Server 70 / 12, GraphQLSchema 33 / 5. LF-split includes trailing empty element where present; duplicates in Gobstones must not be silently collapsed.

### Gobstones — external project is GPL, current snippet source not established

Original Ace contribution [92b97ba8](https://github.com/ajaxorg/ace/commit/92b97ba82bc924aa6861801d17567c083bdc8f45), javifernandes, 2015-11-22, introduces 34-line raw (blob `c837449b27e34a8e10cf32f891fbaef88ffa6657`). [2019 update e740aa81](https://github.com/ajaxorg/ace/commit/e740aa81444974866c28f4722ebd5feb7008fa5c), alanrodas, 2019-06-19, explicitly describes making snippets/highlighting consistent with Gobstones-web behavior, expands raw to blob `c50e8d5b6fdb73bb4e97fa34853d25b720b080db`. The prior [Gobstones-web snapshot a83dbfbf](https://github.com/gobstones/gobstones-web/tree/a83dbfbffe944b07f52943005b4009bfce6699c0) (2019-06-13) has 2599 entries in complete recursive tree and no separately named snippets/completion file. [LICENSE.txt](https://github.com/gobstones/gobstones-web/blob/a83dbfbffe944b07f52943005b4009bfce6699c0/LICENSE.txt) blob `30ace6a87310f143f38bc99a5b22a0f6ae231718` is GPL v3 text. bower.json blob `c2fb7c0a23c6cbb45e1c24f5348a9bfce3c0a160` points to `gobstones/ace-builds#^1.4.2`; gobstones-editor.html blob `0ea2e28e87e24373bd099e0882be925475c98b73` integrates ace-widget. Historical [gobstones/ace-builds e290c82d](https://github.com/gobstones/ace-builds/tree/e290c82df099183ad6610f8766615ea4769570ea) (2018-10-23) retains Ace BSD LICENSE blob `4760be2a6220cf545129b233e20574f2a7bb630e`; its src/snippets/gobstones.js blob `51a0b37de7f8e8709a262d4a7382aafd8d1b5f24` contains the old short English templates, not the expanded Spanish collection. Same-author [alanrodas/ace 7a299258](https://github.com/alanrodas/ace/tree/7a2992588405878cd6aa2f32962bffd7e6dc5dda) (2019-06-14) has original identical raw blob `c837449b...`. The contributor fork of Gobstones-web at `1b920a1b88d57389f8b4a7117f2189a1e3c3801a` also has no named snippets file in its complete tree. No direct evidence of copying the expanded collection from GPL project; no blanket GPL or BSD assignment. Project license alone cannot establish snippet rights. Need source-specific grant or maintainer-approved snippet-only exclusion, no action on mode.

### LSL — exact historical external snapshots, license scope OPEN

All six Ace raw history commits from 2013-05-30 to 2015-09-18 are attributed to buildersbrewery in GitHub commit metadata. Current Builders Brewery repositories queried by pre-2015 date returned no snapshots on default history; the preserved historical fork [dazzle-lsl/linden-scripting-language](https://github.com/dazzle-lsl/linden-scripting-language) supplies the evidence instead.

| Ace raw revision | External source revision | Shared Git blob | Result |
| --- | --- | --- | --- |
| [36198a50](https://github.com/ajaxorg/ace/blob/36198a50f4bdef76c5044ba83df09d3298e90b6a/lib/ace/snippets/lsl.snippets), 2014-08-04 | [d777b7ad](https://github.com/dazzle-lsl/linden-scripting-language/blob/d777b7ad20cfa223a368d8bdf379edfc58130f4f/ace/lib/ace/snippets/lsl.snippets), 2015-08-21 14:40:41 UTC | `bc0d2eb9d0286050bbb56efa09cc02aaec500dba` | 1067 lines / 480 triggers, exact |
| [fb038432](https://github.com/ajaxorg/ace/blob/fb0384329602f0ea99aa1fd983f094f7b0c31797/lib/ace/snippets/lsl.snippets), 2015-09-18 21:49:57 UTC | [54ef136c](https://github.com/dazzle-lsl/linden-scripting-language/blob/54ef136c1eb3cb2703fb0b6b6e610918e03c217d/ace/lib/ace/snippets/lsl.snippets), 2015-09-18 21:42:30 UTC | `352d26e7b4ed7389ddefb8365b4e2d985e63d037` | 1233 lines / 481 triggers, exact |

External intermediate revision `d9e1559efc7506440382788628bb0c25eb71aeb3` has raw blob `0e09d79b30f37bc8d818e36b8b02dac25f4a6f9e`, 1069 lines/481 triggers; commit message cites LeTigre release notes and void return-type fixes. Final external snapshot precedes final Ace snapshot by 7m27s; same author and exact bytes establish common material, not a unique direction for earliest 2013 import. External root README blob `276b2a807b8991a1a0be3bb2b6e818e6012350c8` points to original buildersbrewery repo; ace/README.md blob `978ba7615b0608435bdd30845597aa4aaf72cb43` says files maintained for Ace. Neither grants a license. Complete 1357-entry tree has no root or Ace-directory LICENSE; its three named license files are for separate Sublime Text inputs: KWDB GPL v3 (`8cb9f32f550b7ca8ecf725066c437ee4b356bc18`), Linden Lab viewer LGPL v2.1 (`723f008e956b5c9b045d7139c444ecc222b7ef07`), LSLint public-domain unless otherwise noted (`a737a5c1c8aba42df4809d0e304fce4a8547e8eb`). KWDB XML `692ec4cb9b8057dce53b76426f36889c8e80ee4f` and viewer XML `e67b82ef0b4af85074d4520cceaa345d6f97de96` are possible data sources; no generation path proved, no nested license applied to Ace snippets. Historical Makopo/sublime-text-lsl `fd2b1ec1f5d4ce8a9d372af6df1daa4931b7ca8f` contains different-format completions/events; no exact payload established. Need original grant and/or source-specific data comparison, or explicit maintainer-approved exclusion.

New `ace-lsl-snippet-source-review` is kind review, status partial, license/version/ecosystem null, no notices, not a library/SBOM package or OSV query. Two bounded exact raw equality relations plus exact raw-to-current template relation, immutable source/notice-reference pins and regression; no final attribution acceptance. Scope of SnipMate test now limited to its mapped filenames, LSL independently tested.

### SQL Server — official later MIT reference templates discovered

Ace [f0b3aa0a](https://github.com/ajaxorg/ace/commit/f0b3aa0a6f697898fb07a36a92019b0db5902b4e), Sevin777, 2015-04-17, introduces createproc; [cf0c81a](https://github.com/ajaxorg/ace/commit/cf0c81a25fa5373409b086d824e4405698622f64), 2015-04-19, final raw `403bd6bc551a0fcb224e84fd5c996a0ca6c26984` includes 12 triggers. createproc and createfn have characteristic SSMS template headers, comments and parameter substitutions; stuffxml contains MSDN reference, not a distributed library.

Microsoft's official [sql-server-samples 80d5bf59](https://github.com/microsoft/sql-server-samples/tree/80d5bf59f8df98a4b1bc910a9424c77647896f00) (2018-05-06, initial ssms-templates path history) includes `samples/features/ssms-templates/Sql/Stored Procedure/Create Stored Procedure (New Menu).sql` blob `af6446ac87edcc649836882b4821a92342954024` and `samples/features/ssms-templates/Sql/Function/Create Scalar Function (New Menu).sql` blob `3261841c5cc34ca28113a745ebb5802e1caf461c`. Root [license.txt](https://github.com/microsoft/sql-server-samples/blob/80d5bf59f8df98a4b1bc910a9424c77647896f00/license.txt) blob `9d333bb098c152c0983042ca77f16ac0c8999441` is Microsoft Corporation MIT; README.md blob `447895f7a617ec616864a3f04db52f7dae9bfb5b` explicitly covers samples and templates. Both official template bodies contain distinctive matching sections (author/date/description scaffold, procedure NOCOUNT comments, function parameter and return-value comments) but differ in placeholders, omitted boilerplate and body; no complete exact input relation or evidence that the later published MIT grant covers all 2015 material. Proposed bounded shared-block comparison and source-specific notice with later-grant limitation, not a blanket MIT designation. Other ten triggers remain separate. Special encoded filenames need a separate narrow validator, not broad relaxation of current TextMate-only exception. No inventory/notice change for SQL Server yet.

### GraphQLSchema — small original contribution candidate

[Initial f5a98d4f](https://github.com/ajaxorg/ace/commit/f5a98d4f87751e77eb0ac27bcfdd6dae2bf985b6), DxCx, 2017-04-17, added five templates for type/input/interface/union/enum; later [4cfeb90e](https://github.com/ajaxorg/ace/commit/4cfeb90e96b0fedb5e5b345b33e6f92830685dd5) rename from graphqlscheme to graphqlschema retains blob `32c6286c42d1b728bbd50840b177d8d9d7e73030`. No license marker inside raw, no external source found from distinctive placeholder search. Related mode has Ace BSD header, but not evidence of external snippet rights. Retain candidate pending contribution/source review; no new library or notice.

This increment adds only an LSL review record, 3 source relations, test and research documentation. No new license notices or actual vendor/runtime/profile changes. 35/52 active historical attribution unchanged; LSL exact common source is additional review-only evidence. No exclusion without maintainer disposition, no overall clearance/issue closure/merge approval.


## R5.3a follow-up — Microsoft SSMS partial attribution and ten remaining small payloads

Baseline `4c74dfddf5b36c18dca3b4799b37dabc8970fb97`: exact-head workflows 46069221116, 46069221164, 46069221089 all SUCCESS; metadata only, artifact contents and independent reviews open.

### SQL Server bounded retained-material gate

Re-read both official 2018 Microsoft template files, historical Ace raw and current source module. Verified 4 unique ordered source/target spans for createproc and 6 for createfn (10 total); fixed pairs preserve specific header scaffold, placeholders, comments, NOCOUNT/DECLARE, return-value comment and boundaries, rather than loosely normalize SQL. Each source span occurs exactly once in its own Microsoft file, each target span once in its named Ace trigger and in order. Whole raw Git blobs independently pinned; exact raw-to-current static template relation. Partial comparator intentionally does not verify unrelated triggers or unshared content by itself. Two exact encoded paths allowed only at official Microsoft pinned revision; canonical percent roundtrip maintained, no general widening. Added exact original MIT notice (Git blob `9d333bb098c152c0983042ca77f16ac0c8999441`, SHA256 `201f3705979e932c92cd3c6ddbddf4dc3c71dcc5a82089a1e4018227cfe1cf09`, independently calculated against 1142-byte text and checked against Git identity). README specifically grants MIT for templates. New partial embedded record for source-specific material only, no claim that 2018 grant retroactively clears all 2015 modifications or other ten triggers. No version/PURL/OSV identity. Regression covers scope, tampered blocks, missing trigger, duplicate source blocks, changed EOF, canonical URL rejections and notice/SBOM mapping. Active historical-material coverage 35→36/52; not clearance.

### Ten remaining small payloads — original contribution review inputs

Re-read full historical endpoints (source URL for each is the Ace commit/path already recorded in the endpoint table). Intro commit metadata and complete raw content were inspected. Cedar modules are already static JS and count includes first trigger inside wrapper (7 and 6 respectively); others are raw. No individual grant established merely by absence of source markers.

| Payload | Intro author/date (UTC) | Triggers | Source review observation |
| --- | --- | ---: | --- |
| cedar | Swolebrain, 2026-04-21 | 7 | Common permit/forbid, when/unless, annotation scaffolds; PR #5944 also credits Victor Moreno. |
| cedarschema | Swolebrain, 2026-04-21 | 6 | Namespace/entity/action/type scaffolds. PR explicitly cites vscode-cedar TextMate grammar, not snippet source. |
| csound_document | nwhetsell, 2017-09-03 | 1 | CsoundSynthesizer XML scaffold only; mode's Pygments/Csound citations are separate. |
| csound_orchestra | nwhetsell, 2017-09-03 | 9 | Control, instrument and opcode scaffolds; no external snippet source marker. |
| drools | GitHub author account not resolved, 2015-09-19 | 3 | Rule/query/declare scaffolds; intro mentions drools.org for language details. |
| fsl | StoneCypher, 2018-11-20 | 1 | Machine metadata header; machine_license MIT is a generated-machine field, not a grant for the snippet. |
| maze | geraintwhite, 2015-06-06 | 2 | Two entries share trigger >, distinct description assignment/if; do not collapse. |
| razor | pmdevers, 2016-01-17 | 1 | 35-byte raw, one conditional scaffold (no final LF). |
| robot | SullyJHF, 2022-01-18 / 2022-05-05 | 11 | Settings/keywords/test/variables/control scaffolds; initial and later contribution, source rights still open. |
| velocity | rgriffith, 2013-12-04 | 6 | Common directives macro/foreach/if/import/set; commit describes added common directives. |

Cedar external [vscode-cedar pre-import snapshot dcb96c61](https://github.com/cedar-policy/vscode-cedar/tree/dcb96c6138a9798c935082e36727c2954f7804b9) (2026-03-24) complete tree has no paths named snippet; LICENSE blob `67db8588217f266eb561f75fae738656325deac9`. No direct snippet source established; grammar attribution remains separate. FSL same-author [StoneCypher/jssm snapshot 3dac8f22](https://github.com/StoneCypher/jssm/tree/3dac8f22fe90f68a27a312795dc3a779d45d2325) (2018-05-20) has MIT LICENSE.md blob `a9422124822b6838b1917698e17e2efddb39973c`, example files (states of matter `bab0829451cffa6c5311aaaadeec990e88d75eea`, TCP/IP `02a4e91f213369969955017440b06d1403d7b12b`, HTTP `82b27cf4cc8d41f85afaff4a0e6b468f29edb59d`) share machine metadata conventions but not the exact header. No MIT reassignment for FSL. These are limited source/intro reviews, not exhaustive searches or proof of originality. All ten remain review-open until disposition and independent acceptance. Next: consolidate per-payload evidence/disposition matrix and targeted remaining source leads (including actual Robot template history, Csound source candidates, and upstream contribution grants). No runtime/profile/exclusion change.


## R5.3 disposition matrix — first version

Baseline `73a08a73baa15cfee609adf96641759585e854e5`: all three exact-HEAD workflows SUCCESS (46070085893, 46070085890, 46070085880); artifact content/independent review remain open. Canonical [202-row matrix](ace-snippet-dispositions.json) and [rendered Markdown](ACE_SNIPPET_DISPOSITIONS.md) consolidate 52 nonempty and 150 generated empty-stub assets. 36 active partial historical attribution locations (22 exact SnipMate, 8 modified, 3 derived, Io/Vala, Microsoft), 1 LSL exact-source review-only, 15 historical endpoints still review-open. Each nonempty row carries pinned current source path/blob and historical reference; those references record prior research, not a new historical replay. All rows physically retained; four proposed snippet-only exclusion candidates (ABC, EDIFACT, Gobstones, LSL) pending maintainer decisions. No license/release acceptance. Offline source inventory gate checks exact row closure against lock/vendor hashes, exact stub template hashes, additional component mapping, mapped source relations and canonical Markdown rendering. Native research cross-checks all row classifications and 52 current source blob pins against existing immutable checkout/static payload report; reports explicit matrix verification. R5.3b shared stub template lineage and R5.3g independent acceptance remain open. No runtime/vendor/profile/notice change.


## R5.3b — shared generated loader template

The exact loader is the extModules branch of Ace `Makefile.dryice.js` `exportAce()`, not `tool/templates/snippets.js` (source scaffold). The current build enumerates modeNames for snippets, selects the non-main export filter after compression, replaces MODULES with a JSON array, REQUIRE_NS and NS with ace, slices function text at (13,-1), and prefixes a semicolon. No upstream code execution is needed. For an empty build body the minified output is exactly the loader; the unminified member is a single LF plus that loader. Existing native audit also verifies absence of the actual source module and payload for the 150 names.

| Revision | Makefile Git blob | Observed variant |
| --- | --- | --- |
| [d63863a](https://github.com/ajaxorg/ace/commit/d63863ac0cbc2d5387cb44ef3db6cc65c46ece6e) | `8bf5456296033ef22fe15a469ad3dd9af316c5e9` | require-only |
| [eccdf05](https://github.com/ajaxorg/ace/commit/eccdf0521294eca13b8b2e1df639f180753a07de) | `d799677440f3f41301d26758f201f7baf7b07d0d` | module-export |
| [3a9793c](https://github.com/ajaxorg/ace/commit/3a9793cbc1a7c583f42955a09c8b0b8a73f3c42e) | `0e683d2a8b0fb32eaaf5394ac7a4c6dc093bbcae` | module-export |
| [fc284ad](https://github.com/ajaxorg/ace/commit/fc284ad191a7ed0c6451a80dc2e9614eaeb39624) | `2556766137e948c70f6e1a8ccf86ab7f58b324b6` | guarded-export |
| [68d7fd1](https://github.com/ajaxorg/ace/blob/68d7fd1c0f5ac50cdb610bf06b86074eab3be652/Makefile.dryice.js) | `2d4596dee98c8b09333b192a8f4cd9cd09331185` | guarded-export, exact 2018 template |

2013 `df115ba6595ca326bd630fd3cc63f53e9b62c0ec` introduced placeholder generation; 2014 `d63863a` introduced the architect-build-era require-only branch. 2018 `eccdf05` introduced CommonJS export; `fc284ad` added the current guards (parent checked). The four historical snapshots and current generator each carry the complete file-specific Ajax.org BSD header; stripping comment decoration produces exactly the root LICENSE Git blob `4760be2a6220cf545129b233e20574f2a7bb630e`, also identical to the existing shipped `vendor/licenses/ace.txt`. This is scoped positive license evidence for the emitted loader bytes, not an inference from absence of markers or a license claim for architect-build/dryice tooling, other generated output or language modes. No extra notice or package identity. Current/history pins and exact static template, substitutions, both archive forms and all 150 hashes are verified by the new native research gate. Offline matrix validates the shared evidence record and existing parent notice mapping/bytes. Independent review, exact new-head CI and artifact inspection pending. No changes to runtime, vendor, curated profile, SBOM identities or notices. No release acceptance.


## R5.3c follow-up — Markdown Octopress contribution evidence

Baseline `c32d0f12ed6522b28f9a3b0dedf7e3a00de96e2d`: all three workflows SUCCESS (46071297199, 46071297176, 46071297249), 219 Python tests including both R5.3b regressions, native research job SUCCESS. Artifact content/independent review still open. Re-read the full historical SnipMate Markdown path at parent `036dc1ad1136f6fe057a91a60078b2032273250c` (blob `b69e1359c94e3add25a8d294f9519cf65cdf43c8`), [6f79151](https://github.com/honza/vim-snippets/commit/6f79151a2a5c67199335c0efa824f30bab630d16) (2012-05-11, ngquerol, blob `e0a614fa84e1cb8d5549f06f5b6db2183ec38a19`), [adfd3f4](https://github.com/honza/vim-snippets/commit/adfd3f4ab80966e6b024770410ba6eb175e9959d) (2012-05-12, ngquerol, blob `e4efd3c2d014fe8a9b6ba92fd08e1483aea5d1c3`). Strict consecutive unified patch replay with exact context and hunk counts reproduces both snapshots. Final raw is byte-identical to January 2013 import source `02593f7d57b4944bd857e0aeacfcd5410c0e81f2`. First patch adds 11 templates and Octopress comment, second adds pullquote and explanatory comments. All 12-template suffix bytes (from snippet blockquote to EOF, 1146 ASCII bytes) equal the Ace historical endpoint `3c6cd4d16f89de0531d7e8f06c5e791839ab9eb6` blob `a5110fc9a3d79f0aa98796237773393e4a836e97`; later Ace raw-to-current relation is already gated. Both SnipMate contribution snapshots have original MIT LICENSE blob `495ced27810b679dad1c75375e48db9ae9c9aa` and AUTHORS blob `e985d7ef11ca6ee1879dfc21ebb1d16be84dd960`; the shipped January 2013 AUTHORS was searched for the account/surname string with no match, not proof of missing author under another name.

External [imathis/octopress 79aa4eb4](https://github.com/imathis/octopress/tree/79aa4eb4f76619f0e5eef9e799cbc7e5d38f4465) (2012-04-18, preceding the SnipMate contribution, latest examined default-branch snapshot) complete 182-entry tree contains no named snippet collection. README.markdown blob `c181401caa506b8582ee9505c8e1c6e6f24d10ea` contains MIT license for software and associated documentation, copyright 2009–2011 Brandon Mathis. Inspected plugin files blockquote.rb `7fb8c2617530e97bba8f6ba289e702c818d8db87`, gist_tag.rb `74dd3b37c0acb6bfcbdbcdd73dc34b7dcd753655`, image_tag.rb `4567000707cfe65bc100ec9ed42f1ae40334ee8d`, pullquote.rb `2b59bad6a5c54b5840faf24c7f0ad2f6a693ebe4`, backtick_code_block.rb `40e7900b540be3ac69f84a1df71603780b258759`, code_block.rb `e175d44581a87d6028d92ece2c9a5338a82f412a`, video_tag.rb `6b93be8297b78f9118dadc5255f939a04e9a165f`. Observed tag syntax and plugin examples are consistent with templating purpose, not an established exact source for the snippets; video_tag is not evidence for youtube. Pullquote example documents the same markup/semantic constraint, but exact explanatory sentence origin not established (linked docs not recovered). No plugin implementation is identified as copied into the examined 12-template suffix. Do not assign Octopress MIT wholesale or add a fictitious runtime package. Proposed retain under scoped SnipMate historical attribution, with source-specific documentation/example and contributor review still open. This is research only, not a new networked source gate or independent acceptance.


## Round 7 corrective addendum — contribution licensing and differentiated decisions

Reviewed baseline `245f39d52b1f515ee2a57d597b92096fbaea0852`: two independent scoped Approve verdicts supplied by maintainer, one P4 documentation/research finding and one P5 cosmetic observation. Exact-head workflows 46072225434 / 46072225493 / 46072225405 all SUCCESS (7 jobs); reviewers report 219 tests + 1482 subtests, 7/7 tamper cases and offline wheel/sdist validation (509 vendor + 9 first-party resources). Reviewer 1 reports wheel SHA256 `221036d2459299020a14dcd7b55a805e50e2aedd67ff1bc55bd336847e7800f7`, sdist `085cf9055c9d250932d346d47e56e9fc555a98c755f9c50f3857d8a31da0879b`. These are reviewer measurements, not author-side artifact inspection. Real HAOS and full license/release acceptance remain open. The reported malformed Markdown intro was not reproducible when reading exact HEAD: both renderer and rendered file already contain the complete canonical link. Added a regression assertion for this literal.

### ABC — conditional CLA route

[Ace PR #2273 maintainer request](https://github.com/ajaxorg/ace/pull/2273#issuecomment-67634286) 2014-12-19 requires CLA before merge; [bwl21 reply](https://github.com/ajaxorg/ace/pull/2273#issuecomment-67634591) promises immediate submission; [maintainer merge comment](https://github.com/ajaxorg/ace/pull/2273#issuecomment-68647549) 2015-01-04 confirms merge (PR merged_at also verified). Historical [CONTRIBUTING.md](https://github.com/ajaxorg/ace/blob/07d01fda44ffb7d26e522ced7a8ab06a950e1096/CONTRIBUTING.md) blob `c44edcb03f4dad8762678dab9332749558798da3` explicitly requires signed CLA and links individual/corporate forms. [Individual CLA form](https://github.com/ajaxorg/ace/blob/07d01fda44ffb7d26e522ced7a8ab06a950e1096/doc/Contributor_License_Agreement-v2.pdf) blob `1c4baa870a07e67cffbbc63ac897c57a0d1ca44b`; Round 7 reviewer reports a grant to recipients of distributed software, but author-side PDF content retrieval failed and exact terms have not been independently re-read in this increment. Neither the public thread nor merge proves receipt/signature or rights scope. Ask Ace maintainer to confirm executed applicable CLA and coverage of exact ABC contribution, or obtain bwl21 explicit MIT/BSD/ISC grant on final raw blob `5c3cd677cb9c1c053638501a39b0ee896c942f31` and retained predecessor material, with authority over third-party inputs. No grant asserted pending confirmation.

Zupfnoter spreadsheet: re-confirmed tree path/blob `5cabd73eee08df8e14a2f380678ab855e528d503` (27017 bytes) at `23c8802fe93823775cddf2fe3a6e04d67b28e4ec`. Round 7 reviewer reports exactly two rows in the only sheet: `t_sn_hugo | hugo` and `t_sn_HUGO | This is ~~SN hugo~~`; no ABC material. Close spreadsheet-source lead on that independent reviewer evidence (author did not re-extract workbook). GPL/Commercial project terms still do not prove copying or a permissive grant. Final Ace raw contains nine Zupfnoter-specific triggers; optional product/risk-based exclusion remains reasonable, not mandatory.

### EDIFACT — retain recommendation, separate product decision

[Ace PR #3514 request](https://github.com/ajaxorg/ace/pull/3514#issuecomment-359528919) asks for BSD contribution headers; [bhangun assent](https://github.com/ajaxorg/ace/pull/3514#issuecomment-359614914) and [review confirmation](https://github.com/ajaxorg/ace/pull/3514#pullrequestreview-90671856) expressly confirm adding BSD headers. [Commit 9d883700](https://github.com/ajaxorg/ace/commit/9d8837002db73b69442ee37abef29ae0cc8aad3d) adds headers to mode and highlight rules, NOT raw snippets; PR merged 2018-01-24. This is public contribution licensing evidence, not a new MIT-to-BSD relicensing or blanket grant for original Java. Existing exact two-trigger transformation and original SnipMate MIT/LICENSE/AUTHORS chain remain unchanged. Retain with scoped MIT historical material and Ace BSD declaration/contribution confirmation for modifications, pending overall independent acceptance. Java-like irrelevant completions justify optional product-only removal, not a licensing-driven exclusion. No extra notice or identity.

### Gobstones and LSL — conditional alternatives

[Ace PR #3988](https://github.com/ajaxorg/ace/pull/3988) explicitly describes consistency with Gobstones IDE behavior, not provenance or license; merged 2019-07-11. Seek explicit grant covering initial javierfernandes contribution and alanrodas expansion/retained material (or documented licensed exact source, independently authored licensed replacement). Neighbor GPL/AGPL project licenses do not establish copying or cover Ace; proven copyleft input would require separately assessed compliance.

[Builders Brewery lsl-tools](https://github.com/buildersbrewery/lsl-tools/tree/1bb78bab7fca49dcf441850615fe485e7b94ef16) active successor snapshot 2026-09-16: complete 114-entry tree, ISC LICENSE blob `745ab9c4ddf451b050b8db2d3a7556e247431618`, ARCHIVE_NOTES.md blob `34d8d3f5dbcfb98411691ed15555a9ec38b78274`; no named snippet/Ace collection. ISC does not retroactively license archived blobs. Request grant from authorized rights holder covering exact `bc0d2eb9d0286050bbb56efa09cc02aaec500dba` and `352d26e7b4ed7389ddefb8365b4e2d985e63d037`, including provenance/authority over any third-party input. No GPL/LGPL assignment based on neighboring data sources. No outbound requests sent. Until confirmation, LSL and Gobstones remain license-open; optional exclusions or independently licensed replacements are alternatives, not sole possible solutions.

All four remain physically retained. Matrix still 202 rows, vendor 509, embedded 47/68 notices/54 relations. EDIFACT removed from license-risk exclusion candidate set; ABC/Gobstones/LSL optional risk-based candidates. No final decision, merge, issue closure, P1/AT-12/public release signoff. PR #36/#32 Draft/HOLD.
