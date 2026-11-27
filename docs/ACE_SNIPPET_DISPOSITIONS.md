# Ace snippet disposition matrix (R5.3)

The [machine-readable matrix](ace-snippet-dispositions.json) is canonical.
This records the approved distribution and review dispositions, not legal clearance or release acceptance.
186 assets retained, sixteen physically excluded by maintainer decision. The matrix
tracks all 202 upstream names; historical hashes are not shipped hashes.
The Ace root BSD-3-Clause declaration applies separately, not as proof of external
input rights. Additional component IDs refer to `hass_configurator/third_party/embedded.json`.
A partial attribution is not a license for the whole payload. Review-only records
are not libraries. Priority is proposed review order, not a risk rating.
Historical references record research endpoints or exact original inputs, not
necessarily a unique copy revision. See [research](ACE_SNIPPET_RESEARCH.md).

The offline source inventory gate checks exact row closure, hashes against
the lock and vendor manifest, generated stub bytes by their exact hash,
component mappings, source pin consistency for mapped records and this rendered
document. The native research gate separately compares all 202 upstream row types and
the 52 current source Git blobs (36 retained nonempty, 16 archive-only) against
the immutable checkout and static
payload/empty-stub evidence. It does not replay all historical transformations
or adjudicate rights. R5.3b maps the 150 generated loaders to the exact Ace
exportAce extModules template, with a file-specific BSD-3-Clause header identical
to the existing parent notice. Independent artifact inspection and review remain open.

## Counts

| Evidence class | Count |
| --- | ---: |
| exact-generated-empty-stub | 150 |
| exact-source-license-open | 1 |
| historical-endpoint-review-open | 15 |
| microsoft-partial | 1 |
| snipmate-derived | 3 |
| snipmate-exact | 22 |
| snipmate-modified | 8 |
| textmate-exact | 2 |

Maintainer-approved exclusions: abc, cedar, cedarschema, csound_document, csound_orchestra, drools, edifact, fsl, gobstones, jsoniq, lsl, maze, razor, velocity, wollok, xquery.
EDIFACT removal is product-only; historical MIT/BSD evidence retained.
Language modes are unchanged. Reinstatement requires explicit approval and renewed review.

## Nonempty payloads

| Snippet | Distribution | Evidence class | Additional components | Priority | Proposed disposition | Exclusion reason | Remaining review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| abc | excluded | historical-endpoint-review-open | — | elevated | excluded-reassessment-open | Zupfnoter-specific templates; low HA Configurator utility and unresolved CLA/grant. | PR #2273 CLA receipt/signature and applicable grant unconfirmed; historical Zupfnoter match is not a GPL assignment. No outreach; reassess if reinstatement requested. |
| actionscript | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| c_cpp | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| cedar | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Authorization policy templates; low HA Configurator utility does not warrant further source rights research. | PR #5944 policy scaffolds; no named snippets in examined vscode-cedar tree. Individual contribution/source rights open. Historical evidence retained; reassess only if reinstatement is requested. |
| cedarschema | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Authorization schema templates; low HA Configurator utility does not warrant further source rights research. | PR #5944 schema scaffolds; cited vscode-cedar TextMate grammar is not snippet provenance. Individual contribution/source rights open. Historical evidence retained; reassess only if reinstatement is requested. |
| clojure | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| coffee | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| csound_document | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Audio synthesis document templates; low HA Configurator utility does not warrant further source rights research. | One XML scaffold; mode Pygments/Csound references do not establish snippet provenance. Original contribution review. Historical evidence retained; reassess only if reinstatement is requested. |
| csound_orchestra | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Audio synthesis orchestra templates; low HA Configurator utility does not warrant further source rights research. | Nine language scaffolds; mode references do not establish snippet provenance. Original contribution review. Historical evidence retained; reassess only if reinstatement is requested. |
| css | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| dart | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| diff | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| django | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| drools | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Business rules templates; low HA Configurator utility does not warrant further source rights research. | Three rule/query/declare scaffolds; mode BSD header and drools.org reference do not establish separate snippet rights. Historical evidence retained; reassess only if reinstatement is requested. |
| edifact | excluded | snipmate-derived | — | standard | excluded-reassessment-open | Product-only: mostly Java templates are irrelevant to EDIFACT. Scoped MIT/BSD evidence retained historically; no licensing-driven exclusion. | Historical Java two-trigger transformation, SnipMate MIT and AUTHORS, and PR #3514 BSD contribution confirmation preserved. Product-only exclusion; reassess if reinstatement requested. |
| erlang | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| fsl | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Finite-state machines templates; low HA Configurator utility does not warrant further source rights research. | Same-author JSSM MIT examples share metadata conventions, not exact header. machine_license is template content, not a grant. Historical evidence retained; reassess only if reinstatement is requested. |
| gobstones | excluded | historical-endpoint-review-open | — | elevated | excluded-reassessment-open | Educational language; low HA Configurator utility does not justify additional rights research or contributor outreach. | Initial/expanded contribution history remains open; PR #3988 cites behavior, not source rights. No outreach; reassess if reinstatement requested. |
| graphqlschema | retained | historical-endpoint-review-open | — | standard | retain-review-open | — | PR #3144 documents self-authored schema support and rename; 5/5 raw payload exact to current. Historical Ace BSD declaration; no explicit contribution grant/CLA receipt found. External input review remains bounded/open. |
| haml | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| haskell | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| html | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| io | retained | textmate-exact | ace-textmate-io-snippets | standard | retain-review-open | — | All 10 original TextMate plist entries exactly mapped; original bundle permission retained. Review exceptions and source-specific scope, not other Io grammar. |
| java | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| javascript | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| jsoniq | excluded | historical-endpoint-review-open | — | elevated | excluded-reassessment-open | Specialized query templates; low HA Configurator utility does not warrant further source rights research. Separate mode/grammar review remains open. | Identical raw to XQuery; legacy static module, source rights open. XQLint Apache and REx grant do not cover snippets. Historical evidence retained; reassess only if reinstatement is requested. |
| jsp | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| liquid | retained | snipmate-derived | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical HTML plus fixed 26-line prefix. MIT covers historical SnipMate material only; prefix/HTML changes and individual contributions open. |
| lsl | excluded | exact-source-license-open | — | elevated | excluded-reassessment-open | Second Life scripting; low HA Configurator utility does not justify historical grant outreach. | Exact Builders Brewery historical blobs and missing historical grant preserved; ISC successor not retroactive, KWDB/viewer derivation open. No outreach; reassess if reinstatement requested. |
| lua | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| makefile | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| markdown | retained | snipmate-modified | ace-snipmate-snippets | elevated | retain-review-open | — | Octopress-tag templates introduced by two exact 2012 SnipMate patches under existing MIT; 12-template suffix retained exactly. External documentation/example origin and individual contributor attribution review remain open. |
| maze | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Specialized language templates; low HA Configurator utility does not warrant further source rights research. | Two entries with duplicate trigger and distinct descriptions. Preserve both; original contribution review. Historical evidence retained; reassess only if reinstatement is requested. |
| perl | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| php | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| python | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| r | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| razor | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | ASP.NET templates; low HA Configurator utility does not warrant further source rights research. | Single 35-byte conditional scaffold; original contribution review. Historical evidence retained; reassess only if reinstatement is requested. |
| robot | retained | historical-endpoint-review-open | — | elevated | retain-review-open | — | PR #4614 includes explicit use/modify/copy/redistribute grant; same contributor added 5 then finalized 11 triggers. Final raw exact to current. Candidate retain with parent Ace BSD; external input/independent review remains open. |
| rst | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| ruby | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| sh | retained | snipmate-modified | ace-snipmate-snippets | standard | retain-review-open | — | Historical SnipMate MIT and AUTHORS retained; reconstructed Ace delta and later contribution/external rights review remain open. |
| snippets | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| sql | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| sqlserver | retained | microsoft-partial | ace-sqlserver-microsoft-template-material | elevated | retain-review-open | — | Retain for targeted research: PRs #2457/#2460 and three immutable historical snapshots verified; official 2018 MIT SSMS source, 4+6 scoped shared blocks; earlier source grant and adapted content remain open. |
| tcl | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| tex | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| textile | retained | snipmate-exact | ace-snipmate-snippets | standard | retain-review-open | — | Exact historical SnipMate decoded payload; original MIT and AUTHORS retained. Wrapper and individual/external rights review remains open. |
| vala | retained | textmate-exact | ace-textmate-vala-snippets | elevated | retain-review-open | — | 31/31 TextMate dictionaries mapped. Original Redcar Bundles 2009 TextMate permission preserved verbatim alongside later Butcher MIT notice. Pinned 14 inherited files, 17 additions, class/printf changes and rename closure. Independent review pending; no grammar or final clearance. |
| velocity | excluded | historical-endpoint-review-open | — | standard | excluded-reassessment-open | Java template language templates; low HA Configurator utility does not warrant further source rights research. | Six common directive templates. Original contribution and external input review. Historical evidence retained; reassess only if reinstatement is requested. |
| wollok | excluded | snipmate-derived | — | elevated | excluded-reassessment-open | Educational language templates; low HA Configurator utility does not warrant further source rights research. Historical scoped SnipMate MIT evidence retained in archive. | 16 ordered shared Java spans; MIT covers retained Java material only; adaptations/new triggers and original contribution rights open. Historical evidence retained; reassess only if reinstatement is requested. |
| xquery | excluded | historical-endpoint-review-open | — | elevated | excluded-reassessment-open | XML query templates; low HA Configurator utility does not warrant further source rights research. Separate mode/grammar review remains open. | Identical raw to JSONiq; legacy static module, source rights open. XQLint Apache and REx grant do not cover snippets. Historical evidence retained; reassess only if reinstatement is requested. |

## Empty generated stubs

All rows below have identical structural loader semantics with a name-specific
module ID, not an empty file. Exact published hashes are recorded in JSON.
The shared loader is mapped to `Makefile.dryice.js` (`exportAce`, `extModules`),
with a file-specific BSD-3-Clause header matching `vendor/licenses/ace.txt`.
The historical guarded-export variant matches the current template exactly.
The native audit verifies all 150 minified and unminified archive members by
static substitution; no separate library or notice is created. This mapping is
review-open; no independent per-language license grant or payload is inferred.

| Snippet | Proposed disposition |
| --- | --- |
| abap | retain-stub-review-open |
| ada | retain-stub-review-open |
| alda | retain-stub-review-open |
| apache_conf | retain-stub-review-open |
| apex | retain-stub-review-open |
| applescript | retain-stub-review-open |
| aql | retain-stub-review-open |
| asciidoc | retain-stub-review-open |
| asl | retain-stub-review-open |
| assembly_arm32 | retain-stub-review-open |
| assembly_x86 | retain-stub-review-open |
| astro | retain-stub-review-open |
| autohotkey | retain-stub-review-open |
| basic | retain-stub-review-open |
| batchfile | retain-stub-review-open |
| bibtex | retain-stub-review-open |
| c9search | retain-stub-review-open |
| cirru | retain-stub-review-open |
| clue | retain-stub-review-open |
| cobol | retain-stub-review-open |
| coldfusion | retain-stub-review-open |
| crystal | retain-stub-review-open |
| csharp | retain-stub-review-open |
| csound_score | retain-stub-review-open |
| csp | retain-stub-review-open |
| csv | retain-stub-review-open |
| curly | retain-stub-review-open |
| cuttlefish | retain-stub-review-open |
| d | retain-stub-review-open |
| dockerfile | retain-stub-review-open |
| dot | retain-stub-review-open |
| eiffel | retain-stub-review-open |
| ejs | retain-stub-review-open |
| elixir | retain-stub-review-open |
| elm | retain-stub-review-open |
| flix | retain-stub-review-open |
| forth | retain-stub-review-open |
| fortran | retain-stub-review-open |
| fsharp | retain-stub-review-open |
| ftl | retain-stub-review-open |
| gcode | retain-stub-review-open |
| gdresource | retain-stub-review-open |
| gdscript | retain-stub-review-open |
| gdshader | retain-stub-review-open |
| gherkin | retain-stub-review-open |
| gitignore | retain-stub-review-open |
| glsl | retain-stub-review-open |
| golang | retain-stub-review-open |
| groovy | retain-stub-review-open |
| groq | retain-stub-review-open |
| handlebars | retain-stub-review-open |
| haskell_cabal | retain-stub-review-open |
| haxe | retain-stub-review-open |
| hjson | retain-stub-review-open |
| html_elixir | retain-stub-review-open |
| html_ruby | retain-stub-review-open |
| ini | retain-stub-review-open |
| ion | retain-stub-review-open |
| jack | retain-stub-review-open |
| jade | retain-stub-review-open |
| jexl | retain-stub-review-open |
| json | retain-stub-review-open |
| json5 | retain-stub-review-open |
| jssm | retain-stub-review-open |
| jsx | retain-stub-review-open |
| julia | retain-stub-review-open |
| kotlin | retain-stub-review-open |
| latex | retain-stub-review-open |
| latte | retain-stub-review-open |
| less | retain-stub-review-open |
| lisp | retain-stub-review-open |
| livescript | retain-stub-review-open |
| logiql | retain-stub-review-open |
| logtalk | retain-stub-review-open |
| luapage | retain-stub-review-open |
| lucene | retain-stub-review-open |
| mariadb | retain-stub-review-open |
| mask | retain-stub-review-open |
| matlab | retain-stub-review-open |
| mediawiki | retain-stub-review-open |
| mel | retain-stub-review-open |
| mips | retain-stub-review-open |
| mixal | retain-stub-review-open |
| mushcode | retain-stub-review-open |
| mysql | retain-stub-review-open |
| nasal | retain-stub-review-open |
| nginx | retain-stub-review-open |
| nim | retain-stub-review-open |
| nix | retain-stub-review-open |
| nsis | retain-stub-review-open |
| nunjucks | retain-stub-review-open |
| objectivec | retain-stub-review-open |
| ocaml | retain-stub-review-open |
| odin | retain-stub-review-open |
| partiql | retain-stub-review-open |
| pascal | retain-stub-review-open |
| pgsql | retain-stub-review-open |
| php_laravel_blade | retain-stub-review-open |
| pig | retain-stub-review-open |
| plain_text | retain-stub-review-open |
| plsql | retain-stub-review-open |
| powershell | retain-stub-review-open |
| praat | retain-stub-review-open |
| prisma | retain-stub-review-open |
| prolog | retain-stub-review-open |
| properties | retain-stub-review-open |
| protobuf | retain-stub-review-open |
| prql | retain-stub-review-open |
| puppet | retain-stub-review-open |
| qml | retain-stub-review-open |
| raku | retain-stub-review-open |
| rdoc | retain-stub-review-open |
| red | retain-stub-review-open |
| redshift | retain-stub-review-open |
| rhtml | retain-stub-review-open |
| rust | retain-stub-review-open |
| sac | retain-stub-review-open |
| sass | retain-stub-review-open |
| scad | retain-stub-review-open |
| scala | retain-stub-review-open |
| scheme | retain-stub-review-open |
| scrypt | retain-stub-review-open |
| scss | retain-stub-review-open |
| sjs | retain-stub-review-open |
| slim | retain-stub-review-open |
| smarty | retain-stub-review-open |
| smithy | retain-stub-review-open |
| soy_template | retain-stub-review-open |
| space | retain-stub-review-open |
| sparql | retain-stub-review-open |
| stylus | retain-stub-review-open |
| svg | retain-stub-review-open |
| swift | retain-stub-review-open |
| terraform | retain-stub-review-open |
| text | retain-stub-review-open |
| toml | retain-stub-review-open |
| tsv | retain-stub-review-open |
| tsx | retain-stub-review-open |
| turtle | retain-stub-review-open |
| twig | retain-stub-review-open |
| typescript | retain-stub-review-open |
| vbscript | retain-stub-review-open |
| verilog | retain-stub-review-open |
| vhdl | retain-stub-review-open |
| visualforce | retain-stub-review-open |
| vue | retain-stub-review-open |
| xml | retain-stub-review-open |
| yaml | retain-stub-review-open |
| zeek | retain-stub-review-open |
| zig | retain-stub-review-open |
