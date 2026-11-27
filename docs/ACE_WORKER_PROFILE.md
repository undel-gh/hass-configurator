# #37 — Curated Ace worker and theme profile

Status: **phase 2 curated source committed; installed acceptance and retained attribution pending**.

The sole machine-readable target profile is the JSON literal delimited by
HC_WORKER_PROFILE_BEGIN / END in the first-party ace-bootstrap.js. The same
data controls worker start and creation and is read by scripts/ace_worker_profile.py.
Full upstream Ace 1.45.2 lock remains unchanged. The initial worker subset kept
all non-worker files and six workers: base, YAML, JSON, JavaScript, CSS, HTML.
The five exclusions are XML, PHP, Lua, CoffeeScript and XQuery. Unknown modes
(including SVG and SCSS aliases) have no background diagnostics; their modes
and syntax highlighting remain. HTML's own worker is retained.

The pinned Ace EditSession hook receives the loaded mode, not only the
requested extension. Unsupported modes retain useWorker preference but do
not start a worker and clear stale annotations. The legacy WorkerClient
creation hook checks module, class and exact versioned same-origin URL; no
extra importScripts argument. The UIWorkerClient config.loadModule worker
path is also guarded. These are application policy hooks, not a boundary
against arbitrary JavaScript execution. Saved settings cannot transiently
enable workers during startup. Defaults remain off.

Phase 1 policy passed #353 and rehearsal #10 on 45d857e. Phase 2 removes
five exact files, verifies 490 retained hashes against full upstream lock,
510 vendor resources, checks archive and installed filesystem closure, and
restricts actual overlay and attribution to retained workers. Historical
full-family embedded mapping preserved in docs/history. XQuery/JSONiq modes
and source relationships retained. Removed worker notices remain historical
references pending retained-runtime review. No final Lodash disposition.
Fresh exact-HEAD CI, installed artifact review and HAOS upgrade/rollback pending.

The retained marker audit records all package JS/HTML/CSS/Python files and
same-archive unminified counterparts, with exact hashes and explicit hits.
This is additional evidence, not an automated non-applicability decision.

Direct and simulated-Ingress browser policy tests are also selected for
installed wheel/sdist and Docker. Separate explicit 404 probes follow the
no-automatic-request assertion. File browser round-trips cover each excluded
language; the real installed image layers are checked by filename and exact
JS digest, not by looking only at the final filesystem. Full HAOS cache
upgrade/rollback remains a separate gate.

Round 3 review corrections: explicit regression for UIWorkerClient and worker
module loading, direct excluded Mode.createWorker calls, restored settings
startup (XML and YAML), per-language worker creation count, JSONiq alias,
and main() overlay verification wiring with a successful and a tampered
synthetic overlay. See P1_SUPPLY_CHAIN.md for the historical XML finding
and exact reviewed installed evidence. No upstream runtime change.

Maintainer disposition: both historical Lodash 4.17.21 XML-worker CVEs
remediated by physical component removal for the independently reviewed
f72a7810 runtime configuration. See P1_SUPPLY_CHAIN.md for scope, evidence,
limitations and reopen conditions. Not a blanket VEX, waiver or release signoff.

## Curated theme extension (maintainer-approved)

The #37 scope now also excludes krTheme: historical permission for the
distributed variant has not been established, and the theme is optional.
Profile schema 2 adds an explicit excluded_themes list, separate from
the unchanged worker partition. The complete upstream lock stays intact.
The target contains 489 Ace assets (six workers, 47 theme files) and 509
vendor resources. Every retained upstream asset remains byte-identical.

Remove the first-party selector entry. Before restoring saved editor
options, map both ace/theme/kr_theme and kr_theme to ace/theme/monokai,
preserving other saved options. The existing UI light/dark preference
may subsequently select a retained theme as usual. The upstream
ext-themelist.js still contains a name-only metadata entry: preserve
its reviewed bytes; this entry is not the removed CSS or module.
No claim that arbitrary direct calls to the Ace API cannot request
an absent resource; the server must return 404.

Extend selected-family validation, rehearsal overlay, native research
selection, vendor manifest/routes, retained payload marker scan and
Docker layer filename/digest inspection. Historical source evidence
remains research-only. E2E covers direct and simulated Ingress startup
with old saved settings, absence from the first-party selector, retained
theme loading and an explicit 404 after checking no automatic request.
Select these tests for installed wheel/sdist and Docker. New exact-HEAD
CI, artifact contents, independent review and real HAOS remain pending.


## Curated snippet extension (maintainer-approved 2026-11-28)

Profile schema 3 defines the exact excluded_snippets list: snippets/abc.js, snippets/cedar.js, snippets/cedarschema.js, snippets/csound_document.js, snippets/csound_orchestra.js, snippets/drools.js, snippets/edifact.js, snippets/fsl.js, snippets/gobstones.js, snippets/jsoniq.js, snippets/lsl.js, snippets/maze.js, snippets/razor.js, snippets/velocity.js, snippets/wollok.js, snippets/xquery.js. See ACE_SNIPPET_EXCLUSION_PROPOSAL.md decision record. Physical removal only; all language modes and remaining upstream bytes unchanged. 473 Ace files, 493 vendor resources. The config.loadModule hook returns absent module to a provided callback for excluded canonical string and array IDs; no load attempt or synthetic vendor stub. Retained calls delegate unchanged. This is application policy, not a sandbox. Full upstream lock remains 495 files. Direct/simulated-Ingress tests check tokenization, editing, repeated mode transitions, retained snippet registration and completion options, no automatic excluded request, explicit 404. Layer inspection checks nested path suffix and exact digest. Independent acceptance, CI artifacts and real HAOS remain open.

Second maintainer decision: 12 additional snippet payloads removed; SQL Server retained for targeted license review. Separate JSONiq/XQuery mode/grammar issues remain open. All 16 corresponding modes remain unchanged.
