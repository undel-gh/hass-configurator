# P1 supply-chain audit — Issue #9

Status: **audit implementation candidate; not release acceptance**.
Source baseline: master `196907aa1e37d75adf0bfde7df45c43bcd3d01c0`.
Owner: maintainer. No runtime dependency/version upgrade or privilege change
in this audit candidate.

## Inventory and evidence

Existing `docs/ace-builds-1.9.6-lock.json` pins the official npm tarball
`https://registry.npmjs.org/ace-builds/-/ace-builds-1.9.6.tgz`, SHA-512 SRI,
SHA-256 and all 440 files in **src-min-noconflict**. The existing vendor
manifest pins the Materialize and MDI archives, CSS-relative font closure and
license texts. Existing CI compares exact official archive bytes. Do not
mix Ace families; workers/snippets/extensions belong to the same archive.
The new separate packaged `hass_configurator/third_party/inventory.json`
assigns all original vendored assets plus the four inherited JS/font files
to seven components, fingerprints inherited assets and additional licenses,
and records the source vendor-manifest hash. It does not change the
fingerprint formula or HTTP asset allowlist.

The added notices include original jQuery/js-yaml MIT texts and historical
Roboto/Material Icons Apache-2.0 texts obtained from immutable upstream
GitHub commits. The original MDI OFL notice includes Google attribution.
Roboto is a separate font component, not assumed to be MIT because
Materialize is MIT. Font name-table evidence is collected from every
shipped Roboto WOFF/WOFF2 and the inherited Material Icons WOFF2. Font name-table versions are recorded, not invented upstream archive identities. A license text alone is not proof of the binary's origin;
review the metadata, exact font licenses/copyrights and any NOTICE
obligations before release.

`scripts/audit_supply_chain.py source` produces a deterministic CycloneDX
1.5 **source/locked application BOM**; file-level hashes are properties,
not false package archive hashes. The five exact Python wheel hashes
come from `requirements/docker-runtime.lock`. The declared licenses
(BSD-3-Clause for GitPython/gitdb/smmap, MIT for pyotp, PSF-2.0 for legacy-cgi)
must be checked against actual wheel metadata and shipped notices. The
source BOM is not an entire OS/container SBOM. Actual install inventories
record versions, metadata, license text/file hashes, dependency metadata,
and Debian binary/source versions for the fork image; standalone
wheel/sdist use the resolver and can differ from the Docker lock.
Do not confuse their actual resolved versions with locked Docker pins.

## Risk register — initial review 2026-11-26

No automatic acceptance of any vulnerability. Owner: maintainer;
review every finding before public release. The database scan is evidence,
not exploitability determination; report-only findings do not mean
release approved. New/unknown high or critical findings require explicit
triage and remediation or a justified dated decision under project policy.

| Component / exposure | Evidence and decision |
| --- | --- |
| js-yaml 4.1.0 | [GHSA-mh29-5h37-fv8m](https://github.com/advisories/GHSA-mh29-5h37-fv8m), [GHSA-h67p-54hq-rp68](https://github.com/advisories/GHSA-h67p-54hq-rp68), [GHSA-52cp-r559-cp3m](https://github.com/advisories/GHSA-52cp-r559-cp3m), [GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj), [GHSA-2883-xcg3-v3hh](https://github.com/advisories/GHSA-2883-xcg3-v3hh) (CVE-2026-84375): five distinct advisory matches on 4.1.0. The last advisory has a fixed boundary of 4.3.2; select a reviewed compatible release covering all five and re-scan at selection time. See #33. The editor's check_lint invokes jsyaml.load on editable YAML in the main browser thread; file content can be untrusted. Prototype effects and CPU exhaustion need assessment, update to a reviewed fixed compatible build or remove/replace path. Separate remediation, **OPEN / release gate**, no waiver. |
| Ace 1.9.6 | 2022 build, embedded workers/parsers/third-party snippets may have additional licensing/vulnerabilities not covered by package-level scan. Inspect upstream source and worker contents; specifically identify YAML parser version and advisories. **OPEN**. |
| Materialize 0.100.2 | [CVE-2022-25349](https://www.cve.org/CVERecord?id=CVE-2022-25349), [GHSA-7jvx-f994-rfw2](https://github.com/advisories/GHSA-7jvx-f994-rfw2), [GHSA-7752-f4gf-94gc](https://github.com/advisories/GHSA-7752-f4gf-94gc), [GHSA-98f7-p5rc-jx67](https://github.com/advisories/GHSA-98f7-p5rc-jx67), [GHSA-rg3q-jxmp-pvjj](https://github.com/advisories/GHSA-rg3q-jxmp-pvjj): four distinct matches, including autocomplete/tooltip XSS paths. See #34 for reachability and remediation. Editor initializes autocomplete using HA data. Strict script CSP and safe sinks reduce exposure, not proof of non-applicability. Review data paths and replace/patch vulnerable component; coordinate #31. **OPEN / release gate**. |
| jQuery 3.6.0 | Legacy release; check current package advisories and compatibility before upgrade. **OPEN** until scan/review. |
| GitPython 3.2.1 / gitdb / smmap | Hash locked; [CVE-2026-114145](https://github.com/advisories/GHSA-83vg-56qc-22m7) fixed in 3.2.1 per upstream, other advisories require actual scan. Git privileged routes default off (#7/#27); no broad exemption for enabled Git or older resolver-installed versions. **OPEN** until scan/review. |
| PyOTP / legacy-cgi | Lock and actual install evidence required. cgi removed in Python 3.13; legacy-cgi is compatibility debt, review lifecycle and replace parser in separate scope rather than silently change HTTP handling. **OPEN** until scan/review. |
| Python base image / Debian | Immutable base is not continuously patched. Scan actual Debian source versions and Python packages; separately review CPython/OpenSSL/base OS security coverage and refresh digest if needed. No complete CPE scan claimed. #25 multi-arch packaging separate. **OPEN**. |
| Fonts, legacy JS provenance | Full notice texts and SHA-256 pinned; compare JS to official npm archives and collect font metadata. Exact original font release and embedded attribution not assumed. **OPEN** until evidence reviewed. |

## Reproduce and update

From reviewed checkout, use existing offline vendor runbook for npm archives.
For the inherited JS comparison download exact jquery@3.6.0,
js-yaml@4.1.0 and materialize-css@0.100.2 npm archives using npm pack
--ignore-scripts (build-time only). Capture registry metadata/SRI and
archive comparison. Fetch the immutable Materialize Git JS file to
`/tmp/materialize-tag.js` using the `git_url` in the inventory. The audit
checks the pinned SHA-256/SRI, member digest and exact observed deviations;
this is evidence, not a waiver or a silent normalization. The audit never
overwrites runtime files.

```sh
python scripts/audit_supply_chain.py source --output /tmp/source.cdx.json
# Optional font metadata: install fontTools and Brotli in a disposable audit env.
python scripts/audit_supply_chain.py source --output /tmp/source.cdx.json --archives /tmp --fonts
# Run with the installed artifact's Python, from outside the checkout:
python /path/to/checkout/scripts/audit_supply_chain.py installed --label wheel --output /tmp/wheel-installed.json
# For the fork container use --locked --debian12.
# From checkout (network allowed in CI/audit host only):
python scripts/audit_supply_chain.py scan --installed /tmp/wheel-installed.json /tmp/sdist-installed.json /tmp/docker-installed.json --output /tmp/osv.json
```

Use a fresh checkout for wheel/sdist packaging checks (as CI does). If reusing
an explicitly disposable local build checkout, remove stale generated
`*.egg-info/` (especially `SOURCES.txt`) and build outputs before rebuilding.
A cached setuptools source list can mask a missing `MANIFEST.in` inclusion;
never infer package completeness from a dirty build.

CI uploads source BOM, legacy archive comparison, font metadata, actual
wheel/sdist/image install inventories and OSV package/version results.
A query error, malformed/incomplete response or missing inventory fails
the scan step; a completed query with findings is not zero findings.
OSV npm/PyPI/Debian:12 queries cover named versioned packages only; not
all embedded code, CPython/CPE, fonts or all OS vulnerabilities. Review
the actual reports and upstream advisories; archive release evidence
with exact SHA/date and explicit risk decisions. No runtime telemetry.

For a dependency update: choose exact upstream release; review license,
maintainer/provenance, archive SRI/SHA and advisories; update pinned
lock and regenerate vendor files with reviewed archive; recompute
inventory hashes/notice ownership; update notices and regenerate BOM;
review diffs, installed artifact contents, offline/dynamic browser E2E
and Docker reproducibility; repeat installed artifact and vulnerability
scan and record exact-HEAD results. Do not simply refresh the lock or
trust a successful scan as release signoff. Optional installed RECORD
verification is separate defense-in-depth (not proof of origin); this
candidate verifies packaged application resource bytes and versions,
not all installed distribution RECORD entries.

Trace NFR-002/011, ADR-006. #9 remains open until exact-HEAD CI, evidence
and independent review, plus explicit disposition of findings.

## Initial CI evidence and disposition — 2026-11-26

Reviewed exact source `58c02705a1852fcf913c42e1b57c2f62b6704828`,
[run 45869578006](https://github.com/undel-gh/hass-configurator/actions/runs/45869578006):
4/4 required jobs passed, 140 Python tests; browser source 27 passed/1 skipped,
wheel/sdist/image each 6 passed. Two clean amd64 image builds identical:
`sha256:2f642e74d07185623ab18918f465ebaaa89d3fcdf3ab6e3ee86886217124a95a`.
Artifacts: source 15142646117; installed/OSV 15142646436.
These are historical results, not a claim about later HEADs or release acceptance.

### Exact legacy source findings

- jQuery: official npm member and immutable upstream Git release file match;
  inherited JS differs by the absent final LF only. Preserve and pin this
  byte relationship; no semantic change observed. Review upgrade separately.
- js-yaml: official npm member and immutable upstream Git release file match;
  inherited file replaces one UTF-8 NBSP within a string by ASCII space and
  lacks final LF. This is semantic drift, not harmless whitespace. #33 owns
  remediation alongside five matched advisories.
- Materialize: inherited JS exactly matches the immutable Git release file
  at Dogfalo/materialize commit 9bc43a1199ad5dfb78d58ba47726ab039218a939;
  npm dist JS member differs. CSS/fonts retain their npm provenance. #34 owns
  security and nested attribution review. No claim that npm JS is identical.
- Ten Roboto files: name-table version 2.136 (2017), Google copyright 2011,
  Apache-2.0 license field. Exact delivery via verified Materialize npm archive.
  Material Icons: version 1.017, Google copyright 2018, upstream Apache-2.0;
  original standalone binary archive unresolved. Both have packaged notices.

### Installed and vulnerability evidence

Wheel, sdist and Docker installation verified all 471 inventoried resource/notice
files. Python dependency license metadata/texts support the declared licenses;
project MIT license also present. Docker matched all five lock versions;
standalone wheel and sdist resolved PyOTP 2.12.1 rather than locked 2.10.0.
This is explicit resolver drift, not a Docker-lock failure. GitDB 4.0.12
METADATA uses the generic legacy label `BSD License`; the actual installed
`.dist-info/LICENSE` contains the three BSD conditions, supporting
BSD-3-Clause. Its additional notice identifies two GPL-licensed test pack
fixtures and states they are not included in the distribution. This is a
statement in the shipped license, not a separately verified wheel-member
exclusion in this audit.

OSV scan on 2026-11-26: 213 distinct package/version queries; 78 had advisory
matches. npm: 5 queried, 2 matched (js-yaml 5 IDs, Materialize 4 IDs).
PyPI: 10 queried, 2 matched (pip 24.0, 12 IDs; setuptools 79.0.1, 3 IDs).
None of the five locked app dependency versions matched in this scan;
this is not a guarantee of no vulnerabilities. Debian:12: 198 source/version
queries from 429 installed binaries, 74 matched, 2949 distinct advisory IDs.
Linux source contributed 2319 IDs through linux-libc-dev headers; this is
not an inventory of a running kernel or confirmed exploitable CVEs. Aliases,
source-to-binary applicability, severity, backports and actual reachability
need triage; CPython outside dpkg and embedded libraries need separate review.

| Follow-up | Owner | Decision |
| --- | --- | --- |
| #33 YAML parser and byte drift | maintainer | OPEN, remediate before public release; includes embedded Ace YAML parser |
| #34 Materialize autocomplete / nested components | maintainer | OPEN, remediate or assess specific paths before public release |
| #35 Python/Debian runtime | maintainer | OPEN, triage findings and reduce unnecessary surface before public release |
| #9 nested attribution and font original archive | maintainer | OPEN; review embedded source notices and remaining provenance, no blanket legal signoff |

Ace v1.9.6 source includes worker libraries such as CSSLint 1.0.5, parserlib
1.1.2, CoffeeScript 2.2.1, luaparse 0.3.1, php.js 0.1.0 and JSON parser;
JSHint/YAML/XML/XQuery workers contain further dependencies whose exact
versions/notice obligations must be resolved. Materialize release build
includes Hammer, Velocity and Waves code. Top-level licenses and package
version scans do not establish exhaustive nested attribution or coverage.
No risk acceptance has been granted by the maintainer. #9 remains open.

## Follow-up CI and independent review — 2026-11-26

Exact source `f17c9bb094a62a5fce8184536154deba16dffcaa`,
[run #339 / 45870516568](https://github.com/undel-gh/hass-configurator/actions/runs/45870516568):
4/4 jobs SUCCESS; 141 Python tests, source Chromium 27 passed/1 skipped,
wheel/sdist/Docker each 6 passed. Two no-cache amd64 builds produced the same
image ID `sha256:6356cca68f1f7da3033298fd8ff6f5dd8f2c9f571973fbb57c00a77bf6ff21ca`.
Downloaded source artifact 15141443731 and E2E/installed artifact 15141853575;
reviewed actual JSON and build provenance. All three exact legacy JS
relationships passed, font name tables matched, source BOM has 12 unique
component refs, and 471 inventoried files matched in each installed variant.
Docker lock matched, wheel/sdist PyOTP 2.12.1 differed from locked 2.10.0.
OSV report explicitly binds source commit f17c9bb094a62a5fce8184536154deba16dffcaa; scan
2026-11-26T17:48:56.233139+00:00, 213 queries / 78 matched, same npm/PyPI/Debian
counts and advisory IDs for npm as initial run. No finding suppression.

Round 1 reviews: reviewer-reported 11/11 tamper scenarios caught, no runtime
finding. Risk register synchronized with all five js-yaml and four Materialize
matches; direct path-guard regressions added, including drive-qualified paths
for portability. Audit tool rejects colon-bearing paths (including Windows
drive qualifiers and alternate data stream syntax); this does not change
HTTP/runtime path handling. New exact-HEAD CI required for the follow-up.
Historical image ID is not expected to equal a new source-epoch build's ID.
Review approval of the audit implementation is not remediation, complete
nested license attribution, or release acceptance. #33–#35 remain open;
no risk acceptance or merge authorization inferred from reviews.

## Embedded component and historical font audit (Round 3 candidate)

The audit now maps 30 embedded records: 28 actual library entries and two
open review records (Browserify shims and themes/snippets). Of the records,
12 are identified, 17 partial and one restricted. This is a bounded inventory
of identified code, not exhaustive attribution or a final legal signoff.
The separate `hass_configurator/third_party/embedded.json` carries pinned
source commit/blob references, exact container-file markers, notice hashes,
version evidence and explicit unresolved dispositions. 23 additional full
license files or marked source excerpts are shipped and hash-checked. The
source CycloneDX BOM expands from 12 to 40 library components, with parent
edges for embedded code. Review records are not fictitious libraries. Unknown
or contradictory versions are not assigned purls; only known ecosystem and
version identities are added to OSV queries. File hashes on child components
are explicitly containing-file hashes, not independent package hashes.

The build-time `source --embedded-upstream` check fetches only immutable GitHub
source references, verifies Git blob identity and literal source markers,
compares whole notices or exact excerpts, and verifies original font lineage.
It uploads `embedded-upstream-evidence.json` with SHA-256 and Git blob
identities; no source archive is executed. Local checks still require no
network. Existing npm archive closure and installed artifact byte checks
remain in force. New exact-HEAD CI required; no claimed execution before it.

### Materialize 0.100.2 — nested licenses

Exact tagged JS/source and Grunt concat recipe at
[9bc43a1](https://github.com/Dogfalo/materialize/tree/9bc43a1199ad5dfb78d58ba47726ab039218a939).
Hammer runtime 2.0.4 differs from declared ^2.0.8; Velocity header 1.2.3
conflicts with embedded runtime 1.2.2. The latter and shim 1.0.1 are partial
records, not version-normalized. Easing 1.4.0 includes both George McGinley
Smith and Robert Penner BSD notices. Waves 0.6.4, Pickadate 3.5.0, ClockPicker
0.0.7 (modified 2015), ScrollSpy 0.1.2, jquery.hammer, raf.js and Underscore
fragments are separately attributed. Historical candidate MIT texts are
retained for unresolved copies; original exact revision and missing full
shim text remain open. #34 owns security/path remediation and further
attribution; top-level MIT alone is not license closure.

### Ace — worker and snippet review

Source [238b88e](https://github.com/ajaxorg/ace/tree/238b88ed1773005fd2b81eccacf6cf4ef5e7334d).
All 11 shipped worker files have explicit review records; shared base worker
review is still open. Identified libraries include CSSLint 1.0.5 / Parser-Lib
1.1.2 (full inline MIT headers), CoffeeScript 2.2.1, luaparse 0.3.1,
Underscore 1.10.2, php.js 0.1.0 (header only) and JSON.org json_parse
(public-domain statement, no invented package version). The JSHint version
2.11.0 comes from [Ace update abf1a195](https://github.com/ajaxorg/ace/commit/abf1a195211d8b5eded5e5f0449a566b80594b6e).
The exact Ace source still contains the historical JSON condition; upstream
[JSHint about](https://jshint.com/about/) and its 2020 relicensing process
state versions before 2.12.0 were partly under that non-free license. Record
MIT AND JSON, preserve the source header and top-level MIT license. **OPEN /
public-release HOLD**: establish applicability of subsequent relicensing to
exact shipped code or replace the worker/Ace with a reviewed relicensed
build; no implied policy waiver. Merely disabling a worker does not remove
its distributed bytes. Maintainer decision required. No runtime upgrade in
this audit PR.

The YAML worker is not the standalone 4.1.0 file. Adapted yaml-lint resembles
upstream 1.2.4 (callback rather than Promise); loader comparisons with
js-yaml 3.11.0, 3.12.0, 3.12.2, 3.13.0 and 3.13.1 did not establish an exact
version. API family 3.x, exact release unresolved, #33. Historical js-yaml
3.12.2 license blob equals the existing 4.1.0 MIT notice, not proof of
version. Lodash.merge/clone/slice, HTML5 SAX parser, XMLDOM, XQLint, generated
REx lexer attribution, Browserify dependencies and theme/snippet licenses
remain open at finer granularity; do not assign current npm versions to
historical modified code. jQuery's separately bundled Sizzle 2.3.6 is also
recorded with its upstream MIT license. No claims about unused upstream
build/test dependencies being shipped.

### Font provenance

[HASS Configurator commit 6e361100](https://github.com/undel-gh/hass-configurator/commit/6e3611006c84cf103318a9c4bb5a661e5da73411)
(2019-12-29) introduced the same Material Icons WOFF2 Git blob
`d9c6038f7c3cb67eda285b7034b0144bf1460519`. Its parent used Google's online
`fonts.googleapis.com/icon?family=Material+Icons` stylesheet. The historical
[official Google repository WOFF2](https://github.com/google/material-design-icons/blob/f880f4bd322f55d1fe64aa238e233f719339637b/iconfont/MaterialIcons-Regular.woff2)
(blob `9fa211252080046a23b2449dbdced6abc2b0bb34`) does not match; earlier
repository WOFF2 blobs also differ. Repository lineage and font name-table
metadata are established, but original CDN URL/archive was not recorded.
No source replacement or guessed CDN version. Roboto exact delivery remains
verified through the pinned Materialize archive, original standalone font
release archive still unresolved. Source provenance gap remains explicit;
no font-license signoff beyond existing notices/name-table evidence.

### Remaining decisions

- Resolve the JSHint historical JSON restriction before public release;
  retain the actual condition in the meantime. No legal acceptance inferred.
- Finish exact attribution of partial nested components, including original
  source notices and version identities for #33/#34, and theme/snippet review.
- Review new version-bound OSV results, coordinate #33–#35, and decide
  whether original font provenance requires replacement. No blanket risk waiver.
- Exact-HEAD CI, actual artifact review, independent review and merge decision
  remain pending. PR #32 / #9 not complete; overall P1 still unverified.
