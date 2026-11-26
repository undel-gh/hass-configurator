#!/usr/bin/env python3
"""Read-only research candidate: compare exact npm family to immutable Git build.

Only extract already verified regular files to a new disposable directory.
This is not the runtime vendor command, and no candidate is auto-promoted.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

try:
    from .audit_supply_chain import git_blob_sha1, query_osv, write
except ImportError:
    from audit_supply_chain import git_blob_sha1, query_osv, write

ROOT = Path(__file__).resolve().parents[1]


def inspect_candidate(tarball, registry, lock, offered, old_files):
    raw = tarball.read_bytes()
    sri = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode("ascii")
    if registry.get("dist.integrity") != sri or registry.get("dist.tarball") != lock["tarball"]:
        raise ValueError("Candidate registry integrity/source mismatch")
    prefix = "package/" + lock["family"] + "/"
    family = {}
    with tarfile.open(tarball, "r:gz") as archive:
        names = set()
        package_meta = None
        license_bytes = None
        for m in archive.getmembers():
            if m.name in {"package/package.json", "package/LICENSE"} or m.name.startswith(prefix):
                if m.isdir():
                    continue
                if m.name in names or not m.isfile():
                    raise ValueError("Duplicate or unsafe candidate member: " + m.name)
                names.add(m.name)
                data = archive.extractfile(m).read()
                if m.name == "package/package.json":
                    package_meta = json.loads(data)
                elif m.name == "package/LICENSE":
                    license_bytes = data
                else:
                    name = m.name[len(prefix):]
                    rel = PurePosixPath(name)
                    if (not rel.parts or rel.is_absolute() or ".." in rel.parts or
                            rel.as_posix() != name or "\\" in name or ":" in name):
                        raise ValueError("Invalid candidate family path")
                    family[name] = data
    if not package_meta or (package_meta.get("name"), package_meta.get("version")) != (
            lock["name"], lock["version"]):
        raise ValueError("Candidate package identity mismatch")
    if license_bytes is None or git_blob_sha1(license_bytes) != lock["license_git_blob"]:
        raise ValueError("Candidate LICENSE differs from pinned Git blob")
    actual = {name: git_blob_sha1(data) for name, data in family.items()}
    if actual != lock["files_git_blob"]:
        raise ValueError("Candidate npm family differs from pinned Git tree")
    required = {"ace.js", "ext-modelist.js", "ext-language_tools.js",
                "keybinding-vim.js", "keybinding-emacs.js"}
    required.update("mode-" + n + ".js" for n in offered["language_modes_offered"])
    required.update("theme-" + n + ".js" for n in offered["themes_offered"])
    js = family["worker-javascript.js"]
    yaml = family["worker-yaml.js"]
    report = {
        "status": "archive-verified", "candidate_only": True,
        "name": lock["name"], "version": lock["version"], "family": lock["family"],
        "source_commit": lock["source_commit"], "build_commit": lock["build_commit"],
        "source_checkout": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                  cwd=ROOT, text=True).strip(),
        "npm_integrity": sri, "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "license_sha256": hashlib.sha256(license_bytes).hexdigest(),
        "family_files": len(family), "required_ui_files": len(required),
        "missing_ui_files": sorted(required - set(family)),
        "added_files": sorted(set(family) - set(old_files)),
        "removed_files": sorted(set(old_files) - set(family)),
        "files_sha256": {name: hashlib.sha256(data).hexdigest()
                         for name, data in sorted(family.items())},
        "worker_indicators": {
            "js_jshint_module": b"ace/mode/javascript/jshint" in js,
            "js_old_license_literal": b"Good, not Evil" in js,
            "js_no_undef_rule": b"no-undef" in js,
            "yaml_legacy_lint_module": b"ace/mode/yaml/yaml-lint" in yaml,
            "yaml_legacy_safe_load": b"DEFAULT_SAFE_SCHEMA" in yaml,
            "yaml_parse_all_documents": b"parseAllDocuments" in yaml,
        },
        "limitations": ["Absence of a string is not a license audit.",
            "New bundled dependencies require exact version and notice review.",
            "Archive equality is not proof of functional compatibility."]
    }
    return report, family


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--extract", type=Path, required=True)
    a = p.parse_args()
    lock = json.loads((ROOT / "docs/ace-candidate-1.45.2.json").read_text("utf-8"))
    offered = json.loads((ROOT / "docs/runtime-dependencies.json").read_text("utf-8"))["ace"]
    old = json.loads((ROOT / "docs/ace-builds-1.9.6-lock.json").read_text("utf-8"))
    report, family = inspect_candidate(a.archive, json.loads(a.registry.read_text("utf-8")),
                                       lock, offered, old["files_sha256"])
    # Must be new; prevent any write into the runtime checkout or an existing directory.
    dest = a.extract.resolve()
    if dest == ROOT or ROOT in dest.parents:
        raise ValueError("Candidate extraction must be outside checkout")
    dest.mkdir(parents=True, exist_ok=False)
    for name, raw in family.items():
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    write(a.output, report)
    # Candidate package scan is separate from current runtime OSV evidence.
    # Additional explicit hypotheses are labelled, not asserted shipped versions.
    identities = [("ace-builds", "1.45.2", "candidate"),
                  ("ace-legacy-linters", "1.0.2", "source build dependency"),
                  ("yaml", "2.8.3", "source minimum version, not exact bundle identity"),
                  ("@babel/parser", "7.29.2", "source minimum version, not exact bundle identity"),
                  ("eslint-scope", "9.1.2", "source minimum version, not exact bundle identity"),
                  ("velocity-animate", "1.2.2", "legacy runtime-version candidate"),
                  ("velocity-animate", "1.2.3", "legacy header-version candidate")]
    results = query_osv([{"package": {"ecosystem": "npm", "name": n}, "version": v}
                         for n, v, _ in identities])
    write(a.output.with_name("ace-candidate-osv.json"), {
        "status": "completed", "source_checkout": report["source_checkout"],
        "results": [{**result, "identity_basis": identity[2]}
                    for result, identity in zip(results, identities)],
        "limitations": ["Separate exploratory scan, not actual runtime inventory or bundled version proof."]})


if __name__ == "__main__":
    main()
