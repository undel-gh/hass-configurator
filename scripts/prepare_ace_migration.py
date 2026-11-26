#!/usr/bin/env python3
"""Prepare a disposable integrated-editor rehearsal; never modify the checkout.

Ace is independently pinned to the reviewed #343 archive, Git family and
license. The js-yaml candidate is registry-SRI verified and its license
compared to the immutable upstream source. Its measured hashes are evidence
for later review, NOT an independently committed npm lock yet.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from inspect_ace_candidate import inspect_candidate, ROOT
from audit_supply_chain import git_blob_sha1, query_osv

ACE_SHA256 = "5260354a14533fa8e94572597b1ff53025b1bb0a9b2e25d50ecf2a01e57aa9e0"
ACE_SRI = "sha512-a0IADaETGBnBW5CIkniUJn7F+NyTuHWKqlv1A8FXaMmFflJsMGnU3TzkiyslInqIZ3odfcVKOdXBGIKBefzFDA=="
ACE_LICENSE_SHA256 = "850f545c5254e8c08204edb2a6d50bbb72727c38a82982c17a84bebf6064cdf8"
YAML_VERSION = "4.3.2"
YAML_URL = "https://registry.npmjs.org/js-yaml/-/js-yaml-4.3.2.tgz"
YAML_SOURCE = "79ca68d90f333fbe6d9e42827527e62636200191"
YAML_LICENSE_BLOB = "09d3a29e93d1239edf737a58fb1cd893808abc82"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sri(raw):
    return "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode("ascii")


def exact_member(archive, name):
    matches = [m for m in archive.getmembers() if m.name == name]
    if len(matches) != 1 or not matches[0].isfile():
        raise ValueError("Missing, duplicate or non-regular archive member: " + name)
    return archive.extractfile(matches[0]).read()


def inspect_yaml(path, registry):
    raw = path.read_bytes()
    if registry.get("dist.tarball") != YAML_URL or registry.get("dist.integrity") != sri(raw):
        raise ValueError("js-yaml candidate registry integrity/source mismatch")
    with tarfile.open(path, "r:gz") as archive:
        meta = json.loads(exact_member(archive, "package/package.json"))
        if (meta.get("name"), meta.get("version"), meta.get("license")) != ("js-yaml", YAML_VERSION, "MIT"):
            raise ValueError("js-yaml candidate package identity mismatch")
        license_bytes = exact_member(archive, "package/LICENSE")
        if git_blob_sha1(license_bytes) != YAML_LICENSE_BLOB:
            raise ValueError("js-yaml candidate license differs from immutable source")
        payload = exact_member(archive, "package/dist/js-yaml.min.js")
    return {
        "name": "js-yaml", "version": YAML_VERSION, "source_commit": YAML_SOURCE,
        "tarball": YAML_URL, "archive_sha256": sha(raw), "npm_integrity": sri(raw),
        "member": "package/dist/js-yaml.min.js", "member_sha256": sha(payload),
        "license_sha256": sha(license_bytes), "license_git_blob": YAML_LICENSE_BLOB,
        "relation": "exact", "independent_archive_pin_pending": True,
    }, payload, license_bytes


def outside_new_checkout(path):
    dest = path.resolve()
    if dest == ROOT or ROOT in dest.parents or dest.exists():
        raise ValueError("Rehearsal destination must be new and outside checkout")
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ace", "ace-registry", "yaml", "yaml-registry", "dest", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    dest = outside_new_checkout(args.dest)
    if sha(args.ace.read_bytes()) != ACE_SHA256 or sri(args.ace.read_bytes()) != ACE_SRI:
        raise ValueError("Ace differs from independently reviewed #343 archive")
    lock = json.loads((ROOT / "docs/ace-candidate-1.45.2.json").read_text("utf-8"))
    old = json.loads((ROOT / "docs/ace-builds-1.9.6-lock.json").read_text("utf-8"))
    offered = json.loads((ROOT / "docs/runtime-dependencies.json").read_text("utf-8"))["ace"]
    ace, family = inspect_candidate(args.ace, json.loads(args.ace_registry.read_text("utf-8")),
                                    lock, offered, old["files_sha256"])
    if ace["missing_ui_files"] or ace["family_files"] != 495:
        raise ValueError("Unexpected Ace migration family or missing UI resources")
    with tarfile.open(args.ace, "r:gz") as archive:
        ace_license = exact_member(archive, "package/LICENSE")
    if sha(ace_license) != ACE_LICENSE_SHA256:
        raise ValueError("Ace license differs from independently reviewed #343")
    yaml, yaml_bytes, yaml_license = inspect_yaml(args.yaml, json.loads(args.yaml_registry.read_text("utf-8")))
    queries = [{"package": {"ecosystem": "npm", "name": name}, "version": version}
               for name, version in (("ace-builds", "1.45.2"), ("js-yaml", YAML_VERSION))]
    osv = query_osv(queries)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {"status": "verified-rehearsal-input", "source_checkout": ace["source_checkout"],
              "candidate_only": True, "ace": ace, "js_yaml": yaml, "osv": osv,
              "limitations": ["No committed runtime migration or nested license clearance.",
                              "js-yaml archive hashes require independent review and pin.",
                              "Not installed artifact or real Supervisor acceptance."]}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if any(row["advisories"] for row in osv):
        raise ValueError("Candidate package/version has OSV matches; review before promotion")
    dest.mkdir()
    pkg = dest / "hass_configurator"
    shutil.copytree(ROOT / "hass_configurator", pkg)
    vendor = pkg / "vendor"
    shutil.rmtree(vendor / "ace")
    for name, raw in family.items():
        target = vendor / "ace" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (vendor / "licenses/ace.txt").write_bytes(ace_license)
    (pkg / "js-yaml.min.js").write_bytes(yaml_bytes)
    (pkg / "third_party/licenses/js-yaml.txt").write_bytes(yaml_license)
    manifest_path = vendor / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["resources"] = {name: digest for name, digest in manifest["resources"].items()
                             if not name.startswith("vendor/ace/")}
    manifest["resources"].update({"vendor/ace/" + name: sha(raw) for name, raw in family.items()})
    manifest["resources"]["vendor/licenses/ace.txt"] = sha(ace_license)
    manifest["provenance"]["ace"] = {"package": "ace-builds", "version": "1.45.2",
                                    "tarball": lock["tarball"], "sha256": ACE_SHA256,
                                    "npm_integrity": ACE_SRI, "license_path_in_archive": "package/LICENSE"}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # The overlay intentionally retains the old audit inventory, which MUST NOT
    # pass the release audit. This is an integration rehearsal, not a package.
    print("Rehearsal overlay prepared:", dest)


if __name__ == "__main__":
    main()
