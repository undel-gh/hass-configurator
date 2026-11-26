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
