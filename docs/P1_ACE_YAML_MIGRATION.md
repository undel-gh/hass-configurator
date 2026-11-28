# Ace / YAML migration — Issue #33

## Runtime promotion checkpoint

The #33 branch now promotes exact Ace 1.45.2 and js-yaml 4.3.2 bytes from reviewed pins. Current lock/manifest/inventory updated. Non-Ace resources unchanged. Prior Ace inventory preserved at docs/history/ace-1.9.6-embedded.json; old notice references retained conservatively. New source/marker evidence is partial: no inferred exact nested versions or final licensing clearance. Historical JSHint module/license literal absence is only marker evidence. Main-thread validation, HA/ESPHome tag semantics, current nested attribution, full CI and real HAOS rollback remain open. No merge/public release acceptance.

Status: **runtime bytes promoted on the draft #33 branch; full acceptance pending**.
The original preparation checkpoint below is historical.
Stacked onto PR #32 at b5924860ad8e27a2c47cecb71cac7905627a2819.
Transfer commit: caf070a7dca38e40b926e283a69f61f6748f61d1 (parent e23d7dae).
One-time transfer workflow run 45977039640; artifact 15187527210, verified ZIP SHA-256
`df7c663c8caa9c702b8fed61f166c19897f8e995045781e48b3f97008ab524c7`.
Patch SHA-256 `2ef0e00499ed0c2e861537494d6c446fb32737f58783978f581d6af4d5d7d6ac`.
Preparation job verified new source, exact 495-file archive, all 174 UI files,
source BOM, bounded Node probes and 158 Python tests. Author checked actual
patch, source BOM and input report, and all 495 remote Git blob identities;
js-yaml patch bytes hash to the reviewed member and committed Git blob
ed652e67e0803fb8baf2f74cfb7b06e70d11fcdc. This is pre-final CI evidence.
Temporary workflow and generator are removed after successful branch-only
transfer; both are retained in immutable parent e23d7daedb57bdc8ae4bba97f7834e24cf592af8.
The temporary writer used GitHub's built-in contents-write token only in its
separate patch-apply job, no PAT/secrets, exact branch/parent guard and normal
fast-forward push. No master/audit/checkpoint changes.
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
  recorded in first rehearsal and now pinned (run 45887697858, artifact
  15149503830). Independent promotion review remains pending. No release
  acceptance.
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

## Round 1 correction

- Rehearsal runs on every pull_request (no paths filter). The original
  filter missed transitive inputs; baseline green cannot replace candidate CI.
- Pin exact js-yaml archive/SRI, member and license hashes from reviewed
  rehearsal report. Verify overlay vendor closure, manifest and js-yaml bytes
  before browser tests. Add fail-closed tests for family/missing UI files,
  OSV match, pinned archive/member/license and overlay tampering.
- Historical exact HEAD df98b765b3ca4ffea955c171ef92be17d5e25d0c:
  baseline #344 (45887697769) 4/4 SUCCESS; rehearsal #1 (45887697858)
  SUCCESS, actual Playwright report 11 passed, no flaky/skipped/failures.
  All three evidence archives inspected; candidate OSV zero matches for
  ace-builds 1.45.2 and js-yaml 4.3.2. New HEAD needs fresh CI and evidence.
- Additional maintainer checkpoint: pre-release 0.7.1 tag points to master
  196907aa1e37d75adf0bfde7df45c43bcd3d01c0. Distinct from audit checkpoint
  0.0.4; neither is a public-release security signoff.

## Remaining acceptance

1. Historical preparation gates completed on b63eac42; independent pin review
   confirmed by supplied reviews. Promoted source verified in transfer job.
2. Exact Ace family and js-yaml member committed; current lock/verifier,
   manifest, top-level inventory and partial current attribution updated.
   Complete nested attribution, license evidence, risk register and full
   exact-HEAD installed-artifact checks before acceptance.
3. Determine exact embedded worker dependency identities and licensing; retain
   explicit unresolved gaps and separate release gates. Test #24 YAML tags,
   multi-document, anchors, merge/omap, NBSP and worker-disable semantics.
4. Exact-HEAD full installed wheel/sdist/Docker E2E and fresh OSV; two independent
   reviews, real HA OS fixture 0.0.5 warm upgrade and rollback to 0.0.4.
5. Merge only into audit branch after approval; #9 remains open pending
   final audit and #34–#35 dispositions. No public-release clearance.
