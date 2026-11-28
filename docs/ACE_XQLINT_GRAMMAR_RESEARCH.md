# R5.4a — XQLint grammar and eXide mode lineage research

Status: **research-open / release HOLD**. Baseline `2397c9e3ac538f9ea52a2d31165cb9cccb20ac8e` (Round 8 accepted). No curated asset or runtime changes; XQuery worker and XQuery/JSONiq snippets remain excluded. Scope: both retained mode assets.

## XQLint grammar continuity

All inspected tokenizer path-history entries have William Candillon as author. First XQuery parser grammar (2012-11-17, 900d74d9) had no license header; BSD header appears in 5920dd75 (2012-11-29). Tokenizer introductions 840c3f05 (2013-01-06) and 23cca84b (2013-03-18) carry Ajax.org 2010 BSD headers. Last old XQuery path 8448d960 (2013-03-12); JSONiq context-item change 642b4e00 (2013-05-02). Apache-2.0 LICENSE first added at 78ac2d1d (2014-03-09), same blob as shipped XQLint reference. Both grammars reintroduced at 31da7b6b (2014-03-20) without former BSD/AMD wrappers. The old grammar body is byte-identical for XQuery at July 2014 and JSONiq at March 20. JSONiq c3494acc (2014-03-23) changes QuotString and inserts JSONChar, JSONCharRef and JSONPredefinedCharRef; the exact bounded patch reproduces the July grammar. Two body comparisons and the delta are explicit named source relations. Immutable Git blob checks precede comparison.

Exploratory production-occurrence comparison (duplicates retained; RHS whitespace collapsed, not semantic equivalence): earliest parser 335 vs first lexer 52, 39 shared; December 2012 parser 337 vs first lexer 52, 43 shared; March XQuery 67 vs first JSONiq 67, 65 shared (NCName and NonNCNameChar differ); March 2014 JSONiq 67 to July 70, 66 unchanged, one changed, three added. This corroborates internal ancestry, not a full replay. Standard syntax and JSONiq extensions do not establish independent implementation or rights to copied grammar text. Exact earlier external sources remain open; do not infer W3C or CC license from grammar similarity.

Historical BSD header text matches shipped Ace license after comment/whitespace normalization, not raw equality. Existing XQLint Apache-2.0 notice retained. [REx author permission](https://github.com/GuntherRademacher/rex-parser-generator/issues/80#issuecomment-7224280132) separately covers generated output including modified/minified versions, not grammar inputs. Existing tokenizer literal/shared lexer/wrapper relations unchanged. Gruntfile pins both inputs and REx command. July tokenizer outputs at 5e398389 match the existing mapped blobs. No regeneration with historical REx binary performed.

| Source | Git blob |
|---|---|
| [XQueryParser.ebnf @ 900d74d9](https://github.com/wcandillon/xqlint/blob/900d74d9fda1c2758af045ae6e970af969a43ae4/lib/XQueryParser.ebnf) | `d189eeeb83972c985d18c64791a5fbec520fce95` |
| [XQueryParser.ebnf @ 4244c5a9](https://github.com/wcandillon/xqlint/blob/4244c5a94a6ff9acfe77c7e53e2e0e194b21cda2/lib/XQueryParser.ebnf) | `8c968ad34b64cc8a937bb83f5e7e8b48bb67d80b` |
| [XQueryTokenizer.ebnf @ 840c3f05](https://github.com/wcandillon/xqlint/blob/840c3f05963eb07390112e582c1a2e5affbbb432/lib/XQueryTokenizer.ebnf) | `2dbde102f96306b9c23bddf0271946fad2a91f76` |
| [JSONiqTokenizer.ebnf @ 23cca84b](https://github.com/wcandillon/xqlint/blob/23cca84bb0c18a99362e3890f92b0e3ee3740de3/lib/JSONiqTokenizer.ebnf) | `b03294875246a4b5d7ff1e84af5c9b984b69085a` |
| [LICENSE @ 78ac2d1d](https://github.com/wcandillon/xqlint/blob/78ac2d1db7b90297e0e043c22169937511fe344c/LICENSE) | `e06d2081865a766a8668acc12878f98b27fc9ea0` |
| [Gruntfile.js @ 1778846e](https://github.com/wcandillon/xqlint/blob/1778846ed8e707780d791fd3ffb41feccdf9de04/Gruntfile.js) | `853b6d0efb4076c7442f925c64a709e6bac49326` |
| [XQueryTokenizer.ebnf @ 8448d960](https://github.com/wcandillon/xqlint/blob/8448d96067f3889e8ceb45811c0a5fb5cc82c304/lib/XQueryTokenizer.ebnf) | `51fb83f8417419f879143a0dbc7ddbeae31f7e66` |
| [JSONiqTokenizer.ebnf @ 642b4e00](https://github.com/wcandillon/xqlint/blob/642b4e0053a8fe06cbf44b033dcf71c7a4251f47/lib/JSONiqTokenizer.ebnf) | `36d200b26cfe39181e163c8c1d204550b62bfb6e` |
| [JSONiqTokenizer.ebnf @ 31da7b6b](https://github.com/wcandillon/xqlint/blob/31da7b6be8b8c3245ff6fb23c94904f5b63287aa/lib/lexers/JSONiqTokenizer.ebnf) | `f0a16cc174b875e5b7d77625b4c112123f487e98` |
| [XQueryTokenizer.ebnf @ 1778846e](https://github.com/wcandillon/xqlint/blob/1778846ed8e707780d791fd3ffb41feccdf9de04/lib/lexers/XQueryTokenizer.ebnf) | `d6514598ccf8d385e6baf70319745410630a5c79` |
| [JSONiqTokenizer.ebnf @ 1778846e](https://github.com/wcandillon/xqlint/blob/1778846ed8e707780d791fd3ffb41feccdf9de04/lib/lexers/JSONiqTokenizer.ebnf) | `eff1da00eda14040b50cb2891ea2bcd0f9ba4385` |

## Separate retained mode issue: eXide

Pre-import [eXide snapshot](https://github.com/eXist-db/eXide/blob/e2aaec73a45892b358ded79dbc9ae8f19433a677/src/ace-modes.js) precedes [Ace import](https://github.com/ajaxorg/ace/commit/517e88f2f077263e49159c7b1742b5f3a7c605b4) on 2012-02-06. Original carries Copyright 2011 Wolfgang Meier and GPL-3.0-or-later declaration. Initial mode, behaviour and highlighter have GPL headers; merge snapshot still has GPL header. [PR #645 submission](https://github.com/ajaxorg/ace/pull/645#issuecomment-4857466) and [maintainer acknowledgment](https://github.com/ajaxorg/ace/pull/645#issuecomment-4951252) establish receipt of Candillon's CLA (2012-04-04), not signed agreement text or separate rights from Meier. Candillon changed mode header to MPL 1.1/GPL 2.0/LGPL 2.1 at d069b850 (2012-04-13), crediting both; bulk BSD header change at 8b971619 (2012-09-06). Header changes do not independently establish authorization for inherited material.

Four named method bodies compared from their function declarations through terminators, removing indentation and blank lines only:

| Method | eXide -> initial Ace | Initial Ace -> current XQuery | Initial Ace -> current JSONiq |
|---|---|---|---|
| getNextLineIndent | exact normalized | exact normalized | exact normalized |
| checkOutdent | exact normalized | regex parenthesized | exact normalized |
| autoOutdent | exact normalized | exact normalized | exact normalized |
| toggleCommentLines | exact normalized | exact normalized | exact normalized |

Names/markers are also present in the official minified distribution; both vendored blob IDs match official pinned build blobs (XQuery 4d2b8f6870eab5e565d059a78c3758b97124f5c2; JSONiq afb8381588080c01ba4566cbaf7427075447bed8). Bounded source comparison and marker/identity check, not AST equivalence of whole generated modes or full history replay. No finding about all shared behaviour or XML modules. Record as review-only inventory, not new library/version/PURL or GPL classification of the current whole mode. Existing notices alone do not resolve the earlier contribution rights.

| Source | Git blob |
|---|---|
| [ace-modes.js @ e2aaec73](https://github.com/eXist-db/eXide/blob/e2aaec73a45892b358ded79dbc9ae8f19433a677/src/ace-modes.js) | `88546dc2f58165814391871b940536b571965689` |
| [LICENSE.txt @ e2aaec73](https://github.com/eXist-db/eXide/blob/e2aaec73a45892b358ded79dbc9ae8f19433a677/LICENSE.txt) | `94a9ed024d3859793618152ea559a168bbcbb5e2` |
| [xquery.js @ 517e88f2](https://github.com/ajaxorg/ace/blob/517e88f2f077263e49159c7b1742b5f3a7c605b4/lib/ace/mode/xquery.js) | `aa2883a31419aaffe4825744da972eac361c4ade` |
| [xquery.js @ d1366c29](https://github.com/ajaxorg/ace/blob/d1366c2916665640ef0840340d8d5316b8124599/lib/ace/mode/xquery.js) | `c9ab2d416fb47e7ff9efba7397f064635c9aa29f` |
| [xquery.js @ d069b850](https://github.com/ajaxorg/ace/blob/d069b8508c684b407bfcadbe71e81af38be181e4/lib/ace/mode/xquery.js) | `afcc690eeb284804f0f802ae5b323a7b3ee8040a` |
| [xquery.js @ 8b971619](https://github.com/ajaxorg/ace/blob/8b971619b73f23df37c8ef915bd76d656b711943/lib/ace/mode/xquery.js) | `0bf786e16876a763e19c9c4b43e3d8854cc8e17c` |
| [xquery.js @ 68d7fd1c](https://github.com/ajaxorg/ace/blob/68d7fd1c0f5ac50cdb610bf06b86074eab3be652/lib/ace/mode/xquery.js) | `840a4c31d2186d2d7d68be901d22e551eca4496b` |
| [jsoniq.js @ 68d7fd1c](https://github.com/ajaxorg/ace/blob/68d7fd1c0f5ac50cdb610bf06b86074eab3be652/lib/ace/mode/jsoniq.js) | `a02ee1608c352d35ee7d5ce4b7253e445ff43af8` |

Targeted public history/PR search did not locate a separate Meier permission; not proof none exists. No outreach performed. **Release gate:** verify original grant or other authorized license basis, or obtain explicit maintainer approval of scoped removal/replacement of both affected modes after dependency and compatibility analysis. No silent runtime change. Existing Round 8 technical acceptance remains scoped. Independent review, exact-HEAD CI/artifacts pending. No final license clearance.
