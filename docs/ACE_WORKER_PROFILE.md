# #37 — Curated Ace worker profile

Status: **phase 1 policy implemented; physical pruning pending**.

The sole machine-readable target profile is the JSON literal delimited by
HC_WORKER_PROFILE_BEGIN / END in the first-party ace-bootstrap.js. The same
data controls worker start and creation and is read by scripts/ace_worker_profile.py.
Full upstream Ace 1.45.2 lock remains unchanged. The proposed subset keeps
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

Phase 1 deliberately keeps the full 495-file package and active inventory
until the policy is verified on actual browser paths. The target profile
derives 490 files. Do not claim component absence or Lodash remediation yet.
Next phase must prune exact five files, enforce profile in regeneration and
installed closure, adapt attribution/rehearsal, re-evaluate retained assets
and notices, and run installed/direct/Ingress/warm-cache/HA OS gates.
