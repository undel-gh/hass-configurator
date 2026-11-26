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
shipped Roboto WOFF/WOFF2 and the inherited Material Icons WOFF2. An
original release/version is not invented for fonts with unresolved
provenance. A license text alone is not proof of the binary's origin;
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
| js-yaml 4.1.0 | [GHSA-mh29-5h37-fv8m](https://github.com/advisories/GHSA-mh29-5h37-fv8m), [GHSA-h67p-54hq-rp68](https://github.com/advisories/GHSA-h67p-54hq-rp68), [GHSA-52cp-r559-cp3m](https://github.com/advisories/GHSA-52cp-r559-cp3m), [GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj): affected upstream versions. The editor's check_lint invokes jsyaml.load on editable YAML in the main browser thread; file content can be untrusted. Prototype effects and CPU exhaustion need assessment, update to a reviewed fixed compatible build or remove/replace path. Separate remediation, **OPEN / release gate**, no waiver. |
| Ace 1.9.6 | 2022 build, embedded workers/parsers/third-party snippets may have additional licensing/vulnerabilities not covered by package-level scan. Inspect upstream source and worker contents; specifically identify YAML parser version and advisories. **OPEN**. |
| Materialize 0.100.2 | [CVE-2022-25349](https://www.cve.org/CVERecord?id=CVE-2022-25349), [GHSA-7jvx-f994-rfw2](https://github.com/advisories/GHSA-7jvx-f994-rfw2): autocomplete XSS. Editor initializes autocomplete using HA data. Strict script CSP and safe sinks reduce exposure, not proof of non-applicability. Review data paths and replace/patch vulnerable component; coordinate #31. **OPEN / release gate**. |
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
archive comparison; a mismatch is a provenance gap, not a silent
normalization. The audit never overwrites runtime files.

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
