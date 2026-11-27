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
