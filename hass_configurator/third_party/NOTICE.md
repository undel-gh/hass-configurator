# Third-party notices — HASS Configurator

This package includes offline third-party resources. Their upstream license
texts are distributed unmodified in `../vendor/licenses/` and `licenses/`.
See `inventory.json` for component-to-file ownership, checksums and
immutable license-source references. Existing vendor manifest covers the
original 460 resources; this separate inventory covers inherited JS/font
assets and notices without making notice files web routes.

- Ace 1.9.6: Ajax.org B.V., BSD-3-Clause; complete selected upstream build family.
- Materialize 0.100.2: Copyright 2014-2017 Materialize, MIT.
- Material Design Icons 3.4.93: Austin Andrews, reserved font name Material
  Design Icons (OFL-1.1); upstream notice also credits Google material icons
  (Apache-2.0). No modified font or standalone font sale.
- jQuery 3.6.0: OpenJS Foundation and other contributors, MIT.
- js-yaml 4.1.0: Vitaly Puzrin, MIT.
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

Ace workers contain JSHint 2.11.0, Underscore 1.10.2, CSSLint 1.0.5,
Parser-Lib 1.1.2, CoffeeScript 2.2.1, luaparse 0.3.1, php.js 0.1.0,
JSON.org json_parse (2008-09-18, public domain statement), adapted yaml-lint,
legacy js-yaml 3.x-style code, modular Lodash, HTML5 SAX parser, XMLDOM,
XQLint and additional Browserify shims. Review of transitive licenses,
themes/snippets and unresolved exact versions remains OPEN. jQuery 3.6.0
also embeds Sizzle 2.3.6; its upstream MIT text is included.

**JSHint historical restriction:** the JSHint 2.11.0 top-level MIT text and
JSON-licensed source header are both retained. The latter's field-of-use
condition is not MIT; later JSHint relicensing must not be silently applied
to historical bytes. Public-release decision/remediation required (#9).

The inherited Google Material Icons font exactly matches the 2019-12-29
HASS Configurator introduction commit 6e3611006c84cf103318a9c4bb5a661e5da73411;
the previous HTML used Google's online stylesheet. The original CDN archive
was not recorded. A historical official repository WOFF2 differs. Do not
claim the original binary origin is fully resolved.
