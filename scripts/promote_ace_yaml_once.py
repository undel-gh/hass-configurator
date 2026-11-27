#!/usr/bin/env python3
"""One-time #33 promotion from the independently reviewed rehearsal.

Run only on the old-runtime migration branch in a disposable clean checkout.
Never downloads or executes candidate code; consume the verified overlay and
report made by prepare_ace_migration.py. New nested attribution remains partial.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess

from prepare_ace_migration import (
    ROOT, ACE_SHA256, ACE_SRI, ACE_LICENSE_SHA256,
    YAML_SHA256, YAML_SRI, YAML_MEMBER_SHA256, YAML_LICENSE_SHA256,
    YAML_URL, YAML_SOURCE, YAML_LICENSE_BLOB, sha, verify_overlay,
)
from audit_supply_chain import git_blob_sha1, read_file

PKG = ROOT / "hass_configurator"
BUILD = "c9ea63c0a0a436fbb477c918d6736644f77cab9f"
LINTER = "e0d223c5a880cb2f258c96ccd22feaaffb29e5a5"
HISTORY = "b5924860ad8e27a2c47cecb71cac7905627a2819"
LINTER_LICENSE = "319b7eddf9ad9ee57746f4bb486597c87a35929c"
LINTER_NOTICE = "third_party/licenses/embedded/ace-legacy-linters.txt"


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text("utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def edit(name, replacements):
    path = ROOT / name
    text = path.read_text("utf-8")
    for old, new in replacements:
        require(old in text, "Expected old source text missing: " + name + " / " + old)
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def evidence(name, marker, lock):
    return {"url": "https://github.com/ajaxorg/ace-builds/blob/" + BUILD + "/src-min-noconflict/" + name,
            "git_blob": lock["files_git_blob"][name], "marker": marker}


def linter_evidence(path, blob, marker):
    return {"url": "https://github.com/mkslanc/ace-linters/blob/" + LINTER +
            "/packages/ace-legacy-linters/" + path, "git_blob": blob, "marker": marker}


def record(cid, name, kind, locations, sources, note, notices=None, license=None):
    return {"id": cid, "parent": "ace", "kind": kind, "name": name, "version": None,
            "ecosystem": None, "status": "partial", "license": license,
            "locations": locations, "evidence": sources, "note": note, "notices": notices or []}


def loc(name, marker):
    return {"file": "vendor/ace/" + name, "marker": marker}


def reconcile_embedded(old, old_manifest, manifest, lock, family, license_bytes):
    # Preserve all historical attribution (including notices) until a reviewer
    # has decided exact identities. Only active evidence gets a package entry.
    old = copy.deepcopy(old)
    out = copy.deepcopy(old)
    historical = ROOT / "docs/history/ace-1.9.6-embedded.json"
    require(not historical.exists(), "Historical snapshot already exists")
    historical.parent.mkdir(parents=True, exist_ok=True)
    historical.write_bytes((PKG / "third_party/embedded.json").read_bytes())
    rows = []
    for item in old["components"]:
        if item["parent"] != "ace":
            rows.append(item)
            continue
        if item["id"] in {"ace-jshint", "ace-yaml-parser"}:
            # Retain the historical record in docs and its notices below.
            continue
        locations = item["locations"]
        if not all(location["file"][len("vendor/ace/"):] in family and
                   location["marker"].encode("utf-8") in
                   family[location["file"][len("vendor/ace/"):]] for location in locations):
            continue
        if all(old_manifest["resources"].get(location["file"]) ==
               manifest["resources"].get(location["file"]) for location in locations):
            rows.append(item)
            continue
        # An old marker in changed generated code is only a partial attribution.
        # Preserve explicit known version markers for CoffeeScript/luaparse;
        # do not infer npm identities from a historical generic module name.
        item["status"] = "partial"
        if item["id"] not in {"ace-coffee", "ace-luaparse"}:
            item["version"] = None
            item["ecosystem"] = None
        item["note"] += (" Historical source reference; marker survives in the new "
                         "build, but new embedded byte/version/license closure is not complete.")
        item["evidence"].extend(evidence(location["file"][len("vendor/ace/"):],
                                         location["marker"], lock) for location in locations)
        rows.append(item)
    # Source architecture evidence, not proof of a particular dependency lock
    # in the minified build. Keep versions/PURLs absent until attribution.
    js = "worker-javascript.js"
    yaml = "worker-yaml.js"
    js_source = linter_evidence("src/workers/javascript-worker.ts",
                                "e7c858877314ea7caac5d7845c9980043a60a6b5", "no-undef")
    yaml_source = linter_evidence("src/workers/yaml-worker.ts",
                                  "76ca4bf50c9093640550f2b10229353a631f76ff", "parseAllDocuments")
    require(b"no-undef" in family[js] and b"Unresolved tag" in family[yaml],
            "Expected reviewed worker markers missing")
    require(b"@babel/parser" in family[js], "Expected Babel marker missing")
    rows.append(record("ace-legacy-linters", "ace-legacy-linters (source candidate)", "library",
                       [loc(js, "no-undef"), loc(yaml, "Unresolved tag")],
                       [evidence(js, "no-undef", lock), evidence(yaml, "Unresolved tag", lock),
                        js_source, yaml_source,
                        linter_evidence("package.json", "dbe8ced0479259147b3ea8c5548da910ba953d64",
                                        '"version": "1.0.2"')],
                       "Source package 1.0.2 declares new workers; exact bundled version and nested closure remain open.",
                       [LINTER_NOTICE], "MIT"))
    rows.append(record("ace-babel-parser", "@babel/parser", "library", [loc(js, "@babel/parser")],
                       [evidence(js, "@babel/parser", lock),
                        linter_evidence("src/workers/javascript-worker.ts",
                                        "e7c858877314ea7caac5d7845c9980043a60a6b5", "@babel/parser")],
                       "Source import and shipped marker support partial identity; exact bundled version/license evidence pending."))
    rows.append(record("ace-yaml-parser", "yaml (Ace worker)", "library", [loc(yaml, "Unresolved tag")],
                       [evidence(yaml, "Unresolved tag", lock), yaml_source,
                        linter_evidence("src/workers/yaml-worker.ts",
                                        "76ca4bf50c9093640550f2b10229353a631f76ff", 'from "yaml"')],
                       "Source uses yaml.parseAllDocuments; not the standalone js-yaml parser. Exact bundled version/license closure pending."))
    # Keep the old notice texts as explicit historical references, not as
    # asserted active component licenses, until nested attribution is complete.
    used = {n for row in rows for n in row["notices"]}
    historical_notices = sorted(set(old["notices"]) - used)
    if historical_notices:
        marker = "ace"
        require(marker.encode() in family["ace.js"], "Ace core marker missing")
        rows.append(record("ace-historical-notice-review", "Historical Ace 1.9.6 notice references", "review",
                           [loc("ace.js", marker)], [evidence("ace.js", marker, lock)],
                           "Conservatively retained historical notices pending new bundle attribution. "
                           "These do not assert the old libraries or historical JSON license are present in the new runtime.",
                           historical_notices))
    require(git_blob_sha1(license_bytes) == LINTER_LICENSE, "New linter license source mismatch")
    (PKG / LINTER_NOTICE).write_bytes(license_bytes)
    out["notices"][LINTER_NOTICE] = {
        "sha256": sha(license_bytes),
        "source": "https://github.com/mkslanc/ace-linters/blob/" + LINTER +
                  "/packages/ace-legacy-linters/LICENSE",
        "source_blob": LINTER_LICENSE, "kind": "whole-file",
    }
    out["components"] = rows
    out["worker_review"] = {
        "vendor/ace/" + name: {"status": "open-review",
                               "note": "Ace 1.45.2 exact build verified; full current worker dependencies, versions and notices not cleared."}
        for name in sorted(family) if name.startswith("worker-") and name.endswith(".js")
    }
    require(len(out["worker_review"]) == 11, "Unexpected worker count")
    # Historical literal source relationships concern the 1.9.6 build.
    out["source_relationships"] = []
    out["limitations"] = [
        "Partial current inventory; missing nested identities, versions and notices are release blockers, not accepted risk.",
        "Historical Ace 1.9.6 rows and literal source relationships: docs/history/ace-1.9.6-embedded.json and checkpoint " + HISTORY,
        "Historical retained notices are references, not proof of active libraries or current license closure.",
        "New worker imports and build markers do not establish exact dependency versions. Candidate OSV queries remain separately scoped.",
        "Non-Ace embedded findings and font provenance remain unchanged.",
    ]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overlay", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--linter-license", type=Path, required=True)
    args = ap.parse_args()
    overlay = args.overlay / "hass_configurator"
    report = load(args.report)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(report["source_checkout"] == head and report["status"] == "verified-rehearsal-input",
            "Rehearsal report must bind to exact checkout")
    require(report["overlay_verification"] == {"vendor_resources_verified": 515, "js_yaml_files_verified": 2},
            "Incomplete overlay verification")
    require(len(report["osv"]) == 2 and not any(r["advisories"] for r in report["osv"]),
            "Candidate OSV matches or incomplete queries")
    lock = load(ROOT / "docs/ace-candidate-1.45.2.json")
    ace, yaml = report["ace"], report["js_yaml"]
    require((ace["archive_sha256"], ace["npm_integrity"], ace["license_sha256"]) ==
            (ACE_SHA256, ACE_SRI, ACE_LICENSE_SHA256), "Ace report pin mismatch")
    require((yaml["archive_sha256"], yaml["npm_integrity"], yaml["member_sha256"], yaml["license_sha256"]) ==
            (YAML_SHA256, YAML_SRI, YAML_MEMBER_SHA256, YAML_LICENSE_SHA256), "js-yaml report pin mismatch")
    manifest = load(overlay / "vendor/manifest.json")
    verify_overlay(overlay, manifest, yaml)
    old_manifest = load(PKG / "vendor/manifest.json")
    inv = load(PKG / "third_party/inventory.json")
    require(old_manifest["provenance"]["ace"]["version"] == "1.9.6" and
            next(c for c in inv["components"] if c["id"] == "js-yaml")["version"] == "4.1.0",
            "Promotion requires old runtime")
    require(inv["vendor_manifest_sha256"] == sha((PKG / "vendor/manifest.json").read_bytes()),
            "Old manifest drift")
    require({k: v for k, v in old_manifest["resources"].items() if not k.startswith("vendor/ace/") and k != "vendor/licenses/ace.txt"} ==
            {k: v for k, v in manifest["resources"].items() if not k.startswith("vendor/ace/") and k != "vendor/licenses/ace.txt"},
            "Unexpected non-Ace vendor change")
    require({k: v for k, v in old_manifest["provenance"].items() if k != "ace"} ==
            {k: v for k, v in manifest["provenance"].items() if k != "ace"}, "Non-Ace provenance drift")
    family = {name: read_file(overlay, "vendor/ace/" + name) for name in lock["files_git_blob"]}
    require(len(family) == 495 and {n: git_blob_sha1(raw) for n, raw in family.items()} ==
            lock["files_git_blob"], "New build family differs from pinned Git tree")
    require({n: sha(raw) for n, raw in family.items()} == ace["files_sha256"],
            "New family differs from reviewed report")
    require(not ace["missing_ui_files"] and ace["required_ui_files"] == 174, "Missing UI modules")
    require(not any(b"ace/mode/javascript/jshint" in raw or b"Good, not Evil" in raw
                    for raw in family.values()), "Historical JSHint markers detected; investigate")
    # Existing family is a subset of the new one; no file silently disappears.
    old_names = {n[len("vendor/ace/"):] for n in old_manifest["resources"] if n.startswith("vendor/ace/")}
    require(len(old_names) == 440 and old_names <= set(family) and len(family) - len(old_names) == 55,
            "Unexpected old/new family difference")
    for name, raw in family.items():
        path = PKG / "vendor/ace" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for name in ("vendor/licenses/ace.txt", "js-yaml.min.js", "third_party/licenses/js-yaml.txt", "vendor/manifest.json"):
        (PKG / name).write_bytes(read_file(overlay, name))
    new_lock = {
        "name": "ace-builds", "version": "1.45.2", "family": "src-min-noconflict",
        "tarball": lock["tarball"], "sha256": ACE_SHA256, "npm_integrity": ACE_SRI,
        "license_sha256": ACE_LICENSE_SHA256, "license_git_blob": lock["license_git_blob"],
        "source_commit": lock["source_commit"], "build_commit": lock["build_commit"],
        "family_files": 495, "required_files_checked": 174, "missing_required_files": [],
        "worker_files": sorted(n for n in family if n.startswith("worker-") and n.endswith(".js")),
        "files_sha256": ace["files_sha256"],
    }
    write(ROOT / "docs/ace-builds-1.45.2-lock.json", new_lock)
    inv["vendor_manifest_sha256"] = sha((PKG / "vendor/manifest.json").read_bytes())
    inv["legacy_assets"]["js-yaml.min.js"] = YAML_MEMBER_SHA256
    inv["license_notices"]["third_party/licenses/js-yaml.txt"] = {
        "sha256": YAML_LICENSE_SHA256,
        "source": "https://github.com/nodeca/js-yaml/blob/" + YAML_SOURCE + "/LICENSE",
    }
    inv["legacy_archive_locks"]["js-yaml.min.js"] = {
        "archive": "js-yaml-4.3.2.tgz", "tarball": YAML_URL, "sha256": YAML_SHA256,
        "npm_integrity": YAML_SRI, "member": "package/dist/js-yaml.min.js",
        "member_sha256": YAML_MEMBER_SHA256, "relation": "exact",
    }
    for c in inv["components"]:
        if c["id"] == "ace":
            c["version"] = "1.45.2"
            c["provenance"] = "Exact reviewed npm/Git build family; current nested worker attribution remains partial (#33/#9)."
        if c["id"] == "js-yaml":
            c["version"] = "4.3.2"
            c["provenance"] = "Exact official npm browser member; historical byte drift removed. Main-thread lint and custom tag compatibility remain under review."
    write(PKG / "third_party/inventory.json", inv)
    out = reconcile_embedded(load(PKG / "third_party/embedded.json"), old_manifest,
                             manifest, lock, family, args.linter_license.read_bytes())
    write(PKG / "third_party/embedded.json", out)
    runtime = load(ROOT / "docs/runtime-dependencies.json")
    runtime["ace"].update({
        "proposed_version": "1.45.2", "candidate_archive_url": lock["tarball"],
        "archive_integrity": ACE_SRI, "archive_sha256": ACE_SHA256,
        "lock_file": "docs/ace-builds-1.45.2-lock.json",
        "dynamic_modules_status": "All 495 files of pinned src-min-noconflict family are local; new runtime exact-HEAD acceptance pending.",
        "selection_status": "Promoted candidate on #33 draft branch; all 174 UI-required filenames present; no public-release approval.",
    })
    write(ROOT / "docs/runtime-dependencies.json", runtime)
    # Current runtime verifiers must use the new lock, not the historical lock.
    edit("scripts/vendor_offline_assets.py", [("ace-builds-1.9.6", "ace-builds-1.45.2"), ('"ace-builds", "1.9.6"', '"ace-builds", "1.45.2"'),
        ('            license_file = package_license(archive, alias, resources)',
         '            license_file = package_license(archive, alias, resources)\n'
         '            if alias == "ace" and digest(resources["licenses/ace.txt"]) != ACE_LOCK["license_sha256"]:\n'
         '                raise RuntimeError("Ace license differs from pinned artifact")')])
    edit("scripts/verify_ace_archive.py", [("1.9.6", "1.45.2"),
        ('        members = {\n            n.name[len(BUILD):]: n for n in archive.getmembers()\n            if n.isfile() and n.name.startswith(BUILD)\n        }',
         '        members = {}\n'
         '        for n in archive.getmembers():\n'
         '            if not n.name.startswith(BUILD) or n.isdir():\n'
         '                continue\n'
         '            name = n.name[len(BUILD):]\n'
         '            if not n.isfile() or name in members:\n'
         '                raise ValueError("Duplicate or unsafe Ace member: " + n.name)\n'
         '            members[name] = n\n'
         '        licenses = [n for n in archive.getmembers() if n.name == "package/LICENSE"]\n'
         '        if len(licenses) != 1 or not licenses[0].isfile():\n'
         '            raise ValueError("Missing or unsafe Ace LICENSE")\n'
         '        license_sha256 = hashlib.sha256(archive.extractfile(licenses[0]).read()).hexdigest()'),
        ('"sha256": digest, "family":', '"sha256": digest, "license_sha256": license_sha256, "family":'),
        ('("sha256", "family", "worker_files", "files_sha256")',
         '("name", "version", "tarball", "sha256", "license_sha256", "family", "worker_files", "files_sha256")')])
    edit("tests/test_vendored_assets.py", [("1.9.6", "1.45.2"), ("), 440)", "), 495)"),
        ('self.assertGreaterEqual(len(resources), 455)', 'self.assertEqual(len(resources), 515)')])
    edit("tests/test_p0_closeout.py", [("1.9.6", "1.45.2"), (", 440)", ", 495)")])
    edit("tests/test_haos_fixture.py", [('self.assertGreaterEqual(result["vendor_resource_count"], 460)',
                                        'self.assertEqual(result["vendor_resource_count"], 515)')])
    p = ROOT / "tests/test_supply_chain.py"
    t = p.read_text("utf-8")
    start = t.index('        self.assertEqual(len(vendor["resources"]), 460)')
    end = t.index('        refs = [c["bom-ref"]', start)
    t = t[:start] + '''        self.assertEqual(len(vendor["resources"]), 515)
        bom = sbom(inv, vendor)
        self.assertEqual(bom["bomFormat"], "CycloneDX")
        self.assertEqual(next(c for c in bom["components"] if c["bom-ref"] == "asset:ace")["version"], "1.45.2")
        self.assertEqual(next(c for c in bom["components"] if c["bom-ref"] == "asset:js-yaml")["version"], "4.3.2")
        embedded = [c for c in bom["components"] if c["bom-ref"].startswith("embedded:")]
        self.assertNotIn("embedded:ace-jshint", {c["bom-ref"] for c in embedded})
        self.assertIn("embedded:ace-legacy-linters", next(d for d in bom["dependencies"]
                      if d["ref"] == "asset:ace")["dependsOn"])
        yaml = next(c for c in embedded if c["bom-ref"] == "embedded:ace-yaml-parser")
        self.assertEqual(yaml["name"], "yaml (Ace worker)")
        self.assertNotIn("version", yaml)
        self.assertNotIn("purl", yaml)
        self.assertEqual(inv["legacy_archive_locks"]["js-yaml.min.js"]["relation"], "exact")
        self.assertEqual(len(inv["embedded"]["worker_review"]), 11)
        historical = json.loads((ROOT / "docs/history/ace-1.9.6-embedded.json").read_text("utf-8"))
        self.assertIn("ace-jshint", {c["id"] for c in historical["components"]})
''' + t[end:]
    p.write_text(t, encoding="utf-8")
    # ROOT is not necessarily imported by this test; use PACKAGE.parent.
    edit("tests/test_supply_chain.py", [
        ('(ROOT / "docs/history/ace-1.9.6-embedded.json")', '(PACKAGE.parent / "docs/history/ace-1.9.6-embedded.json")'),
        ('if c["id"] == "ace-jshint")["notices"] = []', 'if c["id"] == "mat-hammer")["notices"] = []'),
        ('doc["source_relationships"][0]["relation"] = "loosely-normalized"',
         'doc["source_relationships"].append({"relation": "loosely-normalized"})'),
        ("third_party/licenses/embedded/jshint-json.txt", "third_party/licenses/embedded/ace-legacy-linters.txt"),
        ('"version": "4.1.0"}, queries)', '"version": "4.3.2"}, queries)'),
        ('self.assertIn({"package": {"ecosystem": "npm", "name": "jshint"},\n                       "version": "2.11.0"}, queries)',
         'self.assertIn({"package": {"ecosystem": "npm", "name": "ace-builds"},\n'
         '                       "version": "1.45.2"}, queries)\n'
         '        self.assertNotIn({"package": {"ecosystem": "npm", "name": "jshint"},\n'
         '                          "version": "2.11.0"}, queries)'),
    ])
    # Keep the rehearsal useful on promoted HEAD without pretending its overlay
    # necessarily carries the old inventory after the promotion.
    edit("scripts/prepare_ace_migration.py", [
        ('"js-yaml hashes pinned from prior rehearsal; promotion review pending."',
         '"js-yaml pins independently reviewed; actual runtime acceptance separate."'),
        ('    # The overlay intentionally retains the old audit inventory, which MUST NOT\n'
         '    # pass the release audit. This is an integration rehearsal, not a package.',
         '    # The overlay retains the checkout audit inventory. Historical old-runtime\n'
         '    # checkouts cannot pass a candidate release audit. Never package this overlay.')])
    notice = PKG / "third_party/NOTICE.md"
    text = notice.read_text("utf-8")
    text = text.replace("original 460 resources", "515 resources on the #33 migration branch")
    text = text.replace("Ace 1.9.6:", "Ace 1.45.2:").replace("js-yaml 4.1.0:", "js-yaml 4.3.2:")
    start = text.index("Ace workers contain JSHint")
    end = text.index("The inherited Google Material Icons", start)
    text = text[:start] + """Ace 1.45.2 uses the independently reviewed 495-file upstream build family.
Current embedded attribution is partial. Source evidence for ace-legacy-linters
(candidate 1.0.2, MIT notice retained), @babel/parser and yaml is recorded;
exact bundled versions, remaining worker dependencies, theme/snippet licenses
and full attribution remain OPEN. The old JSHint module and historical JSON
license literal were not found in the verified new family; this marker check
is not exhaustive license clearance. Historical Ace 1.9.6 records and
notices are retained as references, not as assertions of active components.
The original restricted JSHint 2.11.0 license was not retroactively changed.
jQuery 3.6.0 still embeds Sizzle 2.3.6; its MIT text is included.
No public redistribution approval is implied.

""" + text[end:]
    text = text.replace("Further historical reference notices: HTML5 parser upstream", "Further historical Ace 1.9.6 reference notices (not current worker identities): HTML5 parser upstream")
    notice.write_text(text, encoding="utf-8")
    for name, prefix in (
        ("docs/P1_SUPPLY_CHAIN.md", "## #33 runtime promotion checkpoint\n\n"
         "The original audit below describes Ace 1.9.6 and js-yaml 4.1.0 on checkpoint "
         + HISTORY + ". On the #33 draft branch, exact reviewed Ace 1.45.2 and js-yaml 4.3.2 "
         "bytes are promoted; the current lock, manifest and top-level inventory supersede the old version assertions. "
         "Historical risks remain documented. New embedded inventory is partial, not a license clearance; "
         "installed wheel/sdist/Docker, exact-HEAD OSV and independent review are pending. "
         "#9, #33–#35 remain release gates. No automatic risk acceptance.\n\n"),
        ("docs/ACE_UPGRADE_RESEARCH.md", "## Historical research scope\n\n"
         "This research describes the old-runtime checkpoint and candidate selection. "
         "The #33 migration branch now contains the verified candidate bytes; see P1_ACE_YAML_MIGRATION.md. "
         "Historical results below do not verify new installed artifacts.\n\n"),
        ("docs/P1_ACE_YAML_MIGRATION.md", "## Runtime promotion checkpoint\n\n"
         "The #33 branch now promotes exact Ace 1.45.2 and js-yaml 4.3.2 bytes from reviewed pins. "
         "Current lock/manifest/inventory updated. Non-Ace resources unchanged. "
         "Prior Ace inventory preserved at docs/history/ace-1.9.6-embedded.json; old notice references retained conservatively. "
         "New source/marker evidence is partial: no inferred exact nested versions or final licensing clearance. "
         "Historical JSHint module/license literal absence is only marker evidence. "
         "Main-thread validation, HA/ESPHome tag semantics, current nested attribution, full CI and real HAOS rollback remain open. "
         "No merge/public release acceptance.\n\n"),
    ):
        p = ROOT / name
        text = p.read_text("utf-8")
        split = text.index("\n") + 1
        p.write_text(text[:split] + "\n" + prefix + text[split:].lstrip("\n"), encoding="utf-8")
    print("Promoted exact vendor family, locks, manifest and partial current inventory; nested review remains open.")


if __name__ == "__main__":
    main()
