# Ace / YAML migration — Issue #33

Status: **implementation preparation; no runtime bytes promoted**.
Stacked onto PR #32 at b5924860ad8e27a2c47cecb71cac7905627a2819.
Do not merge this checkpoint or close #33/#9 before the migration and gates.

## First implementation checkpoint

- Ace 1.45.2: independently pin the exact npm archive SHA-256, SRI and LICENSE
  SHA-256 from inspected #343 artifact 15150320218, in addition to the existing
  immutable 495-file Git family checks. Reject changed bytes before execution.
- Standalone js-yaml 4.3.2: candidate on the maintained v4-legacy line, avoiding
  an unrelated major API migration. The cited merge/omap advisories are fixed
  at or before this version; fresh OSV query gates the candidate. Official npm
  browser member is used unmodified; LICENSE matched to immutable source
  79ca68d90f333fbe6d9e42827527e62636200191. Archive/member SHA-256 and SRI
  recorded for independent pin review. No claim of release acceptance.
- Prepare only a new disposable overlay outside checkout. Replace both
  editor candidates, regenerate vendor manifest and run actual Configurator
  under existing CSP and routing; retain normal current-runtime CI unchanged.
  Existing source inventory in overlay deliberately describes old runtime
  and is not an accepted SBOM for candidate. Never package or publish overlay.
- Bounded merge-budget, duplicate omap, NBSP, syntax and multi-document
  compatibility probes; integrated source browser tests cover lazy modules,
  workers, CSP, file operations and simulated Ingress.
- Existing js-yaml UI still uses main-thread parsing and the historical
  custom-tag substitution. Rehearsal does not fix those architectural
  limitations. #24 custom tag support remains separate. Decide whether to
  retain a fixed bounded parser or unify validation without losing diagnostics
  when the Ace worker is disabled.

## Remaining acceptance

1. Review exact rehearsal artifacts and CI for both workflows; pin measured
   js-yaml archive and license before committed promotion.
2. Commit exact Ace family and js-yaml member, update lock/verifier, manifest,
   runtime inventory, embedded component attribution and notices, packaging
   checks, source/installed SBOM and risk register. Do not relabel old
   JSHint records as new or infer exact worker versions from ranges.
3. Determine exact embedded worker dependency identities and licensing; retain
   explicit unresolved gaps and separate release gates. Test #24 YAML tags,
   multi-document, anchors, merge/omap, NBSP and worker-disable semantics.
4. Exact-HEAD full installed wheel/sdist/Docker E2E and fresh OSV; two independent
   reviews, real HA OS fixture 0.0.5 warm upgrade and rollback to 0.0.4.
5. Merge only into audit branch after approval; #9 remains open pending
   final audit and #34–#35 dispositions. No public-release clearance.
